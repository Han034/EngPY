import tkinter as tk
from tkinter import ttk, messagebox

class SchemaPage(ttk.Frame):
    """AutoCAD şema oluşturma sayfası."""
    
    def __init__(self, parent, autocad_frame):
        super().__init__(parent)
        self.parent = parent
        self.autocad_frame = autocad_frame
        self.connector = autocad_frame.connector
        self.main_app = autocad_frame.main_app
        self.theme = self.main_app.theme
        
        self.param_entries = {}
        self._create_widgets()
        self.pack(fill=tk.BOTH, expand=True)
    
    def _create_widgets(self):
        """Widget'ları oluştur."""
        # Başlık etiketi
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=tk.X, padx=15, pady=(10, 15))
        
        ttk.Label(header_frame, text="Hazır Şema Çizimi", 
                 font=self.main_app.heading_font).pack(side=tk.LEFT)
        
        # Ana içerik çerçevesi
        main_content = ttk.Frame(self)
        main_content.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
        
        # Sol taraf - Şema türü seçimi
        left_frame = ttk.LabelFrame(main_content, text="Şema Türü")
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10), pady=5)
        
        # Şema türleri
        self.schema_types = [
            "Dikdörtgen",
            "Daire",
            "Çokgen",
            "Grid Sistemi",
            "Kolon Yerleşimi",
            "Kiriş Yerleşimi"
        ]
        
        self.selected_schema = tk.StringVar(value=self.schema_types[0])
        for schema_type in self.schema_types:
            rb = ttk.Radiobutton(left_frame, text=schema_type, value=schema_type, 
                                variable=self.selected_schema, command=self._update_params)
            rb.pack(anchor=tk.W, padx=10, pady=5)
        
        # Sağ taraf - Parametreler ve önizleme
        right_frame = ttk.Frame(main_content)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Parametreler çerçevesi
        self.params_frame = ttk.LabelFrame(right_frame, text="Parametreler")
        self.params_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Önizleme çerçevesi
        preview_frame = ttk.LabelFrame(right_frame, text="Önizleme")
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Önizleme için canvas
        self.preview_canvas = tk.Canvas(preview_frame, bg="white", width=300, height=200)
        self.preview_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Butonlar çerçevesi
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, padx=15, pady=10)
        
        # Önizleme ve çizim butonları
        preview_btn = ttk.Button(button_frame, text="Önizle", command=self._preview)
        preview_btn.pack(side=tk.LEFT, padx=5)
        
        draw_btn = ttk.Button(button_frame, text="AutoCAD'de Çiz", command=self._draw)
        draw_btn.pack(side=tk.LEFT, padx=5)
        
        # İlk şema türünün parametrelerini göster
        self._update_params()
    
    def _update_params(self):
        """Seçilen şema türüne göre parametre alanlarını güncelle."""
        for widget in self.params_frame.winfo_children():
            widget.destroy()
            
        self.param_entries.clear()
        schema_type = self.selected_schema.get()
        
        # Şema türüne göre uygun parametre alanlarını ekle
        if schema_type == "Dikdörtgen":
            self._add_param("width", "Genişlik (mm):", 0, 0, default="1000")
            self._add_param("height", "Yükseklik (mm):", 1, 0, default="500")
        
        elif schema_type == "Daire":
            self._add_param("radius", "Yarıçap (mm):", 0, 0, default="250")
        
        elif schema_type == "Çokgen":
            self._add_param("sides", "Kenar Sayısı:", 0, 0, default="6")
            self._add_param("radius", "Dış Yarıçap (mm):", 1, 0, default="200")
        
        # Diğer şema türleri...
        
        # Önizleme güncelle
        self._preview()
    
    def _add_param(self, key, label_text, row, col, default=""):
        """Parametreler çerçevesine yeni bir parametre alanı ekler."""
        ttk.Label(self.params_frame, text=label_text).grid(row=row, column=col, sticky="w", padx=5, pady=5)
        entry = ttk.Entry(self.params_frame)
        entry.grid(row=row, column=col+1, sticky="we", padx=5, pady=5)
        entry.insert(0, default)
        self.param_entries[key] = entry
    
    def _preview(self):
        """Seçilen şema türünü ve parametreleri önizle."""
        # Önizleme kodu...
        pass
    
    def _draw(self):
        """Seçilen şemayı AutoCAD'de çiz."""
        try:
            # Bağlantı kontrolü
            if not self.connector.is_connected():
                if not self.connector.connect():
                    messagebox.showerror("Hata", "AutoCAD bağlantısı kurulamadı.")
                    return
            
            schema_type = self.selected_schema.get()
            
            # Şema türüne göre çizim fonksiyonunu çağır
            if schema_type == "Dikdörtgen":
                width = float(self.param_entries["width"].get())
                height = float(self.param_entries["height"].get())
                self.connector.draw_rectangle(width, height)
                
            elif schema_type == "Daire":
                # Daire çizim kodu
                pass
                
            # Diğer şemalar...
            
            # Zoom
            self.connector.acad.ActiveDocument.Utility.Zoom("E")
            messagebox.showinfo("Başarılı", f"{schema_type} çizimi AutoCAD'e gönderildi.")
            
        except Exception as e:
            messagebox.showerror("Hata", f"AutoCAD'de çizim yapılırken hata oluştu: {str(e)}")