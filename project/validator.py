# -*- coding: utf-8 -*-
"""
Project import data validator.

Validate Excel imported project records before saving into database.
"""

import re


class ProjectValidator:

    def validate(self, project_code, project_name):
        errors = []

        if not project_name:
            errors.append('工程名称为空')

        if project_code:
            if not re.match(r'^[A-Za-z0-9#-]+$', str(project_code)):
                errors.append('工程编号格式异常')

        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
