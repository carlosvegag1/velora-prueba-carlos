"""
Modelos de datos Velora - Estructuras Pydantic para validación y tipado.
Incluye modelos para Structured Output de LangChain.
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from enum import Enum


# Enumeraciones
class TipoRequisito(str, Enum):
    """Clasificación según obligatoriedad."""
    OBLIGATORIO = "obligatory"
    DESEABLE = "optional"


class NivelConfianza(str, Enum):
    """Grado de certeza en la evaluación."""
    ALTO = "high"
    MEDIO = "medium"
    BAJO = "low"


# Modelo principal de requisito
class Requisito(BaseModel):
    """Requisito individual con su evaluación."""
    
    descripcion: str = Field(..., alias="description")
    tipo: TipoRequisito = Field(..., alias="type")
    cumplido: bool = Field(default=False, alias="fulfilled")
    encontrado_en_cv: bool = Field(default=False, alias="found_in_cv")
    evidencia: Optional[str] = Field(None, alias="evidence")
    confianza: NivelConfianza = Field(..., alias="confidence")
    razonamiento: Optional[str] = Field(None, alias="reasoning")
    puntuacion_semantica: Optional[float] = Field(None, alias="semantic_score", ge=0, le=1)

    class Config:
        populate_by_name = True


# Modelos Structured Output - Respuestas garantizadas del LLM
class RequisitoExtraido(BaseModel):
    """Requisito extraído de oferta (Structured Output)."""
    description: str = Field(...)
    type: Literal["obligatory", "optional"] = Field(...)


class RespuestaExtraccionRequisitos(BaseModel):
    """Respuesta LLM: extracción de requisitos."""
    requirements: List[RequisitoExtraido] = Field(default_factory=list)


class ResultadoMatching(BaseModel):
    """Resultado de evaluación requisito vs CV."""
    requirement_description: str = Field(...)
    fulfilled: bool = Field(...)
    found_in_cv: bool = Field(...)
    evidence: Optional[str] = Field(None)
    confidence: Literal["high", "medium", "low"] = Field(...)
    reasoning: str = Field(default="")


class RespuestaMatchingCV(BaseModel):
    """Respuesta LLM: matching CV-requisitos."""
    matches: List[ResultadoMatching] = Field(...)
    analysis_summary: str = Field(...)


class EvaluacionRespuesta(BaseModel):
    """Evaluación de respuesta del candidato en entrevista."""
    fulfilled: bool = Field(...)
    evidence: Optional[str] = Field(None)
    confidence: Literal["high", "medium", "low"] = Field(...)


# Modelos de resultados
class ResultadoFase1(BaseModel):
    """Resultado del análisis automático CV vs Oferta."""
    
    puntuacion: float = Field(..., alias="score", ge=0, le=100)
    descartado: bool = Field(..., alias="discarded")
    requisitos_cumplidos: List[Requisito] = Field(default_factory=list, alias="fulfilled_requirements")
    requisitos_no_cumplidos: List[Requisito] = Field(default_factory=list, alias="unfulfilled_requirements")
    requisitos_faltantes: List[str] = Field(default_factory=list, alias="missing_requirements")
    resumen_analisis: str = Field(..., alias="analysis_summary")

    class Config:
        populate_by_name = True


class PreguntaEntrevista(BaseModel):
    """Pregunta generada para entrevista."""
    
    pregunta: str = Field(..., alias="question")
    descripcion_requisito: str = Field(..., alias="requirement_description")
    tipo_requisito: TipoRequisito = Field(..., alias="requirement_type")

    class Config:
        populate_by_name = True


class RespuestaEntrevista(BaseModel):
    """Respuesta del candidato en entrevista."""
    
    pregunta: str = Field(..., alias="question")
    respuesta: str = Field(..., alias="answer")
    descripcion_requisito: str = Field(..., alias="requirement_description")
    tipo_requisito: TipoRequisito = Field(..., alias="requirement_type")

    class Config:
        populate_by_name = True


class ResultadoEvaluacion(BaseModel):
    """Resultado completo de evaluación (Fase 1 + Fase 2)."""
    
    resultado_fase1: ResultadoFase1 = Field(..., alias="phase1_result")
    fase2_completada: bool = Field(default=False, alias="phase2_completed")
    respuestas_entrevista: List[RespuestaEntrevista] = Field(default_factory=list, alias="interview_responses")
    puntuacion_final: float = Field(..., alias="final_score", ge=0, le=100)
    requisitos_finales_cumplidos: List[Requisito] = Field(default_factory=list, alias="final_fulfilled_requirements")
    requisitos_finales_no_cumplidos: List[Requisito] = Field(default_factory=list, alias="final_unfulfilled_requirements")
    descartado_final: bool = Field(..., alias="final_discarded")
    resumen_evaluacion: str = Field(..., alias="evaluation_summary")

    class Config:
        populate_by_name = True


# Aliases para compatibilidad con código existente
Requirement = Requisito
RequirementType = TipoRequisito
ConfidenceLevel = NivelConfianza
Phase1Result = ResultadoFase1
InterviewQuestion = PreguntaEntrevista
InterviewResponse = RespuestaEntrevista
EvaluationResult = ResultadoEvaluacion
RequirementsExtractionResponse = RespuestaExtraccionRequisitos
CVMatchingResponse = RespuestaMatchingCV
ResponseEvaluation = EvaluacionRespuesta
ExtractedRequirement = RequisitoExtraido
RequirementMatch = ResultadoMatching
