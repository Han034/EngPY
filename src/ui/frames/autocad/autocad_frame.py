import tkinter as tk
from tkinter import ttk
from ...components import buttons
from src.ui.frames.base_frame import BaseFrame
from src.interfaces.autocad.connector import AutoCADConnector

class AutoCADFrame(BaseFrame):
    """AutoCAD işlemleri için ana çerçeve."""
    
    def __init__(self, parent, main_app_instance, *args, **kwargs):
        self.current_page = None
        self.connector = AutoCADConnector()  # AutoCAD bağlantı sınıfı
        super().__init__(parent, main_app_instance, *args, **kwargs)
    
    def _create_widgets(self):
        """Ana widget'ları oluştur."""
        # Ana düzen
        self.main_container = ttk.Frame(self)
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # Sub-sidebar (üst navigasyon)
        self.sub_sidebar = ttk.Frame(self.main_container)
        self.sub_sidebar.pack(fill=tk.X, side=tk.TOP)
        self._create_sub_sidebar()
        
        # İçerik alanı
        self.page_container = ttk.Frame(self.main_container)
        self.page_container.pack(fill=tk.BOTH, expand=True)
        
        # Varsayılan sayfayı göster
        self.show_home_page()
    
    def _create_sub_sidebar(self):
        """Navbar'ı oluştur."""
        # Ana Sayfa butonu
        btn_home = buttons.create_nav_button(
            self.sub_sidebar, "Ana Sayfa", self.theme,
            command=self.show_home_page
        )
        btn_home.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Test Alanı butonu
        btn_test = buttons.create_nav_button(
            self.sub_sidebar, "Test Alanı", self.theme,
            command=self.show_test_page
        )
        btn_test.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Çizim Temizle butonu
        btn_clean = buttons.create_nav_button(
            self.sub_sidebar, "Çizim Temizle", self.theme,
            command=self.clean_drawing
        )
        btn_clean.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Layer Yönetimi butonu
        btn_layers = buttons.create_nav_button(
            self.sub_sidebar, "Layer Yönetimi", self.theme,
            command=self.show_layer_page
        )
        btn_layers.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Blok İşlemleri butonu
        btn_blocks = buttons.create_nav_button(
            self.sub_sidebar, "Blok İşlemleri", self.theme, 
            command=self.show_block_page
        )
        btn_blocks.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Schema butonu
        btn_schema = buttons.create_nav_button(
            self.sub_sidebar, "Schema", self.theme,
            command=self.show_schema_page
        )
        btn_schema.pack(side=tk.LEFT, padx=5, pady=5)
    
    def _clear_page_container(self):
        """İçerik alanını temizle."""
        for widget in self.page_container.winfo_children():
            widget.destroy()
    
    def show_home_page(self):
        """Ana sayfayı göster."""
        from .home_page import HomePage
        self._clear_page_container()
        self.current_page = HomePage(self.page_container, self)
    
    def show_test_page(self):
        """Test alanını göster."""
        from .test_page import TestPage
        self._clear_page_container()
        self.current_page = TestPage(self.page_container, self)
    
    def show_layer_page(self):
        """Layer yönetimi sayfasını göster."""
        from .layer_page import LayerPage
        self._clear_page_container()
        self.current_page = LayerPage(self.page_container, self)
    
    def show_block_page(self):
        """Blok işlemleri sayfasını göster."""
        from .block_page import BlockPage
        self._clear_page_container()
        self.current_page = BlockPage(self.page_container, self)
    
    def show_schema_page(self):
        """Schema sayfasını göster."""
        from .schema_page import SchemaPage
        self._clear_page_container()
        self.current_page = SchemaPage(self.page_container, self)
    
    def clean_drawing(self):
        """AutoCAD çizimini temizle."""
        try:
            self.connector.purge_drawing()
            tk.messagebox.showinfo("Başarılı", "Çizim temizlendi.")
        except Exception as e:
            tk.messagebox.showerror("Hata", f"Çizim temizleme hatası: {str(e)}")