import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import simpledialog
import sys
import ctypes
import json
import os
import math

try:
    from pyautocad import Autocad, APoint
except ImportError:
    Autocad = None; APoint = None
    print("Warning: 'pyautocad' library not found. AutoCAD interaction will be disabled. Install with 'pip install pyautocad'")
try:
    import winreg
except ImportError:
    winreg = None

# --- Ayarlar Dosyaları ---
SETTINGS_FILE = "settings.json"
PROFILE_FILE = "profiles.json"

# --- Tema Renkleri ---
themes = {
    "dark": {
        "sidebar_bg": '#2f3136', "content_bg": '#36393f', "sub_sidebar_bg": '#2a2c30',
        "menu_bar_bg": '#202225', "menu_bg": '#2f3136', "menu_fg": '#dcddde',
        "menu_active_bg": '#4f545c', "menu_active_fg": '#ffffff', "text": '#dcddde',
        "title_text": '#ffffff', "button_bg": '#5865f2', "button_fg": '#ffffff',
        "button_hover_bg": '#4752c4', "entry_bg": '#2f3136', "entry_fg": '#dcddde',
        "entry_border": '#40444b', "entry_insert": '#dcddde', "text_area_bg": '#2f3136',
        "text_area_fg": '#dcddde', "text_area_highlight": '#40444b', "check_indicator": '#5865f2',
        "check_fg": '#dcddde', "separator": '#40444b', "listbox_bg": '#2f3136',
        "listbox_fg": '#dcddde', "listbox_select_bg": '#4f545c',
    },
    "light": {
        "sidebar_bg": '#f2f3f5', "content_bg": '#ffffff', "sub_sidebar_bg": '#ebedf0',
        "menu_bar_bg": '#ffffff', "menu_bg": '#f2f3f5', "menu_fg": '#2e3338',
        "menu_active_bg": '#e3e5e8', "menu_active_fg": '#060607', "text": '#2e3338',
        "title_text": '#060607', "button_bg": '#747f8d', "button_fg": '#ffffff',
        "button_hover_bg": '#6a7480', "entry_bg": '#e3e5e8', "entry_fg": '#2e3338',
        "entry_border": '#cccccc', "entry_insert": '#2e3338', "text_area_bg": '#e3e5e8',
        "text_area_fg": '#2e3338', "text_area_highlight": '#cccccc', "check_indicator": '#747f8d',
        "check_fg": '#2e3338', "separator": '#d4d7dc', "listbox_bg": '#ffffff',
        "listbox_fg": '#2e3338', "listbox_select_bg": '#e3e5e8',
    }
}
# --- Standart Malzeme Özellikleri (MPa, N/mm²) ---
CONCRETE_PROPS = { "C20/25": {"fck": 20}, "C25/30": {"fck": 25}, "C30/37": {"fck": 30}, "C35/45": {"fck": 35}, "C40/50": {"fck": 40}, "C45/55": {"fck": 45}, "C50/60": {"fck": 50} }
REBAR_PROPS = { "B420C": {"fyk": 420, "Es": 200000}, "B500C": {"fyk": 500, "Es": 200000} }

# --- Global Değişkenler ---
current_theme_name = "dark"; current_theme = themes[current_theme_name]
current_view_func = None; autocad_status_message = "AutoCAD durumu kontrol ediliyor..."
connected_autocad_doc_name = None; acad_instance = None; app_settings = {}
profiles_data = {}; current_profile_name = "Varsayılan Profil"
sub_sidebar_frame = None; selected_area_points = None; shape_buttons_references = {}
# Ana widget referansları
root = None; pane = None; sidebar_frame = None; content_frame = None; style = None
app_title_label = None; custom_menu_bar = None; menu_buttons = {}; dropdown_menus = {}
# Sayfa değişkenleri/referansları
project_info_vars = {}; material_detail_vars = {}; material_listbox_ref = None
material_detail_widgets = {}; profile_listbox_ref = None
section_detail_vars = {}; section_listbox_ref = None # Kesit sayfası için
section_detail_widgets = {} # Kesit formu widget referansları

# ==============================================================================
# FONKSİYON TANIMLAMALARI
# ==============================================================================

# --- Ayarları Yükleme/Kaydetme ---
def load_settings():
    global app_settings
    default_settings = {"theme": get_system_theme(), "window_geometry": "1100x700+100+50"}
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f: loaded = json.load(f)
            app_settings = default_settings.copy(); app_settings.update(loaded)
            print(f"Settings loaded from {SETTINGS_FILE}")
        except Exception as e: print(f"Error loading settings: {e}. Using defaults."); app_settings = default_settings
    else: print(f"Info: Settings file not found. Using defaults."); app_settings = default_settings
def save_settings():
    global app_settings
    try:
        settings_to_save = { "theme": app_settings.get("theme", "dark"), "window_geometry": app_settings.get("window_geometry", "1100x700+100+50") }
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f: json.dump(settings_to_save, f, indent=4, ensure_ascii=False)
        print(f"Settings saved to {SETTINGS_FILE}")
    except Exception as e: print(f"Error saving settings: {e}")

# --- Profilleri Yükleme/Kaydetme ---
def load_profiles():
    global profiles_data, current_profile_name
    default_project_info = {"name": "Varsayılan Profil", "desc": "", "engineer": "", "concrete_reg": "TS 500 (2000)", "seismic_reg": "TBDY 2018", "load_reg": "TS 498 (1997)", "units": "Metrik (kN, m, C)"}
    default_profile_data = { "project_info": default_project_info, "materials": [], "sections": [] } # sections eklendi
    if os.path.exists(PROFILE_FILE):
        try:
            with open(PROFILE_FILE, 'r', encoding='utf-8') as f: profiles_data = json.load(f)
            if not isinstance(profiles_data, dict) or not profiles_data: print(f"Warning: Profile file empty/invalid. Creating default."); profiles_data = {current_profile_name: default_profile_data}; save_profiles()
            # Kayıtlı profillerden birini varsayılan yap (eğer aktif profil yoksa)
            if not profiles_data: profiles_data = {current_profile_name: default_profile_data}; save_profiles()
            current_profile_name = list(profiles_data.keys())[0] # İlk profili aktif yap
            print(f"Profiles loaded from {PROFILE_FILE}. Active: {current_profile_name}")
        except Exception as e: print(f"Error loading profiles: {e}. Creating default."); profiles_data = {current_profile_name: default_profile_data}; save_profiles()
    else: print(f"Info: Profile file not found. Creating default."); profiles_data = {current_profile_name: default_profile_data}; save_profiles()
def save_profiles():
    global profiles_data
    try:
        with open(PROFILE_FILE, 'w', encoding='utf-8') as f: json.dump(profiles_data, f, indent=4, ensure_ascii=False)
        print(f"Profiles saved to {PROFILE_FILE}")
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

# --- AutoCAD Yardımcı Fonksiyonları ---
def get_acad_instance():
    global acad_instance
    if not Autocad or sys.platform != "win32": acad_instance = None; return None
    try:
        if acad_instance and acad_instance.doc: _ = acad_instance.doc.Name; return acad_instance
        acad_instance = Autocad(create_if_not_exists=False); return acad_instance
    except Exception: acad_instance = None; return None
def get_autocad_variable(var_name, default_value):
    acad = get_acad_instance();
    if acad:
        try: return acad.doc.GetVariable(var_name)
        except Exception as e: print(f"Error getting ACAD var '{var_name}': {e}"); return default_value
    return default_value
def set_autocad_variable(var_name, value):
    acad = get_acad_instance()
    if acad:
        try:
            current_val = acad.doc.GetVariable(var_name)
            if isinstance(current_val, float): value = float(value)
            elif isinstance(current_val, int): value = int(value)
            acad.doc.SetVariable(var_name, value); print(f"Set ACAD var '{var_name}' to {value}"); return True
        except Exception as e: print(f"Error setting ACAD var '{var_name}': {e}"); return False
    else: print("Cannot set ACAD var, not connected."); return False

# --- AutoCAD Bağlantı Kontrolü ---
def check_autocad_connection():
    global connected_autocad_doc_name
    acad = get_acad_instance()
    if acad:
        try: doc_name = acad.doc.Name; connected_autocad_doc_name = doc_name; print(f"ACAD connected. Doc: {doc_name}"); return f"Bağlantı Başarılı (Doküman: {doc_name})"
        except Exception as e: connected_autocad_doc_name = None; print(f"ACAD Error: {e}"); return "Bağlantı kuruldu ancak doküman bilgisi alınamadı."
    else:
        connected_autocad_doc_name = None
        if not Autocad: return "Bağlantı kontrolü için 'pyautocad' kütüphanesi gerekli."
        if sys.platform != "win32": return "AutoCAD bağlantı kontrolü sadece Windows'ta desteklenir."
        return "Çalışan AutoCAD bulunamadı veya bağlantı kurulamadı."

# --- AutoCAD Durumunu Yenileme Fonksiyonu ---
def refresh_autocad_status():
    global autocad_status_message
    print("Refreshing AutoCAD status...")
    autocad_status_message = check_autocad_connection()
    if current_view_func: current_view_func()

# --- Tema Uygulama Fonksiyonu ---
def apply_theme(theme_name):
    global current_theme, current_theme_name, app_settings
    effective_theme_name = theme_name
    if theme_name == "system": effective_theme_name = get_system_theme()
    if effective_theme_name not in themes: effective_theme_name = "dark"
    needs_update = (current_theme_name != effective_theme_name) or (current_view_func is None)
    if not needs_update and current_view_func is not None: return

    current_theme_name = effective_theme_name
    current_theme = themes[current_theme_name]
    print(f"Applying theme: {current_theme_name}")
    app_settings["theme"] = current_theme_name

    if root: root.configure(bg=current_theme['content_bg'])
    if custom_menu_bar: custom_menu_bar.configure(bg=current_theme['menu_bar_bg'])
    if pane: pane.configure(bg=current_theme['content_bg'])
    if sidebar_frame: sidebar_frame.configure(bg=current_theme['sidebar_bg'])
    if content_frame: content_frame.configure(bg=current_theme['content_bg'])

    style.configure('TButton', font=('Segoe UI', 16), padding=(12, 12), foreground=current_theme['button_fg'], background=current_theme['button_bg'], borderwidth=0, relief='flat')
    style.map('TButton', foreground=[('active', current_theme['button_fg'])], background=[('active', current_theme['button_hover_bg'])], relief=[('pressed', 'flat'), ('active', 'flat')])
    style.configure('Sub.TButton', font=('Segoe UI', 14), padding=(6, 6), foreground=current_theme['text'], background=current_theme['sub_sidebar_bg'], borderwidth=0, relief='flat')
    style.map('Sub.TButton', foreground=[('active', current_theme['button_fg'])], background=[('active', current_theme['button_hover_bg'])], relief=[('pressed', 'flat'), ('active', 'flat')])
    style.configure('TEntry', font=('Segoe UI', 14), fieldbackground=current_theme['entry_bg'], foreground=current_theme['entry_fg'], bordercolor=current_theme['entry_border'], insertcolor=current_theme['entry_insert'], borderwidth=1, relief='flat')
    style.map('TEntry', bordercolor=[('focus', current_theme['button_bg'])])
    style.configure('Header.TLabel', font=('Segoe UI', 16, 'bold'), background=current_theme['content_bg'], foreground=current_theme['title_text'])
    style.configure('TSeparator', background=current_theme['separator'])
    style.configure('TCombobox', font=('Segoe UI', 14))

    if app_title_label: app_title_label.configure(background=current_theme['sidebar_bg'], foreground=current_theme['title_text'], font=("Segoe UI", 22, "bold"))

    menu_font_size = 11
    for mb in menu_buttons.values(): mb.configure(bg=current_theme['menu_bar_bg'], fg=current_theme['menu_fg'], activebackground=current_theme['menu_active_bg'], activeforeground=current_theme['menu_active_fg'], font=('Segoe UI', menu_font_size))
    for menu in dropdown_menus.values(): menu.configure(bg=current_theme['menu_bg'], fg=current_theme['menu_fg'], activebackground=current_theme['menu_active_bg'], activeforeground=current_theme['menu_active_fg'], font=('Segoe UI', menu_font_size))

    save_settings()
    if current_view_func and needs_update: current_view_func()

# --- Uygulama Kapatma İşlemi ---
def on_closing():
    global app_settings
    print("Saving settings and exiting application...")
    try: current_geometry = root.winfo_geometry(); app_settings['window_geometry'] = current_geometry; save_settings()
    except Exception as e: print(f"Error saving settings on closing: {e}")
    finally: root.destroy()

# --- İçerik Alanı Widget Oluşturma Fonksiyonları ---
def create_content_label(parent, text):
    return ttk.Label(parent, text=text, font=("Segoe UI", 24), background=current_theme['content_bg'], foreground=current_theme['title_text'])
def create_content_text(parent, text, size=14):
     if "Version" in text: size = 10
     return ttk.Label(parent, text=text, font=("Segoe UI", size), background=current_theme['content_bg'], foreground=current_theme['text'])
def create_content_button(parent, text, command=None):
     is_sub_button = False
     try:
         if parent.cget('bg') == current_theme['sub_sidebar_bg']: is_sub_button = True
     except (AttributeError, tk.TclError): pass
     if is_sub_button: return ttk.Button(parent, text=text, command=command, style='Sub.TButton')
     else: return ttk.Button(parent, text=text, command=command, style='TButton')
def create_content_entry(parent, width=None, textvariable=None):
     entry = ttk.Entry(parent, font=("Segoe UI", 14), style='TEntry', width=width, textvariable=textvariable)
     return entry
def create_content_combobox(parent, values, state='readonly', width=None, textvariable=None):
     combo = ttk.Combobox(parent, values=values, state=state, width=width, style='TCombobox', font=('Segoe UI', 14), textvariable=textvariable)
     return combo
def create_custom_checkbutton(parent, text, variable, command=None, state=tk.NORMAL):
    check_frame = tk.Frame(parent, bg=current_theme['content_bg'])
    check_char_selected = "☑"; check_char_deselected = "☐"; check_font_size = 18
    check_label = tk.Label(check_frame, font=("Segoe UI Symbol", check_font_size), bg=current_theme['content_bg'], fg=current_theme['check_indicator'])
    text_label = ttk.Label(check_frame, text=text, font=("Segoe UI", 15), background=current_theme['content_bg'], foreground=current_theme['check_fg'])
    def update_visual():
        if variable.get() == 1: check_label.config(text=check_char_selected)
        else: check_label.config(text=check_char_deselected)
        current_state = tk.NORMAL if state == tk.NORMAL else tk.DISABLED
        check_label.config(state=current_state); text_label.config(state=current_state)
    check_frame.update_visual_func = update_visual
    def toggle():
        if check_label.cget("state") == tk.DISABLED: return
        variable.set(1 - variable.get()); update_visual()
        if command: command()
    check_label.bind("<Button-1>", lambda e: toggle()); text_label.bind("<Button-1>", lambda e: toggle())
    check_label.pack(side=tk.LEFT); text_label.pack(side=tk.LEFT, padx=(5, 0))
    update_visual(); return check_frame

# --- Yardımcı Fonksiyon: AutoCAD Alt Menüsü Oluşturma ---
def create_autocad_sub_sidebar(parent_frame):
    global sub_sidebar_frame
    sub_sidebar_frame = tk.Frame(parent_frame, height=65, bg=current_theme['sub_sidebar_bg'])
    sub_sidebar_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 10)); sub_sidebar_frame.pack_propagate(False)
    home_button = create_content_button(sub_sidebar_frame, "Ana Sayfa"); home_button.configure(command=show_autocad_home); home_button.pack(side=tk.LEFT, padx=10, pady=7)
    test_button = create_content_button(sub_sidebar_frame, "Test Alanı"); test_button.configure(command=show_autocad_test_area); test_button.pack(side=tk.LEFT, padx=10, pady=7)
    btn1 = create_content_button(sub_sidebar_frame, "Çizim Temizle"); btn1.pack(side=tk.LEFT, padx=10, pady=7)
    btn2 = create_content_button(sub_sidebar_frame, "Layer Yönetimi"); btn2.pack(side=tk.LEFT, padx=10, pady=7)
    btn3 = create_content_button(sub_sidebar_frame, "Blok İşlemleri"); btn3.pack(side=tk.LEFT, padx=10, pady=7)
    return sub_sidebar_frame

# --- Yardımcı Fonksiyon: Hesaplamalar Alt Menüsü Oluşturma ---
def create_calculations_sub_sidebar(parent_frame):
    global sub_sidebar_frame
    sub_sidebar_frame = tk.Frame(parent_frame, height=65, bg=current_theme['sub_sidebar_bg'])
    sub_sidebar_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 10)); sub_sidebar_frame.pack_propagate(False)
    btn_profile = create_content_button(sub_sidebar_frame, "Profiller"); btn_profile.configure(command=show_calc_profiles); btn_profile.pack(side=tk.LEFT, padx=10, pady=7)
    btn_proj = create_content_button(sub_sidebar_frame, "Proje Bilgileri"); btn_proj.configure(command=show_calc_project_info); btn_proj.pack(side=tk.LEFT, padx=10, pady=7)
    btn_mat = create_content_button(sub_sidebar_frame, "Malzemeler"); btn_mat.configure(command=show_calc_materials); btn_mat.pack(side=tk.LEFT, padx=10, pady=7)
    btn_sec = create_content_button(sub_sidebar_frame, "Kesitler"); btn_sec.configure(command=show_calc_sections); btn_sec.pack(side=tk.LEFT, padx=10, pady=7)
    btn_elem = create_content_button(sub_sidebar_frame, "Tekil Eleman"); btn_elem.configure(command=show_calc_element_design); btn_elem.pack(side=tk.LEFT, padx=10, pady=7)
    btn_seismic = create_content_button(sub_sidebar_frame, "Deprem Yükü"); btn_seismic.configure(command=show_calc_seismic); btn_seismic.pack(side=tk.LEFT, padx=10, pady=7)
    btn_report = create_content_button(sub_sidebar_frame, "Raporlama"); btn_report.configure(command=show_calc_reporting); btn_report.pack(side=tk.LEFT, padx=10, pady=7)
    return sub_sidebar_frame

# --- Malzeme Sayfası Yardımcı Fonksiyonları ---
def clear_material_form():
    material_detail_vars.get("user_name", tk.StringVar()).set("")
    material_detail_vars.get("type", tk.StringVar()).set("Beton")
    material_detail_vars.get("class", tk.StringVar()).set("")
    material_detail_vars.get("is_custom", tk.IntVar()).set(0)
    material_detail_vars.get("fck", tk.DoubleVar()).set(0.0)
    material_detail_vars.get("fyk", tk.DoubleVar()).set(0.0)
    material_detail_vars.get("Ec", tk.DoubleVar()).set(0.0)
    material_detail_vars.get("Es", tk.DoubleVar()).set(0.0)
    if material_listbox_ref:
        selection = material_listbox_ref.curselection()
        if selection: material_listbox_ref.selection_clear(selection[0])
    on_material_type_change(); on_custom_material_toggle()

