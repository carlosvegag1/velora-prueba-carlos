"""
Contexto Temporal: Servicio centralizado para referencia temporal del sistema.
Garantiza consistencia en cálculos de experiencia, antigüedad y evaluaciones temporales.
"""

from datetime import date, datetime
from typing import Optional, Tuple
import re


class ContextoTemporal:
    """
    Servicio singleton que proporciona la fecha de referencia del sistema.
    Todas las evaluaciones temporales deben usar este contexto.
    """
    
    _instancia: Optional['ContextoTemporal'] = None
    _fecha_referencia: date = date(2026, 1, 2)
    
    def __new__(cls) -> 'ContextoTemporal':
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
        return cls._instancia
    
    @classmethod
    def obtener_fecha_referencia(cls) -> date:
        return cls._fecha_referencia
    
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
    def calcular_anios_entre(cls, anio_inicio: int, anio_fin: Optional[int] = None) -> float:
        if anio_fin is None or anio_fin >= cls._fecha_referencia.year:
            anio_fin = cls._fecha_referencia.year
        return max(0, anio_fin - anio_inicio)
    
    @classmethod
    def obtener_contexto_prompt(cls) -> str:
        return (
            f"FECHA DE REFERENCIA: {cls.obtener_fecha_formateada()} "
            f"(Usa esta fecha para todos los cálculos de experiencia y antigüedad. "
            f"El año actual es {cls.obtener_anio_referencia()})."
        )
    
    @classmethod
    def generar_instrucciones_experiencia(cls) -> str:
        anio = cls.obtener_anio_referencia()
        return f"""EVALUACIÓN DE EXPERIENCIA TEMPORAL:
- Fecha de referencia: {cls.obtener_fecha_formateada()}
- Año actual: {anio}
- Para calcular años de experiencia: resta el año de inicio del {anio}
- "Presente", "Actual", "Actualmente" = {anio}
- Ejemplo: "2021 - Presente" = {anio - 2021} años de experiencia
- Ejemplo: "2019 - 2022" = 3 años de experiencia"""


_contexto_temporal = ContextoTemporal()


def obtener_contexto_temporal() -> ContextoTemporal:
    return _contexto_temporal


def obtener_fecha_referencia() -> date:
    return ContextoTemporal.obtener_fecha_referencia()


def obtener_contexto_prompt() -> str:
    return ContextoTemporal.obtener_contexto_prompt()


def generar_instrucciones_experiencia() -> str:
    return ContextoTemporal.generar_instrucciones_experiencia()


get_temporal_context = obtener_contexto_temporal
get_reference_date = obtener_fecha_referencia
get_prompt_context = obtener_contexto_prompt
generate_experience_instructions = generar_instrucciones_experiencia
TemporalContext = ContextoTemporal

