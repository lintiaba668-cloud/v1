@echo off
chcp 65001 >nul

echo ===============================
echo PowerRename Win7 Build
echo ===============================

echo.
echo Step 1: Build check
python build_check.py

if %errorlevel% neq 0 (
    echo.
    echo Build check failed.
    pause
    exit /b 1
)

echo.
echo Step 2: Install requirements
python -m pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo Requirements install failed.
    pause
    exit /b 1
)

echo.
echo Step 3: PyInstaller build
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
