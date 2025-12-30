"""
Evaluador Principal del Sistema
Orquesta las dos fases del proceso de evaluación de candidatos.
Incluye integración con LangSmith para trazabilidad y feedback.
"""

from typing import Optional
from langchain_core.language_models import BaseChatModel

from ..models import EvaluationResult, Phase1Result, Requirement, RequirementType
from .analyzer import Phase1Analyzer
from .interviewer import Phase2Interviewer
from ..processing import load_text_file, calculate_score
from ..llm.factory import configure_langsmith, get_langsmith_client


class CandidateEvaluator:
    """
    Sistema completo de evaluación de candidatos basado en LangChain.
    
    Coordina las dos fases:
    1. Análisis de oferta y CV
    2. Entrevista interactiva (si es necesario)
    """
    
    def __init__(
        self,
        provider: str = "openai",
        model_name: str = "gpt-4",
        temperature_phase1: float = 0.1,
        temperature_phase2: float = 0.3,
        llm_phase1: Optional[BaseChatModel] = None,
        llm_phase2: Optional[BaseChatModel] = None,
        api_key: Optional[str] = None,
        enable_langsmith: bool = True
    ):
        """
        Inicializa el evaluador de candidatos.
        
        Args:
            provider: Proveedor del LLM ('openai', 'google', 'anthropic')
            model_name: Nombre del modelo a usar (por defecto gpt-4)
            temperature_phase1: Temperatura para Fase 1 (baja para precisión)
            temperature_phase2: Temperatura para Fase 2 (más alta para conversación)
            llm_phase1: LLM personalizado para Fase 1 (opcional)
            llm_phase2: LLM personalizado para Fase 2 (opcional)
            api_key: API key del proveedor (opcional)
            enable_langsmith: Si habilitar LangSmith para trazabilidad
        """
        # Configurar LangSmith si está habilitado
        self._langsmith_enabled = False
        if enable_langsmith:
            langsmith = configure_langsmith()
            self._langsmith_enabled = langsmith is not None
        
        # Almacenar el último run_id para feedback
        self._last_run_id: Optional[str] = None
        
        # Inicializar componentes
        self.phase1_analyzer = Phase1Analyzer(
            llm=llm_phase1,
            provider=provider,
            model_name=model_name,
            temperature=temperature_phase1,
            api_key=api_key
        )
        
        self.phase2_interviewer = Phase2Interviewer(
            llm=llm_phase2,
            provider=provider,
            model_name=model_name,
            temperature=temperature_phase2,
            api_key=api_key
        )
    
    def evaluate_candidate(
        self,
        job_offer_path: Optional[str] = None,
        cv_path: Optional[str] = None,
        job_offer_text: Optional[str] = None,
        cv_text: Optional[str] = None,
        interactive: bool = True,
        candidate_responses: Optional[list] = None
    ) -> EvaluationResult:
        """
        Ejecuta la evaluación completa del candidato.
        
        Args:
            job_offer_path: Ruta al archivo con la oferta (alternativa a job_offer_text)
            cv_path: Ruta al archivo con el CV (alternativa a cv_text)
            job_offer_text: Texto de la oferta directamente (alternativa a job_offer_path)
            cv_text: Texto del CV directamente (alternativa a cv_path)
            interactive: Si True, solicita respuestas interactivamente en Fase 2
            candidate_responses: Lista de respuestas predefinidas para Fase 2 (solo si interactive=False)
            
        Returns:
            EvaluationResult con el resultado completo
        """
        # Cargar textos
        if job_offer_path:
            job_offer = load_text_file(job_offer_path)
        elif job_offer_text:
            job_offer = job_offer_text
        else:
            raise ValueError("Debe proporcionar job_offer_path o job_offer_text")
        
        if cv_path:
            cv = load_text_file(cv_path)
        elif cv_text:
            cv = cv_text
        else:
            raise ValueError("Debe proporcionar cv_path o cv_text")
        
        # FASE 1: Análisis de CV y oferta
        phase1_result = self.phase1_analyzer.analyze(job_offer, cv)
        
        # Si el candidato fue descartado, no continuar a Fase 2
        if phase1_result.discarded:
            
            return EvaluationResult(
                phase1_result=phase1_result,
                phase2_completed=False,
                interview_responses=[],
                final_score=phase1_result.score,
                final_fulfilled_requirements=phase1_result.fulfilled_requirements,
                final_unfulfilled_requirements=phase1_result.unfulfilled_requirements,
                final_discarded=True,
                evaluation_summary=self._generate_summary(phase1_result, [], phase1_result.score)
            )
        
        # Si no hay requisitos faltantes, no hay necesidad de Fase 2
        if not phase1_result.missing_requirements:
            
            return EvaluationResult(
                phase1_result=phase1_result,
                phase2_completed=False,
                interview_responses=[],
                final_score=phase1_result.score,
                final_fulfilled_requirements=phase1_result.fulfilled_requirements,
                final_unfulfilled_requirements=phase1_result.unfulfilled_requirements,
                final_discarded=False,
                evaluation_summary=self._generate_summary(phase1_result, [], phase1_result.score)
            )
        
        # FASE 2: Entrevista interactiva
        interview_responses = self.phase2_interviewer.conduct_interview(
            phase1_result,
            cv,
            interactive=interactive,
            candidate_responses=candidate_responses
        )
        
        # Re-evaluar con las respuestas de la entrevista
        final_result = self.reevaluate_with_interview(phase1_result, interview_responses)
        
        return final_result
    
    def reevaluate_with_interview(
        self,
        phase1_result: Phase1Result,
        interview_responses: list
    ) -> EvaluationResult:
        """
        Re-evalúa al candidato incorporando las respuestas de la entrevista.
        
        Args:
            phase1_result: Resultado de la Fase 1
            interview_responses: Respuestas de la entrevista
            
        Returns:
            EvaluationResult actualizado
        """
        # Crear mapa de respuestas por requisito
        response_map = {
            resp.requirement_description: resp
            for resp in interview_responses
        }
        
        # Evaluar cada respuesta
        fulfilled_from_interview = []
        unfulfilled_from_interview = []
        
        for resp in interview_responses:
            # Evaluar si la respuesta cumple el requisito
            evaluation = self.phase2_interviewer.evaluate_response(
                resp.requirement_description,
                resp.requirement_type,
                "",  # CV context no necesario aquí, ya se evaluó
                resp.answer
            )
            
            requirement = Requirement(
                description=resp.requirement_description,
                type=resp.requirement_type,
                fulfilled=evaluation["fulfilled"],
                found_in_cv=False,  # Estos requisitos no estaban en el CV
                evidence=evaluation.get("evidence")
            )
            
            if evaluation["fulfilled"]:
                fulfilled_from_interview.append(requirement)
            else:
                unfulfilled_from_interview.append(requirement)
        
        # Combinar resultados de Fase 1 y Fase 2
        all_fulfilled = phase1_result.fulfilled_requirements + fulfilled_from_interview
        all_unfulfilled = []
        
        # Agregar requisitos no cumplidos de Fase 1 que no se preguntaron en Fase 2
        for req in phase1_result.unfulfilled_requirements:
            if req.description not in response_map:
                all_unfulfilled.append(req)
        
        # Agregar requisitos no cumplidos de Fase 2
        all_unfulfilled.extend(unfulfilled_from_interview)
        
        # Calcular puntuación final
        total_requirements = len(phase1_result.fulfilled_requirements) + len(phase1_result.unfulfilled_requirements)
        fulfilled_count = len(all_fulfilled)
        has_unfulfilled_obligatory = any(
            req.type == RequirementType.OBLIGATORY and not req.fulfilled
            for req in all_unfulfilled
        )
        
        final_score = calculate_score(total_requirements, fulfilled_count, has_unfulfilled_obligatory)
        final_discarded = has_unfulfilled_obligatory
        
        # Generar resumen
        evaluation_summary = self._generate_summary(
            phase1_result,
            interview_responses,
            final_score
        )
        
        return EvaluationResult(
            phase1_result=phase1_result,
            phase2_completed=True,
            interview_responses=interview_responses,
            final_score=final_score,
            final_fulfilled_requirements=all_fulfilled,
            final_unfulfilled_requirements=all_unfulfilled,
            final_discarded=final_discarded,
            evaluation_summary=evaluation_summary
        )
    
    def _generate_summary(
        self,
        phase1_result: Phase1Result,
        interview_responses: list,
        final_score: float
    ) -> str:
        """
        Genera un resumen ejecutivo de la evaluación.
        
        Args:
            phase1_result: Resultado de la Fase 1
            interview_responses: Respuestas de la entrevista
            final_score: Puntuación final
            
        Returns:
            String con el resumen
        """
        # Para simplificar, generamos un resumen estructurado
        summary_parts = [
            f"Puntuación Final: {final_score:.1f}%",
            f"\nRequisitos Cumplidos: {len(phase1_result.fulfilled_requirements)}",
            f"Requisitos No Cumplidos: {len(phase1_result.unfulfilled_requirements)}",
        ]
        
        if interview_responses:
            summary_parts.append(f"\nEntrevista Realizada: {len(interview_responses)} pregunta(s)")
        
        if phase1_result.discarded or (final_score == 0 and any(
            req.type == RequirementType.OBLIGATORY
            for req in phase1_result.unfulfilled_requirements
        )):
            summary_parts.append("\nDECISIÓN: CANDIDATO DESCARTADO (requisito obligatorio no cumplido)")
        else:
            summary_parts.append(f"\nDECISIÓN: {'APROBADO' if final_score >= 50 else 'REQUIERE REVISIÓN'}")
        
        return "\n".join(summary_parts)
    
    def record_feedback(
        self,
        score: float,
        comment: Optional[str] = None,
        run_id: Optional[str] = None
    ) -> bool:
        """
        Registra feedback del usuario para mejora continua en LangSmith.
        
        Args:
            score: Puntuación de satisfacción (0-1)
            comment: Comentario opcional del usuario
            run_id: ID del run de LangSmith (usa el último si no se especifica)
            
        Returns:
            True si el feedback se registró correctamente
        """
        if not self._langsmith_enabled:
            return False
        
        target_run_id = run_id or self._last_run_id
        if not target_run_id:
            return False
        
        try:
            langsmith = get_langsmith_client()
            if langsmith:
                langsmith.create_feedback(
                    run_id=target_run_id,
                    key="user_satisfaction",
                    score=score,
                    comment=comment or ""
                )
                return True
        except Exception:
            pass
        
        return False
    
    def get_langsmith_status(self) -> dict:
        """
        Obtiene el estado de la integración con LangSmith.
        
        Returns:
            Diccionario con información del estado
        """
        return {
            "enabled": self._langsmith_enabled,
            "last_run_id": self._last_run_id,
            "client_available": get_langsmith_client() is not None
        }


