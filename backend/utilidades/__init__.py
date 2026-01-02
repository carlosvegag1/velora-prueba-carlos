"""
Utilidades transversales: logger, procesamiento, normalizacion y contexto temporal.
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

from .normalizacion import (
    normalizar_requisitos,
    descomponer_requisito,
    analizar_requisito,
    validar_atomicidad,
)

from .contexto_temporal import (
    ContextoTemporal,
    obtener_contexto_temporal,
    obtener_fecha_referencia,
    obtener_anio_sistema,
    obtener_contexto_prompt,
    generar_instrucciones_experiencia,
    calcular_experiencia,
    validar_contexto_temporal,
    ANIO_SISTEMA,
)

__all__ = [
    "RegistroOperacional", "obtener_registro_operacional",
    "Colores", "Indicadores",
    "calcular_puntuacion", "cargar_archivo_texto",
    "limpiar_descripcion_requisito",
    "procesar_coincidencias", "agregar_requisitos_no_procesados",
    "normalizar_requisitos", "descomponer_requisito",
    "analizar_requisito", "validar_atomicidad",
    "ContextoTemporal", "obtener_contexto_temporal",
    "obtener_fecha_referencia", "obtener_anio_sistema",
    "obtener_contexto_prompt", "generar_instrucciones_experiencia",
    "calcular_experiencia", "validar_contexto_temporal",
    "ANIO_SISTEMA",
]
