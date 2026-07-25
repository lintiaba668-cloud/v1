"""
PowerRename OCR流程测试。
测试：图片 -> OCR -> 工程名称/编号解析。
"""

from pathlib import Path

from ocr.pipeline_ocr import OCRPipeline


def test_image(path):
    image_path = Path(str(path).strip().strip('"'))

    if not image_path.is_file():
        print('测试图片不存在:', image_path)
        print('请核对完整文件名；例如 .jpg 和 .jpg.jpg 是两个不同路径。')
        return 2

    pipeline = OCRPipeline()
    result = pipeline.process(image_path)

    print('==============================')
    print('OCR TEST RESULT')
    print('==============================')
    print('文件:', image_path)

    data = result.get('data', {})
    print('报告类型:', data.get('report_type', ''))
    print('工程名称:', data.get('project_name', ''))
    print('工程编号:', data.get('project_code', ''))
    print('有效:', result.get('valid'))
    print('错误:', result.get('error', ''))

    print('\n----- OCR原始文字 -----')
    print(result.get('text', ''))

    print('\n----- 坐标识别结果 -----')
    items = result.get('items', [])
    for item in items:
        print(
            item.get('text', ''),
            'x=', item.get('x', 0),
            'y=', item.get('y', 0),
            'w=', item.get('w', 0),
            'h=', item.get('h', 0)
        )

    return 0 if result.get('valid') else 1


if __name__ == '__main__':
    print('请输入测试图片路径')
    image = input('> ').strip()
    raise SystemExit(test_image(image))
