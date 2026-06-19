"""
Pipeline completo: exporta archivos .hobo con HOBOware y genera las graficas
de serie temporal y Hovmoller con la app tmednet (tema claro).

Uso: python run_all_sites.py

Configuracion: edita la seccion SITES mas abajo para adaptar las rutas y
los codigos de sitio a tu instalacion.
"""

import subprocess, time, os, sys, re, tempfile
import pyautogui
import win32gui, win32api, win32con, win32process
import pyperclip
import psutil

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.15

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURACION — edita estas rutas antes de ejecutar
# ─────────────────────────────────────────────────────────────────────────────

HOBOWARE = r"C:\Program Files\Onset Computer Corporation\HOBOware\HOBOware.exe"
APP_DIR  = os.path.dirname(os.path.abspath(__file__))
DESKTOP  = os.path.join(os.path.expanduser("~"), "Desktop")
TEMP     = tempfile.gettempdir()

# Cada sitio necesita:
#   hobo_dir   : carpeta con los archivos .hobo originales
#   export_dir : carpeta temporal donde HOBOware dejara los .txt exportados
#   site_code  : codigo numerico del sitio en data/metadata.json
#   site_label : etiqueta para el nombre del archivo de salida

SITES = [
    {
        "hobo_dir":   r"C:\ruta\a\tus\archivos\Sitio-A",
        "export_dir": os.path.join(TEMP, "site5_export"),
        "site_code":  "5",
        "site_label": "cap_de_creus-s_el-gat",
    },
    {
        "hobo_dir":   r"C:\ruta\a\tus\archivos\Sitio-B",
        "export_dir": os.path.join(TEMP, "site6_export"),
        "site_code":  "6",
        "site_label": "medes_pota-del-llop",
    },
    {
        "hobo_dir":   r"C:\ruta\a\tus\archivos\Sitio-C",
        "export_dir": os.path.join(TEMP, "site38_export"),
        "site_code":  "38",
        "site_label": "toulon_cap_sicie",
    },
    {
        "hobo_dir":   r"C:\ruta\a\tus\archivos\Sitio-D",
        "export_dir": os.path.join(TEMP, "site150_export"),
        "site_code":  "150",
        "site_label": "ullastres",
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# Utilidades comunes
# ─────────────────────────────────────────────────────────────────────────────

def snap(shots_dir, label, counter):
    counter[0] += 1
    p = os.path.join(shots_dir, f"{counter[0]:02d}_{label}.png")
    pyautogui.screenshot().save(p)
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

def find_hwnd_for_pid(pid):
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
    t0 = time.time()
    while time.time() - t0 < timeout:
        h = find_hwnd_for_pid(pid)
        if h and substr.lower() in win32gui.GetWindowText(h).lower():
            return h
        time.sleep(0.5)
    return None

def kill_existing_tmednet():
    for p in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if p.info['name'] and 'python' in p.info['name'].lower():
                cmdline = ' '.join(p.info['cmdline'] or [])
                if 'main.py' in cmdline and str(p.pid) != str(os.getpid()):
                    p.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    time.sleep(1)

def kill_hoboware():
    for p in psutil.process_iter(['pid', 'name']):
        try:
            if p.info['name'] and 'hoboware' in p.info['name'].lower():
                p.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    time.sleep(2)

# ─────────────────────────────────────────────────────────────────────────────
# Paso 1: Exportar .hobo con HOBOware
# ─────────────────────────────────────────────────────────────────────────────

def export_with_hoboware(hobo_dir, export_dir, shots_dir):
    os.makedirs(export_dir, exist_ok=True)
    os.makedirs(shots_dir, exist_ok=True)
    counter = [0]

    print("  Lanzando HOBOware...")
    kill_hoboware()
    subprocess.Popen([HOBOWARE])
    print("  Esperando 35s para Java...")
    time.sleep(35)

    hwnd = None
    for _ in range(15):
        hwnd = find_hwnd("hoboware")
        if hwnd:
            break
        time.sleep(2)

    if not hwnd:
        print("  ERROR: HOBOware no encontrado")
        return False

    force_fg(hwnd)
    cx = (win32gui.GetWindowRect(hwnd)[0] + win32gui.GetWindowRect(hwnd)[2]) // 2
    cy = (win32gui.GetWindowRect(hwnd)[1] + win32gui.GetWindowRect(hwnd)[3]) // 2
    pyautogui.click(cx, cy)
    time.sleep(0.4)
    for _ in range(3):
        pyautogui.press("escape")
        time.sleep(0.2)

    # Herramientas → Exportación masiva → Seleccionar archivos
    print("  Abriendo Herramientas > Exportacion masiva...")
    pyautogui.press("f10")
    time.sleep(0.7)
    for _ in range(4):
        pyautogui.press("right")
        time.sleep(0.25)
    pyautogui.press("down")
    time.sleep(0.7)
    for _ in range(2):
        pyautogui.press("down")
        time.sleep(0.2)
    pyautogui.press("right")
    time.sleep(0.5)
    pyautogui.press("enter")
    time.sleep(2.5)
    snap(shots_dir, "select_dialog", counter)

    # Diálogo selección de archivos
    dlg = find_hwnd("seleccione")
    if not dlg:
        print("  ERROR: No aparecio dialogo de seleccion")
        return False

    force_fg(dlg)
    time.sleep(0.5)
    x1, y1, x2, y2 = win32gui.GetWindowRect(dlg)
    w, h = x2 - x1, y2 - y1

    pyautogui.click(x1 + int(w * 0.55), y1 + int(h * 0.87))
    time.sleep(0.4)
    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.2)
    pyperclip.copy(hobo_dir)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.3)
    pyautogui.press("enter")
    time.sleep(2.0)

    pyautogui.click(x1 + int(w * 0.65), y1 + int(h * 0.45))
    time.sleep(0.4)
    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.5)
    snap(shots_dir, "files_selected", counter)

    pyautogui.click(x1 + int(w * 0.87), y1 + int(h * 0.87))
    time.sleep(2.5)
    snap(shots_dir, "after_continuar", counter)

    # Diálogo carpeta de exportación
    exp_dlg = find_hwnd("elegir")
    if not exp_dlg:
        print("  ERROR: No aparecio dialogo de carpeta de exportacion")
        return False

    force_fg(exp_dlg)
    time.sleep(0.5)
    ex1, ey1, ex2, ey2 = win32gui.GetWindowRect(exp_dlg)
    ew, eh = ex2 - ex1, ey2 - ey1

    pyautogui.click(ex1 + int(ew * 0.55), ey1 + int(eh * 0.87))
    time.sleep(0.4)
    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.2)
    pyperclip.copy(export_dir)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.3)
    pyautogui.click(ex1 + int(ew * 0.87), ey1 + int(eh * 0.87))
    time.sleep(8)
    snap(shots_dir, "after_export", counter)

    # Cerrar diálogo "completada" y HOBOware
    done_dlg = find_hwnd("masiva") or find_hwnd("completa")
    if done_dlg:
        force_fg(done_dlg)
        time.sleep(0.3)
        pyautogui.press("enter")
        time.sleep(1)

    hobo_hwnd = find_hwnd("hoboware")
    if hobo_hwnd:
        force_fg(hobo_hwnd)
        time.sleep(0.3)
        pyautogui.hotkey("alt", "f4")
        time.sleep(2)
        close_dlg = find_hwnd("guardar") or find_hwnd("save")
        if close_dlg:
            pyautogui.press("n")
            time.sleep(1)

    # Renombrar: quitar ' (n)' de los .txt exportados
    renamed = 0
    for fname in list(os.listdir(export_dir)):
        if fname.endswith(".txt"):
            clean = re.sub(r'\s*\(\d+\)', '', fname)
            if clean != fname:
                src = os.path.join(export_dir, fname)
                dst = os.path.join(export_dir, clean)
                if not os.path.exists(dst):
                    os.rename(src, dst)
                    renamed += 1

    txts = sorted([f for f in os.listdir(export_dir) if f.endswith(".txt")])
    print(f"  Exportados {len(txts)} archivos (renombrados: {renamed})")
    for f in txts:
        print(f"    {f}")
    return len(txts) > 0

