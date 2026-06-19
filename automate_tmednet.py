"""
Automatiza la app tmednet: carga archivos via CLI (sin dialogo Open),
genera la serie temporal y el Hovmoller, y los guarda en el Escritorio
usando el boton Save nativo de la app.

Uso: python automate_tmednet.py <export_dir> <site_label> <site_code>
"""

import subprocess, time, os, sys
import pyautogui
import win32gui, win32api, win32con, win32process
import pyperclip

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.15

if len(sys.argv) < 4:
    print("Uso: python automate_tmednet.py <export_dir> <site_label> <site_code>")
    print("  export_dir  : carpeta con los .txt exportados por HOBOware")
    print("  site_label  : nombre del sitio para el archivo de salida (ej. capraia)")
    print("  site_code   : codigo numerico del sitio en metadata.json (ej. 252)")
    sys.exit(1)

EXPORT_DIR = sys.argv[1]
SITE_LABEL = sys.argv[2]
SITE_CODE  = sys.argv[3]
DESKTOP    = os.path.join(os.path.expanduser("~"), "Desktop")
APP_DIR    = os.path.dirname(os.path.abspath(__file__))

SHOTS_DIR = os.path.join(EXPORT_DIR, "app_shots")
os.makedirs(SHOTS_DIR, exist_ok=True)

_n = [0]
def snap(label):
    _n[0] += 1
    p = os.path.join(SHOTS_DIR, f"{_n[0]:02d}_{label}.png")
    pyautogui.screenshot().save(p)
    print(f"  [snap] {p}")
    return p

def find_hwnd(substr):
    res = []
    def cb(h, _):
        t = win32gui.GetWindowText(h)
        if win32gui.IsWindowVisible(h) and substr.lower() in t.lower():
            res.append(h)
    win32gui.EnumWindows(cb, None)
    return res[0] if res else None

def force_fg(hwnd):
    win32api.keybd_event(win32con.VK_MENU, 0, 0, 0)
    win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)
    time.sleep(0.05)
    try:
        win32gui.SetForegroundWindow(hwnd)
    except Exception:
        pass
    time.sleep(0.4)

def kill_existing_tmednet():
    """Kill any existing tmednet Python processes to avoid detecting stale windows."""
    import psutil
    for p in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if p.info['name'] and 'python' in p.info['name'].lower():
                cmdline = ' '.join(p.info['cmdline'] or [])
                if 'main.py' in cmdline and str(p.pid) != str(os.getpid()):
                    print(f"  Matando proceso tmednet anterior: PID {p.pid}")
                    p.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    time.sleep(2)

def find_hwnd_for_pid(pid):
    """Find the visible window created by a specific process PID."""
    res = []
    def cb(h, _):
        if win32gui.IsWindowVisible(h) and win32gui.GetWindowText(h):
            try:
                _, wpid = win32process.GetWindowThreadProcessId(h)
                if wpid == pid:
                    res.append(h)
            except Exception:
                pass
    win32gui.EnumWindows(cb, None)
    return res[0] if res else None

def wait_for_pid_window(pid, substr, timeout=40):
    """Wait for the window belonging to process PID with the given title substring."""
    t0 = time.time()
    while time.time() - t0 < timeout:
        h = find_hwnd_for_pid(pid)
        if h and substr.lower() in win32gui.GetWindowText(h).lower():
            return h
        time.sleep(0.5)
    return None

def handle_save_dialog(target_path, label):
    """Wait for the Qt save dialog and paste the target path."""
    save_dlg = None
    for _ in range(20):
        for t in ["Save plot", "Save"]:
            save_dlg = find_hwnd(t)
            if save_dlg:
                break
        if save_dlg:
            break
        time.sleep(0.5)

    if not save_dlg:
        print(f"  AVISO: no se encontro dialogo de guardar para {label}")
        snap(f"no_save_dlg_{label}")
        return False

    force_fg(save_dlg)
    time.sleep(0.4)
    snap(f"save_dlg_{label}")

    # El campo de nombre de archivo tiene el foco por defecto en un dialogo Save nativo
    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.2)
    pyperclip.copy(target_path)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.4)
    snap(f"save_path_typed_{label}")
    pyautogui.press("enter")
    time.sleep(1.5)

    # Handle overwrite confirmation dialog if file already exists
    confirm_dlg = find_hwnd("Confirmar") or find_hwnd("Confirm") or find_hwnd("overwrite") or find_hwnd("reemplazar")
    if confirm_dlg:
        force_fg(confirm_dlg)
        time.sleep(0.2)
        pyautogui.press("enter")
        time.sleep(1.0)

    time.sleep(0.5)
    snap(f"after_save_{label}")
    print(f"  Guardado: {target_path}")
    return True

