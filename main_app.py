# main_app.py
# Ana Tkinter uygulamasını ve ana arayüz yönetimini içeren sınıf.

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

# Diğer modüllerimizi import edelim
import config
import utils
import autocad_interface
import ui_components
# Frame sınıflarını import edelim
from section_frames import PanelFrame, AutoCADFrame, CalculationsFrame, SettingsFrame

class MainApp:
    """Ana uygulama sınıfı."""
    def __init__(self, root_window):
        """Uygulama ana sınıfını başlatır."""
        self.root = root_window
        # utils modülündeki global root referansını ayarla
        # (bring_window_to_front gibi fonksiyonların erişimi için)
        utils.root = self.root

        # --- Ayarları ve Profilleri Yükle ---
        utils.load_settings() # utils.app_settings global'ini doldurur
        utils.load_profiles() # utils.profiles_data global'ini doldurur
        self.app_settings = utils.app_settings # Referansı al
        self.profiles_data = utils.profiles_data # Referansı al
        self.current_profile_name = utils.current_profile_name # Referansı al

        # --- Pencere Ayarları ---
        self.root.title(config.APP_NAME)
        initial_geometry = self.app_settings.get("window_geometry", config.DEFAULT_WINDOW_GEOMETRY)
        try: self.root.geometry(initial_geometry)
        except tk.TclError as e: print(f"Warning: Invalid geometry: {e}"); self.root.geometry(config.DEFAULT_WINDOW_GEOMETRY)
        self.root.minsize(700, 500)
        self.root.protocol("WM_DELETE_WINDOW", self.quit_app) # Kapatma işlemi

        # --- Stil ve Tema ---
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.current_theme_name = self.app_settings.get("theme", "dark")
        self.current_theme = config.themes.get(self.current_theme_name, config.themes["dark"])

        # --- AutoCAD Durumu ---
        self.autocad_status_message = "Kontrol ediliyor..."
        self.connected_autocad_doc_name = None
        # Bağlantı kontrolünü başlat (ama sonucu hemen kullanma, PanelFrame kendi alacak)
        self.refresh_autocad_status_and_view(initial_load=True)

        # --- Ana Arayüz Elemanları ---
        self.custom_menu_bar = None
        self.menu_buttons = {}
        self.dropdown_menus = {}
        self.pane = None
        self.sidebar_frame = None
        self.content_frame = None
        self.app_title_label = None
        self.current_frame_widget = None # content_frame içindeki aktif frame'i tutar

        # --- Arayüzü Oluştur ---
        self._create_menu()
        self._create_main_layout()
        self._create_sidebar_widgets()

        # --- Başlangıç Temasını Uygula ---
        # Widget referansları artık self içinde olduğu için apply_theme'e göndermeye gerek yok
        self.apply_theme_and_save(self.current_theme_name, initial=True)

        # --- Başlangıç Görünümünü Göster ---
        self.show_frame("Panel") # Başlangıçta Panel'i göster

    def _create_menu(self):
        """Özel üst menü çubuğunu oluşturur."""
        self.custom_menu_bar = tk.Frame(self.root, height=30) # Renk apply_theme'de ayarlanacak
        self.custom_menu_bar.pack(side=tk.TOP, fill=tk.X); self.custom_menu_bar.pack_propagate(False)
        self.menu_buttons = {}; self.dropdown_menus = {}
        menu_font_size = 11 # Sabit boyut

        # Dosya Menubutton
        mb_file = tk.Menubutton(self.custom_menu_bar, text="Dosya", relief='flat', font=('Segoe UI', menu_font_size), padx=5, pady=2)
        self.menu_buttons['file'] = mb_file; mb_file.pack(side=tk.LEFT, padx=1)
        menu_file = tk.Menu(mb_file, tearoff=0); self.dropdown_menus['file'] = menu_file
        menu_file.add_command(label="Yeni Proje", command=lambda: print("TODO: Yeni Proje"))
        menu_file.add_command(label="Proje Aç", command=lambda: print("TODO: Proje Aç"))
        menu_file.add_command(label="Proje Kaydet", command=self.save_current_profile)
        menu_file.add_command(label="Projeyi Farklı Kaydet", command=lambda: print("TODO: Farklı Kaydet"))
        menu_file.add_separator(); menu_file.add_command(label="Rapor Al", command=lambda: self.show_calculation_page("reporting"))
        menu_file.add_separator(); menu_file.add_command(label="Çıkış", command=self.quit_app)
        mb_file["menu"] = menu_file

        # Tanımlamalar Menubutton
        mb_defs = tk.Menubutton(self.custom_menu_bar, text="Tanımlamalar", relief='flat', font=('Segoe UI', menu_font_size), padx=5, pady=2)
        self.menu_buttons['defs'] = mb_defs; mb_defs.pack(side=tk.LEFT, padx=1)
        menu_defs = tk.Menu(mb_defs, tearoff=0); self.dropdown_menus['defs'] = menu_defs
        menu_defs.add_command(label="Malzemeler", command=lambda: self.show_calculation_page("materials"))
        menu_defs.add_command(label="Kesitler", command=lambda: self.show_calculation_page("sections"))
        menu_defs.add_command(label="Yükler", command=lambda: print("TODO: Yük Tanımları"))
        mb_defs["menu"] = menu_defs

        # Hesaplama Menubutton
        mb_calc = tk.Menubutton(self.custom_menu_bar, text="Hesaplama", relief='flat', font=('Segoe UI', menu_font_size), padx=5, pady=2)
        self.menu_buttons['calc'] = mb_calc; mb_calc.pack(side=tk.LEFT, padx=1)
        menu_calc = tk.Menu(mb_calc, tearoff=0); self.dropdown_menus['calc'] = menu_calc
        menu_calc.add_command(label="Tekil Eleman Tasarımı", command=lambda: self.show_calculation_page("element_design"))
        menu_calc.add_command(label="Deprem Yükü Hesabı", command=lambda: self.show_calculation_page("seismic_load"))
        mb_calc["menu"] = menu_calc

        # Ayarlar Menubutton
        mb_options = tk.Menubutton(self.custom_menu_bar, text="Ayarlar", relief='flat', font=('Segoe UI', menu_font_size), padx=5, pady=2)
        self.menu_buttons['options'] = mb_options; mb_options.pack(side=tk.LEFT, padx=1)
        menu_options = tk.Menu(mb_options, tearoff=0); self.dropdown_menus['options'] = menu_options
        menu_options.add_command(label="Yönetmelik Seçenekleri", command=lambda: print("TODO: Yönetmelik Ayarları"))
        menu_options.add_command(label="Birim Sistemi", command=lambda: print("TODO: Birim Sistemi"))
        menu_options.add_command(label="Genel Program Ayarları", command=lambda: self.show_frame("Settings"))
        mb_options["menu"] = menu_options

        # Yardım Menubutton
        mb_help = tk.Menubutton(self.custom_menu_bar, text="Yardım", relief='flat', font=('Segoe UI', menu_font_size), padx=5, pady=2)
        self.menu_buttons['help'] = mb_help; mb_help.pack(side=tk.LEFT, padx=1)
        menu_help = tk.Menu(mb_help, tearoff=0); self.dropdown_menus['help'] = menu_help
        menu_help.add_command(label="Hakkında", command=lambda: messagebox.showinfo("Hakkında", f"{config.APP_NAME}\nVersiyon {config.APP_VERSION}"))
        menu_help.add_command(label="Kullanım Kılavuzu", command=lambda: print("TODO: Kılavuz"))
        mb_help["menu"] = menu_help

    def _create_main_layout(self):
        """Ana PanedWindow, sidebar ve content frame'i oluşturur."""
        self.pane = tk.PanedWindow(self.root, bd=0, sashwidth=4, sashrelief=tk.FLAT, orient=tk.HORIZONTAL)
        self.pane.pack(fill=tk.BOTH, expand=True)
        self.sidebar_frame = tk.Frame(self.pane, relief='flat', bd=0)
        self.sidebar_frame.pack_propagate(False)
        self.content_frame = tk.Frame(self.pane, relief='flat', bd=0)
        self.pane.add(self.sidebar_frame, stretch="never", width=250)
        self.pane.add(self.content_frame, stretch="always")

    def _create_sidebar_widgets(self):
        """Sol kenar çubuğu widget'larını oluşturur."""
        self.sidebar_frame.grid_columnconfigure(0, weight=1)
        self.app_title_label = ttk.Label(self.sidebar_frame, text="Ana Menü", font=("Segoe UI", 18, "bold"))
        self.app_title_label.grid(row=0, column=0, pady=(15, 20), padx=10, sticky='n')

        dashboard_button = ttk.Button(self.sidebar_frame, text="Panel", style='TButton', command=lambda: self.show_frame("Panel"))
        dashboard_button.grid(row=1, column=0, pady=5, padx=10, sticky='ew')
        autocad_button = ttk.Button(self.sidebar_frame, text="AutoCAD", style='TButton', command=lambda: self.show_frame("AutoCAD"))
        autocad_button.grid(row=2, column=0, pady=5, padx=10, sticky='ew')
        calc_button = ttk.Button(self.sidebar_frame, text="Hesaplamalar", style='TButton', command=lambda: self.show_frame("Calculations"))
        calc_button.grid(row=3, column=0, pady=5, padx=10, sticky='ew')
        self.sidebar_frame.grid_rowconfigure(4, weight=1) # Boşluk
        settings_button = ttk.Button(self.sidebar_frame, text="Ayarlar", style='TButton', command=lambda: self.show_frame("Settings"))
        settings_button.grid(row=5, column=0, pady=(5, 10), padx=10, sticky='sew')

    def apply_theme_and_save(self, theme_name, initial=False):
        """Temayı uygular ve genel ayarları kaydeder."""
        effective_theme_name = theme_name
        if theme_name == "system": effective_theme_name = utils.get_system_theme()
        if effective_theme_name not in config.themes: effective_theme_name = "dark"

        needs_update = (self.current_theme_name != effective_theme_name) or initial
        # Eğer güncelleme gerekmiyorsa ve bu ilk çalıştırma değilse çık
        if not needs_update and not initial:
             print(f"Info: Theme '{effective_theme_name}' is already active.")
             return

        self.current_theme_name = effective_theme_name
        self.current_theme = config.themes[self.current_theme_name]
        print(f"Applying theme: {self.current_theme_name}")
        self.app_settings["theme"] = self.current_theme_name

        # Ana widget'ları güncelle
        self.root.configure(bg=self.current_theme['content_bg'])
        self.custom_menu_bar.configure(bg=self.current_theme['menu_bar_bg'])
        self.pane.configure(bg=self.current_theme['content_bg'])
        self.sidebar_frame.configure(bg=self.current_theme['sidebar_bg'])
        self.content_frame.configure(bg=self.current_theme['content_bg'])

        # --- Stil Ayarları (Dengeli boyutlar) ---
        self.style.configure('TButton', font=('Segoe UI', 15), padding=(10, 10), foreground=self.current_theme['button_fg'], background=self.current_theme['button_bg'], borderwidth=0, relief='flat')
        self.style.map('TButton', foreground=[('active', self.current_theme['button_fg'])], background=[('active', self.current_theme['button_hover_bg'])], relief=[('pressed', 'flat'), ('active', 'flat')])
        self.style.configure('Sub.TButton', font=('Segoe UI', 12), padding=(5, 5), foreground=self.current_theme['text'], background=self.current_theme['sub_sidebar_bg'], borderwidth=0, relief='flat')
        self.style.map('Sub.TButton', foreground=[('active', self.current_theme['button_fg'])], background=[('active', self.current_theme['button_hover_bg'])], relief=[('pressed', 'flat'), ('active', 'flat')])
        self.style.configure('TEntry', font=('Segoe UI', 13), fieldbackground=self.current_theme['entry_bg'], foreground=self.current_theme['entry_fg'], bordercolor=self.current_theme['entry_border'], insertcolor=self.current_theme['entry_insert'], borderwidth=1, relief='flat')
        self.style.map('TEntry', bordercolor=[('focus', self.current_theme['button_bg'])])
        self.style.configure('Header.TLabel', font=('Segoe UI', 14, 'bold'), background=self.current_theme['content_bg'], foreground=self.current_theme['title_text'])
        self.style.configure('TSeparator', background=self.current_theme['separator'])
        self.style.configure('TCombobox', font=('Segoe UI', 13))

        # Statik widget'lar
        self.app_title_label.configure(background=self.current_theme['sidebar_bg'], foreground=self.current_theme['title_text'], font=("Segoe UI", 18, "bold"))

        # Özel Menü Butonları ve Açılır Menüler
        menu_font_size = 11
        for mb in self.menu_buttons.values(): mb.configure(bg=self.current_theme['menu_bar_bg'], fg=self.current_theme['menu_fg'], activebackground=self.current_theme['menu_active_bg'], activeforeground=self.current_theme['menu_active_fg'], font=('Segoe UI', menu_font_size))
        for menu in self.dropdown_menus.values(): menu.configure(bg=self.current_theme['menu_bg'], fg=self.current_theme['menu_fg'], activebackground=self.current_theme['menu_active_bg'], activeforeground=self.current_theme['menu_active_fg'], font=('Segoe UI', menu_font_size))

        utils.save_settings() # Genel ayarları kaydet

        # Mevcut görünümü yenile (eğer varsa ve tema değiştiyse)
        if self.current_frame_widget and needs_update:
             frame_key = getattr(self.current_frame_widget, "_frame_key", None)
             if frame_key: self.show_frame(frame_key) # Frame'i yeniden oluştur

    def update_current_view(self, view_func, *args):
        """Aktif görünüm fonksiyonunu saklar (Frame yeniden oluşturulduğu için gereksiz)."""
        pass

    def show_frame(self, frame_key):
        """İstenen bölüm çerçevesini content_frame içinde gösterir."""
        print(f"Showing frame: {frame_key}")
        if self.current_frame_widget:
            self.current_frame_widget.destroy()
            self.current_frame_widget = None

        frame_class = None
        if frame_key == "Panel": frame_class = PanelFrame
        elif frame_key == "AutoCAD": frame_class = AutoCADFrame
        elif frame_key == "Calculations": frame_class = CalculationsFrame
        elif frame_key == "Settings": frame_class = SettingsFrame

        if frame_class:
            # Sınıfı oluştururken ana uygulama örneğini (self) gönder
            new_frame = frame_class(self.content_frame, self)
            # Frame'e anahtarını ekleyelim ki apply_theme yeniden oluşturabilsin
            setattr(new_frame, "_frame_key", frame_key)
            new_frame.pack(expand=True, fill='both')
            self.current_frame_widget = new_frame
            # current_view_func'ı ayarla (gerçi frame yeniden oluşturuluyor)
            if hasattr(new_frame, 'show_page'): # CalculationsFrame için
                # Varsayılan sayfanın fonksiyonunu sakla (örn: show_page("profiles"))
                # Bu biraz dolaylı, belki daha iyi bir yöntem bulunur.
                pass
            elif hasattr(new_frame, 'show_autocad_home'): # AutoCADFrame için
                 # self.current_view_func = new_frame.show_autocad_home
                 pass
            # Diğer frame'ler için de benzeri yapılabilir veya show_frame'e view_func gönderilebilir.
            # Şimdilik apply_theme'in frame'i yeniden oluşturmasına güveniyoruz.

        else:
            print(f"Error: Unknown frame key '{frame_key}'")

    def show_calculation_page(self, page_key):
        """Hesaplamalar çerçevesini gösterir ve ilgili alt sayfayı açar."""
        if not isinstance(self.current_frame_widget, CalculationsFrame):
            self.show_frame("Calculations"); self.root.update_idletasks()
        if isinstance(self.current_frame_widget, CalculationsFrame):
            self.current_frame_widget.show_page(page_key)
        else: print("Error: Calculations frame not active.")

    def refresh_autocad_status_and_view(self, initial_load=False):
        """AutoCAD durumunu yeniler ve mevcut görünümü günceller (eğer varsa)."""
        print("Refreshing AutoCAD status...")
        self.autocad_status_message = autocad_interface.check_autocad_connection()
        self.connected_autocad_doc_name = autocad_interface.connected_autocad_doc_name # Globalden almayı bırakalım
        # autocad_interface.py içindeki check_autocad_connection'ın
        # bu bilgileri döndürmesi veya bir sınıf özelliği olarak saklaması daha iyi olur.
        # Şimdilik global değişkenlere bağımlı kalıyoruz.

        if not initial_load and self.current_frame_widget:
            frame_key = getattr(self.current_frame_widget, "_frame_key", None)
            if frame_key: print(f"Refreshing view for frame: {frame_key}"); self.show_frame(frame_key)
            else: print("Warning: Cannot refresh view, frame key not found.")
        elif initial_load: print("Initial load, view refresh skipped.")
        else: print("No current view to refresh.")

    def get_autocad_status_message(self):
        """PanelFrame'in kullanması için durum mesajını döndürür."""
        return self.autocad_status_message

    def save_current_profile(self):
        """Aktif hesaplama profilini kaydeder."""
        if isinstance(self.current_frame_widget, CalculationsFrame):
             if hasattr(self.current_frame_widget, 'save_project_info'):
                 self.current_frame_widget.save_project_info() # Proje bilgilerini kaydet
             # TODO: Malzeme ve kesit sayfaları için de kaydetme metotları çağrılabilir
             # elif hasattr(self.current_frame_widget, 'save_material_info'): self.current_frame_widget.save_material_info()
             else: print("Save method not found for current calculation page.")
        else: messagebox.showinfo("Bilgi", "Kaydedilecek aktif bir hesaplama profili sayfası yok.")

    def quit_app(self):
        """Ayarları kaydedip uygulamayı kapatır."""
        print("Saving settings and exiting application...")
        try:
            current_geometry = self.root.winfo_geometry()
            self.app_settings['window_geometry'] = current_geometry
            utils.save_settings()
        except Exception as e: print(f"Error saving settings on closing: {e}")
        finally: self.root.destroy()