def update_material_listbox():
    if material_listbox_ref and current_profile_name in profiles_data:
        material_listbox_ref.delete(0, tk.END)
        materials = profiles_data[current_profile_name].get("materials", [])
        materials.sort(key=lambda x: x.get("user_name", "").lower())
        for mat in materials:
            display_name = f"{mat.get('type', '?')}: {mat.get('user_name', 'İsimsiz')} ({mat.get('class', 'Özel')})"
            material_listbox_ref.insert(tk.END, display_name)

def on_material_type_change():
    if not material_detail_widgets: return
    mat_type = material_detail_vars.get("type", tk.StringVar()).get()
    is_concrete = (mat_type == "Beton")
    # Alanları göster/gizle (grid kullanarak)
    row_concrete = 2 # Beton sınıfı ve özel checkbox'ı için satır
    row_rebar = 2    # Donatı sınıfı ve özel checkbox'ı için satır
    row_fck = 3      # fck için satır
    row_fyk = 3      # fyk için satır
    row_Es = 4       # Es için satır

    # Önce tüm widget'ları gizle
    for w in material_detail_widgets.values():
        w.grid_remove()

    # İlgili widget'ları göster
    if is_concrete:
        material_detail_widgets["lbl_concrete_class"].grid(row=row_concrete, column=0, sticky='w', padx=5, pady=5)
        material_detail_widgets["combo_concrete_class"].grid(row=row_concrete, column=1, sticky='ew', padx=5, pady=5)
        material_detail_widgets["chk_custom_concrete"].grid(row=row_concrete, column=2, sticky='w', padx=5, pady=5)
        material_detail_widgets["lbl_fck"].grid(row=row_fck, column=0, sticky='w', padx=5, pady=5)
        material_detail_widgets["entry_fck"].grid(row=row_fck, column=1, sticky='w', padx=5, pady=5)
    else: # Donatı
        material_detail_widgets["lbl_rebar_class"].grid(row=row_rebar, column=0, sticky='w', padx=5, pady=5)
        material_detail_widgets["combo_rebar_class"].grid(row=row_rebar, column=1, sticky='ew', padx=5, pady=5)
        material_detail_widgets["chk_custom_rebar"].grid(row=row_rebar, column=2, sticky='w', padx=5, pady=5)
        material_detail_widgets["lbl_fyk"].grid(row=row_fyk, column=0, sticky='w', padx=5, pady=5)
        material_detail_widgets["entry_fyk"].grid(row=row_fyk, column=1, sticky='w', padx=5, pady=5)
        material_detail_widgets["lbl_Es"].grid(row=row_Es, column=0, sticky='w', padx=5, pady=5)
        material_detail_widgets["entry_Es"].grid(row=row_Es, column=1, sticky='w', padx=5, pady=5)

    # Combobox içeriğini güncelle
    material_detail_vars.get("class", tk.StringVar()).set("")
    if is_concrete and material_detail_widgets.get("combo_concrete_class"): material_detail_widgets["combo_concrete_class"]["values"] = list(CONCRETE_PROPS.keys())
    elif not is_concrete and material_detail_widgets.get("combo_rebar_class"): material_detail_widgets["combo_rebar_class"]["values"] = list(REBAR_PROPS.keys())
    on_custom_material_toggle()

def on_material_class_change():
    if material_detail_vars.get("is_custom", tk.IntVar()).get() == 1: return
    mat_type = material_detail_vars.get("type", tk.StringVar()).get()
    mat_class = material_detail_vars.get("class", tk.StringVar()).get()
    if mat_type == "Beton" and mat_class in CONCRETE_PROPS:
        props = CONCRETE_PROPS[mat_class]; material_detail_vars.get("fck", tk.DoubleVar()).set(props.get("fck", 0.0))
    elif mat_type == "Donatı Çeliği" and mat_class in REBAR_PROPS:
        props = REBAR_PROPS[mat_class]; material_detail_vars.get("fyk", tk.DoubleVar()).set(props.get("fyk", 0.0)); material_detail_vars.get("Es", tk.DoubleVar()).set(props.get("Es", 0.0))
    else:
         if mat_type == "Beton": material_detail_vars.get("fck", tk.DoubleVar()).set(0.0)
         else: material_detail_vars.get("fyk", tk.DoubleVar()).set(0.0); material_detail_vars.get("Es", tk.DoubleVar()).set(0.0)

def on_custom_material_toggle():
    if not material_detail_widgets: return
    is_custom = material_detail_vars.get("is_custom", tk.IntVar()).get() == 1
    mat_type = material_detail_vars.get("type", tk.StringVar()).get()
    prop_state = tk.NORMAL if is_custom else tk.DISABLED; class_combo_state = tk.DISABLED if is_custom else 'readonly'
    if mat_type == "Beton":
        if material_detail_widgets.get("entry_fck"): material_detail_widgets["entry_fck"].config(state=prop_state)
        if material_detail_widgets.get("combo_concrete_class"): material_detail_widgets["combo_concrete_class"].config(state=class_combo_state)
        if is_custom: material_detail_vars.get("class", tk.StringVar()).set("Özel"); material_detail_vars.get("fck", tk.DoubleVar()).set(0.0) # Özel seçilince sınıfı ayarla ve değeri sıfırla
        else: on_material_class_change() # Standart seçilince sınıfı ve değeri güncelle
    else: # Donatı
        if material_detail_widgets.get("entry_fyk"): material_detail_widgets["entry_fyk"].config(state=prop_state)
        if material_detail_widgets.get("entry_Es"): material_detail_widgets["entry_Es"].config(state=prop_state)
        if material_detail_widgets.get("combo_rebar_class"): material_detail_widgets["combo_rebar_class"].config(state=class_combo_state)
        if is_custom: material_detail_vars.get("class", tk.StringVar()).set("Özel"); material_detail_vars.get("fyk", tk.DoubleVar()).set(0.0); material_detail_vars.get("Es", tk.DoubleVar()).set(0.0)
        else: on_material_class_change()

def save_material_from_form():
    global profiles_data, current_profile_name
    if not current_profile_name: messagebox.showerror("Hata", "Aktif profil bulunamadı."); return
    user_name = material_detail_vars.get("user_name", tk.StringVar()).get().strip()
    if not user_name: messagebox.showerror("Hata", "Malzeme adı boş olamaz."); return
    mat_type = material_detail_vars.get("type", tk.StringVar()).get()
    is_custom = material_detail_vars.get("is_custom", tk.IntVar()).get() == 1
    mat_class = "Özel" if is_custom else material_detail_vars.get("class", tk.StringVar()).get()
    if not is_custom and not mat_class: messagebox.showerror("Hata", "Lütfen bir malzeme sınıfı seçin."); return # Standartsa sınıf seçilmeli
    props = {}
    try:
        if mat_type == "Beton": props["fck"] = material_detail_vars.get("fck", tk.DoubleVar()).get()
        else: props["fyk"] = material_detail_vars.get("fyk", tk.DoubleVar()).get(); props["Es"] = material_detail_vars.get("Es", tk.DoubleVar()).get()
    except tk.TclError: messagebox.showerror("Hata", "Lütfen geçerli sayısal malzeme özellikleri girin."); return

    new_material_data = {"user_name": user_name, "type": mat_type, "class": mat_class, "is_custom": is_custom, "props": props}
    profile = profiles_data.setdefault(current_profile_name, {"project_info": {}, "materials": [], "sections": []})
    materials = profile.setdefault("materials", [])
    selected_index = -1; original_name_if_editing = None
    if material_listbox_ref: selection = material_listbox_ref.curselection();
    if selection: selected_index = selection[0]
    if selected_index != -1:
        try: original_name_if_editing = materials[selected_index].get("user_name")
        except IndexError: selected_index = -1 # Liste değişmiş olabilir, indeksi sıfırla
    found_index = -1
    for i, mat in enumerate(materials):
        if mat.get("user_name") == user_name: found_index = i; break

    if user_name == original_name_if_editing or found_index == -1:
        if selected_index != -1 and original_name_if_editing is not None: # Düzenleme
             try: materials[selected_index] = new_material_data; print(f"Material '{user_name}' updated.")
             except IndexError: materials.append(new_material_data); print(f"Material '{user_name}' added (update failed, added as new).")
        else: # Yeni malzeme ekleme
             materials.append(new_material_data); print(f"Material '{user_name}' added.")
        save_profiles(); update_material_listbox(); clear_material_form(); messagebox.showinfo("Başarılı", f"Malzeme '{user_name}' kaydedildi.")
    else: messagebox.showerror("Hata", f"'{user_name}' adında başka bir malzeme zaten var.")

def load_selected_material_to_form():
    if not material_listbox_ref: return
    selection = material_listbox_ref.curselection()
    if not selection: return
    selected_index = selection[0]
    materials = profiles_data.get(current_profile_name, {}).get("materials", [])
    if selected_index < 0 or selected_index >= len(materials): messagebox.showerror("Hata", "Seçilen malzeme verisi bulunamadı."); return
    material_data = materials[selected_index]
    material_detail_vars.get("user_name", tk.StringVar()).set(material_data.get("user_name", ""))
    material_detail_vars.get("type", tk.StringVar()).set(material_data.get("type", "Beton"))
    material_detail_vars.get("is_custom", tk.IntVar()).set(1 if material_data.get("is_custom") else 0)
    # Sınıfı ayarlamadan önce tipi ayarlamak önemli
    on_material_type_change() # Bu, doğru combobox'ı ve alanları gösterir
    material_detail_vars.get("class", tk.StringVar()).set(material_data.get("class", ""))
    props = material_data.get("props", {})
    if material_data.get("type") == "Beton": material_detail_vars.get("fck", tk.DoubleVar()).set(props.get("fck", 0.0))
    else: material_detail_vars.get("fyk", tk.DoubleVar()).set(props.get("fyk", 0.0)); material_detail_vars.get("Es", tk.DoubleVar()).set(props.get("Es", 0.0))
    on_custom_material_toggle() # Özel durumuna göre alanları etkinleştir/devre dışı bırak

def delete_selected_material():
    global profiles_data
    if not material_listbox_ref: return
    selection = material_listbox_ref.curselection()
    if not selection: messagebox.showwarning("Malzeme Seçilmedi", "Lütfen silinecek malzemeyi seçin."); return
    selected_index = selection[0]
    profile = profiles_data.get(current_profile_name)
    if profile and "materials" in profile and 0 <= selected_index < len(profile["materials"]):
        material_to_delete = profile["materials"][selected_index]
        user_name_to_delete = material_to_delete.get("user_name", "Bilinmeyen")
        if messagebox.askyesno("Malzeme Sil", f"'{user_name_to_delete}' malzemesini silmek istediğinizden emin misiniz?", parent=root):
            del profile["materials"][selected_index]
            save_profiles(); update_material_listbox(); clear_material_form()
            messagebox.showinfo("Başarılı", f"'{user_name_to_delete}' malzemesi silindi.")
    else: messagebox.showerror("Hata", "Malzeme silinemedi.")

# --- Kesit Sayfası Yardımcı Fonksiyonları (YENİ) ---
def clear_section_form():
    """Kesit detay formunu temizler."""
    section_detail_vars.get("user_name", tk.StringVar()).set("")
    section_detail_vars.get("geom_type", tk.StringVar()).set("Dikdörtgen") # Varsayılan
    section_detail_vars.get("dim_b", tk.DoubleVar()).set(0.0)
    section_detail_vars.get("dim_h", tk.DoubleVar()).set(0.0)
    section_detail_vars.get("dim_D", tk.DoubleVar()).set(0.0)
    section_detail_vars.get("cover", tk.DoubleVar()).set(30.0) # Varsayılan paspayı
    # Hesaplanan özellik etiketlerini temizle (varsa)
    if section_detail_widgets.get("prop_area"): section_detail_widgets["prop_area"].config(text="-")
    if section_detail_widgets.get("prop_ix"): section_detail_widgets["prop_ix"].config(text="-")
    if section_detail_widgets.get("prop_iy"): section_detail_widgets["prop_iy"].config(text="-")
    # Listbox seçimini kaldır
    if section_listbox_ref:
        selection = section_listbox_ref.curselection()
        if selection: section_listbox_ref.selection_clear(selection[0])
    on_section_type_change() # Doğru boyut alanlarını göster

def update_section_listbox():
    """Kesit listesini güncel profilden doldurur."""
    if section_listbox_ref and current_profile_name in profiles_data:
        section_listbox_ref.delete(0, tk.END)
        sections = profiles_data[current_profile_name].get("sections", [])
        sections.sort(key=lambda x: x.get("user_name", "").lower())
        for sec in sections:
            # Listede gösterilecek isim (örn: "Dikdörtgen: Kiriş 25x50")
            display_name = f"{sec.get('geom_type', '?')}: {sec.get('user_name', 'İsimsiz')}"
            section_listbox_ref.insert(tk.END, display_name)

def on_section_type_change():
    """Kesit tipi değiştikçe ilgili boyut alanlarını gösterir/gizler."""
    if not section_detail_widgets: return
    geom_type = section_detail_vars.get("geom_type", tk.StringVar()).get()

    # Tüm boyut çerçevelerini gizle
    if section_detail_widgets.get("rect_dim_frame"): section_detail_widgets["rect_dim_frame"].grid_remove()
    if section_detail_widgets.get("circ_dim_frame"): section_detail_widgets["circ_dim_frame"].grid_remove()
    # TODO: T ve L kesit çerçeveleri eklendiğinde buraya gelecek

    # İlgili çerçeveyi göster
    if geom_type == "Dikdörtgen" and section_detail_widgets.get("rect_dim_frame"):
        section_detail_widgets["rect_dim_frame"].grid()
    elif geom_type == "Dairesel" and section_detail_widgets.get("circ_dim_frame"):
        section_detail_widgets["circ_dim_frame"].grid()
    # TODO: T ve L kesitleri için elif blokları

def load_selected_section_to_form():
    """Listeden seçilen kesiti forma yükler."""
    if not section_listbox_ref: return
    selection = section_listbox_ref.curselection()
    if not selection: return
    selected_index = selection[0]

    sections = profiles_data.get(current_profile_name, {}).get("sections", [])
    if selected_index < 0 or selected_index >= len(sections):
        messagebox.showerror("Hata", "Seçilen kesit verisi bulunamadı.")
        return
    section_data = sections[selected_index]

    # Formu doldur
    section_detail_vars.get("user_name", tk.StringVar()).set(section_data.get("user_name", ""))
    section_detail_vars.get("geom_type", tk.StringVar()).set(section_data.get("geom_type", "Dikdörtgen"))
    section_detail_vars.get("cover", tk.DoubleVar()).set(section_data.get("cover", 30.0))

    dims = section_data.get("dimensions", {})
    section_detail_vars.get("dim_b", tk.DoubleVar()).set(dims.get("b", 0.0))
    section_detail_vars.get("dim_h", tk.DoubleVar()).set(dims.get("h", 0.0))
    section_detail_vars.get("dim_D", tk.DoubleVar()).set(dims.get("D", 0.0))
    # TODO: T ve L kesit boyutları

    # Hesaplanan özellikleri göster (şimdilik placeholder)
    props = section_data.get("properties", {})
    if section_detail_widgets.get("prop_area"): section_detail_widgets["prop_area"].config(text=str(props.get("Area", "-")))
    if section_detail_widgets.get("prop_ix"): section_detail_widgets["prop_ix"].config(text=str(props.get("Ix", "-")))
    if section_detail_widgets.get("prop_iy"): section_detail_widgets["prop_iy"].config(text=str(props.get("Iy", "-")))


    on_section_type_change() # Doğru boyut alanlarını göster

def save_section_from_form():
    """Formdaki verileri alıp aktif profile kesit olarak kaydeder/günceller."""
    global profiles_data, current_profile_name
    if not current_profile_name: messagebox.showerror("Hata", "Aktif profil bulunamadı."); return

    user_name = section_detail_vars.get("user_name", tk.StringVar()).get().strip()
    if not user_name: messagebox.showerror("Hata", "Kesit adı boş olamaz."); return

    geom_type = section_detail_vars.get("geom_type", tk.StringVar()).get()
    dimensions = {}
    cover = 30.0 # Varsayılan
    try:
        cover = section_detail_vars.get("cover", tk.DoubleVar()).get()
        if geom_type == "Dikdörtgen":
            dimensions["b"] = section_detail_vars.get("dim_b", tk.DoubleVar()).get()
            dimensions["h"] = section_detail_vars.get("dim_h", tk.DoubleVar()).get()
            if dimensions["b"] <= 0 or dimensions["h"] <= 0: raise ValueError("Boyutlar pozitif olmalı.")
        elif geom_type == "Dairesel":
            dimensions["D"] = section_detail_vars.get("dim_D", tk.DoubleVar()).get()
            if dimensions["D"] <= 0: raise ValueError("Çap pozitif olmalı.")
        # TODO: T ve L kesit boyutları
        if cover < 0: raise ValueError("Paspayı negatif olamaz.")

    except (tk.TclError, ValueError) as e:
        messagebox.showerror("Hata", f"Lütfen geçerli sayısal boyut/paspayı girin.\n{e}")
        return

    # Yeni kesit verisi (hesaplanan özellikler şimdilik boş)
    new_section_data = {
        "user_name": user_name,
        "geom_type": geom_type,
        "dimensions": dimensions,
        "cover": cover,
        "properties": {} # Hesaplama sonra eklenecek
    }

    profile = profiles_data.setdefault(current_profile_name, {"project_info": {}, "materials": [], "sections": []})
    sections = profile.setdefault("sections", [])

    selected_index = -1; original_name_if_editing = None
    if section_listbox_ref: selection = section_listbox_ref.curselection();
    if selection: selected_index = selection[0]
    if selected_index != -1:
        try: original_name_if_editing = sections[selected_index].get("user_name")
        except IndexError: selected_index = -1
    found_index = -1
    for i, sec in enumerate(sections):
        if sec.get("user_name") == user_name: found_index = i; break

    if user_name == original_name_if_editing or found_index == -1:
        if selected_index != -1 and original_name_if_editing is not None: # Düzenleme
             try: sections[selected_index] = new_section_data; print(f"Section '{user_name}' updated.")
             except IndexError: sections.append(new_section_data); print(f"Section '{user_name}' added (update failed, added as new).")
        else: # Yeni kesit ekleme
             sections.append(new_section_data); print(f"Section '{user_name}' added.")
        save_profiles(); update_section_listbox(); clear_section_form(); messagebox.showinfo("Başarılı", f"Kesit '{user_name}' kaydedildi.")
    else: messagebox.showerror("Hata", f"'{user_name}' adında başka bir kesit zaten var.")


def delete_selected_section():
    """Listeden seçilen kesiti profilden siler."""
    global profiles_data
    if not section_listbox_ref: return
    selection = section_listbox_ref.curselection()
    if not selection: messagebox.showwarning("Kesit Seçilmedi", "Lütfen silinecek kesiti seçin."); return
    selected_index = selection[0]

    profile = profiles_data.get(current_profile_name)
    if profile and "sections" in profile and 0 <= selected_index < len(profile["sections"]):
        section_to_delete = profile["sections"][selected_index]
        user_name_to_delete = section_to_delete.get("user_name", "Bilinmeyen")
        if messagebox.askyesno("Kesiti Sil", f"'{user_name_to_delete}' kesitini silmek istediğinizden emin misiniz?", parent=root):
            del profile["sections"][selected_index]
            save_profiles(); update_section_listbox(); clear_section_form()
            messagebox.showinfo("Başarılı", f"'{user_name_to_delete}' kesiti silindi.")
    else: messagebox.showerror("Hata", "Kesit silinemedi.")


