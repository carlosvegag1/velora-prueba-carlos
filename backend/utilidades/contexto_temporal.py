"""
Contexto Temporal: Servicio centralizado para referencia temporal del sistema.
Garantiza consistencia en calculos de experiencia, antiguedad y evaluaciones temporales.
ANIO DE REFERENCIA CRITICO: 2026 - NO NEGOCIABLE
"""

from datetime import date
from typing import Optional


ANIO_SISTEMA = 2026
MES_SISTEMA = 1
DIA_SISTEMA = 2


class ContextoTemporal:
    """
    Servicio singleton para la fecha de referencia del sistema.
    CRITICO: Todas las evaluaciones temporales DEBEN usar este contexto.
    """
    
    _instancia: Optional['ContextoTemporal'] = None
    _fecha_referencia: date = date(ANIO_SISTEMA, MES_SISTEMA, DIA_SISTEMA)
    
    def __new__(cls) -> 'ContextoTemporal':
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
        return cls._instancia
    
    @classmethod
    def obtener_fecha_referencia(cls) -> date:
        return cls._fecha_referencia
    
    @classmethod
    def obtener_anio_sistema(cls) -> int:
        return ANIO_SISTEMA
    
    @classmethod
    def obtener_fecha_formateada(cls) -> str:
        meses = {
            1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
            5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
            9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
        }
        dia = cls._fecha_referencia.day
        mes = meses[cls._fecha_referencia.month]
        anio = cls._fecha_referencia.year
        return f"{dia} de {mes} de {anio}"
    
    @classmethod
    def obtener_anio_referencia(cls) -> int:
        return cls._fecha_referencia.year
    
    @classmethod
    def calcular_anios_desde(cls, fecha_inicio: date) -> float:
        delta = cls._fecha_referencia - fecha_inicio
        return round(delta.days / 365.25, 1)
    
    @classmethod
    def calcular_anios_entre(cls, anio_inicio: int, anio_fin: Optional[int] = None) -> int:
        if anio_fin is None or anio_fin >= ANIO_SISTEMA:
            anio_fin = ANIO_SISTEMA
        return max(0, anio_fin - anio_inicio)
    
    @classmethod
    def interpretar_presente(cls) -> int:
        return ANIO_SISTEMA
    
    @classmethod
    def obtener_contexto_prompt(cls) -> str:
        return (
            f"FECHA DE REFERENCIA CRITICA: {cls.obtener_fecha_formateada()} "
            f"(ANIO ACTUAL = {ANIO_SISTEMA}. Usa SIEMPRE este anio para calculos de experiencia. "
            f"'Presente', 'Actualidad', 'Actualmente' = {ANIO_SISTEMA})."
        )
    
    @classmethod
    def generar_instrucciones_experiencia(cls) -> str:
        return f"""EVALUACION DE EXPERIENCIA TEMPORAL (CRITICO):
- ANIO ACTUAL DEL SISTEMA: {ANIO_SISTEMA}
- Fecha de referencia: {cls.obtener_fecha_formateada()}
- "Presente", "Actual", "Actualmente", "hasta la fecha" = {ANIO_SISTEMA}
- Para calcular anios de experiencia: {ANIO_SISTEMA} - anio_inicio

EJEMPLOS DE CALCULO:
- "2020 - Presente" = {ANIO_SISTEMA - 2020} anios de experiencia
- "2021 - Actualidad" = {ANIO_SISTEMA - 2021} anios de experiencia
- "2019 - 2023" = 4 anios de experiencia
- "Desde 2018" = {ANIO_SISTEMA - 2018} anios de experiencia

VALIDACION OBLIGATORIA:
Antes de evaluar cualquier CV, confirmar: ANIO_REFERENCIA = {ANIO_SISTEMA}"""
    
    @classmethod
    def validar_contexto(cls) -> dict:
        return {
            "anio_sistema": ANIO_SISTEMA,
            "fecha_referencia": str(cls._fecha_referencia),
            "interpretacion_presente": ANIO_SISTEMA,
            "valido": True
        }


_contexto_temporal = ContextoTemporal()


def obtener_contexto_temporal() -> ContextoTemporal:
    return _contexto_temporal


def obtener_fecha_referencia() -> date:
    return ContextoTemporal.obtener_fecha_referencia()


def obtener_anio_sistema() -> int:
    return ANIO_SISTEMA


def obtener_contexto_prompt() -> str:
    return ContextoTemporal.obtener_contexto_prompt()


def generar_instrucciones_experiencia() -> str:
    return ContextoTemporal.generar_instrucciones_experiencia()


def calcular_experiencia(anio_inicio: int, anio_fin: Optional[int] = None) -> int:
    return ContextoTemporal.calcular_anios_entre(anio_inicio, anio_fin)


def validar_contexto_temporal() -> dict:
    return ContextoTemporal.validar_contexto()


get_temporal_context = obtener_contexto_temporal
get_reference_date = obtener_fecha_referencia
get_system_year = obtener_anio_sistema
get_prompt_context = obtener_contexto_prompt
generate_experience_instructions = generar_instrucciones_experiencia
calculate_experience = calcular_experiencia
validate_temporal_context = validar_contexto_temporal
TemporalContext = ContextoTemporal