# ─────────────────────────────────────────────────────────────────────────────
# Paso 2: Generar gráficas con tmednet
# ─────────────────────────────────────────────────────────────────────────────

def handle_save_dialog(target_path, label):
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
        print(f"  AVISO: no se encontro dialogo de guardar ({label})")
        return False

    force_fg(save_dlg)
    time.sleep(0.4)
    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.2)
    pyperclip.copy(target_path)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.4)
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
    return True

def generate_graphs(export_dir, site_label, site_code, shots_dir):
    txts = sorted([
        os.path.join(export_dir, f).replace("\\", "/")
        for f in os.listdir(export_dir)
        if f.endswith(".txt")
    ])
    if not txts:
        print("  ERROR: no hay .txt en", export_dir)
        return False

    kill_existing_tmednet()

    proc = subprocess.Popen(
        [sys.executable, "main.py", "--light", "--auto-load"] + txts,
        cwd=APP_DIR
    )

    hwnd = wait_for_pid_window(proc.pid, "Temperature Mediterranean", timeout=40)
    if not hwnd:
        print("  ERROR: ventana tmednet no encontrada")
        return False

    print("  Esperando carga de datos (14s)...")
    time.sleep(14)
    force_fg(hwnd)
    time.sleep(0.5)

    # Nombres de archivo de salida
    base = os.path.basename(txts[0])
    parts = base.replace(".txt", "").split("_")
    d_start = parts[1].split("-")[0]
    d_end   = parts[2].split("-")[0]
    ts_name  = f"{site_label}_{site_code}_timeseries_{d_start}_{d_end}"
    hov_name = f"{site_label}_{site_code}_hovmoller_{d_start}_{d_end}"
    ts_path  = os.path.join(DESKTOP, ts_name  + ".png")
    hov_path = os.path.join(DESKTOP, hov_name + ".png")

    # Guardar serie temporal
    print(f"  Guardando serie temporal: {ts_name}.png")
    force_fg(hwnd)
    time.sleep(0.3)
    pyautogui.hotkey("ctrl", "s")
    time.sleep(1.5)
    handle_save_dialog(ts_path, "ts")

    time.sleep(1)

    # Hovmöller
    print("  Generando Hovmoller (Ctrl+H)...")
    force_fg(hwnd)
    time.sleep(0.3)
    pyautogui.hotkey("ctrl", "h")
    time.sleep(3)

    print(f"  Guardando Hovmoller: {hov_name}.png")
    force_fg(hwnd)
    time.sleep(0.3)
    pyautogui.hotkey("ctrl", "s")
    time.sleep(1.5)
    handle_save_dialog(hov_path, "hov")

    # Cerrar app
    time.sleep(1)
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

    # Verificar
    ok = []
    for name in [ts_name + ".png", hov_name + ".png"]:
        p = os.path.join(DESKTOP, name)
        if os.path.exists(p):
            ok.append(f"OK  {name}  ({os.path.getsize(p)//1024} KB)")
        else:
            ok.append(f"FALTA  {name}")
    for line in ok:
        print(" ", line)
    return True

# ─────────────────────────────────────────────────────────────────────────────
# Main: procesar los 4 sitios
# ─────────────────────────────────────────────────────────────────────────────

for i, site in enumerate(SITES, 1):
    print(f"\n{'='*60}")
    print(f"SITIO {i}/4: {site['site_label']} (code {site['site_code']})")
    print(f"{'='*60}")

    shots_dir = os.path.join(site["export_dir"], "shots")

    # Exportar solo si no hay .txt ya exportados
    txts_existing = [f for f in os.listdir(site["export_dir"])
                     if f.endswith(".txt")] if os.path.isdir(site["export_dir"]) else []

    if txts_existing:
        print(f"  Ya hay {len(txts_existing)} .txt en {site['export_dir']}, saltando HOBOware")
    else:
        print("  Paso 1: Exportar con HOBOware")
        ok = export_with_hoboware(site["hobo_dir"], site["export_dir"], shots_dir)
        if not ok:
            print("  ERROR en exportacion, saltando este sitio")
            continue

    print("  Paso 2: Generar graficas con tmednet")
    generate_graphs(site["export_dir"], site["site_label"], site["site_code"], shots_dir)

print("\n\nPIPELINE COMPLETADO")
print("Imagenes en:", DESKTOP)
