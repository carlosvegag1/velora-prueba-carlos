"""
Fase 1: Análisis de Oferta y CV
Analiza la oferta de trabajo, extrae requisitos y los compara con el CV.
Utiliza Structured Output de LangChain para garantizar respuestas válidas.
Incorpora Semantic Similarity para mejorar la precisión del matching.
Soporta orquestación con LangGraph para flujos multi-agente.
"""

import re
import time
from typing import List, Optional, Dict, AsyncGenerator
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate

from ..models import (
    Requirement, RequirementType, ConfidenceLevel, Phase1Result,
    RequirementsExtractionResponse, CVMatchingResponse
)
from ..llm.prompts import EXTRACT_REQUIREMENTS_PROMPT, MATCH_CV_REQUIREMENTS_PROMPT
from ..llm.factory import LLMFactory
from ..llm.embeddings_factory import EmbeddingFactory
from ..processing import calculate_score
from .embeddings import SemanticMatcher
from .logging_config import get_operational_logger


class Phase1Analyzer:
    """Analizador para la Fase 1: Extracción de requisitos y matching con CV"""
    
    def __init__(
        self,
        llm: Optional[BaseChatModel] = None,
        provider: str = "openai",
        model_name: str = "gpt-4",
        temperature: float = 0.1,
        api_key: Optional[str] = None,
        use_semantic_matching: bool = True,
        use_langgraph: bool = False
    ):
        """
        Inicializa el analizador de Fase 1.
        
        Args:
            llm: Instancia de LLM de LangChain (opcional)
            provider: Proveedor del LLM ('openai', 'google', 'anthropic')
            model_name: Nombre del modelo a usar
            temperature: Temperatura para el modelo
            api_key: API key del proveedor (opcional)
            use_semantic_matching: Si usar embeddings para pre-filtrar evidencia
            use_langgraph: Si usar LangGraph para orquestación multi-agente
        """
        self.provider = provider
        self.api_key = api_key
        self.use_semantic_matching = use_semantic_matching
        self.use_langgraph = use_langgraph
        self._op_logger = get_operational_logger()
        
        # Verificar si el proveedor soporta embeddings
        self._embeddings_available = EmbeddingFactory.supports_embeddings(provider)
        self._embedding_warning = EmbeddingFactory.get_embedding_provider_message(provider)
        
        if llm is None:
            self.llm = LLMFactory.create_llm(
                provider=provider,
                model_name=model_name,
                temperature=temperature,
                api_key=api_key
            )
        else:
            self.llm = llm
        
        # Log de configuración del proveedor
        self._op_logger.config_provider(provider, model_name)
        
        # Crear LLMs con structured output para cada tarea
        self.extraction_llm = self.llm.with_structured_output(RequirementsExtractionResponse)
        self.matching_llm = self.llm.with_structured_output(CVMatchingResponse)
        
        # Inicializar semantic matcher solo si:
        # 1. Está habilitado por configuración
        # 2. El proveedor soporta embeddings O hay un proveedor fallback disponible
        self.semantic_matcher: Optional[SemanticMatcher] = None
        
        if use_semantic_matching:
            self._init_semantic_matcher(provider, api_key)
        else:
            self._op_logger.config_semantic(enabled=False)
        
        # Inicializar grafo LangGraph si está habilitado
        self._graph = None
        if use_langgraph:
            self._init_langgraph()
            self._op_logger.config_langgraph(enabled=True)
        else:
            self._op_logger.config_langgraph(enabled=False)
    
    def _init_semantic_matcher(self, provider: str, api_key: Optional[str]):
        """
        Inicializa el matcher semántico con gestión inteligente de proveedores.
        Maneja elegantemente el caso de Anthropic (sin embeddings propios).
        """
        try:
            # Determinar proveedor de embeddings
            if EmbeddingFactory.supports_embeddings(provider):
                # El proveedor LLM soporta embeddings, usarlo directamente
                embedding_provider = provider
                embedding_api_key = api_key
            else:
                # El proveedor LLM no soporta embeddings (ej: Anthropic)
                # Buscar proveedor fallback con API key disponible
                fallback = EmbeddingFactory.get_fallback_provider(exclude_provider=provider)
                
                if fallback:
                    embedding_provider = fallback
                    # Para fallback, usar API key del entorno (no la de Anthropic)
                    embedding_api_key = None  # Se tomará del entorno
                    self._op_logger.info(
                        f"Embeddings: usando {fallback} como fallback (proveedor {provider} no soporta embeddings)"
                    )
                else:
                    # No hay proveedor de embeddings disponible
                    self.semantic_matcher = None
                    self._op_logger.config_semantic(
                        enabled=True, 
                        initialized=False,
                        reason="No hay proveedor de embeddings disponible"
                    )
                    return
            
            # Crear el matcher semántico
            self.semantic_matcher = SemanticMatcher(
                embedding_provider=embedding_provider,
                api_key=embedding_api_key
            )
            self._op_logger.config_semantic(enabled=True, initialized=True)
            
        except Exception as e:
            # Si falla, continuar sin semantic matching
            self.semantic_matcher = None
            self._op_logger.config_semantic(enabled=True, initialized=False, reason=str(e))
    
    def _init_langgraph(self):
        """Inicializa el grafo LangGraph para orquestación multi-agente."""
        try:
            from .graph import create_phase1_graph
            self._graph = create_phase1_graph(self.llm, self.semantic_matcher)
        except ImportError:
            self._graph = None
            self.use_langgraph = False
    
    def get_embedding_status(self) -> dict:
        """
        Retorna el estado de los embeddings para esta instancia.
        Útil para mostrar advertencias en la UI.
        
        Returns:
            Diccionario con estado de embeddings
        """
        return {
            "available": self._embeddings_available,
            "enabled": self.use_semantic_matching,
            "initialized": self.semantic_matcher is not None,
            "provider": self.semantic_matcher.provider if self.semantic_matcher else None,
            "warning": self._embedding_warning
        }
    
    def extract_requirements(self, job_offer: str) -> List[dict]:
        """
        Extrae los requisitos de una oferta de trabajo usando Structured Output.
        
        Args:
            job_offer: Texto de la oferta de trabajo
            
        Returns:
            Lista de diccionarios con 'description' y 'type'
        """
        # Crear prompt para extracción
        prompt = ChatPromptTemplate.from_messages([
            ("system", EXTRACT_REQUIREMENTS_PROMPT),
            ("human", "{job_offer}")
        ])
        
        # Crear chain con structured output
        chain = prompt | self.extraction_llm
        
        # Ejecutar - el resultado es siempre un objeto Pydantic válido
        result: RequirementsExtractionResponse = chain.invoke({"job_offer": job_offer})
        
        # Convertir a lista de diccionarios y deduplicar
        requirements = []
        seen_descriptions = set()
        
        for req in result.requirements:
            # Normalizar descripción para comparación
            normalized = req.description.lower().strip()
            
            if normalized not in seen_descriptions:
                seen_descriptions.add(normalized)
                requirements.append({
                    "description": req.description.strip(),
                    "type": req.type
                })
        
        return requirements
    
    def _get_semantic_evidence(self, cv: str, requirements: List[dict]) -> Dict[str, dict]:
        """
        Obtiene evidencia semántica del CV para cada requisito.
        
        Args:
            cv: Texto del CV
            requirements: Lista de requisitos
            
        Returns:
            Diccionario con evidencia semántica por requisito
        """
        if not self.semantic_matcher:
            return {}
        
        try:
            # Indexar el CV
            self.semantic_matcher.index_cv(cv)
            
            # Buscar evidencia para cada requisito
            evidence_map = {}
            for req in requirements:
                desc = req["description"]
                evidence = self.semantic_matcher.find_evidence(desc, k=2)
                
                if evidence:
                    # Tomar la mejor evidencia
                    best_text, best_score = evidence[0]
                    evidence_map[desc.lower()] = {
                        "text": best_text,
                        "semantic_score": best_score,
                        "all_evidence": evidence
                    }
            
            return evidence_map
        except Exception:
            return {}
        finally:
            if self.semantic_matcher:
                self.semantic_matcher.clear()
    
    def match_cv_with_requirements(
        self,
        cv: str,
        requirements: List[dict],
        semantic_evidence: Optional[Dict[str, dict]] = None
    ) -> dict:
        """
        Evalúa qué requisitos se cumplen según el CV usando Structured Output.
        
        Args:
            cv: Texto del CV del candidato
            requirements: Lista de requisitos a evaluar
            semantic_evidence: Evidencia semántica pre-calculada (opcional)
            
        Returns:
            Diccionario con 'matches' y 'analysis_summary'
        """
        if not requirements:
            return {
                "matches": [],
                "analysis_summary": "No hay requisitos para evaluar."
            }
        
        # Formatear requisitos para el prompt, incluyendo evidencia semántica si existe
        requirements_lines = []
        for req in requirements:
            line = f"- [{req['type'].upper()}] {req['description']}"
            
            # Añadir pista de evidencia semántica si existe
            if semantic_evidence:
                sem_ev = semantic_evidence.get(req['description'].lower())
                if sem_ev and sem_ev.get('semantic_score', 0) > 0.4:
                    line += f"\n  [PISTA SEMÁNTICA - Score: {sem_ev['semantic_score']:.2f}]: \"{sem_ev['text'][:150]}...\""
            
            requirements_lines.append(line)
        
        requirements_text = "\n".join(requirements_lines)
        
        # Crear prompt para matching
        prompt = ChatPromptTemplate.from_messages([
            ("system", MATCH_CV_REQUIREMENTS_PROMPT),
            ("human", "CV del candidato:\n{cv}\n\nRequisitos a evaluar:\n{requirements_list}")
        ])
        
        # Crear chain con structured output
        chain = prompt | self.matching_llm
        
        # Ejecutar
        result: CVMatchingResponse = chain.invoke({
            "cv": cv,
            "requirements_list": requirements_text
        })
        
        # Convertir a diccionario incluyendo confianza, razonamiento y score semántico
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
                # Limpiar prefijos
                desc_clean = re.sub(r'^\s*\[(OBLIGATORY|OPTIONAL)\]\s*', '', desc_lower, flags=re.IGNORECASE)
                sem_ev = semantic_evidence.get(desc_clean)
                if sem_ev:
                    match_dict["semantic_score"] = sem_ev.get("semantic_score")
            
            matches.append(match_dict)
        
        return {
            "matches": matches,
            "analysis_summary": result.analysis_summary
        }
    
    def analyze(self, job_offer: str, cv: str) -> Phase1Result:
        """
        Ejecuta el análisis completo de la Fase 1.
        
        Args:
            job_offer: Texto de la oferta de trabajo
            cv: Texto del CV del candidato
            
        Returns:
            Phase1Result con el resultado completo del análisis
        """
        start_time = time.time()
        
        # Usar LangGraph si está habilitado
        if self.use_langgraph and self._graph:
            self._op_logger.phase1_start(mode="langgraph")
            result = self._analyze_with_langgraph(job_offer, cv)
        else:
            self._op_logger.phase1_start(mode="traditional")
            result = self._analyze_traditional(job_offer, cv)
        
        # Log de finalización
        duration_ms = int((time.time() - start_time) * 1000)
        self._op_logger.phase1_complete(
            discarded=result.discarded,
            score=result.score,
            duration_ms=duration_ms
        )
        
        return result
    
    def _analyze_with_langgraph(self, job_offer: str, cv: str) -> Phase1Result:
        """Ejecuta el análisis usando LangGraph."""
        from .graph import run_phase1_graph
        return run_phase1_graph(self._graph, job_offer, cv)
    
    async def analyze_streaming(self, job_offer: str, cv: str) -> AsyncGenerator[dict, None]:
        """
        Ejecuta el análisis con streaming de progreso.
        Solo disponible con LangGraph habilitado.
        
        Args:
            job_offer: Texto de la oferta de trabajo
            cv: Texto del CV del candidato
            
        Yields:
            Diccionarios con actualizaciones de progreso
        """
        if not self.use_langgraph or not self._graph:
            # Si no hay LangGraph, simular streaming con pasos
            yield {"node": "start", "messages": ["[START] Iniciando analisis..."]}
            result = self._analyze_traditional(job_offer, cv)
            yield {"node": "complete", "messages": ["[OK] Analisis completado"], "result": result}
            return
        
        from .graph import run_phase1_graph_streaming
        
        final_result = None
        async for update in run_phase1_graph_streaming(self._graph, job_offer, cv):
            yield update
            if update.get("node") == "calculate_score":
                final_result = update.get("state")
        
        if final_result:
            yield {"node": "complete", "result": final_result}
    
    def _analyze_traditional(self, job_offer: str, cv: str) -> Phase1Result:
        """Ejecuta el análisis con el flujo tradicional (sin LangGraph)."""
        # Paso 1: Extraer requisitos de la oferta
        requirements = self.extract_requirements(job_offer)
        
        if not requirements:
            raise ValueError(
                "No se encontraron requisitos en la oferta de trabajo. "
                "La oferta debe contener secciones explícitas de requisitos."
            )
        
        # Log de requisitos extraídos
        obligatory = sum(1 for r in requirements if r["type"] == "obligatory")
        optional = len(requirements) - obligatory
        self._op_logger.extraction_complete(len(requirements), obligatory, optional)
        
        # Paso 2: Obtener evidencia semántica (si está habilitado y disponible)
        semantic_evidence = {}
        if self.use_semantic_matching and self.semantic_matcher:
            semantic_evidence = self._get_semantic_evidence(cv, requirements)
            # Log de evidencia semántica
            self._op_logger.semantic_evidence_found(len(semantic_evidence), len(requirements))
        
        # Paso 3: Hacer matching con el CV
        match_result = self.match_cv_with_requirements(cv, requirements, semantic_evidence)
        matches = match_result["matches"]
        analysis_summary = match_result["analysis_summary"]
        
        # Crear mapa de requisitos para referencia
        requirements_map = {req["description"].lower(): req for req in requirements}
        
        # Procesar resultados
        fulfilled_requirements = []
        unfulfilled_requirements = []
        missing_requirements = []
        processed = set()
        
        for match in matches:
            # Limpiar prefijos [OBLIGATORY] o [OPTIONAL] que el LLM puede incluir
            desc_raw = match["requirement_description"]
            desc_clean = re.sub(r'^\s*\[(OBLIGATORY|OPTIONAL)\]\s*', '', desc_raw, flags=re.IGNORECASE)
            desc_lower = desc_clean.lower().strip()
            
            # Evitar duplicados
            if desc_lower in processed:
                continue
            processed.add(desc_lower)
            
            # Buscar el requisito original
            original = requirements_map.get(desc_lower)
            if not original:
                # Buscar por similitud básica
                for key, req in requirements_map.items():
                    if desc_lower in key or key in desc_lower:
                        original = req
                        break
            
            if not original:
                continue
            
            # Mapear nivel de confianza del string al enum
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
        total_requirements = len(requirements)
        fulfilled_count = len(fulfilled_requirements)
        has_unfulfilled_obligatory = any(
            req.type == RequirementType.OBLIGATORY
            for req in unfulfilled_requirements
        )
        
        score = calculate_score(total_requirements, fulfilled_count, has_unfulfilled_obligatory)
        
        # Log de matching completado
        self._op_logger.matching_complete(
            fulfilled=fulfilled_count,
            unfulfilled=len(unfulfilled_requirements),
            score=score
        )
        
        return Phase1Result(
            score=score,
            discarded=has_unfulfilled_obligatory,
            fulfilled_requirements=fulfilled_requirements,
            unfulfilled_requirements=unfulfilled_requirements,
            missing_requirements=missing_requirements,
            analysis_summary=analysis_summary
        )
