"""
LangGraph para orquestación multi-agente de la Fase 1.
Define el grafo de estados y los nodos especializados para extracción,
embedding, matching semántico y cálculo de puntuación.
"""

from typing import TypedDict, List, Optional, Dict, Annotated
from operator import add
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate

from langgraph.graph import StateGraph, END

from ..models import (
    Requirement, RequirementType, ConfidenceLevel, Phase1Result,
    RequirementsExtractionResponse, CVMatchingResponse
)
from ..llm.prompts import EXTRACT_REQUIREMENTS_PROMPT, MATCH_CV_REQUIREMENTS_PROMPT
from .embeddings import SemanticMatcher
from .logging_config import get_operational_logger


# ============================================================================
# DEFINICIÓN DEL ESTADO
# ============================================================================

class Phase1State(TypedDict):
    """Estado compartido entre todos los nodos del grafo."""
    # Entradas
    job_offer: str
    cv: str
    
    # Resultados intermedios
    requirements: List[dict]
    semantic_evidence: Dict[str, dict]
    matches: List[dict]
    
    # Resultados finales
    fulfilled_requirements: List[Requirement]
    unfulfilled_requirements: List[Requirement]
    missing_requirements: List[str]
    score: float
    discarded: bool
    analysis_summary: str
    
    # Control de flujo
    error: Optional[str]
    messages: Annotated[List[str], add]  # Log de mensajes para streaming


# ============================================================================
# NODOS DEL GRAFO (AGENTES ESPECIALIZADOS)
# ============================================================================

def create_extract_node(llm: BaseChatModel):
    """Crea el nodo de extracción de requisitos."""
    
    extraction_llm = llm.with_structured_output(RequirementsExtractionResponse)
    
    def extract_requirements(state: Phase1State) -> dict:
        """Agente Extractor: Extrae requisitos de la oferta."""
        op_logger = get_operational_logger()
        op_logger.langgraph_node("extract_requirements", "ejecutando")
        
        job_offer = state["job_offer"]
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", EXTRACT_REQUIREMENTS_PROMPT),
            ("human", "{job_offer}")
        ])
        
        chain = prompt | extraction_llm
        
        try:
            result: RequirementsExtractionResponse = chain.invoke({"job_offer": job_offer})
            
            # Deduplicar
            requirements = []
            seen = set()
            
            for req in result.requirements:
                normalized = req.description.lower().strip()
                if normalized not in seen:
                    seen.add(normalized)
                    requirements.append({
                        "description": req.description.strip(),
                        "type": req.type
                    })
            
            if not requirements:
                return {
                    "error": "No se encontraron requisitos en la oferta",
                    "requirements": [],
                    "messages": ["[WARN] No se encontraron requisitos"]
                }
            
            return {
                "requirements": requirements,
                "messages": [f"[OK] Extraidos {len(requirements)} requisitos"]
            }
        except Exception as e:
            return {
                "error": f"Error en extracción: {str(e)}",
                "requirements": [],
                "messages": [f"[ERROR] {str(e)}"]
            }
    
    return extract_requirements


def create_embed_node(semantic_matcher: Optional[SemanticMatcher]):
    """Crea el nodo de embeddings semánticos."""
    
    def embed_cv(state: Phase1State) -> dict:
        """Agente Embedder: Genera embeddings del CV y busca evidencia."""
        op_logger = get_operational_logger()
        op_logger.langgraph_node("embed_cv", "ejecutando")
        
        if state.get("error"):
            return {"semantic_evidence": {}, "messages": ["⏭️ Skipping embeddings (error previo)"]}
        
        cv = state["cv"]
        requirements = state["requirements"]
        
        if not semantic_matcher or not requirements:
            return {
                "semantic_evidence": {},
                "messages": ["⏭️ Embeddings deshabilitados o sin requisitos"]
            }
        
        try:
            semantic_matcher.index_cv(cv)
            
            evidence_map = {}
            for req in requirements:
                desc = req["description"]
                evidence = semantic_matcher.find_evidence(desc, k=2)
                
                if evidence:
                    best_text, best_score = evidence[0]
                    evidence_map[desc.lower()] = {
                        "text": best_text,
                        "semantic_score": best_score,
                        "all_evidence": evidence
                    }
            
            semantic_matcher.clear()
            
            return {
                "semantic_evidence": evidence_map,
                "messages": [f"[OK] Encontrada evidencia semantica para {len(evidence_map)} requisitos"]
            }
        except Exception as e:
            return {
                "semantic_evidence": {},
                "messages": [f"[WARN] Embeddings fallaron: {str(e)}"]
            }
    
    return embed_cv


