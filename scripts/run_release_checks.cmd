@echo off
setlocal
cd /d "%~dp0.."
where python >nul 2>&1
if not errorlevel 1 (
    set "PYTHON=python"
) else (
    set "PYTHON=py -3"
)
%PYTHON% scripts\manual\manual_release_preflight.py --skip-install
set "RESULT=%errorlevel%"
echo.
if not "%RESULT%"=="0" echo Release checks failed with code %RESULT%.
pause
exit /b %RESULT%
