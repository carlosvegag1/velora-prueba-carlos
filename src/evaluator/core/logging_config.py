"""
Sistema de Logging Operacional para el Evaluador de Candidatos.
Proporciona trazabilidad concisa y estratégica del flujo de procesos.
Utiliza coloreado ANSI para diferenciación visual sin emojis.
"""

import logging
import sys
from typing import Optional
from datetime import datetime


# Colores ANSI para terminal
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    MAGENTA = '\033[35m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    RESET = '\033[0m'


# Indicadores de estado (sin emojis)
class Indicators:
    OK = "[OK]"
    ERROR = "[ERROR]"
    WARN = "[WARN]"
    INFO = "[INFO]"
    START = "[START]"
    END = "[END]"
    CONFIG = "[CFG]"
    ACTIVE = "[ON]"
    INACTIVE = "[OFF]"


class OperationalLogger:
    """
    Logger operacional para trazabilidad del sistema de evaluacion.
    Proporciona logs informativos, concisos y estrategicamente ubicados.
    Usa coloreado ANSI para diferenciacion visual.
    """
    
    _instance: Optional['OperationalLogger'] = None
    _initialized: bool = False
    
    def __new__(cls) -> 'OperationalLogger':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if OperationalLogger._initialized:
            return
        
        OperationalLogger._initialized = True
        self.enabled = True
        
        # Configurar logger
        self.logger = logging.getLogger("velora.evaluator")
        self.logger.setLevel(logging.INFO)
        
        # Handler para consola con formato personalizado
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def _timestamp(self) -> str:
        """Genera timestamp compacto."""
        return datetime.now().strftime("%H:%M:%S")
    
    def _format_msg(self, indicator: str, category: str, message: str, color: str = "") -> str:
        """Formatea mensaje con estilo consistente."""
        ts = self._timestamp()
        reset = Colors.RESET if color else ""
        return f"{color}[{ts}] {indicator} [{category}] {message}{reset}"
    
    # =========================================================================
    # LOGS DE CONFIGURACION
    # =========================================================================
    
    def config_langgraph(self, enabled: bool):
        """Log de configuracion LangGraph."""
        if not self.enabled:
            return
        
        if enabled:
            status = f"{Colors.GREEN}ACTIVADO{Colors.RESET}"
            detail = "Orquestacion avanzada"
        else:
            status = f"{Colors.YELLOW}DESACTIVADO{Colors.RESET}"
            detail = "Flujo tradicional"
        
        msg = self._format_msg(
            Indicators.CONFIG, "CONFIG",
            f"LangGraph Multi-Agente: {status} -> {detail}",
            Colors.CYAN
        )
        self.logger.info(msg)
    
    def config_semantic(self, enabled: bool, initialized: bool = True, reason: str = ""):
        """Log de configuracion Embeddings Semanticos."""
        if not self.enabled:
            return
        
        if enabled and initialized:
            status = f"{Colors.GREEN}ACTIVADO{Colors.RESET}"
            detail = "Busqueda vectorial FAISS"
        elif enabled and not initialized:
            status = f"{Colors.RED}FALLBACK{Colors.RESET}"
            detail = reason if reason else "Error inicializacion, usando metodo base"
        else:
            status = f"{Colors.YELLOW}DESACTIVADO{Colors.RESET}"
            detail = "Matching directo con LLM"
        
        msg = self._format_msg(
            Indicators.CONFIG, "CONFIG",
            f"Embeddings Semanticos: {status} -> {detail}",
            Colors.CYAN
        )
        self.logger.info(msg)
    
    def config_provider(self, provider: str, model: str):
        """Log de proveedor LLM configurado."""
        if not self.enabled:
            return
        
        msg = self._format_msg(
            Indicators.CONFIG, "CONFIG",
            f"LLM: {Colors.BOLD}{provider.upper()}/{model}{Colors.RESET}",
            Colors.CYAN
        )
        self.logger.info(msg)
    
    # =========================================================================
    # LOGS DE FLUJO FASE 1
    # =========================================================================
    
    def phase1_start(self, mode: str = "traditional"):
        """Log de inicio de Fase 1."""
        if not self.enabled:
            return
        
        mode_label = "LangGraph Multi-Agente" if mode == "langgraph" else "Tradicional"
        msg = self._format_msg(
            Indicators.START, "FASE 1",
            f"Iniciando analisis CV vs Oferta -> Modo: {Colors.BOLD}{mode_label}{Colors.RESET}",
            Colors.BLUE
        )
        self.logger.info(msg)
    
    def extraction_complete(self, total: int, obligatory: int, optional: int):
        """Log de extraccion de requisitos completada."""
        if not self.enabled:
            return
        
        msg = self._format_msg(
            Indicators.OK, "EXTRACCION",
            f"Requisitos extraidos: {Colors.BOLD}{total}{Colors.RESET} "
            f"(Obligatorios: {obligatory}, Opcionales: {optional})",
            Colors.GREEN
        )
        self.logger.info(msg)
    
    def semantic_indexing(self, chunks: int):
        """Log de indexacion semantica del CV."""
        if not self.enabled:
            return
        
        msg = self._format_msg(
            Indicators.OK, "EMBEDDINGS",
            f"CV indexado en FAISS: {Colors.BOLD}{chunks} chunks{Colors.RESET} vectorizados",
            Colors.BLUE
        )
        self.logger.info(msg)
    
    def semantic_evidence_found(self, requirements_with_evidence: int, total: int):
        """Log de evidencia semantica encontrada."""
        if not self.enabled:
            return
        
        msg = self._format_msg(
            Indicators.INFO, "EMBEDDINGS",
            f"Evidencia semantica: {Colors.BOLD}{requirements_with_evidence}/{total}{Colors.RESET} requisitos con matches",
            Colors.BLUE
        )
        self.logger.info(msg)
    
    def matching_complete(self, fulfilled: int, unfulfilled: int, score: float):
        """Log de matching completado."""
        if not self.enabled:
            return
        
        score_color = Colors.GREEN if score >= 70 else (Colors.YELLOW if score >= 40 else Colors.RED)
        msg = self._format_msg(
            Indicators.OK, "MATCHING",
            f"Resultado: {Colors.GREEN}{fulfilled} cumplidos{Colors.RESET}, "
            f"{Colors.RED}{unfulfilled} no cumplidos{Colors.RESET} -> "
            f"Score: {score_color}{Colors.BOLD}{score:.1f}%{Colors.RESET}",
            Colors.BLUE
        )
        self.logger.info(msg)
    
    def phase1_complete(self, discarded: bool, score: float, duration_ms: Optional[int] = None):
        """Log de Fase 1 completada."""
        if not self.enabled:
            return
        
        status = f"{Colors.RED}DESCARTADO{Colors.RESET}" if discarded else f"{Colors.GREEN}APTO{Colors.RESET}"
        duration_str = f" ({duration_ms}ms)" if duration_ms else ""
        msg = self._format_msg(
            Indicators.END, "FASE 1",
            f"Completada{duration_str} -> Estado: {status}, Score: {Colors.BOLD}{score:.1f}%{Colors.RESET}",
            Colors.GREEN if not discarded else Colors.RED
        )
        self.logger.info(msg)
    
    # =========================================================================
    # LOGS DE LANGGRAPH
    # =========================================================================
    
    def langgraph_node(self, node_name: str, status: str = "executing"):
        """Log de nodo LangGraph ejecutandose."""
        if not self.enabled:
            return
        
        msg = self._format_msg(
            Indicators.INFO, "LANGGRAPH",
            f"Nodo '{node_name}' -> {status}",
            Colors.CYAN
        )
        self.logger.info(msg)
    
    # =========================================================================
    # LOGS DE FASE 2
    # =========================================================================
    
    def phase2_start(self, missing_count: int):
        """Log de inicio de Fase 2."""
        if not self.enabled:
            return
        
        msg = self._format_msg(
            Indicators.START, "FASE 2",
            f"Iniciando entrevista -> {Colors.BOLD}{missing_count}{Colors.RESET} requisitos a verificar",
            Colors.BLUE
        )
        self.logger.info(msg)
    
    def phase2_question(self, index: int, total: int):
        """Log de pregunta generada."""
        if not self.enabled:
            return
        
        msg = self._format_msg(
            Indicators.INFO, "ENTREVISTA",
            f"Pregunta {index}/{total} generada",
            Colors.BLUE
        )
        self.logger.info(msg)
    
    def phase2_complete(self, verified: int, final_score: float):
        """Log de Fase 2 completada."""
        if not self.enabled:
            return
        
        msg = self._format_msg(
            Indicators.END, "FASE 2",
            f"Completada -> {Colors.BOLD}{verified}{Colors.RESET} requisitos verificados, "
            f"Score final: {Colors.BOLD}{final_score:.1f}%{Colors.RESET}",
            Colors.GREEN
        )
        self.logger.info(msg)
    
    # =========================================================================
    # LOGS DE RAG
    # =========================================================================
    
    def rag_indexed(self, doc_count: int):
        """Log de indexacion RAG completada."""
        if not self.enabled:
            return
        
        msg = self._format_msg(
            Indicators.OK, "RAG",
            f"Historial indexado: {Colors.BOLD}{doc_count}{Colors.RESET} evaluaciones en vectorstore",
            Colors.BLUE
        )
        self.logger.info(msg)
    
    def rag_query(self, retrieved: int):
        """Log de consulta RAG."""
        if not self.enabled:
            return
        
        msg = self._format_msg(
            Indicators.INFO, "RAG",
            f"Consulta ejecutada -> {Colors.BOLD}{retrieved}{Colors.RESET} documentos recuperados",
            Colors.BLUE
        )
        self.logger.info(msg)
    
    # =========================================================================
    # LOGS DE PERSISTENCIA
    # =========================================================================
    
    def evaluation_saved(self, user_id: str, eval_type: str = "enriched"):
        """Log de evaluacion guardada."""
        if not self.enabled:
            return
        
        msg = self._format_msg(
            Indicators.OK, "STORAGE",
            f"Evaluacion {eval_type} guardada para usuario '{user_id}'",
            Colors.GREEN
        )
        self.logger.info(msg)
    
    # =========================================================================
    # LOGS DE ERROR/WARNING
    # =========================================================================
    
    def info(self, message: str, component: str = "INFO"):
        """Log informativo general."""
        if not self.enabled:
            return
        
        msg = self._format_msg(Indicators.INFO, component, message, Colors.BLUE)
        self.logger.info(msg)
    
    def warning(self, component: str, message: str):
        """Log de advertencia."""
        if not self.enabled:
            return
        
        msg = self._format_msg(Indicators.WARN, component, message, Colors.YELLOW)
        self.logger.warning(msg)
    
    def error(self, component: str, message: str):
        """Log de error."""
        if not self.enabled:
            return
        
        msg = self._format_msg(Indicators.ERROR, component, message, Colors.RED)
        self.logger.error(msg)
    
    # =========================================================================
    # SEPARADORES
    # =========================================================================
    
    def separator(self, title: str = ""):
        """Imprime separador visual."""
        if not self.enabled:
            return
        
        if title:
            self.logger.info(f"\n{Colors.BOLD}{'='*20} {title} {'='*20}{Colors.RESET}")
        else:
            self.logger.info(f"{Colors.BOLD}{'='*50}{Colors.RESET}")


# Instancia global singleton
op_logger = OperationalLogger()


def get_operational_logger() -> OperationalLogger:
    """Obtiene la instancia del logger operacional."""
    return op_logger
