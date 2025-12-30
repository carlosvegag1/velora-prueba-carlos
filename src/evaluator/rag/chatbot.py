"""
Chatbot RAG para consultas inteligentes del historial de evaluaciones.
Utiliza LangChain para orquestar embeddings, recuperación y generación.

Arquitectura desacoplada: El proveedor de embeddings es independiente del LLM.
"""

import logging
from typing import List, Optional, Dict, Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from langchain_core.language_models import BaseChatModel

from .vectorstore import HistoryVectorStore
from ..storage.memory import UserMemory
from ..llm.embeddings_factory import EmbeddingFactory

logger = logging.getLogger(__name__)


# Prompt del sistema para el chatbot
HISTORY_CHATBOT_PROMPT = """Eres un asistente experto en análisis de evaluaciones de candidatos.

CONTEXTO DEL HISTORIAL:
{context}

Tu rol es responder preguntas sobre el historial de evaluaciones del usuario de forma precisa y útil.

INSTRUCCIONES:
1. Usa SOLO la información del contexto proporcionado
2. Si preguntan por patrones, analiza múltiples evaluaciones del contexto
3. Si preguntan por una evaluación específica, da detalles completos
4. Puedes hacer cálculos (promedios, tendencias, comparaciones)
5. Sé conciso pero informativo
6. Si no hay información suficiente en el contexto, indícalo claramente

FORMATO DE RESPUESTA:
- Usa markdown para estructurar la respuesta
- Incluye datos específicos cuando estén disponibles
- Destaca información clave con **negritas**
"""


