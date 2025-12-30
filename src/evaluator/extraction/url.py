"""
Módulo de extracción de ofertas de empleo desde URLs.

Implementa scraping inteligente con:
- Detección de contenido renderizado por JavaScript
- Detección de bloqueo de bots
- Fallback a navegador headless (Playwright)
- Extracción semántica de contenido relevante
"""

import logging
import re
from typing import Optional, Dict, Any, List

import requests

# Dependencias opcionales
try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURACIÓN SEMÁNTICA
# =============================================================================

# Keywords que indican contenido de oferta de empleo
JOB_KEYWORDS: List[str] = [
    "responsabilidades", "requisitos", "experiencia",
    "ofrecemos", "qué buscamos", "perfil",
    "funciones", "misión", "rol", "puesto",
    "vacante", "candidato", "competencias",
    "habilidades", "formación", "titulación"
]

# Indicadores de contenido renderizado por JavaScript
JS_RENDER_MARKERS: List[str] = [
    "enable javascript",
    "please enable javascript",
    "__NEXT_DATA__",
    "data-reactroot",
    "app-root",
    "ng-app",
    # SPA/ATS platforms
    "smartrecruiters",
    "attrax",
    "workday",
    "greenhouse",
    "lever.co",
    "ashbyhq",
    "taleo",
    "successfactors",
    "icims",
    "jobvite",
    "breezy",
    "bamboohr"
]

# Indicadores de bloqueo de bots (frases completas para evitar falsos positivos)
BOT_BLOCK_MARKERS: List[str] = [
    "captcha",
    "i'm not a robot",
    "are you a robot",
    "verify you are human",
    "prove you're human",
    "checking your browser",
    "please wait while we verify",
    "access denied",
    "403 forbidden",
    "blocked",
    "unusual traffic"
]

# Selectores CSS para encontrar contenido de ofertas
JOB_CONTENT_SELECTORS: List[str] = [
    ".job-description",
    ".job-details",
    ".vacancy-description",
    '[itemprop="description"]',
    '[data-testid="job-description"]',
    "article",
    "main",
    '[role="main"]',
    ".content",
    ".post-content",
    "section"
]


# =============================================================================
# FUNCIONES DE DETECCIÓN
# =============================================================================

def looks_like_job_offer(text: str) -> bool:
    """
    Verifica si el texto parece ser una oferta de empleo.
    
    Args:
        text: Texto a analizar
        
    Returns:
        True si contiene keywords de ofertas de empleo
    """
    if not text:
        return False
    text_lower = text.lower()
    matches = sum(1 for keyword in JOB_KEYWORDS if keyword in text_lower)
    return matches >= 2  # Al menos 2 keywords para mayor precisión


def detect_js_rendering(html: str) -> bool:
    """
    Detecta si el contenido requiere JavaScript para renderizarse.
    
    Args:
        html: Contenido HTML
        
    Returns:
        True si el contenido parece necesitar JavaScript
    """
    if not html:
        return False
    html_lower = html.lower()
    return any(marker in html_lower for marker in JS_RENDER_MARKERS)


def detect_bot_block(html: str) -> bool:
    """
    Detecta si la página está bloqueando bots.
    
    Args:
        html: Contenido HTML
        
    Returns:
        True si se detecta bloqueo de bots
    """
    if not html:
        return False
    html_lower = html.lower()
    return any(marker in html_lower for marker in BOT_BLOCK_MARKERS)


# =============================================================================
# EXTRACCIÓN Y LIMPIEZA DE CONTENIDO
# =============================================================================

