@echo off
chcp 65001 >nul
title Trivium Academy - Modo Depuração & Logs
cd /d "%~dp0"

echo ========================================================
echo        TRIVIUM ACADEMY - MODO DESENVOLVEDOR (CONSOLE)
echo ========================================================
echo.
echo Iniciando o Trivium com terminais e logs visiveis...
echo Para fechar todos os servicos, basta fechar a janela principal do Trivium.
echo.

set TRIVIUM_DEBUG=1

if exist "dist_desktop\Trivium.exe" (
    "dist_desktop\Trivium.exe" --debug
) else (
    if exist "backend\.venv\Scripts\python.exe" (
        "backend\.venv\Scripts\python.exe" "backend\desktop_app.py" --debug
    ) else (
        uv run python "backend\desktop_app.py" --debug
    )
)

echo.
echo Sessao de depuracao finalizada.
pause
