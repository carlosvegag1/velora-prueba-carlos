"""
Fase 2: Agente Conversacional de Entrevista con Streaming
Sistema agéntico moderno que realiza entrevistas interactivas en tiempo real.

ARQUITECTURA:
- Streaming asíncrono de respuestas token-by-token
- Cobertura garantizada del 100% de requisitos faltantes
- Conversación natural, empática y profesional
- Integración con el sistema de evaluación existente
"""

import logging
from typing import List, Dict, Any, Optional, Generator

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from ..models import (
    Phase1Result, RequirementType, InterviewResponse,
    ResponseEvaluation
)
from ..llm.prompts import (
    EVALUATE_RESPONSE_PROMPT,
    AGENTIC_SYSTEM_PROMPT,
    AGENTIC_GREETING_PROMPT,
    AGENTIC_QUESTION_PROMPT,
    AGENTIC_CLOSING_PROMPT
)
from ..llm.factory import LLMFactory
from .logging_config import get_operational_logger

logger = logging.getLogger(__name__)


class AgenticInterviewer:
    """
    Sistema agéntico de entrevista conversacional con streaming.
    
    CARACTERÍSTICAS:
    - Streaming token-by-token para UX moderna
    - Cobertura garantizada de todos los requisitos
    - Conversación natural y personalizada
    - Compatible con el sistema de evaluación existente
    
    GARANTÍAS:
    - Genera exactamente UNA pregunta por cada requisito faltante
    - Valida que todos los requisitos sean abordados
    - Log de trazabilidad para auditoría
    """
    
    def __init__(
        self,
        llm: Optional[BaseChatModel] = None,
        provider: str = "openai",
        model_name: str = "gpt-4",
        temperature: float = 0.7,
        api_key: Optional[str] = None
    ):
        """
        Inicializa el entrevistador agéntico.
        
        Args:
            llm: Instancia de LLM (opcional)
            provider: Proveedor del LLM ('openai', 'google', 'anthropic')
            model_name: Nombre del modelo a usar
            temperature: Temperatura para respuestas naturales (default 0.7)
            api_key: API key del proveedor
        """
        self.provider = provider
        self.api_key = api_key
        self._op_logger = get_operational_logger()
        
        # Crear LLM para conversación (temperatura alta para naturalidad)
        if llm is None:
            self.llm = LLMFactory.create_llm(
                provider=provider,
                model_name=model_name,
                temperature=temperature,
                api_key=api_key
            )
        else:
            self.llm = llm
        
        # Crear LLM para evaluación (temperatura baja para precisión)
        self._evaluation_llm = LLMFactory.create_llm(
            provider=provider,
            model_name=model_name,
            temperature=0.1,
            api_key=api_key
        ).with_structured_output(ResponseEvaluation)
        
        # Estado de la entrevista
        self._candidate_name: str = ""
        self._cv_context: str = ""
        self._pending_requirements: List[Dict[str, Any]] = []
        self._conversation_history: List[Dict[str, str]] = []
        self._current_idx: int = 0
        
        self._op_logger.info("AgenticInterviewer inicializado")
    
    def initialize_interview(
        self,
        candidate_name: str,
        phase1_result: Phase1Result,
        cv_context: str
    ) -> Dict[str, Any]:
        """
        Inicializa una nueva sesión de entrevista.
        
        Args:
            candidate_name: Nombre del candidato
            phase1_result: Resultado de Fase 1
            cv_context: Texto del CV
            
        Returns:
            Diccionario con estado inicial
        """
        # Resetear estado
        self._conversation_history = []
        self._current_idx = 0
        self._candidate_name = candidate_name or "candidato"
        self._cv_context = cv_context[:2000]  # Limitar contexto
        
        # Construir lista de requisitos pendientes
        self._pending_requirements = []
        type_map = {
            req.description.lower(): req.type.value
            for req in phase1_result.unfulfilled_requirements
        }
        
        for req_desc in phase1_result.missing_requirements:
            req_type = type_map.get(req_desc.lower(), "optional")
            self._pending_requirements.append({
                "description": req_desc,
                "type": req_type,
                "asked": False,
                "answered": False,
                "response": None
            })
        
        self._op_logger.info(
            f"Entrevista inicializada: {len(self._pending_requirements)} requisitos pendientes"
        )
        
        return {
            "candidate_name": self._candidate_name,
            "total_questions": len(self._pending_requirements),
            "status": "initialized"
        }
    
    def stream_greeting(self) -> Generator[str, None, None]:
        """
        Genera saludo inicial con streaming token-by-token.
        
        Yields:
            Tokens del saludo
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", AGENTIC_SYSTEM_PROMPT.format(
                candidate_name=self._candidate_name,
                pending_count=len(self._pending_requirements),
                cv_summary=self._cv_context[:500]
            )),
            ("human", AGENTIC_GREETING_PROMPT.format(
                candidate_name=self._candidate_name,
                question_count=len(self._pending_requirements)
            ))
        ])
        
        chain = prompt | self.llm | StrOutputParser()
        
        greeting = ""
        try:
            for chunk in chain.stream({}):
                greeting += chunk
                yield chunk
            
            self._conversation_history.append({
                "role": "assistant",
                "content": greeting,
                "type": "greeting"
            })
            self._op_logger.info("Saludo generado con streaming")
            
        except Exception as e:
            logger.error(f"Error en saludo: {e}")
            fallback = f"¡Hola {self._candidate_name}! 👋 He revisado tu CV y tengo {len(self._pending_requirements)} pregunta(s) para ti. ¿Comenzamos?"
            self._conversation_history.append({
                "role": "assistant",
                "content": fallback,
                "type": "greeting"
            })
            yield fallback
    
    def stream_question(self, question_idx: int) -> Generator[str, None, None]:
        """
        Genera una pregunta con streaming token-by-token.
        
        Args:
            question_idx: Índice de la pregunta (0-based)
            
        Yields:
            Tokens de la pregunta
        """
        if question_idx >= len(self._pending_requirements):
            yield "No hay más preguntas pendientes."
            return
        
        requirement = self._pending_requirements[question_idx]
        
        # Construir historial para contexto
        history_text = self._build_conversation_context()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", AGENTIC_SYSTEM_PROMPT.format(
                candidate_name=self._candidate_name,
                pending_count=len(self._pending_requirements) - question_idx,
                cv_summary=self._cv_context[:500]
            )),
            ("human", AGENTIC_QUESTION_PROMPT.format(
                requirement=requirement["description"],
                req_type="OBLIGATORIO" if requirement["type"] == "obligatory" else "DESEABLE",
                current_num=question_idx + 1,
                total_num=len(self._pending_requirements),
                cv_context=self._cv_context[:800],
                conversation_history=history_text
            ))
        ])
        
        chain = prompt | self.llm | StrOutputParser()
        
        question_text = ""
        try:
            for chunk in chain.stream({}):
                question_text += chunk
                yield chunk
            
            self._pending_requirements[question_idx]["asked"] = True
            self._conversation_history.append({
                "role": "assistant",
                "content": question_text,
                "type": "question",
                "requirement_idx": question_idx,
                "requirement": requirement["description"]
            })
            self._current_idx = question_idx
            
            self._op_logger.info(
                f"Pregunta {question_idx + 1}/{len(self._pending_requirements)} generada"
            )
            
        except Exception as e:
            logger.error(f"Error generando pregunta: {e}")
            fallback = f"¿Podrías describir tu experiencia con {requirement['description']}?"
            self._pending_requirements[question_idx]["asked"] = True
            self._conversation_history.append({
                "role": "assistant",
                "content": fallback,
                "type": "question",
                "requirement_idx": question_idx,
                "requirement": requirement["description"]
            })
            yield fallback
    
    def stream_closing(self) -> Generator[str, None, None]:
        """
        Genera mensaje de cierre con streaming token-by-token.
        
        Yields:
            Tokens del cierre
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", AGENTIC_SYSTEM_PROMPT.format(
                candidate_name=self._candidate_name,
                pending_count=0,
                cv_summary=self._cv_context[:300]
            )),
            ("human", AGENTIC_CLOSING_PROMPT.format(
                candidate_name=self._candidate_name
            ))
        ])
        
        chain = prompt | self.llm | StrOutputParser()
        
        closing = ""
        try:
            for chunk in chain.stream({}):
                closing += chunk
                yield chunk
            
            self._conversation_history.append({
                "role": "assistant",
                "content": closing,
                "type": "closing"
            })
            self._op_logger.info("Cierre generado con streaming")
            
        except Exception as e:
            logger.error(f"Error en cierre: {e}")
            fallback = f"¡Perfecto, {self._candidate_name}! 🎉 Gracias por tus respuestas. Procesaré la información para completar tu evaluación."
            self._conversation_history.append({
                "role": "assistant",
                "content": fallback,
                "type": "closing"
            })
            yield fallback
    
    def register_response(self, question_idx: int, response: str) -> Dict[str, Any]:
        """
        Registra la respuesta del candidato.
        
        Args:
            question_idx: Índice de la pregunta respondida
            response: Respuesta del candidato
            
        Returns:
            Estado actualizado
        """
        if question_idx >= len(self._pending_requirements):
            return {"error": "Índice fuera de rango"}
        
        requirement = self._pending_requirements[question_idx]
        requirement["answered"] = True
        requirement["response"] = response
        
        self._conversation_history.append({
            "role": "user",
            "content": response,
            "type": "response",
            "requirement_idx": question_idx
        })
        
        is_complete = question_idx + 1 >= len(self._pending_requirements)
        
        self._op_logger.info(
            f"Respuesta registrada para pregunta {question_idx + 1}"
        )
        
        return {
            "question_idx": question_idx,
            "registered": True,
            "next_question": None if is_complete else question_idx + 1,
            "is_complete": is_complete
        }
    
    def evaluate_response(
        self,
        requirement_description: str,
        requirement_type: RequirementType,
        cv_context: str,
        candidate_response: str
    ) -> Dict[str, Any]:
        """
        Evalúa si la respuesta del candidato cumple un requisito.
        
        Args:
            requirement_description: Descripción del requisito
            requirement_type: Tipo del requisito
            cv_context: Contexto del CV
            candidate_response: Respuesta del candidato
            
        Returns:
            Diccionario con 'fulfilled', 'evidence', 'confidence'
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", EVALUATE_RESPONSE_PROMPT),
            ("human", """Requisito: {requirement_description}
