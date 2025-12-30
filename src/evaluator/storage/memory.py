"""
Sistema de memoria por usuario para almacenar historial de evaluaciones.
Optimizado para RAG con modelo EnrichedEvaluation.
"""

import json
import logging
import re
import uuid
from typing import List, Dict, Any, Optional, Literal
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel, Field

from ..models import EvaluationResult, Phase1Result
from ..core.logging_config import get_operational_logger

logger = logging.getLogger(__name__)


class EnrichedEvaluation(BaseModel):
    """
    Evaluación optimizada para búsqueda RAG.
    Contiene metadatos estructurados para embeddings y consultas semánticas.
    """
    # Identificación
    evaluation_id: str = Field(..., description="UUID único de la evaluación")
    user_id: str = Field(..., description="ID del usuario")
    timestamp: str = Field(..., description="Fecha y hora de la evaluación")
    
    # Estado
    score: float = Field(..., ge=0, le=100, description="Puntuación (0-100)")
    status: Literal["approved", "rejected", "phase1_only"] = Field(
        ..., description="Estado: aprobado, rechazado, o solo fase 1"
    )
    phase_completed: Literal["phase1", "phase2"] = Field(
        ..., description="Última fase completada"
    )
    
    # Oferta
    job_offer_title: str = Field(..., description="Título extraído de la oferta")
    job_offer_summary: str = Field(..., description="Primeros 500 caracteres de la oferta")
    total_requirements: int = Field(..., description="Total de requisitos")
    obligatory_requirements: int = Field(..., description="Requisitos obligatorios")
    optional_requirements: int = Field(..., description="Requisitos opcionales")
    
    # Resultados
    fulfilled_count: int = Field(..., description="Requisitos cumplidos")
    unfulfilled_obligatory_count: int = Field(..., description="Obligatorios no cumplidos")
    unfulfilled_optional_count: int = Field(..., description="Opcionales no cumplidos")
    
    # Detalles
    rejection_reason: Optional[str] = Field(None, description="Razón de rechazo")
    gap_summary: Optional[str] = Field(None, description="Resumen de brechas/carencias")
    strengths_summary: Optional[str] = Field(None, description="Resumen de fortalezas")
    
    # RAG
    searchable_text: str = Field(..., description="Texto concatenado para embeddings")
    
    # Proveedor
    provider: str = Field(..., description="Proveedor de IA")
    model: str = Field(..., description="Modelo usado")
    
    # Datos completos
    full_evaluation: Dict[str, Any] = Field(
        default_factory=dict, description="Evaluación completa serializada"
    )


