"""
Módulo de Extracción: PDFs y URLs.
"""

from .pdf import extraer_texto_de_pdf, extract_text_from_pdf
from .web import extraer_oferta_web, scrape_job_offer_url, extraer_oferta_web_detallado

__all__ = [
    "extraer_texto_de_pdf", "extract_text_from_pdf",
    "extraer_oferta_web", "scrape_job_offer_url", "extraer_oferta_web_detallado",
]
