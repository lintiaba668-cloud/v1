"""
OCR识别引擎接口
Win7兼容版：程序目录内OCR + TSV坐标解析
"""

from pathlib import Path
import csv
import logging
import tempfile
import shutil

from .text_parser import parse_report_text
from .image_preprocess import preprocess
from .ocr_executor import OCRExecutor
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

        self.status = OCRStatus.CHECKING
        self._validate_engine()

        if self.enabled:
            self.status = OCRStatus.READY

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
            logger.error(self.last_error)

    def _parse_tsv(self, tsv_file):
        items = []
        texts = []

        try:
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
                            'block': row.get('block_num', ''),
                            'paragraph': row.get('par_num', ''),
                            'line': row.get('line_num', '')
                        })
                        texts.append(text)

        except Exception as exc:
            self.error_code = ErrorCode.OCR_PARSE_FAILED
            self.last_error = str(exc)
            logger.exception('[%s] TSV解析失败', self.error_code)

        return {
            'items': items,
            'raw_text': '\n'.join(texts)
        }

    def recognize(self, image_path):
        image_path = Path(image_path)
        executor_result = None
        temp_path = None

        try:
            with tempfile.NamedTemporaryFile(
                suffix='.jpg',
                delete=False
            ) as temp:
                temp_path = Path(temp.name)

            logger.info('OCR start: %s', image_path)

            preprocess(str(image_path), str(temp_path))

            executor_result = self.executor.execute(str(temp_path))

            if not executor_result['success']:
                return OCRResult(
                    image=str(image_path),
                    status=OCRStatus.FAILED,
                    error_code=executor_result['error_code'],
                    error_message=executor_result['error_message']
                ).to_dict()

            parsed = self._parse_tsv(executor_result['tsv_file'])
            report = parse_report_text(parsed['raw_text'])

            return OCRResult(
                image=str(image_path),
                raw_text=parsed['raw_text'],
                items=parsed['items'],
                project_name=report.get('project_name', ''),
                project_code=report.get('project_code', ''),
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
