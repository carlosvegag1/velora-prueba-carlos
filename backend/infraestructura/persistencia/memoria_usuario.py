"""
Sistema de memoria por usuario: historial de evaluaciones optimizado para RAG.
"""

import json
import logging
import re
import uuid
from typing import List, Dict, Any, Optional, Literal
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel, Field

from ...modelos import ResultadoEvaluacion, ResultadoFase1
from ...utilidades import obtener_registro_operacional

logger = logging.getLogger(__name__)


class EvaluacionEnriquecida(BaseModel):
    """Evaluación optimizada para búsqueda RAG con metadatos estructurados."""
    
    evaluation_id: str = Field(...)
    user_id: str = Field(...)
    timestamp: str = Field(...)
    score: float = Field(..., ge=0, le=100)
    status: Literal["approved", "rejected", "phase1_only"] = Field(...)
    phase_completed: Literal["phase1", "phase2"] = Field(...)
    job_offer_title: str = Field(...)
    job_offer_summary: str = Field(...)
    total_requirements: int = Field(...)
    obligatory_requirements: int = Field(...)
    optional_requirements: int = Field(...)
    fulfilled_count: int = Field(...)
    unfulfilled_obligatory_count: int = Field(...)
    unfulfilled_optional_count: int = Field(...)
    rejection_reason: Optional[str] = Field(None)
    gap_summary: Optional[str] = Field(None)
    strengths_summary: Optional[str] = Field(None)
    searchable_text: str = Field(...)
    provider: str = Field(...)
    model: str = Field(...)
    full_evaluation: Dict[str, Any] = Field(default_factory=dict)


EnrichedEvaluation = EvaluacionEnriquecida


def extraer_titulo_oferta(texto_oferta: str) -> str:
    """Extrae o genera título de oferta de empleo desde texto."""
    if not texto_oferta:
        return "Oferta de empleo"
    
    texto = texto_oferta.strip()
    texto_limpio = re.sub(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002702-\U000027B0\U0001F900-\U0001F9FF]+', '', texto)
    texto_lower = texto_limpio.lower()
    
    # Mapeo de roles conocidos
    mapeo_roles = {
        'generative ai': 'Generative AI Engineer', 'machine learning': 'Machine Learning Engineer',
        'data scientist': 'Data Scientist', 'data engineer': 'Data Engineer',
        'python developer': 'Python Developer', 'backend developer': 'Backend Developer',
        'frontend developer': 'Frontend Developer', 'fullstack': 'Fullstack Developer',
        'devops': 'DevOps Engineer', 'desarrollador python': 'Desarrollador Python',
    }
    
    for keyword, titulo in mapeo_roles.items():
        if keyword in texto_lower:
            return titulo
    
    # Buscar por patrones
    patrones = [
        r'(?:puesto|posición|rol|vacante|cargo|perfil)[\s:]+([^\n\.]{10,60})',
        r'(?:buscamos|necesitamos|contratamos)[\s:]+(?:un|una)?\s*([^\n\.]{10,60})',
    ]
    
    for patron in patrones:
        match = re.search(patron, texto_limpio, re.IGNORECASE)
        if match:
            titulo = re.sub(r'^[\-\*•#!:]+\s*', '', match.group(1).strip()).strip()
            if titulo and len(titulo) > 8:
                return titulo[:60]
    
    # Fallback por tecnologías
    tecnologias = ['python', 'java', 'javascript', 'react', 'node', 'django', 'fastapi', 'langchain', 'aws']
    for tech in tecnologias:
        if tech in texto_lower:
            if 'llm' in texto_lower or 'langchain' in texto_lower:
                return f"AI Engineer ({tech.capitalize()})"
            return f"Developer ({tech.capitalize()})"
    
    if 'senior' in texto_lower:
        return "Senior Developer"
    elif 'junior' in texto_lower:
        return "Junior Developer"
    
    return "Oferta de empleo"


extract_job_title = extraer_titulo_oferta


