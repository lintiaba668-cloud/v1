"""
文件自动命名模块
规则：工程名称+工程编号
无编号：工程名称
重复自动增加序号
"""

from pathlib import Path


def safe_name(name):
    """清理Windows不允许字符"""
    chars = '<>:"/\\|?*'
    for c in chars:
        name = name.replace(c, '')
    return name.strip()


def build_filename(project_name, project_code='', ext='.jpg'):
    project_name = safe_name(project_name)
    project_code = safe_name(project_code)

    if project_code:
        filename = project_name + project_code
    else:
        filename = project_name

    return filename + ext


def unique_path(folder, filename):
    """处理重复文件名"""
    target = Path(folder) / filename

    if not target.exists():
        return target

    stem = target.stem
    suffix = target.suffix
    index = 2

    while True:
        new_file = Path(folder) / f'{stem}_{index}{suffix}'
        if not new_file.exists():
            return new_file
        index += 1


def rename_file(image_path, output_dir, project_name, project_code=''):
    image_path = Path(image_path)
    filename = build_filename(
        project_name,
        project_code,
        image_path.suffix
    )

    target = unique_path(output_dir, filename)
    target.parent.mkdir(parents=True, exist_ok=True)

    image_path.rename(target)

    return target
