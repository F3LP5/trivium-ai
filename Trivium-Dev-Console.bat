@echo off
setlocal
cd /d "%~dp0"
title Trivium Academy - Modo Depuracao (Logs)

if not exist "%~dp0backend\.venv\Scripts\python.exe" (
    echo [Trivium] Primeira execucao detectada. Preparando ambiente automaticamente...
    call "%~dp0Trivium-Launcher.bat" --setup-only
)
if not exist "%~dp0frontend\node_modules" (
    echo [Trivium] Modulos do frontend ausentes. Preparando...
    call "%~dp0Trivium-Launcher.bat" --setup-only
)

echo ========================================================
echo        TRIVIUM ACADEMY - MODO DESENVOLVEDOR (CONSOLE)
echo ========================================================
echo.
echo Iniciando o Trivium com terminais e logs visiveis...
echo Para fechar todos os servicos, basta fechar esta janela.
echo.

set TRIVIUM_DEBUG=1

if exist "%~dp0dist_desktop\Trivium.exe" (
    "%~dp0dist_desktop\Trivium.exe" --debug
) else (
    if exist "%~dp0backend\.venv\Scripts\python.exe" (
        "%~dp0backend\.venv\Scripts\python.exe" "%~dp0backend\desktop_app.py" --debug
    ) else (
        python "%~dp0backend\desktop_app.py" --debug
    )
)

echo.
echo Sessao de depuracao finalizada.
pause
