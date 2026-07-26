# -*- coding: utf-8 -*-
"""Template-aware OCR for power engineering reports.

This module deliberately avoids a mandatory OpenCV/numpy dependency so the
same source can still be packaged for Windows 7 x86 and x64.

Workflow:
1. apply EXIF orientation and optional document rectification;
2. try 0/90/180/270 degrees and select the angle whose top area most closely
   resembles a start/completion report title;
3. for completion reports, OCR only the first-row project-name and project-code
   cells;
4. for start reports, OCR only the paragraph around "我方完成";
5. return multiple OCR candidates so the imported Excel project library can
   select the standard project record.
"""

import csv
import io
import logging
import re
import tempfile
from pathlib import Path

from PIL import Image, ImageFilter, ImageOps

from .document_rectifier import deskew_document, rectify_document
from .text_parser import (
    clean_project_name_candidate,
    extract_completion_name,
    extract_open_report_name,
    extract_project_code,
)


logger = logging.getLogger('PowerRename.TemplateOCR')

TITLE_TOP_PERCENT = 24
START_BODY_PERCENT = 20
MAX_OCR_WIDTH = 2200
MAX_DOCUMENT_WIDTH = 2200
ACCURACY_RETRY_WIDTH = 3200
ACCURACY_DEEP_RETRY_WIDTH = 3600
CODE_WHITELIST = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-#'
STRONG_ORIENTATION_SCORE = 22
STRONG_FIELD_NAME_SCORE = 60


