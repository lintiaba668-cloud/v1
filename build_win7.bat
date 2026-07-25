@echo off
setlocal
chcp 65001 >nul

for /f "delims=" %%i in ('python -c "import sys; print(str(sys.version_info[0])+'.'+str(sys.version_info[1]))"') do set PYVER=%%i
for /f "delims=" %%i in ('python -c "import struct; print('x64' if struct.calcsize('P')*8==64 else 'x86')"') do set ARCH=%%i

if not "%PYVER%"=="3.8" (
    echo ERROR: Win7 release must be built with Python 3.8.
    echo Current Python: %PYVER%
    pause
    exit /b 1
)

set RELEASE_NAME=PowerRename_Win7_%ARCH%

echo ==========================================
echo PowerRename Win7 Portable Build
ECHO Python: %PYVER%
echo Architecture: %ARCH%
echo Output: release\%RELEASE_NAME%
echo ==========================================

echo.
echo Step 1: Build environment check
python build_check.py
if %errorlevel% neq 0 (
    echo Build check failed.
    pause
    exit /b 1
)

echo.
echo Step 2: Install pinned Win7 requirements
python -m pip install -r requirements-win7.txt
if %errorlevel% neq 0 (
    echo Requirements install failed.
    pause
    exit /b 1
)

echo.
echo Step 3: Run automated tests
python -m pytest -q
if %errorlevel% neq 0 (
    echo Tests failed. Build stopped.
    pause
    exit /b 1
)

echo.
echo Step 4: Clean previous build
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo.
echo Step 5: PyInstaller onedir build
python -m PyInstaller --clean --noconfirm build_win7.spec
if %errorlevel% neq 0 (
    echo PyInstaller build failed.
    pause
    exit /b 1
)

if not exist dist\PowerRename\PowerRename.exe (
    echo EXE not found: dist\PowerRename\PowerRename.exe
    pause
    exit /b 1
)

if not exist release mkdir release
if exist release\%RELEASE_NAME% rmdir /s /q release\%RELEASE_NAME%
move dist\PowerRename release\%RELEASE_NAME% >nul

if not exist release\%RELEASE_NAME%\PowerRename.exe (
    echo Release move failed.
    pause
    exit /b 1
)

echo.
echo Build success.
echo Output: release\%RELEASE_NAME%
echo Copy the whole folder to the target computer.
pause
endlocal
