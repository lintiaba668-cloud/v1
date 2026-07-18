"""
PowerRename OCR流程测试
测试：图片 -> OCR -> 工程名称/编号解析
增强调试版
"""

from ocr.pipeline_ocr import OCRPipeline


def test_image(path):
    pipeline = OCRPipeline()

    result = pipeline.process(path)

    print('==============================')
    print('OCR TEST RESULT')
    print('==============================')

    print('文件:', path)

    data = result.get('data', {})
    print('工程名称:', data.get('project_name', ''))
    print('工程编号:', data.get('project_code', ''))
    print('有效:', result.get('valid'))

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


if __name__ == '__main__':
    print('请输入测试图片路径')
    image = input('> ').strip()
    test_image(image)
