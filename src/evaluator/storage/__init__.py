"""
Almacenamiento: Sistema de memoria por usuario optimizado para RAG.
"""

from .memory import (
    UserMemory,
    EnrichedEvaluation,
    create_enriched_evaluation,
    extract_job_title,
)

__all__ = [
    "UserMemory",
    "EnrichedEvaluation",
    "create_enriched_evaluation",
    "extract_job_title",
]
