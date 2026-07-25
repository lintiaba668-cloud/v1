"""
OCR识别引擎接口。

Primary path:
- automatic 0/90/180/270 orientation selection;
- template-specific project-name/project-code crops;
- multiple field OCR candidates for Excel matching.

Fallback path:
- legacy adaptive top-region OCR for unknown templates.
"""

from pathlib import Path
import csv
import json
import logging
import tempfile

from .text_parser import parse_report_text
from .image_preprocess import preprocess
from .ocr_executor import OCRExecutor
from .orientation_detector import OrientationDetector
from .document_detector import DocumentDetector
from .field_pipeline import FieldPipeline
from .adaptive_region import AdaptiveOCRRegion
from .ocr_scorer import OCRScorer
from .template_field_recognizer import TemplateFieldRecognizer
from core.resource import get_resource_path
from core.error_code import ErrorCode
from core.status import OCRStatus
from core.ocr_result import OCRResult

logger = logging.getLogger("PowerRename.OCR")


class OCREngine:

    def __init__(self):
        self.enabled = True
        self.last_error = ''
        self.error_code = ErrorCode.SUCCESS
        self.status = OCRStatus.INIT
        self.executor = OCRExecutor()

        self.ocr_exe = get_resource_path('engine/tesseract.exe')
        self.tessdata = get_resource_path('engine/tessdata')
        self.ocr_region = self._load_ocr_region()
        self.adaptive_region = AdaptiveOCRRegion()
        self.scorer = OCRScorer()

        self.orientation = OrientationDetector(self.ocr_exe)
        self.document_detector = DocumentDetector()
        self.field_pipeline = FieldPipeline()
        self.template_recognizer = TemplateFieldRecognizer(self.executor)

        self.status = OCRStatus.CHECKING
        self._validate_engine()

        if self.enabled:
            self.status = OCRStatus.READY

    def _load_ocr_region(self):
        default = {'enabled': True, 'top_percent': 28}
        config_path = get_resource_path('config.json')
        try:
            if config_path.exists():
                config = json.loads(config_path.read_text(encoding='utf-8'))
                default.update(config.get('ocr_region', {}))
        except Exception:
            logger.exception('load OCR region config failed')
        return default

    def _validate_engine(self):
        required = [
            self.ocr_exe,
            self.tessdata / 'chi_sim.traineddata',
            self.tessdata / 'eng.traineddata'
        ]
        missing = [str(item) for item in required if not item.exists()]
        if missing:
            self.enabled = False
            self.status = OCRStatus.FAILED
            self.error_code = ErrorCode.ENGINE_MISSING
            self.last_error = 'OCR组件缺失: ' + ', '.join(missing)

    def _parse_tsv(self, tsv_file):
        items = []

        with open(tsv_file, 'r', encoding='utf-8') as file:
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
                    'line': row.get('line_num', '')
                })

        logger.info('[OCR_DATA] box_count=%s', len(items))
        return {
            'items': items,
            'raw_text': self._rebuild_native_text(items)
        }

    @staticmethod
    def _rebuild_native_text(items):
        groups = {}

        for item in items:
            key = (
                item.get('page', ''),
                item.get('block', ''),
                item.get('paragraph', ''),
                item.get('line', '')
            )
            groups.setdefault(key, []).append(item)

        ordered_groups = sorted(
            groups.items(),
            key=lambda pair: (
                min(value.get('y', 0) for value in pair[1]),
                min(value.get('x', 0) for value in pair[1])
            )
        )

        lines = []
        for _, words in ordered_groups:
            words = sorted(words, key=lambda value: value.get('x', 0))
            line = ' '.join(
                value.get('text', '')
                for value in words
                if value.get('text', '')
            ).strip()
            if line:
                lines.append(line)

        return '\n'.join(lines)

    def _recognize_with_region(self, image_path, temp_path, region):
        logger.info('[OCR_REGION] top_percent=%s', region)

        preprocess(str(image_path), str(temp_path), {
            'enabled': True,
            'top_percent': region
        })

        executor_result = self.executor.execute(
            str(temp_path),
            psm=11,
            oem=1,
        )

        if not executor_result['success']:
            return None, executor_result

        parsed = self._parse_tsv(executor_result['tsv_file'])
        pipeline_result = self.field_pipeline.process(parsed['items'])

        native_text = parsed.get('raw_text', '')
        layout_text = pipeline_result.get('layout_text', '')
        parse_text = native_text or layout_text
        fallback = parse_report_text(parse_text)
        coordinate_fields = pipeline_result.get('fields', {})

        fields = {
            'project_name': (
                fallback.get('project_name')
                or coordinate_fields.get('project_name', '')
            ),
            'project_code': (
                fallback.get('project_code')
                or coordinate_fields.get('project_code', '')
            )
        }

        pipeline_result['fields'] = fields
        pipeline_result['items'] = parsed['items']
        pipeline_result['raw_text'] = parse_text
        pipeline_result['layout_text'] = layout_text
        pipeline_result['score'] = self.scorer.score(fields, parse_text)

        logger.info('[OCR_SCORE] %s fields=%s', pipeline_result['score'], fields)
        return pipeline_result, executor_result

    def recognize(self, image_path):
        image_path = Path(image_path)

        if not self.enabled:
            return OCRResult(
                image=str(image_path),
                status=OCRStatus.FAILED,
                error_code=self.error_code,
                error_message=self.last_error
            ).to_dict()

        if not image_path.is_file():
            return OCRResult(
                image=str(image_path),
                status=OCRStatus.FAILED,
                error_code=ErrorCode.IMAGE_PREPROCESS_FAILED,
                error_message='图片文件不存在: ' + str(image_path)
            ).to_dict()

        try:
            template = self.template_recognizer.recognize(image_path)
            report_type = template.get('report_type', '')
            name_candidates = template.get('project_name_candidates', [])
            code_candidates = template.get('project_code_candidates', [])

            template_valid = (
                report_type == 'start' and bool(name_candidates)
            ) or (
                report_type == 'finish'
                and bool(name_candidates or code_candidates)
            )

            if template_valid:
                logger.info(
                    '[TEMPLATE_OCR] type=%s angle=%s names=%s codes=%s',
                    report_type,
                    template.get('rotation_angle', 0),
                    len(name_candidates),
                    len(code_candidates),
                )
                return OCRResult(
                    image=str(image_path),
                    raw_text=template.get('raw_text', ''),
                    items=template.get('items', []),
                    project_name=template.get('project_name', ''),
                    project_code=template.get('project_code', ''),
                    project_name_candidates=name_candidates,
                    project_code_candidates=code_candidates,
                    report_type=report_type,
                    rotation_angle=template.get('rotation_angle', 0),
                    recognition_source=template.get(
                        'recognition_source', 'template_fields'
                    ),
                    status=OCRStatus.FINISHED,
                    error_code=ErrorCode.SUCCESS,
                ).to_dict()

            logger.info('[TEMPLATE_OCR] no reliable fields; legacy fallback')

        except Exception:
            logger.exception('[TEMPLATE_OCR] failed; legacy fallback')

        return self._recognize_legacy(image_path)

    def _recognize_legacy(self, image_path):
        executor_result = None
        temp_path = None

        try:
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp:
                temp_path = Path(temp.name)

            best = None

            for region in self.adaptive_region.candidates():
                pipeline_result, executor_result = self._recognize_with_region(
                    image_path,
                    temp_path,
                    region
                )

                if pipeline_result:
                    if best is None or pipeline_result['score'] > best['score']:
                        best = pipeline_result

                if executor_result:
                    self.executor.cleanup(executor_result)
                    executor_result = None

                fields = pipeline_result.get('fields', {}) if pipeline_result else {}
                if fields.get('project_name') and fields.get('project_code'):
                    break

            if not best:
                return OCRResult(
                    image=str(image_path),
                    status=OCRStatus.FAILED,
                    error_code=ErrorCode.IMAGE_PREPROCESS_FAILED,
                    error_message='未找到有效OCR字段'
                ).to_dict()

            fields = best.get('fields', {})
            text = best.get('raw_text', '') or best.get('layout_text', '')
            parsed = parse_report_text(text)
            name = fields.get('project_name', '')
            code = fields.get('project_code', '')

            return OCRResult(
                image=str(image_path),
                raw_text=text,
                items=best.get('items', []),
                project_name=name,
                project_code=code,
                project_name_candidates=[name] if name else [],
                project_code_candidates=[code] if code else [],
                report_type=(
                    'finish'
                    if code or '竣工验收报告' in ''.join(text.split())
                    else 'start'
                    if '开工报告' in ''.join(text.split())
                    else ''
                ),
                recognition_source='legacy_region',
                status=OCRStatus.FINISHED,
                error_code=ErrorCode.SUCCESS
            ).to_dict()

        except Exception as exc:
            logger.exception('OCR failed: %s', image_path)
            return OCRResult(
                image=str(image_path),
                status=OCRStatus.FAILED,
                error_code=ErrorCode.IMAGE_PREPROCESS_FAILED,
                error_message=str(exc)
            ).to_dict()

        finally:
            if executor_result:
                self.executor.cleanup(executor_result)
            if temp_path and temp_path.exists():
                temp_path.unlink()

    def parse_text(self, text):
        return parse_report_text(text)
