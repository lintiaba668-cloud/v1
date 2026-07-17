"""
输出完成提示模块
"""


class OutputInfo:
    def __init__(self, folder):
        self.folder = folder

    def message(self):
        return f'处理完成，输出目录：{self.folder}'