# --- Sayfa İçeriklerini Oluşturan Fonksiyonlar ---
# ... (populate_project_info_page ve populate_material_page aynı kaldı) ...
def populate_project_info_page(parent_frame):
    global project_info_vars
    project_info_vars = { "name": tk.StringVar(), "desc": tk.StringVar(), "engineer": tk.StringVar(), "concrete_reg": tk.StringVar(), "seismic_reg": tk.StringVar(), "load_reg": tk.StringVar(), "units": tk.StringVar() }
    parent_frame.columnconfigure(1, weight=1)
    ttk.Label(parent_frame, text="Proje Adı:", style='Header.TLabel').grid(row=0, column=0, padx=10, pady=8, sticky='w')
    create_content_entry(parent_frame, textvariable=project_info_vars["name"]).grid(row=0, column=1, padx=10, pady=8, sticky='ew')
    ttk.Label(parent_frame, text="Açıklama:", style='Header.TLabel').grid(row=1, column=0, padx=10, pady=8, sticky='nw')
    desc_text = tk.Text(parent_frame, height=4, width=40, font=("Segoe UI", 14), relief='flat', bd=1, bg=current_theme['text_area_bg'], fg=current_theme['text_area_fg'], insertbackground=current_theme['entry_insert'], highlightthickness=1, highlightbackground=current_theme['entry_border'], highlightcolor=current_theme['button_bg'])
    desc_text.grid(row=1, column=1, padx=10, pady=8, sticky='nsew'); parent_frame.rowconfigure(1, weight=1)
    project_info_vars["desc_widget"] = desc_text
    ttk.Label(parent_frame, text="Mühendis/Firma:", style='Header.TLabel').grid(row=2, column=0, padx=10, pady=8, sticky='w')
    create_content_entry(parent_frame, textvariable=project_info_vars["engineer"]).grid(row=2, column=1, padx=10, pady=8, sticky='ew')
    ttk.Label(parent_frame, text="Betonarme Yön.:", style='Header.TLabel').grid(row=3, column=0, padx=10, pady=8, sticky='w')
    combo_concrete = create_content_combobox(parent_frame, ["TS 500 (2000)"], textvariable=project_info_vars["concrete_reg"]);
    if combo_concrete['values']: combo_concrete.current(0); combo_concrete.grid(row=3, column=1, padx=10, pady=8, sticky='ew')
    ttk.Label(parent_frame, text="Deprem Yön.:", style='Header.TLabel').grid(row=4, column=0, padx=10, pady=8, sticky='w')
    combo_seismic = create_content_combobox(parent_frame, ["TBDY 2018"], textvariable=project_info_vars["seismic_reg"]);
    if combo_seismic['values']: combo_seismic.current(0); combo_seismic.grid(row=4, column=1, padx=10, pady=8, sticky='ew')
    ttk.Label(parent_frame, text="Yük Yön.:", style='Header.TLabel').grid(row=5, column=0, padx=10, pady=8, sticky='w')
    combo_load = create_content_combobox(parent_frame, ["TS 498 (1997)"], textvariable=project_info_vars["load_reg"]);
    if combo_load['values']: combo_load.current(0); combo_load.grid(row=5, column=1, padx=10, pady=8, sticky='ew')
    ttk.Label(parent_frame, text="Birim Sistemi:", style='Header.TLabel').grid(row=6, column=0, padx=10, pady=8, sticky='w')
    combo_unit = create_content_combobox(parent_frame, ["Metrik (kN, m, C)"], textvariable=project_info_vars["units"]);
    if combo_unit['values']: combo_unit.current(0); combo_unit.grid(row=6, column=1, padx=10, pady=8, sticky='ew')
    save_button = ttk.Button(parent_frame, text="Profili Kaydet", command=save_project_info, style='TButton')
    save_button.grid(row=7, column=1, padx=10, pady=20, sticky='e')
    load_project_info()

def populate_material_page(parent_frame):
    # ... (Kod aynı kaldı) ...
    global material_listbox_ref, material_detail_vars, material_detail_widgets
    material_detail_vars = { "user_name": tk.StringVar(), "type": tk.StringVar(value="Beton"), "class": tk.StringVar(), "is_custom": tk.IntVar(value=0), "fck": tk.DoubleVar(), "fyk": tk.DoubleVar(), "Ec": tk.DoubleVar(), "Es": tk.DoubleVar() }
    material_detail_widgets = {}
    mat_pane = tk.PanedWindow(parent_frame, bd=0, sashwidth=4, sashrelief=tk.FLAT, orient=tk.HORIZONTAL, bg=current_theme['content_bg'])
    mat_pane.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    list_frame = tk.Frame(mat_pane, bg=current_theme['content_bg']); mat_pane.add(list_frame, width=300, stretch="never")
    ttk.Label(list_frame, text="Tanımlı Malzemeler:", style='Header.TLabel').pack(anchor='w', padx=5, pady=(0,5))
    listbox = tk.Listbox(list_frame, height=15, font=("Segoe UI", 14), relief='flat', bd=1, bg=current_theme['listbox_bg'], fg=current_theme['listbox_fg'], selectbackground=current_theme['listbox_select_bg'], selectforeground=current_theme['title_text'], highlightthickness=1, highlightbackground=current_theme['entry_border'], exportselection=False)
    listbox.pack(fill=tk.BOTH, expand=True, padx=5); material_listbox_ref = listbox
    listbox.bind('<<ListboxSelect>>', lambda e: load_selected_material_to_form())
    button_frame = tk.Frame(list_frame, bg=current_theme['content_bg']); button_frame.pack(fill=tk.X, pady=5, padx=5)
    ttk.Button(button_frame, text="Yeni", style='TButton', width=6, command=clear_material_form).pack(side=tk.LEFT, padx=2); ttk.Button(button_frame, text="Düzenle", style='TButton', width=6, command=load_selected_material_to_form).pack(side=tk.LEFT, padx=2); ttk.Button(button_frame, text="Sil", style='TButton', width=6, command=delete_selected_material).pack(side=tk.LEFT, padx=2)
    detail_frame = tk.Frame(mat_pane, bg=current_theme['content_bg']); mat_pane.add(detail_frame, stretch="always")
    ttk.Label(detail_frame, text="Malzeme Detayları:", style='Header.TLabel').grid(row=0, column=0, columnspan=3, sticky='w', padx=10, pady=(0,10))
    detail_form_frame = tk.Frame(detail_frame, bg=current_theme['content_bg']); detail_form_frame.grid(row=1, column=0, sticky='nsew', padx=10); detail_frame.rowconfigure(1, weight=1); detail_frame.columnconfigure(0, weight=1); detail_form_frame.columnconfigure(1, weight=1)
    ttk.Label(detail_form_frame, text="Malzeme Adı:", style='Header.TLabel').grid(row=0, column=0, sticky='w', padx=5, pady=5)
    entry_name = create_content_entry(detail_form_frame, textvariable=material_detail_vars["user_name"]); entry_name.grid(row=0, column=1, columnspan=2, sticky='ew', padx=5, pady=5); material_detail_widgets["entry_name"] = entry_name
    ttk.Label(detail_form_frame, text="Malzeme Tipi:", style='Header.TLabel').grid(row=1, column=0, sticky='w', padx=5, pady=5)
    combo_type = create_content_combobox(detail_form_frame, ["Beton", "Donatı Çeliği"], textvariable=material_detail_vars["type"]); combo_type.bind("<<ComboboxSelected>>", lambda e: on_material_type_change()); combo_type.grid(row=1, column=1, columnspan=2, sticky='ew', padx=5, pady=5); material_detail_widgets["combo_type"] = combo_type
    # Beton Alanları
    lbl_concrete_class = ttk.Label(detail_form_frame, text="Beton Sınıfı:", style='Header.TLabel'); material_detail_widgets["lbl_concrete_class"] = lbl_concrete_class; lbl_concrete_class.grid(row=2, column=0, sticky='w', padx=5, pady=5)
    combo_concrete_class = create_content_combobox(detail_form_frame, list(CONCRETE_PROPS.keys()), textvariable=material_detail_vars["class"]); material_detail_widgets["combo_concrete_class"] = combo_concrete_class; combo_concrete_class.bind("<<ComboboxSelected>>", lambda e: on_material_class_change()); combo_concrete_class.grid(row=2, column=1, sticky='ew', padx=5, pady=5)
    chk_custom_concrete = create_custom_checkbutton(detail_form_frame, "Özel", material_detail_vars["is_custom"], command=on_custom_material_toggle); material_detail_widgets["chk_custom_concrete"] = chk_custom_concrete; chk_custom_concrete.grid(row=2, column=2, sticky='w', padx=5, pady=5)
    lbl_fck = ttk.Label(detail_form_frame, text="fck (MPa):", style='Header.TLabel'); material_detail_widgets["lbl_fck"] = lbl_fck; lbl_fck.grid(row=3, column=0, sticky='w', padx=5, pady=5)
    entry_fck = create_content_entry(detail_form_frame, textvariable=material_detail_vars["fck"], width=10); material_detail_widgets["entry_fck"] = entry_fck; entry_fck.grid(row=3, column=1, sticky='w', padx=5, pady=5)
    # Donatı Alanları
    lbl_rebar_class = ttk.Label(detail_form_frame, text="Donatı Sınıfı:", style='Header.TLabel'); material_detail_widgets["lbl_rebar_class"] = lbl_rebar_class; lbl_rebar_class.grid(row=2, column=0, sticky='w', padx=5, pady=5) # Aynı satırda
    combo_rebar_class = create_content_combobox(detail_form_frame, list(REBAR_PROPS.keys()), textvariable=material_detail_vars["class"]); material_detail_widgets["combo_rebar_class"] = combo_rebar_class; combo_rebar_class.bind("<<ComboboxSelected>>", lambda e: on_material_class_change()); combo_rebar_class.grid(row=2, column=1, sticky='ew', padx=5, pady=5)
    chk_custom_rebar = create_custom_checkbutton(detail_form_frame, "Özel", material_detail_vars["is_custom"], command=on_custom_material_toggle); material_detail_widgets["chk_custom_rebar"] = chk_custom_rebar; chk_custom_rebar.grid(row=2, column=2, sticky='w', padx=5, pady=5)
    lbl_fyk = ttk.Label(detail_form_frame, text="fyk (MPa):", style='Header.TLabel'); material_detail_widgets["lbl_fyk"] = lbl_fyk; lbl_fyk.grid(row=3, column=0, sticky='w', padx=5, pady=5)
    entry_fyk = create_content_entry(detail_form_frame, textvariable=material_detail_vars["fyk"], width=10); material_detail_widgets["entry_fyk"] = entry_fyk; entry_fyk.grid(row=3, column=1, sticky='w', padx=5, pady=5)
    lbl_Es = ttk.Label(detail_form_frame, text="Es (MPa):", style='Header.TLabel'); material_detail_widgets["lbl_Es"] = lbl_Es; lbl_Es.grid(row=4, column=0, sticky='w', padx=5, pady=5)
    entry_Es = create_content_entry(detail_form_frame, textvariable=material_detail_vars["Es"], width=15); material_detail_widgets["entry_Es"] = entry_Es; entry_Es.grid(row=4, column=1, sticky='w', padx=5, pady=5)
    # Kaydet/Vazgeç Butonları
    form_button_frame = tk.Frame(detail_frame, bg=current_theme['content_bg']); form_button_frame.grid(row=5, column=0, columnspan=3, sticky='se', pady=10)
    ttk.Button(form_button_frame, text="Vazgeç", style='TButton', command=clear_material_form).pack(side=tk.RIGHT, padx=5); ttk.Button(form_button_frame, text="Kaydet", style='TButton', command=save_material_from_form).pack(side=tk.RIGHT, padx=5)
    clear_material_form(); update_material_listbox(); on_material_type_change()

# Kesit Sayfası İçeriği (YENİ)
def populate_section_page(parent_frame):
    global section_listbox_ref, section_detail_vars, section_detail_widgets
    section_detail_vars = { # Form değişkenleri
        "user_name": tk.StringVar(), "geom_type": tk.StringVar(value="Dikdörtgen"),
        "dim_b": tk.DoubleVar(), "dim_h": tk.DoubleVar(), # Dikdörtgen
        "dim_D": tk.DoubleVar(), # Dairesel
        # TODO: T/L için değişkenler (bf, hf, bw, hw)
        "cover": tk.DoubleVar(value=30.0)
    }
    section_detail_widgets = {} # Widget referansları

    sec_pane = tk.PanedWindow(parent_frame, bd=0, sashwidth=4, sashrelief=tk.FLAT, orient=tk.HORIZONTAL, bg=current_theme['content_bg'])
    sec_pane.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    # --- Sol Liste Alanı ---
    list_frame = tk.Frame(sec_pane, bg=current_theme['content_bg']); sec_pane.add(list_frame, width=300, stretch="never")
    ttk.Label(list_frame, text="Tanımlı Kesitler:", style='Header.TLabel').pack(anchor='w', padx=5, pady=(0,5))
    listbox = tk.Listbox(list_frame, height=15, font=("Segoe UI", 14), relief='flat', bd=1, bg=current_theme['listbox_bg'], fg=current_theme['listbox_fg'], selectbackground=current_theme['listbox_select_bg'], selectforeground=current_theme['title_text'], highlightthickness=1, highlightbackground=current_theme['entry_border'], exportselection=False)
    listbox.pack(fill=tk.BOTH, expand=True, padx=5); section_listbox_ref = listbox
    listbox.bind('<<ListboxSelect>>', lambda e: load_selected_section_to_form())

    button_frame = tk.Frame(list_frame, bg=current_theme['content_bg']); button_frame.pack(fill=tk.X, pady=5, padx=5)
    ttk.Button(button_frame, text="Yeni", style='TButton', width=6, command=clear_section_form).pack(side=tk.LEFT, padx=2)
    ttk.Button(button_frame, text="Düzenle", style='TButton', width=6, command=load_selected_section_to_form).pack(side=tk.LEFT, padx=2)
    ttk.Button(button_frame, text="Sil", style='TButton', width=6, command=delete_selected_section).pack(side=tk.LEFT, padx=2)

    # --- Sağ Detay Alanı ---
    detail_frame = tk.Frame(sec_pane, bg=current_theme['content_bg']); sec_pane.add(detail_frame, stretch="always")
    ttk.Label(detail_frame, text="Kesit Detayları:", style='Header.TLabel').grid(row=0, column=0, columnspan=3, sticky='w', padx=10, pady=(0,10))

    detail_form_frame = tk.Frame(detail_frame, bg=current_theme['content_bg']); detail_form_frame.grid(row=1, column=0, sticky='nsew', padx=10); detail_frame.rowconfigure(1, weight=1); detail_frame.columnconfigure(0, weight=1); detail_form_frame.columnconfigure(1, weight=1)

    # Ortak Alanlar
    ttk.Label(detail_form_frame, text="Kesit Adı:", style='Header.TLabel').grid(row=0, column=0, sticky='w', padx=5, pady=5)
    entry_sec_name = create_content_entry(detail_form_frame, textvariable=section_detail_vars["user_name"]); entry_sec_name.grid(row=0, column=1, columnspan=2, sticky='ew', padx=5, pady=5)
    ttk.Label(detail_form_frame, text="Geometri Tipi:", style='Header.TLabel').grid(row=1, column=0, sticky='w', padx=5, pady=5)
    combo_geom_type = create_content_combobox(detail_form_frame, ["Dikdörtgen", "Dairesel", "Tablalı-T", "Tablalı-L"], textvariable=section_detail_vars["geom_type"]); combo_geom_type.bind("<<ComboboxSelected>>", lambda e: on_section_type_change()); combo_geom_type.grid(row=1, column=1, columnspan=2, sticky='ew', padx=5, pady=5)
    ttk.Label(detail_form_frame, text="Paspayı (c) [mm]:", style='Header.TLabel').grid(row=4, column=0, sticky='w', padx=5, pady=5) # Satır indeksi değişebilir
    entry_cover = create_content_entry(detail_form_frame, textvariable=section_detail_vars["cover"], width=10); entry_cover.grid(row=4, column=1, sticky='w', padx=5, pady=5)

    # Boyut Alanları Çerçeveleri (Başlangıçta gizli)
    rect_dim_frame = tk.Frame(detail_form_frame, bg=current_theme['content_bg']); section_detail_widgets["rect_dim_frame"] = rect_dim_frame; rect_dim_frame.grid(row=2, column=0, columnspan=3, sticky='ew')
    circ_dim_frame = tk.Frame(detail_form_frame, bg=current_theme['content_bg']); section_detail_widgets["circ_dim_frame"] = circ_dim_frame; circ_dim_frame.grid(row=2, column=0, columnspan=3, sticky='ew')
    # TODO: T ve L için çerçeveler

    # Dikdörtgen Boyutları
    ttk.Label(rect_dim_frame, text="Genişlik (b) [mm]:", style='Header.TLabel').grid(row=0, column=0, sticky='w', padx=5, pady=2)
    create_content_entry(rect_dim_frame, textvariable=section_detail_vars["dim_b"], width=10).grid(row=0, column=1, sticky='w', padx=5, pady=2)
    ttk.Label(rect_dim_frame, text="Yükseklik (h) [mm]:", style='Header.TLabel').grid(row=1, column=0, sticky='w', padx=5, pady=2)
    create_content_entry(rect_dim_frame, textvariable=section_detail_vars["dim_h"], width=10).grid(row=1, column=1, sticky='w', padx=5, pady=2)

    # Dairesel Boyutları
    ttk.Label(circ_dim_frame, text="Çap (D) [mm]:", style='Header.TLabel').grid(row=0, column=0, sticky='w', padx=5, pady=2)
    create_content_entry(circ_dim_frame, textvariable=section_detail_vars["dim_D"], width=10).grid(row=0, column=1, sticky='w', padx=5, pady=2)

    # Hesaplanan Özellikler (Placeholder)
    props_frame = tk.Frame(detail_form_frame, bg=current_theme['content_bg']); props_frame.grid(row=3, column=0, columnspan=3, sticky='ew', pady=(15, 5))
    ttk.Label(props_frame, text="Hesaplanan Özellikler:", style='Header.TLabel').pack(anchor='w')
    prop_area = create_content_text(props_frame, "Alan: -", size=12); prop_area.pack(anchor='w', padx=20); section_detail_widgets["prop_area"] = prop_area
    prop_ix = create_content_text(props_frame, "Ix: -", size=12); prop_ix.pack(anchor='w', padx=20); section_detail_widgets["prop_ix"] = prop_ix
    prop_iy = create_content_text(props_frame, "Iy: -", size=12); prop_iy.pack(anchor='w', padx=20); section_detail_widgets["prop_iy"] = prop_iy

    # Kaydet/Vazgeç Butonları
    form_button_frame = tk.Frame(detail_frame, bg=current_theme['content_bg']); form_button_frame.grid(row=6, column=0, columnspan=3, sticky='se', pady=10) # Satır indeksi güncellendi
    ttk.Button(form_button_frame, text="Vazgeç", style='TButton', command=clear_section_form).pack(side=tk.RIGHT, padx=5)
    ttk.Button(form_button_frame, text="Kaydet", style='TButton', command=save_section_from_form).pack(side=tk.RIGHT, padx=5)

    # Başlangıç durumu
    clear_section_form(); update_section_listbox(); on_section_type_change()


