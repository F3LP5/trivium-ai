import os
import sys
import time
import socket
import ctypes
import subprocess
import atexit
import shutil
import urllib.request
from pathlib import Path
try:
    import webview
    HAS_WEBVIEW = True
    # Força o uso estrito do motor moderno Edge Chromium (WebView2)
    os.environ["PYWEBVIEW_GUI"] = "edgechromium"
except Exception:
    HAS_WEBVIEW = False
    webview = None

# Registra o AppUserModelID para o Windows exibir o ícone correto na barra de tarefas
try:
    if sys.platform == 'win32':
        myappid = 'trivium.academy.desktop.v1'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except Exception:
    pass

DEBUG_MODE = "--debug" in sys.argv or os.getenv("TRIVIUM_DEBUG", "").lower() in ("1", "true", "yes")

def get_project_root() -> Path:
    """
    Localiza a raiz do projeto Trivium tanto quando executado como script Python,
    quanto quando executado empacotado pelo PyInstaller (.exe).
    """
    if getattr(sys, 'frozen', False):
        exe_dir = Path(sys.executable).resolve().parent
        # Se estiver em dist_desktop/Trivium.exe, a raiz é o diretório pai
        if (exe_dir.parent / "backend").is_dir() and (exe_dir.parent / "frontend").is_dir():
            return exe_dir.parent
        # Se o executável estiver na raiz
        if (exe_dir / "backend").is_dir() and (exe_dir / "frontend").is_dir():
            return exe_dir
        return exe_dir.parent
    else:
        # Quando executado como backend/desktop_app.py
        current_dir = Path(__file__).resolve().parent
        if (current_dir.parent / "backend").is_dir() and (current_dir.parent / "frontend").is_dir():
            return current_dir.parent
        return current_dir

PROJECT_ROOT = get_project_root()
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"

if getattr(sys, 'frozen', False):
    ICON_PATH = Path(sys._MEIPASS) / "trivium.ico"
else:
    ICON_PATH = PROJECT_ROOT / "assets" / "trivium.ico"
    if not ICON_PATH.exists():
        ICON_PATH = BACKEND_DIR / "trivium.ico"

def ensure_desktop_shortcut():
    """Garante que o atalho oficial 'Trivium' exista na Área de Trabalho do usuário."""
    if sys.platform != "win32":
        return
    try:
        ps_script = PROJECT_ROOT / "assets" / "create_shortcut.ps1"
        if ps_script.exists():
            subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ps_script)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=0x08000000
            )
            return

        user_desktop = Path(os.environ.get("USERPROFILE", "")) / "Desktop"
        if not user_desktop.exists():
            return
        shortcut_file = user_desktop / "Trivium.lnk"
        target_exe = PROJECT_ROOT / "dist_desktop" / "Trivium.exe"
        if not target_exe.exists():
            target_exe = PROJECT_ROOT / "Trivium-Launcher.bat"
        ico_file = PROJECT_ROOT / "assets" / "trivium.ico"
        
        ps_cmd = (
            f"$ws = New-Object -ComObject WScript.Shell; "
            f"$s = $ws.CreateShortcut('{str(shortcut_file)}'); "
            f"$s.TargetPath = '{str(target_exe)}'; "
            f"$s.WorkingDirectory = '{str(PROJECT_ROOT)}'; "
            f"$s.IconLocation = '{str(ico_file)},0'; "
            f"$s.Description = 'Trivium - Rigor, Logica e Maestria'; "
            f"$s.Save()"
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=0x08000000
        )
    except Exception:
        pass

def is_port_in_use(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.8):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False

def is_http_ready(url: str, timeout: float = 1.2) -> bool:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Trivium-Desktop/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.status in (200, 304)
    except Exception:
        return False

