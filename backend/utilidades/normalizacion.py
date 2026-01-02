"""
Normalizacion de Requisitos: Agrupacion contextual inteligente.
Detecta alternativas (OR) vs acumulativos (AND) para evitar fragmentacion excesiva.
Garantiza granularidad optima preservando estabilidad y reproducibilidad.
"""

import re
from typing import List, Dict, Set, Tuple, Optional


DOMINIOS_EQUIVALENTES = {
    "lenguajes_programacion": {
        "keywords": ["python", "java", "javascript", "typescript", "c++", "c#", "go", "rust", "ruby", "php", "kotlin", "swift", "scala"],
        "prefijos": ["conocimientos en", "experiencia en", "dominio de", "programacion en"]
    },
    "frameworks_web": {
        "keywords": ["django", "flask", "fastapi", "spring", "react", "angular", "vue", "node", "express", "rails", "laravel"],
        "prefijos": ["experiencia con", "conocimientos en", "desarrollo con"]
    },
    "bases_datos": {
        "keywords": ["postgresql", "mysql", "mongodb", "redis", "oracle", "sqlserver", "sqlite", "dynamodb", "cassandra"],
        "prefijos": ["experiencia con", "conocimientos en", "manejo de"]
    },
    "cloud": {
        "keywords": ["aws", "azure", "gcp", "google cloud", "amazon web services", "digitalocean", "heroku"],
        "prefijos": ["experiencia en", "certificacion en", "conocimientos de"]
    },
    "herramientas_gestion": {
        "keywords": ["jira", "trello", "asana", "monday", "clickup", "notion", "confluence"],
        "prefijos": ["manejo de", "experiencia con", "uso de"]
    },
    "metodologias": {
        "keywords": ["scrum", "kanban", "agile", "lean", "waterfall", "safe", "xp"],
        "prefijos": ["experiencia en", "conocimientos de", "metodologias"]
    },
    "certificaciones_pm": {
        "keywords": ["pmp", "prince2", "scrum master", "psm", "csm", "pmi-acp", "safe"],
        "prefijos": ["certificacion", "certificado"]
    },
    "industrias": {
        "keywords": ["retail", "e-commerce", "ecommerce", "logistica", "fintech", "banca", "seguros", "salud", "healthcare", "educacion", "telco", "telecomunicaciones", "automotive", "pharma"],
        "prefijos": ["experiencia en", "sector", "industria"]
    },
    "contenedores": {
        "keywords": ["docker", "kubernetes", "k8s", "openshift", "podman", "containerd"],
        "prefijos": ["experiencia con", "conocimientos en"]
    },
    "ci_cd": {
        "keywords": ["jenkins", "gitlab ci", "github actions", "circleci", "travis", "bamboo", "azure devops"],
        "prefijos": ["experiencia con", "conocimientos en"]
    }
}

INDICADORES_OR = [
    r'\s+o\s+',
    r'\s+or\s+',
    r'\s*/\s*',
    r'\(([^)]+)\)',
]

INDICADORES_AND_EXPLICITO = [
    r'\s+y\s+(?!experiencia)(?!conocimientos)',
    r'\s+and\s+',
    r'\s+ademas\s+de\s+',
    r'\s+junto\s+con\s+',
]