def populate_element_design_page(parent_frame): ttk.Label(parent_frame, text="Tekil Eleman Tasarımı (Geliştirilecek)", style='Header.TLabel').pack(padx=10, pady=10)
def populate_seismic_load_page(parent_frame): ttk.Label(parent_frame, text="Deprem Yükü Hesaplama (TBDY 2018) (Geliştirilecek)", style='Header.TLabel').pack(padx=10, pady=10)
def populate_reporting_page(parent_frame): ttk.Label(parent_frame, text="Raporlama Seçenekleri:", style='Header.TLabel').pack(padx=10, pady=10, anchor='w')

# Profil Yönetimi Sayfası İçeriği
def populate_profiles_page(parent_frame):
    global profile_listbox_ref
    parent_frame.columnconfigure(0, weight=1); parent_frame.rowconfigure(1, weight=1)
    ttk.Label(parent_frame, text="Hesaplama Profilleri", style='Header.TLabel').grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky='w')
    listbox = tk.Listbox(parent_frame, font=("Segoe UI", 14), relief='flat', bd=1, bg=current_theme['listbox_bg'], fg=current_theme['listbox_fg'], selectbackground=current_theme['listbox_select_bg'], selectforeground=current_theme['title_text'], highlightthickness=1, highlightbackground=current_theme['entry_border'], exportselection=False)
    listbox.grid(row=1, column=0, padx=(10,0), pady=5, sticky='nsew'); profile_listbox_ref = listbox
    scrollbar = ttk.Scrollbar(parent_frame, orient='vertical', command=listbox.yview); scrollbar.grid(row=1, column=1, padx=(0,10), pady=5, sticky='ns'); listbox['yscrollcommand'] = scrollbar.set
    button_frame = tk.Frame(parent_frame, bg=current_theme['content_bg']); button_frame.grid(row=2, column=0, columnspan=2, pady=10, sticky='ew')
    load_button = ttk.Button(button_frame, text="Seçili Profili Yükle", style='TButton', command=load_selected_profile); load_button.pack(side=tk.LEFT, padx=5)
    new_button = ttk.Button(button_frame, text="Yeni Profil", style='TButton', command=create_new_profile); new_button.pack(side=tk.LEFT, padx=5)
    rename_button = ttk.Button(button_frame, text="Yeniden Adlandır", style='TButton', command=rename_selected_profile); rename_button.pack(side=tk.LEFT, padx=5)
    delete_button = ttk.Button(button_frame, text="Sil", style='TButton', command=delete_selected_profile); delete_button.pack(side=tk.LEFT, padx=5)
    update_profile_listbox()

# --- Ana Görünüm Fonksiyonları ---
# (show_... fonksiyonları aynı kalır)
def show_dashboard():
    global sub_sidebar_frame, current_view_func
    current_view_func = show_dashboard; sub_sidebar_frame = None
    for widget in content_frame.winfo_children(): widget.destroy()
    label = create_content_label(content_frame, "Panel"); label.pack(pady=20, padx=20, anchor='nw')
    dashboard_main_frame = tk.Frame(content_frame, bg=current_theme['content_bg']); dashboard_main_frame.pack(pady=10, padx=20, fill='both', expand=True)
    text_area = tk.Text(dashboard_main_frame, height=10, width=50, relief='flat', bd=1, font=("Segoe UI", 14), bg=current_theme['text_area_bg'], fg=current_theme['text_area_fg'], insertbackground=current_theme['entry_insert'], highlightthickness=1, highlightbackground=current_theme['text_area_highlight'], highlightcolor=current_theme['button_bg'])
    text_area.pack(side=tk.TOP, fill='both', expand=True)
    text_area.config(state=tk.NORMAL); text_area.delete('1.0', tk.END)
    text_area.insert(tk.END, f"AutoCAD Durumu: {autocad_status_message}\n\n"); text_area.insert(tk.END, "Uygulama durumu ve hızlı bilgiler burada gösterilecek...\n"); text_area.config(state=tk.DISABLED)
    refresh_button = ttk.Button(dashboard_main_frame, text="Yenile", command=refresh_autocad_status, style='TButton'); refresh_button.pack(side=tk.BOTTOM, anchor='se', pady=(10, 0))

def show_autocad_home():
    global current_view_func, connected_autocad_doc_name, app_settings
    current_view_func = show_autocad_home
    is_connected = (connected_autocad_doc_name is not None); control_state = tk.NORMAL if is_connected else tk.DISABLED
    for widget in content_frame.winfo_children(): widget.destroy()
    create_autocad_sub_sidebar(content_frame)
    settings_area_frame = tk.Frame(content_frame, bg=current_theme['content_bg']); settings_area_frame.pack(pady=15, padx=25, fill='x', anchor='nw')
    settings_header_label = ttk.Label(settings_area_frame, text="Çalışma Alanı Ayarları", style='Header.TLabel', font=("Segoe UI", 16, "bold")); settings_header_label.pack(anchor='w', pady=(0, 5))
    separator = ttk.Separator(settings_area_frame, orient='horizontal'); separator.pack(fill='x', anchor='w', pady=(0, 15))
    grid_frame = tk.Frame(settings_area_frame, bg=current_theme['content_bg']); grid_frame.pack(anchor='w', pady=5)
    grid_label = ttk.Label(grid_frame, text="Görünüm:", style='Header.TLabel'); grid_label.pack(side=tk.LEFT, padx=(0, 10))
    grid_var = tk.IntVar(); # saved_grid_mode = app_settings.get("autocad_settings", {}).get("gridmode", 0); grid_var.set(saved_grid_mode) # Artık profilde değil
    grid_check_frame = create_custom_checkbutton(grid_frame, "Izgara Modu (GRIDMODE)", grid_var, command=lambda v=grid_var: toggle_grid_mode(v), state=control_state); grid_check_frame.pack(side=tk.LEFT, pady=3)
    osnap_frame = tk.Frame(settings_area_frame, bg=current_theme['content_bg']); osnap_frame.pack(anchor='w', pady=10)
    osnap_label = ttk.Label(osnap_frame, text="Nesne Kenetleme (OSMODE):", style='Header.TLabel'); osnap_label.pack(anchor='w')
    osnap_options_frame = tk.Frame(osnap_frame, bg=current_theme['content_bg']); osnap_options_frame.pack(anchor='w', padx=20, pady=(5,0))
    osnap_vars = {}; osnap_modes = {"Endpoint": 1, "Midpoint": 2, "Center": 4, "Node": 8, "Intersection": 32}
    saved_osmode = 0 # Varsayılan 0 yapalım
    # saved_osmode = app_settings.get("autocad_settings", {}).get("osmode", 0) # Artık profilde değil
    for name, bit_value in osnap_modes.items():
        var = tk.IntVar();
        if saved_osmode & bit_value: var.set(1)
        else: var.set(0)
        chk_frame = create_custom_checkbutton(osnap_options_frame, name, var, command=lambda: update_osmode(osnap_vars, osnap_modes), state=control_state); chk_frame.pack(side=tk.LEFT, padx=5, pady=3)
        osnap_vars[bit_value] = var
    all_check_frames = [];
    if grid_frame: all_check_frames.extend(w for w in grid_frame.winfo_children() if isinstance(w, tk.Frame))
    if osnap_options_frame: all_check_frames.extend(w for w in osnap_options_frame.winfo_children() if isinstance(w, tk.Frame))
    if is_connected: # Bağlıysa AutoCAD'den oku
        current_gridmode = get_autocad_variable("GRIDMODE", 0); grid_var.set(current_gridmode)
        current_osmode = get_autocad_variable("OSMODE", 0)
        for bit_value, var in osnap_vars.items(): var.set(1) if current_osmode & bit_value else var.set(0)
        for frame in all_check_frames:
             if hasattr(frame, "update_visual_func"): frame.update_visual_func()
    if connected_autocad_doc_name: file_text = f"Bağlı Dosya: {connected_autocad_doc_name}"
    else: file_text = "Bağlı Dosya: Yok"
    doc_name_label = create_content_text(content_frame, file_text, size=12); doc_name_label.pack(side=tk.BOTTOM, anchor='se', padx=20, pady=10)

# --- AutoCAD Ayar Komutları ---
def toggle_grid_mode(variable):
    new_grid_mode = variable.get(); set_autocad_variable("GRIDMODE", new_grid_mode)
def update_osmode(osnap_vars_dict, osnap_modes_dict):
    new_osmode_value = 0
    for bit_value, var in osnap_vars_dict.items():
        if var.get() == 1: new_osmode_value |= bit_value
    set_autocad_variable("OSMODE", new_osmode_value)

# --- AutoCAD Test Alanı Fonksiyonları ---
# (select_area_in_autocad ve draw_shape_in_area fonksiyonları aynı kalır)
def select_area_in_autocad(result_text_widget, shape_buttons):
    global selected_area_points
    result_text_widget.config(state=tk.NORMAL); result_text_widget.delete('1.0', tk.END)
    acad = get_acad_instance()
    if not acad: result_text_widget.insert(tk.END, "Hata: AutoCAD bağlantısı kurulamadı."); result_text_widget.config(state=tk.DISABLED); return
    result_text_widget.insert(tk.END, "AutoCAD ekranına geçin ve 4 nokta seçin...\n(Arayüz bu sırada donabilir)\n"); root.update_idletasks()
    points = []; selected_area_points = None; button_state = tk.DISABLED
    try:
        acad.prompt("Lütfen 1. noktayı seçin (İptal için Esc):\n"); p1 = tuple(acad.doc.Utility.GetPoint())
        acad.prompt("Lütfen 2. noktayı seçin:\n"); p2 = tuple(acad.doc.Utility.GetPoint())
        acad.prompt("Lütfen 3. noktayı seçin:\n"); p3 = tuple(acad.doc.Utility.GetPoint())
        acad.prompt("Lütfen 4. noktayı seçin:\n"); p4 = tuple(acad.doc.Utility.GetPoint())
        points = [p1, p2, p3, p4]; selected_area_points = points
        result_text_widget.insert(tk.END, "Seçilen Noktalar:\n")
        for i, p in enumerate(points): result_text_widget.insert(tk.END, f"{i+1}. Nokta: {p}\n")
        result_text_widget.insert(tk.END, "\nAlan başarıyla seçildi. Şimdi şekil çizebilirsiniz."); button_state = tk.NORMAL
    except Exception as e: print(f"Nokta seçimi hatası/iptali: {e}"); result_text_widget.insert(tk.END, f"\nHata veya İptal: Nokta seçimi tamamlanamadı.\n{e}"); selected_area_points = None; button_state = tk.DISABLED
    finally:
        try: acad.prompt("\n")
        except: pass
        result_text_widget.config(state=tk.DISABLED)
        for btn in shape_buttons.values():
             if btn: btn.configure(state=button_state)
        bring_window_to_front()

def draw_shape_in_area(shape_type, result_text_widget):
    global selected_area_points
    result_text_widget.config(state=tk.NORMAL); result_text_widget.delete('1.0', tk.END)
    if not selected_area_points or len(selected_area_points) != 4: result_text_widget.insert(tk.END, "Hata: Önce 'Alan Seç' ile 4 nokta belirlemelisiniz."); result_text_widget.config(state=tk.DISABLED); return
    acad = get_acad_instance()
    if not acad: result_text_widget.insert(tk.END, "Hata: AutoCAD bağlantısı kurulamadı."); result_text_widget.config(state=tk.DISABLED); return
    try: model = acad.ActiveDocument.ModelSpace
    except Exception as e: print(f"ModelSpace erişim hatası: {e}"); result_text_widget.insert(tk.END, f"Hata: AutoCAD ModelSpace erişilemedi.\n{e}"); result_text_widget.config(state=tk.DISABLED); return
    try:
        xs = [p[0] for p in selected_area_points]; ys = [p[1] for p in selected_area_points]
        min_x, max_x = min(xs), max(xs); min_y, max_y = min(ys), max(ys)
        center_x = (min_x + max_x) / 2; center_y = (min_y + max_y) / 2
        width = max_x - min_x; height = max_y - min_y
        size = min(width, height) * 0.8
        if size <= 0: result_text_widget.insert(tk.END, "Hata: Geçersiz alan boyutu."); result_text_widget.config(state=tk.DISABLED); return
        center_point_tuple = (center_x, center_y, 0); radius = size / 2.0
        result_text_widget.insert(tk.END, f"'{shape_type}' çiziliyor...\nMerkez: ({center_x:.2f}, {center_y:.2f}), Boyut: {size:.2f}\n"); root.update_idletasks()
        if not APoint: result_text_widget.insert(tk.END, "Hata: APoint pyautocad'den import edilemedi."); result_text_widget.config(state=tk.DISABLED); return

        if shape_type == 'kare':
            half_size = size / 2.0; p1 = APoint(center_x - half_size, center_y - half_size); p2 = APoint(center_x + half_size, center_y - half_size); p3 = APoint(center_x + half_size, center_y + half_size); p4 = APoint(center_x - half_size, center_y + half_size)
            model.AddLine(p1, p2); model.AddLine(p2, p3); model.AddLine(p3, p4); model.AddLine(p4, p1)
        elif shape_type == 'daire': model.AddCircle(APoint(center_x, center_y), radius)
        elif shape_type == 'üçgen':
            p1 = APoint(center_x, center_y + radius); p2 = APoint(center_x - radius * math.sqrt(3)/2, center_y - radius/2); p3 = APoint(center_x + radius * math.sqrt(3)/2, center_y - radius/2)
            model.AddLine(p1, p2); model.AddLine(p2, p3); model.AddLine(p3, p1)
        result_text_widget.insert(tk.END, f"'{shape_type}' başarıyla çizildi.")
    except Exception as e: print(f"Şekil çizme hatası: {e}"); result_text_widget.insert(tk.END, f"\nHata: Şekil çizilemedi.\n{e}")
    finally: result_text_widget.config(state=tk.DISABLED); bring_window_to_front()

# AutoCAD Test Alanı Görünümü
def show_autocad_test_area():
    # ... (kod aynı kaldı) ...
    global current_view_func, connected_autocad_doc_name, shape_buttons_references
    current_view_func = show_autocad_test_area
    is_connected = (connected_autocad_doc_name is not None); control_state = tk.NORMAL if is_connected else tk.DISABLED
    shape_button_state = tk.NORMAL if selected_area_points else tk.DISABLED
    for widget in content_frame.winfo_children(): widget.destroy()
    create_autocad_sub_sidebar(content_frame)
    label = create_content_label(content_frame, "AutoCAD Test Alanı"); label.pack(pady=10, padx=20, anchor='nw')
    test_main_frame = tk.Frame(content_frame, bg=current_theme['content_bg']); test_main_frame.pack(pady=15, padx=25, fill='both', expand=True, anchor='nw')
    button_area_frame = tk.Frame(test_main_frame, bg=current_theme['content_bg']); button_area_frame.pack(pady=5, anchor='w')
    result_text = tk.Text(test_main_frame, height=10, width=50, relief='flat', bd=1, font=("Segoe UI", 13), bg=current_theme['text_area_bg'], fg=current_theme['text_area_fg'], insertbackground=current_theme['entry_insert'], highlightthickness=1, highlightbackground=current_theme['text_area_highlight'], highlightcolor=current_theme['button_bg'], state=tk.DISABLED); result_text.pack(side=tk.TOP, fill='both', expand=True, pady=(10, 10))
    shape_buttons_references = {}
    select_button = ttk.Button(button_area_frame, text="Alan Seç (4 Nokta)", style='TButton', command=lambda rt=result_text, sb=shape_buttons_references: select_area_in_autocad(rt, sb), state=control_state); select_button.pack(side=tk.LEFT, anchor='w', padx=(0,10))
    square_button = ttk.Button(button_area_frame, text="Kare", style='TButton', command=lambda rt=result_text: draw_shape_in_area('kare', rt), state=shape_button_state); square_button.pack(side=tk.LEFT, anchor='w', padx=5); shape_buttons_references['kare'] = square_button
    triangle_button = ttk.Button(button_area_frame, text="Üçgen", style='TButton', command=lambda rt=result_text: draw_shape_in_area('üçgen', rt), state=shape_button_state); triangle_button.pack(side=tk.LEFT, anchor='w', padx=5); shape_buttons_references['üçgen'] = triangle_button
    circle_button = ttk.Button(button_area_frame, text="Daire", style='TButton', command=lambda rt=result_text: draw_shape_in_area('daire', rt), state=shape_button_state); circle_button.pack(side=tk.LEFT, anchor='w', padx=5); shape_buttons_references['daire'] = circle_button
    if connected_autocad_doc_name: file_text = f"Bağlı Dosya: {connected_autocad_doc_name}"
    else: file_text = "Bağlı Dosya: Yok"
    doc_name_label = create_content_text(content_frame, file_text, size=12); doc_name_label.pack(side=tk.BOTTOM, anchor='se', padx=20, pady=10)


# --- Hesaplamalar Bölümü Sayfa Fonksiyonları ---
def show_calc_project_info():
    global current_view_func, sub_sidebar_frame
    current_view_func = show_calc_project_info; sub_sidebar_frame = None
    for widget in content_frame.winfo_children(): widget.destroy()
    create_calculations_sub_sidebar(content_frame)
    page_frame = ttk.Frame(content_frame, style='TFrame', padding=(15, 15)); page_frame.pack(expand=True, fill='both', padx=10, pady=10)
    populate_project_info_page(page_frame)

def show_calc_materials():
    global current_view_func, sub_sidebar_frame
    current_view_func = show_calc_materials; sub_sidebar_frame = None
    for widget in content_frame.winfo_children(): widget.destroy()
    create_calculations_sub_sidebar(content_frame)
    page_frame = ttk.Frame(content_frame, style='TFrame', padding=(15, 15)); page_frame.pack(expand=True, fill='both', padx=10, pady=10)
    populate_material_page(page_frame)

def show_calc_sections():
    global current_view_func, sub_sidebar_frame
    current_view_func = show_calc_sections; sub_sidebar_frame = None
    for widget in content_frame.winfo_children(): widget.destroy()
    create_calculations_sub_sidebar(content_frame)
    page_frame = ttk.Frame(content_frame, style='TFrame', padding=(15, 15)); page_frame.pack(expand=True, fill='both', padx=10, pady=10)
    populate_section_page(page_frame) # Bu fonksiyon artık içeriği dolduracak

def show_calc_element_design():
    global current_view_func, sub_sidebar_frame
    current_view_func = show_calc_element_design; sub_sidebar_frame = None
    for widget in content_frame.winfo_children(): widget.destroy()
    create_calculations_sub_sidebar(content_frame)
    page_frame = ttk.Frame(content_frame, style='TFrame', padding=(15, 15)); page_frame.pack(expand=True, fill='both', padx=10, pady=10)
    populate_element_design_page(page_frame)

def show_calc_seismic():
    global current_view_func, sub_sidebar_frame
    current_view_func = show_calc_seismic; sub_sidebar_frame = None
    for widget in content_frame.winfo_children(): widget.destroy()
    create_calculations_sub_sidebar(content_frame)
    page_frame = ttk.Frame(content_frame, style='TFrame', padding=(15, 15)); page_frame.pack(expand=True, fill='both', padx=10, pady=10)
    populate_seismic_load_page(page_frame)

