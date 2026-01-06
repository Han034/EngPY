import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
import sys

# UI bileşenleri
from src.ui.frames.panel.panel_frame import PanelFrame
from src.ui.frames.autocad.autocad_frame import AutoCADFrame
from src.ui.frames.calculations.calculations_frame import CalculationsFrame
from src.ui.frames.settings.settings_frame import SettingsFrame

# Yardımcı modüller
from src.utils.config import load_config, save_config

class MainApp(tk.Tk):
    """Ana uygulama sınıfı."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Başlık ve boyutlar
        self.title("EngPY - Mühendislik Yazılımı")
        self.geometry("1200x800")
        
        # Uygulama kapandığında ayarları kaydet
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Ayarları yükle
        self.settings = load_config("settings.json")
        self.theme = self.settings.get("theme", "default")
        
        # Fontlar
        self.heading_font = ("Segoe UI", 12, "bold")
        self.normal_font = ("Segoe UI", 10)
        
        # Tema uygula
        self._apply_theme()
        
        # Çerçeve yönetimi için sözlük
        self.frames = {}
        
        # Ana içerik bölümünü oluştur
        self._create_layout()
        
        # Profil veri yapısı
        self.profiles = self._load_profiles()
        
        # Aktif profil
        self.active_profile = self.profiles[0] if self.profiles else None
    
    def _apply_theme(self):
        """Temayı uygula."""
        style = ttk.Style()
        
        # Varsayılan tema (default)
        if self.theme == "default":
            style.configure(".", 
                           background="#f0f0f0",
                           foreground="#000000",
                           font=self.normal_font)
            
            # Buton stilleri
            style.configure("TButton", 
                           padding=5, 
                           relief="flat",
                           background="#e1e1e1")
            
            style.map("TButton",
                     background=[('active', '#d0d0d0')])
            
        # Koyu tema (dark)
        elif self.theme == "dark":
            style.configure(".", 
                           background="#333333",
                           foreground="#ffffff",
                           font=self.normal_font)
            
            # Buton stilleri
            style.configure("TButton", 
                           padding=5,
                           relief="flat", 
                           background="#555555",
                           foreground="#ffffff")
            
            style.map("TButton",
                     background=[('active', '#777777')])
    
    def _create_layout(self):
        """Ana uygulama düzenini oluştur."""
        # Ana çerçeve
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Üst çubuk - logo ve ana menü
        self.top_bar = ttk.Frame(self.main_frame)
        self.top_bar.pack(fill=tk.X, side=tk.TOP)
        
        # Logo
        self.logo_label = ttk.Label(self.top_bar, text="EngPY", 
                                   font=("Segoe UI", 16, "bold"))
        self.logo_label.pack(side=tk.LEFT, padx=10, pady=5)
        
        # Sol kenar çubuğu
        self.sidebar_frame = ttk.Frame(self.main_frame, width=200)
        self.sidebar_frame.pack(fill=tk.Y, side=tk.LEFT)
        
        # Ana içerik alanı
        self.content_frame = ttk.Frame(self.main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Sidebar butonları
        self._create_sidebar_buttons()
        
        # Varsayılan çerçeveyi göster
        self.show_frame("Panel")
    
    def _create_sidebar_buttons(self):
        """Sol kenar çubuğu butonlarını oluştur."""
        sidebar_buttons = [
            ("Panel", "Panel"),
            ("AutoCAD", "AutoCAD"),
            ("Hesaplamalar", "Calculations"),
            ("Ayarlar", "Settings")
        ]
        
        for text, frame_key in sidebar_buttons:
            btn = ttk.Button(
                self.sidebar_frame, 
                text=text, 
                command=lambda k=frame_key: self.show_frame(k)
            )
            btn.pack(fill=tk.X, padx=5, pady=5)
    
    def show_frame(self, frame_key):
        """Belirtilen çerçeveyi gösterir."""
        print(f"Showing frame: {frame_key}")
        
        # Mevcut çerçeveyi temizle
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Çerçeve daha önce oluşturulduysa yeniden kullan, değilse oluştur
        if frame_key not in self.frames:
            frame_class = self._get_frame_class(frame_key)
            new_frame = frame_class(self.content_frame, self)
            self.frames[frame_key] = new_frame
        
        # Çerçeveyi göster
        self.frames[frame_key].pack(fill=tk.BOTH, expand=True)
    
    def _get_frame_class(self, key):
        """Anahtar değerine göre çerçeve sınıfını döndürür."""
        frame_map = {
            "Panel": PanelFrame,
            "AutoCAD": AutoCADFrame,
            "Calculations": CalculationsFrame,
            "Settings": SettingsFrame
        }
        
        if key in frame_map:
            return frame_map[key]
        else:
            raise ValueError(f"Geçersiz çerçeve anahtarı: {key}")
    
    def _load_profiles(self):
        """Profil verilerini yükler."""
        try:
            with open("data/profiles/profiles.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # Varsayılan profil yapısı
            return [{
                "name": "Default Profile",
                "materials": [],
                "sections": [],
                "project_info": {}
            }]
    
    def save_profiles(self):
        """Profil verilerini kaydeder."""
        try:
            os.makedirs("data/profiles", exist_ok=True)
            with open("data/profiles/profiles.json", "w", encoding="utf-8") as f:
                json.dump(self.profiles, f, indent=4)
        except Exception as e:
            messagebox.showerror("Hata", f"Profil kaydedilemedi: {str(e)}")
    
    def on_close(self):
        """Uygulama kapatılırken çalışır."""
        # Ayarları kaydet
        save_config("settings.json", self.settings)
        print("Saving settings and exiting application...")
        self.destroy()