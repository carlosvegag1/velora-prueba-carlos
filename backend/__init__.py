"""
Velora: Sistema de Evaluacion de Candidatos con IA.

Arquitectura de Capas:
- modelos: Estructuras de datos Pydantic
- utilidades: Funciones auxiliares transversales
- recursos: Prompts y configuraciones
- infraestructura: Integraciones externas (LLM, embeddings, extraccion, persistencia)
- nucleo: Logica de negocio (analisis, entrevista, historial)
- orquestacion: Coordinacion de flujos de trabajo
"""

__version__ = "3.2.0"

from .modelos import (
    TipoRequisito, NivelConfianza,
    Requisito, ResultadoFase1, ResultadoEvaluacion,
    PreguntaEntrevista, RespuestaEntrevista,
    RequisitoExtraido, RespuestaExtraccionRequisitos,
    ResultadoMatching, RespuestaMatchingCV,
    EvaluacionRespuesta,
    RequirementType, ConfidenceLevel,
    Requirement, Phase1Result, EvaluationResult,
    InterviewQuestion, InterviewResponse,
    RequirementsExtractionResponse, CVMatchingResponse,
    ResponseEvaluation,
)

from .utilidades import (
    RegistroOperacional, obtener_registro_operacional,
    Colores, Indicadores,
    calcular_puntuacion, cargar_archivo_texto,
    limpiar_descripcion_requisito,
    procesar_coincidencias, agregar_requisitos_no_procesados,
)

from .nucleo import (
    AnalizadorFase1, Phase1Analyzer,
    EntrevistadorFase2, Phase2Interviewer, AgenticInterviewer,
    AlmacenVectorialHistorial, HistoryVectorStore,
    AsistenteHistorial, HistoryChatbot,
)

from .orquestacion import (
    Orquestador, CoordinadorEvaluacion, Orchestrator, CandidateEvaluator,
    EstadoFase1, Phase1State,
    crear_grafo_fase1, create_phase1_graph,
    ejecutar_grafo_fase1, run_phase1_graph,
)

from .infraestructura import (
    FabricaLLM, LLMFactory,
    FabricaEmbeddings, EmbeddingFactory,
    ComparadorSemantico, SemanticMatcher,
    ConfiguracionHiperparametros, HyperparametersConfig,
    obtener_modelos_disponibles, get_available_models,
    obtener_modelo_por_defecto, get_default_model,
    configurar_langsmith, configure_langsmith,
    extraer_texto_de_pdf, extract_text_from_pdf,
    extraer_oferta_web, scrape_job_offer_url,
    MemoriaUsuario, UserMemory,
    EvaluacionEnriquecida, EnrichedEvaluation,
    crear_evaluacion_enriquecida, create_enriched_evaluation,
)

from .recursos import (
    PROMPT_EXTRACCION_REQUISITOS,
    PROMPT_MATCHING_CV,
    PROMPT_EVALUAR_RESPUESTA,
    PROMPT_SISTEMA_AGENTE,
    PROMPT_SALUDO_AGENTE,
    PROMPT_PREGUNTA_AGENTE,
    PROMPT_CIERRE_AGENTE,
    EXTRACT_REQUIREMENTS_PROMPT,
    MATCH_CV_REQUIREMENTS_PROMPT,
    EVALUATE_RESPONSE_PROMPT,
)


__all__ = [
    "__version__",
    "TipoRequisito", "NivelConfianza",
    "Requisito", "ResultadoFase1", "ResultadoEvaluacion",
    "PreguntaEntrevista", "RespuestaEntrevista",
    "RequisitoExtraido", "RespuestaExtraccionRequisitos",
    "ResultadoMatching", "RespuestaMatchingCV",
    "EvaluacionRespuesta",
    "RequirementType", "ConfidenceLevel",
    "Requirement", "Phase1Result", "EvaluationResult",
    "InterviewQuestion", "InterviewResponse",
    "RequirementsExtractionResponse", "CVMatchingResponse",
    "ResponseEvaluation",
    "RegistroOperacional", "obtener_registro_operacional",
    "Colores", "Indicadores",
    "calcular_puntuacion", "cargar_archivo_texto",
    "AnalizadorFase1", "Phase1Analyzer",
    "EntrevistadorFase2", "Phase2Interviewer", "AgenticInterviewer",
    "AlmacenVectorialHistorial", "HistoryVectorStore",
    "AsistenteHistorial", "HistoryChatbot",
    "Orquestador", "CoordinadorEvaluacion", "Orchestrator", "CandidateEvaluator",
    "EstadoFase1", "Phase1State",
    "crear_grafo_fase1", "create_phase1_graph",
    "ejecutar_grafo_fase1", "run_phase1_graph",
    "FabricaLLM", "LLMFactory",
    "FabricaEmbeddings", "EmbeddingFactory",
    "ComparadorSemantico", "SemanticMatcher",
    "ConfiguracionHiperparametros", "HyperparametersConfig",
    "obtener_modelos_disponibles", "get_available_models",
    "obtener_modelo_por_defecto", "get_default_model",
    "configurar_langsmith", "configure_langsmith",
    "extraer_texto_de_pdf", "extract_text_from_pdf",
    "extraer_oferta_web", "scrape_job_offer_url",
    "MemoriaUsuario", "UserMemory",
    "EvaluacionEnriquecida", "EnrichedEvaluation",
    "crear_evaluacion_enriquecida", "create_enriched_evaluation",
    "PROMPT_EXTRACCION_REQUISITOS",
    "PROMPT_MATCHING_CV",
    "PROMPT_EVALUAR_RESPUESTA",
]
