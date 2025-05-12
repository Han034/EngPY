# section_frames.py
# Uygulamanın ana içerik bölümlerini (Frame sınıfları) tanımlar.

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox, simpledialog
import math

# Diğer modüllerimizi import edelim
import config
import ui_components
import utils
import autocad_interface # AutoCAD fonksiyonları için

# pyautocad importunu buraya da ekleyelim (APoint için)
try:
    from pyautocad import Autocad, APoint # APoint eklendi
except ImportError:
    Autocad = None
    APoint = None # APoint None olarak ayarlandı
    # print("Warning: 'pyautocad' library not found.") # Ana app'te zaten uyarılıyor


# ==================================
# PANEL FRAME SINIFI
# ==================================
class PanelFrame(ttk.Frame):
    """Panel/Gösterge Tablosu bölümünü gösteren çerçeve."""
    _frame_key = "Panel" # Yeniden oluşturma için anahtar
    def __init__(self, parent, main_app_instance, *args, **kwargs):
        super().__init__(parent, style='TFrame', *args, **kwargs)
        self.main_app = main_app_instance # Ana uygulama sınıfına erişim için
        self.theme = self.main_app.current_theme
        self._create_widgets()

    def _create_widgets(self):
        # Bu frame'in içeriğini temizle (önceki view'dan kalma olabilir)
        for widget in self.winfo_children():
            widget.destroy()

        label = ui_components.create_content_label(self, "Panel", self.theme) # Font: 18 bold
        label.pack(pady=20, padx=20, anchor='nw')

        dashboard_main_frame = tk.Frame(self, bg=self.theme['content_bg'])
        dashboard_main_frame.pack(pady=10, padx=20, fill='both', expand=True)

        # Text area font boyutu düzeltildi
        text_area = tk.Text(dashboard_main_frame, height=10, width=50, relief='flat', bd=1,
                            font=("Segoe UI", 13), # Font: 13
                            bg=self.theme['text_area_bg'], fg=self.theme['text_area_fg'],
                            insertbackground=self.theme['entry_insert'], highlightthickness=1,
                            highlightbackground=self.theme['text_area_highlight'],
                            highlightcolor=self.theme['button_bg'])
        text_area.pack(side=tk.TOP, fill='both', expand=True)

        text_area.config(state=tk.NORMAL); text_area.delete('1.0', tk.END)
        # Durum mesajını ve yenileme callback'ini main_app'ten al
        text_area.insert(tk.END, f"AutoCAD Durumu: {self.main_app.autocad_status_message}\n\n")
        text_area.insert(tk.END, "Uygulama durumu ve hızlı bilgiler burada gösterilecek...\n")
        text_area.config(state=tk.DISABLED)

        # Yenileme butonu main_app'teki metodu çağıracak
        refresh_button = ui_components.create_content_button(dashboard_main_frame, "Yenile", self.theme,
                                    command=self.main_app.refresh_autocad_status_and_view, style_key='TButton') # Font: 14
        refresh_button.pack(side=tk.BOTTOM, anchor='se', pady=(10, 0))

# ==================================
# AUTOCAD FRAME SINIFI
# ==================================
class AutoCADFrame(ttk.Frame):
    """AutoCAD ile ilgili işlemleri içeren çerçeve."""
    _frame_key = "AutoCAD"
    def __init__(self, parent, main_app_instance, *args, **kwargs):
        super().__init__(parent, style='TFrame', *args, **kwargs)
        self.main_app = main_app_instance
        self.theme = self.main_app.current_theme
        self.sub_sidebar = None
        self.page_container = None # Sayfa içeriği için konteyner
        self.current_page_frame = None
        self.connected_doc_name = self.main_app.connected_autocad_doc_name
        self.selected_area_points = None
        self.shape_buttons_references = {}
        self.osnap_vars = {}
        self._create_widgets()
        self.show_autocad_home()

    def _create_widgets(self):
        """Ana widgetları (alt menü, sayfa konteyneri) oluşturur."""
        self._create_autocad_sub_sidebar()
        self.page_container = tk.Frame(self, bg=self.theme['content_bg'])
        self.page_container.pack(expand=True, fill='both', padx=10, pady=5)

    def _create_autocad_sub_sidebar(self):
        """AutoCAD bölümü için yatay alt menüyü oluşturur."""
        # Eğer zaten varsa tekrar oluşturmaya gerek yok, sadece görünür yap
        if self.sub_sidebar and self.sub_sidebar.winfo_exists():
             self.sub_sidebar.pack(side=tk.TOP, fill=tk.X, pady=(0, 10)) # Tekrar paketle
             return

        if self.sub_sidebar: self.sub_sidebar.destroy() # Varsa yok et (hata önleme)

        self.sub_sidebar = tk.Frame(self, height=60, bg=self.theme['sub_sidebar_bg']) # Yükseklik sabit
        self.sub_sidebar.pack(side=tk.TOP, fill=tk.X, pady=(0, 10)); self.sub_sidebar.pack_propagate(False)

        home_button = ui_components.create_content_button(self.sub_sidebar, "Ana Sayfa", self.theme, command=self.show_autocad_home, style_key='Sub.TButton'); home_button.pack(side=tk.LEFT, padx=10, pady=5) # pady sabit
        test_button = ui_components.create_content_button(self.sub_sidebar, "Test Alanı", self.theme, command=self.show_autocad_test_area, style_key='Sub.TButton'); test_button.pack(side=tk.LEFT, padx=10, pady=5)
        btn1 = ui_components.create_content_button(self.sub_sidebar, "Çizim Temizle", self.theme, style_key='Sub.TButton', command=lambda: print("TODO: Purge")); btn1.pack(side=tk.LEFT, padx=10, pady=5)
        btn2 = ui_components.create_content_button(self.sub_sidebar, "Layer Yönetimi", self.theme, style_key='Sub.TButton', command=lambda: print("TODO: Layer")); btn2.pack(side=tk.LEFT, padx=10, pady=5)
        btn3 = ui_components.create_content_button(self.sub_sidebar, "Blok İşlemleri", self.theme, style_key='Sub.TButton', command=lambda: print("TODO: Block")); btn3.pack(side=tk.LEFT, padx=10, pady=5)

    def _clear_page_container(self):
        """Sayfa konteynerini temizler ve yeniden oluşturur."""
        if self.current_page_frame: self.current_page_frame.destroy()
        # page_container'ı da temizleyip yeniden oluşturmak daha garanti olabilir
        if self.page_container and self.page_container.winfo_exists():
             self.page_container.destroy()
        self.page_container = tk.Frame(self, bg=self.theme['content_bg'])
        self.page_container.pack(expand=True, fill='both', padx=10, pady=5)
        # Yeni sayfa için boş bir çerçeve oluşturalım
        self.current_page_frame = tk.Frame(self.page_container, bg=self.theme['content_bg'])
        self.current_page_frame.pack(expand=True, fill='both')


    def show_autocad_home(self):
        """AutoCAD ana sayfasını/ayar sayfasını gösterir."""
        self.main_app.update_current_view(self.show_autocad_home)
        self._clear_page_container() # Sadece sayfa içeriğini temizle

        # Bağlantı durumunu ana app'ten al
        self.connected_doc_name = self.main_app.connected_autocad_doc_name
        is_connected = (self.connected_doc_name is not None)
        control_state = tk.NORMAL if is_connected else tk.DISABLED

        # Ayarlar için çerçeve (current_page_frame içine)
        settings_area_frame = tk.Frame(self.current_page_frame, bg=self.theme['content_bg'])
        settings_area_frame.pack(pady=15, padx=15, fill='x', anchor='nw')

        # Header fontu stilden gelecek (Header.TLabel -> 14 bold)
        settings_header_label = ttk.Label(settings_area_frame, text="Çalışma Alanı Ayarları", style='Header.TLabel')
        settings_header_label.pack(anchor='w', pady=(0, 5))
        separator = ttk.Separator(settings_area_frame, orient='horizontal'); separator.pack(fill='x', anchor='w', pady=(0, 15))

        grid_frame = tk.Frame(settings_area_frame, bg=self.theme['content_bg']); grid_frame.pack(anchor='w', pady=5)
        grid_label = ttk.Label(grid_frame, text="Görünüm:", style='Header.TLabel'); grid_label.pack(side=tk.LEFT, padx=(0, 10))
        grid_var = tk.IntVar(); saved_grid_mode = 0 # TODO: Profilden oku
        grid_var.set(saved_grid_mode)
        grid_check_frame = ui_components.create_custom_checkbutton(grid_frame, "Izgara Modu (GRIDMODE)", grid_var, self.theme, command=lambda v=grid_var: self._toggle_grid_mode(v), state=control_state); grid_check_frame.pack(side=tk.LEFT, pady=3)

        osnap_frame = tk.Frame(settings_area_frame, bg=self.theme['content_bg']); osnap_frame.pack(anchor='w', pady=10)
        osnap_label = ttk.Label(osnap_frame, text="Nesne Kenetleme (OSMODE):", style='Header.TLabel'); osnap_label.pack(anchor='w')
        osnap_options_frame = tk.Frame(osnap_frame, bg=self.theme['content_bg']); osnap_options_frame.pack(anchor='w', padx=20, pady=(5,0))
        self.osnap_vars = {}; osnap_modes = {"Endpoint": 1, "Midpoint": 2, "Center": 4, "Node": 8, "Intersection": 32}
        saved_osmode = 0 # TODO: Profilden oku
        for name, bit_value in osnap_modes.items():
            var = tk.IntVar();
            if saved_osmode & bit_value: var.set(1)
            else: var.set(0)
            chk_frame = ui_components.create_custom_checkbutton(osnap_options_frame, name, var, self.theme, command=self._update_osmode, state=control_state); chk_frame.pack(side=tk.LEFT, padx=5, pady=3)
            self.osnap_vars[bit_value] = var

        all_check_frames = [];
        if grid_frame: all_check_frames.extend(w for w in grid_frame.winfo_children() if isinstance(w, tk.Frame))
        if osnap_options_frame: all_check_frames.extend(w for w in osnap_options_frame.winfo_children() if isinstance(w, tk.Frame))
        if is_connected:
            current_gridmode = autocad_interface.get_autocad_variable("GRIDMODE", saved_grid_mode); grid_var.set(current_gridmode)
            current_osmode = autocad_interface.get_autocad_variable("OSMODE", saved_osmode)
            for bit_value, var in self.osnap_vars.items(): var.set(1) if current_osmode & bit_value else var.set(0)
            for frame in all_check_frames:
                 if hasattr(frame, "update_visual_func"): frame.update_visual_func()

        # Bağlı dosya adı (sayfa içeriğinin altına)
        if self.connected_doc_name: file_text = f"Bağlı Dosya: {self.connected_doc_name}"
        else: file_text = "Bağlı Dosya: Yok"
        doc_name_label = ui_components.create_content_text(self.current_page_frame, file_text, self.theme, size=11); # Boyut 11
        doc_name_label.pack(side=tk.BOTTOM, anchor='se', padx=10, pady=5)

    def _toggle_grid_mode(self, variable):
        autocad_interface.set_autocad_variable("GRIDMODE", variable.get())
    def _update_osmode(self):
        new_osmode_value = 0
        for bit_value, var in self.osnap_vars.items():
            if var.get() == 1: new_osmode_value |= bit_value
        autocad_interface.set_autocad_variable("OSMODE", new_osmode_value)

    def _select_area_in_autocad(self, result_text_widget): # shape_buttons kaldırıldı
        """Kullanıcıdan AutoCAD'de 4 nokta seçmesini ister."""
        self.selected_area_points = None
        result_text_widget.config(state=tk.NORMAL); result_text_widget.delete('1.0', tk.END)
        acad = autocad_interface.get_acad_instance()
        if not acad: result_text_widget.insert(tk.END, "Hata: AutoCAD bağlantısı kurulamadı."); result_text_widget.config(state=tk.DISABLED); return
        result_text_widget.insert(tk.END, "AutoCAD ekranına geçin ve 4 nokta seçin...\n(Arayüz bu sırada donabilir)\n"); self.main_app.root.update_idletasks()
        points = []; button_state = tk.DISABLED
        try:
            p1 = autocad_interface.get_point_from_user("Lütfen 1. noktayı seçin (İptal için Esc):")
            if p1 is None: raise Exception("Kullanıcı iptal etti.")
            p2 = autocad_interface.get_point_from_user("Lütfen 2. noktayı seçin:")
            if p2 is None: raise Exception("Kullanıcı iptal etti.")
            p3 = autocad_interface.get_point_from_user("Lütfen 3. noktayı seçin:")
            if p3 is None: raise Exception("Kullanıcı iptal etti.")
            p4 = autocad_interface.get_point_from_user("Lütfen 4. noktayı seçin:")
            if p4 is None: raise Exception("Kullanıcı iptal etti.")
            points = [p1, p2, p3, p4]; self.selected_area_points = points
            result_text_widget.insert(tk.END, "Seçilen Noktalar:\n")
            for i, p in enumerate(points): result_text_widget.insert(tk.END, f"{i+1}. Nokta: {p}\n")
            result_text_widget.insert(tk.END, "\nAlan başarıyla seçildi. Şimdi şekil çizebilirsiniz."); button_state = tk.NORMAL
        except Exception as e: print(f"Nokta seçimi hatası/iptali: {e}"); result_text_widget.insert(tk.END, f"\nHata veya İptal: Nokta seçimi tamamlanamadı.\n{e}"); self.selected_area_points = None; button_state = tk.DISABLED
        finally:
            autocad_interface.prompt_user("\n")
            result_text_widget.config(state=tk.DISABLED)
            # self.shape_buttons_references kullanılarak buton durumu güncellenir
            for btn in self.shape_buttons_references.values():
                 if btn: btn.configure(state=button_state)
            utils.bring_window_to_front()

    def _draw_shape_in_area(self, shape_type, result_text_widget):
        """Seçilen alana belirtilen şekli çizer."""
        result_text_widget.config(state=tk.NORMAL); result_text_widget.delete('1.0', tk.END)
        if not self.selected_area_points or len(self.selected_area_points) != 4: result_text_widget.insert(tk.END, "Hata: Önce 'Alan Seç' ile 4 nokta belirlemelisiniz."); result_text_widget.config(state=tk.DISABLED); return
        acad = autocad_interface.get_acad_instance()
        if not acad: result_text_widget.insert(tk.END, "Hata: AutoCAD bağlantısı kurulamadı."); result_text_widget.config(state=tk.DISABLED); return
        if not APoint: result_text_widget.insert(tk.END, "Hata: APoint pyautocad'den import edilemedi."); result_text_widget.config(state=tk.DISABLED); return
        try:
            xs = [p[0] for p in self.selected_area_points]; ys = [p[1] for p in self.selected_area_points]
            min_x, max_x = min(xs), max(xs); min_y, max_y = min(ys), max(ys)
            center_x = (min_x + max_x) / 2; center_y = (min_y + max_y) / 2
            width = max_x - min_x; height = max_y - min_y
            size = min(width, height) * 0.8
            if size <= 0: result_text_widget.insert(tk.END, "Hata: Geçersiz alan boyutu."); result_text_widget.config(state=tk.DISABLED); return
            radius = size / 2.0
            result_text_widget.insert(tk.END, f"'{shape_type}' çiziliyor...\nMerkez: ({center_x:.2f}, {center_y:.2f}), Boyut: {size:.2f}\n"); self.main_app.root.update_idletasks()

            success = False
            if shape_type == 'kare':
                half_size = size / 2.0; p1 = APoint(center_x - half_size, center_y - half_size); p2 = APoint(center_x + half_size, center_y - half_size); p3 = APoint(center_x + half_size, center_y + half_size); p4 = APoint(center_x - half_size, center_y + half_size)
                success = autocad_interface.draw_line(p1, p2) and autocad_interface.draw_line(p2, p3) and autocad_interface.draw_line(p3, p4) and autocad_interface.draw_line(p4, p1)
            elif shape_type == 'daire':
                success = autocad_interface.draw_circle(APoint(center_x, center_y), radius)
            elif shape_type == 'üçgen':
                p1 = APoint(center_x, center_y + radius); p2 = APoint(center_x - radius * math.sqrt(3)/2, center_y - radius/2); p3 = APoint(center_x + radius * math.sqrt(3)/2, center_y - radius/2)
                success = autocad_interface.draw_line(p1, p2) and autocad_interface.draw_line(p2, p3) and autocad_interface.draw_line(p3, p1)

            if success: result_text_widget.insert(tk.END, f"'{shape_type}' başarıyla çizildi.")
            else: result_text_widget.insert(tk.END, f"\nHata: '{shape_type}' çizilemedi (bkz. log).")
        except Exception as e: print(f"Şekil çizme hatası: {e}"); result_text_widget.insert(tk.END, f"\nHata: Şekil çizilemedi.\n{e}")
        finally: result_text_widget.config(state=tk.DISABLED); utils.bring_window_to_front()

    def show_autocad_test_area(self):
        self.main_app.update_current_view(self.show_autocad_test_area)
        self._clear_page_container()
        # self._create_autocad_sub_sidebar() # Zaten var

        is_connected = (self.connected_doc_name is not None); control_state = tk.NORMAL if is_connected else tk.DISABLED
        shape_button_state = tk.NORMAL if self.selected_area_points else tk.DISABLED

        test_main_frame = tk.Frame(self.current_page_frame, bg=self.theme['content_bg']);
        test_main_frame.pack(pady=15, padx=15, fill='both', expand=True, anchor='nw')

        label = ui_components.create_content_label(test_main_frame, "AutoCAD Test Alanı", self.theme); label.pack(pady=10, padx=0, anchor='nw')
        button_area_frame = tk.Frame(test_main_frame, bg=self.theme['content_bg']); button_area_frame.pack(pady=5, anchor='w')
        # Text area font boyutu düzeltildi
        result_text = tk.Text(test_main_frame, height=10, width=50, relief='flat', bd=1, font=("Segoe UI", 12), bg=self.theme['text_area_bg'], fg=self.theme['text_area_fg'], insertbackground=self.theme['entry_insert'], highlightthickness=1, highlightbackground=self.theme['text_area_highlight'], highlightcolor=self.theme['button_bg'], state=tk.DISABLED); result_text.pack(side=tk.TOP, fill='both', expand=True, pady=(10, 10)) # Font: 12
        self.shape_buttons_references = {}
        # Command düzeltildi: shape_buttons argümanı kaldırıldı
        select_button = ttk.Button(button_area_frame, text="Alan Seç (4 Nokta)", style='TButton', command=lambda rt=result_text: self._select_area_in_autocad(rt), state=control_state); select_button.pack(side=tk.LEFT, anchor='w', padx=(0,10))
        square_button = ttk.Button(button_area_frame, text="Kare", style='TButton', command=lambda rt=result_text: self._draw_shape_in_area('kare', rt), state=shape_button_state); square_button.pack(side=tk.LEFT, anchor='w', padx=5); self.shape_buttons_references['kare'] = square_button
        triangle_button = ttk.Button(button_area_frame, text="Üçgen", style='TButton', command=lambda rt=result_text: self._draw_shape_in_area('üçgen', rt), state=shape_button_state); triangle_button.pack(side=tk.LEFT, anchor='w', padx=5); self.shape_buttons_references['üçgen'] = triangle_button
        circle_button = ttk.Button(button_area_frame, text="Daire", style='TButton', command=lambda rt=result_text: self._draw_shape_in_area('daire', rt), state=shape_button_state); circle_button.pack(side=tk.LEFT, anchor='w', padx=5); self.shape_buttons_references['daire'] = circle_button

        if self.connected_doc_name: file_text = f"Bağlı Dosya: {self.connected_doc_name}"
        else: file_text = "Bağlı Dosya: Yok"
        doc_name_label = ui_components.create_content_text(test_main_frame, file_text, self.theme, size=11); # Font: 11
        doc_name_label.pack(side=tk.BOTTOM, anchor='se', padx=10, pady=5)