def wait_for_http(url: str, port: int, timeout: float = 40.0) -> bool:
    """
    Aguarda a prontidão real HTTP (200/304). Quando o Next.js responde 200,
    aguarda um curto intervalo para assegurar que os arquivos CSS e JS estejam
    prontos para entrega, evitando renderizações sem estilização (FOUC).
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        if is_http_ready(url):
            time.sleep(0.8)  # Margem segura para carregamento pleno de chunks CSS/JS
            return True
        elif is_port_in_use("127.0.0.1", port):
            time.sleep(0.4)
        else:
            time.sleep(0.5)
    return False

def kill_port_tree(port: int):
    try:
        out = subprocess.check_output("netstat -ano -p tcp", shell=True, text=True)
        pids = set()
        for line in out.splitlines():
            if f":{port}" in line and "LISTENING" in line:
                parts = line.strip().split()
                if parts:
                    pid = parts[-1]
                    if pid.isdigit() and int(pid) > 0:
                        pids.add(int(pid))
        for pid in pids:
            subprocess.run(f"taskkill /F /T /PID {pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

def cleanup():
    if DEBUG_MODE:
        print("\n[Trivium] Encerrando servidores locais do Trivium (:8000 e :3000)...")
    for port in [8000, 3000]:
        kill_port_tree(port)

def start_services_if_needed():
    """
    Inicia o Backend FastAPI (:8000) e o Frontend Next.js (:3000) caso não estejam rodando.
    Limpa preventivamente portas que estejam presas por processos zumbis ou travados.
    """
    # Flags do Windows para controle de janelas
    CREATE_NO_WINDOW = 0x08000000
    CREATE_NEW_CONSOLE = 0x00000010

    cflags = CREATE_NEW_CONSOLE if DEBUG_MODE else CREATE_NO_WINDOW

    # 1. Verifica se a porta 8000 está ocupada por um processo zumbi que não responde a HTTP
    if is_port_in_use("127.0.0.1", 8000) and not is_http_ready("http://127.0.0.1:8000/docs", timeout=1.0):
        if DEBUG_MODE:
            print("[Trivium] Porta 8000 ocupada por processo inativo. Reiniciando...")
        kill_port_tree(8000)
        time.sleep(0.5)

    # Inicia Backend FastAPI se a porta 8000 estiver livre
    if not is_port_in_use("127.0.0.1", 8000):
        if DEBUG_MODE:
            print("[Trivium] Inicializando Backend FastAPI na porta 8000...")

        # Detecta comando do Python / uv
        python_venv = BACKEND_DIR / ".venv" / "Scripts" / "python.exe"
        if python_venv.exists():
            backend_cmd = [str(python_venv), "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"]
        elif shutil.which("uv"):
            backend_cmd = ["uv", "run", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"]
        elif shutil.which("python"):
            backend_cmd = ["python", "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"]
        else:
            backend_cmd = ["uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"]

        try:
            subprocess.Popen(
                backend_cmd,
                cwd=str(BACKEND_DIR),
                creationflags=cflags,
                shell=False
            )
        except Exception as e:
            if DEBUG_MODE:
                print(f"[Trivium] Erro ao iniciar backend: {e}")

    # 2. Verifica se a porta 3000 está ocupada por um processo zumbi que não responde a HTTP
    if is_port_in_use("127.0.0.1", 3000) and not is_http_ready("http://127.0.0.1:3000", timeout=1.0):
        if DEBUG_MODE:
            print("[Trivium] Porta 3000 ocupada por processo inativo. Reiniciando...")
        kill_port_tree(3000)
        time.sleep(0.5)

    # Inicia Frontend Next.js se a porta 3000 estiver livre
    if not is_port_in_use("127.0.0.1", 3000):
        if DEBUG_MODE:
            print("[Trivium] Inicializando Frontend Next.js na porta 3000...")

        npm_bin = shutil.which("npm.cmd") or shutil.which("npm") or "npm"
        is_built = (FRONTEND_DIR / ".next" / "BUILD_ID").exists()
        frontend_cmd = [npm_bin, "run", "start", "--", "-p", "3000"] if is_built else [npm_bin, "run", "dev", "--", "-p", "3000"]

        try:
            subprocess.Popen(
                frontend_cmd,
                cwd=str(FRONTEND_DIR),
                creationflags=cflags,
                shell=False
            )
        except Exception as e:
            if DEBUG_MODE:
                print(f"[Trivium] Erro ao iniciar frontend: {e}")

def main():
    frontend_url = "http://localhost:3000"

    # Garante que o atalho oficial 'Trivium' exista na Área de Trabalho
    ensure_desktop_shortcut()

    # Inicia os servidores se ainda não estiverem ativos
    start_services_if_needed()

    if DEBUG_MODE:
        print("[Trivium Debug] Aguardando prontidão dos serviços...")
        print(" - [1/2] Verificando Backend FastAPI (:8000)...")

    backend_ok = wait_for_http("http://127.0.0.1:8000/docs", 8000, timeout=40.0)

    if DEBUG_MODE:
        print(" - [2/2] Verificando Frontend Next.js (:3000)...")

    frontend_ok = wait_for_http("http://127.0.0.1:3000", 3000, timeout=40.0)

    if not backend_ok or not frontend_ok:
        msg = "Não foi possível conectar aos servidores locais do Trivium:\n"
        if not backend_ok:
            msg += " • Backend FastAPI (:8000) não respondeu a tempo.\n"
        if not frontend_ok:
            msg += " • Frontend Next.js (:3000) não respondeu a tempo.\n"
        msg += "\nVerifique se o Node.js e o Python estão instalados ou execute Trivium-Dev-Console.bat para depurar."
        
        if sys.platform == "win32":
            ctypes.windll.user32.MessageBoxW(0, msg, "Trivium Academy - Erro de Inicialização", 0x10)
        else:
            print(f"❌ ERRO CRÍTICO:\n{msg}")
        cleanup()
        sys.exit(1)

    if HAS_WEBVIEW and webview is not None:
        try:
            if DEBUG_MODE:
                print("[Trivium Debug] Servidores online! Abrindo janela desktop...")

            # Cria janela nativa do Desktop com proporções confortáveis
            window = webview.create_window(
                title="Trivium - Rigor, Lógica e Maestria",
                url=frontend_url,
                width=1380,
                height=880,
                min_size=(1024, 700),
                background_color="#0b0b0b",
                confirm_close=False,
                text_select=True,
                zoomable=True,
            )

            window.events.closed += cleanup
            atexit.register(cleanup)

            try:
                webview.start(gui="edgechromium", debug=DEBUG_MODE)
                return
            except Exception as e:
                if DEBUG_MODE:
                    print(f"[Trivium] Inicialização com gui='edgechromium' reportou: {e}. Tentando fallback padrão...")
                try:
                    webview.start(debug=DEBUG_MODE)
                    return
                except Exception as e2:
                    if DEBUG_MODE:
                        print(f"[Trivium] Falha na janela nativa ({e2}). Abrindo no navegador...")
        except Exception as e:
            if DEBUG_MODE:
                print(f"[Trivium] Falha ao configurar webview ({e}). Abrindo no navegador...")

    # Fallback garantido: abre no navegador padrão do usuário
    print(f"[Trivium] Servidores online! Abrindo {frontend_url} no seu navegador...")
    import webbrowser
    webbrowser.open(frontend_url)
    atexit.register(cleanup)
    print("[Trivium] Aplicativo rodando! Pressione Ctrl+C para encerrar os servidores.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        cleanup()

if __name__ == "__main__":
    main()
