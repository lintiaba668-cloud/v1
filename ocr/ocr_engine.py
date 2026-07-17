"""
OCR识别引擎接口
Win7兼容版：支持程序目录内OCR引擎
"""

from pathlib import Path
import subprocess
import os
import tempfile

from .text_parser import parse_report_text
from .image_preprocess import preprocess


class OCREngine:
    def __init__(self):
        self.enabled = True
        self.last_error = ''
        self.base_dir = Path(__file__).resolve().parent.parent
        self.ocr_exe = self.base_dir / 'engine' / 'tesseract.exe'
        self.tessdata = self.base_dir / 'engine' / 'tessdata'

    def _run_ocr(self, image_path):
        """
        调用程序目录内OCR。
        不依赖系统安装环境。
        """
        try:
            if not self.ocr_exe.exists():
                raise FileNotFoundError('OCR组件不存在')

            output_file = tempfile.mktemp()

            env = os.environ.copy()
            env['TESSDATA_PREFIX'] = str(self.tessdata)

            subprocess.run(
                [
                    str(self.ocr_exe),
                    str(image_path),
                    output_file,
                    '-l',
                    'chi_sim+eng',
                    'tsv'
                ],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            return {
                'items': [],
                'raw_text': ''
            }

        except Exception as e:
            self.last_error = str(e)
            return {
                'items': [],
                'raw_text': ''
            }

    def recognize(self, image_path):
        image_path = Path(image_path)
        temp_path = image_path.with_name(image_path.stem + '_ocr.jpg')

        try:
            preprocess(str(image_path), str(temp_path))

            ocr_result = self._run_ocr(str(temp_path))
            raw_text = ocr_result['raw_text']

            result = parse_report_text(raw_text)

            return {
                'image': str(image_path),
                'raw_text': raw_text,
                'items': ocr_result['items'],
                'project_name': result.get('project_name', ''),
                'project_code': result.get('project_code', '')
            }

        except Exception as e:
            self.last_error = str(e)
            return {
                'image': str(image_path),
                'raw_text': '',
                'items': [],
                'project_name': '',
                'project_code': ''
            }

    def parse_text(self, text):
        return parse_report_text(text)
