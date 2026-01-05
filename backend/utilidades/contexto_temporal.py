"""
Contexto Temporal: Fecha actual dinamica para calculos de experiencia.
Usa datetime.now() - sin hardcodeo, sin complejidad innecesaria.
"""

from datetime import date


def obtener_fecha_hoy() -> date:
    """Retorna la fecha actual del sistema."""
    return date.today()


def obtener_fecha_formateada() -> str:
    """Retorna la fecha actual en formato legible: '5 de enero de 2026'."""
    meses = {
        1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
        5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
        9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
    }
    hoy = date.today()
    return f"{hoy.day} de {meses[hoy.month]} de {hoy.year}"


def obtener_contexto_prompt() -> str:
    """
    Genera contexto temporal conciso para prompts.
    Una sola linea que indica la fecha actual.
    """
    hoy = date.today()
    return f"FECHA ACTUAL: {obtener_fecha_formateada()} (año {hoy.year})"


# Aliases para compatibilidad
get_today = obtener_fecha_hoy
get_formatted_date = obtener_fecha_formateada
get_prompt_context = obtener_contexto_prompt
