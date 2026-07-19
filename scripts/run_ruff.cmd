@echo off
setlocal
cd /d "%~dp0.."
where python >nul 2>&1
if not errorlevel 1 (
    set "PYTHON=python"
) else (
    set "PYTHON=py -3"
)
%PYTHON% -m ruff check . --config ruff.toml
set "RESULT=%errorlevel%"
echo.
if not "%RESULT%"=="0" echo Ruff found problems. Exit code %RESULT%.
pause
exit /b %RESULT%
