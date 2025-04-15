# start.py
# Ana uygulamayı başlatan betik.

import tkinter as tk
from main_app import MainApp # Ana uygulama sınıfını import et

if __name__ == "__main__":
    # Ana Tkinter penceresini oluştur
    root = tk.Tk()
    # Ana uygulama sınıfından bir örnek oluştur (bu __init__ içinde her şeyi kuracak)
    app = MainApp(root)
    # Tkinter olay döngüsünü başlat
    root.mainloop()
