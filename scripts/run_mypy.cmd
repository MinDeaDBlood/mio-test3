@echo off
setlocal
cd /d "%~dp0.."
where python >nul 2>&1
if not errorlevel 1 (
    set "PYTHON=python"
) else (
    set "PYTHON=py -3"
)
%PYTHON% scripts\quality\check_typed_boundaries.py
set "RESULT=%errorlevel%"
echo.
if not "%RESULT%"=="0" echo Mypy found problems. Exit code %RESULT%.
pause
exit /b %RESULT%
