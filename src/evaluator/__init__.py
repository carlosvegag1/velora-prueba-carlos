"""
Sistema de Evaluación de Candidatos con LangChain
Utiliza Structured Output para garantizar respuestas válidas del LLM.
Incluye RAG para consultas inteligentes del historial.
"""

from .core import CandidateEvaluator, Phase1Analyzer, AgenticInterviewer
from .models import (
    Requirement,
    RequirementType,
    ConfidenceLevel,
    Phase1Result,
    InterviewQuestion,
    InterviewResponse,
    EvaluationResult,
    # Modelos para Structured Output
    RequirementsExtractionResponse,
    CVMatchingResponse,
    QuestionsGenerationResponse,
    ResponseEvaluation,
)
from .llm import LLMFactory, EmbeddingFactory
from .storage import UserMemory, EnrichedEvaluation, create_enriched_evaluation
from .extraction import extract_text_from_pdf, scrape_job_offer_url
from .rag import HistoryVectorStore, HistoryChatbot

__version__ = "2.0.0"  # Agente conversacional con streaming real
__all__ = [
    # Componentes principales
    "CandidateEvaluator",
    "Phase1Analyzer",
    "AgenticInterviewer",
    # Modelos de datos
    "Requirement",
    "RequirementType",
    "ConfidenceLevel",
    "Phase1Result",
    "InterviewQuestion",
    "InterviewResponse",
    "EvaluationResult",
    # Modelos para Structured Output
    "RequirementsExtractionResponse",
    "CVMatchingResponse",
    "QuestionsGenerationResponse",
    "ResponseEvaluation",
    # Almacenamiento
    "UserMemory",
    "EnrichedEvaluation",
    "create_enriched_evaluation",
    # RAG
    "HistoryVectorStore",
    "HistoryChatbot",
    # Factories
    "LLMFactory",
    "EmbeddingFactory",
    # Utilidades
    "extract_text_from_pdf",
    "scrape_job_offer_url",
]
