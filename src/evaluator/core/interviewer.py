"""
Fase 2: Entrevista Interactiva
Realiza preguntas al candidato sobre requisitos no encontrados en el CV.
Utiliza Structured Output de LangChain para garantizar respuestas válidas.

ARQUITECTURA CRÍTICA:
- La Fase 2 DEBE cubrir el 100% de los requisitos no cumplidos
- Cada requisito faltante tiene su momento de indagación específico
- Ningún requisito puede quedar sin abordar
"""

import logging
from typing import List, Dict, Any, Optional
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate

from ..models import (
    Phase1Result, RequirementType, InterviewQuestion, InterviewResponse,
    QuestionsGenerationResponse, ResponseEvaluation
)
from ..llm.prompts import GENERATE_QUESTIONS_PROMPT, EVALUATE_RESPONSE_PROMPT
from ..llm.factory import LLMFactory

logger = logging.getLogger(__name__)


class Phase2Interviewer:
    """
    Sistema de entrevista interactiva para requisitos faltantes.
    
    GARANTÍA DE COBERTURA:
    - Genera exactamente UNA pregunta por cada requisito faltante
    - Valida que todos los requisitos sean abordados
    - Log de trazabilidad para auditoría
    """
    
    def __init__(
        self,
        llm: Optional[BaseChatModel] = None,
        provider: str = "openai",
        model_name: str = "gpt-4",
        temperature: float = 0.3,
        api_key: Optional[str] = None
    ):
        """
        Inicializa el entrevistador de Fase 2.
        
        Args:
            llm: Instancia de LLM de LangChain (opcional)
            provider: Proveedor del LLM ('openai', 'google', 'anthropic')
            model_name: Nombre del modelo a usar
            temperature: Temperatura para el modelo
            api_key: API key del proveedor (opcional)
        """
        if llm is None:
            self.llm = LLMFactory.create_llm(
                provider=provider,
                model_name=model_name,
                temperature=temperature,
                api_key=api_key
            )
        else:
            self.llm = llm
        
        # Crear LLMs con structured output para cada tarea
        self.questions_llm = self.llm.with_structured_output(QuestionsGenerationResponse)
        self.evaluation_llm = self.llm.with_structured_output(ResponseEvaluation)
    
    def generate_questions(
        self,
        missing_requirements: List[str],
        phase1_result: Phase1Result,
        cv_context: str
    ) -> List[InterviewQuestion]:
        """
        Genera preguntas para los requisitos faltantes usando Structured Output.
        
        GARANTÍA: Genera exactamente UNA pregunta por cada requisito faltante.
        Si el LLM genera menos preguntas, se re-intentan los faltantes.
        
        Args:
            missing_requirements: Lista de descripciones de requisitos no encontrados
            phase1_result: Resultado de la Fase 1 para contexto
            cv_context: Contexto del CV del candidato
            
        Returns:
            Lista de InterviewQuestion (garantizado 1:1 con missing_requirements)
        """
        if not missing_requirements:
            return []
        
        # Log de inicio de generación
        logger.info(
            f"[FASE2] Iniciando generación de preguntas para {len(missing_requirements)} requisitos faltantes"
        )
        
        # Crear contexto de requisitos faltantes con sus tipos
        requirements_with_types = self._build_requirements_context(
            missing_requirements, phase1_result
        )
        
        # Generar preguntas con garantía de cobertura completa
        questions = self._generate_questions_with_coverage(
            requirements_with_types, cv_context
        )
        
        # Log de validación
        logger.info(
            f"[FASE2] Generación completada: {len(questions)} preguntas para {len(missing_requirements)} requisitos"
        )
        
        return questions
    
    def _build_requirements_context(
        self,
        missing_requirements: List[str],
        phase1_result: Phase1Result
    ) -> List[Dict[str, Any]]:
        """
        Construye contexto enriquecido para cada requisito faltante.
        
        Args:
            missing_requirements: Lista de descripciones de requisitos
            phase1_result: Resultado de Fase 1
            
        Returns:
            Lista de diccionarios con info de cada requisito
        """
        requirements_with_types = []
        
        # Crear mapa de tipos desde unfulfilled_requirements
        type_map = {
            req.description.lower(): req.type.value
            for req in phase1_result.unfulfilled_requirements
        }
        
        for req_desc in missing_requirements:
            req_type = type_map.get(req_desc.lower(), "optional")
            requirements_with_types.append({
                "description": req_desc,
                "type": req_type
            })
        
        return requirements_with_types
    
    def _generate_questions_with_coverage(
        self,
        requirements_with_types: List[Dict[str, Any]],
        cv_context: str,
        max_retries: int = 2
    ) -> List[InterviewQuestion]:
        """
        Genera preguntas con GARANTÍA de cobertura completa.
        Re-intenta si faltan preguntas para algunos requisitos.
        
        Args:
            requirements_with_types: Lista de requisitos con tipos
            cv_context: Contexto del CV
            max_retries: Máximo de reintentos para requisitos faltantes
            
        Returns:
            Lista completa de preguntas (1:1 con requisitos)
        """
        all_questions = []
        pending_requirements = requirements_with_types.copy()
        attempts = 0
        
        while pending_requirements and attempts <= max_retries:
            attempts += 1
            
            # Formatear requisitos pendientes para el prompt
            requirements_text = "\n".join([
                f"- [{r['type'].upper()}] {r['description']}"
                for r in pending_requirements
            ])
            
            # Crear prompt para generación de preguntas
            prompt = ChatPromptTemplate.from_messages([
                ("system", GENERATE_QUESTIONS_PROMPT),
                ("human", "Contexto del CV:\n{cv_context}\n\nRequisitos sobre los que preguntar:\n{missing_requirements}")
            ])
            
            # Crear chain con structured output
            chain = prompt | self.questions_llm
            
            # Ejecutar
            try:
                result: QuestionsGenerationResponse = chain.invoke({
                    "cv_context": cv_context[:2000],
                    "missing_requirements": requirements_text
                })
                
                # Procesar preguntas generadas
                generated_questions = self._process_generated_questions(result, pending_requirements)
                all_questions.extend(generated_questions)
                
                # Identificar requisitos aún sin pregunta
                covered_descriptions = {q.requirement_description.lower() for q in generated_questions}
                pending_requirements = [
                    r for r in pending_requirements
                    if r["description"].lower() not in covered_descriptions
                ]
                
                if pending_requirements:
                    logger.warning(
                        f"[FASE2] Intento {attempts}: {len(pending_requirements)} requisitos sin pregunta. "
                        f"Re-intentando..."
                    )
                
            except Exception as e:
                logger.error(f"[FASE2] Error en generación de preguntas (intento {attempts}): {e}")
                break
        
        # Si aún faltan requisitos, generar preguntas fallback
        if pending_requirements:
            logger.warning(
                f"[FASE2] Generando preguntas fallback para {len(pending_requirements)} requisitos"
            )
            fallback_questions = self._generate_fallback_questions(pending_requirements)
            all_questions.extend(fallback_questions)
        
        return all_questions
    
    def _process_generated_questions(
        self,
        result: QuestionsGenerationResponse,
        requirements: List[Dict[str, Any]]
    ) -> List[InterviewQuestion]:
        """
        Procesa y valida las preguntas generadas por el LLM.
        
        Args:
            result: Respuesta del LLM con preguntas
            requirements: Requisitos que deberían tener preguntas
            
        Returns:
            Lista de preguntas válidas
        """
        questions = []
        req_descriptions_lower = {r["description"].lower() for r in requirements}
        
        for q in result.questions:
            req_type = q.requirement_type
            if req_type not in ["obligatory", "optional"]:
                req_type = "optional"
            
            # Verificar que la pregunta corresponde a un requisito pendiente
            q_desc_lower = q.requirement_description.strip().lower()
            
            # Buscar coincidencia exacta o parcial
            matched = False
            matched_req = None
            
            for req in requirements:
                req_lower = req["description"].lower()
                if q_desc_lower == req_lower or q_desc_lower in req_lower or req_lower in q_desc_lower:
                    matched = True
                    matched_req = req
                    break
            
            if matched and matched_req:
                questions.append(InterviewQuestion(
                    question=q.question.strip(),
                    requirement_description=matched_req["description"],  # Usar descripción original
                    requirement_type=RequirementType(matched_req["type"])
                ))
        
        return questions
    
    def _generate_fallback_questions(
        self,
        requirements: List[Dict[str, Any]]
    ) -> List[InterviewQuestion]:
        """
        Genera preguntas fallback para requisitos que no obtuvieron pregunta del LLM.
        Garantiza que ningún requisito quede sin abordar.
        
        Args:
            requirements: Lista de requisitos sin pregunta
            
        Returns:
            Lista de preguntas fallback
        """
        fallback_questions = []
        
        for req in requirements:
            # Generar pregunta genérica pero profesional
            question_text = (
                f"¿Podrías describir tu experiencia o conocimientos relacionados con: "
                f"{req['description']}?"
            )
            
            fallback_questions.append(InterviewQuestion(
                question=question_text,
                requirement_description=req["description"],
                requirement_type=RequirementType(req["type"])
            ))
            
            logger.info(
                f"[FASE2] Pregunta fallback generada para: {req['description'][:50]}..."
            )
        
        return fallback_questions
    
    def evaluate_response(
        self,
        requirement_description: str,
        requirement_type: RequirementType,
        cv_context: str,
        candidate_response: str
    ) -> Dict[str, Any]:
        """
        Evalúa si la respuesta del candidato cumple un requisito usando Structured Output.
        
        Args:
            requirement_description: Descripción del requisito
            requirement_type: Tipo del requisito (obligatory/optional)
            cv_context: Contexto del CV
            candidate_response: Respuesta del candidato
            
        Returns:
            Diccionario con 'fulfilled', 'evidence', y 'confidence'
        """
        # Crear prompt para evaluación
        prompt = ChatPromptTemplate.from_messages([
            ("system", EVALUATE_RESPONSE_PROMPT),
            ("human", """Requisito: {requirement_description}
Tipo: {requirement_type}

Contexto del CV:
{cv_context}

Respuesta del candidato:
{candidate_response}""")
        ])
        
        # Crear chain con structured output
        chain = prompt | self.evaluation_llm
        
        # Ejecutar
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
    
    def conduct_interview(
        self,
        phase1_result: Phase1Result,
        cv_context: str,
        interactive: bool = True,
        candidate_responses: Optional[List[str]] = None
    ) -> List[InterviewResponse]:
        """
        Realiza la entrevista completa con el candidato.
        
        GARANTÍA DE COBERTURA:
        - Genera preguntas para TODOS los requisitos faltantes
        - Cada requisito tiene su momento de indagación
        - Log de trazabilidad completo
        
        Args:
            phase1_result: Resultado de la Fase 1
            cv_context: Contexto del CV del candidato
            interactive: Si True, solicita respuestas al usuario
            candidate_responses: Lista de respuestas predefinidas (si interactive=False)
            
        Returns:
            Lista de InterviewResponse con todas las respuestas
        """
        if not phase1_result.missing_requirements:
            logger.info("[FASE2] No hay requisitos faltantes, omitiendo entrevista")
            return []
        
        # Log de inicio
        logger.info(
            f"[FASE2] Iniciando entrevista para {len(phase1_result.missing_requirements)} "
            f"requisitos faltantes"
        )
        
        # Generar preguntas (garantizado 1:1 con requisitos)
        questions = self.generate_questions(
            phase1_result.missing_requirements,
            phase1_result,
            cv_context
        )
        
        if not questions:
            logger.error("[FASE2] No se pudieron generar preguntas")
            return []
        
        # Log de validación de cobertura
        logger.info(
            f"[FASE2] Preguntas generadas: {len(questions)} | "
            f"Requisitos faltantes: {len(phase1_result.missing_requirements)}"
        )
        
        # Realizar entrevista
        interview_responses = []
        
        for i, question in enumerate(questions, 1):
            # Obtener respuesta
            if interactive:
                candidate_response = input(f"\nPregunta {i}: {question.question}\nRespuesta: ").strip()
            else:
                # Modo no interactivo: usar respuestas predefinidas
                if candidate_responses and i <= len(candidate_responses):
                    candidate_response = candidate_responses[i - 1]
                else:
                    # IMPORTANTE: En lugar de skip, usar respuesta vacía
                    # para que el requisito siga siendo evaluado como no cumplido
                    logger.warning(
                        f"[FASE2] No hay respuesta predefinida para pregunta {i}. "
                        f"Usando respuesta vacía."
                    )
                    candidate_response = ""
            
            # Crear respuesta de entrevista (siempre, incluso con respuesta vacía)
            interview_response = InterviewResponse(
                question=question.question,
                answer=candidate_response,
                requirement_description=question.requirement_description,
                requirement_type=question.requirement_type
            )
            
            interview_responses.append(interview_response)
            
            logger.info(
                f"[FASE2] Pregunta {i}/{len(questions)} procesada: "
                f"{question.requirement_description[:40]}..."
            )
        
        # Log de finalización con validación
        logger.info(
            f"[FASE2] Entrevista completada: {len(interview_responses)} respuestas recopiladas"
        )
        
        return interview_responses
    
    def validate_interview_coverage(
        self,
        phase1_result: Phase1Result,
        interview_responses: List[InterviewResponse]
    ) -> Dict[str, Any]:
        """
        Valida que la entrevista haya cubierto todos los requisitos faltantes.
        Útil para auditoría y debugging.
        
        Args:
            phase1_result: Resultado de Fase 1
            interview_responses: Respuestas de la entrevista
            
        Returns:
            Diccionario con métricas de cobertura
        """
        missing_set = set(r.lower() for r in phase1_result.missing_requirements)
        covered_set = set(r.requirement_description.lower() for r in interview_responses)
        
        covered = missing_set & covered_set
        uncovered = missing_set - covered_set
        
        coverage_pct = (len(covered) / len(missing_set) * 100) if missing_set else 100.0
        
        return {
            "total_missing": len(missing_set),
            "total_covered": len(covered),
            "total_uncovered": len(uncovered),
            "coverage_percentage": coverage_pct,
            "uncovered_requirements": list(uncovered),
            "is_complete": len(uncovered) == 0
        }
