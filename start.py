# start.py
# Ana uygulamayı başlatan betik.

import tkinter as tk
from main_app import MainApp # Ana uygulama sınıfını import et
import sys      # <--- EKLENDİ
import ctypes   # <--- EKLENDİ

# --- DPI Farkındalığı Ayarı (Windows için) ---
# Tkinter root oluşturulmadan ÖNCE çağrılmalı
try:
    if sys.platform == "win32":
        # Windows 8.1 ve sonrası için önerilen: Per Monitor v2
        # PROCESS_PER_MONITOR_DPI_AWARE = 2
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
        print("INFO: Process DPI Awareness set to Per Monitor v2.")
except AttributeError:
    # Eski Windows versiyonları için (veya shcore yoksa)
    try:
        ctypes.windll.user32.SetProcessDPIAware()
        print("INFO: SetProcessDPIAware() called (Legacy System Aware).")
    except Exception as e_legacy:
        print(f"ERROR: Failed to call SetProcessDPIAware(): {e_legacy}")
except Exception as e:
    print(f"ERROR: Could not set DPI awareness - {e}")
# --- Bitti: DPI Farkındalığı Ayarı ---

if __name__ == "__main__":
    # Ana Tkinter penceresini oluştur
    root = tk.Tk()
    # Ana uygulama sınıfından bir örnek oluştur (bu __init__ içinde her şeyi kuracak)
    app = MainApp(root)
    # Tkinter olay döngüsünü başlat
    root.mainloop()
