"""
Capa de Núcleo: Lógica de negocio central del sistema Velora.
"""

from .analisis import AnalizadorFase1, Phase1Analyzer
from .entrevista import EntrevistadorFase2, Phase2Interviewer, AgenticInterviewer
from .historial import (
    AlmacenVectorialHistorial, HistoryVectorStore,
    AsistenteHistorial, HistoryChatbot,
    normalizar_texto_para_embedding
)

__all__ = [
    "AnalizadorFase1", "Phase1Analyzer",
    "EntrevistadorFase2", "Phase2Interviewer", "AgenticInterviewer",
    "AlmacenVectorialHistorial", "HistoryVectorStore",
    "AsistenteHistorial", "HistoryChatbot",
    "normalizar_texto_para_embedding",
]
