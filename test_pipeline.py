"""
PowerRename OCR流程测试
测试：图片 -> OCR -> 工程名称/编号解析
"""

from ocr.pipeline_ocr import OCRPipeline


def test_image(path):
    pipeline = OCRPipeline()

    result = pipeline.process(path)

    print('==============================')
    print('OCR TEST RESULT')
    print('==============================')
    print('文件:', path)
    print('工程名称:', result['data'].get('project_name', ''))
    print('工程编号:', result['data'].get('project_code', ''))
    print('有效:', result.get('valid'))


if __name__ == '__main__':
    print('请输入测试图片路径')
    image = input('> ').strip()
    test_image(image)
