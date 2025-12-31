"""
Fase 2: Entrevistador conversacional con streaming token-by-token.

Garantizo cobertura del 100% de requisitos faltantes mediante entrevista interactiva.
"""

import logging
from typing import List, Dict, Any, Optional, Generator

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from ...modelos import (
    ResultadoFase1, TipoRequisito, RespuestaEntrevista,
    EvaluacionRespuesta
)
from ...recursos import (
    PROMPT_EVALUAR_RESPUESTA,
    PROMPT_SISTEMA_AGENTE,
    PROMPT_SALUDO_AGENTE,
    PROMPT_PREGUNTA_AGENTE,
    PROMPT_CIERRE_AGENTE
)
from ...infraestructura.llm import FabricaLLM, ConfiguracionHiperparametros
from ...utilidades import obtener_registro_operacional

logger = logging.getLogger(__name__)


class EntrevistadorFase2:
    """
    Entrevistador conversacional de Fase 2 con streaming.
    
    Flujo: inicializar → saludo → preguntas → registrar respuestas → cierre.
    """
    
    def __init__(
        self,
        llm: Optional[BaseChatModel] = None,
        proveedor: Optional[str] = None,
        nombre_modelo: Optional[str] = None,
        temperatura: Optional[float] = None,
        api_key: Optional[str] = None
    ):
        """Inicializa el entrevistador con LLMs diferenciados para conversación y evaluación."""
        self.proveedor = proveedor
        self.api_key = api_key
        self._registro = obtener_registro_operacional()
        
        temp_entrevista = temperatura if temperatura is not None else ConfiguracionHiperparametros.obtener_temperatura("phase2_interview")
        temp_evaluacion = ConfiguracionHiperparametros.obtener_temperatura("phase2_evaluation")
        
        if llm is None:
            self.llm = FabricaLLM.crear_llm(
                proveedor=proveedor,
                nombre_modelo=nombre_modelo,
                temperatura=temp_entrevista,
                api_key=api_key
            )
        else:
            self.llm = llm
        
        self._llm_evaluacion = FabricaLLM.crear_llm(
            proveedor=proveedor,
            nombre_modelo=nombre_modelo,
            temperatura=temp_evaluacion,
            api_key=api_key
        ).with_structured_output(EvaluacionRespuesta)
        
        self._nombre_candidato: str = ""
        self._contexto_cv: str = ""
        self._requisitos_pendientes: List[Dict[str, Any]] = []
        self._historial_conversacion: List[Dict[str, str]] = []
        self._indice_actual: int = 0
        
        self._registro.info("EntrevistadorFase2 inicializado")
    
    def inicializar_entrevista(
        self,
        nombre_candidato: str,
        resultado_fase1: ResultadoFase1,
        contexto_cv: str
    ) -> Dict[str, Any]:
        """Configura una nueva sesión de entrevista a partir del resultado de Fase 1."""
        self._historial_conversacion = []
        self._indice_actual = 0
        self._nombre_candidato = nombre_candidato or "candidato"
        self._contexto_cv = contexto_cv[:2000]
        
        self._requisitos_pendientes = []
        mapa_tipos = {
            req.descripcion.lower(): req.tipo.value
            for req in resultado_fase1.requisitos_no_cumplidos
        }
        
        for desc_req in resultado_fase1.requisitos_faltantes:
            tipo_req = mapa_tipos.get(desc_req.lower(), "optional")
            self._requisitos_pendientes.append({
                "description": desc_req,
                "type": tipo_req,
                "asked": False,
                "answered": False,
                "response": None
            })
        
        self._registro.fase2_inicio(len(self._requisitos_pendientes))
        
        return {
            "candidate_name": self._nombre_candidato,
            "total_questions": len(self._requisitos_pendientes),
            "status": "initialized"
        }
    
    initialize_interview = inicializar_entrevista
    
    def transmitir_saludo(self) -> Generator[str, None, None]:
        """Genera saludo inicial con streaming token-by-token."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", PROMPT_SISTEMA_AGENTE.format(
                nombre_candidato=self._nombre_candidato,
                requisitos_pendientes=len(self._requisitos_pendientes),
                resumen_cv=self._contexto_cv[:500]
            )),
            ("human", PROMPT_SALUDO_AGENTE.format(
                nombre_candidato=self._nombre_candidato,
                cantidad_preguntas=len(self._requisitos_pendientes)
            ))
        ])
        
        chain = prompt | self.llm | StrOutputParser()
        
        saludo = ""
        try:
            for chunk in chain.stream({}):
                saludo += chunk
                yield chunk
            
            self._historial_conversacion.append({
                "role": "assistant", "content": saludo, "type": "greeting"
            })
            self._registro.info("Saludo generado con streaming")
            
        except Exception as e:
            logger.error(f"Error en saludo: {e}")
            fallback = f"¡Hola {self._nombre_candidato}! He revisado tu CV y tengo {len(self._requisitos_pendientes)} pregunta(s) para ti. ¿Comenzamos?"
            self._historial_conversacion.append({
                "role": "assistant", "content": fallback, "type": "greeting"
            })
            yield fallback
    
    stream_greeting = transmitir_saludo
    
    def transmitir_pregunta(self, indice_pregunta: int) -> Generator[str, None, None]:
        """Genera una pregunta específica con streaming."""
        if indice_pregunta >= len(self._requisitos_pendientes):
            yield "No hay más preguntas pendientes."
            return
        
        requisito = self._requisitos_pendientes[indice_pregunta]
        historial_texto = self._construir_contexto_conversacion()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", PROMPT_SISTEMA_AGENTE.format(
                nombre_candidato=self._nombre_candidato,
                requisitos_pendientes=len(self._requisitos_pendientes) - indice_pregunta,
                resumen_cv=self._contexto_cv[:500]
            )),
            ("human", PROMPT_PREGUNTA_AGENTE.format(
                requisito=requisito["description"],
                tipo_requisito="OBLIGATORIO" if requisito["type"] == "obligatory" else "DESEABLE",
                numero_actual=indice_pregunta + 1,
                total_preguntas=len(self._requisitos_pendientes),
                contexto_cv=self._contexto_cv[:800],
                historial_conversacion=historial_texto
            ))
        ])
        
        chain = prompt | self.llm | StrOutputParser()
        
        texto_pregunta = ""
        try:
            for chunk in chain.stream({}):
                texto_pregunta += chunk
                yield chunk
            
            self._requisitos_pendientes[indice_pregunta]["asked"] = True
            self._historial_conversacion.append({
                "role": "assistant",
                "content": texto_pregunta,
                "type": "question",
                "requirement_idx": indice_pregunta,
                "requirement": requisito["description"]
            })
            self._indice_actual = indice_pregunta
            
            self._registro.fase2_pregunta(indice_pregunta + 1, len(self._requisitos_pendientes))
            
        except Exception as e:
            logger.error(f"Error generando pregunta: {e}")
            fallback = f"¿Podrías describir tu experiencia con {requisito['description']}?"
            self._requisitos_pendientes[indice_pregunta]["asked"] = True
            self._historial_conversacion.append({
                "role": "assistant",
                "content": fallback,
                "type": "question",
                "requirement_idx": indice_pregunta,
                "requirement": requisito["description"]
            })
            yield fallback
    
    stream_question = transmitir_pregunta
    
    def transmitir_cierre(self) -> Generator[str, None, None]:
        """Genera mensaje de cierre con streaming."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", PROMPT_SISTEMA_AGENTE.format(
                nombre_candidato=self._nombre_candidato,
                requisitos_pendientes=0,
                resumen_cv=self._contexto_cv[:300]
            )),
            ("human", PROMPT_CIERRE_AGENTE.format(
                nombre_candidato=self._nombre_candidato
            ))
        ])
        
        chain = prompt | self.llm | StrOutputParser()
        
        cierre = ""
        try:
            for chunk in chain.stream({}):
                cierre += chunk
                yield chunk
            
            self._historial_conversacion.append({
                "role": "assistant", "content": cierre, "type": "closing"
            })
            self._registro.info("Cierre generado con streaming")
            
        except Exception as e:
            logger.error(f"Error en cierre: {e}")
            fallback = f"¡Perfecto, {self._nombre_candidato}! Gracias por tus respuestas. Procesaré la información para completar tu evaluación."
            self._historial_conversacion.append({
                "role": "assistant", "content": fallback, "type": "closing"
            })
            yield fallback
    
    stream_closing = transmitir_cierre
    
    def registrar_respuesta(self, indice_pregunta: int, respuesta: str) -> Dict[str, Any]:
        """Registra la respuesta del candidato para una pregunta específica."""
        if indice_pregunta >= len(self._requisitos_pendientes):
            return {"error": "Índice fuera de rango"}
        
        requisito = self._requisitos_pendientes[indice_pregunta]
        requisito["answered"] = True
        requisito["response"] = respuesta
        
        self._historial_conversacion.append({
            "role": "user",
            "content": respuesta,
            "type": "response",
            "requirement_idx": indice_pregunta
        })
        
        es_completo = indice_pregunta + 1 >= len(self._requisitos_pendientes)
        
        self._registro.info(f"Respuesta registrada para pregunta {indice_pregunta + 1}")
        
        return {
            "question_idx": indice_pregunta,
            "registered": True,
            "next_question": None if es_completo else indice_pregunta + 1,
            "is_complete": es_completo
        }
    
    register_response = registrar_respuesta
    
    def evaluar_respuesta(
        self,
        descripcion_requisito: str,
        tipo_requisito: TipoRequisito,
        contexto_cv: str,
        respuesta_candidato: str
    ) -> Dict[str, Any]:
        """Evalúa si la respuesta del candidato cumple un requisito."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", PROMPT_EVALUAR_RESPUESTA),
            ("human", """Requisito: {requirement_description}
