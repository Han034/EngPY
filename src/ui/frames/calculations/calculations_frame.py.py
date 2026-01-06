import tkinter as tk
from tkinter import ttk
from ...components import buttons
from src.ui.frames.base_frame import BaseFrame

class CalculationsFrame(BaseFrame):
    """Hesaplamalar bölümü ana çerçevesi."""
    
    def __init__(self, parent, main_app_instance, *args, **kwargs):
        self.current_page = None
        super().__init__(parent, main_app_instance, *args, **kwargs)
    
    def _create_widgets(self):
        """Ana widget'ları oluştur."""
        # Ana düzen
        self.main_container = ttk.Frame(self)
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # Sol sidebar (yan navigasyon)
        self.side_nav = ttk.Frame(self.main_container)
        self.side_nav.pack(fill=tk.Y, side=tk.LEFT, padx=5, pady=5)
        self._create_side_nav()
        
        # İçerik alanı
        self.page_container = ttk.Frame(self.main_container)
        self.page_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Varsayılan sayfayı göster
        self.show_project_info_page()
    
    def _create_side_nav(self):
        """Yan navigasyon butonlarını oluştur."""
        nav_items = [
            ("Proje Bilgileri", self.show_project_info_page),
            ("Malzemeler", self.show_materials_page),
            ("Kesitler", self.show_sections_page),
            ("Tekil Eleman", self.show_element_page),
            ("Deprem Yükü", self.show_seismic_page),
            ("Profiller", self.show_profiles_page)
        ]
        
        for text, command in nav_items:
            btn = buttons.create_nav_button(
                self.side_nav, text, self.theme, command=command
            )
            btn.pack(fill=tk.X, padx=3, pady=3)
    
    def _clear_page_container(self):
        """İçerik alanını temizle."""
        for widget in self.page_container.winfo_children():
            widget.destroy()
    
    def show_project_info_page(self):
        """Proje bilgileri sayfasını göster."""
        from .project_info_page import ProjectInfoPage
        self._clear_page_container()
        self.current_page = ProjectInfoPage(self.page_container, self)
    
    def show_materials_page(self):
        """Malzemeler sayfasını göster."""
        from .materials_page import MaterialsPage
        self._clear_page_container()
        self.current_page = MaterialsPage(self.page_container, self)
    
    def show_sections_page(self):
        """Kesitler sayfasını göster."""
        from .sections_page import SectionsPage
        self._clear_page_container()
        self.current_page = SectionsPage(self.page_container, self)
    
    def show_element_page(self):
        """Tekil eleman sayfasını göster."""
        from .element_page import ElementPage
        self._clear_page_container()
        self.current_page = ElementPage(self.page_container, self)
    
    def show_seismic_page(self):
        """Deprem yükü sayfasını göster."""
        from .seismic_page import SeismicPage
        self._clear_page_container()
        self.current_page = SeismicPage(self.page_container, self)
    
    def show_profiles_page(self):
        """Profiller sayfasını göster."""
        from .profiles_page import ProfilesPage
        self._clear_page_container()
        self.current_page = ProfilesPage(self.page_container, self)