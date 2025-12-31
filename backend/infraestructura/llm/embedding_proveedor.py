"""
Fábrica de Embeddings: Mapeo 1:1 proveedor → modelo de embedding.
OpenAI → text-embedding-3-small, Google → text-embedding-004
Anthropic NO ofrece embeddings propios.
"""

import os
from typing import Optional, List
from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings

try:
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    GOOGLE_EMBEDDINGS_DISPONIBLE = True
except ImportError:
    GOOGLE_EMBEDDINGS_DISPONIBLE = False
    GoogleGenerativeAIEmbeddings = None


MAPA_PROVEEDOR_EMBEDDING = {
    "openai": "text-embedding-3-small",
    "google": "models/text-embedding-004",
}

DIMENSIONES_OPTIMIZADAS = {
    "openai": 512,
    "google": None,
}

PROVEEDORES_SIN_EMBEDDINGS = ["anthropic"]


class FabricaEmbeddings:
    """Fábrica para crear instancias de embeddings."""
    
    @staticmethod
    def obtener_proveedores_disponibles() -> List[str]:
        proveedores = ["openai"]
        if GOOGLE_EMBEDDINGS_DISPONIBLE:
            proveedores.append("google")
        return proveedores
    
    @staticmethod
    def get_available_providers() -> List[str]:
        return FabricaEmbeddings.obtener_proveedores_disponibles()
    
    @staticmethod
    def obtener_modelo_embedding(proveedor: str) -> Optional[str]:
        return MAPA_PROVEEDOR_EMBEDDING.get(proveedor.lower())
    
    @staticmethod
    def get_embedding_model(provider: str) -> Optional[str]:
        return FabricaEmbeddings.obtener_modelo_embedding(provider)
    
    @staticmethod
    def soporta_embeddings(proveedor: str) -> bool:
        proveedor_lower = proveedor.lower()
        if proveedor_lower in PROVEEDORES_SIN_EMBEDDINGS:
            return False
        if proveedor_lower == "google" and not GOOGLE_EMBEDDINGS_DISPONIBLE:
            return False
        return proveedor_lower in MAPA_PROVEEDOR_EMBEDDING
    
    @staticmethod
    def supports_embeddings(provider: str) -> bool:
        return FabricaEmbeddings.soporta_embeddings(provider)
    
    @staticmethod
    def obtener_mensaje_proveedor(proveedor_llm: str) -> Optional[str]:
        if FabricaEmbeddings.soporta_embeddings(proveedor_llm):
            return None
        if proveedor_llm.lower() == "anthropic":
            return "Anthropic no ofrece API de embeddings. Funcionalidades semánticas deshabilitadas."
        return f"El proveedor {proveedor_llm} no soporta embeddings."
    
    @staticmethod
    def get_embedding_provider_message(llm_provider: str) -> Optional[str]:
        return FabricaEmbeddings.obtener_mensaje_proveedor(llm_provider)
    
    @staticmethod
    def crear_embeddings(proveedor: str, api_key: Optional[str] = None, usar_dimensiones_optimizadas: bool = True) -> Embeddings:
        """
        Crea instancia de embeddings del proveedor especificado.
        
        Args:
            proveedor: Nombre del proveedor ('openai', 'google')
            api_key: API key opcional (si no se proporciona, usa variables de entorno)
            usar_dimensiones_optimizadas: Si True, usa dimensiones reducidas para mayor velocidad (default: True)
                - OpenAI: 512 dims en lugar de 1536 (~3x más rápido, ~98% precisión)
                - Google: Sin cambios (768 dims por defecto)
        
        Returns:
            Instancia de Embeddings configurada
        """
        proveedor_lower = proveedor.lower()
        
        if not FabricaEmbeddings.soporta_embeddings(proveedor_lower):
            raise ValueError(f"'{proveedor}' no soporta embeddings. Disponibles: {FabricaEmbeddings.obtener_proveedores_disponibles()}")
        
        modelo_embedding = MAPA_PROVEEDOR_EMBEDDING[proveedor_lower]
        
        if proveedor_lower == "openai":
            kwargs = {"model": modelo_embedding}
            

            if usar_dimensiones_optimizadas and DIMENSIONES_OPTIMIZADAS.get("openai"):
                kwargs["dimensions"] = DIMENSIONES_OPTIMIZADAS["openai"]
            
            key = api_key or os.getenv("OPENAI_API_KEY")
            if key:
                kwargs["openai_api_key"] = key
            return OpenAIEmbeddings(**kwargs)
        
        elif proveedor_lower == "google":
            if not GOOGLE_EMBEDDINGS_DISPONIBLE:
                raise ImportError("langchain-google-genai no instalado")
            kwargs = {"model": modelo_embedding}
            key = api_key or os.getenv("GOOGLE_API_KEY")
            if key:
                kwargs["google_api_key"] = key
            return GoogleGenerativeAIEmbeddings(**kwargs)
        
        raise ValueError(f"Proveedor no válido: {proveedor}")
    
    @staticmethod
    def create_embeddings(provider: str, api_key: Optional[str] = None, usar_dimensiones_optimizadas: bool = True) -> Embeddings:
        """Alias en inglés para crear_embeddings. Mantiene retrocompatibilidad."""
        return FabricaEmbeddings.crear_embeddings(provider, api_key, usar_dimensiones_optimizadas)
    
    @staticmethod
    def validar_api_key(proveedor: str, api_key: Optional[str] = None) -> bool:
        proveedor_lower = proveedor.lower()
        if proveedor_lower in PROVEEDORES_SIN_EMBEDDINGS:
            return False
        if proveedor_lower == "openai":
            return bool(api_key or os.getenv("OPENAI_API_KEY"))
        elif proveedor_lower == "google":
            return bool(api_key or os.getenv("GOOGLE_API_KEY"))
        return False
    
    @staticmethod
    def validate_api_key(provider: str, api_key: Optional[str] = None) -> bool:
        return FabricaEmbeddings.validar_api_key(provider, api_key)
    
    @staticmethod
    def obtener_proveedor_fallback(excluir_proveedor: Optional[str] = None) -> Optional[str]:
        for proveedor in FabricaEmbeddings.obtener_proveedores_disponibles():
            if excluir_proveedor and proveedor.lower() == excluir_proveedor.lower():
                continue
            if FabricaEmbeddings.validar_api_key(proveedor):
                return proveedor
        return None
    
    @staticmethod
    def get_fallback_provider(exclude_provider: Optional[str] = None) -> Optional[str]:
        return FabricaEmbeddings.obtener_proveedor_fallback(exclude_provider)
    
    @staticmethod
    def obtener_dimensiones_optimizadas(proveedor: str) -> Optional[int]:
        """Retorna las dimensiones optimizadas para el proveedor dado."""
        return DIMENSIONES_OPTIMIZADAS.get(proveedor.lower())
    
    @staticmethod
    def get_optimized_dimensions(provider: str) -> Optional[int]:
        """Returns the optimized dimensions for the given provider."""
        return FabricaEmbeddings.obtener_dimensiones_optimizadas(provider)


EmbeddingFactory = FabricaEmbeddings
