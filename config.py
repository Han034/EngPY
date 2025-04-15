# config.py
# Uygulama yapılandırma sabitlerini ve veri sözlüklerini içerir.

import os

# --- Ayarlar Dosyaları ---
SETTINGS_FILE = "settings.json" # Genel uygulama ayarları (tema, pencere boyutu)
PROFILE_FILE = "profiles.json" # Hesaplama profilleri (proje bilgisi, malzemeler, kesitler vb.)

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
# TODO: Daha fazla sınıf ve detaylı özellikler eklenebilir (Ec, fctk, fctd vb.)
CONCRETE_PROPS = {
    "C20/25": {"fck": 20},
    "C25/30": {"fck": 25},
    "C30/37": {"fck": 30},
    "C35/45": {"fck": 35},
    "C40/50": {"fck": 40},
    "C45/55": {"fck": 45},
    "C50/60": {"fck": 50},
}
REBAR_PROPS = {
    "B420C": {"fyk": 420, "Es": 200000},
    "B500C": {"fyk": 500, "Es": 200000},
}

# --- Varsayılan Ayarlar ---
DEFAULT_WINDOW_GEOMETRY = "1100x700+100+50"
DEFAULT_PROFILE_NAME = "Varsayılan Profil"
DEFAULT_PROJECT_INFO = {
    "name": DEFAULT_PROFILE_NAME, "desc": "", "engineer": "",
    "concrete_reg": "TS 500 (2000)", "seismic_reg": "TBDY 2018",
    "load_reg": "TS 498 (1997)", "units": "Metrik (kN, m, C)"
}
DEFAULT_PROFILE_DATA = {
    "project_info": DEFAULT_PROJECT_INFO,
    "materials": [],
    "sections": []
}

# --- Diğer Sabitler ---
APP_NAME = "İnşaat Mühendisliği ve AutoCAD Yardımcı Uygulaması"
APP_VERSION = "1.0.2" # Versiyonu buraya taşıyalım

# --- Font Boyutları (Temel - 96 DPI için) ---
# Bu değerler, DPI ölçeklemesi ile çarpılacak
BASE_FONT_SIZE_MENU = 10
BASE_FONT_SIZE_SMALL = 9
BASE_FONT_SIZE_NORMAL = 11
BASE_FONT_SIZE_MEDIUM = 12
BASE_FONT_SIZE_LARGE = 14
BASE_FONT_SIZE_HEADER = 14
BASE_FONT_SIZE_TITLE = 18
BASE_FONT_SIZE_CHECKBOX_CHAR = 16
BASE_DPI = 96

