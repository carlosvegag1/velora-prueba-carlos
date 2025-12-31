"""
Módulo de Proveedores: LLMs, embeddings e hiperparámetros.
"""

from .llm_proveedor import (
    FabricaLLM, LLMFactory,
    configurar_langsmith, configure_langsmith,
    obtener_cliente_langsmith, get_langsmith_client,
    langsmith_habilitado, is_langsmith_enabled,
)
from .embedding_proveedor import FabricaEmbeddings, EmbeddingFactory
from .comparador_semantico import ComparadorSemantico, SemanticMatcher
from .hiperparametros import (
    HiperparametrosLLM, LLMHyperparameters,
    ConfiguracionHiperparametros, HyperparametersConfig,
)
from .configuracion_modelos import (
    ConfiguracionProveedor, ProviderConfig,
    obtener_modelos_disponibles, get_available_models,
    obtener_modelo_por_defecto, get_default_model,
    obtener_modelo_recomendado, get_recommended_model,
    obtener_configuracion_proveedor, get_provider_config,
    obtener_todos_los_proveedores, get_all_providers,
    es_modelo_valido, is_valid_model,
)

__all__ = [
    "FabricaLLM", "LLMFactory",
    "configurar_langsmith", "configure_langsmith",
    "obtener_cliente_langsmith", "get_langsmith_client",
    "langsmith_habilitado", "is_langsmith_enabled",
    "FabricaEmbeddings", "EmbeddingFactory",
    "ComparadorSemantico", "SemanticMatcher",
    "HiperparametrosLLM", "LLMHyperparameters",
    "ConfiguracionHiperparametros", "HyperparametersConfig",
    "ConfiguracionProveedor", "ProviderConfig",
    "obtener_modelos_disponibles", "get_available_models",
    "obtener_modelo_por_defecto", "get_default_model",
    "obtener_modelo_recomendado", "get_recommended_model",
    "obtener_configuracion_proveedor", "get_provider_config",
    "obtener_todos_los_proveedores", "get_all_providers",
    "es_modelo_valido", "is_valid_model",
]
