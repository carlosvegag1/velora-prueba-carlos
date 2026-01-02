"""
Normalización de Requisitos: Descomposición atómica de requisitos compuestos.
Garantiza granularidad consistente para extracción y matching reproducibles.
"""

import re
from typing import List, Dict, Set, Tuple


SEPARADORES_COMPUESTOS = [
    r'\s*,\s*',
    r'\s+y\s+',
    r'\s+o\s+',
    r'\s+and\s+',
    r'\s+or\s+',
    r'\s*/\s*',
]

PATRONES_LISTA = [
    r'(?:conocimientos?\s+(?:en|de|sobre)\s+)(.+)',
    r'(?:experiencia\s+(?:en|con|trabajando\s+con)\s+)(.+)',
    r'(?:manejo\s+de\s+)(.+)',
    r'(?:dominio\s+de\s+)(.+)',
    r'(?:habilidades?\s+(?:en|de|con)\s+)(.+)',
]

PREFIJOS_PRESERVAR = [
    'conocimientos en',
    'experiencia en',
    'experiencia con',
    'manejo de',
    'dominio de',
    'habilidad en',
    'habilidades en',
]


def _separar_por_todos_los_separadores(texto: str) -> List[str]:
    """Separa texto por todos los separadores de forma recursiva."""
    elementos = [texto]
    
    for sep in SEPARADORES_COMPUESTOS:
        nuevos_elementos = []
        for elem in elementos:
            if re.search(sep, elem, re.IGNORECASE):
                partes = re.split(sep, elem, flags=re.IGNORECASE)
                partes = [p.strip() for p in partes if p.strip() and len(p.strip()) > 1]
                nuevos_elementos.extend(partes)
            else:
                nuevos_elementos.append(elem)
        elementos = nuevos_elementos
    
    return [e for e in elementos if e and len(e) > 1]


def _detectar_elementos_multiples(texto: str) -> Tuple[bool, List[str]]:
    """Detecta si un texto contiene multiples elementos y los separa."""
    texto_limpio = texto.strip()
    
    for patron_lista in PATRONES_LISTA:
        match = re.match(patron_lista, texto_limpio, re.IGNORECASE)
        if match:
            contenido = match.group(1)
            elementos = _separar_por_todos_los_separadores(contenido)
            if len(elementos) > 1:
                return True, elementos
            return False, [texto_limpio]
    
    elementos = _separar_por_todos_los_separadores(texto_limpio)
    
    if len(elementos) > 1:
        elementos_validos = []
        for elem in elementos:
            if not any(elem.lower().startswith(p) for p in ['de', 'en', 'con', 'para']):
                elementos_validos.append(elem)
            elif len(elem) > 10:
                elementos_validos.append(elem)
        
        if len(elementos_validos) > 1:
            return True, elementos_validos
    
    return False, [texto_limpio]


def _obtener_prefijo_contexto(texto_original: str) -> str:
    """Extrae el prefijo contextual de un requisito para preservarlo."""
    texto_lower = texto_original.lower()
    
    for patron_lista in PATRONES_LISTA:
        match = re.match(patron_lista, texto_lower)
        if match:
            prefijo = texto_original[:match.start(1)].strip()
            return prefijo
    
    return ""


def descomponer_requisito(descripcion: str, tipo: str) -> List[Dict[str, str]]:
    """
    Descompone un requisito compuesto en requisitos atómicos.
    
    Ejemplo:
        Input: "Conocimientos en Java, Python y JavaScript"
        Output: [
            {"description": "Conocimientos en Java", "type": "obligatory"},
            {"description": "Conocimientos en Python", "type": "obligatory"},
            {"description": "Conocimientos en JavaScript", "type": "obligatory"}
        ]
    """
    es_multiple, elementos = _detectar_elementos_multiples(descripcion)
    
    if not es_multiple:
        return [{"description": descripcion.strip(), "type": tipo}]
    
    prefijo = _obtener_prefijo_contexto(descripcion)
    requisitos_atomicos = []
    
    for elemento in elementos:
        elemento_limpio = elemento.strip()
        if not elemento_limpio:
            continue
        
        if prefijo and not any(elemento_limpio.lower().startswith(p) for p in PREFIJOS_PRESERVAR):
            descripcion_final = f"{prefijo} {elemento_limpio}"
        else:
            descripcion_final = elemento_limpio
        
        descripcion_final = re.sub(r'\s+', ' ', descripcion_final).strip()
        
        requisitos_atomicos.append({
            "description": descripcion_final,
            "type": tipo
        })
    
    return requisitos_atomicos if requisitos_atomicos else [{"description": descripcion.strip(), "type": tipo}]


def normalizar_requisitos(requisitos: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Normaliza una lista de requisitos aplicando descomposición atómica.
    Elimina duplicados manteniendo el orden.
    """
    requisitos_normalizados = []
    vistos: Set[str] = set()
    
    for req in requisitos:
        descripcion = req.get("description", "").strip()
        tipo = req.get("type", "optional")
        
        if not descripcion:
            continue
        
        requisitos_atomicos = descomponer_requisito(descripcion, tipo)
        
        for req_atomico in requisitos_atomicos:
            clave = req_atomico["description"].lower()
            if clave not in vistos:
                vistos.add(clave)
                requisitos_normalizados.append(req_atomico)
    
    return requisitos_normalizados


def validar_atomicidad(requisito: str) -> bool:
    """Verifica si un requisito es atómico (no contiene múltiples elementos)."""
    es_multiple, _ = _detectar_elementos_multiples(requisito)
    return not es_multiple


decompose_requirement = descomponer_requisito
normalize_requirements = normalizar_requisitos
validate_atomicity = validar_atomicidad

