"""
Capa de Infraestructura: LLMs, embeddings, extracción y persistencia.
"""

from .llm import (
    FabricaLLM, LLMFactory,
    configurar_langsmith, configure_langsmith,
    obtener_cliente_langsmith, get_langsmith_client,
    langsmith_habilitado, is_langsmith_enabled,
    FabricaEmbeddings, EmbeddingFactory,
    ComparadorSemantico, SemanticMatcher,
    HiperparametrosLLM, LLMHyperparameters,
    ConfiguracionHiperparametros, HyperparametersConfig,
    ConfiguracionProveedor, ProviderConfig,
    obtener_modelos_disponibles, get_available_models,
    obtener_modelo_por_defecto, get_default_model,
    obtener_modelo_recomendado, get_recommended_model,
    obtener_configuracion_proveedor, get_provider_config,
    obtener_todos_los_proveedores, get_all_providers,
    es_modelo_valido, is_valid_model,
)

from .extraccion import (
    extraer_texto_de_pdf, extract_text_from_pdf,
    extraer_oferta_web, scrape_job_offer_url,
)

from .persistencia import (
    MemoriaUsuario, UserMemory,
    EvaluacionEnriquecida, EnrichedEvaluation,
    crear_evaluacion_enriquecida, create_enriched_evaluation,
    extraer_titulo_oferta, extract_job_title,
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
    "extraer_texto_de_pdf", "extract_text_from_pdf",
    "extraer_oferta_web", "scrape_job_offer_url",
    "MemoriaUsuario", "UserMemory",
    "EvaluacionEnriquecida", "EnrichedEvaluation",
    "crear_evaluacion_enriquecida", "create_enriched_evaluation",
    "extraer_titulo_oferta", "extract_job_title",
]