def show_calc_reporting():
    global current_view_func, sub_sidebar_frame
    current_view_func = show_calc_reporting; sub_sidebar_frame = None
    for widget in content_frame.winfo_children(): widget.destroy()
    create_calculations_sub_sidebar(content_frame)
    page_frame = ttk.Frame(content_frame, style='TFrame', padding=(15, 15)); page_frame.pack(expand=True, fill='both', padx=10, pady=10)
    populate_reporting_page(page_frame)

# Profiller Sayfası Görünümü
def show_calc_profiles():
    global current_view_func, sub_sidebar_frame
    current_view_func = show_calc_profiles; sub_sidebar_frame = None
    for widget in content_frame.winfo_children(): widget.destroy()
    create_calculations_sub_sidebar(content_frame)
    page_frame = ttk.Frame(content_frame, style='TFrame', padding=(15, 15))
    page_frame.pack(expand=True, fill='both', padx=10, pady=10)
    populate_profiles_page(page_frame)

# Ayarlar Görünümü
def show_settings():
    global sub_sidebar_frame, current_view_func
    current_view_func = show_settings; sub_sidebar_frame = None
    for widget in content_frame.winfo_children(): widget.destroy()
    label = create_content_label(content_frame, "Ayarlar"); label.pack(pady=20, padx=20, anchor='nw')
    theme_frame = tk.Frame(content_frame, bg=current_theme['content_bg']); theme_frame.pack(pady=10, padx=40, anchor='w', fill='x')
    theme_label_text = ttk.Label(theme_frame, text="Uygulama Teması:", font=("Segoe UI", 14), background=current_theme['content_bg'], foreground=current_theme['text']); theme_label_text.pack(side=tk.LEFT, padx=(0, 10))
    dark_button = ttk.Button(theme_frame, text="Siyah", style='TButton', command=lambda: apply_theme("dark")); dark_button.pack(side=tk.LEFT, padx=5)
    light_button = ttk.Button(theme_frame, text="Beyaz", style='TButton', command=lambda: apply_theme("light")); light_button.pack(side=tk.LEFT, padx=5)
    system_button = ttk.Button(theme_frame, text="Sistem", style='TButton', command=lambda: apply_theme("system")); system_button.pack(side=tk.LEFT, padx=5)
    version_label = create_content_text(content_frame, "Version 1.0.1", size=10); version_label.pack(side=tk.BOTTOM, anchor='se', padx=20, pady=10)

# --- Profil Veri Yönetimi Fonksiyonları ---
# (save_project_info, load_project_info, update_profile_listbox, load_selected_profile,
#  create_new_profile, rename_selected_profile, delete_selected_profile fonksiyonları aynı kaldı)
def save_project_info():
    global profiles_data, current_profile_name, project_info_vars
    if not current_profile_name: messagebox.showwarning("Profil Seçilmedi", "Lütfen önce bir profil seçin veya oluşturun."); return
    profile = profiles_data.setdefault(current_profile_name, {"project_info": {}, "materials": [], "sections": []})
    project_info = profile.setdefault("project_info", {})
    project_info["name"] = project_info_vars.get("name", tk.StringVar()).get()
    desc_widget = project_info_vars.get("desc_widget")
    if desc_widget: project_info["desc"] = desc_widget.get("1.0", tk.END).strip()
    else: project_info["desc"] = ""
    project_info["engineer"] = project_info_vars.get("engineer", tk.StringVar()).get()
    project_info["concrete_reg"] = project_info_vars.get("concrete_reg", tk.StringVar()).get()
    project_info["seismic_reg"] = project_info_vars.get("seismic_reg", tk.StringVar()).get()
    project_info["load_reg"] = project_info_vars.get("load_reg", tk.StringVar()).get()
    project_info["units"] = project_info_vars.get("units", tk.StringVar()).get()
    save_profiles(); messagebox.showinfo("Kaydedildi", f"'{current_profile_name}' profili için proje bilgileri kaydedildi.")

def load_project_info():
    global profiles_data, current_profile_name, project_info_vars
    if not project_info_vars: print("Info: Project info variables not ready for loading."); return
    if current_profile_name not in profiles_data:
        print(f"Warning: Profile '{current_profile_name}' not found for loading project info.")
        project_info_vars.get("name", tk.StringVar()).set("Yeni Proje")
        desc_widget = project_info_vars.get("desc_widget");
        if desc_widget: desc_widget.delete("1.0", tk.END)
        project_info_vars.get("engineer", tk.StringVar()).set("")
        return
    profile = profiles_data[current_profile_name]; project_info = profile.get("project_info", {})
    project_info_vars.get("name", tk.StringVar()).set(project_info.get("name", "Yeni Proje"))
    desc_widget = project_info_vars.get("desc_widget")
    if desc_widget: desc_widget.delete("1.0", tk.END); desc_widget.insert("1.0", project_info.get("desc", ""))
    project_info_vars.get("engineer", tk.StringVar()).set(project_info.get("engineer", ""))
    project_info_vars.get("concrete_reg", tk.StringVar()).set(project_info.get("concrete_reg", "TS 500 (2000)"))
    project_info_vars.get("seismic_reg", tk.StringVar()).set(project_info.get("seismic_reg", "TBDY 2018"))
    project_info_vars.get("load_reg", tk.StringVar()).set(project_info.get("load_reg", "TS 498 (1997)"))
    project_info_vars.get("units", tk.StringVar()).set(project_info.get("units", "Metrik (kN, m, C)"))
    print(f"Project info loaded for profile: {current_profile_name}")

# --- Kesit Sayfası Yardımcı Fonksiyonları (YENİ) ---
def clear_section_form():
    """Kesit detay formunu temizler."""
    section_detail_vars.get("user_name", tk.StringVar()).set("")
    section_detail_vars.get("geom_type", tk.StringVar()).set("Dikdörtgen")
    section_detail_vars.get("dim_b", tk.DoubleVar()).set(0.0)
    section_detail_vars.get("dim_h", tk.DoubleVar()).set(0.0)
    section_detail_vars.get("dim_D", tk.DoubleVar()).set(0.0)
    section_detail_vars.get("cover", tk.DoubleVar()).set(30.0)
    if section_detail_widgets.get("prop_area"): section_detail_widgets["prop_area"].config(text="-")
    if section_detail_widgets.get("prop_ix"): section_detail_widgets["prop_ix"].config(text="-")
    if section_detail_widgets.get("prop_iy"): section_detail_widgets["prop_iy"].config(text="-")
    if section_listbox_ref:
        selection = section_listbox_ref.curselection()
        if selection: section_listbox_ref.selection_clear(selection[0])
    on_section_type_change()

def update_section_listbox():
    """Kesit listesini güncel profilden doldurur."""
    if section_listbox_ref and current_profile_name in profiles_data:
        section_listbox_ref.delete(0, tk.END)
        sections = profiles_data[current_profile_name].get("sections", [])
        sections.sort(key=lambda x: x.get("user_name", "").lower())
        for sec in sections:
            display_name = f"{sec.get('geom_type', '?')}: {sec.get('user_name', 'İsimsiz')}"
            section_listbox_ref.insert(tk.END, display_name)

def on_section_type_change():
    """Kesit tipi değiştikçe ilgili boyut alanlarını gösterir/gizler."""
    if not section_detail_widgets: return
    geom_type = section_detail_vars.get("geom_type", tk.StringVar()).get()
    # Tüm boyut çerçevelerini gizle
    if section_detail_widgets.get("rect_dim_frame"): section_detail_widgets["rect_dim_frame"].grid_remove()
    if section_detail_widgets.get("circ_dim_frame"): section_detail_widgets["circ_dim_frame"].grid_remove()
    # İlgili çerçeveyi göster
    if geom_type == "Dikdörtgen" and section_detail_widgets.get("rect_dim_frame"): section_detail_widgets["rect_dim_frame"].grid()
    elif geom_type == "Dairesel" and section_detail_widgets.get("circ_dim_frame"): section_detail_widgets["circ_dim_frame"].grid()

def load_selected_section_to_form():
    """Listeden seçilen kesiti forma yükler."""
    if not section_listbox_ref: return
    selection = section_listbox_ref.curselection()
    if not selection: return
    selected_index = selection[0]
    sections = profiles_data.get(current_profile_name, {}).get("sections", [])
    if selected_index < 0 or selected_index >= len(sections): messagebox.showerror("Hata", "Seçilen kesit verisi bulunamadı."); return
    section_data = sections[selected_index]

    section_detail_vars.get("user_name", tk.StringVar()).set(section_data.get("user_name", ""))
    section_detail_vars.get("geom_type", tk.StringVar()).set(section_data.get("geom_type", "Dikdörtgen"))
    section_detail_vars.get("cover", tk.DoubleVar()).set(section_data.get("cover", 30.0))
    dims = section_data.get("dimensions", {})
    section_detail_vars.get("dim_b", tk.DoubleVar()).set(dims.get("b", 0.0))
    section_detail_vars.get("dim_h", tk.DoubleVar()).set(dims.get("h", 0.0))
    section_detail_vars.get("dim_D", tk.DoubleVar()).set(dims.get("D", 0.0))
    props = section_data.get("properties", {}) # Hesaplanan özellikler (şimdilik boş)
    if section_detail_widgets.get("prop_area"): section_detail_widgets["prop_area"].config(text=str(props.get("Area", "-")))
    if section_detail_widgets.get("prop_ix"): section_detail_widgets["prop_ix"].config(text=str(props.get("Ix", "-")))
    if section_detail_widgets.get("prop_iy"): section_detail_widgets["prop_iy"].config(text=str(props.get("Iy", "-")))
    on_section_type_change()

def save_section_from_form():
    """Formdaki verileri alıp aktif profile kesit olarak kaydeder/günceller."""
    global profiles_data, current_profile_name
    if not current_profile_name: messagebox.showerror("Hata", "Aktif profil bulunamadı."); return
    user_name = section_detail_vars.get("user_name", tk.StringVar()).get().strip()
    if not user_name: messagebox.showerror("Hata", "Kesit adı boş olamaz."); return
    geom_type = section_detail_vars.get("geom_type", tk.StringVar()).get()
    dimensions = {}; cover = 30.0
    try:
        cover = section_detail_vars.get("cover", tk.DoubleVar()).get()
        if geom_type == "Dikdörtgen":
            dimensions["b"] = section_detail_vars.get("dim_b", tk.DoubleVar()).get()
            dimensions["h"] = section_detail_vars.get("dim_h", tk.DoubleVar()).get()
            if dimensions["b"] <= 0 or dimensions["h"] <= 0: raise ValueError("Boyutlar pozitif olmalı.")
        elif geom_type == "Dairesel":
            dimensions["D"] = section_detail_vars.get("dim_D", tk.DoubleVar()).get()
            if dimensions["D"] <= 0: raise ValueError("Çap pozitif olmalı.")
        if cover < 0: raise ValueError("Paspayı negatif olamaz.")
    except (tk.TclError, ValueError) as e: messagebox.showerror("Hata", f"Lütfen geçerli sayısal boyut/paspayı girin.\n{e}"); return

    new_section_data = {"user_name": user_name, "geom_type": geom_type, "dimensions": dimensions, "cover": cover, "properties": {}}
    profile = profiles_data.setdefault(current_profile_name, {"project_info": {}, "materials": [], "sections": []})
    sections = profile.setdefault("sections", [])
    selected_index = -1; original_name_if_editing = None
    if section_listbox_ref: selection = section_listbox_ref.curselection();
    if selection: selected_index = selection[0]
    if selected_index != -1:
        try: original_name_if_editing = sections[selected_index].get("user_name")
        except IndexError: selected_index = -1
    found_index = -1
    for i, sec in enumerate(sections):
        if sec.get("user_name") == user_name: found_index = i; break

    if user_name == original_name_if_editing or found_index == -1:
        if selected_index != -1 and original_name_if_editing is not None: # Düzenleme
             try: sections[selected_index] = new_section_data; print(f"Section '{user_name}' updated.")
             except IndexError: sections.append(new_section_data); print(f"Section '{user_name}' added (update failed, added as new).")
        else: # Yeni kesit ekleme
             sections.append(new_section_data); print(f"Section '{user_name}' added.")
        save_profiles(); update_section_listbox(); clear_section_form(); messagebox.showinfo("Başarılı", f"Kesit '{user_name}' kaydedildi.")
    else: messagebox.showerror("Hata", f"'{user_name}' adında başka bir kesit zaten var.")

def delete_selected_section():
    """Listeden seçilen kesiti profilden siler."""
    global profiles_data
    if not section_listbox_ref: return
    selection = section_listbox_ref.curselection()
    if not selection: messagebox.showwarning("Kesit Seçilmedi", "Lütfen silinecek kesiti seçin."); return
    selected_index = selection[0]
    profile = profiles_data.get(current_profile_name)
    if profile and "sections" in profile and 0 <= selected_index < len(profile["sections"]):
        section_to_delete = profile["sections"][selected_index]
        user_name_to_delete = section_to_delete.get("user_name", "Bilinmeyen")
        if messagebox.askyesno("Kesiti Sil", f"'{user_name_to_delete}' kesitini silmek istediğinizden emin misiniz?", parent=root):
            del profile["sections"][selected_index]
            save_profiles(); update_section_listbox(); clear_section_form()
            messagebox.showinfo("Başarılı", f"'{user_name_to_delete}' kesiti silindi.")
    else: messagebox.showerror("Hata", "Kesit silinemedi.")


# --- Sayfa İçeriklerini Oluşturan Fonksiyonlar ---
# ... (populate_project_info_page ve populate_material_page aynı kaldı) ...
def populate_project_info_page(parent_frame):
    global project_info_vars
    project_info_vars = { "name": tk.StringVar(), "desc": tk.StringVar(), "engineer": tk.StringVar(), "concrete_reg": tk.StringVar(), "seismic_reg": tk.StringVar(), "load_reg": tk.StringVar(), "units": tk.StringVar() }
    parent_frame.columnconfigure(1, weight=1)
    ttk.Label(parent_frame, text="Proje Adı:", style='Header.TLabel').grid(row=0, column=0, padx=10, pady=8, sticky='w')
    create_content_entry(parent_frame, textvariable=project_info_vars["name"]).grid(row=0, column=1, padx=10, pady=8, sticky='ew')
    ttk.Label(parent_frame, text="Açıklama:", style='Header.TLabel').grid(row=1, column=0, padx=10, pady=8, sticky='nw')
    desc_text = tk.Text(parent_frame, height=4, width=40, font=("Segoe UI", 14), relief='flat', bd=1, bg=current_theme['text_area_bg'], fg=current_theme['text_area_fg'], insertbackground=current_theme['entry_insert'], highlightthickness=1, highlightbackground=current_theme['entry_border'], highlightcolor=current_theme['button_bg'])
    desc_text.grid(row=1, column=1, padx=10, pady=8, sticky='nsew'); parent_frame.rowconfigure(1, weight=1)
    project_info_vars["desc_widget"] = desc_text
    ttk.Label(parent_frame, text="Mühendis/Firma:", style='Header.TLabel').grid(row=2, column=0, padx=10, pady=8, sticky='w')
    create_content_entry(parent_frame, textvariable=project_info_vars["engineer"]).grid(row=2, column=1, padx=10, pady=8, sticky='ew')
    ttk.Label(parent_frame, text="Betonarme Yön.:", style='Header.TLabel').grid(row=3, column=0, padx=10, pady=8, sticky='w')
    combo_concrete = create_content_combobox(parent_frame, ["TS 500 (2000)"], textvariable=project_info_vars["concrete_reg"]);
    if combo_concrete['values']: combo_concrete.current(0); combo_concrete.grid(row=3, column=1, padx=10, pady=8, sticky='ew')
    ttk.Label(parent_frame, text="Deprem Yön.:", style='Header.TLabel').grid(row=4, column=0, padx=10, pady=8, sticky='w')
    combo_seismic = create_content_combobox(parent_frame, ["TBDY 2018"], textvariable=project_info_vars["seismic_reg"]);
    if combo_seismic['values']: combo_seismic.current(0); combo_seismic.grid(row=4, column=1, padx=10, pady=8, sticky='ew')
    ttk.Label(parent_frame, text="Yük Yön.:", style='Header.TLabel').grid(row=5, column=0, padx=10, pady=8, sticky='w')
    combo_load = create_content_combobox(parent_frame, ["TS 498 (1997)"], textvariable=project_info_vars["load_reg"]);
    if combo_load['values']: combo_load.current(0); combo_load.grid(row=5, column=1, padx=10, pady=8, sticky='ew')
    ttk.Label(parent_frame, text="Birim Sistemi:", style='Header.TLabel').grid(row=6, column=0, padx=10, pady=8, sticky='w')
    combo_unit = create_content_combobox(parent_frame, ["Metrik (kN, m, C)"], textvariable=project_info_vars["units"]);
    if combo_unit['values']: combo_unit.current(0); combo_unit.grid(row=6, column=1, padx=10, pady=8, sticky='ew')
    save_button = ttk.Button(parent_frame, text="Profili Kaydet", command=save_project_info, style='TButton')
    save_button.grid(row=7, column=1, padx=10, pady=20, sticky='e')
    load_project_info()