def clean_html_content(html: str) -> Optional[str]:
    """
    Extrae y limpia el contenido textual relevante del HTML.
    
    Utiliza BeautifulSoup si está disponible, con fallback a regex.
    Prioriza selectores semánticos para encontrar contenido de ofertas.
    
    Args:
        html: Contenido HTML crudo
        
    Returns:
        Texto limpio o None si no se encuentra contenido relevante
    """
    if not html:
        return None
    
    # Fallback sin BeautifulSoup
    if not BS4_AVAILABLE:
        text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip() or None

    soup = BeautifulSoup(html, "html.parser")
    
    # Buscar contenido en selectores específicos de ofertas
    best_content = None
    max_length = 0
    
    for selector in JOB_CONTENT_SELECTORS:
        for element in soup.select(selector):
            # Eliminar elementos no deseados
            for bad_tag in element(["script", "style", "noscript", "iframe", "nav", "footer", "header"]):
                bad_tag.decompose()
            
            text = element.get_text(separator="\n", strip=True)
            
            # Preferir contenido más largo que parezca oferta
            if len(text) > max_length and len(text) > 200:
                if looks_like_job_offer(text):
                    best_content = text
                    max_length = len(text)
    
    # Fallback al body completo si no se encuentra contenido específico
    if not best_content and soup.body:
        for bad_tag in soup.body(["script", "style", "noscript", "iframe", "nav", "footer", "header"]):
            bad_tag.decompose()
        best_content = soup.body.get_text(separator="\n", strip=True)
    
    if not best_content:
        return None
    
    # Limpiar líneas vacías y caracteres decorativos
    lines = [
        line.strip()
        for line in best_content.split("\n")
        if line.strip() and not re.fullmatch(r"[-•–—=_*]+", line.strip())
    ]
    
    return "\n".join(lines) if lines else None


# =============================================================================
# ESTRATEGIAS DE SCRAPING
# =============================================================================

def _scrape_with_requests(url: str) -> Dict[str, Any]:
    """
    Realiza scraping usando requests (HTTP clásico).
    
    Args:
        url: URL a scrapear
        
    Returns:
        Diccionario con resultado del scraping
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=(5, 20), allow_redirects=True)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        logger.warning("Timeout al acceder a: %s", url)
        return {"success": False, "text": None, "error": "TIMEOUT", "strategy": "requests"}
    except requests.exceptions.RequestException as e:
        logger.warning("Error de request: %s", e)
        return {"success": False, "text": None, "error": f"REQUEST_ERROR: {e}", "strategy": "requests"}
    
    html = response.text or ""
    
    # Verificar bloqueos
    if detect_bot_block(html):
        logger.info("Detectado bloqueo de bots")
        return {"success": False, "text": None, "error": "BOT_BLOCKED", "strategy": "requests"}
    
    if detect_js_rendering(html):
        logger.info("Contenido requiere JavaScript")
        return {"success": False, "text": None, "error": "JS_RENDERED", "strategy": "requests"}
    
    # Extraer contenido
    text = clean_html_content(html)
    
    # Si no hay contenido o no hay keywords, probablemente es una SPA
    if not text or not looks_like_job_offer(text):
        return {"success": False, "text": None, "error": "JS_RENDERED", "strategy": "requests"}
    
    logger.info("Contenido extraído exitosamente (%d caracteres)", len(text))
    return {"success": True, "text": text, "error": None, "strategy": "requests"}


def _scrape_with_browser(url: str) -> Dict[str, Any]:
    """
    Realiza scraping usando navegador headless (Playwright).
    
    Útil para páginas con contenido renderizado por JavaScript.
    Usa subprocess para evitar conflictos con el event loop de Streamlit.
    
    Args:
        url: URL a scrapear
        
    Returns:
        Diccionario con resultado del scraping
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.warning("Playwright no instalado - fallback no disponible")
        return {"success": False, "text": None, "error": "PLAYWRIGHT_NOT_INSTALLED", "strategy": "browser"}
    
    # Usar subprocess para evitar conflictos con asyncio/Streamlit
    import subprocess
    import sys
    import tempfile
    import os
    
    # Script mejorado con técnicas anti-detección de bots
    script = '''
import sys
import time
import random
from playwright.sync_api import sync_playwright

url = sys.argv[1]
output_file = sys.argv[2]

try:
    with sync_playwright() as p:
        # Lanzar navegador con args anti-detección
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-infobars",
                "--window-size=1920,1080",
                "--start-maximized"
            ]
        )
        
        # Crear contexto con configuración realista
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/121.0.0.0 Safari/537.36"
            ),
            locale="es-ES",
            timezone_id="Europe/Madrid",
            extra_http_headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Cache-Control": "max-age=0"
            }
        )
        
        page = context.new_page()
        
        # Evadir detección de webdriver
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['es-ES', 'es', 'en']});
            window.chrome = { runtime: {} };
        """)
        
        # Navegar con espera extendida
        page.goto(url, timeout=45000, wait_until="networkidle")
        
        # Simular comportamiento humano
        time.sleep(random.uniform(1.5, 3.0))
        
        # Scroll gradual para cargar contenido dinámico
        page.evaluate("window.scrollTo(0, document.body.scrollHeight / 3)")
        time.sleep(random.uniform(0.5, 1.0))
        page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
        time.sleep(random.uniform(0.5, 1.0))
        page.evaluate("window.scrollTo(0, 0)")
        time.sleep(random.uniform(0.3, 0.7))
        
        html = page.content()
        browser.close()
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    sys.exit(0)
except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr)
    sys.exit(1)
'''
    
    try:
        # Crear archivo temporal para el HTML
        fd, output_path = tempfile.mkstemp(suffix='.html')
        os.close(fd)
        
        # Crear script temporal
        fd_script, script_path = tempfile.mkstemp(suffix='.py')
        os.close(fd_script)
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script)
        
        # Ejecutar en subprocess con timeout extendido
        result = subprocess.run(
            [sys.executable, script_path, url, output_path],
            capture_output=True,
            text=True,
            timeout=90
        )
        
        # Limpiar script
        os.unlink(script_path)
        
        if result.returncode != 0:
            os.unlink(output_path)
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            logger.error("Error en subprocess Playwright: %s", error_msg)
            return {"success": False, "text": None, "error": f"BROWSER_ERROR: {error_msg}", "strategy": "browser"}
        
        # Leer HTML resultante
        with open(output_path, 'r', encoding='utf-8') as f:
            html = f.read()
        os.unlink(output_path)
        
        text = clean_html_content(html)
        
        if not text:
            return {"success": False, "text": None, "error": "NO_CONTENT", "strategy": "browser"}
        
        if not looks_like_job_offer(text):
            return {"success": False, "text": None, "error": "NOT_JOB_OFFER", "strategy": "browser"}
        
        logger.info("Contenido extraído con browser (%d caracteres)", len(text))
        return {"success": True, "text": text, "error": None, "strategy": "browser"}
    
    except subprocess.TimeoutExpired:
        logger.error("Timeout en subprocess Playwright")
        return {"success": False, "text": None, "error": "BROWSER_TIMEOUT", "strategy": "browser"}
    except (RuntimeError, OSError, Exception) as e:
        logger.error("Error en scraping con browser: %s", e)
        return {"success": False, "text": None, "error": f"BROWSER_ERROR: {e}", "strategy": "browser"}