def create_match_node(llm: BaseChatModel):
    """Crea el nodo de matching CV-requisitos."""
    
    matching_llm = llm.with_structured_output(CVMatchingResponse)
    
    def match_cv(state: Phase1State) -> dict:
        """Agente Matcher: Evalúa requisitos vs CV."""
        op_logger = get_operational_logger()
        op_logger.langgraph_node("semantic_match", "ejecutando")
        
        if state.get("error"):
            return {"matches": [], "messages": ["⏭️ Skipping matching (error previo)"]}
        
        cv = state["cv"]
        requirements = state["requirements"]
        semantic_evidence = state.get("semantic_evidence", {})
        
        if not requirements:
            return {
                "matches": [],
                "analysis_summary": "No hay requisitos para evaluar",
                "messages": ["[WARN] Sin requisitos para evaluar"]
            }
        
        # Formatear requisitos con pistas semánticas
        requirements_lines = []
        for req in requirements:
            line = f"- [{req['type'].upper()}] {req['description']}"
            
            sem_ev = semantic_evidence.get(req['description'].lower())
            if sem_ev and sem_ev.get('semantic_score', 0) > 0.4:
                line += f"\n  [PISTA SEMÁNTICA - Score: {sem_ev['semantic_score']:.2f}]: \"{sem_ev['text'][:150]}...\""
            
            requirements_lines.append(line)
        
        requirements_text = "\n".join(requirements_lines)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", MATCH_CV_REQUIREMENTS_PROMPT),
            ("human", "CV del candidato:\n{cv}\n\nRequisitos a evaluar:\n{requirements_list}")
        ])
        
        chain = prompt | matching_llm
        
        try:
            result: CVMatchingResponse = chain.invoke({
                "cv": cv,
                "requirements_list": requirements_text
            })
            
            matches = []
            for match in result.matches:
                match_dict = {
                    "requirement_description": match.requirement_description.strip(),
                    "fulfilled": match.fulfilled,
                    "found_in_cv": match.found_in_cv,
                    "evidence": match.evidence.strip() if match.evidence else None,
                    "confidence": match.confidence,
                    "reasoning": match.reasoning.strip() if match.reasoning else None,
                    "semantic_score": None
                }
                
                # Añadir score semántico si existe
                if semantic_evidence:
                    desc_lower = match.requirement_description.lower().strip()
                    import re
                    desc_clean = re.sub(r'^\s*\[(OBLIGATORY|OPTIONAL)\]\s*', '', desc_lower, flags=re.IGNORECASE)
                    sem_ev = semantic_evidence.get(desc_clean)
                    if sem_ev:
                        match_dict["semantic_score"] = sem_ev.get("semantic_score")
                
                matches.append(match_dict)
            
            fulfilled = sum(1 for m in matches if m["fulfilled"])
            
            return {
                "matches": matches,
                "analysis_summary": result.analysis_summary,
                "messages": [f"[OK] Matching completado: {fulfilled}/{len(matches)} cumplidos"]
            }
        except Exception as e:
            return {
                "matches": [],
                "analysis_summary": f"Error: {str(e)}",
                "error": f"Error en matching: {str(e)}",
                "messages": [f"[ERROR] Error en matching: {str(e)}"]
            }
    
    return match_cv


def create_score_node():
    """Crea el nodo de cálculo de puntuación."""
    
    def calculate_final_score(state: Phase1State) -> dict:
        """Agente Scorer: Calcula puntuación y genera resultado final."""
        op_logger = get_operational_logger()
        op_logger.langgraph_node("calculate_score", "ejecutando")
        
        if state.get("error"):
            return {
                "score": 0.0,
                "discarded": True,
                "fulfilled_requirements": [],
                "unfulfilled_requirements": [],
                "missing_requirements": [],
                "messages": ["[ERROR] Evaluacion fallida por error previo"]
            }
        
        requirements = state["requirements"]
        matches = state["matches"]
        semantic_evidence = state.get("semantic_evidence", {})
        
        # Crear mapa de requisitos
        requirements_map = {req["description"].lower(): req for req in requirements}
        
        fulfilled_requirements = []
        unfulfilled_requirements = []
        missing_requirements = []
        processed = set()
        
        import re
        
        for match in matches:
            desc_raw = match["requirement_description"]
            desc_clean = re.sub(r'^\s*\[(OBLIGATORY|OPTIONAL)\]\s*', '', desc_raw, flags=re.IGNORECASE)
            desc_lower = desc_clean.lower().strip()
            
            if desc_lower in processed:
                continue
            processed.add(desc_lower)
            
            original = requirements_map.get(desc_lower)
            if not original:
                for key, req in requirements_map.items():
                    if desc_lower in key or key in desc_lower:
                        original = req
                        break
            
            if not original:
                continue
            
            confidence_str = match.get("confidence", "medium")
            confidence = ConfidenceLevel(confidence_str) if confidence_str else ConfidenceLevel.MEDIUM
            
            requirement = Requirement(
                description=original["description"],
                type=RequirementType(original["type"]),
                fulfilled=match["fulfilled"],
                found_in_cv=match["found_in_cv"],
                evidence=match.get("evidence"),
                confidence=confidence,
                reasoning=match.get("reasoning"),
                semantic_score=match.get("semantic_score")
            )
            
            if match["fulfilled"]:
                fulfilled_requirements.append(requirement)
            else:
                unfulfilled_requirements.append(requirement)
                # CRÍTICO: Agregar TODOS los requisitos no cumplidos a missing_requirements
                # para que la Fase 2 pregunte sobre el 100% de los requisitos faltantes
                missing_requirements.append(original["description"])
        
        # Verificar requisitos no evaluados
        for req in requirements:
            if req["description"].lower() not in processed:
                requirement = Requirement(
                    description=req["description"],
                    type=RequirementType(req["type"]),
                    fulfilled=False,
                    found_in_cv=False,
                    confidence=ConfidenceLevel.LOW,
                    reasoning="Requisito no evaluado por el modelo"
                )
                unfulfilled_requirements.append(requirement)
                missing_requirements.append(req["description"])
        
        # Calcular puntuación
        total = len(requirements)
        fulfilled = len(fulfilled_requirements)
        has_unfulfilled_obligatory = any(
            req.type == RequirementType.OBLIGATORY
            for req in unfulfilled_requirements
        )
        
        if total == 0:
            score = 100.0
        elif has_unfulfilled_obligatory:
            score = 0.0
        else:
            score = (fulfilled / total) * 100.0
        
        status = "DESCARTADO" if has_unfulfilled_obligatory else f"Score: {score:.1f}%"
        
        return {
            "score": score,
            "discarded": has_unfulfilled_obligatory,
            "fulfilled_requirements": fulfilled_requirements,
            "unfulfilled_requirements": unfulfilled_requirements,
            "missing_requirements": missing_requirements,
            "messages": [f"[END] Resultado: {status}"]
        }
    
    return calculate_final_score