# ── 1. Recopilar archivos ─────────────────────────────────────────────────────
txts = sorted([
    os.path.join(EXPORT_DIR, f).replace("\\", "/")
    for f in os.listdir(EXPORT_DIR)
    if f.endswith(".txt")
])
if not txts:
    print(f"ERROR: No hay .txt en {EXPORT_DIR}")
    sys.exit(1)

print(f"Lanzando tmednet para {SITE_LABEL} (site {SITE_CODE}) con {len(txts)} archivos...")

# ── 2. Lanzar la app con --auto-load ─────────────────────────────────────────
# Matar instancias anteriores para evitar confundir ventanas
kill_existing_tmednet()

proc = subprocess.Popen(
    [sys.executable, "main.py", "--light", "--auto-load"] + txts,
    cwd=APP_DIR
)

# Buscar la ventana del proceso EXACTO que acabamos de lanzar
hwnd = wait_for_pid_window(proc.pid, "Temperature Mediterranean", timeout=40)
if not hwnd:
    print("ERROR: No se encontro la ventana principal de tmednet")
    sys.exit(1)

# Esperar a que el splash desaparezca y los archivos se carguen y ploteen
# --auto-load llama load_and_plot_all a los 2.8s, la carga lleva ~3-5s mas
print("Esperando carga de datos (20s)...")
time.sleep(20)
force_fg(hwnd)
time.sleep(0.5)

rect = win32gui.GetWindowRect(hwnd)
wx1, wy1, wx2, wy2 = rect
ww, wh = wx2 - wx1, wy2 - wy1
print(f"Ventana: {ww}x{wh} en ({wx1},{wy1})")
snap("01_timeseries_loaded")

# ── 3. Calcular nombres de archivo de salida ──────────────────────────────────
base = os.path.basename(txts[0])          # e.g. 252_20250925-00_20260410-11_-5.0.txt
parts = base.replace(".txt", "").split("_")
# parts: ['252', '20250925-00', '20260410-11', '-5.0']  (depth may be negative)
d_start = parts[1].split("-")[0]          # '20250925'
d_end   = parts[2].split("-")[0]          # '20260410'
ts_name  = f"{SITE_LABEL}_{SITE_CODE}_timeseries_{d_start}_{d_end}"
hov_name = f"{SITE_LABEL}_{SITE_CODE}_hovmoller_{d_start}_{d_end}"
ts_path  = os.path.join(DESKTOP, ts_name  + ".png")
hov_path = os.path.join(DESKTOP, hov_name + ".png")

# ── 4. Guardar serie temporal (Ctrl+S) ────────────────────────────────────────
print(f"Guardando serie temporal: {ts_name}.png")
force_fg(hwnd)
time.sleep(0.3)
pyautogui.hotkey("ctrl", "s")
time.sleep(1.5)
snap("02_after_ctrlS_ts")

handle_save_dialog(ts_path, "ts")

time.sleep(1)

# ── 5. Generar Hovmoller (Ctrl+H) ─────────────────────────────────────────────
print("Generando Hovmoller (Ctrl+H)...")
force_fg(hwnd)
time.sleep(0.3)
pyautogui.hotkey("ctrl", "h")
time.sleep(3)
snap("03_hovmoller_plot")

# ── 6. Guardar Hovmoller (Ctrl+S) ────────────────────────────────────────────
print(f"Guardando Hovmoller: {hov_name}.png")
force_fg(hwnd)
time.sleep(0.3)
pyautogui.hotkey("ctrl", "s")
time.sleep(1.5)
snap("04_after_ctrlS_hov")

handle_save_dialog(hov_path, "hov")

# ── 7. Cerrar la app ──────────────────────────────────────────────────────────
time.sleep(1)
print("Cerrando la app...")
force_fg(hwnd)
time.sleep(0.3)
pyautogui.hotkey("alt", "f4")
time.sleep(1.5)
close_dlg = find_hwnd("Exit") or find_hwnd("Quit") or find_hwnd("T-MEDNet")
if close_dlg:
    force_fg(close_dlg)
    time.sleep(0.3)
    pyautogui.press("enter")
    time.sleep(0.5)

# ── 8. Verificar resultados ───────────────────────────────────────────────────
print("\nResultado final:")
for name in [ts_name + ".png", hov_name + ".png"]:
    p = os.path.join(DESKTOP, name)
    if os.path.exists(p):
        print(f"  OK  {name}  ({os.path.getsize(p)//1024} KB)")
    else:
        print(f"  FALTA  {name}")
print(f"\nCapturas de diagnostico: {SHOTS_DIR}")
