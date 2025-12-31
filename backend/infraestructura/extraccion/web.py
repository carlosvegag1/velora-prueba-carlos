"""
Extracción de ofertas de empleo desde URLs.
Scraping inteligente con detección de JS y fallback a Playwright.
"""

import logging
import re
from typing import Optional, Dict, Any, List

import requests

try:
    from bs4 import BeautifulSoup
    BS4_DISPONIBLE = True
except ImportError:
    BS4_DISPONIBLE = False

logger = logging.getLogger(__name__)


# Palabras clave para validar que es una oferta de empleo
PALABRAS_CLAVE_OFERTA: List[str] = [
    "responsabilidades", "requisitos", "experiencia", "ofrecemos", "qué buscamos", "perfil",
    "funciones", "misión", "rol", "puesto", "vacante", "candidato", "competencias",
    "habilidades", "formación", "titulación"
]

# Marcadores de contenido renderizado por JS
MARCADORES_JS: List[str] = [
    "enable javascript", "please enable javascript", "__NEXT_DATA__", "data-reactroot",
    "app-root", "ng-app", "smartrecruiters", "attrax", "workday", "greenhouse",
    "lever.co", "ashbyhq", "taleo", "successfactors", "icims", "jobvite", "breezy", "bamboohr"
]

# Marcadores de bloqueo de bots
MARCADORES_BLOQUEO_BOT: List[str] = [
    "captcha", "i'm not a robot", "are you a robot", "verify you are human",
    "prove you're human", "checking your browser", "please wait while we verify",
    "access denied", "403 forbidden", "blocked", "unusual traffic"
]

# Selectores CSS para contenido de ofertas
SELECTORES_CONTENIDO: List[str] = [
    ".job-description", ".job-details", ".vacancy-description", '[itemprop="description"]',
    '[data-testid="job-description"]', "article", "main", '[role="main"]',
    ".content", ".post-content", "section"
]


def parece_oferta_trabajo(texto: str) -> bool:
    if not texto:
        return False
    texto_lower = texto.lower()
    return sum(1 for kw in PALABRAS_CLAVE_OFERTA if kw in texto_lower) >= 2


def detectar_renderizado_js(html: str) -> bool:
    if not html:
        return False
    html_lower = html.lower()
    return any(marcador in html_lower for marcador in MARCADORES_JS)


def detectar_bloqueo_bot(html: str) -> bool:
    if not html:
        return False
    html_lower = html.lower()
    return any(marcador in html_lower for marcador in MARCADORES_BLOQUEO_BOT)


def limpiar_contenido_html(html: str) -> Optional[str]:
    """Extrae y limpia contenido textual relevante del HTML."""
    if not html:
        return None
    
    if not BS4_DISPONIBLE:
        texto = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
        texto = re.sub(r"<style[^>]*>.*?</style>", "", texto, flags=re.DOTALL | re.IGNORECASE)
        texto = re.sub(r"<[^>]+>", " ", texto)
        texto = re.sub(r"\s+", " ", texto)
        return texto.strip() or None

    soup = BeautifulSoup(html, "html.parser")
    mejor_contenido = None
    max_longitud = 0
    
    for selector in SELECTORES_CONTENIDO:
        for elemento in soup.select(selector):
            for etiqueta in elemento(["script", "style", "noscript", "iframe", "nav", "footer", "header"]):
                etiqueta.decompose()
            texto = elemento.get_text(separator="\n", strip=True)
            if len(texto) > max_longitud and len(texto) > 200:
                if parece_oferta_trabajo(texto):
                    mejor_contenido = texto
                    max_longitud = len(texto)
    
    if not mejor_contenido and soup.body:
        for etiqueta in soup.body(["script", "style", "noscript", "iframe", "nav", "footer", "header"]):
            etiqueta.decompose()
        mejor_contenido = soup.body.get_text(separator="\n", strip=True)
    
    if not mejor_contenido:
        return None
    
    lineas = [
        linea.strip() for linea in mejor_contenido.split("\n")
        if linea.strip() and not re.fullmatch(r"[-•–—=_*]+", linea.strip())
    ]
    return "\n".join(lineas) if lineas else None


