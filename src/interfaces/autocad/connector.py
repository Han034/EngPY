import win32com.client
import pythoncom

class AutoCADConnector:
    """AutoCAD ile etkileşim için arabirimi sağlar."""
    
    def __init__(self):
        self.acad = None
    
    def connect(self):
        """AutoCAD'e bağlanır."""
        try:
            pythoncom.CoInitialize()
            self.acad = win32com.client.Dispatch("AutoCAD.Application")
            self.acad.Visible = True
            return True
        except Exception as e:
            self.acad = None
            raise Exception(f"AutoCAD bağlantı hatası: {str(e)}")
    
    def is_connected(self):
        """AutoCAD bağlantısının durumunu kontrol eder."""
        return self.acad is not None
    
    def ensure_connection(self):
        """Bağlantının olup olmadığını kontrol eder, yoksa bağlanmayı dener."""
        if not self.is_connected():
            return self.connect()
        return True
    
    def purge_drawing(self):
        """Çizimi temizler."""
        self.ensure_connection()
        # AutoCAD purge komutu burada
        self.acad.ActiveDocument.SendCommand("_-PURGE\nA\n*\nN\n ")
    
    def draw_line(self, start_point, end_point):
        """Çizgi çizer."""
        self.ensure_connection()
        
        # Points for AutoCAD
        start = self._make_point(start_point)
        end = self._make_point(end_point)
        
        # Çizgi oluştur
        return self.acad.ActiveDocument.ModelSpace.AddLine(start, end)
    
    def draw_rectangle(self, width, height, origin=(0,0,0)):
        """Dikdörtgen çizer."""
        self.ensure_connection()
        
        x, y, z = origin
        points = [
            (x, y, z),
            (x + width, y, z),
            (x + width, y + height, z),
            (x, y + height, z),
            (x, y, z)
        ]
        
        # Variant tipinde noktalar oluştur
        acad_points = [self._make_point(point) for point in points]
        
        # Poliçizgi oluştur
        return self.acad.ActiveDocument.ModelSpace.AddPolyline(acad_points)
    
    def _make_point(self, point_tuple):
        """AutoCAD için point variant oluşturur."""
        import win32com.client
        import pythoncom
        return win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, point_tuple)