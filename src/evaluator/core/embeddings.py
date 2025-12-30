"""
Módulo de Embeddings Semánticos para Matching CV-Requisitos.
Utiliza embeddings para pre-filtrar y encontrar evidencia semántica en el CV.

Arquitectura simplificada: Mapeo 1:1 proveedor → modelo de embedding.
"""

import re
from typing import List, Dict, Optional, Tuple
from langchain_community.vectorstores import FAISS
from langchain_core.embeddings import Embeddings

from .logging_config import get_operational_logger
from ..llm.embeddings_factory import EmbeddingFactory


class SemanticMatcher:
    """
    Matcher semántico que usa embeddings para encontrar evidencia en el CV.
    Mejora la precisión del matching al pre-filtrar información relevante.
    
    Usa arquitectura simplificada: 1 proveedor = 1 modelo de embedding fijo.
    """
    
    def __init__(
        self,
        embedding_provider: str = "openai",
        api_key: Optional[str] = None
    ):
        """
        Inicializa el matcher semántico.
        
        Args:
            embedding_provider: Proveedor de embeddings ('openai', 'google')
            api_key: API key del proveedor (opcional, puede estar en env)
            
        Raises:
            ValueError: Si el proveedor no soporta embeddings
        """
        # Validar que el proveedor soporta embeddings
        if not EmbeddingFactory.supports_embeddings(embedding_provider):
            raise ValueError(
                f"El proveedor '{embedding_provider}' no soporta embeddings. "
                f"Usa: {EmbeddingFactory.get_available_providers()}"
            )
        
        self.provider = embedding_provider
        # El modelo se asigna automáticamente (mapeo 1:1)
        self.model = EmbeddingFactory.get_embedding_model(embedding_provider)
        
        # Crear embeddings usando la factory simplificada
        self.embeddings = EmbeddingFactory.create_embeddings(
            provider=embedding_provider,
            api_key=api_key
        )
        
        self._vectorstore: Optional[FAISS] = None
        self._chunks: List[str] = []
    
    def _split_cv_into_chunks(self, cv_text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """
        Divide el CV en chunks semánticos.
        Intenta dividir por secciones primero, luego por tamaño.
        
        Args:
            cv_text: Texto completo del CV
            chunk_size: Tamaño máximo de cada chunk
            overlap: Solapamiento entre chunks
            
        Returns:
            Lista de chunks de texto
        """
        # Patrones comunes de secciones en CVs
        section_patterns = [
            r'\n(?=(?:EXPERIENCIA|FORMACIÓN|EDUCACIÓN|HABILIDADES|SKILLS|IDIOMAS|PROYECTOS|CERTIFICACIONES))',
            r'\n(?=[A-ZÁÉÍÓÚÑ]{3,}\s*(?:\n|:))',  # Títulos en mayúsculas
            r'\n{2,}',  # Doble salto de línea
        ]
        
        # Intentar dividir por secciones
        chunks = []
        current_text = cv_text
        
        for pattern in section_patterns:
            if len(current_text) > chunk_size:
                parts = re.split(pattern, current_text, flags=re.IGNORECASE)
                if len(parts) > 1:
                    chunks.extend([p.strip() for p in parts if p.strip()])
                    break
        
        # Si no se encontraron secciones claras, dividir por tamaño
        if not chunks:
            chunks = self._split_by_size(cv_text, chunk_size, overlap)
        else:
            # Asegurar que los chunks no sean demasiado grandes
            final_chunks = []
            for chunk in chunks:
                if len(chunk) > chunk_size * 2:
                    final_chunks.extend(self._split_by_size(chunk, chunk_size, overlap))
                else:
                    final_chunks.append(chunk)
            chunks = final_chunks
        
        return [c for c in chunks if len(c) > 20]  # Filtrar chunks muy pequeños
    
    def _split_by_size(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        """Divide texto por tamaño con solapamiento."""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Intentar cortar en un espacio o punto
            if end < len(text):
                # Buscar el último espacio o punto antes del límite
                last_break = max(
                    text.rfind(' ', start, end),
                    text.rfind('.', start, end),
                    text.rfind('\n', start, end)
                )
                if last_break > start:
                    end = last_break + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - overlap
            if start < 0:
                start = 0
        
        return chunks
    
    def index_cv(self, cv_text: str) -> int:
        """
        Indexa el CV creando un vectorstore temporal.
        
        Args:
            cv_text: Texto completo del CV
            
        Returns:
            Número de chunks indexados
        """
        self._chunks = self._split_cv_into_chunks(cv_text)
        
        if not self._chunks:
            self._chunks = [cv_text]
        
        self._vectorstore = FAISS.from_texts(self._chunks, self.embeddings)
        
        # Log de indexación
        op_logger = get_operational_logger()
        op_logger.semantic_indexing(len(self._chunks))
        
        return len(self._chunks)
    
    def find_evidence(
        self,
        requirement: str,
        k: int = 3,
        score_threshold: float = 0.3
    ) -> List[Tuple[str, float]]:
        """
        Encuentra evidencia semántica en el CV para un requisito.
        
        Args:
            requirement: Descripción del requisito
            k: Número máximo de resultados
            score_threshold: Umbral mínimo de similitud (0-1, menor es mejor en FAISS)
            
        Returns:
            Lista de tuplas (texto_evidencia, score_similitud)
        """
        if not self._vectorstore:
            return []
        
        # Buscar documentos similares
        results = self._vectorstore.similarity_search_with_score(requirement, k=k)
        
        # Filtrar por umbral y formatear resultados
        evidence = []
        for doc, score in results:
            # FAISS retorna distancia L2, menor es mejor
            # Convertir a similitud (0-1 donde 1 es más similar)
            similarity = 1 / (1 + score)
            
            if similarity >= score_threshold:
                evidence.append((doc.page_content, similarity))
        
        return evidence
    
    def find_all_evidence(
        self,
        requirements: List[str],
        k: int = 2
    ) -> Dict[str, List[Tuple[str, float]]]:
        """
        Encuentra evidencia para múltiples requisitos.
        
        Args:
            requirements: Lista de descripciones de requisitos
            k: Número de resultados por requisito
            
        Returns:
            Diccionario {requisito: [(evidencia, score), ...]}
        """
        evidence_map = {}
        
        for req in requirements:
            evidence_map[req] = self.find_evidence(req, k=k)
        
        return evidence_map
    
    def get_best_match_score(self, requirement: str) -> float:
        """
        Obtiene el mejor score de similitud para un requisito.
        
        Args:
            requirement: Descripción del requisito
            
        Returns:
            Score de similitud (0-1, mayor es mejor)
        """
        evidence = self.find_evidence(requirement, k=1)
        if evidence:
            return evidence[0][1]
        return 0.0
    
    def clear(self):
        """Limpia el vectorstore y los chunks."""
        self._vectorstore = None
        self._chunks = []
