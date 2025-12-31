"""
Fábrica LLM: Creación de instancias para OpenAI, Google y Anthropic.
Incluye configuración de LangSmith para trazabilidad.
"""

import os
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseChatModel

from .configuracion_modelos import obtener_modelos_disponibles, obtener_modelo_por_defecto

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    GOOGLE_DISPONIBLE = True
except ImportError:
    GOOGLE_DISPONIBLE = False
    ChatGoogleGenerativeAI = None

try:
    from langchain_anthropic import ChatAnthropic
    ANTHROPIC_DISPONIBLE = True
except ImportError:
    ANTHROPIC_DISPONIBLE = False
    ChatAnthropic = None

try:
    from langsmith import Client as ClienteLangSmith
    LANGSMITH_DISPONIBLE = True
except ImportError:
    LANGSMITH_DISPONIBLE = False
    ClienteLangSmith = None


_cliente_langsmith: Optional["ClienteLangSmith"] = None
_langsmith_configurado: bool = False


def configurar_langsmith(nombre_proyecto: str = "velora-evaluator") -> Optional["ClienteLangSmith"]:
    """Configura LangSmith para trazabilidad si hay API key disponible."""
    global _cliente_langsmith, _langsmith_configurado
    
    if _langsmith_configurado:
        return _cliente_langsmith
    
    _langsmith_configurado = True
    
    if not LANGSMITH_DISPONIBLE:
        return None
    
    api_key = os.getenv("LANGSMITH_API_KEY")
    if not api_key:
        return None
    
    try:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_PROJECT"] = nombre_proyecto
        _cliente_langsmith = ClienteLangSmith()
        return _cliente_langsmith
    except Exception:
        return None


configure_langsmith = configurar_langsmith


def obtener_cliente_langsmith() -> Optional["ClienteLangSmith"]:
    global _cliente_langsmith
    if not _langsmith_configurado:
        configurar_langsmith()
    return _cliente_langsmith


get_langsmith_client = obtener_cliente_langsmith


def langsmith_habilitado() -> bool:
    return obtener_cliente_langsmith() is not None


is_langsmith_enabled = langsmith_habilitado


class FabricaLLM:
    """Fábrica para crear instancias de LLM de diferentes proveedores."""
    
    @staticmethod
    def obtener_proveedores_disponibles() -> list:
        proveedores = ["openai"]
        if GOOGLE_DISPONIBLE:
            proveedores.append("google")
        if ANTHROPIC_DISPONIBLE:
            proveedores.append("anthropic")
        return proveedores
    
    @staticmethod
    def get_available_providers() -> list:
        return FabricaLLM.obtener_proveedores_disponibles()
    
    @staticmethod
    def obtener_proveedor_desde_modelo(nombre_modelo: str) -> str:
        modelo_lower = nombre_modelo.lower()
        if modelo_lower.startswith("gpt") or "openai" in modelo_lower:
            return "openai"
        elif "gemini" in modelo_lower or modelo_lower.startswith("gemini"):
            return "google"
        elif "claude" in modelo_lower:
            return "anthropic"
        return "openai"
    
    @staticmethod
    def get_provider_from_model(model_name: str) -> str:
        return FabricaLLM.obtener_proveedor_desde_modelo(model_name)
    
    @staticmethod
    def crear_llm(
        proveedor: str,
        nombre_modelo: str,
        temperatura: float = 0.1,
        api_key: Optional[str] = None
    ) -> BaseChatModel:
        """Crea instancia de LLM del proveedor especificado."""
        proveedor_lower = proveedor.lower()
        
        if proveedor_lower == "openai":
            kwargs = {"model": nombre_modelo, "temperature": temperatura}
            if api_key:
                kwargs["openai_api_key"] = api_key
            return ChatOpenAI(**kwargs)
        
        elif proveedor_lower == "google":
            if not GOOGLE_DISPONIBLE:
                raise ImportError("langchain-google-genai no instalado")
            kwargs = {"model": nombre_modelo, "temperature": temperatura}
            if api_key:
                kwargs["google_api_key"] = api_key
            return ChatGoogleGenerativeAI(**kwargs)
        
        elif proveedor_lower == "anthropic":
            if not ANTHROPIC_DISPONIBLE:
                raise ImportError("langchain-anthropic no instalado")
            kwargs = {"model": nombre_modelo, "temperature": temperatura}
            if api_key:
                kwargs["anthropic_api_key"] = api_key
            return ChatAnthropic(**kwargs)
        
        raise ValueError(f"Proveedor no válido: {proveedor}")
    
    @staticmethod
    def create_llm(provider: str, model_name: str, temperature: float = 0.1, api_key: Optional[str] = None) -> BaseChatModel:
        return FabricaLLM.crear_llm(provider, model_name, temperature, api_key)
    
    @staticmethod
    def obtener_modelos_disponibles(proveedor: str) -> list:
        return obtener_modelos_disponibles(proveedor)
    
    @staticmethod
    def get_available_models(provider: str) -> list:
        return FabricaLLM.obtener_modelos_disponibles(provider)
    
    @staticmethod
    def obtener_modelo_por_defecto(proveedor: str) -> str:
        return obtener_modelo_por_defecto(proveedor) or ""
    
    @staticmethod
    def get_default_model(provider: str) -> str:
        return FabricaLLM.obtener_modelo_por_defecto(provider)


LLMFactory = FabricaLLM
