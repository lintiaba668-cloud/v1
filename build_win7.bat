@echo off
chcp 65001 >nul

echo ===============================
echo PowerRename Win7 Build
echo ===============================

python -m pip install -r requirements.txt

python -m PyInstaller build_win7.spec

if %errorlevel%==0 (
    echo.
    echo Build success.
    echo Output: dist\PowerRename
) else (
    echo.
    echo Build failed.
)

pause
