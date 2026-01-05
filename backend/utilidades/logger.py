"""
Logger: Sistema de registro operacional con colores ANSI para terminal.
Configurado para funcionar correctamente en Docker con flush inmediato.
"""

import logging
import sys
from typing import Optional
from datetime import datetime


class Colores:
    CABECERA = '\033[95m'
    AZUL = '\033[94m'
    CIAN = '\033[96m'
    VERDE = '\033[92m'
    AMARILLO = '\033[93m'
    ROJO = '\033[91m'
    MAGENTA = '\033[35m'
    NEGRITA = '\033[1m'
    TENUE = '\033[2m'
    RESET = '\033[0m'


Colors = Colores


class Indicadores:
    OK = "[OK]"
    ERROR = "[ERROR]"
    ADVERTENCIA = "[WARN]"
    INFO = "[INFO]"
    INICIO = "[START]"
    FIN = "[END]"
    CONFIG = "[CFG]"
    ACTIVO = "[ON]"
    INACTIVO = "[OFF]"


class FlushStreamHandler(logging.StreamHandler):
    """Handler que fuerza flush despues de cada mensaje (necesario para Docker)."""
    
    def emit(self, record):
        super().emit(record)
        self.flush()


class RegistroOperacional:
    """
    Registro operacional singleton para trazabilidad del sistema.
    Flush inmediato para visibilidad en Docker.
    """
    
    _instancia: Optional['RegistroOperacional'] = None
    _inicializado: bool = False
    
    def __new__(cls) -> 'RegistroOperacional':
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
        return cls._instancia
    
    def __init__(self):
        if RegistroOperacional._inicializado:
            return
        
        RegistroOperacional._inicializado = True
        self.habilitado = True
        
        self.logger = logging.getLogger("velora.sistema")
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False
        
        if not self.logger.handlers:
            handler = FlushStreamHandler(sys.stdout)
            handler.setLevel(logging.INFO)
            handler.setFormatter(logging.Formatter('%(message)s'))
            self.logger.addHandler(handler)
    
    def _marca_tiempo(self) -> str:
        return datetime.now().strftime("%H:%M:%S")
    
    def _formatear(self, indicador: str, categoria: str, mensaje: str, color: str = "") -> str:
        ts = self._marca_tiempo()
        reset = Colores.RESET if color else ""
        return f"{color}[{ts}] {indicador} [{categoria}] {mensaje}{reset}"
    
    def config_langgraph(self, habilitado: bool):
        if not self.habilitado:
            return
        estado = f"{Colores.VERDE}ACTIVADO{Colores.RESET}" if habilitado else f"{Colores.AMARILLO}DESACTIVADO{Colores.RESET}"
        detalle = "Orquestacion multi-agente" if habilitado else "Flujo tradicional"
        msg = self._formatear(Indicadores.CONFIG, "CONFIG", f"LangGraph: {estado} - {detalle}", Colores.CIAN)
        self.logger.info(msg)
    
    def config_semantic(self, habilitado: bool, inicializado: bool = True, razon: str = ""):
        if not self.habilitado:
            return
        if habilitado and inicializado:
            estado = f"{Colores.VERDE}ACTIVADO{Colores.RESET}"
            detalle = "Busqueda vectorial FAISS"
        elif habilitado and not inicializado:
            estado = f"{Colores.ROJO}FALLBACK{Colores.RESET}"
            detalle = razon if razon else "Error inicializacion"
        else:
            estado = f"{Colores.AMARILLO}DESACTIVADO{Colores.RESET}"
            detalle = "Matching directo con LLM"
        msg = self._formatear(Indicadores.CONFIG, "CONFIG", f"Embeddings: {estado} - {detalle}", Colores.CIAN)
        self.logger.info(msg)
    
    def config_proveedor(self, proveedor: str, modelo: str):
        if not self.habilitado:
            return
        msg = self._formatear(Indicadores.CONFIG, "CONFIG", f"LLM: {Colores.NEGRITA}{proveedor.upper()}/{modelo}{Colores.RESET}", Colores.CIAN)
        self.logger.info(msg)
    
    config_provider = config_proveedor
    
    def fase1_inicio(self, modo: str = "tradicional"):
        if not self.habilitado:
            return
        etiqueta = "LangGraph Multi-Agente" if modo == "langgraph" else "Tradicional"
        msg = self._formatear(Indicadores.INICIO, "FASE 1", f"Iniciando analisis - Modo: {Colores.NEGRITA}{etiqueta}{Colores.RESET}", Colores.AZUL)
        self.logger.info(msg)
    
    phase1_start = fase1_inicio
    
    def extraccion_completa(self, total: int, obligatorios: int, opcionales: int):
        if not self.habilitado:
            return
        msg = self._formatear(Indicadores.OK, "EXTRACCION", f"Requisitos: {Colores.NEGRITA}{total}{Colores.RESET} (Obligatorios: {obligatorios}, Deseables: {opcionales})", Colores.VERDE)
        self.logger.info(msg)
    
    extraction_complete = extraccion_completa
    
    def indexacion_semantica(self, fragmentos: int):
        if not self.habilitado:
            return
        msg = self._formatear(Indicadores.OK, "EMBEDDINGS", f"CV indexado: {Colores.NEGRITA}{fragmentos} fragmentos{Colores.RESET}", Colores.AZUL)
        self.logger.info(msg)
    
    semantic_indexing = indexacion_semantica
    
    def evidencia_semantica_encontrada(self, con_evidencia: int, total: int):
        if not self.habilitado:
            return
        msg = self._formatear(Indicadores.INFO, "EMBEDDINGS", f"Evidencia: {Colores.NEGRITA}{con_evidencia}/{total}{Colores.RESET} requisitos", Colores.AZUL)
        self.logger.info(msg)
    
    semantic_evidence_found = evidencia_semantica_encontrada
    
    def matching_completo(self, cumplidos: int, no_cumplidos: int, puntuacion: float):
        if not self.habilitado:
            return
        color_punt = Colores.VERDE if puntuacion >= 70 else (Colores.AMARILLO if puntuacion >= 40 else Colores.ROJO)
        msg = self._formatear(Indicadores.OK, "MATCHING", f"{Colores.VERDE}{cumplidos} cumplidos{Colores.RESET}, {Colores.ROJO}{no_cumplidos} no cumplidos{Colores.RESET} - Puntuacion: {color_punt}{Colores.NEGRITA}{puntuacion:.1f}%{Colores.RESET}", Colores.AZUL)
        self.logger.info(msg)
    
    matching_complete = matching_completo
    
    def fase1_completa(self, descartado: bool, puntuacion: float, duracion_ms: Optional[int] = None):
        if not self.habilitado:
            return
        estado = f"{Colores.ROJO}DESCARTADO{Colores.RESET}" if descartado else f"{Colores.VERDE}APTO{Colores.RESET}"
        duracion_str = f" ({duracion_ms}ms)" if duracion_ms else ""
        color = Colores.ROJO if descartado else Colores.VERDE
        msg = self._formatear(Indicadores.FIN, "FASE 1", f"Completada{duracion_str} - Estado: {estado}, Puntuacion: {Colores.NEGRITA}{puntuacion:.1f}%{Colores.RESET}", color)
        self.logger.info(msg)
    
    phase1_complete = fase1_completa
    
    def nodo_langgraph(self, nombre_nodo: str, estado: str = "ejecutando"):
        if not self.habilitado:
            return
        msg = self._formatear(Indicadores.INFO, "LANGGRAPH", f"Nodo '{nombre_nodo}' - {estado}", Colores.CIAN)
        self.logger.info(msg)
    
    langgraph_node = nodo_langgraph
    
    def fase2_inicio(self, requisitos_faltantes: int):
        if not self.habilitado:
            return
        msg = self._formatear(Indicadores.INICIO, "FASE 2", f"Iniciando entrevista - {Colores.NEGRITA}{requisitos_faltantes}{Colores.RESET} requisitos a verificar", Colores.AZUL)
        self.logger.info(msg)
    
    phase2_start = fase2_inicio
    
    def fase2_pregunta(self, indice: int, total: int):
        if not self.habilitado:
            return
        msg = self._formatear(Indicadores.INFO, "ENTREVISTA", f"Pregunta {indice}/{total} generada", Colores.AZUL)
        self.logger.info(msg)
    
    phase2_question = fase2_pregunta
    
    def fase2_completa(self, verificados: int, puntuacion_final: float):
        if not self.habilitado:
            return
        msg = self._formatear(Indicadores.FIN, "FASE 2", f"Completada - {Colores.NEGRITA}{verificados}{Colores.RESET} verificados, Puntuacion: {Colores.NEGRITA}{puntuacion_final:.1f}%{Colores.RESET}", Colores.VERDE)
        self.logger.info(msg)
    
    phase2_complete = fase2_completa
    
    def rag_indexado(self, num_documentos: int):
        if not self.habilitado:
            return
        msg = self._formatear(Indicadores.OK, "RAG", f"Historial indexado: {Colores.NEGRITA}{num_documentos}{Colores.RESET} evaluaciones", Colores.AZUL)
        self.logger.info(msg)
    
    rag_indexed = rag_indexado
    
    def rag_consulta(self, recuperados: int):
        if not self.habilitado:
            return
        msg = self._formatear(Indicadores.INFO, "RAG", f"Consulta ejecutada - {Colores.NEGRITA}{recuperados}{Colores.RESET} documentos", Colores.AZUL)
        self.logger.info(msg)
    
    rag_query = rag_consulta
    
    def evaluacion_guardada(self, id_usuario: str, tipo: str = "enriquecida"):
        if not self.habilitado:
            return
        msg = self._formatear(Indicadores.OK, "ALMACENAMIENTO", f"Evaluacion {tipo} guardada para '{id_usuario}'", Colores.VERDE)
        self.logger.info(msg)
    
    evaluation_saved = evaluacion_guardada
    
    def info(self, mensaje: str, componente: str = "INFO"):
        if not self.habilitado:
            return
        msg = self._formatear(Indicadores.INFO, componente, mensaje, Colores.AZUL)
        self.logger.info(msg)
    
    def advertencia(self, componente: str, mensaje: str):
        if not self.habilitado:
            return
        msg = self._formatear(Indicadores.ADVERTENCIA, componente, mensaje, Colores.AMARILLO)
        self.logger.warning(msg)
    
    warning = advertencia
    
    def error(self, componente: str, mensaje: str):
        if not self.habilitado:
            return
        msg = self._formatear(Indicadores.ERROR, componente, mensaje, Colores.ROJO)
        self.logger.error(msg)
    
    def separador(self, titulo: str = ""):
        if not self.habilitado:
            return
        if titulo:
            self.logger.info(f"\n{Colores.NEGRITA}{'='*20} {titulo} {'='*20}{Colores.RESET}")
        else:
            self.logger.info(f"{Colores.NEGRITA}{'='*50}{Colores.RESET}")


_registro_operacional = RegistroOperacional()


def obtener_registro_operacional() -> RegistroOperacional:
    return _registro_operacional


get_operational_logger = obtener_registro_operacional
OperationalLogger = RegistroOperacional
