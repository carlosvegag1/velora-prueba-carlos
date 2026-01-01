"""
Asistente RAG para consultas inteligentes del historial de evaluaciones.

El proveedor de embeddings es independiente del LLM de generación.
"""

import logging
from typing import List, Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from langchain_core.language_models import BaseChatModel

from .almacen_vectorial import AlmacenVectorialHistorial
from ...infraestructura.persistencia import MemoriaUsuario
from ...infraestructura.llm import FabricaEmbeddings

logger = logging.getLogger(__name__)


PROMPT_ASISTENTE_HISTORIAL = """Eres un asistente experto en análisis de evaluaciones de candidatos.

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


class AsistenteHistorial:
    """
    Asistente conversacional RAG para consultas sobre el historial de evaluaciones.
    
    Soporta múltiples proveedores de embeddings independientemente del LLM.
    """
    
    def __init__(
        self,
        id_usuario: str,
        llm: BaseChatModel,
        memoria: Optional[MemoriaUsuario] = None,
        proveedor_embeddings: Optional[str] = None,
        api_key_embeddings: Optional[str] = None
    ):
        """Inicializa el asistente RAG con almacén vectorial y LLM."""
        self.id_usuario = id_usuario
        self.llm = llm
        self.memoria = memoria or MemoriaUsuario()
        
        proveedor_actual = proveedor_embeddings
        if not FabricaEmbeddings.validar_api_key(proveedor_embeddings, api_key_embeddings):
            fallback = FabricaEmbeddings.obtener_proveedor_fallback()
            if fallback:
                proveedor_actual = fallback
                logger.info(f"Usando {fallback} para embeddings (fallback)")
        
        self.almacen_vectorial = AlmacenVectorialHistorial(
            id_usuario,
            proveedor_embeddings=proveedor_actual,
            api_key=api_key_embeddings
        )
        self._asegurar_indexacion()
        
        self.historial_conversacion: List[tuple] = []
        self.ultimos_documentos_recuperados: List[Document] = []
    
    @property
    def user_id(self):
        return self.id_usuario
    
    @property
    def memory(self):
        return self.memoria
    
    @property
    def vectorstore(self):
        return self.almacen_vectorial
    
    @property
    def conversation_history(self):
        return self.historial_conversacion
    
    @property
    def last_retrieved_docs(self):
        return self.ultimos_documentos_recuperados
    
    def _asegurar_indexacion(self):
        """Asegura que el historial esté indexado correctamente."""
        evaluaciones = self.memoria.obtener_textos_buscables(self.id_usuario)
        
        if not evaluaciones:
            logger.info(f"No hay evaluaciones para indexar para {self.id_usuario}")
            return
        
        if not self.almacen_vectorial.esta_inicializado:
            logger.info(f"Creando índice para {self.id_usuario}")
            self.almacen_vectorial.indexar_evaluaciones(evaluaciones)
        else:
            cantidad_actual = self.almacen_vectorial.cantidad_documentos
            if len(evaluaciones) > cantidad_actual:
                logger.info(f"Reindexando: {len(evaluaciones)} evaluaciones (tenía {cantidad_actual})")
                self.almacen_vectorial.reconstruir_indice(evaluaciones)
    
    def _formatear_contexto(self, documentos: List[Document]) -> str:
        """Formatea documentos recuperados como contexto para el LLM."""
        if not documentos:
            return "No se encontraron evaluaciones en el historial."
        
        partes = []
        for i, doc in enumerate(documentos, 1):
            meta = doc.metadata
            parte = f"""
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
            partes.append(parte)
        
        return "\n".join(partes)
    
    def consultar(self, pregunta: str, k: int = 5) -> str:
        """Procesa una pregunta del usuario sobre su historial."""
        # #region agent log
        import json, time, os
        log_path = '/app/.cursor/debug.log' if os.path.exists('/app') else '.cursor/debug.log'
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps({'location':'asistente.py:142','message':'consultar() ENTRY','data':{'pregunta':pregunta,'pregunta_type':str(type(pregunta)),'pregunta_is_none':pregunta is None,'k':k},'timestamp':int(time.time()*1000),'sessionId':'debug-session','hypothesisId':'H2,H4'}) + '\n')
        # #endregion
        
        try:
            # #region agent log
            log_path = '/app/.cursor/debug.log' if os.path.exists('/app') else '.cursor/debug.log'
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps({'location':'asistente.py:144','message':'Before almacen_vectorial.buscar()','data':{'pregunta':pregunta},'timestamp':int(time.time()*1000),'sessionId':'debug-session','hypothesisId':'H4'}) + '\n')
            # #endregion
            
            documentos = self.almacen_vectorial.buscar(pregunta, k=k)
            self.ultimos_documentos_recuperados = documentos
            
            # #region agent log
            log_path = '/app/.cursor/debug.log' if os.path.exists('/app') else '.cursor/debug.log'
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps({'location':'asistente.py:145','message':'After buscar() - before formatear','data':{'docs_count':len(documentos)},'timestamp':int(time.time()*1000),'sessionId':'debug-session','hypothesisId':'H4'}) + '\n')
            # #endregion
            
            contexto = self._formatear_contexto(documentos)
        except Exception as e:
            # #region agent log
            log_path = '/app/.cursor/debug.log' if os.path.exists('/app') else '.cursor/debug.log'
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps({'location':'asistente.py:147','message':'Exception in buscar/formatear','data':{'error':str(e),'error_type':str(type(e))},'timestamp':int(time.time()*1000),'sessionId':'debug-session','hypothesisId':'H4'}) + '\n')
            # #endregion
            raise
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", PROMPT_ASISTENTE_HISTORIAL),
            ("human", "{question}")
        ])
        
        chain = prompt | self.llm
        
        try:
            respuesta = chain.invoke({"context": contexto, "question": pregunta})
            
            if hasattr(respuesta, 'content'):
                texto_respuesta = respuesta.content
            else:
                texto_respuesta = str(respuesta)
            
            self.historial_conversacion.append((pregunta, texto_respuesta))
            
            return texto_respuesta
            
        except Exception as e:
            logger.error(f"Error al generar respuesta: {e}")
            # #region agent log
            log_path = '/app/.cursor/debug.log' if os.path.exists('/app') else '.cursor/debug.log'
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps({'location':'asistente.py:169','message':'Exception in chain.invoke()','data':{'error':str(e),'error_type':str(type(e))},'timestamp':int(time.time()*1000),'sessionId':'debug-session','hypothesisId':'H2'}) + '\n')
            # #endregion
            return f"Error al procesar la consulta: {str(e)}"
    
    query = consultar
    
    def consultar_con_historial(self, pregunta: str, k: int = 5) -> str:
        """Procesa una pregunta considerando el historial de conversación."""
        documentos = self.almacen_vectorial.buscar(pregunta, k=k)
        self.ultimos_documentos_recuperados = documentos
        contexto = self._formatear_contexto(documentos)
        
        mensajes = [("system", PROMPT_ASISTENTE_HISTORIAL.format(context=contexto))]
        
        for p, r in self.historial_conversacion[-3:]:
            mensajes.append(("human", p))
            mensajes.append(("assistant", r))
        
        mensajes.append(("human", pregunta))
        
        prompt = ChatPromptTemplate.from_messages(mensajes)
        
        try:
            chain = prompt | self.llm
            respuesta = chain.invoke({})
            
            if hasattr(respuesta, 'content'):
                texto_respuesta = respuesta.content
            else:
                texto_respuesta = str(respuesta)
            
            self.historial_conversacion.append((pregunta, texto_respuesta))
            return texto_respuesta
            
        except Exception as e:
            logger.error(f"Error al generar respuesta: {e}")
            return f"Error: {str(e)}"
    
    query_with_history = consultar_con_historial
    
    def obtener_resumen_rapido(self) -> str:
        """Genera un resumen rápido del historial sin usar el LLM."""
        evaluaciones = self.memoria.obtener_evaluaciones(self.id_usuario)
        
        if not evaluaciones:
            return "No tienes evaluaciones en tu historial."
        
        total = len(evaluaciones)
        puntuaciones = [e.get("score", 0) for e in evaluaciones]
        promedio = sum(puntuaciones) / total if total > 0 else 0
        
        aprobadas = sum(1 for e in evaluaciones if e.get("status") == "approved")
        rechazadas = sum(1 for e in evaluaciones if e.get("status") == "rejected")
        solo_fase1 = sum(1 for e in evaluaciones if e.get("status") == "phase1_only")
        
        ultima = max(evaluaciones, key=lambda x: x.get("timestamp", ""))
        
        resumen = f"""
**Resumen de tu Historial**

| Métrica | Valor |
|---------|-------|
| Total evaluaciones | {total} |
| Puntuación promedio | {promedio:.1f}% |
| Aprobadas | {aprobadas} |
| Rechazadas | {rechazadas} |
| Solo Fase 1 | {solo_fase1} |

**Ultima evaluacion**: {ultima.get('timestamp', 'N/A')[:10]}
- Puesto: {ultima.get('job_offer_title', 'N/A')}
- Puntuación: {ultima.get('score', 0):.1f}%
- Estado: {ultima.get('status', 'N/A')}
"""
        return resumen
    
    get_quick_summary = obtener_resumen_rapido
    
    def limpiar_historial(self):
        """Limpia el historial de conversación."""
        self.historial_conversacion = []
    
    clear_history = limpiar_historial
    
    def refrescar_indice(self):
        """Fuerza una re-indexación del historial."""
        evaluaciones = self.memoria.obtener_textos_buscables(self.id_usuario)
        if evaluaciones:
            self.almacen_vectorial.reconstruir_indice(evaluaciones)
    
    refresh_index = refrescar_indice


HistoryChatbot = AsistenteHistorial
