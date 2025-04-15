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
# Bu fonksiyonlar henüz sınıf yapısına entegre edilmediği için
# global değişkenlere erişmeye çalışacaklar. Bu durum daha sonra düzeltilecektir.
# Örneğin, app_settings ve profiles_data bir veri yöneticisi sınıfında,
# root ise ana uygulama sınıfında olacak.
app_settings = {}
profiles_data = {}
root = None # Ana pencere referansı (bring_window_to_front için)
current_profile_name = config.DEFAULT_PROFILE_NAME # load_profiles içinde kullanılacak

# --- Ayarları Yükleme/Kaydetme ---
def load_settings():
    """Genel ayarları settings.json dosyasından yükler ve app_settings'i günceller."""
    global app_settings # TODO: Sınıf yapısında global kullanım kaldırılacak
    default_settings = {"theme": get_system_theme(), "window_geometry": config.DEFAULT_WINDOW_GEOMETRY}
    if os.path.exists(config.SETTINGS_FILE):
        try:
            with open(config.SETTINGS_FILE, 'r', encoding='utf-8') as f: loaded = json.load(f)
            app_settings = default_settings.copy(); app_settings.update(loaded)
            print(f"Settings loaded from {config.SETTINGS_FILE}")
        except Exception as e: print(f"Error loading settings: {e}. Using defaults."); app_settings = default_settings
    else: print(f"Info: Settings file not found. Using defaults."); app_settings = default_settings
    # Fonksiyonun bir değer döndürmesi gerekebilir veya doğrudan global'i değiştirmesi yeterli olabilir.
    # Şimdilik global'i değiştirmesi yeterli.

def save_settings():
    """Global app_settings sözlüğünü settings.json dosyasına kaydeder."""
    global app_settings # TODO: Sınıf yapısında global kullanım kaldırılacak
    try:
        settings_to_save = {
            "theme": app_settings.get("theme", "dark"),
            "window_geometry": app_settings.get("window_geometry", config.DEFAULT_WINDOW_GEOMETRY)
        }
        with open(config.SETTINGS_FILE, 'w', encoding='utf-8') as f: json.dump(settings_to_save, f, indent=4, ensure_ascii=False)
        print(f"Settings saved to {config.SETTINGS_FILE}")
    except Exception as e: print(f"Error saving settings: {e}")

# --- Profilleri Yükleme/Kaydetme ---
def load_profiles():
    """Profilleri profiles.json dosyasından yükler."""
    global profiles_data, current_profile_name # TODO: Sınıf yapısında global kullanım kaldırılacak
    # Varsayılan profil verisini config'den al
    default_profile_data = config.DEFAULT_PROFILE_DATA.copy()
    # Varsayılan profil adını da config'den alabiliriz
    default_profile_name = config.DEFAULT_PROFILE_NAME

    if os.path.exists(config.PROFILE_FILE):
        try:
            with open(config.PROFILE_FILE, 'r', encoding='utf-8') as f: profiles_data = json.load(f)
            if not isinstance(profiles_data, dict) or not profiles_data:
                print(f"Warning: Profile file empty/invalid. Creating default."); profiles_data = {default_profile_name: default_profile_data}; save_profiles()

            # Aktif profil adını kontrol et (varsa app_settings'ten okunabilir veya son kullanılan saklanabilir)
            # Şimdilik basitçe ilk profili veya varsayılanı aktif yapalım
            if not profiles_data: # Eğer json boşsa {}
                 profiles_data = {default_profile_name: default_profile_data}; save_profiles()

            # TODO: Son kullanılan profili settings.json'a ekleyip oradan okumak daha iyi olabilir.
            # Şimdilik listedeki ilk profili veya varsayılanı aktif kabul edelim.
            if current_profile_name not in profiles_data:
                 current_profile_name = list(profiles_data.keys())[0]

            print(f"Profiles loaded from {config.PROFILE_FILE}. Active: {current_profile_name}")

        except Exception as e:
            print(f"Error loading profiles: {e}. Creating default."); profiles_data = {default_profile_name: default_profile_data}; current_profile_name = default_profile_name; save_profiles()
    else:
        print(f"Info: Profile file not found. Creating default."); profiles_data = {default_profile_name: default_profile_data}; current_profile_name = default_profile_name; save_profiles()

def save_profiles():
    """Global profiles_data sözlüğünü profiles.json dosyasına kaydeder."""
    global profiles_data # TODO: Sınıf yapısında global kullanım kaldırılacak
    try:
        with open(config.PROFILE_FILE, 'w', encoding='utf-8') as f: json.dump(profiles_data, f, indent=4, ensure_ascii=False)
        print(f"Profiles saved to {config.PROFILE_FILE}")
    except Exception as e: print(f"Error saving profiles: {e}")

# --- Sistem Teması Algılama ---
def get_system_theme():
    """Windows sistem temasını (açık/koyu) algılar."""
    if winreg and sys.platform == "win32":
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Themes\Personalize')
            value, _ = winreg.QueryValueEx(key, 'AppsUseLightTheme'); winreg.CloseKey(key)
            return "light" if value == 1 else "dark"
        except Exception: return "dark" # Hata durumunda varsayılan
    else: return "dark" # Windows dışı için varsayılan

# --- Pencereyi Ön Plana Getirme ---
def bring_window_to_front():
    """Uygulama penceresini ön plana getirir."""
    global root # TODO: root referansı argüman olarak alınmalı veya sınıf metodu olmalı
    if not root: return
    try:
        if sys.platform == "win32":
            hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
            ctypes.windll.user32.SetForegroundWindow(hwnd)
            print("Info: Window to front (Win).")
        else:
            root.lift(); root.focus_force()
            print("Info: Window to front (Other).")
    except Exception as e: print(f"Error bringing window to front: {e}")

# --- DPI Ölçekleme Faktörünü Alma (Şimdilik Kullanılmıyor ama burada durabilir) ---
def get_dpi_scale_factor(window):
    """Belirtilen pencerenin DPI ölçek faktörünü döndürür."""
    if sys.platform == "win32":
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
            dpi = ctypes.windll.shcore.GetDpiForWindow(int(window.winfo_id()))
            scale = dpi / config.BASE_DPI
            print(f"Detected DPI: {dpi}, Scale Factor: {scale:.2f}")
            return max(1.0, min(3.0, scale))
        except Exception as e:
            print(f"Error detecting DPI: {e}. Using default scale 1.0")
            return 1.0
    else:
        return 1.0