def populate_material_page(parent_frame):
    # ... (Kod aynı kaldı) ...
    global material_listbox_ref, material_detail_vars, material_detail_widgets
    material_detail_vars = { "user_name": tk.StringVar(), "type": tk.StringVar(value="Beton"), "class": tk.StringVar(), "is_custom": tk.IntVar(value=0), "fck": tk.DoubleVar(), "fyk": tk.DoubleVar(), "Ec": tk.DoubleVar(), "Es": tk.DoubleVar() }
    material_detail_widgets = {}
    mat_pane = tk.PanedWindow(parent_frame, bd=0, sashwidth=4, sashrelief=tk.FLAT, orient=tk.HORIZONTAL, bg=current_theme['content_bg'])
    mat_pane.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    list_frame = tk.Frame(mat_pane, bg=current_theme['content_bg']); mat_pane.add(list_frame, width=300, stretch="never")
    ttk.Label(list_frame, text="Tanımlı Malzemeler:", style='Header.TLabel').pack(anchor='w', padx=5, pady=(0,5))
    listbox = tk.Listbox(list_frame, height=15, font=("Segoe UI", 14), relief='flat', bd=1, bg=current_theme['listbox_bg'], fg=current_theme['listbox_fg'], selectbackground=current_theme['listbox_select_bg'], selectforeground=current_theme['title_text'], highlightthickness=1, highlightbackground=current_theme['entry_border'], exportselection=False)
    listbox.pack(fill=tk.BOTH, expand=True, padx=5); material_listbox_ref = listbox
    listbox.bind('<<ListboxSelect>>', lambda e: load_selected_material_to_form())
    button_frame = tk.Frame(list_frame, bg=current_theme['content_bg']); button_frame.pack(fill=tk.X, pady=5, padx=5)
    ttk.Button(button_frame, text="Yeni", style='TButton', width=6, command=clear_material_form).pack(side=tk.LEFT, padx=2); ttk.Button(button_frame, text="Düzenle", style='TButton', width=6, command=load_selected_material_to_form).pack(side=tk.LEFT, padx=2); ttk.Button(button_frame, text="Sil", style='TButton', width=6, command=delete_selected_material).pack(side=tk.LEFT, padx=2)
    detail_frame = tk.Frame(mat_pane, bg=current_theme['content_bg']); mat_pane.add(detail_frame, stretch="always")
    ttk.Label(detail_frame, text="Malzeme Detayları:", style='Header.TLabel').grid(row=0, column=0, columnspan=3, sticky='w', padx=10, pady=(0,10))
    detail_form_frame = tk.Frame(detail_frame, bg=current_theme['content_bg']); detail_form_frame.grid(row=1, column=0, sticky='nsew', padx=10); detail_frame.rowconfigure(1, weight=1); detail_frame.columnconfigure(0, weight=1); detail_form_frame.columnconfigure(1, weight=1)
    ttk.Label(detail_form_frame, text="Malzeme Adı:", style='Header.TLabel').grid(row=0, column=0, sticky='w', padx=5, pady=5)
    entry_name = create_content_entry(detail_form_frame, textvariable=material_detail_vars["user_name"]); entry_name.grid(row=0, column=1, columnspan=2, sticky='ew', padx=5, pady=5); material_detail_widgets["entry_name"] = entry_name
    ttk.Label(detail_form_frame, text="Malzeme Tipi:", style='Header.TLabel').grid(row=1, column=0, sticky='w', padx=5, pady=5)
    combo_type = create_content_combobox(detail_form_frame, ["Beton", "Donatı Çeliği"], textvariable=material_detail_vars["type"]); combo_type.bind("<<ComboboxSelected>>", lambda e: on_material_type_change()); combo_type.grid(row=1, column=1, columnspan=2, sticky='ew', padx=5, pady=5); material_detail_widgets["combo_type"] = combo_type
    # Beton Alanları
    lbl_concrete_class = ttk.Label(detail_form_frame, text="Beton Sınıfı:", style='Header.TLabel'); material_detail_widgets["lbl_concrete_class"] = lbl_concrete_class; lbl_concrete_class.grid(row=2, column=0, sticky='w', padx=5, pady=5)
    combo_concrete_class = create_content_combobox(detail_form_frame, list(CONCRETE_PROPS.keys()), textvariable=material_detail_vars["class"]); material_detail_widgets["combo_concrete_class"] = combo_concrete_class; combo_concrete_class.bind("<<ComboboxSelected>>", lambda e: on_material_class_change()); combo_concrete_class.grid(row=2, column=1, sticky='ew', padx=5, pady=5)
    chk_custom_concrete = create_custom_checkbutton(detail_form_frame, "Özel", material_detail_vars["is_custom"], command=on_custom_material_toggle); material_detail_widgets["chk_custom_concrete"] = chk_custom_concrete; chk_custom_concrete.grid(row=2, column=2, sticky='w', padx=5, pady=5)
    lbl_fck = ttk.Label(detail_form_frame, text="fck (MPa):", style='Header.TLabel'); material_detail_widgets["lbl_fck"] = lbl_fck; lbl_fck.grid(row=3, column=0, sticky='w', padx=5, pady=5)
    entry_fck = create_content_entry(detail_form_frame, textvariable=material_detail_vars["fck"], width=10); material_detail_widgets["entry_fck"] = entry_fck; entry_fck.grid(row=3, column=1, sticky='w', padx=5, pady=5)
    # Donatı Alanları
    lbl_rebar_class = ttk.Label(detail_form_frame, text="Donatı Sınıfı:", style='Header.TLabel'); material_detail_widgets["lbl_rebar_class"] = lbl_rebar_class; lbl_rebar_class.grid(row=2, column=0, sticky='w', padx=5, pady=5) # Aynı satırda
    combo_rebar_class = create_content_combobox(detail_form_frame, list(REBAR_PROPS.keys()), textvariable=material_detail_vars["class"]); material_detail_widgets["combo_rebar_class"] = combo_rebar_class; combo_rebar_class.bind("<<ComboboxSelected>>", lambda e: on_material_class_change()); combo_rebar_class.grid(row=2, column=1, sticky='ew', padx=5, pady=5)
    chk_custom_rebar = create_custom_checkbutton(detail_form_frame, "Özel", material_detail_vars["is_custom"], command=on_custom_material_toggle); material_detail_widgets["chk_custom_rebar"] = chk_custom_rebar; chk_custom_rebar.grid(row=2, column=2, sticky='w', padx=5, pady=5)
    lbl_fyk = ttk.Label(detail_form_frame, text="fyk (MPa):", style='Header.TLabel'); material_detail_widgets["lbl_fyk"] = lbl_fyk; lbl_fyk.grid(row=3, column=0, sticky='w', padx=5, pady=5)
    entry_fyk = create_content_entry(detail_form_frame, textvariable=material_detail_vars["fyk"], width=10); material_detail_widgets["entry_fyk"] = entry_fyk; entry_fyk.grid(row=3, column=1, sticky='w', padx=5, pady=5)
    lbl_Es = ttk.Label(detail_form_frame, text="Es (MPa):", style='Header.TLabel'); material_detail_widgets["lbl_Es"] = lbl_Es; lbl_Es.grid(row=4, column=0, sticky='w', padx=5, pady=5)
    entry_Es = create_content_entry(detail_form_frame, textvariable=material_detail_vars["Es"], width=15); material_detail_widgets["entry_Es"] = entry_Es; entry_Es.grid(row=4, column=1, sticky='w', padx=5, pady=5)
    # Kaydet/Vazgeç Butonları
    form_button_frame = tk.Frame(detail_frame, bg=current_theme['content_bg']); form_button_frame.grid(row=5, column=0, columnspan=3, sticky='se', pady=10)
    ttk.Button(form_button_frame, text="Vazgeç", style='TButton', command=clear_material_form).pack(side=tk.RIGHT, padx=5); ttk.Button(form_button_frame, text="Kaydet", style='TButton', command=save_material_from_form).pack(side=tk.RIGHT, padx=5)
    clear_material_form(); update_material_listbox(); on_material_type_change()


# Kesit Sayfası İçeriği (YENİ)
def populate_section_page(parent_frame):
    global section_listbox_ref, section_detail_vars, section_detail_widgets
    section_detail_vars = { # Form değişkenleri
        "user_name": tk.StringVar(), "geom_type": tk.StringVar(value="Dikdörtgen"),
        "dim_b": tk.DoubleVar(), "dim_h": tk.DoubleVar(), # Dikdörtgen
        "dim_D": tk.DoubleVar(), # Dairesel
        "cover": tk.DoubleVar(value=30.0)
    }
    section_detail_widgets = {} # Widget referansları

    sec_pane = tk.PanedWindow(parent_frame, bd=0, sashwidth=4, sashrelief=tk.FLAT, orient=tk.HORIZONTAL, bg=current_theme['content_bg'])
    sec_pane.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    # --- Sol Liste Alanı ---
    list_frame = tk.Frame(sec_pane, bg=current_theme['content_bg']); sec_pane.add(list_frame, width=300, stretch="never")
    ttk.Label(list_frame, text="Tanımlı Kesitler:", style='Header.TLabel').pack(anchor='w', padx=5, pady=(0,5))
    listbox = tk.Listbox(list_frame, height=15, font=("Segoe UI", 14), relief='flat', bd=1, bg=current_theme['listbox_bg'], fg=current_theme['listbox_fg'], selectbackground=current_theme['listbox_select_bg'], selectforeground=current_theme['title_text'], highlightthickness=1, highlightbackground=current_theme['entry_border'], exportselection=False)
    listbox.pack(fill=tk.BOTH, expand=True, padx=5); section_listbox_ref = listbox
    listbox.bind('<<ListboxSelect>>', lambda e: load_selected_section_to_form())

    button_frame = tk.Frame(list_frame, bg=current_theme['content_bg']); button_frame.pack(fill=tk.X, pady=5, padx=5)
    ttk.Button(button_frame, text="Yeni", style='TButton', width=6, command=clear_section_form).pack(side=tk.LEFT, padx=2)
    ttk.Button(button_frame, text="Düzenle", style='TButton', width=6, command=load_selected_section_to_form).pack(side=tk.LEFT, padx=2)
    ttk.Button(button_frame, text="Sil", style='TButton', width=6, command=delete_selected_section).pack(side=tk.LEFT, padx=2)

    # --- Sağ Detay Alanı ---
    detail_frame = tk.Frame(sec_pane, bg=current_theme['content_bg']); sec_pane.add(detail_frame, stretch="always")
    ttk.Label(detail_frame, text="Kesit Detayları:", style='Header.TLabel').grid(row=0, column=0, columnspan=3, sticky='w', padx=10, pady=(0,10))

    detail_form_frame = tk.Frame(detail_frame, bg=current_theme['content_bg']); detail_form_frame.grid(row=1, column=0, sticky='nsew', padx=10); detail_frame.rowconfigure(1, weight=1); detail_frame.columnconfigure(0, weight=1); detail_form_frame.columnconfigure(1, weight=1)

    # Ortak Alanlar
    ttk.Label(detail_form_frame, text="Kesit Adı:", style='Header.TLabel').grid(row=0, column=0, sticky='w', padx=5, pady=5)
    entry_sec_name = create_content_entry(detail_form_frame, textvariable=section_detail_vars["user_name"]); entry_sec_name.grid(row=0, column=1, columnspan=2, sticky='ew', padx=5, pady=5)
    ttk.Label(detail_form_frame, text="Geometri Tipi:", style='Header.TLabel').grid(row=1, column=0, sticky='w', padx=5, pady=5)
    combo_geom_type = create_content_combobox(detail_form_frame, ["Dikdörtgen", "Dairesel"], textvariable=section_detail_vars["geom_type"]); # Şimdilik T/L yok
    combo_geom_type.bind("<<ComboboxSelected>>", lambda e: on_section_type_change()); combo_geom_type.grid(row=1, column=1, columnspan=2, sticky='ew', padx=5, pady=5)

    # Boyut Alanları Çerçeveleri (Başlangıçta gizli) - Grid satırı 2
    rect_dim_frame = tk.Frame(detail_form_frame, bg=current_theme['content_bg']); section_detail_widgets["rect_dim_frame"] = rect_dim_frame; rect_dim_frame.grid(row=2, column=0, columnspan=3, sticky='ew')
    circ_dim_frame = tk.Frame(detail_form_frame, bg=current_theme['content_bg']); section_detail_widgets["circ_dim_frame"] = circ_dim_frame; circ_dim_frame.grid(row=2, column=0, columnspan=3, sticky='ew')

    # Dikdörtgen Boyutları (rect_dim_frame içinde)
    ttk.Label(rect_dim_frame, text="Genişlik (b) [mm]:", style='Header.TLabel').grid(row=0, column=0, sticky='w', padx=5, pady=2)
    create_content_entry(rect_dim_frame, textvariable=section_detail_vars["dim_b"], width=10).grid(row=0, column=1, sticky='w', padx=5, pady=2)
    ttk.Label(rect_dim_frame, text="Yükseklik (h) [mm]:", style='Header.TLabel').grid(row=1, column=0, sticky='w', padx=5, pady=2)
    create_content_entry(rect_dim_frame, textvariable=section_detail_vars["dim_h"], width=10).grid(row=1, column=1, sticky='w', padx=5, pady=2)

    # Dairesel Boyutları (circ_dim_frame içinde)
    ttk.Label(circ_dim_frame, text="Çap (D) [mm]:", style='Header.TLabel').grid(row=0, column=0, sticky='w', padx=5, pady=2)
    create_content_entry(circ_dim_frame, textvariable=section_detail_vars["dim_D"], width=10).grid(row=0, column=1, sticky='w', padx=5, pady=2)

    # Paspayı (Grid satırı 3)
    ttk.Label(detail_form_frame, text="Paspayı (c) [mm]:", style='Header.TLabel').grid(row=3, column=0, sticky='w', padx=5, pady=5)
    entry_cover = create_content_entry(detail_form_frame, textvariable=section_detail_vars["cover"], width=10); entry_cover.grid(row=3, column=1, sticky='w', padx=5, pady=5)

    # Hesaplanan Özellikler (Placeholder - Grid satırı 4)
    props_frame = tk.Frame(detail_form_frame, bg=current_theme['content_bg']); props_frame.grid(row=4, column=0, columnspan=3, sticky='ew', pady=(15, 5))
    ttk.Label(props_frame, text="Hesaplanan Özellikler:", style='Header.TLabel').pack(anchor='w')
    prop_area = create_content_text(props_frame, "Alan: -", size=12); prop_area.pack(anchor='w', padx=20); section_detail_widgets["prop_area"] = prop_area
    prop_ix = create_content_text(props_frame, "Ix: -", size=12); prop_ix.pack(anchor='w', padx=20); section_detail_widgets["prop_ix"] = prop_ix
    prop_iy = create_content_text(props_frame, "Iy: -", size=12); prop_iy.pack(anchor='w', padx=20); section_detail_widgets["prop_iy"] = prop_iy

    # Kaydet/Vazgeç Butonları (Grid satırı 5)
    form_button_frame = tk.Frame(detail_frame, bg=current_theme['content_bg']); form_button_frame.grid(row=5, column=0, columnspan=3, sticky='se', pady=10)
    ttk.Button(form_button_frame, text="Vazgeç", style='TButton', command=clear_section_form).pack(side=tk.RIGHT, padx=5)
    ttk.Button(form_button_frame, text="Kaydet", style='TButton', command=save_section_from_form).pack(side=tk.RIGHT, padx=5)

    # Başlangıç durumu
    clear_section_form(); update_section_listbox(); on_section_type_change()


def populate_element_design_page(parent_frame): ttk.Label(parent_frame, text="Tekil Eleman Tasarımı (Geliştirilecek)", style='Header.TLabel').pack(padx=10, pady=10)
def populate_seismic_load_page(parent_frame): ttk.Label(parent_frame, text="Deprem Yükü Hesaplama (TBDY 2018) (Geliştirilecek)", style='Header.TLabel').pack(padx=10, pady=10)
def populate_reporting_page(parent_frame): ttk.Label(parent_frame, text="Raporlama Seçenekleri:", style='Header.TLabel').pack(padx=10, pady=10, anchor='w')

# Profil Yönetimi Sayfası İçeriği
def populate_profiles_page(parent_frame):
    # ... (kod aynı kaldı) ...
    global profile_listbox_ref
    parent_frame.columnconfigure(0, weight=1); parent_frame.rowconfigure(1, weight=1)
    ttk.Label(parent_frame, text="Hesaplama Profilleri", style='Header.TLabel').grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky='w')
    listbox = tk.Listbox(parent_frame, font=("Segoe UI", 14), relief='flat', bd=1, bg=current_theme['listbox_bg'], fg=current_theme['listbox_fg'], selectbackground=current_theme['listbox_select_bg'], selectforeground=current_theme['title_text'], highlightthickness=1, highlightbackground=current_theme['entry_border'], exportselection=False)
    listbox.grid(row=1, column=0, padx=(10,0), pady=5, sticky='nsew'); profile_listbox_ref = listbox
    scrollbar = ttk.Scrollbar(parent_frame, orient='vertical', command=listbox.yview); scrollbar.grid(row=1, column=1, padx=(0,10), pady=5, sticky='ns'); listbox['yscrollcommand'] = scrollbar.set
    button_frame = tk.Frame(parent_frame, bg=current_theme['content_bg']); button_frame.grid(row=2, column=0, columnspan=2, pady=10, sticky='ew')
    load_button = ttk.Button(button_frame, text="Seçili Profili Yükle", style='TButton', command=load_selected_profile); load_button.pack(side=tk.LEFT, padx=5)
    new_button = ttk.Button(button_frame, text="Yeni Profil", style='TButton', command=create_new_profile); new_button.pack(side=tk.LEFT, padx=5)
    rename_button = ttk.Button(button_frame, text="Yeniden Adlandır", style='TButton', command=rename_selected_profile); rename_button.pack(side=tk.LEFT, padx=5)
    delete_button = ttk.Button(button_frame, text="Sil", style='TButton', command=delete_selected_profile); delete_button.pack(side=tk.LEFT, padx=5)
    update_profile_listbox()

# --- Ana Görünüm Fonksiyonları ---
# (show_... fonksiyonları aynı kalır)
def show_dashboard():
    global sub_sidebar_frame, current_view_func
    current_view_func = show_dashboard; sub_sidebar_frame = None
    for widget in content_frame.winfo_children(): widget.destroy()
    label = create_content_label(content_frame, "Panel"); label.pack(pady=20, padx=20, anchor='nw')
    dashboard_main_frame = tk.Frame(content_frame, bg=current_theme['content_bg']); dashboard_main_frame.pack(pady=10, padx=20, fill='both', expand=True)
    text_area = tk.Text(dashboard_main_frame, height=10, width=50, relief='flat', bd=1, font=("Segoe UI", 14), bg=current_theme['text_area_bg'], fg=current_theme['text_area_fg'], insertbackground=current_theme['entry_insert'], highlightthickness=1, highlightbackground=current_theme['text_area_highlight'], highlightcolor=current_theme['button_bg'])
    text_area.pack(side=tk.TOP, fill='both', expand=True)
    text_area.config(state=tk.NORMAL); text_area.delete('1.0', tk.END)
    text_area.insert(tk.END, f"AutoCAD Durumu: {autocad_status_message}\n\n"); text_area.insert(tk.END, "Uygulama durumu ve hızlı bilgiler burada gösterilecek...\n"); text_area.config(state=tk.DISABLED)
    refresh_button = ttk.Button(dashboard_main_frame, text="Yenile", command=refresh_autocad_status, style='TButton'); refresh_button.pack(side=tk.BOTTOM, anchor='se', pady=(10, 0))

