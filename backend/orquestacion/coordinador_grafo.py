"""
Coordinador de Grafo LangGraph: Construcción alternativa para Fase 1.

Ofrece una implementación orientada a objetos del grafo multi-agente.
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
from ..infraestructura.llm import ComparadorSemantico


class EstadoFase1(TypedDict):
    """Estado compartido entre los nodos del grafo de Fase 1."""
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


class ConstructorGrafoFase1:
    """
    Construye el grafo LangGraph para Fase 1 con enfoque OOP.
    
    Flujo: extraer_requisitos → embeber_cv → matching_semantico → calcular_puntuacion
    """
    
    def __init__(
        self,
        llm: BaseChatModel,
        comparador_semantico: Optional[ComparadorSemantico] = None,
        usar_matching_semantico: bool = False
    ):
        """Inicializa el constructor con LLM y comparador semántico opcional."""
        self.llm = llm
        self.comparador_semantico = comparador_semantico
        self.usar_matching_semantico = usar_matching_semantico
        self._registro = obtener_registro_operacional()
    
    def _extraer_requisitos(self, estado: EstadoFase1) -> dict:
        """Nodo: Extrae requisitos de la oferta de trabajo."""
        self._registro.nodo_langgraph("extraer_requisitos", "ejecutando")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", PROMPT_EXTRACCION_REQUISITOS),
            ("human", "Oferta de trabajo:\n\n{oferta_trabajo}")
        ])
        
        llm_estructurado = self.llm.with_structured_output(RespuestaExtraccionRequisitos)
        cadena = prompt | llm_estructurado
        
        resultado = cadena.invoke({"oferta_trabajo": estado["oferta_trabajo"]})
        
        requisitos = [req.model_dump() for req in resultado.requirements]
        
        obligatorios = len([r for r in requisitos if r["type"] == "obligatory"])
        opcionales = len([r for r in requisitos if r["type"] == "optional"])
        self._registro.extraccion_completa(len(requisitos), obligatorios, opcionales)
        
        return {"requisitos": requisitos}
    
    def _embeber_cv(self, estado: EstadoFase1) -> dict:
        """Nodo: Embebe el CV y busca evidencia semántica."""
        self._registro.nodo_langgraph("embeber_cv", "ejecutando")
        
        if not self.comparador_semantico or not self.usar_matching_semantico:
            self._registro.config_semantic(False)
            return {"evidencia_semantica": {}}
        
        try:
            fragmentos = self.comparador_semantico.indexar_cv(estado["cv"])
            if fragmentos:
                self._registro.indexacion_semantica(len(fragmentos))
            
            evidencia = {}
            requisitos_con_evidencia = 0
            
            for req in estado["requisitos"]:
                desc = req["description"]
                resultado = self.comparador_semantico.buscar_evidencia(desc)
                if resultado:
                    evidencia[desc] = resultado
                    requisitos_con_evidencia += 1
            
            self._registro.evidencia_semantica_encontrada(
                requisitos_con_evidencia, len(estado["requisitos"])
            )
            
            return {"evidencia_semantica": evidencia}
            
        except Exception as e:
            self._registro.advertencia("EMBEDDINGS", f"Error: {str(e)}")
            return {"evidencia_semantica": {}}
    
    def _matching_semantico(self, estado: EstadoFase1) -> dict:
        """Nodo: Realiza el matching de requisitos contra el CV."""
        self._registro.nodo_langgraph("matching_semantico", "ejecutando")
        
        requisitos_str = ""
        for i, req in enumerate(estado["requisitos"], 1):
            desc = req["description"]
            tipo = "OBLIGATORIO" if req["type"] == "obligatory" else "DESEABLE"
            
            if desc in estado.get("evidencia_semantica", {}):
                ev = estado["evidencia_semantica"][desc]
                fragmento = ev.get("chunk", "")
                requisitos_str += f"{i}. [{tipo}] {desc}\n   [Contexto CV: {fragmento[:200]}...]\n\n"
            else:
                requisitos_str += f"{i}. [{tipo}] {desc}\n\n"
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", PROMPT_MATCHING_CV),
            ("human", "REQUISITOS A EVALUAR:\n{requisitos}\n\nCV DEL CANDIDATO:\n{cv}")
        ])
        
        llm_estructurado = self.llm.with_structured_output(RespuestaMatchingCV)
        cadena = prompt | llm_estructurado
        
        resultado = cadena.invoke({
            "requisitos": requisitos_str,
            "cv": estado["cv"]
        })
        
        coincidencias = [m.model_dump() for m in resultado.matches]
        
        return {"coincidencias": coincidencias}
    
    def _calcular_puntuacion(self, estado: EstadoFase1) -> dict:
        """Nodo: Calcula la puntuación final y genera resultado."""
        self._registro.nodo_langgraph("calcular_puntuacion", "ejecutando")
        
        cumplidos, no_cumplidos, faltantes = procesar_coincidencias(
            estado["requisitos"],
            estado["coincidencias"]
        )
        
        cumplidos, no_cumplidos, faltantes = agregar_requisitos_no_procesados(
            estado["requisitos"],
            estado["coincidencias"],
            cumplidos,
            no_cumplidos,
            faltantes
        )
        
        total = len(cumplidos) + len(no_cumplidos)
        obligatorio_no_cumplido = any(
            req.tipo == TipoRequisito.OBLIGATORIO and not req.cumplido
            for req in no_cumplidos
        )
        
        puntuacion = calcular_puntuacion(total, len(cumplidos), obligatorio_no_cumplido)
        descartado = obligatorio_no_cumplido
        
        self._registro.matching_completo(len(cumplidos), len(no_cumplidos), puntuacion)
        
        resumen = self._generar_resumen(cumplidos, no_cumplidos, puntuacion, descartado)
        
        return {
            "requisitos_cumplidos": cumplidos,
            "requisitos_no_cumplidos": no_cumplidos,
            "requisitos_faltantes": faltantes,
            "puntuacion": puntuacion,
            "descartado": descartado,
            "resumen_analisis": resumen
        }
    
    def _generar_resumen(
        self,
        cumplidos: List[Requisito],
        no_cumplidos: List[Requisito],
        puntuacion: float,
        descartado: bool
    ) -> str:
        """Genera resumen del análisis."""
        partes = [
            f"Puntuacion: {puntuacion:.1f}%",
            f"Cumplidos: {len(cumplidos)}",
            f"No cumplidos: {len(no_cumplidos)}"
        ]
        
        if descartado:
            partes.append("Estado: DESCARTADO (requisito obligatorio no cumplido)")
        else:
            partes.append("Estado: APTO para entrevista")
        
        return "\n".join(partes)
    
    def construir_grafo(self) -> StateGraph:
        """Construye y retorna el grafo de estados compilado."""
        grafo = StateGraph(EstadoFase1)
        
        grafo.add_node("extraer_requisitos", self._extraer_requisitos)
        grafo.add_node("embeber_cv", self._embeber_cv)
        grafo.add_node("matching_semantico", self._matching_semantico)
        grafo.add_node("calcular_puntuacion", self._calcular_puntuacion)
        
        grafo.set_entry_point("extraer_requisitos")
        grafo.add_edge("extraer_requisitos", "embeber_cv")
        grafo.add_edge("embeber_cv", "matching_semantico")
        grafo.add_edge("matching_semantico", "calcular_puntuacion")
        grafo.add_edge("calcular_puntuacion", END)
        
        return grafo.compile()


def ejecutar_analisis_con_grafo(
    llm: BaseChatModel,
    oferta_trabajo: str,
    cv: str,
    comparador_semantico: Optional[ComparadorSemantico] = None,
    usar_matching_semantico: bool = False
) -> ResultadoFase1:
    """Ejecuta el análisis de Fase 1 usando el grafo LangGraph."""
    registro = obtener_registro_operacional()
    registro.fase1_inicio("langgraph")
    
    constructor = ConstructorGrafoFase1(
        llm=llm,
        comparador_semantico=comparador_semantico,
        usar_matching_semantico=usar_matching_semantico
    )
    grafo = constructor.construir_grafo()
    
    estado_inicial = {
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
        "resumen_analisis": ""
    }
    
    resultado = grafo.invoke(estado_inicial)
    
    resultado_fase1 = ResultadoFase1(
        requisitos_cumplidos=resultado["requisitos_cumplidos"],
        requisitos_no_cumplidos=resultado["requisitos_no_cumplidos"],
        requisitos_faltantes=resultado["requisitos_faltantes"],
        puntuacion=resultado["puntuacion"],
        descartado=resultado["descartado"],
        resumen_analisis=resultado["resumen_analisis"]
    )
    
    registro.fase1_completa(resultado["descartado"], resultado["puntuacion"])
    
    return resultado_fase1


GrafoFase1Builder = ConstructorGrafoFase1
Phase1GraphBuilder = ConstructorGrafoFase1
run_phase1_with_graph = ejecutar_analisis_con_grafo
