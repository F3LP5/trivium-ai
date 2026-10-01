@echo off
setlocal
cd /d "%~dp0"
title Trivium Academy - Launcher

REM Executa a preparacao e configuracao autonoma
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0assets\bootstrap.ps1"
if %errorlevel% neq 0 (
    echo.
    echo [ERRO] Falha durante a verificacao do ambiente.
    pause
    exit /b 1
)

if "%1"=="--setup-only" (
    exit /b 0
)

echo.
echo [Trivium] Inicializando aplicativo...
echo.

if exist "%~dp0dist_desktop\Trivium.exe" (
    start "" "%~dp0dist_desktop\Trivium.exe" %*
    exit /b 0
)

if exist "%~dp0backend\.venv\Scripts\pythonw.exe" (
    start "" "%~dp0backend\.venv\Scripts\pythonw.exe" "%~dp0backend\desktop_app.py" %*
) else (
    start "" python "%~dp0backend\desktop_app.py" %*
)

exit /b 0