def show_autocad_home():
    global current_view_func, connected_autocad_doc_name, app_settings
    current_view_func = show_autocad_home
    is_connected = (connected_autocad_doc_name is not None); control_state = tk.NORMAL if is_connected else tk.DISABLED
    for widget in content_frame.winfo_children(): widget.destroy()
    create_autocad_sub_sidebar(content_frame)
    settings_area_frame = tk.Frame(content_frame, bg=current_theme['content_bg']); settings_area_frame.pack(pady=15, padx=25, fill='x', anchor='nw')
    settings_header_label = ttk.Label(settings_area_frame, text="Çalışma Alanı Ayarları", style='Header.TLabel', font=("Segoe UI", 16, "bold")); settings_header_label.pack(anchor='w', pady=(0, 5))
    separator = ttk.Separator(settings_area_frame, orient='horizontal'); separator.pack(fill='x', anchor='w', pady=(0, 15))
    grid_frame = tk.Frame(settings_area_frame, bg=current_theme['content_bg']); grid_frame.pack(anchor='w', pady=5)
    grid_label = ttk.Label(grid_frame, text="Görünüm:", style='Header.TLabel'); grid_label.pack(side=tk.LEFT, padx=(0, 10))
    grid_var = tk.IntVar(); # saved_grid_mode = app_settings.get("autocad_settings", {}).get("gridmode", 0); grid_var.set(saved_grid_mode) # Artık profilde değil
    grid_check_frame = create_custom_checkbutton(grid_frame, "Izgara Modu (GRIDMODE)", grid_var, command=lambda v=grid_var: toggle_grid_mode(v), state=control_state); grid_check_frame.pack(side=tk.LEFT, pady=3)
    osnap_frame = tk.Frame(settings_area_frame, bg=current_theme['content_bg']); osnap_frame.pack(anchor='w', pady=10)
    osnap_label = ttk.Label(osnap_frame, text="Nesne Kenetleme (OSMODE):", style='Header.TLabel'); osnap_label.pack(anchor='w')
    osnap_options_frame = tk.Frame(osnap_frame, bg=current_theme['content_bg']); osnap_options_frame.pack(anchor='w', padx=20, pady=(5,0))
    osnap_vars = {}; osnap_modes = {"Endpoint": 1, "Midpoint": 2, "Center": 4, "Node": 8, "Intersection": 32}
    saved_osmode = 0 # Varsayılan 0 yapalım
    # saved_osmode = app_settings.get("autocad_settings", {}).get("osmode", 0) # Artık profilde değil
    for name, bit_value in osnap_modes.items():
        var = tk.IntVar();
        if saved_osmode & bit_value: var.set(1)
        else: var.set(0)
        chk_frame = create_custom_checkbutton(osnap_options_frame, name, var, command=lambda: update_osmode(osnap_vars, osnap_modes), state=control_state); chk_frame.pack(side=tk.LEFT, padx=5, pady=3)
        osnap_vars[bit_value] = var
    all_check_frames = [];
    if grid_frame: all_check_frames.extend(w for w in grid_frame.winfo_children() if isinstance(w, tk.Frame))
    if osnap_options_frame: all_check_frames.extend(w for w in osnap_options_frame.winfo_children() if isinstance(w, tk.Frame))
    if is_connected: # Bağlıysa AutoCAD'den oku
        current_gridmode = get_autocad_variable("GRIDMODE", 0); grid_var.set(current_gridmode)
        current_osmode = get_autocad_variable("OSMODE", 0)
        for bit_value, var in osnap_vars.items(): var.set(1) if current_osmode & bit_value else var.set(0)
        for frame in all_check_frames:
             if hasattr(frame, "update_visual_func"): frame.update_visual_func()
    if connected_autocad_doc_name: file_text = f"Bağlı Dosya: {connected_autocad_doc_name}"
    else: file_text = "Bağlı Dosya: Yok"
    doc_name_label = create_content_text(content_frame, file_text, size=12); doc_name_label.pack(side=tk.BOTTOM, anchor='se', padx=20, pady=10)

# --- AutoCAD Ayar Komutları ---
def toggle_grid_mode(variable):
    new_grid_mode = variable.get(); set_autocad_variable("GRIDMODE", new_grid_mode)
def update_osmode(osnap_vars_dict, osnap_modes_dict):
    new_osmode_value = 0
    for bit_value, var in osnap_vars_dict.items():
        if var.get() == 1: new_osmode_value |= bit_value
    set_autocad_variable("OSMODE", new_osmode_value)

# --- AutoCAD Test Alanı Fonksiyonları ---
# (select_area_in_autocad ve draw_shape_in_area fonksiyonları aynı kalır)
def select_area_in_autocad(result_text_widget, shape_buttons):
    global selected_area_points
    result_text_widget.config(state=tk.NORMAL); result_text_widget.delete('1.0', tk.END)
    acad = get_acad_instance()
    if not acad: result_text_widget.insert(tk.END, "Hata: AutoCAD bağlantısı kurulamadı."); result_text_widget.config(state=tk.DISABLED); return
    result_text_widget.insert(tk.END, "AutoCAD ekranına geçin ve 4 nokta seçin...\n(Arayüz bu sırada donabilir)\n"); root.update_idletasks()
    points = []; selected_area_points = None; button_state = tk.DISABLED
    try:
        acad.prompt("Lütfen 1. noktayı seçin (İptal için Esc):\n"); p1 = tuple(acad.doc.Utility.GetPoint())
        acad.prompt("Lütfen 2. noktayı seçin:\n"); p2 = tuple(acad.doc.Utility.GetPoint())
        acad.prompt("Lütfen 3. noktayı seçin:\n"); p3 = tuple(acad.doc.Utility.GetPoint())
        acad.prompt("Lütfen 4. noktayı seçin:\n"); p4 = tuple(acad.doc.Utility.GetPoint())
        points = [p1, p2, p3, p4]; selected_area_points = points
        result_text_widget.insert(tk.END, "Seçilen Noktalar:\n")
        for i, p in enumerate(points): result_text_widget.insert(tk.END, f"{i+1}. Nokta: {p}\n")
        result_text_widget.insert(tk.END, "\nAlan başarıyla seçildi. Şimdi şekil çizebilirsiniz."); button_state = tk.NORMAL
    except Exception as e: print(f"Nokta seçimi hatası/iptali: {e}"); result_text_widget.insert(tk.END, f"\nHata veya İptal: Nokta seçimi tamamlanamadı.\n{e}"); selected_area_points = None; button_state = tk.DISABLED
    finally:
        try: acad.prompt("\n")
        except: pass
        result_text_widget.config(state=tk.DISABLED)
        for btn in shape_buttons.values():
             if btn: btn.configure(state=button_state)
        bring_window_to_front()

def draw_shape_in_area(shape_type, result_text_widget):
    global selected_area_points
    result_text_widget.config(state=tk.NORMAL); result_text_widget.delete('1.0', tk.END)
    if not selected_area_points or len(selected_area_points) != 4: result_text_widget.insert(tk.END, "Hata: Önce 'Alan Seç' ile 4 nokta belirlemelisiniz."); result_text_widget.config(state=tk.DISABLED); return
    acad = get_acad_instance()
    if not acad: result_text_widget.insert(tk.END, "Hata: AutoCAD bağlantısı kurulamadı."); result_text_widget.config(state=tk.DISABLED); return
    try: model = acad.ActiveDocument.ModelSpace
    except Exception as e: print(f"ModelSpace erişim hatası: {e}"); result_text_widget.insert(tk.END, f"Hata: AutoCAD ModelSpace erişilemedi.\n{e}"); result_text_widget.config(state=tk.DISABLED); return
    try:
        xs = [p[0] for p in selected_area_points]; ys = [p[1] for p in selected_area_points]
        min_x, max_x = min(xs), max(xs); min_y, max_y = min(ys), max(ys)
        center_x = (min_x + max_x) / 2; center_y = (min_y + max_y) / 2
        width = max_x - min_x; height = max_y - min_y
        size = min(width, height) * 0.8
        if size <= 0: result_text_widget.insert(tk.END, "Hata: Geçersiz alan boyutu."); result_text_widget.config(state=tk.DISABLED); return
        center_point_tuple = (center_x, center_y, 0); radius = size / 2.0
        result_text_widget.insert(tk.END, f"'{shape_type}' çiziliyor...\nMerkez: ({center_x:.2f}, {center_y:.2f}), Boyut: {size:.2f}\n"); root.update_idletasks()
        if not APoint: result_text_widget.insert(tk.END, "Hata: APoint pyautocad'den import edilemedi."); result_text_widget.config(state=tk.DISABLED); return

        if shape_type == 'kare':
            half_size = size / 2.0; p1 = APoint(center_x - half_size, center_y - half_size); p2 = APoint(center_x + half_size, center_y - half_size); p3 = APoint(center_x + half_size, center_y + half_size); p4 = APoint(center_x - half_size, center_y + half_size)
            model.AddLine(p1, p2); model.AddLine(p2, p3); model.AddLine(p3, p4); model.AddLine(p4, p1)
        elif shape_type == 'daire': model.AddCircle(APoint(center_x, center_y), radius)
        elif shape_type == 'üçgen':
            p1 = APoint(center_x, center_y + radius); p2 = APoint(center_x - radius * math.sqrt(3)/2, center_y - radius/2); p3 = APoint(center_x + radius * math.sqrt(3)/2, center_y - radius/2)
            model.AddLine(p1, p2); model.AddLine(p2, p3); model.AddLine(p3, p1)
        result_text_widget.insert(tk.END, f"'{shape_type}' başarıyla çizildi.")
    except Exception as e: print(f"Şekil çizme hatası: {e}"); result_text_widget.insert(tk.END, f"\nHata: Şekil çizilemedi.\n{e}")
    finally: result_text_widget.config(state=tk.DISABLED); bring_window_to_front()

# AutoCAD Test Alanı Görünümü
def show_autocad_test_area():
    # ... (kod aynı kaldı) ...
    global current_view_func, connected_autocad_doc_name, shape_buttons_references
    current_view_func = show_autocad_test_area
    is_connected = (connected_autocad_doc_name is not None); control_state = tk.NORMAL if is_connected else tk.DISABLED
    shape_button_state = tk.NORMAL if selected_area_points else tk.DISABLED
    for widget in content_frame.winfo_children(): widget.destroy()
    create_autocad_sub_sidebar(content_frame)
    label = create_content_label(content_frame, "AutoCAD Test Alanı"); label.pack(pady=10, padx=20, anchor='nw')
    test_main_frame = tk.Frame(content_frame, bg=current_theme['content_bg']); test_main_frame.pack(pady=15, padx=25, fill='both', expand=True, anchor='nw')
    button_area_frame = tk.Frame(test_main_frame, bg=current_theme['content_bg']); button_area_frame.pack(pady=5, anchor='w')
    result_text = tk.Text(test_main_frame, height=10, width=50, relief='flat', bd=1, font=("Segoe UI", 13), bg=current_theme['text_area_bg'], fg=current_theme['text_area_fg'], insertbackground=current_theme['entry_insert'], highlightthickness=1, highlightbackground=current_theme['text_area_highlight'], highlightcolor=current_theme['button_bg'], state=tk.DISABLED); result_text.pack(side=tk.TOP, fill='both', expand=True, pady=(10, 10))
    shape_buttons_references = {}
    select_button = ttk.Button(button_area_frame, text="Alan Seç (4 Nokta)", style='TButton', command=lambda rt=result_text, sb=shape_buttons_references: select_area_in_autocad(rt, sb), state=control_state); select_button.pack(side=tk.LEFT, anchor='w', padx=(0,10))
    square_button = ttk.Button(button_area_frame, text="Kare", style='TButton', command=lambda rt=result_text: draw_shape_in_area('kare', rt), state=shape_button_state); square_button.pack(side=tk.LEFT, anchor='w', padx=5); shape_buttons_references['kare'] = square_button
    triangle_button = ttk.Button(button_area_frame, text="Üçgen", style='TButton', command=lambda rt=result_text: draw_shape_in_area('üçgen', rt), state=shape_button_state); triangle_button.pack(side=tk.LEFT, anchor='w', padx=5); shape_buttons_references['üçgen'] = triangle_button
    circle_button = ttk.Button(button_area_frame, text="Daire", style='TButton', command=lambda rt=result_text: draw_shape_in_area('daire', rt), state=shape_button_state); circle_button.pack(side=tk.LEFT, anchor='w', padx=5); shape_buttons_references['daire'] = circle_button
    if connected_autocad_doc_name: file_text = f"Bağlı Dosya: {connected_autocad_doc_name}"
    else: file_text = "Bağlı Dosya: Yok"
    doc_name_label = create_content_text(content_frame, file_text, size=12); doc_name_label.pack(side=tk.BOTTOM, anchor='se', padx=20, pady=10)


# --- Hesaplamalar Bölümü Sayfa Fonksiyonları ---
def show_calc_project_info():
    global current_view_func, sub_sidebar_frame
    current_view_func = show_calc_project_info; sub_sidebar_frame = None
    for widget in content_frame.winfo_children(): widget.destroy()
    create_calculations_sub_sidebar(content_frame)
    page_frame = ttk.Frame(content_frame, style='TFrame', padding=(15, 15)); page_frame.pack(expand=True, fill='both', padx=10, pady=10)
    populate_project_info_page(page_frame)

def show_calc_materials():
    global current_view_func, sub_sidebar_frame
    current_view_func = show_calc_materials; sub_sidebar_frame = None
    for widget in content_frame.winfo_children(): widget.destroy()
    create_calculations_sub_sidebar(content_frame)
    page_frame = ttk.Frame(content_frame, style='TFrame', padding=(15, 15)); page_frame.pack(expand=True, fill='both', padx=10, pady=10)
    populate_material_page(page_frame)

def show_calc_sections():
    global current_view_func, sub_sidebar_frame
    current_view_func = show_calc_sections; sub_sidebar_frame = None
    for widget in content_frame.winfo_children(): widget.destroy()
    create_calculations_sub_sidebar(content_frame)
    page_frame = ttk.Frame(content_frame, style='TFrame', padding=(15, 15)); page_frame.pack(expand=True, fill='both', padx=10, pady=10)
    populate_section_page(page_frame) # Bu fonksiyon artık içeriği dolduracak

def show_calc_element_design():
    global current_view_func, sub_sidebar_frame
    current_view_func = show_calc_element_design; sub_sidebar_frame = None
    for widget in content_frame.winfo_children(): widget.destroy()
    create_calculations_sub_sidebar(content_frame)
    page_frame = ttk.Frame(content_frame, style='TFrame', padding=(15, 15)); page_frame.pack(expand=True, fill='both', padx=10, pady=10)
    populate_element_design_page(page_frame)

def show_calc_seismic():
    global current_view_func, sub_sidebar_frame
    current_view_func = show_calc_seismic; sub_sidebar_frame = None
    for widget in content_frame.winfo_children(): widget.destroy()
    create_calculations_sub_sidebar(content_frame)
    page_frame = ttk.Frame(content_frame, style='TFrame', padding=(15, 15)); page_frame.pack(expand=True, fill='both', padx=10, pady=10)
    populate_seismic_load_page(page_frame)

def show_calc_reporting():
    global current_view_func, sub_sidebar_frame
    current_view_func = show_calc_reporting; sub_sidebar_frame = None
    for widget in content_frame.winfo_children(): widget.destroy()
    create_calculations_sub_sidebar(content_frame)
    page_frame = ttk.Frame(content_frame, style='TFrame', padding=(15, 15)); page_frame.pack(expand=True, fill='both', padx=10, pady=10)
    populate_reporting_page(page_frame)

# Profiller Sayfası Görünümü
def show_calc_profiles():
    global current_view_func, sub_sidebar_frame
    current_view_func = show_calc_profiles; sub_sidebar_frame = None
    for widget in content_frame.winfo_children(): widget.destroy()
    create_calculations_sub_sidebar(content_frame)
    page_frame = ttk.Frame(content_frame, style='TFrame', padding=(15, 15))
    page_frame.pack(expand=True, fill='both', padx=10, pady=10)
    populate_profiles_page(page_frame)

# Ayarlar Görünümü
def show_settings():
    global sub_sidebar_frame, current_view_func
    current_view_func = show_settings; sub_sidebar_frame = None
    for widget in content_frame.winfo_children(): widget.destroy()
    label = create_content_label(content_frame, "Ayarlar"); label.pack(pady=20, padx=20, anchor='nw')
    theme_frame = tk.Frame(content_frame, bg=current_theme['content_bg']); theme_frame.pack(pady=10, padx=40, anchor='w', fill='x')
    theme_label_text = ttk.Label(theme_frame, text="Uygulama Teması:", font=("Segoe UI", 14), background=current_theme['content_bg'], foreground=current_theme['text']); theme_label_text.pack(side=tk.LEFT, padx=(0, 10))
    dark_button = ttk.Button(theme_frame, text="Siyah", style='TButton', command=lambda: apply_theme("dark")); dark_button.pack(side=tk.LEFT, padx=5)
    light_button = ttk.Button(theme_frame, text="Beyaz", style='TButton', command=lambda: apply_theme("light")); light_button.pack(side=tk.LEFT, padx=5)
    system_button = ttk.Button(theme_frame, text="Sistem", style='TButton', command=lambda: apply_theme("system")); system_button.pack(side=tk.LEFT, padx=5)
    version_label = create_content_text(content_frame, "Version 1.0.1", size=10); version_label.pack(side=tk.BOTTOM, anchor='se', padx=20, pady=10)

# --- Profil Veri Yönetimi Fonksiyonları ---
# (save_project_info, load_project_info, update_profile_listbox, load_selected_profile,
#  create_new_profile, rename_selected_profile, delete_selected_profile fonksiyonları aynı kaldı)
def save_project_info():
    global profiles_data, current_profile_name, project_info_vars
    if not current_profile_name: messagebox.showwarning("Profil Seçilmedi", "Lütfen önce bir profil seçin veya oluşturun."); return
    profile = profiles_data.setdefault(current_profile_name, {"project_info": {}, "materials": [], "sections": []})
    project_info = profile.setdefault("project_info", {})
    project_info["name"] = project_info_vars.get("name", tk.StringVar()).get()
    desc_widget = project_info_vars.get("desc_widget")
    if desc_widget: project_info["desc"] = desc_widget.get("1.0", tk.END).strip()
    else: project_info["desc"] = ""
    project_info["engineer"] = project_info_vars.get("engineer", tk.StringVar()).get()
    project_info["concrete_reg"] = project_info_vars.get("concrete_reg", tk.StringVar()).get()
    project_info["seismic_reg"] = project_info_vars.get("seismic_reg", tk.StringVar()).get()
    project_info["load_reg"] = project_info_vars.get("load_reg", tk.StringVar()).get()
    project_info["units"] = project_info_vars.get("units", tk.StringVar()).get()
    save_profiles(); messagebox.showinfo("Kaydedildi", f"'{current_profile_name}' profili için proje bilgileri kaydedildi.")

def load_project_info():
    global profiles_data, current_profile_name, project_info_vars
    if not project_info_vars: print("Info: Project info variables not ready for loading."); return
    if current_profile_name not in profiles_data:
        print(f"Warning: Profile '{current_profile_name}' not found for loading project info.")
        project_info_vars.get("name", tk.StringVar()).set("Yeni Proje")
        desc_widget = project_info_vars.get("desc_widget");
        if desc_widget: desc_widget.delete("1.0", tk.END)
        project_info_vars.get("engineer", tk.StringVar()).set("")
        return
    profile = profiles_data[current_profile_name]; project_info = profile.get("project_info", {})
    project_info_vars.get("name", tk.StringVar()).set(project_info.get("name", "Yeni Proje"))
    desc_widget = project_info_vars.get("desc_widget")
    if desc_widget: desc_widget.delete("1.0", tk.END); desc_widget.insert("1.0", project_info.get("desc", ""))
    project_info_vars.get("engineer", tk.StringVar()).set(project_info.get("engineer", ""))
    project_info_vars.get("concrete_reg", tk.StringVar()).set(project_info.get("concrete_reg", "TS 500 (2000)"))
    project_info_vars.get("seismic_reg", tk.StringVar()).set(project_info.get("seismic_reg", "TBDY 2018"))
    project_info_vars.get("load_reg", tk.StringVar()).set(project_info.get("load_reg", "TS 498 (1997)"))
    project_info_vars.get("units", tk.StringVar()).set(project_info.get("units", "Metrik (kN, m, C)"))
    print(f"Project info loaded for profile: {current_profile_name}")

