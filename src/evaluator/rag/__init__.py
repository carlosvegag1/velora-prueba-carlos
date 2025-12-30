"""
RAG (Retrieval Augmented Generation) para consultas inteligentes del historial.
"""

from .vectorstore import HistoryVectorStore
from .chatbot import HistoryChatbot

__all__ = [
    "HistoryVectorStore",
    "HistoryChatbot",
]

