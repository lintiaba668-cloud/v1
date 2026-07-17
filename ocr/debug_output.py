"""
OCR调试输出
用于查看识别原文
"""

from pathlib import Path


def save_text(image, text, folder='ocr_debug'):
    folder = Path(folder)
    folder.mkdir(exist_ok=True)

    file = folder / (Path(image).stem + '.txt')
    file.write_text(text, encoding='utf-8')

    return file