class TemplateFieldRecognizer:

    def __init__(self, executor, debug_dir=None):
        self.executor = executor
        self.debug_dir = Path(debug_dir or 'logs/template_ocr')
        self.debug_dir.mkdir(parents=True, exist_ok=True)

    def recognize(self, image_path, accuracy_mode=True):
        image_path = Path(image_path)
        source_image = ImageOps.exif_transpose(
            Image.open(str(image_path))
        ).convert('RGB')
        image = self._ocr_working_copy(source_image)
        image = rectify_document(image)

        orientation = self._select_orientation(image)
        oriented, deskew_angle = deskew_document(orientation['image'])

        if deskew_angle:
            refreshed = self._analyze_orientation(
                oriented,
                orientation['angle'],
            )
            # Never let an optional correction erase a reliable template
            # classification obtained from the original pixels.
            if (
                refreshed.get('report_type') == orientation.get('report_type')
                or (
                    not orientation.get('report_type')
                    and refreshed.get('report_type')
                )
            ):
                orientation = refreshed
            else:
                deskew_angle = 0.0

        orientation['deskew_angle'] = deskew_angle
        oriented = orientation['image']
        report_type = orientation['report_type']
        retry_image = source_image
        if orientation.get('angle', 0):
            retry_image = retry_image.rotate(
                orientation['angle'],
                expand=True,
                fillcolor='white',
            )

        self.debug_dir.mkdir(parents=True, exist_ok=True)
        stem = self._safe_stem(image_path.stem)
        oriented.save(self.debug_dir / (stem + '_01_oriented.jpg'))

        if report_type == 'finish':
            fields = self._recognize_completion(
                oriented,
                orientation,
                stem,
                accuracy_mode=accuracy_mode,
            )
            has_domain_code = any(
                self._code_format_score(value) > 0
                for value in fields.get('project_code_candidates', [])
            )
            if accuracy_mode and not has_domain_code:
                probe_fields = self._recognize_completion_probe(
                    oriented,
                    stem,
                )
                if probe_fields.get('project_code_candidates'):
                    fields = self._merge_field_results(
                        fields,
                        probe_fields,
                    )
                    has_domain_code = True
            if accuracy_mode and not has_domain_code:
                retry_fields = (
                    self._recognize_completion_high_resolution(
                        retry_image,
                        stem,
                    )
                )
                fields = self._merge_field_results(
                    fields,
                    retry_fields,
                )
            if accuracy_mode and self._looks_like_start_fields(fields):
                start_fields = self._recognize_start(
                    oriented,
                    orientation,
                    stem,
                    retry_image=retry_image,
                    accuracy_mode=accuracy_mode,
                )
                if start_fields.get('project_name_candidates'):
                    fields = start_fields
                    report_type = 'start'
                    orientation['report_type'] = report_type
        elif report_type == 'start':
            fields = self._recognize_start(
                oriented,
                orientation,
                stem,
                retry_image=retry_image,
                accuracy_mode=accuracy_mode,
            )
        else:
            # A tilted phone photo can hide both Chinese field labels from
            # title OCR even though the printed code itself is crisp. Probe
            # the two common first-row vertical positions before falling back
            # to whole-region OCR.
            if accuracy_mode:
                fields = self._recognize_completion_probe(
                    oriented,
                    stem,
                )
                if not fields.get('project_code_candidates'):
                    retry_fields = (
                        self._recognize_completion_high_resolution(
                            retry_image,
                            stem,
                        )
                    )
                    fields = self._merge_field_results(
                        fields,
                        retry_fields,
                    )
            else:
                fields = {
                    'project_name': '',
                    'project_code': '',
                    'project_name_candidates': [],
                    'project_code_candidates': [],
                    'field_texts': [],
                }
            if fields.get('project_code_candidates'):
                report_type = 'finish'
                orientation['report_type'] = report_type
                orientation['score'] = max(orientation.get('score', 0), 10)
            else:
                fields = {
                    'project_name': '',
                    'project_code': '',
                    'project_name_candidates': [],
                    'project_code_candidates': [],
                    'field_texts': [],
                }

        raw_parts = [orientation.get('text', '')]
        raw_parts.extend(fields.get('field_texts', []))

        return {
            'report_type': report_type,
            'rotation_angle': orientation.get('angle', 0),
            'deskew_angle': orientation.get('deskew_angle', 0.0),
            'orientation_score': orientation.get('score', 0),
            'raw_text': '\n'.join(part for part in raw_parts if part),
            'items': orientation.get('items', []),
            'project_name': fields.get('project_name', ''),
            'project_code': fields.get('project_code', ''),
            'project_name_candidates': fields.get(
                'project_name_candidates', []
            ),
            'project_code_candidates': fields.get(
                'project_code_candidates', []
            ),
            'recognition_source': 'template_fields',
        }

    def _looks_like_start_fields(self, fields):
        if fields.get('project_code_candidates'):
            return False

        values = list(fields.get('project_name_candidates', []))
        values.extend(fields.get('field_texts', []))
        compact = self._compact(''.join(str(value) for value in values))
        return (
            '开工' in compact and '请审批' in compact
        ) or any(
            marker in compact
            for marker in (
                '开工请审批',
                '开工,请审批',
                '开工，请审批',
                '项目开工前',
                '我方完成',
            )
        )

    def _select_orientation(self, image):
        upright = self._analyze_orientation(image, 0)

        # A complete upright title already proves the orientation. Avoid three
        # more Tesseract processes for the common case; weak/partial titles
        # still use the full 0/90/180/270 search.
        if (
            upright.get('report_type') in ('start', 'finish')
            and upright.get('score', 0) >= STRONG_ORIENTATION_SCORE
        ):
            logger.info(
                '[ORIENTATION] angle=0 score=%s type=%s fast=true',
                upright['score'],
                upright['report_type'],
            )
            return upright

        candidates = [upright]
        for angle in (90, 180, 270):
            rotated = image.rotate(angle, expand=True, fillcolor='white')
            candidates.append(self._analyze_orientation(rotated, angle))

        candidates.sort(
            key=lambda value: (
                value['score'],
                bool(value['report_type']),
                value['image'].height >= value['image'].width,
                -value['angle'],
            ),
            reverse=True,
        )

        best = candidates[0]

        # If OCR cannot see the title at all, portrait orientation is still the
        # safer default for these A4 templates. This also handles landscape
        # phone photos whose EXIF orientation is missing.
        if best['score'] <= 0 and image.width > image.height:
            portrait = [
                value for value in candidates
                if value['angle'] in (90, 270)
            ]
            portrait.sort(
                key=lambda value: (
                    value['score'],
                    value['image'].height,
                ),
                reverse=True,
            )
            best = portrait[0]

        logger.info(
            '[ORIENTATION] angle=%s score=%s type=%s',
            best['angle'],
            best['score'],
            best['report_type'],
        )
        return best

    def _analyze_orientation(self, image, angle):
        width, height = image.size
        title_crop_left = int(width * 0.02)
        title_crop = image.crop((
            title_crop_left,
            0,
            int(width * 0.98),
            max(1, int(height * TITLE_TOP_PERCENT / 100.0)),
        ))
        prepared, scale = self._prepare_image(title_crop, binary=False)
        ocr = self._ocr_image(
            prepared,
            psm=11,
            languages='chi_sim+eng',
        )
        score, report_type = self._score_title(ocr.get('text', ''))

        result = {
            'angle': angle,
            'image': image,
            'score': score,
            'report_type': report_type,
            'text': ocr.get('text', ''),
            'items': ocr.get('items', []),
            'title_crop_height': title_crop.height,
            'title_crop_left': title_crop_left,
            'prepared_height': prepared.height,
            'prepared_width': prepared.width,
            'scale': scale,
        }

        # On washed-out phone photos the title may be unreadable while the
        # printed first-row labels remain crisp. Both labels together uniquely
        # identify the completion-report template.
        if not result['report_type']:
            name_label = self._find_field_label(result, 'project_name')
            code_label = self._find_field_label(result, 'project_code')
            if name_label and code_label:
                result['report_type'] = 'finish'
                result['score'] = max(result['score'], 12)

        return result

    def _recognize_completion(
        self,
        image,
        orientation,
        stem,
        accuracy_mode=True,
    ):
        name_box, code_box = self._completion_boxes(image, orientation)
        name_crop = image.crop(name_box)
        code_crop = image.crop(code_box)

        name_crop.save(self.debug_dir / (stem + '_02_name_crop.jpg'))
        code_crop.save(self.debug_dir / (stem + '_03_code_crop.jpg'))

        # The same light JPEG normalization used by the debug crop suppresses
        # paper grain and materially improves Tesseract on small printed cells.
        name_crop = self._jpeg_normalize(name_crop)
        code_crop = self._jpeg_normalize(code_crop)

        # Project codes are cheaper and more constrained than Chinese names.
        # Run them first so a standard-form result can take the fast path.
        code_texts = self._run_field_variants(
            code_crop,
            psms=(7, 6) if accuracy_mode else (7,),
            languages='eng',
            whitelist=CODE_WHITELIST,
            include_binary=accuracy_mode,
            stop_when=self._has_strong_code,
        )

        code_candidates = self._code_candidates(code_texts)

        has_domain_code = any(
            self._code_format_score(value) > 0
            for value in code_candidates
        )
        if (
            accuracy_mode
            and not has_domain_code
            and code_crop.height >= 30
        ):
            # Table borders can dominate a tall, perspective-skewed code
            # cell. OCR the central text band without the outer border and
            # label-side noise before trying broader vertical fallbacks.
            inset_code_crop = code_crop.crop((
                int(code_crop.width * 0.12),
                int(code_crop.height * 0.20),
                max(1, int(code_crop.width * 0.94)),
                max(1, int(code_crop.height * 0.78)),
            ))
            retry_texts = self._run_field_variants(
                self._jpeg_normalize(inset_code_crop),
                psms=(7, 6),
                languages='eng',
                whitelist=CODE_WHITELIST,
                include_binary=True,
                stop_when=self._has_strong_code,
            )
            code_texts.extend(
                value for value in retry_texts if value not in code_texts
            )
            code_candidates = self._code_candidates(code_texts)
            has_domain_code = any(
                self._code_format_score(value) > 0
                for value in code_candidates
            )

        if (
            accuracy_mode
            and not has_domain_code
            and code_crop.height >= 30
        ):
            # A correctly located code cell can still contain several rows of
            # whitespace. Retry only its upper half, where the printed code
            # sits, before trying the legacy lower-cell fallback.
            upper_code_crop = code_crop.crop((
                0,
                0,
                code_crop.width,
                max(1, int(code_crop.height * 0.50)),
            ))
            retry_texts = self._run_field_variants(
                self._jpeg_normalize(upper_code_crop),
                psms=(7, 6),
                languages='eng',
                whitelist=CODE_WHITELIST,
                include_binary=True,
                stop_when=self._has_strong_code,
            )
            code_texts.extend(
                value for value in retry_texts if value not in code_texts
            )
            code_candidates = self._code_candidates(code_texts)
            has_domain_code = any(
                self._code_format_score(value) > 0
                for value in code_candidates
            )

        if (
            accuracy_mode
            and not has_domain_code
            and code_crop.height >= 30
        ):
            # Strong perspective can leave the code in a very shallow strip
            # at the top of an otherwise tall cell. Keep this as a second,
            # failure-only probe so normal images pay no extra OCR cost.
            tight_upper_crop = code_crop.crop((
                0,
                0,
                code_crop.width,
                max(1, int(code_crop.height * 0.30)),
            ))
            retry_texts = self._run_field_variants(
                self._jpeg_normalize(tight_upper_crop),
                psms=(7, 6),
                languages='eng',
                whitelist=CODE_WHITELIST,
                include_binary=True,
                stop_when=self._has_strong_code,
            )
            code_texts.extend(
                value for value in retry_texts if value not in code_texts
            )
            code_candidates = self._code_candidates(code_texts)
            has_domain_code = any(
                self._code_format_score(value) > 0
                for value in code_candidates
            )

        if (
            accuracy_mode
            and not has_domain_code
            and code_crop.height >= 30
        ):
            # A wide fallback crop can include the bottom of the report title.
            # Retry below it, keeping the complete code cell and its baseline.
            lower_code_crop = code_crop.crop((
                0,
                int(code_crop.height * 0.32),
                code_crop.width,
                code_crop.height,
            ))
            retry_texts = self._run_field_variants(
                self._jpeg_normalize(lower_code_crop),
                psms=(7, 6),
                languages='eng',
                whitelist=CODE_WHITELIST,
                include_binary=True,
                stop_when=self._has_strong_code,
            )
            code_texts.extend(
                value for value in retry_texts if value not in code_texts
            )
            code_candidates = self._code_candidates(code_texts)

        name_texts = self._run_field_variants(
            name_crop,
            psms=(6, 11) if accuracy_mode else (6,),
            languages='chi_sim+eng',
            include_binary=accuracy_mode,
            stop_when=self._has_strong_completion_name,
        )
        name_candidates = self._name_candidates(name_texts)

        return {
            'project_name': (
                name_candidates[0] if name_candidates else ''
            ),
            'project_code': (
                code_candidates[0] if code_candidates else ''
            ),
            'project_name_candidates': name_candidates,
            'project_code_candidates': code_candidates,
            'field_texts': name_texts + code_texts,
        }

    def _recognize_start(
        self,
        image,
        orientation,
        stem,
        retry_image=None,
        accuracy_mode=True,
    ):
        body_crop = image.crop(self._start_body_box(image, orientation))
        body_crop.save(self.debug_dir / (stem + '_02_start_body.jpg'))

        texts = self._run_field_variants(
            body_crop,
            psms=(6, 11) if accuracy_mode else (6,),
            languages='chi_sim+eng',
            include_binary=accuracy_mode,
            stop_when=self._has_strong_start_name,
        )
        texts.insert(0, orientation.get('text', ''))

        candidates = []
        for text in texts:
            name = extract_open_report_name(text)
            if name:
                candidates.append(name)

        candidates = self._rank_names(candidates)

        needs_accuracy_retry = (
            not candidates
            or self._name_score(candidates[0]) < STRONG_FIELD_NAME_SCORE
        )
        if (
            accuracy_mode
            and needs_accuracy_retry
            and retry_image is not None
        ):
            retry_fields = self._recognize_start_high_resolution(
                retry_image,
                stem,
                title_bottom_ratio=self._title_bottom_ratio(orientation),
            )
            if retry_fields.get('project_name_candidates'):
                merged_candidates = self._rank_names(
                    candidates
                    + retry_fields.get('project_name_candidates', [])
                )
                return {
                    'project_name': (
                        merged_candidates[0]
                        if merged_candidates else ''
                    ),
                    'project_code': '',
                    'project_name_candidates': merged_candidates,
                    'project_code_candidates': [],
                    'field_texts': (
                        texts + retry_fields.get('field_texts', [])
                    ),
                }

        return {
            'project_name': candidates[0] if candidates else '',
            'project_code': '',
            'project_name_candidates': candidates,
            'project_code_candidates': [],
            'field_texts': texts,
        }

    def _recognize_start_high_resolution(
        self,
        image,
        stem,
        title_bottom_ratio=None,
    ):
        width, height = image.size
        body_crop = image.crop((
            int(width * 0.04),
            int(height * 0.03),
            int(width * 0.97),
            int(height * 0.24),
        ))
        body_crop.save(
            self.debug_dir / (stem + '_04_start_accuracy_retry.jpg')
        )
        texts = self._run_field_variants(
            body_crop,
            psms=(6, 11),
            languages='chi_sim+eng',
            include_binary=True,
            stop_when=self._has_strong_start_name,
            max_width=ACCURACY_RETRY_WIDTH,
        )
        candidates = self._rank_names([
            extract_open_report_name(text)
            for text in texts
            if extract_open_report_name(text)
        ])

        # Long start-report names commonly wrap after the first voltage/line
        # fragment. A broad paragraph crop can recognize only the second line
        # and still look plausible because it ends in “工程”. Deep mode gets
        # one dedicated, high-resolution pass over the two visual name rows.
        # Use Chinese recognition here: mixed-language segmentation tends to
        # turn the first row's repeated kV/I-road tokens into Latin noise.
        two_line_fields = self._recognize_start_two_line_high_resolution(
            image,
            stem,
            title_bottom_ratio=title_bottom_ratio,
        )
        texts.extend(
            value
            for value in two_line_fields.get('field_texts', [])
            if value not in texts
        )
        candidates = self._rank_names(
            candidates
            + two_line_fields.get('project_name_candidates', [])
        )

        if (
            not candidates
            or self._name_score(candidates[0]) < STRONG_FIELD_NAME_SCORE
        ):
            # Some phone photos include another document above the report.
            # Shift the crop down and sharpen only after the normal and first
            # high-resolution passes fail, keeping the common path fast.
            deep_crop = image.crop((
                int(width * 0.03),
                int(height * 0.08),
                int(width * 0.99),
                int(height * 0.30),
            ))
            deep_crop.save(
                self.debug_dir / (stem + '_05_start_deep_retry.jpg')
            )
            prepared, _ = self._prepare_image(
                deep_crop,
                max_width=ACCURACY_DEEP_RETRY_WIDTH,
            )
            prepared = prepared.filter(ImageFilter.UnsharpMask(
                radius=1.4,
                percent=220,
                threshold=2,
            ))

            for psm in (11, 6):
                result = self._ocr_image(
                    prepared,
                    psm=psm,
                    languages='chi_sim+eng',
                )
                text = result.get('text', '').strip()
                if text and text not in texts:
                    texts.append(text)
                name = extract_open_report_name(text)
                if name:
                    candidates = self._rank_names(candidates + [name])
                if (
                    candidates
                    and self._name_score(candidates[0])
                    >= STRONG_FIELD_NAME_SCORE
                ):
                    break

        if (
            (
                not candidates
                or self._name_score(candidates[0])
                < STRONG_FIELD_NAME_SCORE
            )
            and width > height * 1.35
        ):
            # A previously cropped/exported start report may contain only the
            # top half of the page. Its name row then sits near 35%-50% of the
            # image rather than the usual 10%-20%.
            landscape_crop = image.crop((
                int(width * 0.03),
                int(height * 0.08),
                int(width * 0.99),
                int(height * 0.58),
            ))
            landscape_crop.save(
                self.debug_dir / (
                    stem + '_06_start_landscape_retry.jpg'
                )
            )
            prepared, _ = self._prepare_image(
                landscape_crop,
                max_width=ACCURACY_DEEP_RETRY_WIDTH,
            )
            prepared = prepared.filter(ImageFilter.UnsharpMask(
                radius=1.2,
                percent=180,
                threshold=2,
            ))

            for psm in (11, 6):
                result = self._ocr_image(
                    prepared,
                    psm=psm,
                    languages='chi_sim+eng',
                )
                text = result.get('text', '').strip()
                if text and text not in texts:
                    texts.append(text)
                name = extract_open_report_name(text)
                if name:
                    candidates = self._rank_names(candidates + [name])
                if (
                    candidates
                    and self._name_score(candidates[0])
                    >= STRONG_FIELD_NAME_SCORE
                ):
                    break

        return {
            'project_name': candidates[0] if candidates else '',
            'project_code': '',
            'project_name_candidates': candidates,
            'project_code_candidates': [],
            'field_texts': texts,
        }

    def _recognize_start_two_line_high_resolution(
        self,
        image,
        stem,
        title_bottom_ratio=None,
    ):
        width, height = image.size
        title_bottom = (
            float(title_bottom_ratio)
            if title_bottom_ratio is not None
            else 0.06
        )
        top_ratio = max(0.075, min(title_bottom + 0.023, 0.125))
        bottom_ratio = min(0.20, top_ratio + 0.055)
        name_crop = image.crop((
            int(width * 0.27),
            int(height * top_ratio),
            int(width * 0.98),
            int(height * bottom_ratio),
        ))
        name_crop.save(
            self.debug_dir / (stem + '_07_start_two_line_retry.jpg')
        )
        texts = self._run_field_variants(
            name_crop,
            psms=(6, 11),
            languages='chi_sim',
            include_binary=True,
            stop_when=self._has_strong_completion_name,
            max_width=ACCURACY_DEEP_RETRY_WIDTH,
        )
        candidates = self._name_candidates(texts)

        return {
            'project_name': candidates[0] if candidates else '',
            'project_code': '',
            'project_name_candidates': candidates,
            'project_code_candidates': [],
            'field_texts': texts,
        }

    def _start_body_box(self, image, orientation):
        width, height = image.size
        title_bottom = self._title_bottom_ratio(orientation)
        top_ratio = max(0.035, min(title_bottom, 0.12))

        # The required start-report fields end at "开工，请审批". Excluding the
        # checklist/signature area cuts OCR pixels substantially and removes
        # dates, ticks and stamp noise without trimming wrapped project names.
        return (
            int(width * 0.04),
            int(height * top_ratio),
            int(width * 0.97),
            int(height * START_BODY_PERCENT / 100.0),
        )

    def _recognize_completion_probe(self, image, stem):
        code_texts = []
        selected_box = None
        selected_candidates = []

        for box in self._completion_probe_code_boxes(image):
            code_crop = image.crop(box)
            texts = self._run_field_variants(
                self._jpeg_normalize(code_crop),
                psms=(7, 6),
                languages='eng',
                whitelist=CODE_WHITELIST,
                include_binary=True,
                stop_when=self._has_strong_code,
            )
            candidates = [
                value for value in self._code_candidates(texts)
                if self._is_completion_probe_code(value)
            ]

            if not candidates:
                # The broad probe deliberately includes the “工程编号” label
                # so it works across different table layouts. On bordered or
                # slightly skewed phone photos that extra label/table line can
                # make Tesseract reject an otherwise clear code. Retry only
                # the inner value band before giving up on this row.
                crop_width, crop_height = code_crop.size
                value_crop = code_crop.crop((
                    int(crop_width * 0.20),
                    int(crop_height * 0.18),
                    int(crop_width * 0.96),
                    int(crop_height * 0.82),
                ))
                inset_texts = self._run_field_variants(
                    self._jpeg_normalize(value_crop),
                    psms=(7, 6),
                    languages='eng',
                    whitelist=CODE_WHITELIST,
                    include_binary=True,
                    stop_when=self._has_strong_code,
                )
                texts.extend(
                    value for value in inset_texts
                    if value not in texts
                )
                candidates = [
                    value for value in self._code_candidates(texts)
                    if self._is_completion_probe_code(value)
                ]

            code_texts.extend(
                value for value in texts if value not in code_texts
            )

            if candidates:
                selected_box = box
                selected_candidates = candidates
                break

        if not selected_candidates:
            return {
                'project_name': '',
                'project_code': '',
                'project_name_candidates': [],
                'project_code_candidates': [],
                'field_texts': code_texts,
            }

        width, _ = image.size
        row_top, row_bottom = selected_box[1], selected_box[3]
        name_box = (
            int(width * 0.10),
            row_top,
            int(width * 0.76),
            row_bottom,
        )
        name_crop = image.crop(name_box)
        code_crop = image.crop(selected_box)
        name_crop.save(self.debug_dir / (stem + '_02_name_crop.jpg'))
        code_crop.save(self.debug_dir / (stem + '_03_code_crop.jpg'))

        name_texts = self._run_field_variants(
            self._jpeg_normalize(name_crop),
            psms=(6, 11),
            languages='chi_sim+eng',
            include_binary=True,
            stop_when=self._has_strong_completion_name,
        )
        name_candidates = self._name_candidates(name_texts)

        return {
            'project_name': (
                name_candidates[0] if name_candidates else ''
            ),
            'project_code': selected_candidates[0],
            'project_name_candidates': name_candidates,
            'project_code_candidates': selected_candidates,
            'field_texts': name_texts + code_texts,
        }

    def _recognize_completion_high_resolution(self, image, stem):
        """Accuracy-only full first-row retry on the original pixels."""
        width, height = image.size
        top_crop = image.crop((
            int(width * 0.03),
            int(height * 0.01),
            int(width * 0.99),
            int(height * 0.30),
        ))
        top_crop.save(
            self.debug_dir / (
                stem + '_07_completion_accuracy_retry.jpg'
            )
        )

        name_texts = self._run_field_variants(
            top_crop,
            psms=(6, 11),
            languages='chi_sim+eng',
            include_binary=True,
            stop_when=self._has_strong_completion_name,
            max_width=ACCURACY_DEEP_RETRY_WIDTH,
        )
        sharpened = top_crop.filter(ImageFilter.UnsharpMask(
            radius=1.2,
            percent=190,
            threshold=2,
        ))
        code_texts = self._run_field_variants(
            sharpened,
            psms=(11, 6, 7),
            languages='eng',
            whitelist=CODE_WHITELIST,
            include_binary=True,
            stop_when=self._has_strong_code,
            max_width=ACCURACY_DEEP_RETRY_WIDTH,
        )

        name_candidates = []
        for text in name_texts:
            value = extract_completion_name(text)
            if value:
                name_candidates.append(value)
        name_candidates.extend(self._name_candidates(name_texts))
        name_candidates = self._rank_names(name_candidates)
        code_candidates = self._code_candidates(
            code_texts + name_texts
        )

        return {
            'project_name': (
                name_candidates[0] if name_candidates else ''
            ),
            'project_code': (
                code_candidates[0] if code_candidates else ''
            ),
            'project_name_candidates': name_candidates,
            'project_code_candidates': code_candidates,
            'field_texts': name_texts + code_texts,
        }

    def _merge_field_results(self, primary, retry):
        name_candidates = self._rank_names(
            list(primary.get('project_name_candidates', []))
            + list(retry.get('project_name_candidates', []))
        )
        code_candidates = self._code_candidates(
            list(primary.get('project_code_candidates', []))
            + list(retry.get('project_code_candidates', []))
        )
        field_texts = []
        for value in (
            list(primary.get('field_texts', []))
            + list(retry.get('field_texts', []))
        ):
            if value and value not in field_texts:
                field_texts.append(value)

        return {
            'project_name': (
                name_candidates[0] if name_candidates else ''
            ),
            'project_code': (
                code_candidates[0] if code_candidates else ''
            ),
            'project_name_candidates': name_candidates,
            'project_code_candidates': code_candidates,
            'field_texts': field_texts,
        }

    @staticmethod
    def _completion_probe_code_boxes(image):
        width, height = image.size
        ratios = (
            # Tightly framed scans and most upright phone photos.
            (0.64, 0.030, 0.995, 0.145),
            # Photos with another sheet/margin above the report title.
            (0.70, 0.105, 0.995, 0.205),
        )
        return [
            (
                int(width * left),
                int(height * top),
                int(width * right),
                int(height * bottom),
            )
            for left, top, right, bottom in ratios
        ]

    def _is_completion_probe_code(self, value):
        compact = str(value or '').upper()
        return (
            self._code_format_score(compact) > 0
            and bool(re.match(
                r'^(?:B113|C513|181320|211320)',
                compact,
            ))
        )

    def _completion_boxes(self, image, orientation):
        width, height = image.size
        name_label = self._find_field_label(
            orientation,
            field='project_name',
        )
        code_label = self._find_field_label(
            orientation,
            field='project_code',
        )
        labels = [
            value for value in (name_label, code_label) if value
        ]

        if labels:
            scale = float(orientation.get('scale') or 1.0)
            label_tops = [value['top'] / scale for value in labels]
            label_bottoms = [
                (value['top'] + value['height']) / scale
                for value in labels
            ]
            label_height = max(
                1.0,
                max(value['height'] / scale for value in labels),
            )
            row_top = max(
                0,
                min(label_tops) - label_height * 0.45 - height * 0.004,
            )
            row_bottom = min(
                height,
                max(label_bottoms) + label_height * 1.55 + height * 0.006,
            )
            minimum_height = height * 0.042
            if row_bottom - row_top < minimum_height:
                row_bottom = min(height, row_top + minimum_height)
        else:
            title_bottom = self._title_bottom_ratio(orientation)
            # Without reliable label coordinates, begin above the estimated
            # title bottom and include two shallow rows. This avoids dropping
            # the project row on tightly framed phone photos.
            row_top = height * max(0.018, min(title_bottom * 0.60, 0.050))
            row_bottom = min(height, row_top + height * 0.085)

        crop_left = float(orientation.get('title_crop_left') or 0)
        scale = float(orientation.get('scale') or 1.0)

        if name_label:
            name_left = (
                crop_left
                + (name_label['left'] + name_label['width']) / scale
                - width * 0.006
            )
        else:
            name_left = width * 0.11

        if code_label:
            code_label_left = (
                crop_left + code_label['left'] / scale
            )
            code_label_right = (
                crop_left
                + (code_label['left'] + code_label['width']) / scale
            )
            name_right = code_label_left + width * 0.008
            code_label_width = code_label['width'] / scale
            if code_label_width > width * 0.18:
                # PSM 11 can merge the label and the printed code into one
                # abnormally wide word. Its right edge then points outside the
                # code cell, so use the conservative table boundary instead.
                code_left = width * 0.66
            else:
                code_left = code_label_right - width * 0.010
        else:
            name_right = width * 0.70
            code_left = width * 0.66

        # Validate OCR-derived geometry.  A bad label span must never make a
        # crop narrower than the conservative fallback cells.
        if name_right - name_left < width * 0.30:
            name_left = width * 0.11
            name_right = width * 0.70
        if width * 0.985 - code_left < width * 0.16:
            code_left = width * 0.66

        name_box = (
            int(max(0, name_left)),
            int(row_top),
            int(min(width, name_right)),
            int(row_bottom),
        )
        code_box = (
            int(max(0, code_left)),
            int(row_top),
            int(width * 0.985),
            int(row_bottom),
        )
        return name_box, code_box

    def _find_project_name_label(self, orientation):
        return self._find_field_label(orientation, 'project_name')

    def _find_field_label(self, orientation, field):
        lines = self._group_native_lines(orientation.get('items', []))
        matches = []

        for line in lines:
            words = line.get('words', [])

            for start in range(len(words)):
                for end in range(start + 1, min(len(words), start + 4) + 1):
                    span = words[start:end]
                    compact = self._compact(''.join(
                        value.get('text', '') for value in span
                    ))
                    score = self._field_label_score(compact, field)

                    if not score:
                        continue

                    left = min(value.get('x', 0) for value in span)
                    top = min(value.get('y', 0) for value in span)
                    right = max(
                        value.get('x', 0) + value.get('w', 0)
                        for value in span
                    )
                    bottom = max(
                        value.get('y', 0) + value.get('h', 0)
                        for value in span
                    )
                    left_ratio = left / float(
                        max(1, orientation.get('prepared_width', 1))
                    )

                    if left_ratio > 0.82:
                        continue

                    value = {
                        'text': compact,
                        'left': left,
                        'top': top,
                        'width': right - left,
                        'height': bottom - top,
                    }
                    matches.append((score, -top, value))

        if not matches:
            return None

        matches.sort(
            key=lambda item: (item[0], item[1]),
            reverse=True,
        )
        return matches[0][2]

    @staticmethod
    def _field_label_score(compact, field):
        if field == 'project_name':
            if '工程名称' in compact:
                return 30
            if '工程' in compact and ('名' in compact or '称' in compact):
                return 15
            return 0

        if field == 'project_code':
            if '工程编号' in compact:
                return 30
            if '工程' in compact and ('编' in compact or '号' in compact):
                return 15
            return 0

        return 0

    def _title_bottom_ratio(self, orientation):
        lines = self._group_native_lines(orientation.get('items', []))
        prepared_height = float(max(1, orientation.get('prepared_height', 1)))
        crop_height = float(max(1, orientation.get('title_crop_height', 1)))
        best = None

        for line in lines:
            compact = self._compact(line['text'])
            score = 0

            for token, weight in (
                ('配网', 4),
                ('工程', 3),
                ('开工', 8),
                ('竣工', 8),
                ('验收', 8),
                ('报告', 5),
            ):
                if token in compact:
                    score += weight

            if score and (best is None or score > best[0]):
                best = (score, line)

        if not best:
            return 0.055

        bottom_prepared = best[1]['top'] + best[1]['height']
        bottom_in_crop = bottom_prepared / prepared_height * crop_height
        image_height = float(max(1, orientation['image'].height))
        return max(0.02, min(0.16, bottom_in_crop / image_height))

    def _run_field_variants(
        self,
        image,
        psms,
        languages,
        whitelist='',
        include_binary=False,
        stop_when=None,
        max_width=None,
    ):
        texts = []
        prepare_options = {}
        if max_width is not None:
            prepare_options['max_width'] = max_width
        variants = [(
            False,
            self._prepare_image(
                image,
                binary=False,
                **prepare_options
            )[0],
        )]

        if include_binary:
            variants.append((
                True,
                self._prepare_image(
                    image,
                    binary=True,
                    **prepare_options
                )[0],
            ))

        for _, prepared in variants:
            for psm in psms:
                result = self._ocr_image(
                    prepared,
                    psm=psm,
                    languages=languages,
                    whitelist=whitelist,
                )
                text = result.get('text', '').strip()
                if text and text not in texts:
                    texts.append(text)
                    if stop_when and stop_when(texts):
                        return texts

        return texts

    def _has_strong_start_name(self, texts):
        for text in texts:
            name = extract_open_report_name(text)
            if name and self._name_score(name) >= STRONG_FIELD_NAME_SCORE:
                return True
        return False

    def _has_strong_completion_name(self, texts):
        return any(
            self._name_score(value) >= STRONG_FIELD_NAME_SCORE
            for value in self._name_candidates(texts)
        )

    def _has_strong_code(self, texts):
        return any(
            self._code_format_score(value) >= 3
            for value in self._code_candidates(texts)
        )

    def _ocr_image(self, image, psm, languages, whitelist=''):
        temp_path = None
        executor_result = None

        try:
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp:
                temp_path = Path(temp.name)
            image.save(str(temp_path))

            executor_result = self.executor.execute(
                str(temp_path),
                psm=psm,
                languages=languages,
                whitelist=whitelist,
                oem=1,
            )

            if not executor_result.get('success'):
                return {'text': '', 'items': []}

            parsed = self._parse_tsv(executor_result['tsv_file'])
            return parsed

        finally:
            if executor_result:
                self.executor.cleanup(executor_result)
            if temp_path and temp_path.exists():
                temp_path.unlink()

    def _parse_tsv(self, tsv_file):
        items = []

        with open(str(tsv_file), 'r', encoding='utf-8') as file:
            # Tesseract TSV is tab-delimited but not CSV-quoted. OCR can emit
            # a literal double quote as a glyph; the csv default would treat
            # it as the start of a multiline quoted field and swallow every
            # following TSV row into one corrupt text box.
            reader = csv.DictReader(
                file,
                delimiter='\t',
                quoting=csv.QUOTE_NONE,
            )
            for row in reader:
                text = row.get('text', '').strip()
                confidence = row.get('conf', '-1')

                if not text or confidence == '-1':
                    continue

                try:
                    confidence_value = float(confidence)
                except Exception:
                    confidence_value = -1.0

                # Tesseract occasionally emits full-image garbage boxes with
                # zero/negative confidence. They corrupt field geometry and
                # are not useful for matching.
                if confidence_value < 0:
                    continue

                items.append({
                    'text': text,
                    'confidence': confidence_value,
                    'x': int(row.get('left', 0)),
                    'y': int(row.get('top', 0)),
                    'w': int(row.get('width', 0)),
                    'h': int(row.get('height', 0)),
                    'page': row.get('page_num', ''),
                    'block': row.get('block_num', ''),
                    'paragraph': row.get('par_num', ''),
                    'line': row.get('line_num', ''),
                })

        lines = self._group_native_lines(items)
        return {
            'items': items,
            'text': '\n'.join(line['text'] for line in lines),
        }

    def _group_native_lines(self, items):
        groups = {}

        for item in items:
            key = (
                item.get('page', ''),
                item.get('block', ''),
                item.get('paragraph', ''),
                item.get('line', ''),
            )
            groups.setdefault(key, []).append(item)

        result = []
        for words in groups.values():
            words = sorted(words, key=lambda value: value.get('x', 0))
            left = min(value.get('x', 0) for value in words)
            top = min(value.get('y', 0) for value in words)
            right = max(
                value.get('x', 0) + value.get('w', 0)
                for value in words
            )
            bottom = max(
                value.get('y', 0) + value.get('h', 0)
                for value in words
            )
            result.append({
                'text': ' '.join(
                    value.get('text', '') for value in words
                    if value.get('text', '')
                ).strip(),
                'left': left,
                'top': top,
                'width': right - left,
                'height': bottom - top,
                'words': words,
            })

        result.sort(key=lambda value: (value['top'], value['left']))
        return result

    def _name_candidates(self, texts):
        candidates = []

        for text in texts:
            lines = [
                self._compact(line)
                for line in str(text).splitlines()
                if self._compact(line)
            ]

            # The field can occupy one or two lines. Keep individual lines and
            # adjacent combinations; Excel matching will select the best one.
            for index, line in enumerate(lines):
                candidates.append(clean_project_name_candidate(line))
                if index + 1 < len(lines):
                    candidates.append(clean_project_name_candidate(
                        line + lines[index + 1]
                    ))

            candidates.append(clean_project_name_candidate(text))

        return self._rank_names(candidates)

    def _rank_names(self, candidates):
        values = []
        seen = set()

        for candidate in candidates:
            value = clean_project_name_candidate(candidate)
            if not value or value in seen:
                continue
            score = self._name_score(value)
            if score < 20:
                continue
            seen.add(value)
            values.append((score, value))

        values.sort(key=lambda item: (item[0], len(item[1])), reverse=True)
        return [value for _, value in values]

    def _name_score(self, value):
        compact = self._compact(value)
        chinese_count = len(re.findall(r'[\u4e00-\u9fff]', compact))
        latin_count = len(re.findall(r'[A-Za-z]', compact))

        if chinese_count < 3 or len(compact) < 6 or len(compact) > 100:
            return -100

        if any(word in compact for word in (
            '建设单位', '设计单位', '施工单位', '监理单位',
            '主要工程内容', '工程造价', '实际竣工日期',
            '拆除工程量', '新建工程量',
            '项目开工前的各项', '开工前的各项',
        )):
            return -100

        score = min(chinese_count, 30)

        if re.search(r'(?:10|35|110|220)[kK][vV]', compact):
            score += 25
        if '工程' in compact:
            score += 18
        if compact.endswith('工程'):
            score += 8

        for word in (
            '台区', '线路', '开闭所', '分界开关', '箱式变',
            '配套', '业扩', '治理', '迁改', '新装', '改造',
        ):
            if word in compact:
                score += 5

        # Real project names contain a few Latin identifiers (kV, A03, I路),
        # but a long Latin-heavy prefix is characteristic of a badly
        # segmented OCR line. Do not let the voltage/“工程” bonuses make such
        # noise look reliable enough to skip the high-resolution retry.
        if latin_count > 12 and latin_count > chinese_count:
            score -= min(35, latin_count - chinese_count + 15)

        return score

    def _code_candidates(self, texts):
        candidates = []

        for text in texts:
            parsed = extract_project_code('工程编号\n' + str(text))
            if parsed:
                candidates.append(parsed)

            for value in re.findall(r'[#A-Z0-9][#A-Z0-9\-]{4,23}', str(text).upper()):
                value = re.sub(r'[^#A-Z0-9\-]', '', value)
                if 'KV' not in value:
                    # OCR sometimes prefixes border/label glyphs. Expose the
                    # embedded domain code as an extra Excel-match candidate.
                    embedded = re.search(
                        r'(?:B113|C513|181320|211320)[A-Z0-9#\-]{5,17}',
                        value,
                    )
                    if embedded:
                        candidates.append(embedded.group(0))
                    if re.match(r'^\d{13}$', value):
                        candidates.append(value[:12] + '-' + value[12:])
                    candidates.append(value)

        repaired = []
        for value in candidates:
            repaired.extend(self._repair_domain_code_candidates(value))
        candidates.extend(repaired)

        values = []
        seen = set()

        for value in candidates:
            compact = value.replace('-', '').replace('#', '')
            digit_count = sum(char.isdigit() for char in compact)
            if len(compact) < 5 or digit_count < 3:
                continue
            if value in seen:
                continue
            seen.add(value)
            known_prefix = bool(re.match(
                r'^(?:B113|C513|181320|211320)',
                value,
            ))
            format_score = self._code_format_score(value)
            values.append((
                format_score,
                known_prefix,
                10 <= len(compact) <= 18,
                digit_count,
                '-' in value or '#' in value,
                -len(compact),
                value,
            ))

        values.sort(reverse=True)
        return [item[-1] for item in values]

    @staticmethod
    def _repair_domain_code_candidates(value):
        """Expose conservative variants for fixed-format prefix loss.

        These are candidates only; the project matcher still requires an
        exact, unique row in the imported engineering library. The common
        failures here are caused by a table border clipping the left edge and
        by Tesseract confusing the fixed migration-code ``Z`` marker.
        """
        compact = re.sub(
            r'[^A-Z0-9\-#]',
            '',
            str(value or '').upper(),
        )
        bases = [compact]

        for observed, prefix in (
            ('81320', '1'),
            ('1320', '18'),
            ('320', '181'),
        ):
            if compact.startswith(observed):
                bases.append(prefix + compact)
                break

        if compact.startswith('513') and len(
            compact.replace('-', '').replace('#', '')
        ) == 11:
            bases.append('C' + compact)
        if compact.startswith('113') and len(
            compact.replace('-', '').replace('#', '')
        ) == 11:
            bases.append('B' + compact)

        variants = []
        for base in bases[1:]:
            variants.append(base)

        for base in list(bases):
            core = base.replace('-', '').replace('#', '')
            if not re.match(r'^[BC]\d{11}$', core):
                continue

            structured = core[:8] + 'Z' + core[9:]
            variants.append(structured)

            # 2/7 and Z are frequent OCR confusions in the three-character
            # suffix. Generate one-character alternatives; conflicting exact
            # library hits are kept for manual review by the service layer.
            for index in range(9, 12):
                if structured[index] in ('2', '7'):
                    variants.append(
                        structured[:index]
                        + 'Z'
                        + structured[index + 1:]
                    )

        result = []
        seen = set()
        for candidate in variants:
            if candidate and candidate != compact and candidate not in seen:
                seen.add(candidate)
                result.append(candidate)
        return result

    @staticmethod
    def _code_format_score(value):
        compact = str(value or '').upper()
        if re.match(r'^[BC]\d{7}Z[A-Z0-9]{3}$', compact):
            return 3
        if re.match(r'^\d{12}-\d{1,2}$', compact):
            return 3
        if re.match(r'^\d{11}[A-Z](?:-?\d{2})?$', compact):
            return 3
        if re.match(r'^(?:B113|C513|181320|211320)', compact):
            return 1
        return 0

    @staticmethod
    def _jpeg_normalize(image):
        buffer = io.BytesIO()
        image.convert('RGB').save(buffer, format='JPEG', quality=75)
        buffer.seek(0)
        normalized = Image.open(buffer).convert('RGB')
        normalized.load()
        return normalized

    @staticmethod
    def _ocr_working_copy(image):
        """Bound OCR pixels while preserving the untouched source image."""
        if image.width <= MAX_DOCUMENT_WIDTH:
            return image

        scale = float(MAX_DOCUMENT_WIDTH) / float(image.width)
        return image.resize((
            MAX_DOCUMENT_WIDTH,
            max(1, int(round(image.height * scale))),
        ), Image.Resampling.LANCZOS)

    def _prepare_image(self, image, binary=False, max_width=None):
        prepared = ImageOps.autocontrast(image.convert('L'))
        scale = 1.0
        target_width = int(max_width or MAX_OCR_WIDTH)

        if prepared.width != target_width:
            scale = float(target_width) / float(max(1, prepared.width))
            prepared = prepared.resize((
                target_width,
                max(1, int(round(prepared.height * scale))),
            ), Image.Resampling.LANCZOS)

        if binary:
            threshold = self._otsu_threshold(prepared)
            prepared = prepared.point(
                lambda value: 255 if value > threshold else 0,
                mode='1',
            ).convert('L')

        return prepared, scale

    @staticmethod
    def _otsu_threshold(image):
        histogram = image.histogram()[:256]
        total = sum(histogram)

        if total <= 0:
            return 160

        weighted_sum = sum(index * count for index, count in enumerate(histogram))
        background_weight = 0
        background_sum = 0
        maximum = -1.0
        threshold = 160

        for index, count in enumerate(histogram):
            background_weight += count
            if background_weight <= 0:
                continue

            foreground_weight = total - background_weight
            if foreground_weight <= 0:
                break

            background_sum += index * count
            background_mean = background_sum / float(background_weight)
            foreground_mean = (
                weighted_sum - background_sum
            ) / float(foreground_weight)
            variance = (
                background_weight
                * foreground_weight
                * (background_mean - foreground_mean) ** 2
            )

            if variance > maximum:
                maximum = variance
                threshold = index

        return threshold

    @staticmethod
    def _score_title(text):
        compact = TemplateFieldRecognizer._compact(text)
        start_score = 0
        finish_score = 0

        for token, weight in (
            ('配网', 4),
            ('工程', 3),
            ('报告', 5),
        ):
            if token in compact:
                start_score += weight
                finish_score += weight

        if '开工' in compact and '开工日期' not in compact:
            start_score += 10

        for token, weight in (
            ('我方完成', 10),
            ('项目开工前', 8),
        ):
            if token in compact:
                start_score += weight

        if '开工报告' in compact:
            # An explicit title is stronger than unrelated completion-table
            # labels visible on another sheet in the same phone photo.
            start_score += 15

        for token, weight in (
            ('竣工', 10),
            ('验收', 8),
            ('实际竣工日期', 6),
            ('工程编号', 5),
        ):
            if token in compact:
                finish_score += weight

        if '竣工验收报告' in compact:
            finish_score += 15

        structure_hits = sum(
            token in compact
            for token in ('建设单位', '设计单位', '施工单位', '监理单位')
        )
        if (
            ('工程名称' in compact or '程名称' in compact)
            and structure_hits >= 2
        ):
            finish_score += 12

        if start_score > finish_score and start_score >= 8:
            return start_score, 'start'
        if finish_score >= start_score and finish_score >= 8:
            return finish_score, 'finish'
        return max(start_score, finish_score), ''

    @staticmethod
    def _compact(value):
        return re.sub(r'\s+', '', str(value or ''))

    @staticmethod
    def _safe_stem(value):
        return re.sub(r'[^A-Za-z0-9_.-]', '_', str(value or 'image'))[:80]
