"""
Fase 1: Extraccion de requisitos de ofertas y matching con CV.

Uso Structured Output para respuestas validas garantizadas.
Incluye normalizacion atomica post-extraccion para reproducibilidad.
"""

import re
import time
from typing import List, Optional, Dict, AsyncGenerator
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate

from ...modelos import (
    ResultadoFase1, TipoRequisito,
    RespuestaExtraccionRequisitos, RespuestaMatchingCV
)
from ...recursos import PROMPT_EXTRACCION_REQUISITOS, PROMPT_MATCHING_CV
from ...infraestructura.llm import (
    FabricaLLM, FabricaEmbeddings,
    ConfiguracionHiperparametros, ComparadorSemantico
)
from ...utilidades import (
    calcular_puntuacion, procesar_coincidencias,
    agregar_requisitos_no_procesados, obtener_registro_operacional
)
from ...utilidades.normalizacion import normalizar_requisitos
from ...utilidades.contexto_temporal import obtener_contexto_prompt


class AnalizadorFase1:
    """
    Analizador de Fase 1: Extrae requisitos y evalua su cumplimiento contra el CV.
    
    Garantiza:
    - Granularidad atomica mediante normalizacion post-extraccion
    - Contexto temporal consistente en todas las evaluaciones
    - Reproducibilidad del 100% en extraccion de requisitos
    """
    
    def __init__(
        self,
        llm: Optional[BaseChatModel] = None,
        proveedor: Optional[str] = None,
        nombre_modelo: Optional[str] = None,
        temperatura: Optional[float] = None,
        api_key: Optional[str] = None,
        usar_matching_semantico: bool = True,
        usar_langgraph: bool = False
    ):
        self.proveedor = proveedor
        self.api_key = api_key
        self.usar_matching_semantico = usar_matching_semantico
        self.usar_langgraph = usar_langgraph
        self._registro = obtener_registro_operacional()
        
        temp_efectiva = temperatura if temperatura is not None else ConfiguracionHiperparametros.obtener_temperatura("phase1_extraction")
        
        self._embeddings_disponibles = FabricaEmbeddings.soporta_embeddings(proveedor)
        self._advertencia_embeddings = FabricaEmbeddings.obtener_mensaje_proveedor(proveedor)
        
        if llm is None:
            self.llm = FabricaLLM.crear_llm(
                proveedor=proveedor,
                nombre_modelo=nombre_modelo,
                temperatura=temp_efectiva,
                api_key=api_key
            )
        else:
            self.llm = llm
        
        self._registro.config_proveedor(proveedor, nombre_modelo)
        
        self.llm_extraccion = self.llm.with_structured_output(RespuestaExtraccionRequisitos)
        self.llm_matching = self.llm.with_structured_output(RespuestaMatchingCV)
        
        self.comparador_semantico: Optional[ComparadorSemantico] = None
        if usar_matching_semantico:
            self._inicializar_comparador_semantico(proveedor, api_key)
        else:
            self._registro.config_semantic(habilitado=False)
        
        self._grafo = None
        if usar_langgraph:
            self._inicializar_langgraph()
            self._registro.config_langgraph(habilitado=True)
        else:
            self._registro.config_langgraph(habilitado=False)
    
    def _inicializar_comparador_semantico(self, proveedor: str, api_key: Optional[str]):
        try:
            if FabricaEmbeddings.soporta_embeddings(proveedor):
                proveedor_embeddings = proveedor
                api_key_embeddings = api_key
            else:
                fallback = FabricaEmbeddings.obtener_proveedor_fallback(excluir_proveedor=proveedor)
                if fallback:
                    proveedor_embeddings = fallback
                    api_key_embeddings = None
                    self._registro.info(f"Embeddings: usando {fallback} como fallback")
                else:
                    self.comparador_semantico = None
                    self._registro.config_semantic(
                        habilitado=True, inicializado=False,
                        razon="No hay proveedor de embeddings disponible"
                    )
                    return
            
            self.comparador_semantico = ComparadorSemantico(
                proveedor_embeddings=proveedor_embeddings,
                api_key=api_key_embeddings
            )
            self._registro.config_semantic(habilitado=True, inicializado=True)
            
        except Exception as e:
            self.comparador_semantico = None
            self._registro.config_semantic(habilitado=True, inicializado=False, razon=str(e))
    
    def _inicializar_langgraph(self):
        try:
            from ...orquestacion.grafo_fase1 import crear_grafo_fase1
            self._grafo = crear_grafo_fase1(self.llm, self.comparador_semantico)
        except ImportError:
            self._grafo = None
            self.usar_langgraph = False
    
    def obtener_estado_embeddings(self) -> dict:
        return {
            "disponible": self._embeddings_disponibles,
            "habilitado": self.usar_matching_semantico,
            "inicializado": self.comparador_semantico is not None,
            "proveedor": self.comparador_semantico.proveedor if self.comparador_semantico else None,
            "advertencia": self._advertencia_embeddings
        }
    
    get_embedding_status = obtener_estado_embeddings
    
    def extraer_requisitos(self, oferta_trabajo: str) -> List[dict]:
        """
        Extrae requisitos de una oferta de trabajo con granularidad atomica.
        Aplica normalizacion post-extraccion para descomponer requisitos compuestos.
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", PROMPT_EXTRACCION_REQUISITOS),
            ("human", "{job_offer}")
        ])
        
        chain = prompt | self.llm_extraccion
        resultado: RespuestaExtraccionRequisitos = chain.invoke({"job_offer": oferta_trabajo})
        
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
        
        requisitos_normalizados = normalizar_requisitos(requisitos_raw)
        
        return requisitos_normalizados
    
    extract_requirements = extraer_requisitos
    
    def _obtener_evidencia_semantica(self, cv: str, requisitos: List[dict]) -> Dict[str, dict]:
        if not self.comparador_semantico:
            return {}
        
        try:
            self.comparador_semantico.indexar_cv(cv)
            
            mapa_evidencia = {}
            for req in requisitos:
                desc = req["description"]
                evidencia = self.comparador_semantico.encontrar_evidencia(desc, k=2)
                
                if evidencia:
                    mejor_texto, mejor_score = evidencia[0]
                    mapa_evidencia[desc.lower()] = {
                        "text": mejor_texto,
                        "semantic_score": mejor_score,
                        "all_evidence": evidencia
                    }
            
            return mapa_evidencia
        except Exception:
            return {}
        finally:
            if self.comparador_semantico:
                self.comparador_semantico.limpiar()
    
    def evaluar_cv_con_requisitos(
        self,
        cv: str,
        requisitos: List[dict],
        evidencia_semantica: Optional[Dict[str, dict]] = None
    ) -> dict:
        """
        Evalua que requisitos se cumplen segun el CV.
        Incluye contexto temporal para calculo preciso de experiencia.
        """
        if not requisitos:
            return {"matches": [], "analysis_summary": "No hay requisitos para evaluar."}
        
        lineas = []
        for req in requisitos:
            linea = f"- [{req['type'].upper()}] {req['description']}"
            
            if evidencia_semantica:
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
        
        chain = prompt | self.llm_matching
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
        
        return {"matches": coincidencias, "analysis_summary": resultado.analysis_summary}
    
    match_cv_with_requirements = evaluar_cv_con_requisitos
    
    def analizar(self, oferta_trabajo: str, cv: str) -> ResultadoFase1:
        tiempo_inicio = time.time()
        
        if self.usar_langgraph and self._grafo:
            self._registro.fase1_inicio(modo="langgraph")
            resultado = self._analizar_con_langgraph(oferta_trabajo, cv)
        else:
            self._registro.fase1_inicio(modo="tradicional")
            resultado = self._analizar_tradicional(oferta_trabajo, cv)
        
        duracion_ms = int((time.time() - tiempo_inicio) * 1000)
        self._registro.fase1_completa(
            descartado=resultado.descartado,
            puntuacion=resultado.puntuacion,
            duracion_ms=duracion_ms
        )
        
        return resultado
    
    analyze = analizar
    
    def _analizar_con_langgraph(self, oferta_trabajo: str, cv: str) -> ResultadoFase1:
        from ...orquestacion.grafo_fase1 import ejecutar_grafo_fase1
        return ejecutar_grafo_fase1(self._grafo, oferta_trabajo, cv)
    
    async def analizar_streaming(self, oferta_trabajo: str, cv: str) -> AsyncGenerator[dict, None]:
        if not self.usar_langgraph or not self._grafo:
            yield {"node": "start", "messages": ["[START] Iniciando analisis..."]}
            resultado = self._analizar_tradicional(oferta_trabajo, cv)
            yield {"node": "complete", "messages": ["[OK] Analisis completado"], "result": resultado}
            return
        
        from ...orquestacion.grafo_fase1 import ejecutar_grafo_fase1_streaming
        
        resultado_final = None
        async for actualizacion in ejecutar_grafo_fase1_streaming(self._grafo, oferta_trabajo, cv):
            yield actualizacion
            if actualizacion.get("node") == "calcular_puntuacion":
                resultado_final = actualizacion.get("state")
        
        if resultado_final:
            yield {"node": "complete", "result": resultado_final}
    
    analyze_streaming = analizar_streaming
    
    def _analizar_tradicional(self, oferta_trabajo: str, cv: str) -> ResultadoFase1:
        requisitos = self.extraer_requisitos(oferta_trabajo)
        
        if not requisitos:
            raise ValueError(
                "No se encontraron requisitos en la oferta de trabajo. "
                "La oferta debe contener secciones explicitas de requisitos."
            )
        
        obligatorios = sum(1 for r in requisitos if r["type"] == "obligatory")
        opcionales = len(requisitos) - obligatorios
        self._registro.extraccion_completa(len(requisitos), obligatorios, opcionales)
        
        evidencia_semantica = {}
        if self.usar_matching_semantico and self.comparador_semantico:
            evidencia_semantica = self._obtener_evidencia_semantica(cv, requisitos)
            self._registro.evidencia_semantica_encontrada(len(evidencia_semantica), len(requisitos))
        
        resultado_matching = self.evaluar_cv_con_requisitos(cv, requisitos, evidencia_semantica)
        coincidencias = resultado_matching["matches"]
        resumen_analisis = resultado_matching["analysis_summary"]
        
        req_cumplidos, req_no_cumplidos, req_faltantes, procesados = \
            procesar_coincidencias(coincidencias, requisitos, evidencia_semantica)
        
        agregar_requisitos_no_procesados(
            requisitos, procesados, req_no_cumplidos, req_faltantes
        )
        
        total_requisitos = len(requisitos)
        cantidad_cumplidos = len(req_cumplidos)
        tiene_obligatorio_no_cumplido = any(
            req.tipo == TipoRequisito.OBLIGATORIO
            for req in req_no_cumplidos
        )
        
        puntuacion = calcular_puntuacion(total_requisitos, cantidad_cumplidos, tiene_obligatorio_no_cumplido)
        
        self._registro.matching_completo(
            cumplidos=cantidad_cumplidos,
            no_cumplidos=len(req_no_cumplidos),
            puntuacion=puntuacion
        )
        
        return ResultadoFase1(
            puntuacion=puntuacion,
            descartado=tiene_obligatorio_no_cumplido,
            requisitos_cumplidos=req_cumplidos,
            requisitos_no_cumplidos=req_no_cumplidos,
            requisitos_faltantes=req_faltantes,
            resumen_analisis=resumen_analisis
        )


Phase1Analyzer = AnalizadorFase1
