"""
Grafo LangGraph para orquestacion multi-agente de la Fase 1.

Incluye normalizacion atomica y contexto temporal para reproducibilidad.
Flujo: extraer_requisitos -> embeber_cv -> matching_semantico -> calcular_puntuacion
"""

import re
from typing import TypedDict, List, Optional, Dict, Annotated
from operator import add
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate

from langgraph.graph import StateGraph, END

from ..modelos import (
    Requisito, TipoRequisito, ResultadoFase1,
    RespuestaExtraccionRequisitos, RespuestaMatchingCV
)
from ..recursos import PROMPT_EXTRACCION_REQUISITOS, PROMPT_MATCHING_CV
from ..utilidades import (
    calcular_puntuacion, procesar_coincidencias,
    agregar_requisitos_no_procesados, obtener_registro_operacional
)
from ..utilidades.normalizacion import normalizar_requisitos
from ..utilidades.contexto_temporal import obtener_contexto_prompt
from ..infraestructura.llm import ComparadorSemantico


class EstadoFase1(TypedDict):
    oferta_trabajo: str
    cv: str
    requisitos: List[dict]
    evidencia_semantica: Dict[str, dict]
    coincidencias: List[dict]
    requisitos_cumplidos: List[Requisito]
    requisitos_no_cumplidos: List[Requisito]
    requisitos_faltantes: List[str]
    puntuacion: float
    descartado: bool
    resumen_analisis: str
    error: Optional[str]
    mensajes: Annotated[List[str], add]


Phase1State = EstadoFase1


def crear_nodo_extraccion(llm: BaseChatModel):
    """Nodo que extrae requisitos con granularidad atomica."""
    llm_extraccion = llm.with_structured_output(RespuestaExtraccionRequisitos)
    
    def extraer_requisitos(estado: EstadoFase1) -> dict:
        registro = obtener_registro_operacional()
        registro.nodo_langgraph("extraer_requisitos", "ejecutando")
        
        oferta = estado["oferta_trabajo"]
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", PROMPT_EXTRACCION_REQUISITOS),
            ("human", "{job_offer}")
        ])
        
        chain = prompt | llm_extraccion
        
        try:
            resultado: RespuestaExtraccionRequisitos = chain.invoke({"job_offer": oferta})
            
            requisitos_raw = []
            vistos = set()
            
            for req in resultado.requirements:
                normalizado = req.description.lower().strip()
                if normalizado not in vistos:
                    vistos.add(normalizado)
                    requisitos_raw.append({
                        "description": req.description.strip(),
                        "type": req.type
                    })
            
            requisitos = normalizar_requisitos(requisitos_raw)
            
            if not requisitos:
                return {
                    "error": "No se encontraron requisitos en la oferta",
                    "requisitos": [],
                    "mensajes": ["[WARN] No se encontraron requisitos"]
                }
            
            return {
                "requisitos": requisitos,
                "mensajes": [f"[OK] Extraidos {len(requisitos)} requisitos (normalizados)"]
            }
        except Exception as e:
            return {
                "error": f"Error en extraccion: {str(e)}",
                "requisitos": [],
                "mensajes": [f"[ERROR] {str(e)}"]
            }
    
    return extraer_requisitos


create_extract_node = crear_nodo_extraccion


def crear_nodo_embedding(comparador_semantico: Optional[ComparadorSemantico]):
    
    def embeber_cv(estado: EstadoFase1) -> dict:
        registro = obtener_registro_operacional()
        registro.nodo_langgraph("embeber_cv", "ejecutando")
        
        if estado.get("error"):
            return {"evidencia_semantica": {}, "mensajes": ["[SKIP] Embeddings (error previo)"]}
        
        cv = estado["cv"]
        requisitos = estado["requisitos"]
        
        if not comparador_semantico or not requisitos:
            return {
                "evidencia_semantica": {},
                "mensajes": ["[SKIP] Embeddings deshabilitados o sin requisitos"]
            }
        
        try:
            comparador_semantico.indexar_cv(cv)
            
            mapa_evidencia = {}
            for req in requisitos:
                desc = req["description"]
                evidencia = comparador_semantico.encontrar_evidencia(desc, k=2)
                
                if evidencia:
                    mejor_texto, mejor_score = evidencia[0]
                    mapa_evidencia[desc.lower()] = {
                        "text": mejor_texto,
                        "semantic_score": mejor_score,
                        "all_evidence": evidencia
                    }
            
            comparador_semantico.limpiar()
            
            return {
                "evidencia_semantica": mapa_evidencia,
                "mensajes": [f"[OK] Evidencia semantica para {len(mapa_evidencia)} requisitos"]
            }
        except Exception as e:
            return {
                "evidencia_semantica": {},
                "mensajes": [f"[WARN] Embeddings fallaron: {str(e)}"]
            }
    
    return embeber_cv


