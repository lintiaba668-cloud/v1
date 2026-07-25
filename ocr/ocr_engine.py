"""
OCR识别引擎接口。
Win7兼容版：程序目录内 Tesseract + TSV 坐标解析。
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
                conf = row.get('conf', '-1')
                if text and conf != '-1':
                    items.append({
                        'text': text,
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
        """按 Tesseract TSV 原生 block/paragraph/line 重建文本。

        这条文本用于字段解析；现有 TextLayout 仍保留给坐标定位模块使用。
        """
        groups = {}

        for item in items:
            key = (
                item.get('page', ''),
                item.get('block', ''),
                item.get('paragraph', ''),
                item.get('line', ''),
                item.get('y', 0)
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

        executor_result = self.executor.execute(str(temp_path), psm=11)

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
        executor_result = None
        temp_path = None

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

            return OCRResult(
                image=str(image_path),
                raw_text=text,
                items=best.get('items', []),
                project_name=fields.get('project_name', ''),
                project_code=fields.get('project_code', ''),
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
