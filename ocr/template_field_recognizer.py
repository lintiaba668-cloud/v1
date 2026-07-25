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
import logging
import re
import tempfile
from pathlib import Path

from PIL import Image, ImageOps

from .document_rectifier import rectify_document
from .text_parser import (
    clean_project_name_candidate,
    extract_open_report_name,
    extract_project_code,
)


logger = logging.getLogger('PowerRename.TemplateOCR')

TITLE_TOP_PERCENT = 24
START_BODY_PERCENT = 33
MAX_OCR_WIDTH = 2200
CODE_WHITELIST = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-#'


class TemplateFieldRecognizer:

    def __init__(self, executor, debug_dir=None):
        self.executor = executor
        self.debug_dir = Path(debug_dir or 'logs/template_ocr')

    def recognize(self, image_path):
        image_path = Path(image_path)
        image = ImageOps.exif_transpose(Image.open(str(image_path))).convert('RGB')
        image = rectify_document(image)

        orientation = self._select_orientation(image)
        oriented = orientation['image']
        report_type = orientation['report_type']

        self.debug_dir.mkdir(parents=True, exist_ok=True)
        stem = self._safe_stem(image_path.stem)
        oriented.save(self.debug_dir / (stem + '_01_oriented.jpg'))

        if report_type == 'finish':
            fields = self._recognize_completion(
                oriented,
                orientation,
                stem,
            )
        elif report_type == 'start':
            fields = self._recognize_start(
                oriented,
                orientation,
                stem,
            )
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

    def _select_orientation(self, image):
        candidates = []

        for angle in (0, 90, 180, 270):
            rotated = image.rotate(angle, expand=True, fillcolor='white')
            width, height = rotated.size
            title_crop = rotated.crop((
                int(width * 0.02),
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

            candidates.append({
                'angle': angle,
                'image': rotated,
                'score': score,
                'report_type': report_type,
                'text': ocr.get('text', ''),
                'items': ocr.get('items', []),
                'title_crop_height': title_crop.height,
                'prepared_height': prepared.height,
                'prepared_width': prepared.width,
                'scale': scale,
            })

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

    def _recognize_completion(self, image, orientation, stem):
        name_box, code_box = self._completion_boxes(image, orientation)
        name_crop = image.crop(name_box)
        code_crop = image.crop(code_box)

        name_crop.save(self.debug_dir / (stem + '_02_name_crop.jpg'))
        code_crop.save(self.debug_dir / (stem + '_03_code_crop.jpg'))

        name_texts = self._run_field_variants(
            name_crop,
            psms=(6, 11),
            languages='chi_sim+eng',
            include_binary=True,
        )
        code_texts = self._run_field_variants(
            code_crop,
            psms=(7, 6),
            languages='eng',
            whitelist=CODE_WHITELIST,
            include_binary=True,
        )

        name_candidates = self._name_candidates(name_texts)
        code_candidates = self._code_candidates(code_texts)

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

    def _recognize_start(self, image, orientation, stem):
        width, height = image.size
        title_bottom = self._title_bottom_ratio(orientation)
        top_ratio = max(0.035, min(title_bottom, 0.12))

        body_crop = image.crop((
            int(width * 0.04),
            int(height * top_ratio),
            int(width * 0.97),
            int(height * START_BODY_PERCENT / 100.0),
        ))
        body_crop.save(self.debug_dir / (stem + '_02_start_body.jpg'))

        texts = self._run_field_variants(
            body_crop,
            psms=(6, 11),
            languages='chi_sim+eng',
            include_binary=True,
        )
        texts.insert(0, orientation.get('text', ''))

        candidates = []
        for text in texts:
            name = extract_open_report_name(text)
            if name:
                candidates.append(name)

        candidates = self._rank_names(candidates)

        return {
            'project_name': candidates[0] if candidates else '',
            'project_code': '',
            'project_name_candidates': candidates,
            'project_code_candidates': [],
            'field_texts': texts,
        }

    def _completion_boxes(self, image, orientation):
        width, height = image.size
        label = self._find_project_name_label(orientation)

        if label:
            scale = float(orientation.get('scale') or 1.0)
            label_top = label['top'] / scale
            label_height = max(1.0, label['height'] / scale)
            row_top = max(0, label_top - label_height * 0.15)
            row_height = max(
                height * 0.032,
                min(height * 0.052, label_height * 2.0),
            )
        else:
            title_bottom = self._title_bottom_ratio(orientation)
            row_top = height * max(0.035, min(title_bottom * 0.92, 0.075))
            row_height = height * 0.043

        row_bottom = min(height, row_top + row_height)

        # The first row layout is stable across the supplied completion
        # templates: label | project name | code label | project code.
        name_box = (
            int(width * 0.18),
            int(row_top),
            int(width * 0.70),
            int(row_bottom),
        )
        code_box = (
            int(width * 0.76),
            int(row_top),
            int(width * 0.98),
            int(row_bottom),
        )
        return name_box, code_box

    def _find_project_name_label(self, orientation):
        lines = self._group_native_lines(orientation.get('items', []))
        matches = []

        for line in lines:
            compact = self._compact(line['text'])
            left_ratio = line['left'] / float(
                max(1, orientation.get('prepared_width', 1))
            )

            score = 0
            if '工程名称' in compact:
                score = 20
            elif (
                '工程' in compact
                and ('名' in compact or '称' in compact)
                and left_ratio < 0.45
            ):
                score = 10

            if score:
                matches.append((score, -line['top'], line))

        if not matches:
            return None

        matches.sort(reverse=True)
        return matches[0][2]

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
    ):
        texts = []
        variants = [(False, self._prepare_image(image, binary=False)[0])]

        if include_binary:
            variants.append((True, self._prepare_image(image, binary=True)[0]))

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

        return texts

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
            reader = csv.DictReader(file, delimiter='\t')
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

        if chinese_count < 3 or len(compact) < 6 or len(compact) > 100:
            return -100

        if any(word in compact for word in (
            '建设单位', '设计单位', '施工单位', '监理单位',
            '主要工程内容', '工程造价', '实际竣工日期',
            '拆除工程量', '新建工程量',
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
                    candidates.append(value)

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
            values.append((
                10 <= len(compact) <= 18,
                digit_count,
                '-' in value or '#' in value,
                len(compact),
                value,
            ))

        values.sort(reverse=True)
        return [item[-1] for item in values]

    def _prepare_image(self, image, binary=False):
        prepared = ImageOps.autocontrast(image.convert('L'))
        scale = 1.0

        if prepared.width < MAX_OCR_WIDTH:
            scale = float(MAX_OCR_WIDTH) / float(max(1, prepared.width))
            prepared = prepared.resize((
                MAX_OCR_WIDTH,
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

        for token, weight in (
            ('开工', 10),
            ('我方完成', 10),
            ('项目开工前', 8),
        ):
            if token in compact:
                start_score += weight

        for token, weight in (
            ('竣工', 10),
            ('验收', 8),
            ('实际竣工日期', 6),
            ('工程编号', 5),
        ):
            if token in compact:
                finish_score += weight

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