Tipo: {requirement_type}

Contexto del CV:
{cv_context}

Respuesta del candidato:
{candidate_response}""")
        ])
        
        chain = prompt | self._llm_evaluacion
        
        try:
            resultado: EvaluacionRespuesta = chain.invoke({
                "requirement_description": descripcion_requisito,
                "requirement_type": tipo_requisito.value if isinstance(tipo_requisito, TipoRequisito) else tipo_requisito,
                "cv_context": contexto_cv[:1500],
                "candidate_response": respuesta_candidato
            })
            
            return {
                "fulfilled": resultado.fulfilled,
                "evidence": resultado.evidence.strip() if resultado.evidence else None,
                "confidence": resultado.confidence
            }
        except Exception as e:
            logger.error(f"Error evaluando respuesta: {e}")
            return {"fulfilled": False, "evidence": None, "confidence": "low"}
    
    evaluate_response = evaluar_respuesta
    
    def obtener_respuestas_entrevista(self) -> List[RespuestaEntrevista]:
        """Obtiene las respuestas formateadas para el sistema de evaluación."""
        respuestas = []
        
        for i, req in enumerate(self._requisitos_pendientes):
            if not req["answered"] or not req["response"]:
                continue
            
            texto_pregunta = self._buscar_pregunta_para_requisito(i)
            
            respuestas.append(RespuestaEntrevista(
                pregunta=texto_pregunta,
                respuesta=req["response"],
                descripcion_requisito=req["description"],
                tipo_requisito=TipoRequisito(req["type"])
            ))
        
        return respuestas
    
    get_interview_responses = obtener_respuestas_entrevista
    
    def obtener_estado(self) -> Dict[str, Any]:
        """Obtiene el estado actual de la entrevista."""
        respondidas = sum(1 for r in self._requisitos_pendientes if r["answered"])
        
        return {
            "candidate_name": self._nombre_candidato,
            "total_requirements": len(self._requisitos_pendientes),
            "current_idx": self._indice_actual,
            "answered_count": respondidas,
            "is_complete": respondidas >= len(self._requisitos_pendientes),
            "pending_requirements": [
                {"description": r["description"], "type": r["type"],
                 "asked": r["asked"], "answered": r["answered"]}
                for r in self._requisitos_pendientes
            ]
        }
    
    get_state = obtener_estado
    
    def validar_cobertura(self) -> Dict[str, Any]:
        """Valida la cobertura de requisitos (para auditoría)."""
        total = len(self._requisitos_pendientes)
        preguntados = sum(1 for r in self._requisitos_pendientes if r["asked"])
        respondidos = sum(1 for r in self._requisitos_pendientes if r["answered"])
        
        no_cubiertos = [
            r["description"] for r in self._requisitos_pendientes
            if not r["answered"]
        ]
        
        cobertura = (respondidos / total * 100) if total > 0 else 100.0
        
        self._registro.fase2_completa(respondidos, cobertura)
        
        return {
            "total_requirements": total,
            "asked_count": preguntados,
            "answered_count": respondidos,
            "coverage_percentage": cobertura,
            "uncovered_requirements": no_cubiertos,
            "is_complete": len(no_cubiertos) == 0
        }
    
    validate_coverage = validar_cobertura
    
    def _construir_contexto_conversacion(self) -> str:
        """Construye contexto de conversación para mantener coherencia."""
        if not self._historial_conversacion:
            return "Sin historial previo"
        
        partes = []
        for entrada in self._historial_conversacion[-4:]:
            rol = "Entrevistador" if entrada["role"] == "assistant" else "Candidato"
            contenido = entrada["content"][:200]
            partes.append(f"{rol}: {contenido}")
        
        return "\n".join(partes)
    
    def _buscar_pregunta_para_requisito(self, indice_requisito: int) -> str:
        """Busca la pregunta generada para un requisito específico."""
        for entrada in self._historial_conversacion:
            if entrada.get("type") == "question" and entrada.get("requirement_idx") == indice_requisito:
                return entrada["content"]
        
        req = self._requisitos_pendientes[indice_requisito]
        return f"¿Podrías describir tu experiencia con {req['description']}?"


Phase2Interviewer = EntrevistadorFase2
AgenticInterviewer = EntrevistadorFase2
