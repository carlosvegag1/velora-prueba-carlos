"""
Comparador Semantico: Embeddings para enriquecer contexto en evaluacion de CV.
Busqueda vectorial con FAISS. Prioriza comprension global sobre coincidencias literales.
"""

import re
from typing import List, Dict, Optional, Tuple
from langchain_community.vectorstores import FAISS
from langchain_core.embeddings import Embeddings

from .embedding_proveedor import FabricaEmbeddings


class ComparadorSemantico:
    """
    Comparador semantico que usa embeddings para enriquecer el contexto de evaluacion.
    Los resultados son sugerencias para el LLM, NO restricciones.
    El LLM siempre evalua el CV completo con comprension global.
    """
    
    def __init__(self, proveedor_embeddings: Optional[str] = None, api_key: Optional[str] = None):
        if proveedor_embeddings and not FabricaEmbeddings.soporta_embeddings(proveedor_embeddings):
            raise ValueError(f"'{proveedor_embeddings}' no soporta embeddings")
        
        if not proveedor_embeddings:
            raise ValueError("Se requiere especificar un proveedor de embeddings")
        
        self.proveedor = proveedor_embeddings
        self.modelo = FabricaEmbeddings.obtener_modelo_embedding(proveedor_embeddings)
        self.embeddings = FabricaEmbeddings.crear_embeddings(proveedor=proveedor_embeddings, api_key=api_key)
        self._vectorstore: Optional[FAISS] = None
        self._chunks: List[str] = []
    
    @property
    def provider(self):
        return self.proveedor
    
    @property
    def model(self):
        return self.modelo
    
    def _dividir_cv_en_chunks(self, texto_cv: str, tamano_chunk: int = 800, solapamiento: int = 150) -> List[str]:
        """
        Divide el CV en chunks semanticos amplios para capturar contexto completo.
        Prioriza secciones naturales del CV sobre division arbitraria.
        """
        patrones_seccion = [
            r'\n(?=(?:EXPERIENCIA|FORMACION|EDUCACION|HABILIDADES|SKILLS|IDIOMAS|PROYECTOS|CERTIFICACIONES|PERFIL|RESUMEN))',
            r'\n(?=[A-ZÁÉÍÓÚÑ]{4,}\s*(?:\n|:))',
            r'\n{2,}',
        ]
        
        chunks = []
        texto_actual = texto_cv
        
        for patron in patrones_seccion:
            if len(texto_actual) > tamano_chunk:
                partes = re.split(patron, texto_actual, flags=re.IGNORECASE)
                if len(partes) > 1:
                    chunks.extend([p.strip() for p in partes if p.strip()])
                    break
        
        if not chunks:
            chunks = self._dividir_por_tamano(texto_cv, tamano_chunk, solapamiento)
        else:
            chunks_finales = []
            for chunk in chunks:
                if len(chunk) > tamano_chunk * 2:
                    chunks_finales.extend(self._dividir_por_tamano(chunk, tamano_chunk, solapamiento))
                else:
                    chunks_finales.append(chunk)
            chunks = chunks_finales
        
        return [c for c in chunks if len(c) > 30]
    
    def _dividir_por_tamano(self, texto: str, tamano_chunk: int, solapamiento: int) -> List[str]:
        chunks = []
        inicio = 0
        
        while inicio < len(texto):
            fin = inicio + tamano_chunk
            if fin < len(texto):
                ultimo_corte = max(
                    texto.rfind(' ', inicio, fin),
                    texto.rfind('.', inicio, fin),
                    texto.rfind('\n', inicio, fin)
                )
                if ultimo_corte > inicio:
                    fin = ultimo_corte + 1
            
            chunk = texto[inicio:fin].strip()
            if chunk:
                chunks.append(chunk)
            inicio = fin - solapamiento
            if inicio < 0:
                inicio = 0
        
        return chunks
    
    def indexar_cv(self, texto_cv: str) -> int:
        """Indexa el CV creando vectorstore temporal. Retorna numero de chunks."""
        self._chunks = self._dividir_cv_en_chunks(texto_cv)
        if not self._chunks:
            self._chunks = [texto_cv]
        self._vectorstore = FAISS.from_texts(self._chunks, self.embeddings)
        return len(self._chunks)
    
    index_cv = indexar_cv
    
    def encontrar_evidencia(self, requisito: str, k: int = 3, umbral_score: float = 0.2) -> List[Tuple[str, float]]:
        """
        Encuentra contexto semantico relevante para un requisito.
        Umbral bajo (0.2) para capturar evidencia implicita y contextual.
        Retorna [(texto, score)].
        """
        if not self._vectorstore:
            return []
        
        resultados = self._vectorstore.similarity_search_with_score(requisito, k=k)
        evidencia = []
        for doc, score in resultados:
            similitud = 1 / (1 + score)
            if similitud >= umbral_score:
                evidencia.append((doc.page_content, similitud))
        return evidencia
    
    find_evidence = encontrar_evidencia
    
    def encontrar_toda_la_evidencia(self, requisitos: List[str], k: int = 3) -> Dict[str, List[Tuple[str, float]]]:
        """Encuentra contexto para multiples requisitos."""
        return {req: self.encontrar_evidencia(req, k=k) for req in requisitos}
    
    find_all_evidence = encontrar_toda_la_evidencia
    
    def obtener_mejor_score(self, requisito: str) -> float:
        evidencia = self.encontrar_evidencia(requisito, k=1)
        return evidencia[0][1] if evidencia else 0.0
    
    get_best_match_score = obtener_mejor_score
    
    def limpiar(self):
        """Limpia vectorstore y chunks."""
        self._vectorstore = None
        self._chunks = []
    
    clear = limpiar


SemanticMatcher = ComparadorSemantico
