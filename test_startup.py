"""
PowerRename 启动环境测试
用于打包前检查Win7兼容运行条件
"""

from core.startup_check import StartupCheck


def main():
    print('PowerRename startup test')
    print('-' * 30)

    check = StartupCheck()
    result = check.run()

    if result['ok']:
        print('OK: 环境检查通过')
    else:
        print('FAILED:')
        for error in result['errors']:
            print('-', error)


if __name__ == '__main__':
    main()