PATRONES_ALTERNATIVAS = [
    r'(?:alguno|cualquiera)\s+de\s+(?:los\s+siguientes|estas?)',
    r'(?:preferiblemente|idealmente)\s+(?:en\s+)?(.+)',
    r'frameworks?\s+(?:web|backend)\s*\(([^)]+)\)',
    r'bases?\s+de\s+datos\s*\(([^)]+)\)',
    r'experiencia\s+en\s+(?:sector|industria)\s+(?:de\s+)?(.+)',
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


def _identificar_dominio(texto: str) -> Optional[str]:
    """Identifica el dominio semantico de un texto."""
    texto_lower = texto.lower()
    
    for dominio, config in DOMINIOS_EQUIVALENTES.items():
        for keyword in config["keywords"]:
            if keyword in texto_lower:
                return dominio
    
    return None


def _elementos_mismo_dominio(elementos: List[str]) -> bool:
    """Verifica si todos los elementos pertenecen al mismo dominio semantico."""
    if len(elementos) <= 1:
        return True
    
    dominios = [_identificar_dominio(elem) for elem in elementos]
    dominios_validos = [d for d in dominios if d is not None]
    
    if not dominios_validos:
        return False
    
    return len(set(dominios_validos)) == 1


def _es_alternativa_contextual(texto: str) -> bool:
    """Detecta si el texto indica alternativas (logica OR)."""
    texto_lower = texto.lower()
    
    for patron in PATRONES_ALTERNATIVAS:
        if re.search(patron, texto_lower, re.IGNORECASE):
            return True
    
    for indicador in INDICADORES_OR:
        if re.search(indicador, texto_lower, re.IGNORECASE):
            if not any(re.search(ind, texto_lower, re.IGNORECASE) for ind in INDICADORES_AND_EXPLICITO):
                return True
    
    return False


def _es_acumulativo_explicito(texto: str) -> bool:
    """Detecta si el texto indica requisitos acumulativos (logica AND)."""
    texto_lower = texto.lower()
    
    for indicador in INDICADORES_AND_EXPLICITO:
        if re.search(indicador, texto_lower, re.IGNORECASE):
            return True
    
    return False


def _extraer_elementos(texto: str) -> List[str]:
    """Extrae elementos individuales de un texto."""
    separadores = [r'\s*,\s*', r'\s+y\s+', r'\s+o\s+', r'\s+and\s+', r'\s+or\s+', r'\s*/\s*']
    
    elementos = [texto]
    for sep in separadores:
        nuevos = []
        for elem in elementos:
            partes = re.split(sep, elem, flags=re.IGNORECASE)
            nuevos.extend([p.strip() for p in partes if p.strip() and len(p.strip()) > 1])
        elementos = nuevos
    
    return [e for e in elementos if e and len(e) > 1]


def _obtener_prefijo_contexto(texto_original: str) -> str:
    """Extrae el prefijo contextual de un requisito."""
    texto_lower = texto_original.lower()
    
    for patron in PATRONES_LISTA:
        match = re.match(patron, texto_lower)
        if match:
            return texto_original[:match.start(1)].strip()
    
    return ""


def _limpiar_parentesis_alternativas(texto: str) -> str:
    """Limpia parentesis que indican alternativas y los integra."""
    patron = r'\(([^)]+(?:o|or|/)[^)]+)\)'
    
    def reemplazar(match):
        contenido = match.group(1)
        return contenido
    
    return re.sub(patron, reemplazar, texto, flags=re.IGNORECASE)


def _construir_requisito_agrupado(elementos: List[str], prefijo: str, tipo: str) -> Dict[str, str]:
    """Construye un requisito agrupado con logica OR."""
    if len(elementos) == 1:
        descripcion = f"{prefijo} {elementos[0]}".strip() if prefijo else elementos[0]
    else:
        elementos_formateados = ", ".join(elementos[:-1]) + " o " + elementos[-1]
        descripcion = f"{prefijo} {elementos_formateados}".strip() if prefijo else elementos_formateados
    
    descripcion = re.sub(r'\s+', ' ', descripcion).strip()
    
    return {
        "description": descripcion,
        "type": tipo,
        "logic": "OR",
        "alternatives": elementos
    }


def _construir_requisitos_atomicos(elementos: List[str], prefijo: str, tipo: str) -> List[Dict[str, str]]:
    """Construye requisitos atomicos individuales (logica AND)."""
    requisitos = []
    
    for elemento in elementos:
        elemento_limpio = elemento.strip()
        if not elemento_limpio:
            continue
        
        if prefijo and not any(elemento_limpio.lower().startswith(p) for p in PREFIJOS_PRESERVAR):
            descripcion = f"{prefijo} {elemento_limpio}"
        else:
            descripcion = elemento_limpio
        
        descripcion = re.sub(r'\s+', ' ', descripcion).strip()
        
        requisitos.append({
            "description": descripcion,
            "type": tipo,
            "logic": "AND"
        })
    
    return requisitos


def analizar_requisito(descripcion: str, tipo: str) -> List[Dict[str, str]]:
    """
    Analiza un requisito y decide si agruparlo (OR) o dividirlo (AND).
    
    Reglas de agrupacion:
    - AGRUPAR (OR): Elementos del mismo dominio semantico que son alternativas
    - DIVIDIR (AND): Dominios distintos o requisitos acumulativos explicitos
    
    Ejemplos:
        "Python, Java o C++" -> 1 requisito agrupado (alternativas mismo dominio)
        "Docker y Kubernetes" -> 2 requisitos (tecnologias complementarias)
        "Experiencia en retail, e-commerce o logistica" -> 1 requisito (industrias alternativas)
    """
    descripcion_limpia = _limpiar_parentesis_alternativas(descripcion.strip())
    prefijo = _obtener_prefijo_contexto(descripcion_limpia)
    
    for patron in PATRONES_LISTA:
        match = re.match(patron, descripcion_limpia, re.IGNORECASE)
        if match:
            contenido = match.group(1)
            elementos = _extraer_elementos(contenido)
            
            if len(elementos) <= 1:
                return [{"description": descripcion.strip(), "type": tipo, "logic": "SINGLE"}]
            
            if _es_acumulativo_explicito(descripcion_limpia):
                return _construir_requisitos_atomicos(elementos, prefijo, tipo)
            
            if _es_alternativa_contextual(descripcion_limpia):
                return [_construir_requisito_agrupado(elementos, prefijo, tipo)]
            
            if _elementos_mismo_dominio(elementos):
                return [_construir_requisito_agrupado(elementos, prefijo, tipo)]
            
            return _construir_requisitos_atomicos(elementos, prefijo, tipo)
    
    elementos = _extraer_elementos(descripcion_limpia)
    
    if len(elementos) <= 1:
        return [{"description": descripcion.strip(), "type": tipo, "logic": "SINGLE"}]
    
    if _es_acumulativo_explicito(descripcion_limpia):
        return _construir_requisitos_atomicos(elementos, "", tipo)
    
    if _es_alternativa_contextual(descripcion_limpia) or _elementos_mismo_dominio(elementos):
        return [_construir_requisito_agrupado(elementos, "", tipo)]
    
    return _construir_requisitos_atomicos(elementos, "", tipo)


def normalizar_requisitos(requisitos: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Normaliza requisitos con agrupacion contextual inteligente.
    - Agrupa alternativas del mismo dominio (logica OR)
    - Divide requisitos de dominios distintos (logica AND)
    - Elimina duplicados preservando orden
    """
    requisitos_normalizados = []
    vistos: Set[str] = set()
    
    for req in requisitos:
        descripcion = req.get("description", "").strip()
        tipo = req.get("type", "optional")
        
        if not descripcion:
            continue
        
        requisitos_analizados = analizar_requisito(descripcion, tipo)
        
        for req_normalizado in requisitos_analizados:
            clave = req_normalizado["description"].lower()
            if clave not in vistos:
                vistos.add(clave)
                resultado = {
                    "description": req_normalizado["description"],
                    "type": req_normalizado["type"]
                }
                if "alternatives" in req_normalizado:
                    resultado["alternatives"] = req_normalizado["alternatives"]
                requisitos_normalizados.append(resultado)
    
    return requisitos_normalizados


def descomponer_requisito(descripcion: str, tipo: str) -> List[Dict[str, str]]:
    """Alias para compatibilidad. Usa analizar_requisito internamente."""
    return analizar_requisito(descripcion, tipo)


def validar_atomicidad(requisito: str) -> bool:
    """Verifica si un requisito es atomico o contiene alternativas agrupadas."""
    resultado = analizar_requisito(requisito, "optional")
    return len(resultado) == 1


decompose_requirement = descomponer_requisito
normalize_requirements = normalizar_requisitos
validate_atomicity = validar_atomicidad
analyze_requirement = analizar_requisito
