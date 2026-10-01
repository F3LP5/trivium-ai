[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Write-Host ""
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "       TRIVIUM ACADEMY - CONFIGURACAO AUTOMATICA        " -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Atalho na Área de Trabalho
try {
    $desktop = [Environment]::GetFolderPath("Desktop")
    if (Test-Path $desktop) {
        $lnkPath = Join-Path $desktop "Trivium.lnk"
        $targetExe = Join-Path $root "Trivium-Launcher.bat"
        $icoPath = Join-Path $root "assets\trivium.ico"
        $ws = New-Object -ComObject WScript.Shell
        $shortcut = $ws.CreateShortcut($lnkPath)
        $shortcut.TargetPath = $targetExe
        $shortcut.WorkingDirectory = $root
        if (Test-Path $icoPath) { $shortcut.IconLocation = "$icoPath,0" }
        $shortcut.Description = "Trivium - Rigor, Logica e Maestria"
        $shortcut.Save()
    }
} catch {}

# 2. Node.js (Sistema ou Portátil)
$hasNode = $false
try {
    $nodeCmd = Get-Command node -ErrorAction SilentlyContinue
    if ($nodeCmd) { $hasNode = $true }
} catch {}

$portableNodeDir = Join-Path $env:LOCALAPPDATA "trivium\node"
if (-not $hasNode -and (Test-Path (Join-Path $portableNodeDir "node.exe"))) {
    $hasNode = $true
}

if (-not $hasNode) {
    Write-Host "[1/4] Node.js nao detectado. Baixando versao portatil (sem necessidade de admin)..." -ForegroundColor Yellow
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    $zipPath = Join-Path $env:TEMP "node-portable.zip"
    $nodeExtract = Join-Path $env:TEMP "node-extract"
    Invoke-WebRequest -Uri "https://nodejs.org/dist/v20.18.0/node-v20.18.0-win-x64.zip" -OutFile $zipPath
    if (Test-Path $nodeExtract) { Remove-Item $nodeExtract -Recurse -Force -ErrorAction SilentlyContinue }
    Expand-Archive -Path $zipPath -DestinationPath $nodeExtract -Force
    if (-not (Test-Path $portableNodeDir)) { New-Item -ItemType Directory -Force -Path $portableNodeDir | Out-Null }
    $subDir = (Get-ChildItem -Path $nodeExtract -Directory | Select-Object -First 1).FullName
    Copy-Item -Path (Join-Path $subDir "*") -Destination $portableNodeDir -Recurse -Force
    Remove-Item $zipPath -Force -ErrorAction SilentlyContinue
    Remove-Item $nodeExtract -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "[OK] Node.js portatil instalado com sucesso!" -ForegroundColor Green
}

# Configura PATH do Node nesta sessão se for portátil
if (Test-Path (Join-Path $portableNodeDir "node.exe")) {
    $env:PATH = "$portableNodeDir;$env:PATH"
}

# 3. Gerenciador Python UV & Ambiente Virtual
$backendDir = Join-Path $root "backend"
$venvPython = Join-Path $backendDir ".venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    Write-Host "[2/4] Preparando ambiente Python (3.12)..." -ForegroundColor Yellow
    
    $uvBin = $null
    $possibleUv = @(
        (Get-Command uv -ErrorAction SilentlyContinue).Source,
        (Join-Path $env:USERPROFILE ".local\bin\uv.exe"),
        (Join-Path $env:LOCALAPPDATA "uv\uv.exe"),
        (Join-Path $env:USERPROFILE ".cargo\bin\uv.exe")
    )
    foreach ($p in $possibleUv) {
        if ($p -and (Test-Path $p)) { $uvBin = $p; break }
    }

    if (-not $uvBin) {
        Write-Host "      Baixando gerenciador uv..." -ForegroundColor Gray
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        try {
            Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression
        } catch {
            $uvZip = Join-Path $env:TEMP "uv.zip"
            Invoke-WebRequest -Uri "https://github.com/astral-sh/uv/releases/latest/download/uv-x86_64-pc-windows-msvc.zip" -OutFile $uvZip
            $uvDir = Join-Path $env:LOCALAPPDATA "uv"
            Expand-Archive -Path $uvZip -DestinationPath $uvDir -Force
            Remove-Item $uvZip -Force -ErrorAction SilentlyContinue
        }
        foreach ($p in @((Join-Path $env:USERPROFILE ".local\bin\uv.exe"), (Join-Path $env:LOCALAPPDATA "uv\uv.exe"), (Join-Path $env:USERPROFILE ".cargo\bin\uv.exe"))) {
            if (Test-Path $p) { $uvBin = $p; break }
        }
    }

    if (-not $uvBin) {
        throw "Nao foi possivel instalar o gerenciador Python UV."
    }

    Write-Host "      Criando ambiente virtual com Python 3.12..." -ForegroundColor Gray
    & $uvBin venv (Join-Path $backendDir ".venv") --python 3.12
    Write-Host "      Instalando dependencias do backend (FastAPI, PyWebView, LiteLLM)..." -ForegroundColor Gray
    $reqFile = Join-Path $backendDir "requirements.txt"
    & $uvBin pip install -r $reqFile --python $venvPython
    Write-Host "      Configurando Chromium para geracao de PDFs (Playwright)..." -ForegroundColor Gray
    & $venvPython -m playwright install chromium
    Write-Host "[OK] Backend configurado com sucesso!" -ForegroundColor Green
} else {
    Write-Host "[OK] Backend e ambiente Python ja configurados." -ForegroundColor Green
}

# 4. Frontend Next.js (Instalação e Build)
$frontendDir = Join-Path $root "frontend"
$nodeModules = Join-Path $frontendDir "node_modules"
$nextBuild = Join-Path $frontendDir ".next"

$npmCmd = "npm.cmd"
if (-not (Get-Command $npmCmd -ErrorAction SilentlyContinue)) {
    if (Test-Path (Join-Path $portableNodeDir "npm.cmd")) {
        $npmCmd = (Join-Path $portableNodeDir "npm.cmd")
    }
}

if (-not (Test-Path $nodeModules)) {
    Write-Host "[3/4] Instalando dependencias da interface web..." -ForegroundColor Yellow
    Push-Location $frontendDir
    try {
        & $npmCmd install
    } finally {
        Pop-Location
    }
}

if (-not (Test-Path $nextBuild)) {
    Write-Host "[4/4] Compilando versao de producao do frontend..." -ForegroundColor Yellow
    Push-Location $frontendDir
    try {
        & $npmCmd run build
    } finally {
        Pop-Location
    }
    Write-Host "[OK] Interface web pronta!" -ForegroundColor Green
} else {
    Write-Host "[OK] Frontend pronto." -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================================" -ForegroundColor Green
Write-Host "       TRIVIUM ACADEMY ESTA PRONTO PARA USO!            " -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Green
Write-Host ""