# ============================================================================
# CONSTRUCCIÓN DEL GRAFO
# ============================================================================

def create_phase1_graph(
    llm: BaseChatModel,
    semantic_matcher: Optional[SemanticMatcher] = None
) -> StateGraph:
    """
    Crea el grafo LangGraph para la Fase 1.
    
    Args:
        llm: Modelo de lenguaje a usar
        semantic_matcher: Matcher semántico opcional
        
    Returns:
        Grafo compilado listo para ejecutar
    """
    # Crear nodos
    extract_node = create_extract_node(llm)
    embed_node = create_embed_node(semantic_matcher)
    match_node = create_match_node(llm)
    score_node = create_score_node()
    
    # Definir el grafo
    graph = StateGraph(Phase1State)
    
    # Añadir nodos
    graph.add_node("extract_requirements", extract_node)
    graph.add_node("embed_cv", embed_node)
    graph.add_node("semantic_match", match_node)
    graph.add_node("calculate_score", score_node)
    
    # Definir el flujo
    graph.set_entry_point("extract_requirements")
    graph.add_edge("extract_requirements", "embed_cv")
    graph.add_edge("embed_cv", "semantic_match")
    graph.add_edge("semantic_match", "calculate_score")
    graph.add_edge("calculate_score", END)
    
    return graph.compile()


def run_phase1_graph(
    graph,
    job_offer: str,
    cv: str
) -> Phase1Result:
    """
    Ejecuta el grafo de Fase 1 y retorna el resultado.
    
    Args:
        graph: Grafo compilado
        job_offer: Texto de la oferta de trabajo
        cv: Texto del CV
        
    Returns:
        Phase1Result con el resultado del análisis
    """
    # Estado inicial
    initial_state: Phase1State = {
        "job_offer": job_offer,
        "cv": cv,
        "requirements": [],
        "semantic_evidence": {},
        "matches": [],
        "fulfilled_requirements": [],
        "unfulfilled_requirements": [],
        "missing_requirements": [],
        "score": 0.0,
        "discarded": False,
        "analysis_summary": "",
        "error": None,
        "messages": []
    }
    
    # Ejecutar el grafo
    final_state = graph.invoke(initial_state)
    
    # Verificar errores
    if final_state.get("error"):
        raise ValueError(final_state["error"])
    
    # Construir resultado
    return Phase1Result(
        score=final_state["score"],
        discarded=final_state["discarded"],
        fulfilled_requirements=final_state["fulfilled_requirements"],
        unfulfilled_requirements=final_state["unfulfilled_requirements"],
        missing_requirements=final_state["missing_requirements"],
        analysis_summary=final_state.get("analysis_summary", "")
    )


async def run_phase1_graph_streaming(
    graph,
    job_offer: str,
    cv: str
):
    """
    Ejecuta el grafo con streaming de estados intermedios.
    
    Args:
        graph: Grafo compilado
        job_offer: Texto de la oferta de trabajo
        cv: Texto del CV
        
    Yields:
        Diccionarios con actualizaciones de estado
    """
    initial_state: Phase1State = {
        "job_offer": job_offer,
        "cv": cv,
        "requirements": [],
        "semantic_evidence": {},
        "matches": [],
        "fulfilled_requirements": [],
        "unfulfilled_requirements": [],
        "missing_requirements": [],
        "score": 0.0,
        "discarded": False,
        "analysis_summary": "",
        "error": None,
        "messages": []
    }
    
    # Stream de estados
    async for state in graph.astream(initial_state):
        # Extraer el nombre del nodo y su output
        for node_name, node_output in state.items():
            yield {
                "node": node_name,
                "messages": node_output.get("messages", []),
                "state": node_output
            }

