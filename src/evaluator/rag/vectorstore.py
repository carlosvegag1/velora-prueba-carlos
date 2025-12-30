"""
VectorStore para búsqueda semántica en el historial de evaluaciones.
Utiliza FAISS para indexación eficiente.

Arquitectura desacoplada: El proveedor de embeddings es configurable
e independiente del LLM usado para análisis.
"""

import logging
import unicodedata
from typing import List, Dict, Any, Optional
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from ..core.logging_config import get_operational_logger
from ..llm.embeddings_factory import EmbeddingFactory

logger = logging.getLogger(__name__)


def normalize_text_for_embedding(text: str) -> str:
    """
    Normaliza texto para evitar errores de codificación en embeddings.
    Convierte caracteres Unicode problemáticos a ASCII compatible.
    
    Args:
        text: Texto a normalizar
        
    Returns:
        Texto normalizado compatible con APIs de embeddings
    """
    if not text:
        return ""
    
    # Normalizar a forma NFC (composición canónica)
    text = unicodedata.normalize('NFC', text)
    
    # Asegurar que es string válido UTF-8
    try:
        text = text.encode('utf-8').decode('utf-8')
    except (UnicodeEncodeError, UnicodeDecodeError):
        # Fallback: eliminar caracteres problemáticos
        text = text.encode('ascii', 'ignore').decode('ascii')
    
    return text