class HistoryChatbot:
    """
    Chatbot conversacional para consultas sobre el historial de evaluaciones.
    Combina búsqueda semántica (RAG) con generación de respuestas.
    
    Soporta múltiples proveedores de embeddings (OpenAI, Google, etc.)
    independientemente del LLM seleccionado para generación.
    """
    
    def __init__(
        self,
        user_id: str,
        llm: BaseChatModel,
        memory: Optional[UserMemory] = None,
        embedding_provider: str = "openai",
        embedding_api_key: Optional[str] = None
    ):
        """
        Inicializa el chatbot RAG.
        
        Args:
            user_id: ID del usuario
            llm: Modelo de lenguaje a usar
            memory: Instancia de UserMemory (opcional, se crea si no se proporciona)
            embedding_provider: Proveedor de embeddings ('openai', 'google')
            embedding_api_key: API key para embeddings (opcional, puede estar en env)
        """
        self.user_id = user_id
        self.llm = llm
        self.memory = memory or UserMemory()
        
        # Determinar proveedor de embeddings con fallback
        actual_provider = embedding_provider
        if not EmbeddingFactory.validate_api_key(embedding_provider, embedding_api_key):
            # Intentar fallback a un proveedor disponible
            fallback = EmbeddingFactory.get_fallback_provider()
            if fallback:
                actual_provider = fallback
                logger.info(f"Usando {fallback} para embeddings (fallback)")
        
        # Inicializar vectorstore con el proveedor configurado
        self.vectorstore = HistoryVectorStore(
            user_id,
            embedding_provider=actual_provider,
            api_key=embedding_api_key
        )
        self._ensure_indexed()
        
        # Historial de conversación (simple)
        self.conversation_history: List[tuple] = []
        
        # Últimos documentos recuperados
        self.last_retrieved_docs: List[Document] = []
    
    def _ensure_indexed(self):
        """
        Asegura que el historial esté indexado en el vectorstore.
        Si no hay índice o hay nuevas evaluaciones, reindexar.
        """
        evaluations = self.memory.get_searchable_texts(self.user_id)
        
        if not evaluations:
            logger.info(f"No hay evaluaciones para indexar para {self.user_id}")
            return
        
        # Si no hay índice, crear uno
        if not self.vectorstore.is_initialized:
            logger.info(f"Creando índice para {self.user_id}")
            self.vectorstore.index_evaluations(evaluations)
        else:
            # Verificar si hay nuevas evaluaciones
            current_count = self.vectorstore.document_count
            if len(evaluations) > current_count:
                logger.info(f"Reindexando: {len(evaluations)} evaluaciones (tenía {current_count})")
                self.vectorstore.rebuild_index(evaluations)
    
    def _format_context(self, docs: List[Document]) -> str:
        """
        Formatea los documentos recuperados como contexto para el LLM.
        
        Args:
            docs: Documentos recuperados
            
        Returns:
            Contexto formateado como string
        """
        if not docs:
            return "No se encontraron evaluaciones en el historial."
        
        context_parts = []
        for i, doc in enumerate(docs, 1):
            meta = doc.metadata
            part = f"""
--- Evaluación #{i} ---
- ID: {meta.get('evaluation_id', 'N/A')[:8]}...
- Fecha: {meta.get('timestamp', 'N/A')[:10]}
- Puesto: {meta.get('job_offer_title', 'N/A')}
- Puntuación: {meta.get('score', 0):.1f}%
- Estado: {meta.get('status', 'N/A')}
- Razón de rechazo: {meta.get('rejection_reason', 'N/A')}
- Brechas: {meta.get('gap_summary', 'N/A')}
- Fortalezas: {meta.get('strengths_summary', 'N/A')}

Texto completo: {doc.page_content[:500]}
"""
            context_parts.append(part)
        
        return "\n".join(context_parts)
    
    def query(
        self,
        question: str,
        k: int = 5
    ) -> str:
        """
        Procesa una pregunta del usuario sobre su historial.
        
        Args:
            question: Pregunta del usuario
            k: Número de documentos a recuperar
            
        Returns:
            Respuesta generada
        """
        # 1. Buscar documentos relevantes
        docs = self.vectorstore.search(question, k=k)
        self.last_retrieved_docs = docs
        
        # 2. Formatear contexto
        context = self._format_context(docs)
        
        # 3. Crear prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", HISTORY_CHATBOT_PROMPT),
            ("human", "{question}")
        ])
        
        # 4. Crear chain y ejecutar
        chain = prompt | self.llm
        
        try:
            response = chain.invoke({
                "context": context,
                "question": question
            })
            
            # Extraer contenido de la respuesta
            if hasattr(response, 'content'):
                answer = response.content
            else:
                answer = str(response)
            
            # Guardar en historial
            self.conversation_history.append((question, answer))
            
            return answer
            
        except Exception as e:
            logger.error(f"Error al generar respuesta: {e}")
            return f"Error al procesar la consulta: {str(e)}"
    
    def query_with_history(
        self,
        question: str,
        k: int = 5
    ) -> str:
        """
        Procesa una pregunta considerando el historial de conversación.
        
        Args:
            question: Pregunta del usuario
            k: Número de documentos a recuperar
            
        Returns:
            Respuesta generada
        """
        # 1. Buscar documentos
        docs = self.vectorstore.search(question, k=k)
        self.last_retrieved_docs = docs
        context = self._format_context(docs)
        
        # 2. Construir mensajes con historial
        messages = [("system", HISTORY_CHATBOT_PROMPT.format(context=context))]
        
        # Añadir historial reciente (últimas 3 interacciones)
        for q, a in self.conversation_history[-3:]:
            messages.append(("human", q))
            messages.append(("assistant", a))
        
        messages.append(("human", question))
        
        # 3. Crear prompt con historial
        prompt = ChatPromptTemplate.from_messages(messages)
        
        # 4. Generar respuesta
        try:
            chain = prompt | self.llm
            response = chain.invoke({})
            
            if hasattr(response, 'content'):
                answer = response.content
            else:
                answer = str(response)
            
            self.conversation_history.append((question, answer))
            return answer
            
        except Exception as e:
            logger.error(f"Error al generar respuesta: {e}")
            return f"Error: {str(e)}"
    
    def get_quick_summary(self) -> str:
        """
        Genera un resumen rápido del historial sin usar el LLM.
        Útil para mostrar estadísticas básicas.
        
        Returns:
            Resumen del historial
        """
        evaluations = self.memory.get_evaluations(self.user_id)
        
        if not evaluations:
            return "📭 No tienes evaluaciones en tu historial."
        
        # Calcular estadísticas
        total = len(evaluations)
        scores = [e.get("score", 0) for e in evaluations]
        avg_score = sum(scores) / total if total > 0 else 0
        
        approved = sum(1 for e in evaluations if e.get("status") == "approved")
        rejected = sum(1 for e in evaluations if e.get("status") == "rejected")
        phase1_only = sum(1 for e in evaluations if e.get("status") == "phase1_only")
        
        # Última evaluación
        latest = max(evaluations, key=lambda x: x.get("timestamp", ""))
        
        summary = f"""
**Resumen de tu Historial**

| Métrica | Valor |
|---------|-------|
| Total evaluaciones | {total} |
| Puntuación promedio | {avg_score:.1f}% |
| Aprobadas | {approved} |
| Rechazadas | {rejected} |
| Solo Fase 1 | {phase1_only} |

📅 **Última evaluación**: {latest.get('timestamp', 'N/A')[:10]}
- Puesto: {latest.get('job_offer_title', 'N/A')}
- Puntuación: {latest.get('score', 0):.1f}%
- Estado: {latest.get('status', 'N/A')}
"""
        return summary
    
    def clear_history(self):
        """Limpia el historial de conversación."""
        self.conversation_history = []
    
    def refresh_index(self):
        """Fuerza una re-indexación del historial."""
        evaluations = self.memory.get_searchable_texts(self.user_id)
        if evaluations:
            self.vectorstore.rebuild_index(evaluations)

