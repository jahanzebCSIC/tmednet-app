"""
Exporta los .hobo de Cap de Creus-S El Gat con HOBOware y deja los .txt
en el directorio de exportación.
HOBOware se lanza automáticamente.
"""

import subprocess, time, os, sys, re
import pyautogui
import win32gui, win32con, win32api
import pyperclip

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.15

HOBOWARE   = r"C:\Program Files\Onset Computer Corporation\HOBOware\HOBOware.exe"
HOBO_DIR   = r"C:\Users\jahan\Desktop\Tmednet datos\Cape-Creus-S_(El-Gat)"
EXPORT_DIR = r"C:\Users\jahan\AppData\Local\Temp\el_gat_export"
SHOTS_DIR  = os.path.join(EXPORT_DIR, "shots")
os.makedirs(EXPORT_DIR, exist_ok=True)
os.makedirs(SHOTS_DIR, exist_ok=True)

_n = [0]
def snap(label):
    _n[0] += 1
    p = os.path.join(SHOTS_DIR, f"{_n[0]:02d}_{label}.png")
    pyautogui.screenshot().save(p)
    print(f"  [snap] {p}")

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

# ── 1. Lanzar HOBOware ───────────────────────────────────────────────────────
print("Lanzando HOBOware...")
# Cerrar instancias anteriores
import psutil
for p in psutil.process_iter(['pid', 'name']):
    try:
        if p.info['name'] and 'hoboware' in p.info['name'].lower():
            p.kill()
    except Exception:
        pass
time.sleep(2)

subprocess.Popen([HOBOWARE])
print("Esperando 35s para que cargue Java...")
time.sleep(35)

hwnd = None
for _ in range(15):
    hwnd = find_hwnd("hoboware")
    if hwnd:
        break
    time.sleep(2)

if not hwnd:
    print("ERROR: No se encontro HOBOware")
    sys.exit(1)

print(f"HOBOware encontrado: rect={win32gui.GetWindowRect(hwnd)}")
force_fg(hwnd)
cx = (win32gui.GetWindowRect(hwnd)[0] + win32gui.GetWindowRect(hwnd)[2]) // 2
cy = (win32gui.GetWindowRect(hwnd)[1] + win32gui.GetWindowRect(hwnd)[3]) // 2
pyautogui.click(cx, cy)
time.sleep(0.4)
for _ in range(3):
    pyautogui.press("escape")
    time.sleep(0.2)
snap("01_ready")

# ── 2. Herramientas → Exportación masiva → Seleccionar archivos ──────────────
print("Abriendo Herramientas > Exportacion masiva > Seleccionar archivos...")
pyautogui.press("f10")
time.sleep(0.7)
for _ in range(4):
    pyautogui.press("right")
    time.sleep(0.25)
pyautogui.press("down")
time.sleep(0.7)
snap("02_herramientas_open")
for _ in range(2):
    pyautogui.press("down")
    time.sleep(0.2)
pyautogui.press("right")
time.sleep(0.5)
pyautogui.press("enter")
time.sleep(2.5)
snap("03_select_dialog")

# ── 3. Diálogo selección de archivos ─────────────────────────────────────────
dlg = find_hwnd("seleccione")
if not dlg:
    print("ERROR: No aparecio dialogo de seleccion")
    snap("ERROR_no_select_dialog")
    sys.exit(1)

force_fg(dlg)
time.sleep(0.5)
x1, y1, x2, y2 = win32gui.GetWindowRect(dlg)
w, h = x2 - x1, y2 - y1

pyautogui.click(x1 + int(w * 0.55), y1 + int(h * 0.87))
time.sleep(0.4)
pyautogui.hotkey("ctrl", "a")
time.sleep(0.2)
pyperclip.copy(HOBO_DIR)
pyautogui.hotkey("ctrl", "v")
time.sleep(0.3)
pyautogui.press("enter")
time.sleep(2.0)
snap("04_navigated")

pyautogui.click(x1 + int(w * 0.65), y1 + int(h * 0.45))
time.sleep(0.4)
pyautogui.hotkey("ctrl", "a")
time.sleep(0.5)
snap("05_files_selected")

pyautogui.click(x1 + int(w * 0.87), y1 + int(h * 0.87))
time.sleep(2.5)
snap("06_after_continuar")

# ── 4. Diálogo carpeta de exportación ────────────────────────────────────────
exp_dlg = find_hwnd("elegir")
if not exp_dlg:
    print("ERROR: No aparecio dialogo de carpeta de exportacion")
    snap("ERROR_no_export_dialog")
    sys.exit(1)

force_fg(exp_dlg)
time.sleep(0.5)
ex1, ey1, ex2, ey2 = win32gui.GetWindowRect(exp_dlg)
ew, eh = ex2 - ex1, ey2 - ey1

pyautogui.click(ex1 + int(ew * 0.55), ey1 + int(eh * 0.87))
time.sleep(0.4)
pyautogui.hotkey("ctrl", "a")
time.sleep(0.2)
pyperclip.copy(EXPORT_DIR)
pyautogui.hotkey("ctrl", "v")
time.sleep(0.3)
snap("07_export_path")

pyautogui.click(ex1 + int(ew * 0.87), ey1 + int(eh * 0.87))
print("Exportando (esperar ~15s)...")
time.sleep(15)
snap("08_after_export")

# ── 5. Cerrar diálogos y HOBOware ────────────────────────────────────────────
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

# ── 6. Renombrar (quitar " (n)") ─────────────────────────────────────────────
for fname in list(os.listdir(EXPORT_DIR)):
    if fname.endswith(".txt"):
        clean = re.sub(r'\s*\(\d+\)', '', fname)
        if clean != fname:
            src = os.path.join(EXPORT_DIR, fname)
            dst = os.path.join(EXPORT_DIR, clean)
            if not os.path.exists(dst):
                os.rename(src, dst)

txts = sorted([f for f in os.listdir(EXPORT_DIR) if f.endswith(".txt")])
print(f"\nExportados {len(txts)} archivos:")
for f in txts:
    print(f"  {f}")

if not txts:
    print("ERROR: No se exporto ningun .txt — revisa las capturas en:", SHOTS_DIR)
    sys.exit(1)

print(f"\nCaptures en: {SHOTS_DIR}")
print(f"Ahora ejecuta: python generate_cap_creus_s_plots.py")