def crear_evaluacion_enriquecida(
    id_usuario: str,
    texto_oferta: str,
    texto_cv: str,
    resultado_fase1: ResultadoFase1,
    fase2_completada: bool = False,
    resultado_evaluacion: Optional[ResultadoEvaluacion] = None,
    proveedor: str = "openai",
    modelo: str = "gpt-4"
) -> EvaluacionEnriquecida:
    """Crea evaluación enriquecida a partir de resultados."""
    eval_id = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()
    titulo_oferta = extraer_titulo_oferta(texto_oferta)
    
    # Conteos
    cumplidos = resultado_fase1.requisitos_cumplidos
    no_cumplidos = resultado_fase1.requisitos_no_cumplidos
    
    obligatorios_cumplidos = [r for r in cumplidos if r.tipo.value == "obligatory"]
    opcionales_cumplidos = [r for r in cumplidos if r.tipo.value == "optional"]
    obligatorios_no_cumplidos = [r for r in no_cumplidos if r.tipo.value == "obligatory"]
    opcionales_no_cumplidos = [r for r in no_cumplidos if r.tipo.value == "optional"]
    
    total_obligatorios = len(obligatorios_cumplidos) + len(obligatorios_no_cumplidos)
    total_opcionales = len(opcionales_cumplidos) + len(opcionales_no_cumplidos)
    total_reqs = total_obligatorios + total_opcionales
    
    # Estado
    if resultado_fase1.descartado:
        estado = "rejected"
    elif fase2_completada and resultado_evaluacion:
        estado = "rejected" if resultado_evaluacion.descartado_final else "approved"
    else:
        estado = "phase1_only"
    
    puntuacion = resultado_evaluacion.puntuacion_final if resultado_evaluacion else resultado_fase1.puntuacion
    
    # Razón de rechazo
    razon_rechazo = None
    if estado == "rejected" and obligatorios_no_cumplidos:
        razon_rechazo = f"{len(obligatorios_no_cumplidos)} obligatorio(s) no cumplido(s): " + \
            ", ".join([r.descripcion[:50] for r in obligatorios_no_cumplidos[:3]])
    
    # Resúmenes
    resumen_brechas = ", ".join([r.descripcion for r in no_cumplidos])[:300] if no_cumplidos else None
    resumen_fortalezas = ", ".join([r.descripcion for r in cumplidos])[:300] if cumplidos else None
    
    # Texto para embeddings
    partes = [f"Evaluación: {titulo_oferta}", f"Estado: {estado}", f"Puntuación: {puntuacion:.1f}%"]
    if resumen_brechas:
        partes.append(resumen_brechas)
    if resumen_fortalezas:
        partes.append(resumen_fortalezas)
    if razon_rechazo:
        partes.append(f"Rechazado: {razon_rechazo}")
    for req in cumplidos:
        partes.append(f"Cumplido: {req.descripcion}")
    for req in no_cumplidos:
        partes.append(f"No cumplido: {req.descripcion}")
    
    texto_buscable = " | ".join(partes)
    
    eval_completa = resultado_evaluacion.model_dump() if resultado_evaluacion else {"phase1_result": resultado_fase1.model_dump()}
    
    return EvaluacionEnriquecida(
        evaluation_id=eval_id, user_id=id_usuario, timestamp=timestamp, score=puntuacion,
        status=estado, phase_completed="phase2" if fase2_completada else "phase1",
        job_offer_title=titulo_oferta, job_offer_summary=texto_oferta[:500],
        total_requirements=total_reqs, obligatory_requirements=total_obligatorios,
        optional_requirements=total_opcionales, fulfilled_count=len(cumplidos),
        unfulfilled_obligatory_count=len(obligatorios_no_cumplidos),
        unfulfilled_optional_count=len(opcionales_no_cumplidos),
        rejection_reason=razon_rechazo, gap_summary=resumen_brechas,
        strengths_summary=resumen_fortalezas, searchable_text=texto_buscable,
        provider=proveedor, model=modelo, full_evaluation=eval_completa
    )


create_enriched_evaluation = crear_evaluacion_enriquecida