# ==================================
# CALCULATIONS FRAME SINIFI
# ==================================
class CalculationsFrame(ttk.Frame):
    """Hesaplamalar bölümünü ve alt sayfalarını yöneten çerçeve."""
    _frame_key = "Calculations"
    def __init__(self, parent, main_app_instance, *args, **kwargs):
        super().__init__(parent, style='TFrame', *args, **kwargs)
        self.main_app = main_app_instance
        self.theme = self.main_app.current_theme
        self.profiles_data = self.main_app.profiles_data
        self.current_profile_name = self.main_app.current_profile_name
        self.sub_sidebar = None
        self.page_container = None
        self.current_page_frame = None
        self.project_info_vars = {}
        self.material_detail_vars = {}
        self.material_listbox_ref = None
        self.material_detail_widgets = {}
        self.profile_listbox_ref = None
        self.section_detail_vars = {}
        self.section_listbox_ref = None
        self.section_detail_widgets = {}
        self._create_widgets()
        self.show_page("profiles")

        # --- YENİ: Kesitler için değişkenler ---
        self.section_detail_vars = {} # Formdaki Tkinter değişkenlerini tutacak
        self.section_listbox_ref = None # Listbox widget'ına referans
        self.section_detail_widgets = {} # Formdaki widget'lara referans (show/hide için)
        # --- Bitti: Kesitler için değişkenler ---

        # --- YENİ: Tekil Eleman Tasarımı için değişkenler ---
        self.element_design_vars = {} # Formdaki Tkinter değişkenleri
        self.element_design_widgets = {} # Form widget referansları (Combobox vb.)
        # --- Bitti: Tekil Eleman Tasarımı için değişkenler ---

    def _create_widgets(self):
        self.sub_sidebar = self._create_calculations_sub_sidebar(self)
        self.page_container = tk.Frame(self, bg=self.theme['content_bg'])
        self.page_container.pack(expand=True, fill='both', padx=10, pady=5)

    def _create_calculations_sub_sidebar(self, parent_frame):
        sub_sidebar = tk.Frame(parent_frame, height=60, bg=self.theme['sub_sidebar_bg'])
        sub_sidebar.pack(side=tk.TOP, fill=tk.X, pady=(0, 10)); sub_sidebar.pack_propagate(False)
        btn_profile = ui_components.create_content_button(sub_sidebar, "Profiller", self.theme, command=lambda: self.show_page("profiles"), style_key='Sub.TButton'); btn_profile.pack(side=tk.LEFT, padx=10, pady=5)
        btn_proj = ui_components.create_content_button(sub_sidebar, "Proje Bilgileri", self.theme, command=lambda: self.show_page("project_info"), style_key='Sub.TButton'); btn_proj.pack(side=tk.LEFT, padx=10, pady=5)
        btn_mat = ui_components.create_content_button(sub_sidebar, "Malzemeler", self.theme, command=lambda: self.show_page("materials"), style_key='Sub.TButton'); btn_mat.pack(side=tk.LEFT, padx=10, pady=5)
        btn_sec = ui_components.create_content_button(sub_sidebar, "Kesitler", self.theme, command=lambda: self.show_page("sections"), style_key='Sub.TButton'); btn_sec.pack(side=tk.LEFT, padx=10, pady=5)
        btn_elem = ui_components.create_content_button(sub_sidebar, "Tekil Eleman", self.theme, command=lambda: self.show_page("element_design"), style_key='Sub.TButton'); btn_elem.pack(side=tk.LEFT, padx=10, pady=5)
        btn_seismic = ui_components.create_content_button(sub_sidebar, "Deprem Yükü", self.theme, command=lambda: self.show_page("seismic_load"), style_key='Sub.TButton'); btn_seismic.pack(side=tk.LEFT, padx=10, pady=5)
        btn_report = ui_components.create_content_button(sub_sidebar, "Raporlama", self.theme, command=lambda: self.show_page("reporting"), style_key='Sub.TButton'); btn_report.pack(side=tk.LEFT, padx=10, pady=5)
        return sub_sidebar

    def show_page(self, page_key):
        self.main_app.update_current_view(self.show_page, page_key)
        if self.current_page_frame: self.current_page_frame.destroy()
        # page_container'ın var olduğundan emin ol
        if not self.page_container or not self.page_container.winfo_exists():
             self.page_container = tk.Frame(self, bg=self.theme['content_bg'])
             self.page_container.pack(expand=True, fill='both', padx=10, pady=5)

        self.current_page_frame = tk.Frame(self.page_container, bg=self.theme['content_bg'])
        self.current_page_frame.pack(expand=True, fill='both')

        if page_key == "project_info": self.populate_project_info_page(self.current_page_frame)
        elif page_key == "materials": self.populate_material_page(self.current_page_frame)
        elif page_key == "sections": self.populate_section_page(self.current_page_frame)
        elif page_key == "element_design": self.populate_element_design_page(self.current_page_frame)
        elif page_key == "seismic_load": self.populate_seismic_load_page(self.current_page_frame)
        elif page_key == "reporting": self.populate_reporting_page(self.current_page_frame)
        elif page_key == "profiles": self.populate_profiles_page(self.current_page_frame)
        else: ttk.Label(self.current_page_frame, text=f"Bilinmeyen sayfa: {page_key}").pack()

    # --- Sayfa İçeriklerini Oluşturan Metotlar ---
    def populate_project_info_page(self, parent_frame):
        self.project_info_vars = { "name": tk.StringVar(), "desc": tk.StringVar(), "engineer": tk.StringVar(), "concrete_reg": tk.StringVar(), "seismic_reg": tk.StringVar(), "load_reg": tk.StringVar(), "units": tk.StringVar() }
        parent_frame.columnconfigure(1, weight=1)
        ttk.Label(parent_frame, text="Proje Adı:", style='Header.TLabel').grid(row=0, column=0, padx=10, pady=8, sticky='w')
        ui_components.create_content_entry(parent_frame, current_theme=self.theme, textvariable=self.project_info_vars["name"]).grid(row=0, column=1, padx=10, pady=8, sticky='ew')
        ttk.Label(parent_frame, text="Açıklama:", style='Header.TLabel').grid(row=1, column=0, padx=10, pady=8, sticky='nw')
        desc_text = tk.Text(parent_frame, height=4, width=40, font=("Segoe UI", 13), relief='flat', bd=1, bg=self.theme['text_area_bg'], fg=self.theme['text_area_fg'], insertbackground=self.theme['entry_insert'], highlightthickness=1, highlightbackground=self.theme['entry_border'], highlightcolor=self.theme['button_bg'])
        desc_text.grid(row=1, column=1, padx=10, pady=8, sticky='nsew'); parent_frame.rowconfigure(1, weight=1)
        self.project_info_vars["desc_widget"] = desc_text
        ttk.Label(parent_frame, text="Mühendis/Firma:", style='Header.TLabel').grid(row=2, column=0, padx=10, pady=8, sticky='w')
        ui_components.create_content_entry(parent_frame, current_theme=self.theme, textvariable=self.project_info_vars["engineer"]).grid(row=2, column=1, padx=10, pady=8, sticky='ew')
        ttk.Label(parent_frame, text="Betonarme Yön.:", style='Header.TLabel').grid(row=3, column=0, padx=10, pady=8, sticky='w')
        combo_concrete = ui_components.create_content_combobox(parent_frame, ["TS 500 (2000)"], current_theme=self.theme, textvariable=self.project_info_vars["concrete_reg"]);
        if combo_concrete['values']: combo_concrete.current(0); combo_concrete.grid(row=3, column=1, padx=10, pady=8, sticky='ew')
        ttk.Label(parent_frame, text="Deprem Yön.:", style='Header.TLabel').grid(row=4, column=0, padx=10, pady=8, sticky='w')
        combo_seismic = ui_components.create_content_combobox(parent_frame, ["TBDY 2018"], current_theme=self.theme, textvariable=self.project_info_vars["seismic_reg"]);
        if combo_seismic['values']: combo_seismic.current(0); combo_seismic.grid(row=4, column=1, padx=10, pady=8, sticky='ew')
        ttk.Label(parent_frame, text="Yük Yön.:", style='Header.TLabel').grid(row=5, column=0, padx=10, pady=8, sticky='w')
        combo_load = ui_components.create_content_combobox(parent_frame, ["TS 498 (1997)"], current_theme=self.theme, textvariable=self.project_info_vars["load_reg"]);
        if combo_load['values']: combo_load.current(0); combo_load.grid(row=5, column=1, padx=10, pady=8, sticky='ew')
        ttk.Label(parent_frame, text="Birim Sistemi:", style='Header.TLabel').grid(row=6, column=0, padx=10, pady=8, sticky='w')
        combo_unit = ui_components.create_content_combobox(parent_frame, ["Metrik (kN, m, C)"], current_theme=self.theme, textvariable=self.project_info_vars["units"]);
        if combo_unit['values']: combo_unit.current(0); combo_unit.grid(row=6, column=1, padx=10, pady=8, sticky='ew')
        save_button = ttk.Button(parent_frame, text="Profili Kaydet", command=self.save_project_info, style='TButton')
        save_button.grid(row=7, column=1, padx=10, pady=20, sticky='e')
        self.load_project_info()

    def populate_material_page(self, parent_frame):
        self.material_detail_vars = { "user_name": tk.StringVar(), "type": tk.StringVar(value="Beton"), "class": tk.StringVar(), "is_custom": tk.IntVar(value=0), "fck": tk.DoubleVar(), "fyk": tk.DoubleVar(), "Ec": tk.DoubleVar(), "Es": tk.DoubleVar() }
        self.material_detail_widgets = {}
        mat_pane = tk.PanedWindow(parent_frame, bd=0, sashwidth=4, sashrelief=tk.FLAT, orient=tk.HORIZONTAL, bg=self.theme['content_bg'])
        mat_pane.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        list_frame = tk.Frame(mat_pane, bg=self.theme['content_bg']); mat_pane.add(list_frame, width=250, stretch="never")
        ttk.Label(list_frame, text="Tanımlı Malzemeler:", style='Header.TLabel').pack(anchor='w', padx=5, pady=(0,5))
        listbox = tk.Listbox(list_frame, height=15, font=("Segoe UI", 13), relief='flat', bd=1, bg=self.theme['listbox_bg'], fg=self.theme['listbox_fg'], selectbackground=self.theme['listbox_select_bg'], selectforeground=self.theme['title_text'], highlightthickness=1, highlightbackground=self.theme['entry_border'], exportselection=False)
        listbox.pack(fill=tk.BOTH, expand=True, padx=5); self.material_listbox_ref = listbox
        listbox.bind('<<ListboxSelect>>', lambda e: self.load_selected_material_to_form())
        button_frame = tk.Frame(list_frame, bg=self.theme['content_bg']); button_frame.pack(fill=tk.X, pady=5, padx=5)
        ttk.Button(button_frame, text="Yeni", style='TButton', width=6, command=self.clear_material_form).pack(side=tk.LEFT, padx=2); ttk.Button(button_frame, text="Düzenle", style='TButton', width=6, command=self.load_selected_material_to_form).pack(side=tk.LEFT, padx=2); ttk.Button(button_frame, text="Sil", style='TButton', width=6, command=self.delete_selected_material).pack(side=tk.LEFT, padx=2)
        detail_frame = tk.Frame(mat_pane, bg=self.theme['content_bg']); mat_pane.add(detail_frame, stretch="always")
        ttk.Label(detail_frame, text="Malzeme Detayları:", style='Header.TLabel').grid(row=0, column=0, columnspan=3, sticky='w', padx=10, pady=(0,10))
        detail_form_frame = tk.Frame(detail_frame, bg=self.theme['content_bg']); detail_form_frame.grid(row=1, column=0, sticky='nsew', padx=10); detail_frame.rowconfigure(1, weight=1); detail_frame.columnconfigure(0, weight=1); detail_form_frame.columnconfigure(1, weight=1)
        ttk.Label(detail_form_frame, text="Malzeme Adı:", style='Header.TLabel').grid(row=0, column=0, sticky='w', padx=5, pady=5)
        entry_name = ui_components.create_content_entry(detail_form_frame, current_theme=self.theme, textvariable=self.material_detail_vars["user_name"]); entry_name.grid(row=0, column=1, columnspan=2, sticky='ew', padx=5, pady=5); self.material_detail_widgets["entry_name"] = entry_name
        ttk.Label(detail_form_frame, text="Malzeme Tipi:", style='Header.TLabel').grid(row=1, column=0, sticky='w', padx=5, pady=5)
        combo_type = ui_components.create_content_combobox(detail_form_frame, ["Beton", "Donatı Çeliği"], current_theme=self.theme, textvariable=self.material_detail_vars["type"]); combo_type.bind("<<ComboboxSelected>>", lambda e: self.on_material_type_change()); combo_type.grid(row=1, column=1, columnspan=2, sticky='ew', padx=5, pady=5); self.material_detail_widgets["combo_type"] = combo_type
        lbl_concrete_class = ttk.Label(detail_form_frame, text="Beton Sınıfı:", style='Header.TLabel'); lbl_concrete_class.grid(row=2, column=0, sticky='w', padx=5, pady=5); self.material_detail_widgets["lbl_concrete_class"] = lbl_concrete_class
        combo_concrete_class = ui_components.create_content_combobox(detail_form_frame, list(config.CONCRETE_PROPS.keys()), current_theme=self.theme, textvariable=self.material_detail_vars["class"]); combo_concrete_class.bind("<<ComboboxSelected>>", lambda e: self.on_material_class_change()); combo_concrete_class.grid(row=2, column=1, sticky='ew', padx=5, pady=5); self.material_detail_widgets["combo_concrete_class"] = combo_concrete_class
        chk_custom_concrete = ui_components.create_custom_checkbutton(detail_form_frame, "Özel", self.material_detail_vars["is_custom"], self.theme, command=self.on_custom_material_toggle); chk_custom_concrete.grid(row=2, column=2, sticky='w', padx=5, pady=5); self.material_detail_widgets["chk_custom_concrete"] = chk_custom_concrete
        lbl_fck = ttk.Label(detail_form_frame, text="fck (MPa):", style='Header.TLabel'); lbl_fck.grid(row=3, column=0, sticky='w', padx=5, pady=5); self.material_detail_widgets["lbl_fck"] = lbl_fck
        entry_fck = ui_components.create_content_entry(detail_form_frame, current_theme=self.theme, textvariable=self.material_detail_vars["fck"], width=10); entry_fck.grid(row=3, column=1, sticky='w', padx=5, pady=5); self.material_detail_widgets["entry_fck"] = entry_fck
        lbl_rebar_class = ttk.Label(detail_form_frame, text="Donatı Sınıfı:", style='Header.TLabel'); self.material_detail_widgets["lbl_rebar_class"] = lbl_rebar_class; lbl_rebar_class.grid(row=2, column=0, sticky='w', padx=5, pady=5)
        combo_rebar_class = ui_components.create_content_combobox(detail_form_frame, list(config.REBAR_PROPS.keys()), current_theme=self.theme, textvariable=self.material_detail_vars["class"]); self.material_detail_widgets["combo_rebar_class"] = combo_rebar_class; combo_rebar_class.bind("<<ComboboxSelected>>", lambda e: self.on_material_class_change()); combo_rebar_class.grid(row=2, column=1, sticky='ew', padx=5, pady=5)
        chk_custom_rebar = ui_components.create_custom_checkbutton(detail_form_frame, "Özel", self.material_detail_vars["is_custom"], self.theme, command=self.on_custom_material_toggle); self.material_detail_widgets["chk_custom_rebar"] = chk_custom_rebar; chk_custom_rebar.grid(row=2, column=2, sticky='w', padx=5, pady=5)
        lbl_fyk = ttk.Label(detail_form_frame, text="fyk (MPa):", style='Header.TLabel'); self.material_detail_widgets["lbl_fyk"] = lbl_fyk; lbl_fyk.grid(row=3, column=0, sticky='w', padx=5, pady=5)
        entry_fyk = ui_components.create_content_entry(detail_form_frame, current_theme=self.theme, textvariable=self.material_detail_vars["fyk"], width=10); self.material_detail_widgets["entry_fyk"] = entry_fyk; entry_fyk.grid(row=3, column=1, sticky='w', padx=5, pady=5)
        lbl_Es = ttk.Label(detail_form_frame, text="Es (MPa):", style='Header.TLabel'); self.material_detail_widgets["lbl_Es"] = lbl_Es; lbl_Es.grid(row=4, column=0, sticky='w', padx=5, pady=5)
        entry_Es = ui_components.create_content_entry(detail_form_frame, current_theme=self.theme, textvariable=self.material_detail_vars["Es"], width=15); self.material_detail_widgets["entry_Es"] = entry_Es; entry_Es.grid(row=4, column=1, sticky='w', padx=5, pady=5)
        form_button_frame = tk.Frame(detail_frame, bg=self.theme['content_bg']); form_button_frame.grid(row=5, column=0, columnspan=3, sticky='se', pady=10)
        ttk.Button(form_button_frame, text="Vazgeç", style='TButton', command=self.clear_material_form).pack(side=tk.RIGHT, padx=5); ttk.Button(form_button_frame, text="Kaydet", style='TButton', command=self.save_material_from_form).pack(side=tk.RIGHT, padx=5)
        self.clear_material_form(); self.update_material_listbox(); self.on_material_type_change()

    def populate_section_page(self, parent_frame): ttk.Label(parent_frame, text="Kesit Kütüphanesi (Geliştirilecek)", style='Header.TLabel').pack(padx=10, pady=10)
    def populate_element_design_page(self, parent_frame): ttk.Label(parent_frame, text="Tekil Eleman Tasarımı (Geliştirilecek)", style='Header.TLabel').pack(padx=10, pady=10)
    def populate_seismic_load_page(self, parent_frame): ttk.Label(parent_frame, text="Deprem Yükü Hesaplama (TBDY 2018) (Geliştirilecek)", style='Header.TLabel').pack(padx=10, pady=10)
    def populate_reporting_page(self, parent_frame): ttk.Label(parent_frame, text="Raporlama Seçenekleri:", style='Header.TLabel').pack(padx=10, pady=10, anchor='w')
    def populate_profiles_page(self, parent_frame):
        self.profile_listbox_ref = None
        parent_frame.columnconfigure(0, weight=1); parent_frame.rowconfigure(1, weight=1)
        ttk.Label(parent_frame, text="Hesaplama Profilleri", style='Header.TLabel').grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky='w')
        listbox = tk.Listbox(parent_frame, font=("Segoe UI", 13), relief='flat', bd=1, bg=self.theme['listbox_bg'], fg=self.theme['listbox_fg'], selectbackground=self.theme['listbox_select_bg'], selectforeground=self.theme['title_text'], highlightthickness=1, highlightbackground=self.theme['entry_border'], exportselection=False)
        listbox.grid(row=1, column=0, padx=(10,0), pady=5, sticky='nsew'); self.profile_listbox_ref = listbox
        scrollbar = ttk.Scrollbar(parent_frame, orient='vertical', command=listbox.yview); scrollbar.grid(row=1, column=1, padx=(0,10), pady=5, sticky='ns'); listbox['yscrollcommand'] = scrollbar.set
        button_frame = tk.Frame(parent_frame, bg=self.theme['content_bg']); button_frame.grid(row=2, column=0, columnspan=2, pady=10, sticky='ew')
        load_button = ttk.Button(button_frame, text="Seçili Profili Yükle", style='TButton', command=self.load_selected_profile); load_button.pack(side=tk.LEFT, padx=5)
        new_button = ttk.Button(button_frame, text="Yeni Profil", style='TButton', command=self.create_new_profile); new_button.pack(side=tk.LEFT, padx=5)
        rename_button = ttk.Button(button_frame, text="Yeniden Adlandır", style='TButton', command=self.rename_selected_profile); rename_button.pack(side=tk.LEFT, padx=5)
        delete_button = ttk.Button(button_frame, text="Sil", style='TButton', command=self.delete_selected_profile); delete_button.pack(side=tk.LEFT, padx=5)
        self.update_profile_listbox()


    # --- Tekil Eleman Tasarımı Yardımcı Metotları ---

    def _get_profile_data(self, data_key):
        """Aktif profilden belirli bir veri listesini (materials/sections) alır."""
        if not self.main_app.current_profile_name:
            return []
        profile = self.main_app.profiles_data.get(self.main_app.current_profile_name, {})
        return profile.get(data_key, [])

    def _find_item_by_name(self, item_list, name):
        """Verilen listede 'user_name' ile eşleşen ilk öğeyi bulur."""
        for item in item_list:
            if item.get("user_name") == name:
                return item
        return None

    def _update_element_design_comboboxes(self):
        """Tekil Eleman Tasarımı sayfası için kesit ve donatı combobox'larını doldurur."""
        if not self.element_design_widgets: return # Widget'lar yoksa çık

        sections = self._get_profile_data("sections")
        materials = self._get_profile_data("materials")

        # Kesit Combobox (Sadece Dikdörtgen)
        rect_sections = sorted(
            [s for s in sections if s.get("type") == "Dikdörtgen"],
            key=lambda x: x.get("user_name", "").lower()
        )
        section_display_names = []
        for s in rect_sections:
            dims = s.get("dimensions", {})
            b = dims.get('b', 0); h = dims.get('h', 0)
            section_display_names.append(f"{s.get('user_name')} (b/h={b:.0f}/{h:.0f})")

        combo_section = self.element_design_widgets.get("combo_section")
        if combo_section:
            combo_section['values'] = section_display_names
            if not section_display_names:
                 combo_section.set("Tanımlı Dikdörtgen Kesit Yok")
                 combo_section.config(state=tk.DISABLED)
            else:
                 combo_section.config(state='readonly')
                 # Mevcut değeri koru veya ilkini seç (şimdilik boş bırakabiliriz)
                 # combo_section.current(0) # Veya mevcut seçimi korumaya çalış

        # Donatı Malzemesi Combobox
        rebar_materials = sorted(
            [m for m in materials if m.get("type") == "Donatı Çeliği"],
             key=lambda x: x.get("user_name", "").lower()
        )
        rebar_names = [m.get("user_name", "İsimsiz") for m in rebar_materials]

        combo_rebar = self.element_design_widgets.get("combo_rebar")
        if combo_rebar:
             combo_rebar['values'] = rebar_names
             if not rebar_names:
                 combo_rebar.set("Tanımlı Donatı Malzemesi Yok")
                 combo_rebar.config(state=tk.DISABLED)
             else:
                 combo_rebar.config(state='readonly')
                 # Mevcut değeri koru veya ilkini seç
                 # combo_rebar.current(0) # Veya mevcut seçimi korumaya çalış

    def _on_element_design_section_select(self, event=None):
        """Kesit seçimi değiştiğinde ilgili beton bilgilerini gösterir."""
        if not self.element_design_vars or not self.element_design_widgets: return

        selected_display_name = self.element_design_vars["selected_section_display"].get()
        if not selected_display_name or selected_display_name == "Tanımlı Dikdörtgen Kesit Yok":
            self.element_design_vars["concrete_material"].set("-")
            self.element_design_vars["concrete_fck"].set("-")
            return

        # Display name'den gerçek user_name'i çıkar (ilk kelime)
        selected_section_name = selected_display_name.split(" ")[0]

        sections = self._get_profile_data("sections")
        selected_section_data = self._find_item_by_name(sections, selected_section_name)

        if not selected_section_data:
            self.element_design_vars["concrete_material"].set("Hata: Kesit bulunamadı")
            self.element_design_vars["concrete_fck"].set("-")
            return

        concrete_material_name = selected_section_data.get("material_name")
        if not concrete_material_name:
             self.element_design_vars["concrete_material"].set("Hata: Malzeme atanmamış")
             self.element_design_vars["concrete_fck"].set("-")
             return

        materials = self._get_profile_data("materials")
        concrete_material_data = self._find_item_by_name(materials, concrete_material_name)

        if not concrete_material_data:
            self.element_design_vars["concrete_material"].set(f"{concrete_material_name} (Tanımsız)")
            self.element_design_vars["concrete_fck"].set("-")
        else:
            self.element_design_vars["concrete_material"].set(concrete_material_name)
            fck = concrete_material_data.get("props", {}).get("fck", 0.0)
            self.element_design_vars["concrete_fck"].set(f"{fck:.1f} MPa")


    def populate_element_design_page(self, parent_frame):
        """Tekil Eleman Tasarımı sayfasını oluşturur (Basit Eğilme)."""
        self.element_design_vars = {
            "selected_section_display": tk.StringVar(), # Combobox'ta görünen ad
            "concrete_material": tk.StringVar(value="-"), # Gösterilecek beton malzeme adı
            "concrete_fck": tk.StringVar(value="-"), # Gösterilecek fck
            "selected_rebar_name": tk.StringVar(), # Seçilen donatı adı
            "n_top": tk.IntVar(value=3), # Üst donatı adedi
            "phi_top": tk.DoubleVar(value=16), # Üst donatı çapı (mm)
            "n_bot": tk.IntVar(value=2), # Alt donatı adedi (şimdilik hesapta kullanılmayacak)
            "phi_bot": tk.DoubleVar(value=14), # Alt donatı çapı (mm)
            "cover": tk.DoubleVar(value=30), # Paspayı (mm)
            "stirrup_phi": tk.DoubleVar(value=10), # Etriye çapı (mm) - d hesabı için
            "design_moment_md": tk.DoubleVar(value=100), # Uygulanan moment (kNm)
            "results_text": tk.StringVar(value="Hesaplama sonucu burada gösterilecek.") # Sonuç alanı
        }
        self.element_design_widgets = {} # Widget referanslarını temizle

        parent_frame.columnconfigure(1, weight=1) # Giriş alanlarının genişlemesi için

        row_idx = 0
        # --- Başlık ---
        label_title = ui_components.create_content_label(parent_frame, "Tekil Eleman Tasarımı - Dikdörtgen Kesit Eğilme", self.theme)
        label_title.grid(row=row_idx, column=0, columnspan=3, padx=10, pady=15, sticky='w')
        row_idx += 1

        # --- Kesit Seçimi ---
        ttk.Label(parent_frame, text="Hesaplanacak Kesit:", style='Header.TLabel').grid(row=row_idx, column=0, padx=10, pady=5, sticky='w')
        combo_section = ui_components.create_content_combobox(parent_frame, [], self.theme, textvariable=self.element_design_vars["selected_section_display"])
        combo_section.grid(row=row_idx, column=1, columnspan=2, padx=10, pady=5, sticky='ew')
        combo_section.bind("<<ComboboxSelected>>", self._on_element_design_section_select)
        self.element_design_widgets["combo_section"] = combo_section
        row_idx += 1

        # --- Beton Bilgileri (Okuma Amaçlı) ---
        ttk.Label(parent_frame, text="Beton Malzemesi:", style='TLabel').grid(row=row_idx, column=0, padx=10, pady=2, sticky='w')
        lbl_concrete_mat = ttk.Label(parent_frame, textvariable=self.element_design_vars["concrete_material"], style='Data.TLabel') # Yeni stil gerekebilir
        lbl_concrete_mat.grid(row=row_idx, column=1, padx=10, pady=2, sticky='w')
        row_idx += 1
        ttk.Label(parent_frame, text="Beton Dayanımı (fck):", style='TLabel').grid(row=row_idx, column=0, padx=10, pady=2, sticky='w')
        lbl_concrete_fck = ttk.Label(parent_frame, textvariable=self.element_design_vars["concrete_fck"], style='Data.TLabel')
        lbl_concrete_fck.grid(row=row_idx, column=1, padx=10, pady=2, sticky='w')
        # Stil Tanımı (apply_theme_and_save içine eklenebilir veya burada tanımlanabilir)
        """ try:
             self.style.configure('Data.TLabel', font=('Segoe UI', 12, 'bold'), background=self.theme['content_bg'], foreground=self.theme['text'])
        except tk.TclError: pass # Zaten varsa hata vermesin """
        row_idx += 1

        # --- Donatı Seçimi ---
        ttk.Label(parent_frame, text="Donatı Malzemesi:", style='Header.TLabel').grid(row=row_idx, column=0, padx=10, pady=5, sticky='w')
        combo_rebar = ui_components.create_content_combobox(parent_frame, [], self.theme, textvariable=self.element_design_vars["selected_rebar_name"])
        combo_rebar.grid(row=row_idx, column=1, columnspan=2, padx=10, pady=5, sticky='ew')
        self.element_design_widgets["combo_rebar"] = combo_rebar
        row_idx += 1

        # --- Donatı Detayları ---
        ttk.Label(parent_frame, text="Üst Donatı (Adet):", style='TLabel').grid(row=row_idx, column=0, padx=10, pady=2, sticky='w')
        entry_n_top = ui_components.create_content_entry(parent_frame, self.theme, width=8, textvariable=self.element_design_vars["n_top"])
        entry_n_top.grid(row=row_idx, column=1, padx=10, pady=2, sticky='w')
        row_idx += 1
        ttk.Label(parent_frame, text="Üst Donatı Çapı (mm):", style='TLabel').grid(row=row_idx, column=0, padx=10, pady=2, sticky='w')
        # Combobox daha kullanıcı dostu olabilir
        combo_phi_top = ui_components.create_content_combobox(parent_frame, [8, 10, 12, 14, 16, 18, 20, 22, 25, 28, 30, 32], self.theme, state='normal', width=6, textvariable=self.element_design_vars["phi_top"])
        combo_phi_top.grid(row=row_idx, column=1, padx=10, pady=2, sticky='w')
        row_idx += 1

        ttk.Label(parent_frame, text="Alt Donatı (Adet):", style='TLabel').grid(row=row_idx, column=0, padx=10, pady=2, sticky='w')
        entry_n_bot = ui_components.create_content_entry(parent_frame, self.theme, width=8, textvariable=self.element_design_vars["n_bot"])
        entry_n_bot.grid(row=row_idx, column=1, padx=10, pady=2, sticky='w')
        row_idx += 1
        ttk.Label(parent_frame, text="Alt Donatı Çapı (mm):", style='TLabel').grid(row=row_idx, column=0, padx=10, pady=2, sticky='w')
        combo_phi_bot = ui_components.create_content_combobox(parent_frame, [8, 10, 12, 14, 16, 18, 20, 22, 25, 28, 30, 32], self.theme, state='normal', width=6, textvariable=self.element_design_vars["phi_bot"])
        combo_phi_bot.grid(row=row_idx, column=1, padx=10, pady=2, sticky='w')
        row_idx += 1

        # --- Diğer Girdiler ---
        ttk.Label(parent_frame, text="Paspayı (mm):", style='TLabel').grid(row=row_idx, column=0, padx=10, pady=2, sticky='w')
        entry_cover = ui_components.create_content_entry(parent_frame, self.theme, width=8, textvariable=self.element_design_vars["cover"])
        entry_cover.grid(row=row_idx, column=1, padx=10, pady=2, sticky='w')
        row_idx += 1
        ttk.Label(parent_frame, text="Etriye Çapı (mm):", style='TLabel').grid(row=row_idx, column=0, padx=10, pady=2, sticky='w')
        entry_stirrup = ui_components.create_content_entry(parent_frame, self.theme, width=8, textvariable=self.element_design_vars["stirrup_phi"])
        entry_stirrup.grid(row=row_idx, column=1, padx=10, pady=2, sticky='w')
        row_idx += 1
        ttk.Label(parent_frame, text="Tasarım Momenti Md (kNm):", style='Header.TLabel').grid(row=row_idx, column=0, padx=10, pady=5, sticky='w')
        entry_md = ui_components.create_content_entry(parent_frame, self.theme, width=15, textvariable=self.element_design_vars["design_moment_md"])
        entry_md.grid(row=row_idx, column=1, padx=10, pady=5, sticky='w')
        row_idx += 1

        # --- Hesaplama Butonu ---
        btn_calculate = ui_components.create_content_button(parent_frame, "Hesapla", self.theme, command=self._calculate_bending_capacity)
        btn_calculate.grid(row=row_idx, column=0, columnspan=3, padx=10, pady=15)
        row_idx += 1

        # --- Sonuç Alanı ---
        results_frame = tk.Frame(parent_frame, bg=self.theme['text_area_bg'], bd=1, relief=tk.FLAT)
        results_frame.grid(row=row_idx, column=0, columnspan=3, padx=10, pady=10, sticky='nsew')
        parent_frame.rowconfigure(row_idx, weight=1)
        print(f"DEBUG: results_frame oluşturuldu ve grid'e eklendi (row={row_idx}).") # Eklendi

        results_text_widget = tk.Text(results_frame, wrap=tk.WORD, height=10,
                                  # font=("Consolas", 11), # Eski Font
                                  font=("Segoe UI", 12),    # Yeni Font (Panel'dekine benzer)
                                  bg=self.theme['text_area_bg'], # Arkaplan (Panel ile aynı)
                                  fg=self.theme['text_area_fg'],  # Yazı rengi (Panel ile aynı)
                                  relief='flat',                # Kenarlık stili
                                  bd=1,                         # Kenarlık Kalınlığı (Panel'deki gibi)
                                  highlightthickness=1,         # Odak/Vurgu Kalınlığı (Panel'deki gibi)
                                  highlightbackground=self.theme['entry_border'], # Kenarlık Rengi (entry'ler gibi)
                                  padx=5,                       # İç boşluk X
                                  pady=5,                       # İç boşluk Y
                                  state=tk.DISABLED)            # Başlangıçta düzenlenemez
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=results_text_widget.yview)
        results_text_widget.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        results_text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        print(f"DEBUG: results_text_widget ve scrollbar oluşturuldu ve pack edildi.") # Eklendi
        self.element_design_widgets["results_text_widget"] = results_text_widget

        # --- Başlangıç Ayarları ---
        self._update_element_design_comboboxes() # Combobox'ları doldur
        # İlk kesit seçiliyse bilgilerini yükle
        if combo_section and combo_section['values']:
            combo_section.current(0)
            self._on_element_design_section_select()
        # İlk donatı malzemesini seç
        if combo_rebar and combo_rebar['values']:
             combo_rebar.current(0)

    def _calculate_bending_capacity(self):
        """Tekil eleman tasarımı sayfasındaki girdilere göre eğilme momenti kapasitesini hesaplar."""
        results_widget = self.element_design_widgets.get("results_text_widget")
        if not results_widget: return

        results_widget.config(state=tk.NORMAL) # Yazmak için aktif et
        results_widget.delete('1.0', tk.END)    # Önceki sonuçları temizle

        output = [] # Sonuç metinlerini biriktirecek liste
        output.append("--- GİRDİLER ---")

        try:
            # 1. Seçili Kesiti Al
            selected_section_display = self.element_design_vars["selected_section_display"].get()
            if not selected_section_display or selected_section_display == "Tanımlı Dikdörtgen Kesit Yok":
                raise ValueError("Lütfen geçerli bir dikdörtgen kesit seçin.")
            selected_section_name = selected_section_display.split(" ")[0]
            sections = self._get_profile_data("sections")
            section_data = self._find_item_by_name(sections, selected_section_name)
            if not section_data or section_data.get("type") != "Dikdörtgen":
                raise ValueError(f"Seçilen kesit '{selected_section_name}' bulunamadı veya dikdörtgen değil.")

            dims = section_data.get("dimensions", {})
            b = float(dims.get("b", 0.0)) # mm
            h = float(dims.get("h", 0.0)) # mm
            if b <= 0 or h <= 0: raise ValueError("Kesit boyutları (b, h) pozitif olmalı.")
            output.append(f"Kesit: {selected_section_name} (b={b:.0f} mm, h={h:.0f} mm)")

            # 2. Beton Malzemesini Al
            concrete_material_name = section_data.get("material_name")
            if not concrete_material_name: raise ValueError("Kesit için beton malzemesi atanmamış.")
            materials = self._get_profile_data("materials")
            concrete_material_data = self._find_item_by_name(materials, concrete_material_name)
            if not concrete_material_data: raise ValueError(f"Beton malzemesi '{concrete_material_name}' profil tanımlarında bulunamadı.")
            concrete_props = concrete_material_data.get("props", {})
            fck = float(concrete_props.get("fck", 0.0)) # MPa (N/mm²)
            if fck <= 0: raise ValueError("Beton karakteristik dayanımı (fck) pozitif olmalı.")
            output.append(f"Beton: {concrete_material_name} (fck = {fck:.1f} MPa)")

            # 3. Donatı Malzemesini Al
            selected_rebar_name = self.element_design_vars["selected_rebar_name"].get()
            if not selected_rebar_name or selected_rebar_name == "Tanımlı Donatı Malzemesi Yok":
                raise ValueError("Lütfen geçerli bir donatı malzemesi seçin.")
            rebar_material_data = self._find_item_by_name(materials, selected_rebar_name)
            if not rebar_material_data: raise ValueError(f"Donatı malzemesi '{selected_rebar_name}' profil tanımlarında bulunamadı.")
            rebar_props = rebar_material_data.get("props", {})
            fyk = float(rebar_props.get("fyk", 0.0)) # MPa (N/mm²)
            Es = float(rebar_props.get("Es", 200000.0)) # MPa (N/mm²) - Varsayılan 2e5
            if fyk <= 0: raise ValueError("Donatı karakteristik akma dayanımı (fyk) pozitif olmalı.")
            output.append(f"Donatı: {selected_rebar_name} (fyk = {fyk:.0f} MPa, Es = {Es:.0f} MPa)")

            # 4. Donatı ve Diğer Girdileri Al
            n_top = self.element_design_vars["n_top"].get()
            phi_top = self.element_design_vars["phi_top"].get()
            # n_bot = self.element_design_vars["n_bot"].get() # Şimdilik kullanılmıyor
            # phi_bot = self.element_design_vars["phi_bot"].get() # Şimdilik kullanılmıyor
            cover = self.element_design_vars["cover"].get()
            stirrup_phi = self.element_design_vars["stirrup_phi"].get()
            Md_kNm = self.element_design_vars["design_moment_md"].get() # kNm

            if n_top <= 0 or phi_top <= 0: raise ValueError("Üst donatı adedi ve çapı pozitif olmalı.")
            if cover < 0: raise ValueError("Paspayı negatif olamaz.")
            if stirrup_phi < 0: raise ValueError("Etriye çapı negatif olamaz.")

            output.append(f"Üst Donatı (Çekme): {n_top} adet, Ø{phi_top:.0f} mm")
            output.append(f"Paspayı: {cover:.0f} mm")
            output.append(f"Etriye Çapı: {stirrup_phi:.0f} mm")
            output.append(f"Tasarım Momenti (Md): {Md_kNm:.2f} kNm")
            output.append("\n--- HESAPLAMA (TS 500 - Basitleştirilmiş) ---")

            # 5. Hesaplama Sabitleri ve Tasarım Değerleri
            gamma_mc = 1.5
            gamma_ms = 1.15
            fcd = fck / gamma_mc
            fyd = fyk / gamma_ms
            epsilon_cu3 = 0.003
            # k1: Beton basınç bloğu derinliği / Tarafsız eksen derinliği oranı
            k1 = 0.85 # fck <= 50 MPa için (TS 500 Tablo 3.3) - Daha hassas kontrol eklenebilir
            output.append(f"fcd = {fck:.1f} / {gamma_mc} = {fcd:.2f} MPa")
            output.append(f"fyd = {fyk:.0f} / {gamma_ms} = {fyd:.2f} MPa")
            output.append(f"Es = {Es:.0f} MPa, ε_cu3 = {epsilon_cu3:.4f}, k1 = {k1:.2f}")

            # 6. Donatı Alanı ve Faydalı Yükseklik
            As_top = n_top * math.pi * (phi_top / 2)**2 # mm² (Çekme donatısı)
            # As_bot = n_bot * math.pi * (phi_bot / 2)**2 # mm² (Basınç donatısı - Şimdilik yok)

            # Faydalı yükseklik (d) - Çekme donatısının merkezine olan mesafe
            d = h - cover - stirrup_phi - (phi_top / 2) # mm
            if d <= 0: raise ValueError(f"Hesaplanan faydalı yükseklik (d={d:.1f} mm) geçersiz.")
            output.append(f"Çekme Donatı Alanı (As) = {As_top:.2f} mm²")
            output.append(f"Faydalı Yükseklik (d) = {h:.0f} - {cover:.0f} - {stirrup_phi:.0f} - {phi_top/2:.1f} = {d:.2f} mm")

            # 7. Moment Kapasitesi (Mr) Hesabı (Tek Donatılı)
            # Basınç bloğu derinliği (a)
            # As * fyd = 0.85 * fcd * b * a
            a = (As_top * fyd) / (0.85 * fcd * b)
            output.append(f"Basınç Bloğu Derinliği (a) = ({As_top:.2f} * {fyd:.2f}) / (0.85 * {fcd:.2f} * {b:.0f}) = {a:.2f} mm")

            # Tarafsız eksen derinliği (c = a/k1)
            c = a / k1
            output.append(f"Tarafsız Eksen Derinliği (c) = {a:.2f} / {k1:.2f} = {c:.2f} mm")

            # Kontrol: a, kesit içinde mi? (Basit kontrol)
            if a <= 0 or a > h: raise ValueError(f"Hesaplanan basınç bloğu derinliği (a={a:.1f}mm) geçersiz.")
            # Kontrol: Tarafsız eksen faydalı yükseklik içinde mi?
            if c > d: # Bu aslında çeliğin akmadığı anlamına gelebilir (daha detaylı kontrol lazım)
                 output.append(f"UYARI: Tarafsız eksen (c={c:.1f}mm) faydalı yüksekliğin (d={d:.1f}mm) dışında. Hesap şüpheli olabilir.")
                 # Şimdilik devam edelim ama normalde burada farklı hesap gerekir.

            # Moment Kapasitesi (Mr)
            # Mr = As * fyd * (d - a/2)
            Mr_Nmm = As_top * fyd * (d - a / 2)
            Mr_kNm = Mr_Nmm / 1e6 # Nmm'den kNm'ye çevrim
            output.append(f"Moment Kapasitesi (Mr) = {As_top:.2f} * {fyd:.2f} * ({d:.2f} - {a/2:.2f})")
            output.append(f"Mr = {Mr_Nmm:.2f} Nmm = {Mr_kNm:.2f} kNm")

            # 8. Karşılaştırma
            output.append("\n--- SONUÇ ---")
            Md_Nmm = Md_kNm * 1e6
            ratio = Mr_Nmm / Md_Nmm if Md_Nmm != 0 else float('inf')

            if Mr_Nmm >= Md_Nmm:
                status = "YETERLİ"
                output.append(f"KAPASİTE DURUMU: {status} (Mr = {Mr_kNm:.2f} kNm >= Md = {Md_kNm:.2f} kNm)")
            else:
                status = "YETERSİZ"
                output.append(f"KAPASİTE DURUMU: {status} (Mr = {Mr_kNm:.2f} kNm < Md = {Md_kNm:.2f} kNm)")
            output.append(f"Kapasite Oranı (Mr / Md): {ratio:.3f}")

            # TODO: Minimum ve maksimum donatı oranları kontrolü eklenebilir.
            # As_min = ...
            # As_max = ...
            # if not (As_min <= As_top <= As_max): output.append("UYARI: Donatı oranı sınırların dışında!")

        except ValueError as ve:
            output.append(f"\n!!! HATA: {ve}")
        except Exception as e:
            output.append(f"\n!!! BEKLENMEDİK HATA: {e}")
        finally:
            # Sonuçları Text widget'ına yaz
            results_widget.insert(tk.END, "\n".join(output))
            results_widget.config(state=tk.DISABLED) # Tekrar düzenlenemez yap

    # --- Profil Veri Yönetimi Metotları ---
    def save_project_info(self):
        if not self.current_profile_name: messagebox.showwarning("Profil Seçilmedi", "Lütfen önce bir profil seçin veya oluşturun."); return
        profile = self.profiles_data.setdefault(self.current_profile_name, {"project_info": {}, "materials": [], "sections": []})
        project_info = profile.setdefault("project_info", {})
        project_info["name"] = self.project_info_vars.get("name", tk.StringVar()).get()
        desc_widget = self.project_info_vars.get("desc_widget")
        if desc_widget: project_info["desc"] = desc_widget.get("1.0", tk.END).strip()
        else: project_info["desc"] = ""
        project_info["engineer"] = self.project_info_vars.get("engineer", tk.StringVar()).get()
        project_info["concrete_reg"] = self.project_info_vars.get("concrete_reg", tk.StringVar()).get()
        project_info["seismic_reg"] = self.project_info_vars.get("seismic_reg", tk.StringVar()).get()
        project_info["load_reg"] = self.project_info_vars.get("load_reg", tk.StringVar()).get()
        project_info["units"] = self.project_info_vars.get("units", tk.StringVar()).get()
        utils.save_profiles(); messagebox.showinfo("Kaydedildi", f"'{self.current_profile_name}' profili için proje bilgileri kaydedildi.")

    def load_project_info(self):
        if not self.project_info_vars: return
        if self.current_profile_name not in self.profiles_data:
            print(f"Warning: Profile '{self.current_profile_name}' not found for loading project info.")
            self.project_info_vars.get("name", tk.StringVar()).set("Yeni Proje")
            desc_widget = self.project_info_vars.get("desc_widget");
            if desc_widget: desc_widget.delete("1.0", tk.END)
            self.project_info_vars.get("engineer", tk.StringVar()).set("")
            return
        profile = self.profiles_data[self.current_profile_name]; project_info = profile.get("project_info", {})
        self.project_info_vars.get("name", tk.StringVar()).set(project_info.get("name", "Yeni Proje"))
        desc_widget = self.project_info_vars.get("desc_widget")
        if desc_widget: desc_widget.delete("1.0", tk.END); desc_widget.insert("1.0", project_info.get("desc", ""))
        self.project_info_vars.get("engineer", tk.StringVar()).set(project_info.get("engineer", ""))
        self.project_info_vars.get("concrete_reg", tk.StringVar()).set(project_info.get("concrete_reg", "TS 500 (2000)"))
        self.project_info_vars.get("seismic_reg", tk.StringVar()).set(project_info.get("seismic_reg", "TBDY 2018"))
        self.project_info_vars.get("load_reg", tk.StringVar()).set(project_info.get("load_reg", "TS 498 (1997)"))
        self.project_info_vars.get("units", tk.StringVar()).set(project_info.get("units", "Metrik (kN, m, C)"))
        print(f"Project info loaded for profile: {self.current_profile_name}")

    # --- Malzeme Sayfası Metotları ---
    def clear_material_form(self):
        self.material_detail_vars.get("user_name", tk.StringVar()).set("")
        self.material_detail_vars.get("type", tk.StringVar()).set("Beton")
        self.material_detail_vars.get("class", tk.StringVar()).set("")
        self.material_detail_vars.get("is_custom", tk.IntVar()).set(0)
        self.material_detail_vars.get("fck", tk.DoubleVar()).set(0.0)
        self.material_detail_vars.get("fyk", tk.DoubleVar()).set(0.0)
        self.material_detail_vars.get("Ec", tk.DoubleVar()).set(0.0)
        self.material_detail_vars.get("Es", tk.DoubleVar()).set(0.0)
        if self.material_listbox_ref:
            selection = self.material_listbox_ref.curselection()
            if selection: self.material_listbox_ref.selection_clear(selection[0])
        self.on_material_type_change(); self.on_custom_material_toggle()

    def update_material_listbox(self):
        if self.material_listbox_ref and self.current_profile_name in self.profiles_data:
            self.material_listbox_ref.delete(0, tk.END)
            materials = self.profiles_data[self.current_profile_name].get("materials", [])
            materials.sort(key=lambda x: x.get("user_name", "").lower())
            for mat in materials:
                display_name = f"{mat.get('type', '?')}: {mat.get('user_name', 'İsimsiz')} ({mat.get('class', 'Özel')})"
                self.material_listbox_ref.insert(tk.END, display_name)

    def on_material_type_change(self):
        if not self.material_detail_widgets: return
        mat_type = self.material_detail_vars.get("type", tk.StringVar()).get()
        is_concrete = (mat_type == "Beton")
        for w_name in ["lbl_concrete_class", "combo_concrete_class", "chk_custom_concrete", "lbl_fck", "entry_fck"]:
            widget = self.material_detail_widgets.get(w_name)
            if widget:
                try:
                    if is_concrete: widget.grid()
                    else: widget.grid_remove()
                except tk.TclError: pass
        for w_name in ["lbl_rebar_class", "combo_rebar_class", "chk_custom_rebar", "lbl_fyk", "entry_fyk", "lbl_Es", "entry_Es"]:
             widget = self.material_detail_widgets.get(w_name)
             if widget:
                try:
                    if not is_concrete: widget.grid()
                    else: widget.grid_remove()
                except tk.TclError: pass
        self.material_detail_vars.get("class", tk.StringVar()).set("")
        if is_concrete and self.material_detail_widgets.get("combo_concrete_class"): self.material_detail_widgets["combo_concrete_class"]["values"] = list(config.CONCRETE_PROPS.keys())
        elif not is_concrete and self.material_detail_widgets.get("combo_rebar_class"): self.material_detail_widgets["combo_rebar_class"]["values"] = list(config.REBAR_PROPS.keys())
        self.on_custom_material_toggle()

    def on_material_class_change(self):
        if self.material_detail_vars.get("is_custom", tk.IntVar()).get() == 1: return
        mat_type = self.material_detail_vars.get("type", tk.StringVar()).get()
        mat_class = self.material_detail_vars.get("class", tk.StringVar()).get()
        if mat_type == "Beton" and mat_class in config.CONCRETE_PROPS:
            props = config.CONCRETE_PROPS[mat_class]; self.material_detail_vars.get("fck", tk.DoubleVar()).set(props.get("fck", 0.0))
        elif mat_type == "Donatı Çeliği" and mat_class in config.REBAR_PROPS:
            props = config.REBAR_PROPS[mat_class]; self.material_detail_vars.get("fyk", tk.DoubleVar()).set(props.get("fyk", 0.0)); self.material_detail_vars.get("Es", tk.DoubleVar()).set(props.get("Es", 0.0))
        else:
             if mat_type == "Beton": self.material_detail_vars.get("fck", tk.DoubleVar()).set(0.0)
             else: self.material_detail_vars.get("fyk", tk.DoubleVar()).set(0.0); self.material_detail_vars.get("Es", tk.DoubleVar()).set(0.0)

    def on_custom_material_toggle(self):
        if not self.material_detail_widgets: return
        is_custom = self.material_detail_vars.get("is_custom", tk.IntVar()).get() == 1
        mat_type = self.material_detail_vars.get("type", tk.StringVar()).get()
        prop_state = tk.NORMAL if is_custom else tk.DISABLED; class_combo_state = tk.DISABLED if is_custom else 'readonly'
        if mat_type == "Beton":
            if self.material_detail_widgets.get("entry_fck"): self.material_detail_widgets["entry_fck"].config(state=prop_state)
            if self.material_detail_widgets.get("combo_concrete_class"): self.material_detail_widgets["combo_concrete_class"].config(state=class_combo_state)
            if is_custom: self.material_detail_vars.get("class", tk.StringVar()).set("Özel")
            else: self.on_material_class_change()
        else:
            if self.material_detail_widgets.get("entry_fyk"): self.material_detail_widgets["entry_fyk"].config(state=prop_state)
            if self.material_detail_widgets.get("entry_Es"): self.material_detail_widgets["entry_Es"].config(state=prop_state)
            if self.material_detail_widgets.get("combo_rebar_class"): self.material_detail_widgets["combo_rebar_class"].config(state=class_combo_state)
            if is_custom: self.material_detail_vars.get("class", tk.StringVar()).set("Özel")
            else: self.on_material_class_change()

    def save_material_from_form(self):
        if not self.current_profile_name: messagebox.showerror("Hata", "Aktif profil bulunamadı."); return
        user_name = self.material_detail_vars.get("user_name", tk.StringVar()).get().strip()
        if not user_name: messagebox.showerror("Hata", "Malzeme adı boş olamaz."); return
        mat_type = self.material_detail_vars.get("type", tk.StringVar()).get()
        mat_class = self.material_detail_vars.get("class", tk.StringVar()).get() if self.material_detail_vars.get("is_custom", tk.IntVar()).get() == 0 else "Özel"
        is_custom = self.material_detail_vars.get("is_custom", tk.IntVar()).get() == 1
        props = {}
        try:
            if mat_type == "Beton": props["fck"] = self.material_detail_vars.get("fck", tk.DoubleVar()).get()
            else: props["fyk"] = self.material_detail_vars.get("fyk", tk.DoubleVar()).get(); props["Es"] = self.material_detail_vars.get("Es", tk.DoubleVar()).get()
        except tk.TclError: messagebox.showerror("Hata", "Lütfen geçerli sayısal malzeme özellikleri girin."); return

        new_material_data = {"user_name": user_name, "type": mat_type, "class": mat_class, "is_custom": is_custom, "props": props}
        profile = self.profiles_data.setdefault(self.current_profile_name, {"project_info": {}, "materials": [], "sections": []})
        materials = profile.setdefault("materials", [])
        selected_index = -1
        if self.material_listbox_ref: selection = self.material_listbox_ref.curselection();
        if selection: selected_index = selection[0]
        found_index = -1; original_name_if_editing = None
        if selected_index != -1:
            try: original_name_if_editing = materials[selected_index].get("user_name")
            except IndexError: pass
        for i, mat in enumerate(materials):
            if mat.get("user_name") == user_name: found_index = i; break

        if user_name == original_name_if_editing or found_index == -1:
            if selected_index != -1 and original_name_if_editing is not None :
                 try: materials[selected_index] = new_material_data; print(f"Material '{user_name}' updated.")
                 except IndexError: materials.append(new_material_data); print(f"Material '{user_name}' added (update failed, added as new).")
            else: materials.append(new_material_data); print(f"Material '{user_name}' added.")
            utils.save_profiles(); self.update_material_listbox(); self.clear_material_form(); messagebox.showinfo("Başarılı", f"Malzeme '{user_name}' kaydedildi.")
        else: messagebox.showerror("Hata", f"'{user_name}' adında başka bir malzeme zaten var.")

    def load_selected_material_to_form(self):
        if not self.material_listbox_ref: return
        selection = self.material_listbox_ref.curselection()
        if not selection: return
        selected_index = selection[0]
        materials = self.profiles_data.get(self.current_profile_name, {}).get("materials", [])
        if selected_index < 0 or selected_index >= len(materials): messagebox.showerror("Hata", "Seçilen malzeme verisi bulunamadı."); return
        material_data = materials[selected_index]
        self.material_detail_vars.get("user_name", tk.StringVar()).set(material_data.get("user_name", ""))
        self.material_detail_vars.get("type", tk.StringVar()).set(material_data.get("type", "Beton"))
        self.material_detail_vars.get("class", tk.StringVar()).set(material_data.get("class", ""))
        self.material_detail_vars.get("is_custom", tk.IntVar()).set(1 if material_data.get("is_custom") else 0)
        props = material_data.get("props", {})
        if material_data.get("type") == "Beton": self.material_detail_vars.get("fck", tk.DoubleVar()).set(props.get("fck", 0.0))
        else: self.material_detail_vars.get("fyk", tk.DoubleVar()).set(props.get("fyk", 0.0)); self.material_detail_vars.get("Es", tk.DoubleVar()).set(props.get("Es", 0.0))
        self.on_material_type_change(); self.on_custom_material_toggle()

    def delete_selected_material(self):
        if not self.material_listbox_ref: return
        selection = self.material_listbox_ref.curselection()
        if not selection: messagebox.showwarning("Malzeme Seçilmedi", "Lütfen silinecek malzemeyi seçin."); return
        selected_index = selection[0]
        profile = self.profiles_data.get(self.current_profile_name)
        if profile and "materials" in profile and 0 <= selected_index < len(profile["materials"]):
            material_to_delete = profile["materials"][selected_index]
            user_name_to_delete = material_to_delete.get("user_name", "Bilinmeyen")
            if messagebox.askyesno("Malzeme Sil", f"'{user_name_to_delete}' malzemesini silmek istediğinizden emin misiniz?", parent=self.main_app.root):
                del profile["materials"][selected_index]
                utils.save_profiles(); self.update_material_listbox(); self.clear_material_form()
                messagebox.showinfo("Başarılı", f"'{user_name_to_delete}' malzemesi silindi.")
        else: messagebox.showerror("Hata", "Malzeme silinemedi.")

    # --- Profil Yönetimi Sayfası Metotları ---
    def update_profile_listbox(self):
         if self.profile_listbox_ref:
             self.profile_listbox_ref.delete(0, tk.END)
             for name in sorted(self.profiles_data.keys()): self.profile_listbox_ref.insert(tk.END, name)
             try:
                 idx = list(sorted(self.profiles_data.keys())).index(self.current_profile_name)
                 self.profile_listbox_ref.selection_clear(0, tk.END); self.profile_listbox_ref.select_set(idx); self.profile_listbox_ref.activate(idx)
             except ValueError: pass

    def load_selected_profile(self):
        if not self.profile_listbox_ref: return
        selection = self.profile_listbox_ref.curselection()
        if not selection: messagebox.showwarning("Profil Seçilmedi", "Lütfen listeden yüklenecek bir profil seçin."); return
        selected_name = self.profile_listbox_ref.get(selection[0])
        if selected_name in self.profiles_data:
            self.current_profile_name = selected_name
            self.main_app.current_profile_name = selected_name # Ana app'teki ismi de güncelle
            print(f"Profile '{self.current_profile_name}' selected.")
            self.show_page("project_info"); messagebox.showinfo("Profil Yüklendi", f"'{self.current_profile_name}' profili yüklendi.")
        else: messagebox.showerror("Hata", f"Seçilen profil '{selected_name}' bulunamadı.")

    def create_new_profile(self):
         new_name = simpledialog.askstring("Yeni Profil", "Yeni profil için bir isim girin:", parent=self.main_app.root)
         if new_name and new_name.strip():
             new_name = new_name.strip()
             if new_name in self.profiles_data: messagebox.showerror("Hata", f"'{new_name}' isimli profil zaten mevcut.")
             else:
                 default_profile_data = config.DEFAULT_PROFILE_DATA.copy()
                 default_profile_data["project_info"]["name"] = new_name
                 self.profiles_data[new_name] = default_profile_data
                 self.current_profile_name = new_name
                 self.main_app.current_profile_name = new_name
                 utils.save_profiles(); self.update_profile_listbox(); self.show_page("project_info")
                 messagebox.showinfo("Başarılı", f"'{new_name}' profili oluşturuldu ve aktif hale getirildi.")
         elif new_name is not None: messagebox.showwarning("Geçersiz İsim", "Profil adı boş olamaz.")

    def rename_selected_profile(self):
         if not self.profile_listbox_ref: return
         selection = self.profile_listbox_ref.curselection()
         if not selection: messagebox.showwarning("Profil Seçilmedi", "Lütfen listeden yeniden adlandırılacak bir profil seçin."); return
         old_name = self.profile_listbox_ref.get(selection[0])
         new_name = simpledialog.askstring("Profili Yeniden Adlandır", f"'{old_name}' için yeni isim girin:", initialvalue=old_name, parent=self.main_app.root)
         if new_name and new_name.strip():
             new_name = new_name.strip()
             if new_name == old_name: return
             if new_name in self.profiles_data: messagebox.showerror("Hata", f"'{new_name}' isimli profil zaten mevcut.")
             else:
                 self.profiles_data[new_name] = self.profiles_data.pop(old_name)
                 if "project_info" in self.profiles_data[new_name]: self.profiles_data[new_name]["project_info"]["name"] = new_name
                 if self.current_profile_name == old_name:
                     self.current_profile_name = new_name
                     self.main_app.current_profile_name = new_name
                 utils.save_profiles(); self.update_profile_listbox()
                 messagebox.showinfo("Başarılı", f"'{old_name}' profili '{new_name}' olarak yeniden adlandırıldı.")
         elif new_name is not None: messagebox.showwarning("Geçersiz İsim", "Profil adı boş olamaz.")

    def delete_selected_profile(self):
         if not self.profile_listbox_ref: return
         selection = self.profile_listbox_ref.curselection()
         if not selection: messagebox.showwarning("Profil Seçilmedi", "Lütfen listeden silinecek bir profil seçin."); return
         profile_to_delete = self.profile_listbox_ref.get(selection[0])
         if len(self.profiles_data) <= 1: messagebox.showerror("Hata", "Son kalan profil silinemez."); return
         if messagebox.askyesno("Profili Sil", f"'{profile_to_delete}' profilini silmek istediğinizden emin misiniz?", parent=self.main_app.root):
             del self.profiles_data[profile_to_delete]
             if self.current_profile_name == profile_to_delete:
                 self.current_profile_name = list(self.profiles_data.keys())[0]
                 self.main_app.current_profile_name = self.current_profile_name
                 self.load_project_info()
             utils.save_profiles(); self.update_profile_listbox()
             messagebox.showinfo("Başarılı", f"'{profile_to_delete}' profili silindi.")

    def _update_section_material_combobox(self):
        """Kesit formu için Malzeme ComboBox'ını günceller (Sadece Beton)."""
        if not self.section_detail_widgets or "combo_material" not in self.section_detail_widgets:
            return

        combo_material = self.section_detail_widgets["combo_material"]
        materials = self.main_app.profiles_data.get(self.main_app.current_profile_name, {}).get("materials", [])
        # Sadece Beton malzemelerini filtrele ve isimlerini al
        concrete_material_names = sorted([
            mat.get("user_name", "İsimsiz") for mat in materials if mat.get("type") == "Beton"
        ])

        if not concrete_material_names:
            combo_material['values'] = []
            combo_material.set("Tanımlı Beton Yok")
            combo_material.config(state=tk.DISABLED)
        else:
            current_value = self.section_detail_vars.get("material_name", tk.StringVar()).get()
            combo_material['values'] = concrete_material_names
            if current_value in concrete_material_names:
                combo_material.set(current_value)
            elif concrete_material_names:
                 combo_material.set(concrete_material_names[0]) # İlkini seç
            else:
                combo_material.set("")
            combo_material.config(state='readonly')

    def populate_section_page(self, parent_frame):
        """Kesit Kütüphanesi sayfasını oluşturur ve doldurur."""
        # Form değişkenlerini tanımla (Tkinter değişkenleri)
        self.section_detail_vars = {
            "user_name": tk.StringVar(),
            "type": tk.StringVar(value="Dikdörtgen"), # Varsayılan tip
            "material_name": tk.StringVar(), # Malzeme adı (Combobox'tan seçilecek)
            "width_b": tk.DoubleVar(), # Dikdörtgen için genişlik (mm?)
            "height_h": tk.DoubleVar(), # Dikdörtgen için yükseklik (mm?)
            "diameter_d": tk.DoubleVar() # Dairesel için çap (mm?)
            # TODO: Gelecekte çelik profil seçimi veya donatı bilgisi eklenebilir
        }
        self.section_detail_widgets = {} # Widget referanslarını temizle

        # PanedWindow (Sol: Liste, Sağ: Detay)
        section_pane = tk.PanedWindow(parent_frame, bd=0, sashwidth=4, sashrelief=tk.FLAT, orient=tk.HORIZONTAL, bg=self.theme['content_bg'])
        section_pane.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # --- Sol Bölüm: Kesit Listesi ---
        list_frame = tk.Frame(section_pane, bg=self.theme['content_bg'])
        section_pane.add(list_frame, width=250, stretch="never") # Sabit genişlik

        ttk.Label(list_frame, text="Tanımlı Kesitler:", style='Header.TLabel').pack(anchor='w', padx=5, pady=(0,5))

        self.section_listbox_ref = tk.Listbox(list_frame, height=15, font=("Segoe UI", 13), relief='flat', bd=1,
                                              bg=self.theme['listbox_bg'], fg=self.theme['listbox_fg'],
                                              selectbackground=self.theme['listbox_select_bg'],
                                              selectforeground=self.theme['title_text'],
                                              highlightthickness=1, highlightbackground=self.theme['entry_border'],
                                              exportselection=False)
        self.section_listbox_ref.pack(fill=tk.BOTH, expand=True, padx=5)
        self.section_listbox_ref.bind('<<ListboxSelect>>', lambda e: self.load_selected_section_to_form())

        # Liste Butonları (Yeni, Düzenle, Sil)
        list_button_frame = tk.Frame(list_frame, bg=self.theme['content_bg'])
        list_button_frame.pack(fill=tk.X, pady=5, padx=5)
        ttk.Button(list_button_frame, text="Yeni", style='TButton', width=6, command=self.clear_section_form).pack(side=tk.LEFT, padx=2)
        # Düzenle butonu da seçili formu yükler, sonra kaydedilir
        ttk.Button(list_button_frame, text="Düzenle", style='TButton', width=8, command=self.load_selected_section_to_form).pack(side=tk.LEFT, padx=2)
        ttk.Button(list_button_frame, text="Sil", style='TButton', width=6, command=self.delete_selected_section).pack(side=tk.LEFT, padx=2)

        # --- Sağ Bölüm: Kesit Detay Formu ---
        detail_frame = tk.Frame(section_pane, bg=self.theme['content_bg'])
        section_pane.add(detail_frame, stretch="always")

        ttk.Label(detail_frame, text="Kesit Detayları:", style='Header.TLabel').grid(row=0, column=0, columnspan=3, sticky='w', padx=10, pady=(0,10))

        # Detay Formu Çerçevesi (Grid Layout Kullanımı)
        detail_form_frame = tk.Frame(detail_frame, bg=self.theme['content_bg'])
        detail_form_frame.grid(row=1, column=0, sticky='nsew', padx=10)
        detail_frame.rowconfigure(1, weight=1) # Form alanının genişlemesini sağla
        detail_frame.columnconfigure(0, weight=1)
        detail_form_frame.columnconfigure(1, weight=1) # Giriş alanlarının genişlemesi için

        row_idx = 0
        # Kesit Adı
        ttk.Label(detail_form_frame, text="Kesit Adı:", style='Header.TLabel').grid(row=row_idx, column=0, sticky='w', padx=5, pady=5)
        entry_name = ui_components.create_content_entry(detail_form_frame, current_theme=self.theme, textvariable=self.section_detail_vars["user_name"])
        entry_name.grid(row=row_idx, column=1, sticky='ew', padx=5, pady=5)
        self.section_detail_widgets["entry_name"] = entry_name
        row_idx += 1

        # Kesit Tipi
        ttk.Label(detail_form_frame, text="Kesit Tipi:", style='Header.TLabel').grid(row=row_idx, column=0, sticky='w', padx=5, pady=5)
        combo_type = ui_components.create_content_combobox(detail_form_frame, ["Dikdörtgen", "Dairesel"], # Başlangıç tipleri
                                                          current_theme=self.theme, textvariable=self.section_detail_vars["type"])
        combo_type.bind("<<ComboboxSelected>>", lambda e: self.on_section_type_change())
        combo_type.grid(row=row_idx, column=1, sticky='ew', padx=5, pady=5)
        self.section_detail_widgets["combo_type"] = combo_type
        row_idx += 1

        # Malzeme (Beton Malzemeleri listelenecek)
        ttk.Label(detail_form_frame, text="Malzeme:", style='Header.TLabel').grid(row=row_idx, column=0, sticky='w', padx=5, pady=5)
        combo_material = ui_components.create_content_combobox(detail_form_frame, [], # Başlangıçta boş, sonra doldurulacak
                                                               current_theme=self.theme, textvariable=self.section_detail_vars["material_name"])
        combo_material.grid(row=row_idx, column=1, sticky='ew', padx=5, pady=5)
        self.section_detail_widgets["combo_material"] = combo_material
        row_idx += 1

        # --- Boyutlar --- (Başlangıçta bazıları gizli olacak)
        # Genişlik (b) - Dikdörtgen için
        lbl_width = ttk.Label(detail_form_frame, text="Genişlik b (mm):", style='Header.TLabel')
        lbl_width.grid(row=row_idx, column=0, sticky='w', padx=5, pady=5)
        entry_width = ui_components.create_content_entry(detail_form_frame, current_theme=self.theme, textvariable=self.section_detail_vars["width_b"], width=15)
        entry_width.grid(row=row_idx, column=1, sticky='w', padx=5, pady=5) # 'w' ile sola yasla
        self.section_detail_widgets["lbl_width"] = lbl_width
        self.section_detail_widgets["entry_width"] = entry_width
        row_idx += 1

        # Yükseklik (h) - Dikdörtgen için
        lbl_height = ttk.Label(detail_form_frame, text="Yükseklik h (mm):", style='Header.TLabel')
        lbl_height.grid(row=row_idx, column=0, sticky='w', padx=5, pady=5)
        entry_height = ui_components.create_content_entry(detail_form_frame, current_theme=self.theme, textvariable=self.section_detail_vars["height_h"], width=15)
        entry_height.grid(row=row_idx, column=1, sticky='w', padx=5, pady=5)
        self.section_detail_widgets["lbl_height"] = lbl_height
        self.section_detail_widgets["entry_height"] = entry_height
        row_idx += 1

        # Çap (D) - Dairesel için
        lbl_diameter = ttk.Label(detail_form_frame, text="Çap D (mm):", style='Header.TLabel')
        lbl_diameter.grid(row=row_idx, column=0, sticky='w', padx=5, pady=5)
        entry_diameter = ui_components.create_content_entry(detail_form_frame, current_theme=self.theme, textvariable=self.section_detail_vars["diameter_d"], width=15)
        entry_diameter.grid(row=row_idx, column=1, sticky='w', padx=5, pady=5)
        self.section_detail_widgets["lbl_diameter"] = lbl_diameter
        self.section_detail_widgets["entry_diameter"] = entry_diameter
        row_idx += 1

        # Form Butonları (Vazgeç, Kaydet)
        form_button_frame = tk.Frame(detail_frame, bg=self.theme['content_bg'])
        # Grid içinde sağ alta yerleştirme (detail_frame'in gridine göre)
        form_button_frame.grid(row=row_idx, column=0, columnspan=3, sticky='se', pady=10, padx=10)
        ttk.Button(form_button_frame, text="Vazgeç", style='TButton', command=self.clear_section_form).pack(side=tk.RIGHT, padx=5)
        ttk.Button(form_button_frame, text="Kaydet", style='TButton', command=self.save_section_from_form).pack(side=tk.RIGHT, padx=5)

        # --- Başlangıç Durumu ---
        self.clear_section_form() # Formu temizle ve başlangıç durumuna getir
        self.update_section_listbox() # Listbox'ı doldur
        self._update_section_material_combobox() # Malzeme listesini doldur
        self.on_section_type_change() # Boyut alanlarını ayarla

    def clear_section_form(self):
        """Kesit detay formunu temizler ve başlangıç durumuna getirir."""
        if not self.section_detail_vars: return # Henüz oluşturulmadıysa çık

        self.section_detail_vars["user_name"].set("")
        self.section_detail_vars["type"].set("Dikdörtgen") # Varsayılana dön
        self.section_detail_vars["material_name"].set("")
        self.section_detail_vars["width_b"].set(0.0)
        self.section_detail_vars["height_h"].set(0.0)
        self.section_detail_vars["diameter_d"].set(0.0)

        # Listbox seçimini temizle
        if self.section_listbox_ref:
            selection = self.section_listbox_ref.curselection()
            if selection:
                self.section_listbox_ref.selection_clear(selection[0])

        # Widget durumlarını ayarla (Tip değişikliğini tetikle)
        self.on_section_type_change()
        # Malzeme combobox'ını güncelle (belki yeni malzeme eklenmiştir)
        self._update_section_material_combobox()
        # İsim girişini etkinleştir
        if "entry_name" in self.section_detail_widgets:
           self.section_detail_widgets["entry_name"].config(state=tk.NORMAL)


    def update_section_listbox(self):
        """Aktif profilin kesitlerini Listbox'ta gösterir."""
        if not self.section_listbox_ref or not self.main_app.current_profile_name:
            return # Listbox veya profil yoksa çık

        self.section_listbox_ref.delete(0, tk.END) # Listeyi temizle
        profile_data = self.main_app.profiles_data.get(self.main_app.current_profile_name)

        if profile_data and "sections" in profile_data:
            sections = profile_data["sections"]
            # İsimlere göre sırala (küçük/büyük harf duyarsız)
            sections.sort(key=lambda x: x.get("user_name", "").lower())
            for section in sections:
                # Listbox'ta gösterilecek metin (Tip ve Boyutlar)
                display_name = section.get("user_name", "İsimsiz")
                sec_type = section.get("type", "?")
                dims = section.get("dimensions", {})
                dim_str = ""
                if sec_type == "Dikdörtgen":
                    b = dims.get('b', 0); h = dims.get('h', 0)
                    dim_str = f"b/h={b:.0f}/{h:.0f}"
                elif sec_type == "Dairesel":
                    d = dims.get('D', 0)
                    dim_str = f"D={d:.0f}"
                # TODO: Diğer tipler için gösterim eklenebilir
                self.section_listbox_ref.insert(tk.END, f"{display_name} ({sec_type}, {dim_str})")


    def on_section_type_change(self):
        """Kesit tipi değiştiğinde boyut giriş alanlarını gösterir/gizler."""
        if not self.section_detail_widgets: return # Widgetlar henüz yoksa çık

        sec_type = self.section_detail_vars.get("type", tk.StringVar()).get()
        is_rectangular = (sec_type == "Dikdörtgen")
        is_circular = (sec_type == "Dairesel")

        # Dikdörtgen boyutları
        for w_name in ["lbl_width", "entry_width", "lbl_height", "entry_height"]:
            widget = self.section_detail_widgets.get(w_name)
            if widget:
                try:
                    if is_rectangular: widget.grid()
                    else: widget.grid_remove()
                except tk.TclError: pass # Zaten gizliyse hata vermesin

        # Dairesel boyutları
        for w_name in ["lbl_diameter", "entry_diameter"]:
            widget = self.section_detail_widgets.get(w_name)
            if widget:
                try:
                    if is_circular: widget.grid()
                    else: widget.grid_remove()
                except tk.TclError: pass

        # TODO: Diğer kesit tipleri için alanlar eklendiğinde burası genişletilmeli


    def load_selected_section_to_form(self):
        """Listbox'tan seçilen kesitin bilgilerini forma yükler."""
        if not self.section_listbox_ref or not self.main_app.current_profile_name: return
        selection = self.section_listbox_ref.curselection()
        if not selection: return # Seçim yoksa çık

        selected_index = selection[0]
        profile_data = self.main_app.profiles_data.get(self.main_app.current_profile_name)

        if profile_data and "sections" in profile_data:
            sections = profile_data["sections"]
             # Listbox sıralaması ile veri sıralaması aynı olmalı (update_section_listbox'a göre)
            sections.sort(key=lambda x: x.get("user_name", "").lower())
            if 0 <= selected_index < len(sections):
                section_data = sections[selected_index]

                self.section_detail_vars["user_name"].set(section_data.get("user_name", ""))
                self.section_detail_vars["type"].set(section_data.get("type", "Dikdörtgen"))
                self.section_detail_vars["material_name"].set(section_data.get("material_name", ""))

                dims = section_data.get("dimensions", {})
                self.section_detail_vars["width_b"].set(dims.get("b", 0.0))
                self.section_detail_vars["height_h"].set(dims.get("h", 0.0))
                self.section_detail_vars["diameter_d"].set(dims.get("D", 0.0))

                # Widget durumlarını güncelle
                self.on_section_type_change()
                # Malzeme combobox'ını güncelle ve seçili değeri ayarla
                self._update_section_material_combobox()
                 # İsim girişini düzenleme modunda devre dışı bırakmak isteyebiliriz
                 # ama yeniden adlandırma için açık kalsın. Silme/Ekleme adı kontrol edecek.
                # if "entry_name" in self.section_detail_widgets:
                #    self.section_detail_widgets["entry_name"].config(state=tk.DISABLED)

            else:
                messagebox.showerror("Hata", "Seçilen kesit verisi bulunamadı.", parent=self.main_app.root)
        else:
            messagebox.showerror("Hata", "Profil verisi veya kesitler bulunamadı.", parent=self.main_app.root)


    def save_section_from_form(self):
        """Formdaki bilgileri kullanarak kesiti profile kaydeder (yeni veya güncelleme)."""
        if not self.main_app.current_profile_name:
             messagebox.showerror("Hata", "Aktif profil bulunamadı.", parent=self.main_app.root)
             return

        user_name = self.section_detail_vars["user_name"].get().strip()
        if not user_name:
            messagebox.showerror("Hata", "Kesit adı boş olamaz.", parent=self.main_app.root)
            return

        sec_type = self.section_detail_vars["type"].get()
        material_name = self.section_detail_vars["material_name"].get()
        if not material_name or material_name == "Tanımlı Beton Yok":
             messagebox.showerror("Hata", "Lütfen geçerli bir beton malzeme seçin.", parent=self.main_app.root)
             return

        dimensions = {}
        try:
            if sec_type == "Dikdörtgen":
                b = self.section_detail_vars["width_b"].get()
                h = self.section_detail_vars["height_h"].get()
                if b <= 0 or h <= 0: raise ValueError("Boyutlar pozitif olmalı")
                dimensions = {"b": b, "h": h}
            elif sec_type == "Dairesel":
                d = self.section_detail_vars["diameter_d"].get()
                if d <= 0: raise ValueError("Çap pozitif olmalı")
                dimensions = {"D": d}
            # TODO: Diğer tipler için boyut alma eklenebilir
        except (tk.TclError, ValueError) as e:
             messagebox.showerror("Hata", f"Lütfen geçerli sayısal boyutlar girin.\n({e})", parent=self.main_app.root)
             return

        # Kaydedilecek yeni kesit verisi
        new_section_data = {
            "user_name": user_name,
            "type": sec_type,
            "material_name": material_name,
            "dimensions": dimensions
        }

        # Profil verisine erişim
        profile = self.main_app.profiles_data.setdefault(self.main_app.current_profile_name, config.DEFAULT_PROFILE_DATA.copy())
        sections = profile.setdefault("sections", [])

        # Düzenleme mi, yeni mi kontrolü
        original_name_if_editing = None
        selected_index = -1
        if self.section_listbox_ref:
            selection = self.section_listbox_ref.curselection()
            if selection:
                selected_index = selection[0]
                 # Sıralanmış listeye göre orijinal veriyi bulmamız lazım
                sections.sort(key=lambda x: x.get("user_name", "").lower()) # Tekrar sırala (güvenlik için)
                try:
                    original_name_if_editing = sections[selected_index].get("user_name")
                except IndexError:
                    selected_index = -1 # Hata olursa ekleme moduna geç

        # Aynı isimde başka kesit var mı? (Düzenleme yapılan hariç)
        found_existing_index = -1
        for i, sec in enumerate(sections):
            if sec.get("user_name") == user_name and user_name != original_name_if_editing:
                found_existing_index = i
                break

        if found_existing_index != -1:
             messagebox.showerror("Hata", f"'{user_name}' adında başka bir kesit zaten var.", parent=self.main_app.root)
        else:
            is_update = (selected_index != -1 and original_name_if_editing is not None)
            if is_update:
                try:
                    sections[selected_index] = new_section_data
                    print(f"Section '{user_name}' updated.")
                except IndexError:
                     sections.append(new_section_data) # Güncelleme başarısız olursa ekle
                     print(f"Section '{user_name}' added (update failed).")
            else:
                 sections.append(new_section_data)
                 print(f"Section '{user_name}' added.")

            # Değişiklikleri kaydet
            utils.save_profiles()
            # Arayüzü güncelle
            self.update_section_listbox()
            self.clear_section_form()
            messagebox.showinfo("Başarılı", f"Kesit '{user_name}' başarıyla kaydedildi.", parent=self.main_app.root)


    def delete_selected_section(self):
        """Listbox'tan seçilen kesiti profilden siler."""
        if not self.section_listbox_ref or not self.main_app.current_profile_name: return
        selection = self.section_listbox_ref.curselection()
        if not selection:
             messagebox.showwarning("Kesit Seçilmedi", "Lütfen silinecek kesiti seçin.", parent=self.main_app.root)
             return

        selected_index = selection[0]
        profile = self.main_app.profiles_data.get(self.main_app.current_profile_name)

        if profile and "sections" in profile:
            sections = profile["sections"]
            sections.sort(key=lambda x: x.get("user_name", "").lower()) # Sırala

            if 0 <= selected_index < len(sections):
                section_to_delete = sections[selected_index]
                user_name_to_delete = section_to_delete.get("user_name", "Bilinmeyen")

                if messagebox.askyesno("Kesit Sil", f"'{user_name_to_delete}' kesitini silmek istediğinizden emin misiniz?", parent=self.main_app.root):
                    del sections[selected_index]
                    utils.save_profiles()
                    self.update_section_listbox()
                    self.clear_section_form()
                    messagebox.showinfo("Başarılı", f"'{user_name_to_delete}' kesiti silindi.", parent=self.main_app.root)
            else:
                 messagebox.showerror("Hata", "Silinecek kesit bulunamadı (indeks hatası).", parent=self.main_app.root)
        else:
             messagebox.showerror("Hata", "Kesit silinemedi (profil veya kesit verisi yok).", parent=self.main_app.root)
