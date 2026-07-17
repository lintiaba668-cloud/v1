"""
启动环境检查
"""


def check_environment():
    result = {
        'python': True,
        'ocr': False,
        'gui': False
    }

    try:
        import PySide6
        result['gui'] = True
    except Exception:
        pass

    try:
        import paddleocr
        result['ocr'] = True
    except Exception:
        pass

    return result