create_embed_node = crear_nodo_embedding


def crear_nodo_matching(llm: BaseChatModel):
    """Nodo que evalua requisitos con contexto temporal."""
    llm_matching = llm.with_structured_output(RespuestaMatchingCV)
    
    def matching_cv(estado: EstadoFase1) -> dict:
        registro = obtener_registro_operacional()
        registro.nodo_langgraph("matching_semantico", "ejecutando")
        
        if estado.get("error"):
            return {"coincidencias": [], "mensajes": ["[SKIP] Matching (error previo)"]}
        
        cv = estado["cv"]
        requisitos = estado["requisitos"]
        evidencia_semantica = estado.get("evidencia_semantica", {})
        
        if not requisitos:
            return {
                "coincidencias": [],
                "resumen_analisis": "No hay requisitos para evaluar",
                "mensajes": ["[WARN] Sin requisitos para evaluar"]
            }
        
        lineas = []
        for req in requisitos:
            linea = f"- [{req['type'].upper()}] {req['description']}"
            
            ev_sem = evidencia_semantica.get(req['description'].lower())
            if ev_sem and ev_sem.get('semantic_score', 0) > 0.4:
                linea += f"\n  [PISTA SEMANTICA - Score: {ev_sem['semantic_score']:.2f}]: \"{ev_sem['text'][:150]}...\""
            
            lineas.append(linea)
        
        texto_requisitos = "\n".join(lineas)
        contexto_temporal = obtener_contexto_prompt()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", PROMPT_MATCHING_CV),
            ("human", f"CONTEXTO TEMPORAL: {contexto_temporal}\n\nCV del candidato:\n{{cv}}\n\nRequisitos a evaluar:\n{{requirements_list}}")
        ])
        
        chain = prompt | llm_matching
        
        try:
            resultado: RespuestaMatchingCV = chain.invoke({
                "cv": cv,
                "requirements_list": texto_requisitos
            })
            
            coincidencias = []
            for match in resultado.matches:
                match_dict = {
                    "requirement_description": match.requirement_description.strip(),
                    "fulfilled": match.fulfilled,
                    "found_in_cv": match.found_in_cv,
                    "evidence": match.evidence.strip() if match.evidence else None,
                    "confidence": match.confidence,
                    "reasoning": match.reasoning.strip() if match.reasoning else None,
                    "semantic_score": None
                }
                
                if evidencia_semantica:
                    desc_lower = match.requirement_description.lower().strip()
                    desc_limpia = re.sub(r'^\s*\[(OBLIGATORY|OPTIONAL)\]\s*', '', desc_lower, flags=re.IGNORECASE)
                    ev_sem = evidencia_semantica.get(desc_limpia)
                    if ev_sem:
                        match_dict["semantic_score"] = ev_sem.get("semantic_score")
                
                coincidencias.append(match_dict)
            
            cumplidos = sum(1 for m in coincidencias if m["fulfilled"])
            
            return {
                "coincidencias": coincidencias,
                "resumen_analisis": resultado.analysis_summary,
                "mensajes": [f"[OK] Matching completado: {cumplidos}/{len(coincidencias)} cumplidos"]
            }
        except Exception as e:
            return {
                "coincidencias": [],
                "resumen_analisis": f"Error: {str(e)}",
                "error": f"Error en matching: {str(e)}",
                "mensajes": [f"[ERROR] Error en matching: {str(e)}"]
            }
    
    return matching_cv


create_match_node = crear_nodo_matching


