"""
Almacén vectorial FAISS para búsqueda semántica en el historial de evaluaciones.

El proveedor de embeddings es configurable e independiente del LLM de análisis.
"""

import logging
import unicodedata
from typing import List, Dict, Any, Optional
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from ...utilidades import obtener_registro_operacional
from ...infraestructura.llm import FabricaEmbeddings

logger = logging.getLogger(__name__)


def normalizar_texto_para_embedding(texto: str) -> str:
    """Normaliza texto para evitar errores de codificación en APIs de embeddings."""
    if not texto:
        return ""
    
    texto = unicodedata.normalize('NFC', texto)
    
    try:
        texto = texto.encode('utf-8').decode('utf-8')
    except (UnicodeEncodeError, UnicodeDecodeError):
        texto = texto.encode('ascii', 'ignore').decode('ascii')
    
    return texto


normalize_text_for_embedding = normalizar_texto_para_embedding


class AlmacenVectorialHistorial:
    """
    Gestiona el almacenamiento vectorial del historial de evaluaciones.
    
    Soporta múltiples proveedores de embeddings (OpenAI, Google, etc.).
    """
    
    def __init__(
        self,
        id_usuario: str,
        ruta_almacenamiento: str = "data/vectores",
        proveedor_embeddings: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        """Inicializa el almacén vectorial para un usuario."""
        self.id_usuario = id_usuario
        self.ruta_almacenamiento = Path(ruta_almacenamiento)
        self.ruta_store = self.ruta_almacenamiento / id_usuario
        self.proveedor_embeddings = proveedor_embeddings
        
        self.ruta_almacenamiento.mkdir(parents=True, exist_ok=True)
        
        self.embeddings = FabricaEmbeddings.crear_embeddings(
            proveedor=proveedor_embeddings,
            api_key=api_key
        )
        
        self.vectorstore: Optional[FAISS] = None
        self._cargar_existente_si_compatible()
        
        self.ultimos_documentos_recuperados: List[Document] = []
    
    @property
    def user_id(self):
        return self.id_usuario
    
    @property
    def storage_path(self):
        return self.ruta_almacenamiento
    
    @property
    def store_path(self):
        return self.ruta_store
    
    @property
    def embedding_provider(self):
        return self.proveedor_embeddings
    
    @property
    def last_retrieved_docs(self):
        return self.ultimos_documentos_recuperados
    
    def _cargar_existente_si_compatible(self):
        """Carga un vectorstore existente solo si fue creado con el mismo proveedor."""
        ruta_indice = self.ruta_store / "index.faiss"
        archivo_proveedor = self.ruta_store / "embedding_provider.txt"
        
        if not ruta_indice.exists():
            return
        
        if archivo_proveedor.exists():
            try:
                proveedor_guardado = archivo_proveedor.read_text(encoding='utf-8').strip()
                if proveedor_guardado != self.proveedor_embeddings:
                    logger.warning(
                        f"Índice incompatible: creado con '{proveedor_guardado}', "
                        f"actual '{self.proveedor_embeddings}'. Re-indexación necesaria."
                    )
                    return
            except Exception:
                pass
        
        try:
            self.vectorstore = FAISS.load_local(
                str(self.ruta_store),
                self.embeddings,
                allow_dangerous_deserialization=True
            )
            logger.info(f"VectorStore cargado para usuario {self.id_usuario}")
        except Exception as e:
            logger.warning(f"Error al cargar vectorstore: {e}")
            self.vectorstore = None
    
    def indexar_evaluaciones(self, evaluaciones: List[tuple]) -> bool:
        """Indexa evaluaciones para búsqueda semántica."""
        if not evaluaciones:
            logger.warning("No hay evaluaciones para indexar")
            return False
        
        try:
            textos = [normalizar_texto_para_embedding(texto) for texto, _ in evaluaciones]
            metadatos = [meta for _, meta in evaluaciones]
            
            self.vectorstore = FAISS.from_texts(textos, self.embeddings, metadatas=metadatos)
            self.vectorstore.save_local(str(self.ruta_store))
            
            archivo_proveedor = self.ruta_store / "embedding_provider.txt"
            archivo_proveedor.write_text(self.proveedor_embeddings, encoding='utf-8')
            
            logger.info(f"Indexadas {len(evaluaciones)} evaluaciones para {self.id_usuario}")
            
            registro = obtener_registro_operacional()
            registro.rag_indexado(len(evaluaciones))
            
            return True
            
        except Exception as e:
            logger.error(f"Error al indexar evaluaciones: {e}")
            return False
    
    index_evaluations = indexar_evaluaciones
    
    def agregar_evaluacion(self, texto_busqueda: str, metadata: Dict[str, Any]) -> bool:
        """Añade una nueva evaluación al índice existente."""
        try:
            texto_normalizado = normalizar_texto_para_embedding(texto_busqueda)
            
            if self.vectorstore is None:
                self.vectorstore = FAISS.from_texts(
                    [texto_normalizado], self.embeddings, metadatas=[metadata]
                )
            else:
                self.vectorstore.add_texts([texto_normalizado], metadatas=[metadata])
            
            self.vectorstore.save_local(str(self.ruta_store))
            
            archivo_proveedor = self.ruta_store / "embedding_provider.txt"
            archivo_proveedor.write_text(self.proveedor_embeddings, encoding='utf-8')
            
            logger.info(f"Evaluación añadida al índice de {self.id_usuario}")
            return True
            
        except Exception as e:
            logger.error(f"Error al añadir evaluación: {e}")
            return False
    
    add_evaluation = agregar_evaluacion
    
    def buscar(self, consulta: str, k: int = 5) -> List[Document]:
        """Realiza búsqueda semántica en el historial."""
        if self.vectorstore is None:
            logger.warning("VectorStore no inicializado")
            return []
        
        try:
            consulta_normalizada = normalizar_texto_para_embedding(consulta)
            documentos = self.vectorstore.similarity_search(consulta_normalizada, k=k)
            self.ultimos_documentos_recuperados = documentos
            
            registro = obtener_registro_operacional()
            registro.rag_consulta(len(documentos))
            
            return documentos
            
        except Exception as e:
            logger.error(f"Error en búsqueda: {e}")
            return []
    
    search = buscar
    
    def buscar_con_puntuaciones(self, consulta: str, k: int = 5) -> List[tuple]:
        """Realiza búsqueda semántica con scores de similitud."""
        if self.vectorstore is None:
            return []
        
        try:
            consulta_normalizada = normalizar_texto_para_embedding(consulta)
            resultados = self.vectorstore.similarity_search_with_score(consulta_normalizada, k=k)
            self.ultimos_documentos_recuperados = [doc for doc, _ in resultados]
            return resultados
            
        except Exception as e:
            logger.error(f"Error en búsqueda con scores: {e}")
            return []
    
    search_with_scores = buscar_con_puntuaciones
    
    def reconstruir_indice(self, evaluaciones: List[tuple]) -> bool:
        """Reconstruye el índice desde cero."""
        if self.ruta_store.exists():
            import shutil
            shutil.rmtree(str(self.ruta_store))
        
        self.ruta_store.mkdir(parents=True, exist_ok=True)
        
        return self.indexar_evaluaciones(evaluaciones)
    
    rebuild_index = reconstruir_indice
    
    @property
    def esta_inicializado(self) -> bool:
        """Verifica si el vectorstore está inicializado."""
        return self.vectorstore is not None
    
    @property
    def is_initialized(self) -> bool:
        return self.esta_inicializado
    
    @property
    def cantidad_documentos(self) -> int:
        """Retorna el número de documentos indexados."""
        if self.vectorstore is None:
            return 0
        try:
            return self.vectorstore.index.ntotal
        except Exception:
            return 0
    
    @property
    def document_count(self) -> int:
        return self.cantidad_documentos


HistoryVectorStore = AlmacenVectorialHistorial