def _scrape_con_requests(url: str) -> Dict[str, Any]:
    """Scraping con HTTP clásico."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=(5, 20), allow_redirects=True)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        logger.warning("Timeout: %s", url)
        return {"success": False, "text": None, "error": "TIMEOUT", "strategy": "requests"}
    except requests.exceptions.RequestException as e:
        logger.warning("Error request: %s", e)
        return {"success": False, "text": None, "error": f"REQUEST_ERROR: {e}", "strategy": "requests"}
    
    html = response.text or ""
    
    if detectar_bloqueo_bot(html):
        return {"success": False, "text": None, "error": "BOT_BLOCKED", "strategy": "requests"}
    
    if detectar_renderizado_js(html):
        return {"success": False, "text": None, "error": "JS_RENDERED", "strategy": "requests"}
    
    texto = limpiar_contenido_html(html)
    if not texto or not parece_oferta_trabajo(texto):
        return {"success": False, "text": None, "error": "JS_RENDERED", "strategy": "requests"}
    
    logger.info("Extraído con requests (%d chars)", len(texto))
    return {"success": True, "text": texto, "error": None, "strategy": "requests"}


def _scrape_con_navegador(url: str) -> Dict[str, Any]:
    """Scraping con Playwright headless."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.warning("Playwright no instalado")
        return {"success": False, "text": None, "error": "PLAYWRIGHT_NOT_INSTALLED", "strategy": "browser"}
    
    import subprocess
    import sys
    import tempfile
    import os
    
    script = '''
import sys
import time
import random
from playwright.sync_api import sync_playwright

url = sys.argv[1]
output_file = sys.argv[2]

try:
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--disable-dev-shm-usage",
                  "--no-sandbox", "--disable-setuid-sandbox", "--disable-infobars",
                  "--window-size=1920,1080", "--start-maximized"]
        )
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/121.0.0.0 Safari/537.36",
            locale="es-ES", timezone_id="Europe/Madrid",
            extra_http_headers={"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "es-ES,es;q=0.9,en;q=0.8", "Accept-Encoding": "gzip, deflate, br"}
        )
        page = context.new_page()
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            window.chrome = { runtime: {} };
        """)
        page.goto(url, timeout=30000, wait_until="domcontentloaded")
        time.sleep(random.uniform(0.3, 0.6))
        page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
        time.sleep(random.uniform(0.1, 0.3))
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
        fd, ruta_salida = tempfile.mkstemp(suffix='.html')
        os.close(fd)
        fd_script, ruta_script = tempfile.mkstemp(suffix='.py')
        os.close(fd_script)
        with open(ruta_script, 'w', encoding='utf-8') as f:
            f.write(script)
        
        resultado = subprocess.run([sys.executable, ruta_script, url, ruta_salida],
                                   capture_output=True, text=True, timeout=60)
        os.unlink(ruta_script)
        
        if resultado.returncode != 0:
            os.unlink(ruta_salida)
            error_msg = resultado.stderr.strip() if resultado.stderr else "Error desconocido"
            logger.error("Error Playwright: %s", error_msg)
            return {"success": False, "text": None, "error": f"BROWSER_ERROR: {error_msg}", "strategy": "browser"}
        
        with open(ruta_salida, 'r', encoding='utf-8') as f:
            html = f.read()
        os.unlink(ruta_salida)
        
        texto = limpiar_contenido_html(html)
        if not texto:
            return {"success": False, "text": None, "error": "NO_CONTENT", "strategy": "browser"}
        if not parece_oferta_trabajo(texto):
            return {"success": False, "text": None, "error": "NOT_JOB_OFFER", "strategy": "browser"}
        
        logger.info("Extraído con browser (%d chars)", len(texto))
        return {"success": True, "text": texto, "error": None, "strategy": "browser"}
    
    except subprocess.TimeoutExpired:
        logger.error("Timeout Playwright")
        return {"success": False, "text": None, "error": "BROWSER_TIMEOUT", "strategy": "browser"}
    except Exception as e:
        logger.error("Error browser: %s", e)
        return {"success": False, "text": None, "error": f"BROWSER_ERROR: {e}", "strategy": "browser"}


def extraer_oferta_web(url: str, habilitar_fallback_navegador: bool = True) -> Optional[str]:
    """Extrae contenido de oferta desde URL. Usa Playwright como fallback si falla requests."""
    logger.info("Scraping: %s", url)
    
    resultado = _scrape_con_requests(url)
    if resultado["success"]:
        return resultado["text"]
    
    errores_fallback = {"JS_RENDERED", "NO_CONTENT", "NOT_JOB_OFFER", "BOT_BLOCKED"}
    if habilitar_fallback_navegador and resultado["error"] in errores_fallback:
        logger.info("Fallback browser (error: %s)", resultado["error"])
        resultado = _scrape_con_navegador(url)
        if resultado["success"]:
            return resultado["text"]
    
    logger.warning("No se pudo extraer: %s", resultado['error'])
    return None


scrape_job_offer_url = extraer_oferta_web


def extraer_oferta_web_detallado(url: str, habilitar_fallback_navegador: bool = True) -> Dict[str, Any]:
    """Versión detallada que retorna información completa del scraping."""
    logger.info("Scraping detallado: %s", url)
    
    resultado = _scrape_con_requests(url)
    if resultado["success"]:
        return resultado
    
    errores_fallback = {"JS_RENDERED", "NO_CONTENT", "NOT_JOB_OFFER", "BOT_BLOCKED"}
    if habilitar_fallback_navegador and resultado["error"] in errores_fallback:
        return _scrape_con_navegador(url)
    
    return resultado


scrape_job_offer_url_detailed = extraer_oferta_web_detallado
