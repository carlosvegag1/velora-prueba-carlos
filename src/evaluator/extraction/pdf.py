"""
Extracción de texto de archivos PDF.
Utiliza pypdf como librería principal.
"""

from typing import Optional
import io

try:
    from pypdf import PdfReader
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False


def extract_text_from_pdf(file_content: bytes) -> Optional[str]:
    """
    Extrae texto de un archivo PDF.
    
    Args:
        file_content: Contenido del archivo PDF como bytes
        
    Returns:
        Texto extraído del PDF, o None si hay error
        
    Raises:
        ImportError: Si pypdf no está instalado
        ValueError: Si hay error en la extracción
    """
    if not PYPDF_AVAILABLE:
        raise ImportError(
            "pypdf no está instalado. "
            "Instálalo con: pip install pypdf"
        )
    
    try:
        pdf_file = io.BytesIO(file_content)
        reader = PdfReader(pdf_file)
        text_parts = []
        
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
        
        return "\n\n".join(text_parts) if text_parts else None
        
    except Exception as e:
        raise ValueError(f"Error al extraer texto del PDF: {str(e)}")
