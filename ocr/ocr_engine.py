"""
OCR识别引擎接口
优化版：OCR文字+坐标输出，支持字段区域定位
"""

from pathlib import Path

from .text_parser import parse_report_text
from .image_preprocess import preprocess


class OCREngine:
    def __init__(self):
        self.enabled = True
        self.last_error = ''

    def _run_ocr(self, image_path):
        """
        返回OCR文字及坐标。
        优先使用image_to_data。
        """
        try:
            import pytesseract
            from PIL import Image

            data = pytesseract.image_to_data(
                Image.open(image_path),
                lang='chi_sim+eng',
                output_type=pytesseract.Output.DICT
            )

            items = []
            texts = []

            count = len(data['text'])
            for i in range(count):
                text = data['text'][i].strip()
                conf = data['conf'][i]

                if text and str(conf) != '-1':
                    items.append({
                        'text': text,
                        'x': data['left'][i],
                        'y': data['top'][i],
                        'w': data['width'][i],
                        'h': data['height'][i]
                    })
                    texts.append(text)

            return {
                'items': items,
                'raw_text': '\n'.join(texts)
            }

        except Exception as e:
            self.last_error = str(e)
            return {
                'items': [],
                'raw_text': ''
            }

    def recognize(self, image_path):
        """
        图片预处理 -> OCR坐标识别 -> 字段解析
        """
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
