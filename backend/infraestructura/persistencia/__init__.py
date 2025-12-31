"""
Módulo de Persistencia: Almacenamiento de evaluaciones por usuario.
"""

from .memoria_usuario import (
    MemoriaUsuario, UserMemory,
    EvaluacionEnriquecida, EnrichedEvaluation,
    crear_evaluacion_enriquecida, create_enriched_evaluation,
    extraer_titulo_oferta, extract_job_title,
)

__all__ = [
    "MemoriaUsuario", "UserMemory",
    "EvaluacionEnriquecida", "EnrichedEvaluation",
    "crear_evaluacion_enriquecida", "create_enriched_evaluation",
    "extraer_titulo_oferta", "extract_job_title",
]
