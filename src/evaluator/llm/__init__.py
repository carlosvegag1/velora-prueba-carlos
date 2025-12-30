"""
Gestión de LLMs y Embeddings: Factories, Prompts, Hiperparámetros y LangSmith.
Arquitectura desacoplada para multi-proveedor.
"""

from .factory import (
    LLMFactory,
    configure_langsmith,
    get_langsmith_client,
    is_langsmith_enabled
)
from .embeddings_factory import EmbeddingFactory
from .hyperparameters import (
    LLMHyperparameters,
    HyperparametersConfig,
    PHASE1_EXTRACTION,
    PHASE1_MATCHING,
    PHASE2_INTERVIEW,
    PHASE2_EVALUATION,
    RAG_CHATBOT,
)
from . import prompts

__all__ = [
    # LLM Factory
    "LLMFactory",
    # Embedding Factory
    "EmbeddingFactory",
    # Hiperparámetros
    "LLMHyperparameters",
    "HyperparametersConfig",
    "PHASE1_EXTRACTION",
    "PHASE1_MATCHING",
    "PHASE2_INTERVIEW",
    "PHASE2_EVALUATION",
    "RAG_CHATBOT",
    # LangSmith
    "configure_langsmith",
    "get_langsmith_client",
    "is_langsmith_enabled",
    # Prompts
    "prompts",
]