# =============================================================================
# API PÚBLICA
# =============================================================================

def scrape_job_offer_url(
    url: str,
    enable_browser_fallback: bool = True
) -> Optional[str]:
    """
    Extrae el contenido de una oferta de empleo desde una URL.
    
    Implementa estrategia de fallback:
    1. Intenta con requests (HTTP clásico)
    2. Si falla por JS/contenido, intenta con navegador headless
    
    Args:
        url: URL de la oferta de empleo
        enable_browser_fallback: Habilitar fallback a Playwright
        
    Returns:
        Texto de la oferta o None si no se pudo extraer
    """
    logger.info("Iniciando scraping de: %s", url)
    
    # Primer intento con requests
    result = _scrape_with_requests(url)
    
    if result["success"]:
        return result["text"]
    
    # Fallback a navegador si corresponde (incluye BOT_BLOCKED)
    fallback_errors = {"JS_RENDERED", "NO_CONTENT", "NOT_JOB_OFFER", "BOT_BLOCKED"}
    if enable_browser_fallback and result["error"] in fallback_errors:
        logger.info("Intentando fallback con navegador headless (error: %s)", result["error"])
        result = _scrape_with_browser(url)
        
        if result["success"]:
            return result["text"]
    
    logger.warning("No se pudo extraer contenido: %s", result['error'])
    return None


def scrape_job_offer_url_detailed(
    url: str,
    enable_browser_fallback: bool = True
) -> Dict[str, Any]:
    """
    Versión detallada que retorna información completa del scraping.
    
    Args:
        url: URL de la oferta de empleo
        enable_browser_fallback: Habilitar fallback a Playwright
        
    Returns:
        Diccionario con: success, text, error, strategy
    """
    logger.info("Iniciando scraping detallado de: %s", url)
    
    result = _scrape_with_requests(url)
    
    if result["success"]:
        return result
    
    fallback_errors = {"JS_RENDERED", "NO_CONTENT", "NOT_JOB_OFFER", "BOT_BLOCKED"}
    if enable_browser_fallback and result["error"] in fallback_errors:
        logger.info("Intentando fallback con navegador headless (error: %s)", result["error"])
        return _scrape_with_browser(url)
    
    return result
