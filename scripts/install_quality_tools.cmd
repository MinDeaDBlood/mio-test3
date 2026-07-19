@echo off
setlocal
cd /d "%~dp0.."
where python >nul 2>&1
if not errorlevel 1 (
    set "PYTHON=python"
) else (
    set "PYTHON=py -3"
)
%PYTHON% -m pip install -r requirements-quality.txt
set "RESULT=%errorlevel%"
echo.
if not "%RESULT%"=="0" echo Installation failed with code %RESULT%.
pause
exit /b %RESULT%
