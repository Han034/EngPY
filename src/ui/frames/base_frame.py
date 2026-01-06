import tkinter as tk
from tkinter import ttk

class BaseFrame(ttk.Frame):
    """Tüm uygulama çerçeveleri için temel sınıf."""
    
    def __init__(self, parent, main_app_instance, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.parent = parent
        self.main_app = main_app_instance
        self.theme = self.main_app.theme
        
        # Her alt sınıfta çağrılacak
        self._create_widgets()
        
    def _create_widgets(self):
        """Alt sınıflar tarafından uygulanacak widget oluşturma metodu."""
        raise NotImplementedError("Alt sınıflar bu metodu uygulamalıdır.")
        
    def refresh(self):
        """Çerçevenin içeriğini yeniler."""
        # Alt sınıflar gerekirse bu metodu override edebilir
        pass