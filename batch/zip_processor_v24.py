"""
V2.4 批量ZIP处理模块
支持批量图片解析和输出结果
"""

import os
import zipfile
import shutil


def extract_zip(zip_path, output_dir):
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)

    os.makedirs(output_dir, exist_ok=True)

    with zipfile.ZipFile(zip_path, 'r') as z:
        z.extractall(output_dir)

    return output_dir


def collect_images(folder):
    images = []

    for root, _, files in os.walk(folder):
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                images.append(os.path.join(root, file))

    return images