# --- Kesit Sayfası Yardımcı Fonksiyonları ---
def clear_section_form():
    section_detail_vars.get("user_name", tk.StringVar()).set("")
    section_detail_vars.get("geom_type", tk.StringVar()).set("Dikdörtgen")
    section_detail_vars.get("dim_b", tk.DoubleVar()).set(0.0)
    section_detail_vars.get("dim_h", tk.DoubleVar()).set(0.0)
    section_detail_vars.get("dim_D", tk.DoubleVar()).set(0.0)
    section_detail_vars.get("cover", tk.DoubleVar()).set(30.0)
    if section_detail_widgets.get("prop_area"): section_detail_widgets["prop_area"].config(text="-")
    if section_detail_widgets.get("prop_ix"): section_detail_widgets["prop_ix"].config(text="-")
    if section_detail_widgets.get("prop_iy"): section_detail_widgets["prop_iy"].config(text="-")
    if section_listbox_ref:
        selection = section_listbox_ref.curselection()
        if selection: section_listbox_ref.selection_clear(selection[0])
    on_section_type_change()

def update_section_listbox():
    if section_listbox_ref and current_profile_name in profiles_data:
        section_listbox_ref.delete(0, tk.END)
        sections = profiles_data[current_profile_name].get("sections", [])
        sections.sort(key=lambda x: x.get("user_name", "").lower())
        for sec in sections:
            display_name = f"{sec.get('geom_type', '?')}: {sec.get('user_name', 'İsimsiz')}"
            section_listbox_ref.insert(tk.END, display_name)

def on_section_type_change():
    if not section_detail_widgets: return
    geom_type = section_detail_vars.get("geom_type", tk.StringVar()).get()
    # İlgili çerçeveyi göster/gizle
    if section_detail_widgets.get("rect_dim_frame"):
        if geom_type == "Dikdörtgen": section_detail_widgets["rect_dim_frame"].grid()
        else: section_detail_widgets["rect_dim_frame"].grid_remove()
    if section_detail_widgets.get("circ_dim_frame"):
        if geom_type == "Dairesel": section_detail_widgets["circ_dim_frame"].grid()
        else: section_detail_widgets["circ_dim_frame"].grid_remove()

def load_selected_section_to_form():
    if not section_listbox_ref: return
    selection = section_listbox_ref.curselection()
    if not selection: return
    selected_index = selection[0]
    sections = profiles_data.get(current_profile_name, {}).get("sections", [])
    if selected_index < 0 or selected_index >= len(sections): messagebox.showerror("Hata", "Seçilen kesit verisi bulunamadı."); return
    section_data = sections[selected_index]
    section_detail_vars.get("user_name", tk.StringVar()).set(section_data.get("user_name", ""))
    section_detail_vars.get("geom_type", tk.StringVar()).set(section_data.get("geom_type", "Dikdörtgen"))
    section_detail_vars.get("cover", tk.DoubleVar()).set(section_data.get("cover", 30.0))
    dims = section_data.get("dimensions", {})
    section_detail_vars.get("dim_b", tk.DoubleVar()).set(dims.get("b", 0.0))
    section_detail_vars.get("dim_h", tk.DoubleVar()).set(dims.get("h", 0.0))
    section_detail_vars.get("dim_D", tk.DoubleVar()).set(dims.get("D", 0.0))
    props = section_data.get("properties", {})
    if section_detail_widgets.get("prop_area"): section_detail_widgets["prop_area"].config(text=str(props.get("Area", "-")))
    if section_detail_widgets.get("prop_ix"): section_detail_widgets["prop_ix"].config(text=str(props.get("Ix", "-")))
    if section_detail_widgets.get("prop_iy"): section_detail_widgets["prop_iy"].config(text=str(props.get("Iy", "-")))
    on_section_type_change()

def save_section_from_form():
    global profiles_data, current_profile_name
    if not current_profile_name: messagebox.showerror("Hata", "Aktif profil bulunamadı."); return
    user_name = section_detail_vars.get("user_name", tk.StringVar()).get().strip()
    if not user_name: messagebox.showerror("Hata", "Kesit adı boş olamaz."); return
    geom_type = section_detail_vars.get("geom_type", tk.StringVar()).get()
    dimensions = {}; cover = 30.0
    try:
        cover = section_detail_vars.get("cover", tk.DoubleVar()).get()
        if geom_type == "Dikdörtgen":
            dimensions["b"] = section_detail_vars.get("dim_b", tk.DoubleVar()).get()
            dimensions["h"] = section_detail_vars.get("dim_h", tk.DoubleVar()).get()
            if dimensions["b"] <= 0 or dimensions["h"] <= 0: raise ValueError("Boyutlar pozitif olmalı.")
        elif geom_type == "Dairesel":
            dimensions["D"] = section_detail_vars.get("dim_D", tk.DoubleVar()).get()
            if dimensions["D"] <= 0: raise ValueError("Çap pozitif olmalı.")
        if cover < 0: raise ValueError("Paspayı negatif olamaz.")
    except (tk.TclError, ValueError) as e: messagebox.showerror("Hata", f"Lütfen geçerli sayısal boyut/paspayı girin.\n{e}"); return

    new_section_data = {"user_name": user_name, "geom_type": geom_type, "dimensions": dimensions, "cover": cover, "properties": {}}
    profile = profiles_data.setdefault(current_profile_name, {"project_info": {}, "materials": [], "sections": []})
    sections = profile.setdefault("sections", [])
    selected_index = -1; original_name_if_editing = None
    if section_listbox_ref: selection = section_listbox_ref.curselection();
    if selection: selected_index = selection[0]
    if selected_index != -1:
        try: original_name_if_editing = sections[selected_index].get("user_name")
        except IndexError: selected_index = -1
    found_index = -1
    for i, sec in enumerate(sections):
        if sec.get("user_name") == user_name: found_index = i; break

    if user_name == original_name_if_editing or found_index == -1:
        if selected_index != -1 and original_name_if_editing is not None:
             try: sections[selected_index] = new_section_data; print(f"Section '{user_name}' updated.")
             except IndexError: sections.append(new_section_data); print(f"Section '{user_name}' added (update failed, added as new).")
        else: sections.append(new_section_data); print(f"Section '{user_name}' added.")
        save_profiles(); update_section_listbox(); clear_section_form(); messagebox.showinfo("Başarılı", f"Kesit '{user_name}' kaydedildi.")
    else: messagebox.showerror("Hata", f"'{user_name}' adında başka bir kesit zaten var.")

def delete_selected_section():
    global profiles_data
    if not section_listbox_ref: return
    selection = section_listbox_ref.curselection()
    if not selection: messagebox.showwarning("Kesit Seçilmedi", "Lütfen silinecek kesiti seçin."); return
    selected_index = selection[0]
    profile = profiles_data.get(current_profile_name)
    if profile and "sections" in profile and 0 <= selected_index < len(profile["sections"]):
        section_to_delete = profile["sections"][selected_index]
        user_name_to_delete = section_to_delete.get("user_name", "Bilinmeyen")
        if messagebox.askyesno("Kesiti Sil", f"'{user_name_to_delete}' kesitini silmek istediğinizden emin misiniz?", parent=root):
            del profile["sections"][selected_index]
            save_profiles(); update_section_listbox(); clear_section_form()
            messagebox.showinfo("Başarılı", f"'{user_name_to_delete}' kesiti silindi.")
    else: messagebox.showerror("Hata", "Kesit silinemedi.")


# --- Profil Yönetimi Sayfası Fonksiyonları ---
# (update_profile_listbox, load_selected_profile, create_new_profile,
#  rename_selected_profile, delete_selected_profile fonksiyonları aynı kaldı)
def update_profile_listbox():
    if profile_listbox_ref:
        profile_listbox_ref.delete(0, tk.END)
        for name in sorted(profiles_data.keys()): profile_listbox_ref.insert(tk.END, name)
        try:
            idx = list(sorted(profiles_data.keys())).index(current_profile_name)
            profile_listbox_ref.selection_clear(0, tk.END); profile_listbox_ref.select_set(idx); profile_listbox_ref.activate(idx)
        except ValueError: pass

def load_selected_profile():
    global current_profile_name
    if not profile_listbox_ref: return
    selection = profile_listbox_ref.curselection()
    if not selection: messagebox.showwarning("Profil Seçilmedi", "Lütfen listeden yüklenecek bir profil seçin."); return
    selected_name = profile_listbox_ref.get(selection[0])
    if selected_name in profiles_data:
        current_profile_name = selected_name; print(f"Profile '{current_profile_name}' selected.")
        show_calc_project_info(); # Proje bilgilerini yükle/göster
        # Malzeme ve Kesit listelerini de güncelle (eğer o sayfalar açıksa diye değil, genel olarak)
        if material_listbox_ref: update_material_listbox()
        if section_listbox_ref: update_section_listbox()
        messagebox.showinfo("Profil Yüklendi", f"'{current_profile_name}' profili yüklendi.")
    else: messagebox.showerror("Hata", f"Seçilen profil '{selected_name}' bulunamadı.")

def create_new_profile():
    global profiles_data, current_profile_name
    new_name = simpledialog.askstring("Yeni Profil", "Yeni profil için bir isim girin:", parent=root)
    if new_name and new_name.strip():
        new_name = new_name.strip()
        if new_name in profiles_data: messagebox.showerror("Hata", f"'{new_name}' isimli profil zaten mevcut.")
        else:
            default_profile_data = {"project_info": {"name": new_name}, "materials": [], "sections": []}
            profiles_data[new_name] = default_profile_data; current_profile_name = new_name
            save_profiles(); update_profile_listbox(); show_calc_project_info()
            messagebox.showinfo("Başarılı", f"'{new_name}' profili oluşturuldu ve aktif hale getirildi.")
    elif new_name is not None: messagebox.showwarning("Geçersiz İsim", "Profil adı boş olamaz.")

def rename_selected_profile():
    global profiles_data, current_profile_name
    if not profile_listbox_ref: return
    selection = profile_listbox_ref.curselection()
    if not selection: messagebox.showwarning("Profil Seçilmedi", "Lütfen listeden yeniden adlandırılacak bir profil seçin."); return
    old_name = profile_listbox_ref.get(selection[0])
    new_name = simpledialog.askstring("Profili Yeniden Adlandır", f"'{old_name}' için yeni isim girin:", initialvalue=old_name, parent=root)
    if new_name and new_name.strip():
        new_name = new_name.strip()
        if new_name == old_name: return
        if new_name in profiles_data: messagebox.showerror("Hata", f"'{new_name}' isimli profil zaten mevcut.")
        else:
            profiles_data[new_name] = profiles_data.pop(old_name)
            if current_profile_name == old_name: current_profile_name = new_name
            save_profiles(); update_profile_listbox()
            messagebox.showinfo("Başarılı", f"'{old_name}' profili '{new_name}' olarak yeniden adlandırıldı.")
    elif new_name is not None: messagebox.showwarning("Geçersiz İsim", "Profil adı boş olamaz.")

def delete_selected_profile():
    global profiles_data, current_profile_name
    if not profile_listbox_ref: return
    selection = profile_listbox_ref.curselection()
    if not selection: messagebox.showwarning("Profil Seçilmedi", "Lütfen listeden silinecek bir profil seçin."); return
    profile_to_delete = profile_listbox_ref.get(selection[0])
    if len(profiles_data) <= 1: messagebox.showerror("Hata", "Son kalan profil silinemez."); return
    if messagebox.askyesno("Profili Sil", f"'{profile_to_delete}' profilini silmek istediğinizden emin misiniz?", parent=root):
        del profiles_data[profile_to_delete]
        if current_profile_name == profile_to_delete: current_profile_name = list(profiles_data.keys())[0]; load_project_info()
        save_profiles(); update_profile_listbox()
        messagebox.showinfo("Başarılı", f"'{profile_to_delete}' profili silindi.")


# --- Sayfa İçeriklerini Oluşturan Fonksiyonlar ---
# (populate_... fonksiyonları buraya taşındı)
# ... populate_project_info_page ...
# ... populate_material_page ...
# ... populate_section_page ...
# ... populate_element_design_page ...
# ... populate_seismic_load_page ...
# ... populate_reporting_page ...
# ... populate_profiles_page ...


# --- Ana Görünüm Fonksiyonları ---
# (show_... fonksiyonları buraya taşındı)
# ... show_dashboard ...
# ... show_autocad_home ...
# ... show_autocad_test_area ...
# ... show_calc_project_info ...
# ... show_calc_materials ...
# ... show_calc_sections ...
# ... show_calc_element_design ...
# ... show_calc_seismic ...
# ... show_calc_reporting ...
# ... show_calc_profiles ...
# ... show_settings ...


# ==============================================================================
# ANA UYGULAMA AKIŞI
# ==============================================================================

# --- Ana Pencere ve Ana Yapı Oluşturma ---
root = tk.Tk()
root.title("İnşaat Mühendisliği ve AutoCAD Yardımcı Uygulaması")

# --- Stil Ayarları ---
style = ttk.Style()
style.theme_use('clam')

# --- Ana Menü Çubuğu (Özel) ---
custom_menu_bar = tk.Frame(root, height=30)
custom_menu_bar.pack(side=tk.TOP, fill=tk.X); custom_menu_bar.pack_propagate(False)
menu_buttons = {}; dropdown_menus = {}
mb_file = tk.Menubutton(custom_menu_bar, text="Dosya", relief='flat', font=('Segoe UI', 11), padx=5, pady=2); menu_buttons['file'] = mb_file; mb_file.pack(side=tk.LEFT, padx=1)
menu_file = tk.Menu(mb_file, tearoff=0); dropdown_menus['file'] = menu_file; menu_file.add_command(label="Yeni Proje", command=lambda: print("TODO: Yeni Proje")); menu_file.add_command(label="Proje Aç", command=lambda: print("TODO: Proje Aç")); menu_file.add_command(label="Proje Kaydet", command=lambda: print("TODO: Proje Kaydet")); menu_file.add_command(label="Projeyi Farklı Kaydet", command=lambda: print("TODO: Farklı Kaydet")); menu_file.add_separator(); menu_file.add_command(label="Rapor Al", command=lambda: print("TODO: Rapor Al")); menu_file.add_separator(); menu_file.add_command(label="Çıkış", command=on_closing); mb_file["menu"] = menu_file
mb_defs = tk.Menubutton(custom_menu_bar, text="Tanımlamalar", relief='flat', font=('Segoe UI', 11), padx=5, pady=2); menu_buttons['defs'] = mb_defs; mb_defs.pack(side=tk.LEFT, padx=1)
menu_defs = tk.Menu(mb_defs, tearoff=0); dropdown_menus['defs'] = menu_defs; menu_defs.add_command(label="Malzemeler", command=show_calc_materials); menu_defs.add_command(label="Kesitler", command=show_calc_sections); menu_defs.add_command(label="Yükler", command=lambda: print("TODO: Yük Tanımları")); mb_defs["menu"] = menu_defs
mb_calc = tk.Menubutton(custom_menu_bar, text="Hesaplama", relief='flat', font=('Segoe UI', 11), padx=5, pady=2); menu_buttons['calc'] = mb_calc; mb_calc.pack(side=tk.LEFT, padx=1)
menu_calc = tk.Menu(mb_calc, tearoff=0); dropdown_menus['calc'] = menu_calc; menu_calc.add_command(label="Tekil Eleman Tasarımı", command=show_calc_element_design); menu_calc.add_command(label="Deprem Yükü Hesabı", command=show_calc_seismic); mb_calc["menu"] = menu_calc
mb_options = tk.Menubutton(custom_menu_bar, text="Ayarlar", relief='flat', font=('Segoe UI', 11), padx=5, pady=2); menu_buttons['options'] = mb_options; mb_options.pack(side=tk.LEFT, padx=1)
menu_options = tk.Menu(mb_options, tearoff=0); dropdown_menus['options'] = menu_options
menu_options.add_command(label="Yönetmelik Seçenekleri", command=lambda: print("TODO: Yönetmelik Ayarları")); menu_options.add_command(label="Birim Sistemi", command=lambda: print("TODO: Birim Sistemi")); menu_options.add_command(label="Genel Program Ayarları", command=show_settings); mb_options["menu"] = menu_options
mb_help = tk.Menubutton(custom_menu_bar, text="Yardım", relief='flat', font=('Segoe UI', 11), padx=5, pady=2); menu_buttons['help'] = mb_help; mb_help.pack(side=tk.LEFT, padx=1)
menu_help = tk.Menu(mb_help, tearoff=0); dropdown_menus['help'] = menu_help
menu_help.add_command(label="Hakkında", command=lambda: messagebox.showinfo("Hakkında", "İnşaat Mühendisliği Yardımcı Uygulaması\nVersiyon 1.0.1")); menu_help.add_command(label="Kullanım Kılavuzu", command=lambda: print("TODO: Kılavuz")); mb_help["menu"] = menu_help

# --- Ana İçerik Alanı (PanedWindow) ---
pane = tk.PanedWindow(root, bd=0, sashwidth=4, sashrelief=tk.FLAT, orient=tk.HORIZONTAL)
pane.pack(fill=tk.BOTH, expand=True)
sidebar_frame = tk.Frame(pane, relief='flat', bd=0)
sidebar_frame.pack_propagate(False)
content_frame = tk.Frame(pane, relief='flat', bd=0)
pane.add(sidebar_frame, stretch="never", width=250)
pane.add(content_frame, stretch="always")

# --- Statik Sidebar Widget'ları Oluşturma ---
sidebar_frame.grid_columnconfigure(0, weight=1)
app_title_label = ttk.Label(sidebar_frame, text="Ana Menü", font=("Segoe UI", 18, "bold"))
app_title_label.grid(row=0, column=0, pady=(15, 20), padx=10, sticky='n')
dashboard_button = ttk.Button(sidebar_frame, text="Panel", style='TButton', command=show_dashboard)
dashboard_button.grid(row=1, column=0, pady=5, padx=10, sticky='ew')
autocad_button = ttk.Button(sidebar_frame, text="AutoCAD", style='TButton', command=show_autocad_home)
autocad_button.grid(row=2, column=0, pady=5, padx=10, sticky='ew')
calc_button = ttk.Button(sidebar_frame, text="Hesaplamalar", style='TButton', command=show_calc_project_info) # Varsayılan sayfa
calc_button.grid(row=3, column=0, pady=5, padx=10, sticky='ew')
sidebar_frame.grid_rowconfigure(4, weight=1)
settings_button = ttk.Button(sidebar_frame, text="Ayarlar", style='TButton', command=show_settings)
settings_button.grid(row=5, column=0, pady=(5, 10), padx=10, sticky='sew')

# --- Başlangıç Ayarları ---
try:
    if sys.platform == "win32": ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception as e: print(f"Warning: DPI awareness error: {e}")

load_settings() # Genel ayarları yükle
load_profiles() # Hesaplama profillerini yükle

initial_geometry = app_settings.get("window_geometry", "1100x700+100+50")
try: root.geometry(initial_geometry)
except tk.TclError as e: print(f"Warning: Invalid geometry: {e}"); root.geometry("1100x700+100+50")
root.minsize(700, 500)
root.protocol("WM_DELETE_WINDOW", on_closing)

autocad_status_message = check_autocad_connection()
initial_theme_name = app_settings.get("theme", "dark")
print(f"Info: Setting initial theme to '{initial_theme_name}'.")

# Başlangıç temasını uygula
apply_theme(initial_theme_name)

# Başlangıç görünümünü göster
show_dashboard()

# --- Ana Döngü ---
root.mainloop()