class HistoryVectorStore:
    """
    Gestiona el almacenamiento vectorial del historial de evaluaciones.
    Permite búsquedas semánticas sobre evaluaciones pasadas.
    
    Soporta múltiples proveedores de embeddings (OpenAI, Google, etc.)
    """
    
    def __init__(
        self,
        user_id: str,
        storage_path: str = "data/vectors",
        embedding_provider: str = "openai",
        api_key: Optional[str] = None
    ):
        """
        Inicializa el vectorstore para un usuario.
        
        Args:
            user_id: ID del usuario
            storage_path: Ruta base para almacenar vectores
            embedding_provider: Proveedor de embeddings ('openai', 'google')
            api_key: API key del proveedor (opcional, puede estar en env)
        """
        self.user_id = user_id
        self.storage_path = Path(storage_path)
        self.store_path = self.storage_path / user_id
        self.embedding_provider = embedding_provider
        
        # Crear directorio si no existe
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Inicializar embeddings usando la factory (mapeo 1:1 proveedor-modelo)
        self.embeddings = EmbeddingFactory.create_embeddings(
            provider=embedding_provider,
            api_key=api_key
        )
        
        # Cargar vectorstore existente si existe y es compatible
        self.vectorstore: Optional[FAISS] = None
        self._load_existing_if_compatible()
        
        # Últimos documentos recuperados (para mostrar en UI)
        self.last_retrieved_docs: List[Document] = []
    
    def _load_existing_if_compatible(self):
        """
        Carga un vectorstore existente solo si fue creado con el mismo proveedor.
        Evita errores de dimensiones incompatibles entre proveedores de embeddings.
        """
        index_path = self.store_path / "index.faiss"
        provider_file = self.store_path / "embedding_provider.txt"
        
        if not index_path.exists():
            return
        
        # Verificar si el proveedor coincide
        if provider_file.exists():
            try:
                saved_provider = provider_file.read_text(encoding='utf-8').strip()
                if saved_provider != self.embedding_provider:
                    logger.warning(
                        f"Índice incompatible: creado con '{saved_provider}', "
                        f"actual '{self.embedding_provider}'. Re-indexación necesaria."
                    )
                    # No cargar - se re-indexará automáticamente
                    return
            except Exception:
                pass  # Si no puede leer, intentar cargar de todos modos
        
        try:
            self.vectorstore = FAISS.load_local(
                str(self.store_path),
                self.embeddings,
                allow_dangerous_deserialization=True
            )
            logger.info(f"VectorStore cargado para usuario {self.user_id}")
        except Exception as e:
            logger.warning(f"Error al cargar vectorstore (posible incompatibilidad): {e}")
            self.vectorstore = None
    
    def index_evaluations(
        self,
        evaluations: List[tuple]
    ) -> bool:
        """
        Indexa evaluaciones para búsqueda semántica.
        
        Args:
            evaluations: Lista de tuplas (searchable_text, metadata_dict)
            
        Returns:
            True si se indexó correctamente
        """
        if not evaluations:
            logger.warning("No hay evaluaciones para indexar")
            return False
        
        try:
            # Normalizar textos para evitar errores de codificación
            texts = [normalize_text_for_embedding(text) for text, _ in evaluations]
            metadatas = [meta for _, meta in evaluations]
            
            # Crear nuevo vectorstore
            self.vectorstore = FAISS.from_texts(
                texts,
                self.embeddings,
                metadatas=metadatas
            )
            
            # Guardar a disco
            self.vectorstore.save_local(str(self.store_path))
            
            # Guardar proveedor usado para verificar compatibilidad futura
            provider_file = self.store_path / "embedding_provider.txt"
            provider_file.write_text(self.embedding_provider, encoding='utf-8')
            
            logger.info(f"Indexadas {len(evaluations)} evaluaciones para {self.user_id}")
            
            # Log operacional
            op_logger = get_operational_logger()
            op_logger.rag_indexed(len(evaluations))
            
            return True
            
        except Exception as e:
            logger.error(f"Error al indexar evaluaciones: {e}")
            return False
    
    def add_evaluation(
        self,
        searchable_text: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Añade una nueva evaluación al índice existente.
        
        Args:
            searchable_text: Texto para embedding
            metadata: Metadatos de la evaluación
            
        Returns:
            True si se añadió correctamente
        """
        try:
            # Normalizar texto para evitar errores de codificación
            normalized_text = normalize_text_for_embedding(searchable_text)
            
            if self.vectorstore is None:
                # Crear nuevo vectorstore
                self.vectorstore = FAISS.from_texts(
                    [normalized_text],
                    self.embeddings,
                    metadatas=[metadata]
                )
            else:
                # Añadir al existente
                self.vectorstore.add_texts(
                    [normalized_text],
                    metadatas=[metadata]
                )
            
            # Guardar a disco
            self.vectorstore.save_local(str(self.store_path))
            
            # Guardar proveedor usado
            provider_file = self.store_path / "embedding_provider.txt"
            provider_file.write_text(self.embedding_provider, encoding='utf-8')
            
            logger.info(f"Evaluación añadida al índice de {self.user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error al añadir evaluación: {e}")
            return False
    
    def search(
        self,
        query: str,
        k: int = 5
    ) -> List[Document]:
        """
        Realiza búsqueda semántica en el historial.
        
        Args:
            query: Consulta del usuario
            k: Número de resultados a retornar
            
        Returns:
            Lista de documentos relevantes
        """
        if self.vectorstore is None:
            logger.warning("VectorStore no inicializado")
            return []
        
        try:
            # Normalizar query para evitar errores de codificación
            normalized_query = normalize_text_for_embedding(query)
            
            docs = self.vectorstore.similarity_search(normalized_query, k=k)
            self.last_retrieved_docs = docs
            
            # Log operacional
            op_logger = get_operational_logger()
            op_logger.rag_query(len(docs))
            
            return docs
            
        except Exception as e:
            logger.error(f"Error en búsqueda: {e}")
            return []
    
    def search_with_scores(
        self,
        query: str,
        k: int = 5
    ) -> List[tuple]:
        """
        Realiza búsqueda semántica con scores de similitud.
        
        Args:
            query: Consulta del usuario
            k: Número de resultados a retornar
            
        Returns:
            Lista de tuplas (Document, score)
        """
        if self.vectorstore is None:
            return []
        
        try:
            # Normalizar query para evitar errores de codificación
            normalized_query = normalize_text_for_embedding(query)
            results = self.vectorstore.similarity_search_with_score(normalized_query, k=k)
            self.last_retrieved_docs = [doc for doc, _ in results]
            return results
            
        except Exception as e:
            logger.error(f"Error en búsqueda con scores: {e}")
            return []
    
    def rebuild_index(
        self,
        evaluations: List[tuple]
    ) -> bool:
        """
        Reconstruye el índice desde cero.
        Útil cuando se han modificado evaluaciones.
        
        Args:
            evaluations: Lista de tuplas (searchable_text, metadata_dict)
            
        Returns:
            True si se reconstruyó correctamente
        """
        # Eliminar índice existente
        if self.store_path.exists():
            import shutil
            shutil.rmtree(str(self.store_path))
        
        self.store_path.mkdir(parents=True, exist_ok=True)
        
        # Crear nuevo índice
        return self.index_evaluations(evaluations)
    
    @property
    def is_initialized(self) -> bool:
        """Verifica si el vectorstore está inicializado."""
        return self.vectorstore is not None
    
    @property
    def document_count(self) -> int:
        """Retorna el número de documentos indexados."""
        if self.vectorstore is None:
            return 0
        try:
            return self.vectorstore.index.ntotal
        except Exception:
            return 0