class MemoriaUsuario:
    """Gestor de memoria por usuario - Evaluaciones enriquecidas."""
    
    def __init__(self, ruta_almacenamiento: str = "data/memoria_usuario"):
        self.ruta_almacenamiento = Path(ruta_almacenamiento)
        try:
            self.ruta_almacenamiento.mkdir(parents=True, exist_ok=True)
            logger.info(f"Memoria inicializada: {self.ruta_almacenamiento.absolute()}")
        except Exception as e:
            logger.error(f"Error creando directorio: {e}")
            raise
    
    @property
    def storage_path(self):
        return self.ruta_almacenamiento
    
    def guardar_evaluacion(self, enriquecida: EvaluacionEnriquecida) -> EvaluacionEnriquecida:
        archivo = self.ruta_almacenamiento / f"{enriquecida.user_id}.json"
        try:
            evaluaciones = self.obtener_evaluaciones(enriquecida.user_id)
            evaluaciones.append(enriquecida.model_dump())
            with open(archivo, "w", encoding="utf-8") as f:
                json.dump(evaluaciones, f, indent=2, ensure_ascii=False)
            logger.info(f"Evaluación guardada: {enriquecida.user_id}")
            obtener_registro_operacional().evaluacion_guardada(enriquecida.user_id, "enriquecida")
            return enriquecida
        except Exception as e:
            logger.error(f"Error guardando: {e}")
            raise
    
    save_evaluation = guardar_evaluacion
    
    def obtener_evaluaciones(self, id_usuario: str) -> List[Dict[str, Any]]:
        archivo = self.ruta_almacenamiento / f"{id_usuario}.json"
        if not archivo.exists():
            return []
        try:
            with open(archivo, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error leyendo: {e}")
            return []
    
    get_evaluations = obtener_evaluaciones
    
    def obtener_ultima_evaluacion(self, id_usuario: str) -> Optional[Dict[str, Any]]:
        evaluaciones = self.obtener_evaluaciones(id_usuario)
        if evaluaciones:
            evaluaciones.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            return evaluaciones[0]
        return None
    
    get_latest_evaluation = obtener_ultima_evaluacion
    
    def obtener_evaluaciones_rechazadas(self, id_usuario: str) -> List[Dict[str, Any]]:
        return [e for e in self.obtener_evaluaciones(id_usuario) if e.get("status") == "rejected"]
    
    get_rejected_evaluations = obtener_evaluaciones_rechazadas
    
    def obtener_evaluaciones_aprobadas(self, id_usuario: str) -> List[Dict[str, Any]]:
        return [e for e in self.obtener_evaluaciones(id_usuario) if e.get("status") == "approved"]
    
    get_approved_evaluations = obtener_evaluaciones_aprobadas
    
    def guardar_evaluacion_fase1(
        self, id_usuario: str, texto_oferta: str, texto_cv: str,
        resultado_fase1: ResultadoFase1, proveedor: Optional[str] = None, modelo: Optional[str] = None
    ) -> EvaluacionEnriquecida:
        enriquecida = crear_evaluacion_enriquecida(
            id_usuario=id_usuario, texto_oferta=texto_oferta, texto_cv=texto_cv,
            resultado_fase1=resultado_fase1, fase2_completada=False,
            resultado_evaluacion=None, proveedor=proveedor, modelo=modelo
        )
        return self.guardar_evaluacion(enriquecida)
    
    save_phase1_evaluation = guardar_evaluacion_fase1
    
    def obtener_textos_buscables(self, id_usuario: str) -> List[tuple]:
        evaluaciones = self.obtener_evaluaciones(id_usuario)
        return [
            (e.get("searchable_text", ""), {
                "evaluation_id": e.get("evaluation_id"), "timestamp": e.get("timestamp"),
                "score": e.get("score"), "status": e.get("status"),
                "job_offer_title": e.get("job_offer_title"),
                "rejection_reason": e.get("rejection_reason"),
                "gap_summary": e.get("gap_summary"), "strengths_summary": e.get("strengths_summary"),
            })
            for e in evaluaciones
        ]
    
    get_searchable_texts = obtener_textos_buscables
    
    def obtener_cantidad_evaluaciones(self, id_usuario: str) -> int:
        return len(self.obtener_evaluaciones(id_usuario))
    
    get_evaluation_count = obtener_cantidad_evaluaciones
    
    def obtener_puntuacion_promedio(self, id_usuario: str) -> Optional[float]:
        evaluaciones = self.obtener_evaluaciones(id_usuario)
        if not evaluaciones:
            return None
        puntuaciones = [e.get("score", 0) for e in evaluaciones]
        return sum(puntuaciones) / len(puntuaciones)
    
    get_average_score = obtener_puntuacion_promedio
    
    def limpiar_datos_usuario(self, id_usuario: str) -> bool:
        archivo = self.ruta_almacenamiento / f"{id_usuario}.json"
        try:
            if archivo.exists():
                archivo.unlink()
                logger.info(f"Datos eliminados: {id_usuario}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error eliminando: {e}")
            return False
    
    clear_user_data = limpiar_datos_usuario


UserMemory = MemoriaUsuario