def crear_nodo_puntuacion():
    
    def calcular_puntuacion_final(estado: EstadoFase1) -> dict:
        registro = obtener_registro_operacional()
        registro.nodo_langgraph("calcular_puntuacion", "ejecutando")
        
        if estado.get("error"):
            return {
                "puntuacion": 0.0,
                "descartado": True,
                "requisitos_cumplidos": [],
                "requisitos_no_cumplidos": [],
                "requisitos_faltantes": [],
                "mensajes": ["[ERROR] Evaluacion fallida por error previo"]
            }
        
        requisitos = estado["requisitos"]
        coincidencias = estado["coincidencias"]
        evidencia_semantica = estado.get("evidencia_semantica", {})
        
        req_cumplidos, req_no_cumplidos, req_faltantes, procesados = \
            procesar_coincidencias(coincidencias, requisitos, evidencia_semantica)
        
        agregar_requisitos_no_procesados(
            requisitos, procesados, req_no_cumplidos, req_faltantes
        )
        
        total = len(requisitos)
        cumplidos = len(req_cumplidos)
        tiene_obligatorio_no_cumplido = any(
            req.tipo == TipoRequisito.OBLIGATORIO
            for req in req_no_cumplidos
        )
        
        puntuacion = calcular_puntuacion(total, cumplidos, tiene_obligatorio_no_cumplido)
        
        estado_texto = "DESCARTADO" if tiene_obligatorio_no_cumplido else f"Score: {puntuacion:.1f}%"
        
        return {
            "puntuacion": puntuacion,
            "descartado": tiene_obligatorio_no_cumplido,
            "requisitos_cumplidos": req_cumplidos,
            "requisitos_no_cumplidos": req_no_cumplidos,
            "requisitos_faltantes": req_faltantes,
            "mensajes": [f"[END] Resultado: {estado_texto}"]
        }
    
    return calcular_puntuacion_final


create_score_node = crear_nodo_puntuacion


def crear_grafo_fase1(
    llm: BaseChatModel,
    comparador_semantico: Optional[ComparadorSemantico] = None
) -> StateGraph:
    nodo_extraccion = crear_nodo_extraccion(llm)
    nodo_embedding = crear_nodo_embedding(comparador_semantico)
    nodo_matching = crear_nodo_matching(llm)
    nodo_puntuacion = crear_nodo_puntuacion()
    
    grafo = StateGraph(EstadoFase1)
    
    grafo.add_node("extraer_requisitos", nodo_extraccion)
    grafo.add_node("embeber_cv", nodo_embedding)
    grafo.add_node("matching_semantico", nodo_matching)
    grafo.add_node("calcular_puntuacion", nodo_puntuacion)
    
    grafo.set_entry_point("extraer_requisitos")
    grafo.add_edge("extraer_requisitos", "embeber_cv")
    grafo.add_edge("embeber_cv", "matching_semantico")
    grafo.add_edge("matching_semantico", "calcular_puntuacion")
    grafo.add_edge("calcular_puntuacion", END)
    
    return grafo.compile()


create_phase1_graph = crear_grafo_fase1


def ejecutar_grafo_fase1(grafo, oferta_trabajo: str, cv: str) -> ResultadoFase1:
    estado_inicial: EstadoFase1 = {
        "oferta_trabajo": oferta_trabajo,
        "cv": cv,
        "requisitos": [],
        "evidencia_semantica": {},
        "coincidencias": [],
        "requisitos_cumplidos": [],
        "requisitos_no_cumplidos": [],
        "requisitos_faltantes": [],
        "puntuacion": 0.0,
        "descartado": False,
        "resumen_analisis": "",
        "error": None,
        "mensajes": []
    }
    
    estado_final = grafo.invoke(estado_inicial)
    
    if estado_final.get("error"):
        raise ValueError(estado_final["error"])
    
    return ResultadoFase1(
        puntuacion=estado_final["puntuacion"],
        descartado=estado_final["descartado"],
        requisitos_cumplidos=estado_final["requisitos_cumplidos"],
        requisitos_no_cumplidos=estado_final["requisitos_no_cumplidos"],
        requisitos_faltantes=estado_final["requisitos_faltantes"],
        resumen_analisis=estado_final.get("resumen_analisis", "")
    )


run_phase1_graph = ejecutar_grafo_fase1


async def ejecutar_grafo_fase1_streaming(grafo, oferta_trabajo: str, cv: str):
    estado_inicial: EstadoFase1 = {
        "oferta_trabajo": oferta_trabajo,
        "cv": cv,
        "requisitos": [],
        "evidencia_semantica": {},
        "coincidencias": [],
        "requisitos_cumplidos": [],
        "requisitos_no_cumplidos": [],
        "requisitos_faltantes": [],
        "puntuacion": 0.0,
        "descartado": False,
        "resumen_analisis": "",
        "error": None,
        "mensajes": []
    }
    
    async for estado in grafo.astream(estado_inicial):
        for nombre_nodo, salida_nodo in estado.items():
            yield {
                "node": nombre_nodo,
                "messages": salida_nodo.get("mensajes", []),
                "state": salida_nodo
            }


run_phase1_graph_streaming = ejecutar_grafo_fase1_streaming
