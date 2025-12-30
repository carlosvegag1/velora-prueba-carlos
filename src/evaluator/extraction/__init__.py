"""
Extracción de datos: PDFs y URLs.
"""

from .pdf import extract_text_from_pdf
from .url import scrape_job_offer_url

__all__ = [
    "extract_text_from_pdf",
    "scrape_job_offer_url",
]

