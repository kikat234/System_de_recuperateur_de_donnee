import io
from Modeles.SignatureFichiers import   FILE_SIGNATURES 
# Import optionnel de PIL pour l'aperçu d'images
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("⚠️  Pillow n'est pas installé. Les aperçus d'images ne seront pas disponibles.")
    print("   Pour installer : pip install Pillow")
class FilePreview:
    @staticmethod
    def can_preview(file_type):
        """Vérifie si un aperçu est possible"""
        if file_type in ['PNG', 'JPEG', 'GIF', 'BMP'] and not PIL_AVAILABLE:
            return False
        return file_type in ['PNG', 'JPEG', 'GIF', 'BMP', 'PDF']
    
    @staticmethod
    def generate_image_preview(file_data, max_size=(300, 300)):
        """Génère un aperçu d'image"""
        if not PIL_AVAILABLE:
            return None
        try:
            image = Image.open(io.BytesIO(file_data))
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(image)
        except Exception as e:
            return None
    
    @staticmethod
    def get_text_preview(file_data, max_chars=1000):
        """Génère un aperçu texte pour PDF"""
        try:
            # Extraction simple de texte ASCII du PDF
            text = file_data.decode('latin-1', errors='ignore')
            # Filtrer les caractères imprimables
            preview = ''.join(c for c in text if c.isprintable() or c in '\n\r\t')
            return preview[:max_chars]
        except:
            return "Aperçu non disponible"