def extract_job_title(job_offer_text: str) -> str:
    """
    Extrae o genera el título de una oferta de empleo.
    Busca patrones comunes y genera un título descriptivo.
    """
    if not job_offer_text:
        return "Oferta de empleo"
    
    text = job_offer_text.strip()
    text_clean = re.sub(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002702-\U000027B0\U0001F900-\U0001F9FF]+', '', text)
    text_lower = text_clean.lower()
    
    # Mapeo de palabras clave a títulos
    role_keywords = {
        'generative ai': 'Generative AI Engineer',
        'machine learning': 'Machine Learning Engineer',
        'data scientist': 'Data Scientist',
        'data engineer': 'Data Engineer',
        'data analyst': 'Data Analyst',
        'python developer': 'Python Developer',
        'backend developer': 'Backend Developer',
        'frontend developer': 'Frontend Developer',
        'fullstack': 'Fullstack Developer',
        'devops': 'DevOps Engineer',
        'cloud': 'Cloud Engineer',
        'ux/ui': 'UX/UI Designer',
        'diseñador ux': 'Diseñador UX/UI',
        'desarrollador python': 'Desarrollador Python',
        'ingeniero de software': 'Ingeniero de Software',
        'arquitecto': 'Arquitecto de Software',
    }
    
    for keyword, title in role_keywords.items():
        if keyword in text_lower:
            return title
    
    # Patrones para títulos explícitos
    patterns = [
        r'(?:puesto|posición|rol|vacante|cargo|perfil)[\s:]+([^\n\.]{10,60})',
        r'(?:buscamos|necesitamos|contratamos)[\s:]+(?:un|una)?\s*([^\n\.]{10,60})',
        r'we are hiring[!:\s]+([^\n\.]{10,60})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text_clean, re.IGNORECASE)
        if match:
            title = match.group(1).strip()
            title = re.sub(r'^[\-\*•#!:]+\s*', '', title).strip()
            if title and len(title) > 8:
                return title[:60]
    
    # Buscar tecnologías principales
    tech_found = []
    techs = ['python', 'java', 'javascript', 'react', 'node', 'django', 'fastapi', 
             'langchain', 'aws', 'azure', 'docker', 'kubernetes']
    for tech in techs:
        if tech in text_lower:
            tech_found.append(tech.capitalize())
    
    if tech_found:
        main_tech = tech_found[0]
        if 'llm' in text_lower or 'langchain' in text_lower or 'ia generativa' in text_lower:
            return f"AI Engineer ({main_tech})"
        else:
            return f"Developer ({main_tech})"
    
    # Roles genéricos
    if 'senior' in text_lower:
        return "Senior Developer"
    elif 'junior' in text_lower:
        return "Junior Developer"
    elif 'lead' in text_lower or 'líder' in text_lower:
        return "Tech Lead"
    elif 'manager' in text_lower:
        return "Project Manager"
    elif 'diseñador' in text_lower or 'designer' in text_lower:
        return "Designer"
    elif 'analyst' in text_lower or 'analista' in text_lower:
        return "Analyst"
    
    return "Oferta de empleo"


def create_enriched_evaluation(
    user_id: str,
    job_offer_text: str,
    cv_text: str,
    phase1_result: Phase1Result,
    phase2_completed: bool = False,
    evaluation_result: Optional[EvaluationResult] = None,
    provider: str = "openai",
    model: str = "gpt-4"
) -> EnrichedEvaluation:
    """
    Crea una evaluación enriquecida a partir de los resultados.
    
    Args:
        user_id: ID del usuario
        job_offer_text: Texto completo de la oferta
        cv_text: Texto del CV
        phase1_result: Resultado de la fase 1
        phase2_completed: Si se completó la fase 2
        evaluation_result: Resultado completo (si fase 2 completada)
        provider: Proveedor de IA
        model: Modelo usado
    
    Returns:
        EnrichedEvaluation lista para guardar
    """
    eval_id = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()
    job_title = extract_job_title(job_offer_text)
    
    # Calcular conteos
    fulfilled = phase1_result.fulfilled_requirements
    unfulfilled = phase1_result.unfulfilled_requirements
    
    obligatory_fulfilled = [r for r in fulfilled if r.type.value == "obligatory"]
    optional_fulfilled = [r for r in fulfilled if r.type.value == "optional"]
    obligatory_unfulfilled = [r for r in unfulfilled if r.type.value == "obligatory"]
    optional_unfulfilled = [r for r in unfulfilled if r.type.value == "optional"]
    
    total_obligatory = len(obligatory_fulfilled) + len(obligatory_unfulfilled)
    total_optional = len(optional_fulfilled) + len(optional_unfulfilled)
    total_reqs = total_obligatory + total_optional
    
    # Estado
    if phase1_result.discarded:
        status = "rejected"
    elif phase2_completed and evaluation_result:
        status = "rejected" if evaluation_result.final_discarded else "approved"
    else:
        status = "phase1_only"
    
    # Score
    score = evaluation_result.final_score if evaluation_result else phase1_result.score
    
    # Razón de rechazo
    rejection_reason = None
    if status == "rejected":
        if obligatory_unfulfilled:
            rejection_reason = f"{len(obligatory_unfulfilled)} requisito(s) obligatorio(s) no cumplido(s): " + \
                ", ".join([r.description[:50] for r in obligatory_unfulfilled[:3]])
        else:
            rejection_reason = "No cumple los requisitos mínimos"
    
    # Resumen de brechas (sin prefijo redundante, limite 300 caracteres)
    gap_summary = None
    if unfulfilled:
        gaps_text = ", ".join([r.description for r in unfulfilled])
        if len(gaps_text) > 300:
            gap_summary = gaps_text[:297] + "..."
        else:
            gap_summary = gaps_text
    
    # Resumen de fortalezas (sin prefijo redundante, limite 300 caracteres)
    strengths_summary = None
    if fulfilled:
        strengths_text = ", ".join([r.description for r in fulfilled])
        if len(strengths_text) > 300:
            strengths_summary = strengths_text[:297] + "..."
        else:
            strengths_summary = strengths_text
    
    # Texto searchable para embeddings
    searchable_parts = [
        f"Evaluación para: {job_title}",
        f"Estado: {status}",
        f"Puntuación: {score:.1f}%",
        f"Fecha: {timestamp[:10]}",
    ]
    
    if gap_summary:
        searchable_parts.append(gap_summary)
    if strengths_summary:
        searchable_parts.append(strengths_summary)
    if rejection_reason:
        searchable_parts.append(f"Rechazado porque: {rejection_reason}")
    
    for req in fulfilled:
        searchable_parts.append(f"Cumplido: {req.description}")
    for req in unfulfilled:
        searchable_parts.append(f"No cumplido: {req.description}")
    
    searchable_text = " | ".join(searchable_parts)
    
    # Evaluación completa serializada
    if evaluation_result:
        full_eval = evaluation_result.model_dump()
    else:
        full_eval = {"phase1_result": phase1_result.model_dump()}
    
    return EnrichedEvaluation(
        evaluation_id=eval_id,
        user_id=user_id,
        timestamp=timestamp,
        score=score,
        status=status,
        phase_completed="phase2" if phase2_completed else "phase1",
        job_offer_title=job_title,
        job_offer_summary=job_offer_text[:500],
        total_requirements=total_reqs,
        obligatory_requirements=total_obligatory,
        optional_requirements=total_optional,
        fulfilled_count=len(fulfilled),
        unfulfilled_obligatory_count=len(obligatory_unfulfilled),
        unfulfilled_optional_count=len(optional_unfulfilled),
        rejection_reason=rejection_reason,
        gap_summary=gap_summary,
        strengths_summary=strengths_summary,
        searchable_text=searchable_text,
        provider=provider,
        model=model,
        full_evaluation=full_eval
    )


class UserMemory:
    """Gestor de memoria por usuario - Solo evaluaciones enriquecidas"""
    
    def __init__(self, storage_path: str = "data/user_memory"):
        """
        Inicializa el gestor de memoria.
        
        Args:
            storage_path: Ruta donde se guardan los datos
        """
        self.storage_path = Path(storage_path)
        try:
            self.storage_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Directorio de memoria inicializado: {self.storage_path.absolute()}")
        except Exception as e:
            logger.error(f"Error al crear directorio de memoria: {e}")
            raise
    
    def save_evaluation(self, enriched: EnrichedEvaluation) -> EnrichedEvaluation:
        """
        Guarda una evaluación.
        
        Args:
            enriched: Evaluación a guardar
            
        Returns:
            La evaluación guardada
        """
        user_file = self.storage_path / f"{enriched.user_id}.json"
        
        try:
            evaluations = self.get_evaluations(enriched.user_id)
            evaluations.append(enriched.model_dump())
            
            with open(user_file, "w", encoding="utf-8") as f:
                json.dump(evaluations, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Evaluación guardada para {enriched.user_id}")
            
            op_logger = get_operational_logger()
            op_logger.evaluation_saved(enriched.user_id, "enriched")
            
            return enriched
        except Exception as e:
            logger.error(f"Error al guardar evaluación: {e}")
            raise
    
    def get_evaluations(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Obtiene todas las evaluaciones de un usuario.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Lista de evaluaciones
        """
        user_file = self.storage_path / f"{user_id}.json"
        
        if not user_file.exists():
            return []
        
        try:
            with open(user_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error al leer evaluaciones: {e}")
            return []
    
    def get_latest_evaluation(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene la evaluación más reciente de un usuario.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Última evaluación o None
        """
        evaluations = self.get_evaluations(user_id)
        if evaluations:
            evaluations.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            return evaluations[0]
        return None
    
    def get_rejected_evaluations(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Obtiene las evaluaciones rechazadas.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Lista de evaluaciones rechazadas
        """
        evaluations = self.get_evaluations(user_id)
        return [e for e in evaluations if e.get("status") == "rejected"]
    
    def get_approved_evaluations(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Obtiene las evaluaciones aprobadas.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Lista de evaluaciones aprobadas
        """
        evaluations = self.get_evaluations(user_id)
        return [e for e in evaluations if e.get("status") == "approved"]
    
    def save_phase1_evaluation(
        self,
        user_id: str,
        job_offer_text: str,
        cv_text: str,
        phase1_result: Phase1Result,
        provider: str = "openai",
        model: str = "gpt-4"
    ) -> EnrichedEvaluation:
        """
        Guarda una evaluación inmediatamente después de Fase 1.
        
        Args:
            user_id: ID del usuario
            job_offer_text: Texto de la oferta
            cv_text: Texto del CV
            phase1_result: Resultado de la fase 1
            provider: Proveedor de IA
            model: Modelo usado
            
        Returns:
            Evaluación guardada
        """
        enriched = create_enriched_evaluation(
            user_id=user_id,
            job_offer_text=job_offer_text,
            cv_text=cv_text,
            phase1_result=phase1_result,
            phase2_completed=False,
            evaluation_result=None,
            provider=provider,
            model=model
        )
        
        return self.save_evaluation(enriched)
    
    def get_searchable_texts(self, user_id: str) -> List[tuple]:
        """
        Obtiene los textos buscables y metadatos para indexar en vectorstore.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Lista de tuplas (searchable_text, metadata_dict)
        """
        evaluations = self.get_evaluations(user_id)
        
        results = []
        for eval_data in evaluations:
            text = eval_data.get("searchable_text", "")
            metadata = {
                "evaluation_id": eval_data.get("evaluation_id"),
                "timestamp": eval_data.get("timestamp"),
                "score": eval_data.get("score"),
                "status": eval_data.get("status"),
                "job_offer_title": eval_data.get("job_offer_title"),
                "rejection_reason": eval_data.get("rejection_reason"),
                "gap_summary": eval_data.get("gap_summary"),
                "strengths_summary": eval_data.get("strengths_summary"),
            }
            results.append((text, metadata))
        
        return results
    
    def get_evaluation_count(self, user_id: str) -> int:
        """
        Obtiene el número total de evaluaciones.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Número de evaluaciones
        """
        return len(self.get_evaluations(user_id))
    
    def get_average_score(self, user_id: str) -> Optional[float]:
        """
        Obtiene el score promedio del usuario.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Score promedio o None si no hay evaluaciones
        """
        evaluations = self.get_evaluations(user_id)
        if not evaluations:
            return None
        
        scores = [e.get("score", 0) for e in evaluations]
        return sum(scores) / len(scores)
    
    def clear_user_data(self, user_id: str) -> bool:
        """
        Elimina todos los datos de un usuario.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            True si se eliminaron los datos
        """
        user_file = self.storage_path / f"{user_id}.json"
        
        try:
            if user_file.exists():
                user_file.unlink()
                logger.info(f"Datos eliminados para usuario {user_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error al eliminar datos: {e}")
            return False
