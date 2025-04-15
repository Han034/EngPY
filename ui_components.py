# ui_components.py
# Tekrar kullanılabilir Tkinter/ttk widget'ları oluşturan fonksiyonları içerir.

import tkinter as tk
from tkinter import ttk
import config # Tema renkleri ve sabitler için

# --- İçerik Alanı Widget Oluşturma Fonksiyonları ---

def create_content_label(parent, text, current_theme):
    """Belirtilen temaya uygun ana başlık etiketi oluşturur."""
    font_size = 20 # Makul başlık boyutu
    return ttk.Label(parent, text=text, font=("Segoe UI", font_size, "bold"),
                     background=current_theme['content_bg'],
                     foreground=current_theme['title_text'])

def create_content_text(parent, text, current_theme, size=12): # Varsayılan normal metin boyutu: 12
    """Belirtilen temaya uygun normal metin etiketi oluşturur."""
    if "Version" in text: size = 10 # Versiyon küçük kalsın
    return ttk.Label(parent, text=text, font=("Segoe UI", size),
                     background=current_theme['content_bg'],
                     foreground=current_theme['text'])

def create_content_button(parent, text, current_theme, command=None, style_key='TButton'):
    """Belirtilen temaya ve stile uygun buton oluşturur."""
    # style_key: 'TButton' (ana içerik/sidebar) veya 'Sub.TButton' (alt menü)
    return ttk.Button(parent, text=text, command=command, style=style_key)

def create_content_entry(parent, current_theme, width=None, textvariable=None):
    """Belirtilen temaya uygun giriş alanı oluşturur."""
    # Font boyutu stilden alınacak (TEntry)
    entry = ttk.Entry(parent, style='TEntry', width=width, textvariable=textvariable)
    return entry

def create_content_combobox(parent, values, current_theme, state='readonly', width=None, textvariable=None):
    """Belirtilen temaya uygun combobox oluşturur."""
    # Font boyutu stilden alınacak (TCombobox)
    combo = ttk.Combobox(parent, values=values, state=state, width=width, style='TCombobox', textvariable=textvariable)
    return combo

def create_custom_checkbutton(parent, text, variable, current_theme, command=None, state=tk.NORMAL):
    """Unicode karakterler kullanarak özel bir checkbutton oluşturur."""
    check_frame = tk.Frame(parent, bg=current_theme['content_bg'])
    check_char_selected = "☑"; check_char_deselected = "☐"; check_font_size = 16 # Kutucuk boyutu
    check_label = tk.Label(check_frame, font=("Segoe UI Symbol", check_font_size),
                           bg=current_theme['content_bg'], fg=current_theme['check_indicator'])
    # Yanındaki metnin fontu
    text_label = ttk.Label(check_frame, text=text, font=("Segoe UI", 13), # Font: 13
                           background=current_theme['content_bg'], foreground=current_theme['check_fg'])
    def update_visual():
        # Tema değişikliğinde renkleri de güncellemek için:
        check_frame.config(bg=current_theme['content_bg']) # Çerçeve arkaplanı
        check_label.config(bg=current_theme['content_bg'], fg=current_theme['check_indicator'])
        text_label.config(background=current_theme['content_bg'], foreground=current_theme['check_fg'])

        if variable.get() == 1: check_label.config(text=check_char_selected)
        else: check_label.config(text=check_char_deselected)
        current_state = tk.NORMAL if state == tk.NORMAL else tk.DISABLED
        check_label.config(state=current_state); text_label.config(state=current_state)


    check_frame.update_visual_func = update_visual

    def toggle():
        if check_label.cget("state") == tk.DISABLED: return
        variable.set(1 - variable.get()); update_visual()
        if command: command()

    check_label.bind("<Button-1>", lambda e: toggle())
    text_label.bind("<Button-1>", lambda e: toggle())
    check_label.pack(side=tk.LEFT); text_label.pack(side=tk.LEFT, padx=(5, 0))
    update_visual(); return check_frame
