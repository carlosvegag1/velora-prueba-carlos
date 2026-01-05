"""
Funciones de procesamiento: cálculo de puntuaciones y procesamiento de requisitos.
"""

import re
from pathlib import Path
from typing import List, Dict, Set, Tuple, Any

from ..modelos import Requisito, TipoRequisito, NivelConfianza


def calcular_puntuacion(
    total_requisitos: int,
    cantidad_cumplidos: int,
    tiene_obligatorio_no_cumplido: bool
) -> float:
    """
    Calcula la puntuación según reglas del sistema:
    - Si falta obligatorio: 0%
    - Si todos cumplen: 100%
    - Resto: proporcional
    """
    if total_requisitos == 0:
        return 100.0
    if tiene_obligatorio_no_cumplido:
        return 0.0
    return (cantidad_cumplidos / total_requisitos) * 100.0


calculate_score = calcular_puntuacion


def cargar_archivo_texto(ruta_archivo: str) -> str:
    """Carga contenido de archivo de texto."""
    path = Path(ruta_archivo)
    if not path.exists():
        raise FileNotFoundError(f"El archivo no existe: {ruta_archivo}")
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


load_text_file = cargar_archivo_texto


def limpiar_descripcion_requisito(descripcion: str) -> str:
    """Elimina prefijos tipo [OBLIGATORY] de descripciones."""
    return re.sub(r'^\s*\[(OBLIGATORY|OPTIONAL)\]\s*', '', descripcion, flags=re.IGNORECASE).strip()


clean_requirement_description = limpiar_descripcion_requisito


def procesar_coincidencias(
    coincidencias: List[Dict[str, Any]],
    requisitos: List[Dict[str, str]],
    evidencia_semantica: Dict[str, Dict] = None
) -> Tuple[List[Requisito], List[Requisito], List[str], Set[str]]:
    """
    Procesa resultados de matching y genera listas de requisitos.
    Retorna: (cumplidos, no_cumplidos, faltantes, procesados)
    """
    mapa_requisitos = {req["description"].lower(): req for req in requisitos}
    
    requisitos_cumplidos = []
    requisitos_no_cumplidos = []
    requisitos_faltantes = []
    procesados: Set[str] = set()
    
    for coincidencia in coincidencias:
        desc_raw = coincidencia["requirement_description"]
        desc_limpia = limpiar_descripcion_requisito(desc_raw)
        desc_lower = desc_limpia.lower().strip()
        
        if desc_lower in procesados:
            continue
        procesados.add(desc_lower)
        
        original = mapa_requisitos.get(desc_lower)
        if not original:
            for clave, req in mapa_requisitos.items():
                if desc_lower in clave or clave in desc_lower:
                    original = req
                    break
        
        if not original:
            continue
        
        confianza_str = coincidencia.get("confidence", "medium")
        confianza = NivelConfianza(confianza_str) if confianza_str else NivelConfianza.MEDIO
        
        puntuacion_semantica = None
        evidencia_cercana = None
        if evidencia_semantica:
            ev_sem = evidencia_semantica.get(desc_lower) or evidencia_semantica.get(original["description"].lower())
            if ev_sem:
                puntuacion_semantica = ev_sem.get("semantic_score")
                evidencia_cercana = ev_sem.get("text")
        
        evidencia_final = coincidencia.get("evidence")
        
        if not coincidencia["fulfilled"] and evidencia_cercana and not evidencia_final:
            evidencia_final = f"[Fragmento mas cercano encontrado (score: {puntuacion_semantica:.2f}): '{evidencia_cercana[:150]}...'] - Contenido insuficiente para cumplir el requisito."
        
        requisito = Requisito(
            description=original["description"],
            type=TipoRequisito(original["type"]),
            fulfilled=coincidencia["fulfilled"],
            found_in_cv=coincidencia["found_in_cv"],
            evidence=evidencia_final,
            confidence=confianza,
            reasoning=coincidencia.get("reasoning"),
            semantic_score=puntuacion_semantica or coincidencia.get("semantic_score")
        )
        
        if coincidencia["fulfilled"]:
            requisitos_cumplidos.append(requisito)
        else:
            requisitos_no_cumplidos.append(requisito)
            requisitos_faltantes.append(original["description"])
    
    return requisitos_cumplidos, requisitos_no_cumplidos, requisitos_faltantes, procesados


process_matches = procesar_coincidencias


def agregar_requisitos_no_procesados(
    requisitos: List[Dict[str, str]],
    procesados: Set[str],
    requisitos_no_cumplidos: List[Requisito],
    requisitos_faltantes: List[str]
) -> None:
    """Añade requisitos no procesados a listas de no cumplidos (in-place)."""
    for req in requisitos:
        if req["description"].lower() not in procesados:
            requisito = Requisito(
                description=req["description"],
                type=TipoRequisito(req["type"]),
                fulfilled=False,
                found_in_cv=False,
                evidence="No se encontro informacion relacionada en el CV para evaluar este requisito.",
                confidence=NivelConfianza.BAJO,
                reasoning="Requisito no evaluado por el modelo - sin evidencia disponible"
            )
            requisitos_no_cumplidos.append(requisito)
            requisitos_faltantes.append(req["description"])


add_unprocessed_requirements = agregar_requisitos_no_procesados
