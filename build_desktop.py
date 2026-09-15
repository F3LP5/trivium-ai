"""
Script de automação para compilar o executável desktop do Trivium com a logo oficial.
Gera o executável nativo do Windows com ícone incorporado.
"""
import sys
import os
import subprocess
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT_DIR = Path(__file__).resolve().parent
ASSETS_DIR = ROOT_DIR / "assets"
BACKEND_DIR = ROOT_DIR / "backend"
ICO_PATH = ASSETS_DIR / "trivium.ico"

def build_executable():
    print("=======================================================")
    print("  TRIVIUM ACADEMY - COMPILACAO DO EXECUTAVEL DESKTOP   ")
    print("=======================================================")

    if not ICO_PATH.exists():
        print(f"Erro: Icone nao encontrado em {ICO_PATH}")
        sys.exit(1)

    print(f"[OK] Icone oficial verificado: {ICO_PATH}")

    cmd = [
        "uv", "run",
        "--with", "pyinstaller",
        "--with", "pywebview",
        "--with", "pillow",
        "pyinstaller",
        "--noconsole",
        "--onefile",
        f"--icon={ICO_PATH}",
        "--name=Trivium",
        f"--add-data={ICO_PATH};.",
        "--collect-all=webview",
        "--distpath=dist_desktop",
        "--workpath=build_desktop",
        str(BACKEND_DIR / "desktop_app.py")
    ]

    print("\nExecutando PyInstaller via uv...")
    print("Comando:", " ".join(cmd))
    result = subprocess.run(cmd, cwd=str(ROOT_DIR))

    if result.returncode == 0:
        exe_path = ROOT_DIR / "dist_desktop" / "Trivium.exe"
        print("\n=======================================================")
        print("[OK] COMPILACAO CONCLUIDA COM SUCESSO!")
        print(f"Executavel gerado em: {exe_path}")
        print("=======================================================")
    else:
        print("\n[ERRO] Falha na compilacao do executavel.")
        sys.exit(result.returncode)

if __name__ == "__main__":
    build_executable()
