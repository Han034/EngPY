import sys
import os
from pathlib import Path

def main():
    """Uygulamayı başlatır."""
    # Proje kök dizinini belirle
    project_root = Path(__file__).parent.parent.parent
    
    # PYTHONPATH'e ekle
    sys.path.insert(0, str(project_root))
    
    # Artık src modülünü içe aktarabiliriz
    from src.app.main_app import MainApp
    
    app = MainApp()
    app.mainloop()

if __name__ == "__main__":
    main()