# -*- coding: utf-8 -*-

"""OCR result data object with dictionary compatibility."""


class OCRResult:

    def __init__(
        self,
        image='',
        raw_text='',
        items=None,
        project_name='',
        project_code='',
        project_name_candidates=None,
        project_code_candidates=None,
        report_type='',
        rotation_angle=0,
        recognition_source='',
        status='',
        error_code=0,
        error_message=''
    ):
        self.image = image
        self.raw_text = raw_text
        self.items = items or []
        self.project_name = project_name
        self.project_code = project_code
        self.project_name_candidates = project_name_candidates or []
        self.project_code_candidates = project_code_candidates or []
        self.report_type = report_type
        self.rotation_angle = rotation_angle
        self.recognition_source = recognition_source
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
            'project_name_candidates': self.project_name_candidates,
            'project_code_candidates': self.project_code_candidates,
            'report_type': self.report_type,
            'rotation_angle': self.rotation_angle,
            'recognition_source': self.recognition_source,
            'status': self.status,
            'error_code': self.error_code,
            'error_message': self.error_message
        }
