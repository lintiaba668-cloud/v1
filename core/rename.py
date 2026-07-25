"""
文件自动命名模块。

规则：
- 开工报告：工程名称.jpg
- 竣工验收报告：工程名称_工程编号.jpg
- 重复文件自动增加 _2、_3
- 输出采用复制，不移动或删除用户原始图片
"""

from pathlib import Path
import shutil


def safe_name(name):
    """清理 Windows 文件名不允许的字符。"""
    value = str(name or '')
    chars = '<>:"/\\|?*'

    for char in chars:
        value = value.replace(char, '')

    # Windows 不允许文件名以空格或句点结尾。
    return value.strip().rstrip('.')


def build_filename(project_name, project_code='', ext='.jpg'):
    project_name = safe_name(project_name)
    project_code = safe_name(project_code)
    extension = str(ext or '.jpg')

    if extension and not extension.startswith('.'):
        extension = '.' + extension

    if project_code:
        filename = project_name + '_' + project_code
    else:
        filename = project_name

    return filename + extension.lower()


def unique_path(folder, filename):
    """处理重复文件名。"""
    target = Path(folder) / filename

    if not target.exists():
        return target

    stem = target.stem
    suffix = target.suffix
    index = 2

    while True:
        new_file = Path(folder) / '{}_{}{}'.format(stem, index, suffix)
        if not new_file.exists():
            return new_file
        index += 1


def rename_file(image_path, output_dir, project_name, project_code=''):
    """复制原图到输出目录并使用标准名称，保留原始文件。"""
    image_path = Path(image_path)

    if not image_path.is_file():
        raise FileNotFoundError('原始图片不存在: ' + str(image_path))

    filename = build_filename(
        project_name,
        project_code,
        image_path.suffix
    )

    target = unique_path(output_dir, filename)
    target.parent.mkdir(parents=True, exist_ok=True)

    shutil.copy2(str(image_path), str(target))
    return target
