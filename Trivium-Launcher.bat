@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Trivium Academy - Setup & Launcher

REM ========================================================
REM 1. Criação automática do atalho oficial "Trivium" na Área de Trabalho
REM ========================================================
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0assets\create_shortcut.ps1" >nul 2>&1

REM ========================================================
REM 2. Verificação e Instalação Autônoma do Node.js
REM ========================================================
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ========================================================
    echo   [Trivium] Node.js não foi detectado no sistema.
    echo   Iniciando instalação inteligente automática...
    echo ========================================================
    echo.
    
    REM Tenta instalar silenciosamente via Windows Package Manager (winget)
    where winget >nul 2>&1
    if %errorlevel% equ 0 (
        echo Baixando e instalando Node.js LTS via winget...
        winget install OpenJS.NodeJS.LTS --silent --accept-package-agreements --accept-source-agreements
        REM Atualiza PATH na sessão atual
        for /f "tokens=*" %%P in ('powershell -NoProfile -Command "[Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [Environment]::GetEnvironmentVariable('Path', 'User')"') do set "PATH=%%P"
    )

    REM Se ainda assim não estiver no PATH, baixa o instalador oficial MSI
    where node >nul 2>&1
    if %errorlevel% neq 0 (
        echo Baixando instalador oficial do Node.js LTS...
        powershell -NoProfile -Command "Invoke-WebRequest -Uri 'https://nodejs.org/dist/v20.18.0/node-v20.18.0-x64.msi' -OutFile '$env:TEMP\nodejs-installer.msi'"
        echo Executando instalador do Node.js...
        msiexec /i "%TEMP%\nodejs-installer.msi" /passive
        REM Recarrega o PATH do sistema
        for /f "tokens=*" %%P in ('powershell -NoProfile -Command "[Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [Environment]::GetEnvironmentVariable('Path', 'User')"') do set "PATH=%%P"
    )

    where node >nul 2>&1
    if %errorlevel% neq 0 (
        echo.
        echo [AVISO] O instalador do Node.js foi concluído.
        echo Por favor, reinicie este script (Trivium-Launcher.bat) para carregar o novo ambiente.
        pause
        exit /b 0
    )
    echo [OK] Node.js instalado com sucesso!
)

REM ========================================================
REM 3. Verificação e Instalação Autônoma do Python / UV
REM ========================================================
set "NEED_PYTHON=0"
if not exist "backend\.venv\Scripts\python.exe" (
    where uv >nul 2>&1
    if %errorlevel% neq 0 (
        where python >nul 2>&1
        if %errorlevel% neq 0 (
            set "NEED_PYTHON=1"
        )
    )
)

if "%NEED_PYTHON%"=="1" (
    echo.
    echo ========================================================
    echo   [Trivium] Python não foi detectado no sistema.
    echo   Configurando gerenciador portátil de alta velocidade (uv)...
    echo ========================================================
    echo.
    powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"
    set "PATH=%USERPROFILE%\.local\bin;%USERPROFILE%\.cargo\bin;%PATH%"
)

REM Prepara o ambiente virtual do backend se ainda não existir
if not exist "backend\.venv" (
    echo.
    echo [Trivium] Configurando ambiente virtual Python (3.12)...
    cd /d "%~dp0backend"
    where uv >nul 2>&1
    if %errorlevel% equ 0 (
        call uv venv --python 3.12
        call uv pip install -r requirements.txt
    ) else (
        where python >nul 2>&1
        if %errorlevel% equ 0 (
            python -m venv .venv
            call .venv\Scripts\python.exe -m pip install -r requirements.txt
        )
    )
    cd /d "%~dp0"
)

REM ========================================================
REM 4. Preparação do Frontend Next.js (Primeira execução)
REM ========================================================
if not exist "frontend\node_modules" (
    echo.
    echo [Trivium] Instalando pacotes do frontend...
    cd /d "%~dp0frontend"
    call npm install
    echo [Trivium] Gerando build de produção otimizado...
    call npm run build
    cd /d "%~dp0"
)

REM ========================================================
REM 5. Execução do Trivium
REM ========================================================
echo.
echo ========================================================
echo   [Trivium] Inicializando serviços e interface desktop...
echo ========================================================
echo.

if exist "dist_desktop\Trivium.exe" (
    start "" "dist_desktop\Trivium.exe" %*
    timeout /t 2 /nobreak >nul
    exit
)

if exist "backend\.venv\Scripts\python.exe" (
    start "" "backend\.venv\Scripts\pythonw.exe" "backend\desktop_app.py" %*
) else (
    where uv >nul 2>&1
    if %errorlevel% equ 0 (
        start "" uv run python "backend\desktop_app.py" %*
    ) else (
        start "" python "backend\desktop_app.py" %*
    )
)
timeout /t 2 /nobreak >nul
exit