# ==================================
# SETTINGS FRAME SINIFI
# ==================================
class SettingsFrame(ttk.Frame):
    """Genel Ayarlar bölümünü gösteren çerçeve."""
    _frame_key = "Settings"
    def __init__(self, parent, main_app_instance, *args, **kwargs):
        super().__init__(parent, style='TFrame', *args, **kwargs)
        self.main_app = main_app_instance
        self.theme = self.main_app.current_theme
        self._create_widgets()

    def _create_widgets(self):
        for widget in self.winfo_children(): widget.destroy()
        label = ui_components.create_content_label(self, "Ayarlar", self.theme); label.pack(pady=20, padx=20, anchor='nw')
        theme_frame = tk.Frame(self, bg=self.theme['content_bg']); theme_frame.pack(pady=10, padx=40, anchor='w', fill='x')
        theme_label_text = ttk.Label(theme_frame, text="Uygulama Teması:", font=("Segoe UI", 13), background=self.theme['content_bg'], foreground=self.theme['text']); theme_label_text.pack(side=tk.LEFT, padx=(0, 10)) # Font: 13
        dark_button = ttk.Button(theme_frame, text="Siyah", style='TButton', command=lambda: self.main_app.apply_theme_and_save("dark")); dark_button.pack(side=tk.LEFT, padx=5)
        light_button = ttk.Button(theme_frame, text="Beyaz", style='TButton', command=lambda: self.main_app.apply_theme_and_save("light")); light_button.pack(side=tk.LEFT, padx=5)
        system_button = ttk.Button(theme_frame, text="Sistem", style='TButton', command=lambda: self.main_app.apply_theme_and_save("system")); system_button.pack(side=tk.LEFT, padx=5)
        version_label = ui_components.create_content_text(self, f"Version {config.APP_VERSION}", self.theme, size=10); version_label.pack(side=tk.BOTTOM, anchor='se', padx=20, pady=10) # Font: 10

