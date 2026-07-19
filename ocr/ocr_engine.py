"""
OCR识别引擎接口
Win7兼容版：程序目录内OCR + TSV坐标解析
"""

from pathlib import Path
import subprocess
import os
import tempfile
import csv
import logging

from .text_parser import parse_report_text
from .image_preprocess import preprocess
from core.resource import get_resource_path
from core.error_code import ErrorCode


logger = logging.getLogger(__name__)


class OCREngine:

    def __init__(self):
        self.enabled = True
        self.last_error = ''
        self.error_code = ErrorCode.SUCCESS
        self.status = 'INIT'
        self.ocr_exe = get_resource_path('engine/tesseract.exe')
        self.tessdata = get_resource_path('engine/tessdata')
        self.status = 'CHECKING'
        self._validate_engine()

        if self.enabled:
            self.status = 'READY'

    def _validate_engine(self):
        required_files = [
            self.ocr_exe,
            self.tessdata / 'chi_sim.traineddata',
            self.tessdata / 'eng.traineddata'
        ]

        missing = [str(p) for p in required_files if not p.exists()]

        if missing:
            self.enabled = False
            self.status = 'FAILED'
            self.error_code = ErrorCode.ENGINE_MISSING
            self.last_error = 'OCR组件缺失: ' + ', '.join(missing)
            logger.error('[%s] %s', self.error_code, self.last_error)

    def _parse_tsv(self, tsv_file):
        items = []
        texts = []

        try:
            with open(tsv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter='\t')
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

        except Exception as e:
            self.error_code = ErrorCode.OCR_PARSE_FAILED
            self.last_error = str(e)
            logger.exception('[%s] TSV解析失败', self.error_code)

        return {
            'items': items,
            'raw_text': '\n'.join(texts)
        }

    def _run_ocr(self, image_path):
        if not self.enabled:
            return {'items': [], 'raw_text': ''}

        temp_file = None

        try:
            self.status = 'RUNNING'

            with tempfile.NamedTemporaryFile(delete=False) as f:
                temp_file = f.name

            env = os.environ.copy()
            env['TESSDATA_PREFIX'] = str(self.tessdata)

            result = subprocess.run(
                [
                    str(self.ocr_exe),
                    str(image_path),
                    temp_file,
                    '-l',
                    'chi_sim+eng',
                    'tsv'
                ],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=60
            )

            if result.returncode != 0:
                self.error_code = ErrorCode.OCR_EXEC_FAILED
                error = result.stderr.decode('utf-8', errors='ignore')
                raise RuntimeError(error)

            return self._parse_tsv(temp_file + '.tsv')

        except subprocess.TimeoutExpired:
            self.status = 'FAILED'
            self.error_code = ErrorCode.OCR_TIMEOUT
            self.last_error = 'OCR执行超时'
            logger.error('[%s] %s', self.error_code, self.last_error)
            return {'items': [], 'raw_text': ''}

        except Exception as e:
            self.status = 'FAILED'
            self.last_error = str(e)
            logger.exception('[%s] OCR执行失败', self.error_code)
            return {'items': [], 'raw_text': ''}

        finally:
            if temp_file:
                try:
                    temp = Path(temp_file)
                    if temp.exists():
                        temp.unlink()
                    tsv = Path(temp_file + '.tsv')
                    if tsv.exists():
                        tsv.unlink()
                except Exception:
                    pass

    def recognize(self, image_path):
        image_path = Path(image_path)
        temp_path = image_path.with_name(image_path.stem + '_ocr.jpg')

        try:
            preprocess(str(image_path), str(temp_path))
            ocr_result = self._run_ocr(str(temp_path))
            result = parse_report_text(ocr_result['raw_text'])
            self.status = 'FINISHED'

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

        except Exception as e:
            self.status = 'FAILED'
            self.last_error = str(e)
            logger.exception('识别失败')
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
