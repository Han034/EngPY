# autocad_interface.py
# AutoCAD ile etkileşim kurmak için fonksiyonları içerir.

import sys
try:
    from pyautocad import Autocad, APoint
except ImportError:
    Autocad = None
    APoint = None
    print("Warning: 'pyautocad' library not found. AutoCAD interaction will be disabled. Install with 'pip install pyautocad'")

# --- Global Değişkenler (Bu modül içinde geçici) ---
# TODO: Sınıf yapısında bu global değişkenler yerine sınıf özellikleri kullanılacak
acad_instance = None
connected_autocad_doc_name = None

# --- Bağlantı ve Temel İşlemler ---
def get_acad_instance():
    """Çalışan AutoCAD örneğini döndürür, yoksa None döndürür."""
    global acad_instance
    if not Autocad or sys.platform != "win32":
        acad_instance = None
        return None
    try:
        # Bağlantıyı test etmek için basit bir özellik okuması yapılabilir
        if acad_instance and acad_instance.doc:
            _ = acad_instance.doc.Name # Bağlantı hala geçerli mi?
            return acad_instance
        # Yeni bağlantı dene
        print("Attempting to connect to AutoCAD...")
        acad_instance = Autocad(create_if_not_exists=False)
        print("Connected to AutoCAD instance.")
        return acad_instance
    except Exception as e:
        print(f"Failed to get/verify AutoCAD instance: {e}")
        acad_instance = None
        return None

def check_autocad_connection():
    """Çalışan bir AutoCAD örneği olup olmadığını kontrol eder ve durumu döndürür."""
    global connected_autocad_doc_name, acad_instance
    acad = get_acad_instance() # Önce bağlantıyı almayı dene/yenile
    if acad:
        try:
            doc_name = acad.doc.Name # Doküman adını almayı dene
            connected_autocad_doc_name = doc_name
            print(f"ACAD connected. Doc: {doc_name}")
            return f"Bağlantı Başarılı (Doküman: {doc_name})"
        except Exception as e:
            # Bağlantı var ama doküman adı alınamıyor (örn. başlangıç ekranı)
            connected_autocad_doc_name = None
            print(f"ACAD Error (could not get doc name): {e}")
            return "Bağlantı kuruldu ancak aktif doküman yok/bilgisi alınamadı."
    else:
        # Bağlantı tamamen başarısız
        connected_autocad_doc_name = None
        if not Autocad: return "Bağlantı kontrolü için 'pyautocad' kütüphanesi gerekli."
        if sys.platform != "win32": return "AutoCAD bağlantı kontrolü sadece Windows'ta desteklenir."
        return "Çalışan AutoCAD bulunamadı veya bağlantı kurulamadı."

def get_autocad_variable(var_name, default_value):
    """AutoCAD'den bir sistem değişkenini okur."""
    acad = get_acad_instance()
    if acad:
        try:
            return acad.doc.GetVariable(var_name)
        except Exception as e:
            print(f"Error getting ACAD var '{var_name}': {e}")
            return default_value
    return default_value

def set_autocad_variable(var_name, value):
    """AutoCAD'de bir sistem değişkenini ayarlar."""
    acad = get_acad_instance()
    if acad:
        try:
            # Değişken tipini kontrol etmeye çalışalım
            current_val = acad.doc.GetVariable(var_name)
            if isinstance(current_val, float):
                value = float(value)
            elif isinstance(current_val, int):
                 # OSMODE gibi bit kodları için int olmalı
                 value = int(value)
            # Diğer tipler (string vb.) için doğrudan atama yapılabilir
            acad.doc.SetVariable(var_name, value)
            print(f"Set ACAD var '{var_name}' to {value}")
            return True
        except Exception as e:
            print(f"Error setting ACAD var '{var_name}': {e}")
            return False
    else:
        print("Cannot set ACAD var, not connected.")
        return False

# --- Çizim Fonksiyonları (Temel) ---
# Not: Bu fonksiyonlar APoint nesneleri veya koordinat demetleri alabilir.
# Hata yönetimi eklendi.

def draw_line(start_point, end_point):
    """Verilen iki nokta arasına çizgi çizer."""
    acad = get_acad_instance()
    if acad and APoint:
        try:
            p1 = APoint(start_point) # Gelen veriyi APoint'e çevir
            p2 = APoint(end_point)
            acad.ActiveDocument.ModelSpace.AddLine(p1, p2)
            print(f"Line drawn from {p1} to {p2}")
            return True
        except Exception as e:
            print(f"Error drawing line: {e}")
            return False
    return False

def draw_circle(center_point, radius):
    """Verilen merkez ve yarıçapta daire çizer."""
    acad = get_acad_instance()
    if acad and APoint:
        try:
            cp = APoint(center_point) # Merkezi APoint yap
            acad.ActiveDocument.ModelSpace.AddCircle(cp, float(radius)) # Yarıçapı float yap
            print(f"Circle drawn at {cp} with radius {radius}")
            return True
        except Exception as e:
            print(f"Error drawing circle: {e}")
            return False
    return False

def draw_lwpolyline(vertices):
    """Verilen köşe noktalarıyla hafif polyline çizer."""
    # vertices: [(x1, y1), (x2, y2), ...] veya [x1, y1, x2, y2, ...] formatında olabilir.
    # AddLwPolyline düzleştirilmiş liste bekler: (x1, y1, x2, y2, ...)
    acad = get_acad_instance()
    if acad:
        try:
            # Gelen verteks listesini düzleştir ve float yap
            flat_vertices = tuple(float(coord) for point in vertices for coord in point[:2]) # Sadece X,Y al
            acad.ActiveDocument.ModelSpace.AddLwPolyline(flat_vertices)
            print(f"LwPolyline drawn with {len(vertices)} vertices.")
            return True
        except Exception as e:
            print(f"Error drawing lwpolyline: {e}")
            return False
    return False

def prompt_user(message):
    """AutoCAD komut satırında kullanıcıya mesaj gösterir."""
    acad = get_acad_instance()
    if acad:
        try:
            acad.prompt(message)
            return True
        except Exception as e:
            print(f"Error prompting user: {e}")
            return False
    return False

def get_point_from_user(prompt_message="Nokta seçin:"):
    """Kullanıcıdan bir nokta seçmesini ister ve koordinatları döndürür."""
    acad = get_acad_instance()
    if acad:
        try:
            acad.prompt(prompt_message + "\n")
            point = acad.doc.Utility.GetPoint() # Hata fırlatabilir
            return tuple(point) # Tuple olarak döndür
        except Exception as e:
            print(f"Error getting point from user: {e}")
            return None # Hata veya iptal durumunda None döndür
    return None

