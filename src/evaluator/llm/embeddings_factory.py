"""
Factory para crear instancias de Embeddings por proveedor.
Arquitectura simplificada: Mapeo unívoco 1 proveedor = 1 modelo de embedding.

Mapeo de proveedores a modelos de embeddings:
- OpenAI → text-embedding-3-small (óptimo costo/rendimiento)
- Google → models/text-embedding-004 (última versión)

NOTA IMPORTANTE:
- Anthropic NO ofrece API de embeddings propia
- Cuando el LLM es Anthropic, usar OpenAI o Google como proveedor de embeddings
"""

import os
from typing import Optional, List
from langchain_core.embeddings import Embeddings

# OpenAI - siempre disponible
from langchain_openai import OpenAIEmbeddings

# Google - opcional
try:
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    GOOGLE_EMBEDDINGS_AVAILABLE = True
except ImportError:
    GOOGLE_EMBEDDINGS_AVAILABLE = False
    GoogleGenerativeAIEmbeddings = None


# =============================================================================
# MAPEO UNÍVOCO PROVEEDOR → EMBEDDING (1:1)
# Decisión técnica: cada proveedor tiene su modelo óptimo predefinido
# =============================================================================

EMBEDDING_PROVIDER_MAP = {
    "openai": "text-embedding-3-small",
    "google": "models/text-embedding-004",
}

# Proveedores que NO tienen embeddings propios
PROVIDERS_WITHOUT_EMBEDDINGS = ["anthropic"]


class EmbeddingFactory:
    """
    Factory para crear instancias de embeddings.
    Arquitectura simplificada: 1 proveedor = 1 modelo de embedding fijo.
    """
    
    @staticmethod
    def get_available_providers() -> List[str]:
        """
        Retorna lista de proveedores de embeddings disponibles.
        Excluye proveedores que no tienen API de embeddings (Anthropic).
        
        Returns:
            Lista de proveedores con embeddings disponibles
        """
        providers = ["openai"]  # OpenAI siempre disponible
        
        if GOOGLE_EMBEDDINGS_AVAILABLE:
            providers.append("google")
        
        return providers
    
    @staticmethod
    def get_embedding_model(provider: str) -> Optional[str]:
        """
        Retorna el modelo de embedding asignado al proveedor.
        Mapeo unívoco 1:1, sin opciones de selección.
        
        Args:
            provider: Proveedor de embeddings
            
        Returns:
            Nombre del modelo de embeddings o None si no soporta embeddings
        """
        return EMBEDDING_PROVIDER_MAP.get(provider.lower())
    
    @staticmethod
    def supports_embeddings(provider: str) -> bool:
        """
        Verifica si un proveedor soporta embeddings.
        
        Args:
            provider: Nombre del proveedor (openai, google, anthropic)
            
        Returns:
            True si el proveedor tiene API de embeddings, False si no
        """
        provider_lower = provider.lower()
        
        # Verificar si está en la lista de proveedores sin embeddings
        if provider_lower in PROVIDERS_WITHOUT_EMBEDDINGS:
            return False
        
        # Verificar si tiene modelo asignado y librería disponible
        if provider_lower == "google" and not GOOGLE_EMBEDDINGS_AVAILABLE:
            return False
        
        return provider_lower in EMBEDDING_PROVIDER_MAP
    
    @staticmethod
    def get_embedding_provider_message(llm_provider: str) -> Optional[str]:
        """
        Genera mensaje informativo cuando el proveedor LLM no soporta embeddings.
        
        Args:
            llm_provider: Proveedor del LLM seleccionado
            
        Returns:
            Mensaje informativo o None si el proveedor soporta embeddings
        """
        if EmbeddingFactory.supports_embeddings(llm_provider):
            return None
        
        if llm_provider.lower() == "anthropic":
            return (
                "⚠️ Anthropic no ofrece API de embeddings. "
                "Las funcionalidades de embeddings semánticos quedan deshabilitadas con este proveedor. "
                "Para usar embeddings, configura una API key de OpenAI o Google adicionalmente."
            )
        
        return f"El proveedor {llm_provider} no soporta embeddings."
    
    @staticmethod
    def create_embeddings(
        provider: str,
        api_key: Optional[str] = None
    ) -> Embeddings:
        """
        Crea una instancia de embeddings del proveedor especificado.
        Usa automáticamente el modelo óptimo predefinido para el proveedor.
        
        Args:
            provider: Proveedor de embeddings ('openai', 'google')
            api_key: API key del proveedor (opcional, puede estar en env)
            
        Returns:
            Instancia de Embeddings configurada
            
        Raises:
            ValueError: Si el proveedor no soporta embeddings
            ImportError: Si el proveedor no está instalado
        """
        provider_lower = provider.lower()
        
        # Validar que el proveedor soporta embeddings
        if not EmbeddingFactory.supports_embeddings(provider_lower):
            raise ValueError(
                f"El proveedor '{provider}' no soporta embeddings. "
                f"Proveedores disponibles: {EmbeddingFactory.get_available_providers()}"
            )
        
        # Obtener modelo asignado (mapeo 1:1)
        embedding_model = EMBEDDING_PROVIDER_MAP[provider_lower]
        
        if provider_lower == "openai":
            kwargs = {"model": embedding_model}
            
            # API key desde parámetro o variable de entorno
            key = api_key or os.getenv("OPENAI_API_KEY")
            if key:
                kwargs["openai_api_key"] = key
            
            return OpenAIEmbeddings(**kwargs)
        
        elif provider_lower == "google":
            if not GOOGLE_EMBEDDINGS_AVAILABLE:
                raise ImportError(
                    "langchain-google-genai no está instalado. "
                    "Instálalo con: pip install langchain-google-genai"
                )
            
            kwargs = {"model": embedding_model}
            
            # API key desde parámetro o variable de entorno
            key = api_key or os.getenv("GOOGLE_API_KEY")
            if key:
                kwargs["google_api_key"] = key
            
            return GoogleGenerativeAIEmbeddings(**kwargs)
        
        else:
            raise ValueError(
                f"Proveedor de embeddings no válido: {provider}. "
                f"Proveedores disponibles: {EmbeddingFactory.get_available_providers()}"
            )
    
    @staticmethod
    def validate_api_key(provider: str, api_key: Optional[str] = None) -> bool:
        """
        Valida si hay API key disponible para un proveedor de embeddings.
        
        Args:
            provider: Proveedor de embeddings
            api_key: API key opcional
            
        Returns:
            True si hay API key disponible
        """
        provider_lower = provider.lower()
        
        # Proveedores sin embeddings retornan False
        if provider_lower in PROVIDERS_WITHOUT_EMBEDDINGS:
            return False
        
        if provider_lower == "openai":
            return bool(api_key or os.getenv("OPENAI_API_KEY"))
        elif provider_lower == "google":
            return bool(api_key or os.getenv("GOOGLE_API_KEY"))
        else:
            return False
    
    @staticmethod
    def get_fallback_provider(exclude_provider: Optional[str] = None) -> Optional[str]:
        """
        Retorna un proveedor de embeddings con API key disponible.
        Útil como fallback cuando el proveedor principal no soporta embeddings.
        
        Args:
            exclude_provider: Proveedor a excluir de la búsqueda (ej: anthropic)
            
        Returns:
            Nombre del proveedor con embeddings o None si ninguno tiene API key
        """
        for provider in EmbeddingFactory.get_available_providers():
            if exclude_provider and provider.lower() == exclude_provider.lower():
                continue
            if EmbeddingFactory.validate_api_key(provider):
                return provider
        return None
