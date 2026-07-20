"""
OCR识别引擎接口
Win7兼容版：程序目录内OCR + TSV坐标解析
"""

from pathlib import Path
import csv
import logging

from .text_parser import parse_report_text
from .image_preprocess import preprocess
from .ocr_executor import OCRExecutor
from core.resource import get_resource_path
from core.error_code import ErrorCode


logger = logging.getLogger("PowerRename.OCR")


class OCREngine:

    def __init__(self):
        self.enabled = True
        self.last_error = ''
        self.error_code = ErrorCode.SUCCESS
        self.status = 'INIT'

        self.executor = OCRExecutor()

        self.ocr_exe = get_resource_path(
            'engine/tesseract.exe'
        )

        self.tessdata = get_resource_path(
            'engine/tessdata'
        )

        self.status = 'CHECKING'
        self._validate_engine()

        if self.enabled:
            self.status = 'READY'

    def _validate_engine(self):
        required = [
            self.ocr_exe,
            self.tessdata / 'chi_sim.traineddata',
            self.tessdata / 'eng.traineddata'
        ]

        missing = [
            str(item)
            for item in required
            if not item.exists()
        ]

        if missing:
            self.enabled = False
            self.status = 'FAILED'
            self.error_code = ErrorCode.ENGINE_MISSING
            self.last_error = 'OCR组件缺失: ' + ', '.join(missing)
            logger.error(
                '[%s] %s',
                self.error_code,
                self.last_error
            )

    def _parse_tsv(self, tsv_file):
        items = []
        texts = []

        try:
            with open(
                tsv_file,
                'r',
                encoding='utf-8'
            ) as file:

                reader = csv.DictReader(
                    file,
                    delimiter='\t'
                )

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

        except Exception as exc:
            self.error_code = ErrorCode.OCR_PARSE_FAILED
            self.last_error = str(exc)
            logger.exception(
                '[%s] TSV解析失败',
                self.error_code
            )

        return {
            'items': items,
            'raw_text': '\n'.join(texts)
        }

    def _run_ocr(self, image_path):

        if not self.enabled:
            return {
                'items': [],
                'raw_text': ''
            }

        self.status = 'RUNNING'

        result = self.executor.execute(
            image_path
        )

        if not result['success']:
            self.status = 'FAILED'
            self.error_code = result['error_code']
            self.last_error = result['error_message']

            return {
                'items': [],
                'raw_text': ''
            }

        self.status = 'FINISHED'

        return self._parse_tsv(
            result['tsv_file']
        )

    def recognize(self, image_path):

        image_path = Path(image_path)
        temp_path = image_path.with_name(
            image_path.stem + '_ocr.jpg'
        )

        try:
            preprocess(
                str(image_path),
                str(temp_path)
            )

            ocr_result = self._run_ocr(
                str(temp_path)
            )

            result = parse_report_text(
                ocr_result['raw_text']
            )

            return {
                'image': str(image_path),
                'raw_text': ocr_result['raw_text'],
                'items': ocr_result['items'],
                'project_name': result.get('project_name', ''),
                'project_code': result.get('project_code', ''),
                'status': self.status,
                'error_code': self.error_code,
                'error_message': self.last_error
            }

        except Exception as exc:
            self.status = 'FAILED'
            self.last_error = str(exc)

            logger.exception(
                '识别失败'
            )

            return {
                'image': str(image_path),
                'raw_text': '',
                'items': [],
                'project_name': '',
                'project_code': '',
                'status': self.status,
                'error_code': self.error_code,
                'error_message': self.last_error
            }

    def parse_text(self, text):
        return parse_report_text(text)
