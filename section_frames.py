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
    print("Warning: 'pyautocad' library not found. AutoCAD interaction will be disabled. Install with 'pip install pyautocad'")


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

        label = ui_components.create_content_label(self, "Panel", self.theme) # Font: 20 bold
        label.pack(pady=20, padx=20, anchor='nw')

        dashboard_main_frame = tk.Frame(self, bg=self.theme['content_bg'])
        dashboard_main_frame.pack(pady=10, padx=20, fill='both', expand=True)

        # Text area font boyutu
        text_font_size = 13
        text_area = tk.Text(dashboard_main_frame, height=10, width=50, relief='flat', bd=1,
                            font=("Segoe UI", text_font_size),
                            bg=self.theme['text_area_bg'],
                            fg=self.theme['text_area_fg'],
                            insertbackground=self.theme['entry_insert'],
                            highlightthickness=1,
                            highlightbackground=self.theme['text_area_highlight'],
                            highlightcolor=self.theme['button_bg'])
        text_area.pack(side=tk.TOP, fill='both', expand=True)

        text_area.config(state=tk.NORMAL)
        text_area.delete('1.0', tk.END)
        # Durum mesajını ve yenileme callback'ini main_app'ten al
        text_area.insert(tk.END, f"AutoCAD Durumu: {self.main_app.autocad_status_message}\n\n")
        text_area.insert(tk.END, "Uygulama durumu ve hızlı bilgiler burada gösterilecek...\n")
        text_area.config(state=tk.DISABLED)

        # Yenileme butonu main_app'teki metodu çağıracak
        refresh_button = ui_components.create_content_button(dashboard_main_frame, "Yenile", self.theme,
                                    command=self.main_app.refresh_autocad_status_and_view, style_key='TButton') # Font: 15
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
        self.current_page_frame = None
        self.connected_doc_name = self.main_app.connected_autocad_doc_name
        self.selected_area_points = None
        self.shape_buttons_references = {}
        self.osnap_vars = {}
        self._create_widgets() # Ana widget'ları (alt menü gibi) oluştur
        self.show_autocad_home() # Başlangıçta ana sayfayı göster

    def _create_widgets(self):
        # Ana widget'lar burada oluşturulabilir, örneğin alt menü
        self._create_autocad_sub_sidebar()
        # Sayfa içeriği için bir konteyner
        self.page_container = tk.Frame(self, bg=self.theme['content_bg'])
        self.page_container.pack(expand=True, fill='both', padx=10, pady=5)


    def _create_autocad_sub_sidebar(self):
        """AutoCAD bölümü için yatay alt menüyü oluşturur."""
        if self.sub_sidebar: self.sub_sidebar.destroy()

        self.sub_sidebar = tk.Frame(self, height=60, bg=self.theme['sub_sidebar_bg'])
        self.sub_sidebar.pack(side=tk.TOP, fill=tk.X, pady=(0, 10)); self.sub_sidebar.pack_propagate(False)

        home_button = ui_components.create_content_button(self.sub_sidebar, "Ana Sayfa", self.theme, command=self.show_autocad_home, style_key='Sub.TButton'); home_button.pack(side=tk.LEFT, padx=10, pady=5)
        test_button = ui_components.create_content_button(self.sub_sidebar, "Test Alanı", self.theme, command=self.show_autocad_test_area, style_key='Sub.TButton'); test_button.pack(side=tk.LEFT, padx=10, pady=5)
        btn1 = ui_components.create_content_button(self.sub_sidebar, "Çizim Temizle", self.theme, style_key='Sub.TButton', command=lambda: print("TODO: Purge")); btn1.pack(side=tk.LEFT, padx=10, pady=5)
        btn2 = ui_components.create_content_button(self.sub_sidebar, "Layer Yönetimi", self.theme, style_key='Sub.TButton', command=lambda: print("TODO: Layer")); btn2.pack(side=tk.LEFT, padx=10, pady=5)
        btn3 = ui_components.create_content_button(self.sub_sidebar, "Blok İşlemleri", self.theme, style_key='Sub.TButton', command=lambda: print("TODO: Block")); btn3.pack(side=tk.LEFT, padx=10, pady=5)

    def _clear_page_container(self):
        """Sayfa konteynerini temizler."""
        if self.current_page_frame:
             self.current_page_frame.destroy()
        # Yeni bir çerçeve oluştur ve paketle
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

        settings_header_label = ttk.Label(settings_area_frame, text="Çalışma Alanı Ayarları", style='Header.TLabel')
        settings_header_label.pack(anchor='w', pady=(0, 5))
        separator = ttk.Separator(settings_area_frame, orient='horizontal'); separator.pack(fill='x', anchor='w', pady=(0, 15))

        grid_frame = tk.Frame(settings_area_frame, bg=self.theme['content_bg']); grid_frame.pack(anchor='w', pady=5)
        grid_label = ttk.Label(grid_frame, text="Görünüm:", style='Header.TLabel'); grid_label.pack(side=tk.LEFT, padx=(0, 10))
        grid_var = tk.IntVar()
        saved_grid_mode = 0 # TODO: Profilden oku
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

        if self.connected_doc_name: file_text = f"Bağlı Dosya: {self.connected_doc_name}"
        else: file_text = "Bağlı Dosya: Yok"
        doc_name_label = ui_components.create_content_text(self.current_page_frame, file_text, self.theme, size=11);
        doc_name_label.pack(side=tk.BOTTOM, anchor='se', padx=10, pady=5)

    def _toggle_grid_mode(self, variable):
        autocad_interface.set_autocad_variable("GRIDMODE", variable.get())
    def _update_osmode(self):
        new_osmode_value = 0
        for bit_value, var in self.osnap_vars.items():
            if var.get() == 1: new_osmode_value |= bit_value
        autocad_interface.set_autocad_variable("OSMODE", new_osmode_value)

    def _select_area_in_autocad(self, result_text_widget, shape_buttons):
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
            for btn in shape_buttons.values():
                 if btn: btn.configure(state=button_state)
            utils.bring_window_to_front()

    def _draw_shape_in_area(self, shape_type, result_text_widget):
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
        self._clear_page_container(); self._create_autocad_sub_sidebar()
        is_connected = (self.connected_doc_name is not None); control_state = tk.NORMAL if is_connected else tk.DISABLED
        shape_button_state = tk.NORMAL if self.selected_area_points else tk.DISABLED

        test_main_frame = tk.Frame(self.current_page_frame, bg=self.theme['content_bg']);
        test_main_frame.pack(pady=15, padx=15, fill='both', expand=True, anchor='nw')

        label = ui_components.create_content_label(test_main_frame, "AutoCAD Test Alanı", self.theme); label.pack(pady=10, padx=0, anchor='nw')
        button_area_frame = tk.Frame(test_main_frame, bg=self.theme['content_bg']); button_area_frame.pack(pady=5, anchor='w')
        result_text = tk.Text(test_main_frame, height=10, width=50, relief='flat', bd=1, font=("Segoe UI", 12), bg=self.theme['text_area_bg'], fg=self.theme['text_area_fg'], insertbackground=self.theme['entry_insert'], highlightthickness=1, highlightbackground=self.theme['text_area_highlight'], highlightcolor=self.theme['button_bg'], state=tk.DISABLED); result_text.pack(side=tk.TOP, fill='both', expand=True, pady=(10, 10))
        self.shape_buttons_references = {}
        select_button = ttk.Button(button_area_frame, text="Alan Seç (4 Nokta)", style='TButton', command=lambda rt=result_text, sb=self.shape_buttons_references: self._select_area_in_autocad(rt, sb), state=control_state); select_button.pack(side=tk.LEFT, anchor='w', padx=(0,10))
        square_button = ttk.Button(button_area_frame, text="Kare", style='TButton', command=lambda rt=result_text: self._draw_shape_in_area('kare', rt), state=shape_button_state); square_button.pack(side=tk.LEFT, anchor='w', padx=5); self.shape_buttons_references['kare'] = square_button
        triangle_button = ttk.Button(button_area_frame, text="Üçgen", style='TButton', command=lambda rt=result_text: self._draw_shape_in_area('üçgen', rt), state=shape_button_state); triangle_button.pack(side=tk.LEFT, anchor='w', padx=5); self.shape_buttons_references['üçgen'] = triangle_button
        circle_button = ttk.Button(button_area_frame, text="Daire", style='TButton', command=lambda rt=result_text: self._draw_shape_in_area('daire', rt), state=shape_button_state); circle_button.pack(side=tk.LEFT, anchor='w', padx=5); self.shape_buttons_references['daire'] = circle_button

        if self.connected_doc_name: file_text = f"Bağlı Dosya: {self.connected_doc_name}"
        else: file_text = "Bağlı Dosya: Yok"
        doc_name_label = ui_components.create_content_text(test_main_frame, file_text, self.theme, size=11);
        doc_name_label.pack(side=tk.BOTTOM, anchor='se', padx=10, pady=5)


# ==================================
# CALCULATIONS FRAME SINIFI
# ==================================
# (Kod aynı kaldı)
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

    def _create_widgets(self):
        self.sub_sidebar = self._create_calculations_sub_sidebar(self)
        self.page_container = tk.Frame(self, bg=self.theme['content_bg'])
        self.page_container.pack(expand=True, fill='both', padx=10, pady=10)

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

