"""
Modelos de datos para el sistema de evaluación de candidatos.
Utiliza Pydantic para validación y estructuración de datos.
Incluye modelos para Structured Output de LangChain.
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from enum import Enum


class RequirementType(str, Enum):
    """Tipo de requisito: obligatorio o opcional"""
    OBLIGATORY = "obligatory"
    OPTIONAL = "optional"


class ConfidenceLevel(str, Enum):
    """Nivel de confianza en el matching"""
    HIGH = "high"      # Evidencia explícita en CV
    MEDIUM = "medium"  # Evidencia inferida o parcial
    LOW = "low"        # Sin evidencia clara


class Requirement(BaseModel):
    """Representa un requisito individual de la oferta"""
    description: str = Field(..., description="Descripción del requisito")
    type: RequirementType = Field(..., description="Tipo: obligatorio u opcional")
    fulfilled: bool = Field(default=False, description="Si el requisito está cumplido")
    found_in_cv: bool = Field(default=False, description="Si el requisito fue encontrado en el CV")
    evidence: Optional[str] = Field(None, description="Evidencia de cumplimiento encontrada en el CV")
    confidence: ConfidenceLevel = Field(default=ConfidenceLevel.MEDIUM, description="Nivel de confianza en la evaluación")
    reasoning: Optional[str] = Field(None, description="Explicación del razonamiento de la evaluación")
    semantic_score: Optional[float] = Field(None, ge=0, le=1, description="Score de similitud semántica (0-1)")


# ============================================================================
# MODELOS PARA STRUCTURED OUTPUT DE LANGCHAIN
# Estos modelos se usan con llm.with_structured_output() para garantizar
# respuestas válidas del LLM sin necesidad de parsing manual de JSON.
# ============================================================================

class ExtractedRequirement(BaseModel):
    """Requisito extraído de una oferta de empleo (para structured output)"""
    description: str = Field(..., description="Descripción exacta del requisito tal como aparece en la oferta")
    type: Literal["obligatory", "optional"] = Field(
        ..., 
        description="Tipo de requisito: 'obligatory' para obligatorios/imprescindibles, 'optional' para deseables/opcionales"
    )


class RequirementsExtractionResponse(BaseModel):
    """Respuesta del LLM para extracción de requisitos (structured output)"""
    requirements: List[ExtractedRequirement] = Field(
        default_factory=list,
        description="Lista de requisitos extraídos de la oferta de empleo"
    )


class RequirementMatch(BaseModel):
    """Resultado de matching de un requisito con el CV (para structured output)"""
    requirement_description: str = Field(..., description="Descripción del requisito evaluado")
    fulfilled: bool = Field(..., description="Si el requisito está cumplido según el CV")
    found_in_cv: bool = Field(..., description="Si se encontró información relacionada en el CV")
    evidence: Optional[str] = Field(None, description="Evidencia específica encontrada en el CV")
    confidence: Literal["high", "medium", "low"] = Field(
        default="medium",
        description="Nivel de confianza: 'high' (evidencia explícita), 'medium' (inferido), 'low' (sin evidencia clara)"
    )
    reasoning: str = Field(
        default="",
        description="Explicación breve del razonamiento detrás de la decisión"
    )


class CVMatchingResponse(BaseModel):
    """Respuesta del LLM para matching CV-requisitos (structured output)"""
    matches: List[RequirementMatch] = Field(
        ...,
        description="Lista de resultados de matching para cada requisito"
    )
    analysis_summary: str = Field(..., description="Resumen breve del análisis realizado")


class GeneratedQuestion(BaseModel):
    """Pregunta generada para la entrevista (para structured output)"""
    question: str = Field(..., description="Pregunta clara y específica para el candidato")
    requirement_description: str = Field(..., description="Requisito relacionado con la pregunta")
    requirement_type: Literal["obligatory", "optional"] = Field(..., description="Tipo del requisito")


class QuestionsGenerationResponse(BaseModel):
    """Respuesta del LLM para generación de preguntas (structured output)"""
    questions: List[GeneratedQuestion] = Field(
        ...,
        description="Lista de preguntas generadas para la entrevista"
    )


class ResponseEvaluation(BaseModel):
    """Evaluación de una respuesta del candidato (para structured output)"""
    fulfilled: bool = Field(..., description="Si la respuesta demuestra que el candidato cumple el requisito")
    evidence: Optional[str] = Field(None, description="Evidencia específica de la respuesta")
    confidence: Literal["high", "medium", "low"] = Field(
        default="medium",
        description="Nivel de confianza en la evaluación"
    )


# ============================================================================
# MODELOS DE RESULTADOS (existentes)
# ============================================================================

class Phase1Result(BaseModel):
    """Resultado de la Fase 1: Análisis inicial de CV vs Oferta"""
    score: float = Field(..., ge=0, le=100, description="Puntuación del candidato (0-100%)")
    discarded: bool = Field(..., description="Si el candidato fue descartado por requisito obligatorio")
    fulfilled_requirements: List[Requirement] = Field(default_factory=list, description="Requisitos cumplidos")
    unfulfilled_requirements: List[Requirement] = Field(default_factory=list, description="Requisitos no cumplidos")
    missing_requirements: List[str] = Field(default_factory=list, description="Requisitos no encontrados en el CV (descripción)")
    analysis_summary: str = Field(..., description="Resumen del análisis realizado")


class InterviewQuestion(BaseModel):
    """Pregunta generada para la entrevista"""
    question: str = Field(..., description="Texto de la pregunta")
    requirement_description: str = Field(..., description="Requisito relacionado")
    requirement_type: RequirementType = Field(..., description="Tipo de requisito")


class InterviewResponse(BaseModel):
    """Respuesta del candidato en la entrevista"""
    question: str = Field(..., description="Pregunta realizada")
    answer: str = Field(..., description="Respuesta del candidato")
    requirement_description: str = Field(..., description="Requisito relacionado")
    requirement_type: RequirementType = Field(..., description="Tipo de requisito")


class EvaluationResult(BaseModel):
    """Resultado final completo de la evaluación"""
    phase1_result: Phase1Result = Field(..., description="Resultado de la fase 1")
    phase2_completed: bool = Field(default=False, description="Si se completó la fase 2")
    interview_responses: List[InterviewResponse] = Field(default_factory=list, description="Respuestas de la entrevista")
    final_score: float = Field(..., ge=0, le=100, description="Puntuación final (0-100%)")
    final_fulfilled_requirements: List[Requirement] = Field(default_factory=list, description="Requisitos finales cumplidos")
    final_unfulfilled_requirements: List[Requirement] = Field(default_factory=list, description="Requisitos finales no cumplidos")
    final_discarded: bool = Field(..., description="Si el candidato fue descartado tras evaluación completa")
    evaluation_summary: str = Field(..., description="Resumen completo de la evaluación")
