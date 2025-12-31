"""
Utilidades transversales: logger y funciones de procesamiento.
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

__all__ = [
    "RegistroOperacional", "obtener_registro_operacional",
    "Colores", "Indicadores",
    "calcular_puntuacion", "cargar_archivo_texto",
    "limpiar_descripcion_requisito",
    "procesar_coincidencias", "agregar_requisitos_no_procesados",
]
