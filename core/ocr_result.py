# -*- coding: utf-8 -*-

"""OCR result data object.

Internal structured result container while keeping dictionary compatibility.
"""


class OCRResult:

    def __init__(
        self,
        image='',
        raw_text='',
        items=None,
        project_name='',
        project_code='',
        status='',
        error_code=0,
        error_message=''
    ):
        self.image = image
        self.raw_text = raw_text
        self.items = items or []
        self.project_name = project_name
        self.project_code = project_code
        self.status = status
        self.error_code = error_code
        self.error_message = error_message

    def to_dict(self):
        return {
            'image': self.image,
            'raw_text': self.raw_text,
            'items': self.items,
            'project_name': self.project_name,
            'project_code': self.project_code,
            'status': self.status,
            'error_code': self.error_code,
            'error_message': self.error_message
        }
