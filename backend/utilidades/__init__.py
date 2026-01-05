"""
Utilidades transversales: logger, procesamiento y contexto temporal.
"""

from .logger import (
    RegistroOperacional,
    obtener_registro_operacional,
    Colores,
    Indicadores,
)

from .procesamiento import (
    calcular_puntuacion,
    cargar_archivo_texto,
    limpiar_descripcion_requisito,
    procesar_coincidencias,
    agregar_requisitos_no_procesados,
)

from .contexto_temporal import (
    obtener_fecha_hoy,
    obtener_fecha_formateada,
    obtener_contexto_prompt,
)

__all__ = [
    "RegistroOperacional", "obtener_registro_operacional",
    "Colores", "Indicadores",
    "calcular_puntuacion", "cargar_archivo_texto",
    "limpiar_descripcion_requisito",
    "procesar_coincidencias", "agregar_requisitos_no_procesados",
    "obtener_fecha_hoy", "obtener_fecha_formateada", "obtener_contexto_prompt",
]
