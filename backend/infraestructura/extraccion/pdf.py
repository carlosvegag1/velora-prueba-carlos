"""
Extracción de texto desde PDFs (rutas o bytes).
"""

import io
import logging
from typing import Union
from pypdf import PdfReader

logger = logging.getLogger(__name__)


def extraer_texto_de_pdf(fuente: Union[str, bytes]) -> str:
    """Extrae texto de PDF (ruta str o contenido bytes)."""
    try:
        if isinstance(fuente, bytes):
            archivo_pdf = io.BytesIO(fuente)
            reader = PdfReader(archivo_pdf)
        elif isinstance(fuente, str):
            reader = PdfReader(fuente)
        else:
            raise ValueError(f"Tipo no soportado: {type(fuente)}")
        
        texto = ""
        for pagina in reader.pages:
            texto_pagina = pagina.extract_text()
            if texto_pagina:
                texto += texto_pagina + "\n"
        
        resultado = texto.strip()
        if not resultado:
            logger.warning("PDF sin texto extraíble (puede ser escaneado)")
        return resultado
        
    except FileNotFoundError:
        logger.error(f"PDF no encontrado: {fuente}")
        raise
    except Exception as e:
        logger.error(f"Error extrayendo PDF: {e}")
        raise


extract_text_from_pdf = extraer_texto_de_pdf
