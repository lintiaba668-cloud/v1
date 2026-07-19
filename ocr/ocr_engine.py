"""
OCR识别引擎接口
Win7兼容版：程序目录内OCR + TSV坐标解析
"""

from pathlib import Path
import subprocess
import os
import tempfile
import csv

from .text_parser import parse_report_text
from .image_preprocess import preprocess
from core.resource import get_resource_path


class OCREngine:
    def __init__(self):
        self.enabled = True
        self.last_error = ''
        self.ocr_exe = get_resource_path('engine/tesseract.exe')
        self.tessdata = get_resource_path('engine/tessdata')

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
            self.last_error = str(e)

        return {
            'items': items,
            'raw_text': '\n'.join(texts)
        }

    def _run_ocr(self, image_path):
        try:
            if not self.ocr_exe.exists():
                raise FileNotFoundError('OCR组件不存在')

            output_file = tempfile.mktemp()
            tsv_file = output_file + '.tsv'

            env = os.environ.copy()
            env['TESSDATA_PREFIX'] = str(self.tessdata)

            subprocess.run([
                str(self.ocr_exe),
                str(image_path),
                output_file,
                '-l',
                'chi_sim+eng',
                'tsv'
            ], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            return self._parse_tsv(tsv_file)

        except Exception as e:
            self.last_error = str(e)
            return {'items': [], 'raw_text': ''}

    def recognize(self, image_path):
        image_path = Path(image_path)
        temp_path = image_path.with_name(image_path.stem + '_ocr.jpg')

        try:
            preprocess(str(image_path), str(temp_path))
            ocr_result = self._run_ocr(str(temp_path))
            result = parse_report_text(ocr_result['raw_text'])

            return {
                'image': str(image_path),
                'raw_text': ocr_result['raw_text'],
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
