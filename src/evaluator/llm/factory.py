"""
Factory para crear instancias de LLM de diferentes proveedores.
Soporta OpenAI, Google (Gemini), y Anthropic (Claude).
Incluye configuración de LangSmith para trazabilidad.
"""

import os
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseChatModel

# Imports opcionales para otros proveedores
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False
    ChatGoogleGenerativeAI = None

try:
    from langchain_anthropic import ChatAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    ChatAnthropic = None

# LangSmith para trazabilidad
try:
    from langsmith import Client as LangSmithClient
    LANGSMITH_AVAILABLE = True
except ImportError:
    LANGSMITH_AVAILABLE = False
    LangSmithClient = None


# Variable global para el cliente de LangSmith
_langsmith_client: Optional["LangSmithClient"] = None
_langsmith_configured: bool = False


def configure_langsmith(project_name: str = "velora-evaluator") -> Optional["LangSmithClient"]:
    """
    Configura LangSmith para trazabilidad si hay API key disponible.
    
    Args:
        project_name: Nombre del proyecto en LangSmith
        
    Returns:
        Cliente de LangSmith si está configurado, None si no
    """
    global _langsmith_client, _langsmith_configured
    
    if _langsmith_configured:
        return _langsmith_client
    
    _langsmith_configured = True
    
    if not LANGSMITH_AVAILABLE:
        return None
    
    api_key = os.getenv("LANGSMITH_API_KEY")
    if not api_key:
        return None
    
    try:
        # Configurar variables de entorno para LangChain tracing
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_PROJECT"] = project_name
        
        # Crear cliente
        _langsmith_client = LangSmithClient()
        return _langsmith_client
    except Exception:
        return None


def get_langsmith_client() -> Optional["LangSmithClient"]:
    """
    Obtiene el cliente de LangSmith si está configurado.
    
    Returns:
        Cliente de LangSmith o None
    """
    global _langsmith_client
    
    if not _langsmith_configured:
        configure_langsmith()
    
    return _langsmith_client


def is_langsmith_enabled() -> bool:
    """
    Verifica si LangSmith está habilitado.
    
    Returns:
        True si LangSmith está configurado y disponible
    """
    return get_langsmith_client() is not None


class LLMFactory:
    """Factory para crear instancias de LLM de diferentes proveedores"""
    
    # Modelos disponibles por proveedor
    OPENAI_MODELS = [
        "gpt-5.2",
        "gpt-5.2-instant",
        "gpt-5.2-thinking",
        "gpt-4.1",
        "gpt-4o"
    ]

    GOOGLE_MODELS = [
        "gemini-3-pro",
        "gemini-3-pro-deepthink",
        "gemini-3-flash",
        "gemini-2.5-pro",
        "gemini-2.5-flash"
    ]

    ANTHROPIC_MODELS = [
        "claude-opus-4.5",
        "claude-sonnet-4.5",
        "claude-haiku-4.5",
        "claude-3.5-sonnet",
        "claude-3.5-haiku"
    ]


    @staticmethod
    def get_available_providers() -> list:
        """
        Obtiene la lista de proveedores disponibles (con librerías instaladas).
        
        Returns:
            Lista de proveedores disponibles
        """
        providers = ["openai"]  # OpenAI siempre está disponible
        
        if GOOGLE_AVAILABLE:
            providers.append("google")
        
        if ANTHROPIC_AVAILABLE:
            providers.append("anthropic")
        
        return providers
    
    @staticmethod
    def get_provider_from_model(model_name: str) -> str:
        """
        Determina el proveedor basándose en el nombre del modelo.
        
        Args:
            model_name: Nombre del modelo
            
        Returns:
            Nombre del proveedor: 'openai', 'google', o 'anthropic'
        """
        model_lower = model_name.lower()
        
        if model_lower.startswith("gpt") or "openai" in model_lower:
            return "openai"
        elif "gemini" in model_lower or model_lower.startswith("gemini"):
            return "google"
        elif "claude" in model_lower:
            return "anthropic"
        else:
            # Por defecto, asumir OpenAI
            return "openai"
    
    @staticmethod
    def create_llm(
        provider: str,
        model_name: str,
        temperature: float = 0.1,
        api_key: Optional[str] = None
    ) -> BaseChatModel:
        """
        Crea una instancia de LLM del proveedor especificado.
        
        Args:
            provider: Proveedor ('openai', 'google', 'anthropic')
            model_name: Nombre del modelo
            temperature: Temperatura para el modelo
            api_key: API key del proveedor (opcional, puede estar en env)
            
        Returns:
            Instancia de BaseChatModel
            
        Raises:
            ValueError: Si el proveedor no es válido
        """
        provider_lower = provider.lower()
        
        if provider_lower == "openai":
            kwargs = {"model": model_name, "temperature": temperature}
            if api_key:
                kwargs["openai_api_key"] = api_key
            return ChatOpenAI(**kwargs)
        
        elif provider_lower == "google":
            if not GOOGLE_AVAILABLE:
                raise ImportError(
                    "langchain-google-genai no está instalado. "
                    "Instálalo con: pip install langchain-google-genai"
                )
            kwargs = {"model": model_name, "temperature": temperature}
            if api_key:
                kwargs["google_api_key"] = api_key
            return ChatGoogleGenerativeAI(**kwargs)
        
        elif provider_lower == "anthropic":
            if not ANTHROPIC_AVAILABLE:
                raise ImportError(
                    "langchain-anthropic no está instalado. "
                    "Instálalo con: pip install langchain-anthropic"
                )
            kwargs = {"model": model_name, "temperature": temperature}
            if api_key:
                kwargs["anthropic_api_key"] = api_key
            return ChatAnthropic(**kwargs)
        
        else:
            raise ValueError(f"Proveedor no válido: {provider}. Use 'openai', 'google', o 'anthropic'")
    
    @staticmethod
    def get_available_models(provider: str) -> list:
        """
        Obtiene la lista de modelos disponibles para un proveedor.
        
        Args:
            provider: Proveedor ('openai', 'google', 'anthropic')
            
        Returns:
            Lista de nombres de modelos
        """
        provider_lower = provider.lower()
        
        if provider_lower == "openai":
            return LLMFactory.OPENAI_MODELS
        elif provider_lower == "google":
            return LLMFactory.GOOGLE_MODELS
        elif provider_lower == "anthropic":
            return LLMFactory.ANTHROPIC_MODELS
        else:
            return []

