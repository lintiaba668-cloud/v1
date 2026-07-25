"""
PowerRename V1 program entry.
Win7 compatible portable production startup.
"""

import os
import sys
import traceback

from PyQt5.QtWidgets import QApplication, QMessageBox

from core.logger import init_logger, get_logger
from core.resource import get_base_path
from core.startup_check import StartupCheck
from ui.main_window_v3 import MainWindowV3


logger = get_logger('main')


def show_error(title, message):
    QMessageBox.critical(None, title, message)


def format_startup_errors(errors):
    lines = []

    for item in errors or []:
        if isinstance(item, dict):
            code = item.get('code', '')
            message = item.get('message', '')
            detail = item.get('detail', '')
            text = '[{}] {}'.format(code, message) if code else str(message)
            if detail:
                text += '\n' + str(detail)
            lines.append(text)
        else:
            lines.append(str(item))

    return '\n\n'.join(lines)


def startup():
    # Portable mode: all relative output/temp paths are anchored beside the EXE.
    os.chdir(str(get_base_path()))

    init_logger()
    logger.info('PowerRename starting')

    app = QApplication(sys.argv)

    try:
        check = StartupCheck()
        result = check.run()

        if not result['ok']:
            logger.error(
                'Startup check failed: %s',
                result['errors']
            )

            show_error(
                '运行环境检查失败',
                format_startup_errors(result['errors'])
            )
            return 1

        logger.info('Startup check passed')

        window = MainWindowV3()
        window.show()

        logger.info('UI started')
        return app.exec_()

    except Exception:
        error = traceback.format_exc()
        logger.exception('Startup exception')

        show_error(
            '程序启动异常',
            '程序启动失败，请查看logs目录。\n\n' + error
        )
        return 1


if __name__ == '__main__':
    sys.exit(startup())