Tipo: {requirement_type}

Contexto del CV:
{cv_context}

Respuesta del candidato:
{candidate_response}""")
        ])
        
        chain = prompt | self._evaluation_llm
        
        try:
            result: ResponseEvaluation = chain.invoke({
                "requirement_description": requirement_description,
                "requirement_type": requirement_type.value if isinstance(requirement_type, RequirementType) else requirement_type,
                "cv_context": cv_context[:1500],
                "candidate_response": candidate_response
            })
            
            return {
                "fulfilled": result.fulfilled,
                "evidence": result.evidence.strip() if result.evidence else None,
                "confidence": result.confidence
            }
        except Exception as e:
            logger.error(f"Error evaluando respuesta: {e}")
            return {
                "fulfilled": False,
                "evidence": None,
                "confidence": "low"
            }
    
    def get_interview_responses(self) -> List[InterviewResponse]:
        """
        Obtiene las respuestas formateadas para el sistema de evaluación.
        
        Returns:
            Lista de InterviewResponse
        """
        responses = []
        
        for i, req in enumerate(self._pending_requirements):
            if not req["answered"] or not req["response"]:
                continue
            
            # Buscar la pregunta en el historial
            question_text = self._find_question_for_requirement(i)
            
            responses.append(InterviewResponse(
                question=question_text,
                answer=req["response"],
                requirement_description=req["description"],
                requirement_type=RequirementType(req["type"])
            ))
        
        return responses
    
    def get_state(self) -> Dict[str, Any]:
        """
        Obtiene el estado actual de la entrevista.
        
        Returns:
            Estado completo
        """
        answered_count = sum(1 for r in self._pending_requirements if r["answered"])
        
        return {
            "candidate_name": self._candidate_name,
            "total_requirements": len(self._pending_requirements),
            "current_idx": self._current_idx,
            "answered_count": answered_count,
            "is_complete": answered_count >= len(self._pending_requirements),
            "pending_requirements": [
                {
                    "description": r["description"],
                    "type": r["type"],
                    "asked": r["asked"],
                    "answered": r["answered"]
                }
                for r in self._pending_requirements
            ]
        }
    
    def validate_coverage(self) -> Dict[str, Any]:
        """
        Valida la cobertura de requisitos (para auditoría).
        
        Returns:
            Métricas de cobertura
        """
        total = len(self._pending_requirements)
        asked = sum(1 for r in self._pending_requirements if r["asked"])
        answered = sum(1 for r in self._pending_requirements if r["answered"])
        
        uncovered = [
            r["description"] for r in self._pending_requirements
            if not r["answered"]
        ]
        
        coverage = (answered / total * 100) if total > 0 else 100.0
        
        self._op_logger.info(f"Cobertura de entrevista: {coverage:.1f}%")
        
        return {
            "total_requirements": total,
            "asked_count": asked,
            "answered_count": answered,
            "coverage_percentage": coverage,
            "uncovered_requirements": uncovered,
            "is_complete": len(uncovered) == 0
        }
    
    def _build_conversation_context(self) -> str:
        """Construye contexto de conversación para prompts."""
        if not self._conversation_history:
            return "Sin historial previo"
        
        context_parts = []
        for entry in self._conversation_history[-4:]:
            role = "Entrevistador" if entry["role"] == "assistant" else "Candidato"
            content = entry["content"][:200]
            context_parts.append(f"{role}: {content}")
        
        return "\n".join(context_parts)
    
    def _find_question_for_requirement(self, requirement_idx: int) -> str:
        """Busca la pregunta generada para un requisito."""
        for entry in self._conversation_history:
            if entry.get("type") == "question" and entry.get("requirement_idx") == requirement_idx:
                return entry["content"]
        
        # Fallback
        req = self._pending_requirements[requirement_idx]
        return f"¿Podrías describir tu experiencia con {req['description']}?"
