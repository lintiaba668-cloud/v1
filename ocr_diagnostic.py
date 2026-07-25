# -*- coding: utf-8 -*-
"""Batch OCR diagnostic tool.

Usage:
    python ocr_diagnostic.py "D:\\报告图片文件夹"

Outputs:
    logs/ocr_diagnostic.csv
"""

import csv
import sys
from pathlib import Path

from ocr.pipeline_ocr import OCRPipeline


SUPPORTED = {'.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff'}


def collect_images(path):
    path = Path(path)

    if path.is_file() and path.suffix.lower() in SUPPORTED:
        return [path]

    if path.is_dir():
        return sorted(
            item for item in path.rglob('*')
            if item.is_file() and item.suffix.lower() in SUPPORTED
        )

    return []


def run(source):
    files = collect_images(source)

    if not files:
        print('没有找到可识别的图片:', source)
        return 2

    pipeline = OCRPipeline()
    rows = []

    for index, image in enumerate(files, 1):
        print('[{}/{}] {}'.format(index, len(files), image.name))
        result = pipeline.process(image)
        data = result.get('data', {})

        row = {
            '文件': str(image),
            '报告类型': data.get('report_type', ''),
            '旋转角度': data.get('rotation_angle', 0),
            '识别来源': data.get('source', ''),
            '工程名称': data.get('project_name', ''),
            '工程编号': data.get('project_code', ''),
            '名称候选': ' || '.join(
                data.get('project_name_candidates', [])
            ),
            '编号候选': ' || '.join(
                data.get('project_code_candidates', [])
            ),
            '有效': result.get('valid', False),
            '错误': result.get('error', ''),
        }
        rows.append(row)

        print('  类型:', row['报告类型'])
        print('  旋转:', row['旋转角度'])
        print('  名称:', row['工程名称'])
        print('  编号:', row['工程编号'])
        print('  有效:', row['有效'])
        if row['错误']:
            print('  错误:', row['错误'])

    output = Path('logs/ocr_diagnostic.csv')
    output.parent.mkdir(parents=True, exist_ok=True)

    with output.open('w', newline='', encoding='utf-8-sig') as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print('\n诊断结果已保存:', output.resolve())
    print('字段裁切调试图目录:', Path('logs/template_ocr').resolve())
    return 0


if __name__ == '__main__':
    if len(sys.argv) >= 2:
        source_path = sys.argv[1]
    else:
        source_path = input('请输入图片或文件夹路径\n> ').strip().strip('"')

    raise SystemExit(run(source_path))
