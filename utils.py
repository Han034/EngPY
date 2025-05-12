# utils.py
# Genel yardımcı fonksiyonları içerir.

import sys
import ctypes
import json
import os
try:
    import winreg
except ImportError:
    winreg = None

# Yapılandırma sabitlerini config dosyasından import et
import config

# --- Global Değişken Referansları (Geçici - Sınıflara Taşınacak) ---
app_settings = {}
profiles_data = {}
root = None
current_profile_name = config.DEFAULT_PROFILE_NAME

# --- DPI Ölçekleme Faktörünü Alma ---
def get_dpi_scale_factor():
    """Geçerli DPI ölçek faktörünü döndürür (Windows için)."""
    if sys.platform == "win32":
        try:
            # DPI farkındalığını ayarlamaya gerek YOK, sistemin değerini alalım
            # Farklı Windows versiyonları için farklı API'ler gerekebilir
            # En günceli SetThreadDpiAwarenessContext veya SetProcessDpiAwareness
            # Daha basit ve yaygın olanı GetDC/GetDeviceCaps deneyelim
            dc = ctypes.windll.user32.GetDC(0)
            dpi = ctypes.windll.gdi32.GetDeviceCaps(dc, 88) # LOGPIXELSX
            ctypes.windll.user32.ReleaseDC(0, dc)
            calculated_scale = dpi / config.BASE_DPI # config'deki BASE_DPI (96) kullanılır
            print(f"Detected DPI: {dpi}, Calculated Scale Factor: {calculated_scale:.2f}")
            # tk scaling genellikle 1.0'dan büyük değerler bekler
            return calculated_scale if calculated_scale >= 1.0 else 1.0
        except Exception as e:
            print(f"Error detecting DPI: {e}. Using default scale 1.0")
            return 1.0
    else:
        # Diğer platformlar için varsayılan
        print("DPI detection skipped (not on Windows). Using default scale 1.0")
        return 1.0

# --- Ayarları Yükleme/Kaydetme ---
def load_settings():
    global app_settings
    default_settings = {"theme": get_system_theme(), "window_geometry": config.DEFAULT_WINDOW_GEOMETRY}
    if os.path.exists(config.SETTINGS_FILE):
        try:
            with open(config.SETTINGS_FILE, 'r', encoding='utf-8') as f: loaded = json.load(f)
            app_settings = default_settings.copy(); app_settings.update(loaded)
            print(f"Settings loaded from {config.SETTINGS_FILE}")
        except Exception as e: print(f"Error loading settings: {e}. Using defaults."); app_settings = default_settings
    else: print(f"Info: Settings file not found. Using defaults."); app_settings = default_settings

def save_settings():
    global app_settings
    try:
        settings_to_save = { "theme": app_settings.get("theme", "dark"), "window_geometry": app_settings.get("window_geometry", config.DEFAULT_WINDOW_GEOMETRY) }
        with open(config.SETTINGS_FILE, 'w', encoding='utf-8') as f: json.dump(settings_to_save, f, indent=4, ensure_ascii=False)
        print(f"Settings saved to {config.SETTINGS_FILE}")
    except Exception as e: print(f"Error saving settings: {e}")

# --- Profilleri Yükleme/Kaydetme ---
def load_profiles():
    global profiles_data, current_profile_name
    default_profile_data = config.DEFAULT_PROFILE_DATA.copy()
    default_profile_name = config.DEFAULT_PROFILE_NAME
    if os.path.exists(config.PROFILE_FILE):
        try:
            with open(config.PROFILE_FILE, 'r', encoding='utf-8') as f: profiles_data = json.load(f)
            if not isinstance(profiles_data, dict) or not profiles_data: print(f"Warning: Profile file empty/invalid. Creating default."); profiles_data = {default_profile_name: default_profile_data}; save_profiles()
            if current_profile_name not in profiles_data:
                if profiles_data: current_profile_name = list(profiles_data.keys())[0]
                else: profiles_data = {default_profile_name: default_profile_data}; save_profiles()
            print(f"Profiles loaded from {config.PROFILE_FILE}. Active: {current_profile_name}")
        except Exception as e: print(f"Error loading profiles: {e}. Creating default."); profiles_data = {default_profile_name: default_profile_data}; current_profile_name = default_profile_name; save_profiles()
    else: print(f"Info: Profile file not found. Creating default."); profiles_data = {default_profile_name: default_profile_data}; current_profile_name = default_profile_name; save_profiles()
def save_profiles():
    global profiles_data
    try:
        with open(config.PROFILE_FILE, 'w', encoding='utf-8') as f: json.dump(profiles_data, f, indent=4, ensure_ascii=False)
        print(f"Profiles saved to {config.PROFILE_FILE}")
    except Exception as e: print(f"Error saving profiles: {e}")

# --- Sistem Teması Algılama ---
def get_system_theme():
    if winreg and sys.platform == "win32":
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Themes\Personalize')
            value, _ = winreg.QueryValueEx(key, 'AppsUseLightTheme'); winreg.CloseKey(key)
            return "light" if value == 1 else "dark"
        except Exception: return "dark"
    else: return "dark"

# --- Pencereyi Ön Plana Getirme ---
def bring_window_to_front():
    if not root: return
    try:
        if sys.platform == "win32": hwnd = ctypes.windll.user32.GetParent(root.winfo_id()); ctypes.windll.user32.SetForegroundWindow(hwnd); print("Info: Window to front (Win).")
        else: root.lift(); root.focus_force(); print("Info: Window to front (Other).")
    except Exception as e: print(f"Error bringing window to front: {e}")

