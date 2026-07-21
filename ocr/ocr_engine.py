"""
OCR识别引擎接口
Win7兼容版：程序目录内OCR + TSV坐标解析
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

        self.orientation = OrientationDetector(self.ocr_exe)
        self.document_detector = DocumentDetector()
        self.field_pipeline = FieldPipeline()

        self.status = OCRStatus.CHECKING
        self._validate_engine()

        if self.enabled:
            self.status = OCRStatus.READY

    def _load_ocr_region(self):
        default = {'enabled': True, 'top_percent': 25}
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
        texts = []

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
                        'h': int(row.get('height', 0))
                    })
                    texts.append(text)

        logger.info('[OCR_DATA] box_count=%s', len(items))

        return {'items': items, 'raw_text': '\n'.join(texts)}

    def _recognize_with_region(self, image_path, temp_path, region):
        logger.info('[OCR_REGION] top_percent=%s', region)

        preprocess(str(image_path), str(temp_path), {
            'enabled': True,
            'top_percent': region
        })

        executor_result = self.executor.execute(str(temp_path))

        if not executor_result['success']:
            return None, executor_result

        parsed = self._parse_tsv(executor_result['tsv_file'])

        logger.info('[FIELD] input_boxes=%s', len(parsed['items']))

        pipeline_result = self.field_pipeline.process(parsed['items'])

        fields = pipeline_result.get('fields', {})
        logger.info(
            '[FIELD] project_name=%s project_code=%s',
            fields.get('project_name', ''),
            fields.get('project_code', '')
        )

        return pipeline_result, executor_result

    def recognize(self, image_path):
        image_path = Path(image_path)
        executor_result = None
        temp_path = None

        try:
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp:
                temp_path = Path(temp.name)

            final_pipeline = None

            for region in self.adaptive_region.candidates():
                pipeline_result, executor_result = self._recognize_with_region(
                    image_path,
                    temp_path,
                    region
                )

                if pipeline_result:
                    fields = pipeline_result.get('fields', {})
                    if not self.adaptive_region.need_expand(fields):
                        final_pipeline = pipeline_result
                        break

                if executor_result:
                    self.executor.cleanup(executor_result)
                    executor_result = None

            if not final_pipeline:
                return OCRResult(
                    image=str(image_path),
                    status=OCRStatus.FAILED,
                    error_code=ErrorCode.IMAGE_PREPROCESS_FAILED,
                    error_message='未找到有效OCR字段'
                ).to_dict()

            fields = final_pipeline.get('fields', {})
            fallback = parse_report_text(final_pipeline['layout_text'])

            return OCRResult(
                image=str(image_path),
                raw_text=final_pipeline['layout_text'],
                project_name=fields.get('project_name') or fallback.get('project_name', ''),
                project_code=fields.get('project_code') or fallback.get('project_code', ''),
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
