# Script de criação do atalho oficial do Trivium na Área de Trabalho
$ErrorActionPreference = "SilentlyContinue"

$desktop = [Environment]::GetFolderPath("Desktop")
if (-not (Test-Path $desktop)) {
    exit 0
}

$root = Split-Path -Parent $PSScriptRoot
$lnkPath = Join-Path $desktop "Trivium.lnk"

$targetExe = Join-Path $root "dist_desktop\Trivium.exe"
if (-not (Test-Path $targetExe)) {
    $targetExe = Join-Path $root "Trivium-Launcher.bat"
}

$icoPath = Join-Path $root "assets\trivium.ico"

$ws = New-Object -ComObject WScript.Shell
$shortcut = $ws.CreateShortcut($lnkPath)
$shortcut.TargetPath = $targetExe
$shortcut.WorkingDirectory = $root
if (Test-Path $icoPath) {
    $shortcut.IconLocation = "$icoPath,0"
}
$shortcut.Description = "Trivium - Rigor, Logica e Maestria"
$shortcut.Save()

Write-Host "[OK] Atalho criado em: $lnkPath" -ForegroundColor Green
