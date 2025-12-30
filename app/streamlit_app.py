"""
Velora - Sistema de Evaluación de Candidatos
Versión 1.2 - Fixed UI Visibility

Prueba técnica desarrollada por Carlos Vega
para postularse a Ingeniero de IA Generativa en Velora
"""

import streamlit as st
import sys
import logging
from pathlib import Path
import os

# Rutas de logos de Velora (imágenes PNG)
ASSETS_DIR = Path(__file__).resolve().parent / "assets"
VELORA_LOGO_LARGE = ASSETS_DIR / "Velora_logotipo_grande_Color.png"
VELORA_LOGO_SMALL = ASSETS_DIR / "Velora_logotipo_pequeño_Color.png"
VELORA_LOGO_APPLE_ICON = ASSETS_DIR / "Velora_logotipo_apple_icon.png"

# =============================================================================
# CONFIGURACIÓN DE PÁGINA (PRIMERA INSTRUCCIÓN OBLIGATORIA)
# =============================================================================
st.set_page_config(
    page_title="Velora | Evaluador de Candidatos",
    page_icon=str(VELORA_LOGO_APPLE_ICON),
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configurar logging
logger = logging.getLogger(__name__)

# Agregar el directorio raíz al path para imports
# Usamos resolve() para evitar errores con rutas relativas
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Importación segura de módulos
try:
    from src.evaluator import (
        CandidateEvaluator,
        LLMFactory,
        EvaluationResult,
        extract_text_from_pdf,
        UserMemory,
        scrape_job_offer_url,
        HistoryChatbot,
        create_enriched_evaluation,
    )
    from src.evaluator.llm.embeddings_factory import EmbeddingFactory
    from src.evaluator.core.analyzer import Phase1Analyzer
    from src.evaluator.models import InterviewResponse
except ImportError as e:
    st.error(f"Error importando módulos: {e}. Asegúrate de ejecutar desde la raíz del proyecto.")
    st.stop()

# =============================================================================
# SISTEMA DE DISEÑO CORPORATIVO VELORA
# =============================================================================

# Paleta de colores Velora
VELORA_PRIMARY = "#00B4D8"      # Azul turquesa principal
VELORA_SECONDARY = "#00CED1"    # Turquesa secundario
VELORA_DARK = "#3D4043"         # Gris oscuro para texto
VELORA_GRAY = "#6B7280"         # Gris medio
VELORA_LIGHT_GRAY = "#F3F4F6"   # Gris claro para fondos
VELORA_WHITE = "#FFFFFF"
VELORA_SUCCESS = "#10B981"      # Verde para éxito
VELORA_ERROR = "#EF4444"        # Rojo para errores
VELORA_WARNING = "#F59E0B"      # Amarillo para advertencias

# Estilos CSS corporativos - v1.0 Production Ready
st.markdown(f"""
<style>
    /* ============================================
       BASE TIPOGRÁFICA - VELORA DESIGN SYSTEM v1.0
       ============================================ */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Fuente global */
    html, body, .stApp {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }}
    
    /* Ocultar branding Streamlit */
    #MainMenu, footer, .stDeployButton {{
        display: none !important;
    }}
    
    header[data-testid="stHeader"] {{
        background: transparent !important;
    }}
    
    /* Fix iconos Material - ocultar texto fallback */
    [data-testid="collapsedControl"],
    [data-testid="stExpanderToggleIcon"] {{
        font-size: 0 !important;
    }}
    [data-testid="collapsedControl"] svg,
    [data-testid="stExpanderToggleIcon"] svg {{
        width: 20px !important;
        height: 20px !important;
    }}

    /* ============================================
       CONTENEDOR PRINCIPAL - Máxima elevación y centrado
       ============================================ */
    .main .block-container {{
        padding-top: 0.5rem !important;
        padding-bottom: 2rem;
        max-width: 1100px;
        margin: 0 auto;
    }}
    
    /* Alineación global centrada */
    .main .block-container .stMarkdown,
    .main .block-container h1,
    .main .block-container h2,
    .main .block-container h3 {{
        text-align: center;
    }}
    
    /* ============================================
       HEADER CORPORATIVO - Elevado y amplificado
       ============================================ */
    .velora-header {{
        background: linear-gradient(135deg, {VELORA_WHITE} 0%, rgba(0, 180, 216, 0.04) 100%);
        border-bottom: 3px solid;
        border-image: linear-gradient(90deg, {VELORA_PRIMARY}, {VELORA_SECONDARY}) 1;
        padding: 0.75rem 2rem 1.5rem 2rem;
        margin: -0.5rem -1rem 1.5rem -1rem;
        text-align: center;
        display: flex;
        flex-direction: column;
        align-items: center;
    }}
    
    .velora-subtitle {{
        font-size: 1.375rem;
        font-weight: 700;
        color: {VELORA_PRIMARY};
        margin: 0.75rem auto 0.5rem auto;
        line-height: 1.4;
        max-width: 850px;
        text-align: center;
    }}
    
    .velora-description {{
        font-size: 1.0625rem;
        font-weight: 400;
        color: {VELORA_DARK};
        margin: 0 auto;
        line-height: 1.7;
        max-width: 900px;
        text-align: center;
    }}
    
    /* ============================================
       SIDEBAR - Panel lateral con presencia visual
       ============================================ */
    section[data-testid="stSidebar"] {{
        background: linear-gradient(180deg, #FAFBFC 0%, rgba(0, 180, 216, 0.04) 100%) !important;
        border-right: 4px solid;
        border-image: linear-gradient(180deg, {VELORA_PRIMARY}, {VELORA_SECONDARY}) 1 !important;
        width: 280px !important;
        min-width: 280px !important;
        padding-top: 0.5rem !important;
    }}
    
    section[data-testid="stSidebar"] > div {{
        padding: 0.25rem 1rem !important;
    }}
    
    section[data-testid="stSidebar"] .stMarkdown {{
        text-align: center;
    }}
    
    section[data-testid="stSidebar"] .stTextInput,
    section[data-testid="stSidebar"] .stSelectbox {{
        max-width: 240px;
        margin: 0 auto;
    }}
    
    .sidebar-title {{
        font-size: 0.9375rem;
        font-weight: 700;
        color: {VELORA_PRIMARY};
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin: 1rem 0 0.75rem 0;
        padding-bottom: 0.75rem;
        border-bottom: 2px solid rgba(0, 180, 216, 0.25);
        text-align: center;
    }}
    
    /* ============================================
       PESTAÑAS - Más grandes y azul corporativo
       ============================================ */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 12px;
        background: transparent;
        border-bottom: 2px solid {VELORA_LIGHT_GRAY};
        padding: 0;
        margin-bottom: 1.5rem;
        justify-content: center;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        background: transparent;
        border-radius: 10px 10px 0 0;
        padding: 1.25rem 2.5rem;
        font-weight: 600;
        font-size: 1.125rem;
        color: {VELORA_GRAY};
        border: none;
        transition: all 0.2s ease;
    }}
    
    .stTabs [data-baseweb="tab"]:hover {{
        background: rgba(0, 180, 216, 0.08);
        color: {VELORA_PRIMARY};
    }}
    
    .stTabs [aria-selected="true"] {{
        background: linear-gradient(180deg, rgba(0, 180, 216, 0.12) 0%, transparent 100%);
        color: {VELORA_PRIMARY} !important;
        border-bottom: 4px solid {VELORA_PRIMARY} !important;
        margin-bottom: -2px;
    }}
    
    /* ============================================
       CARDS Y CONTENEDORES
       ============================================ */
    .velora-card {{
        background: {VELORA_WHITE};
        border: 1px solid #E5E7EB;
        border-top: 3px solid {VELORA_PRIMARY};
        border-radius: 8px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0, 180, 216, 0.08);
        transition: box-shadow 0.2s ease;
    }}
    
    .velora-card:hover {{
        box-shadow: 0 4px 16px rgba(0, 180, 216, 0.12);
    }}
    
    .velora-card-header {{
        font-size: 1rem;
        font-weight: 600;
        color: {VELORA_PRIMARY};
        margin-bottom: 1rem;
        padding-bottom: 0.75rem;
        border-bottom: 1px solid rgba(0, 180, 216, 0.2);
    }}
    
    /* ============================================
       MÉTRICAS REFINADAS
       ============================================ */
    [data-testid="stMetric"] {{
        background: linear-gradient(135deg, {VELORA_WHITE} 0%, rgba(0, 180, 216, 0.03) 100%);
        border-radius: 8px;
        padding: 1rem;
        border: 1px solid rgba(0, 180, 216, 0.1);
    }}
    
    [data-testid="stMetricValue"] {{
        font-size: 1.75rem;
        font-weight: 700;
        color: {VELORA_PRIMARY};
    }}
    
    [data-testid="stMetricLabel"] {{
        font-size: 0.75rem;
        font-weight: 600;
        color: {VELORA_GRAY};
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}
    
    [data-testid="stMetricDelta"] {{
        font-size: 0.85rem;
        font-weight: 500;
    }}
    
    /* ============================================
       BOTONES CORPORATIVOS - Más grandes
       ============================================ */
    .stButton > button {{
        background: linear-gradient(135deg, {VELORA_PRIMARY} 0%, {VELORA_SECONDARY} 100%);
        color: {VELORA_WHITE};
        border: none;
        border-radius: 8px;
        font-weight: 600;
        font-size: 1.0625rem;
        padding: 0.875rem 2rem;
        transition: all 0.2s ease;
    }}
    
    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(0, 180, 216, 0.35);
    }}
    
    .stButton > button:disabled {{
        background: #D1D5DB;
        color: #9CA3AF;
        cursor: not-allowed;
        transform: none;
        box-shadow: none;
    }}
    
    /* Botón secundario */
    .stButton > button[kind="secondary"] {{
        background: {VELORA_WHITE};
        color: {VELORA_DARK};
        border: 2px solid #E5E7EB;
        font-size: 1rem;
    }}
    
    /* ============================================
       INPUTS PROFESIONALES
       ============================================ */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > div {{
        border: 1px solid #E5E7EB;
        border-radius: 6px;
        font-size: 0.9rem;
        transition: border-color 0.2s ease, box-shadow 0.2s ease;
    }}
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {{
        border-color: {VELORA_PRIMARY};
        box-shadow: 0 0 0 3px rgba(0, 180, 216, 0.1);
    }}
    
    /* ============================================
       EXPANDERS REFINADOS
       ============================================ */
    .streamlit-expanderHeader {{
        font-size: 0.95rem;
        font-weight: 500;
        color: {VELORA_DARK};
        background: {VELORA_LIGHT_GRAY};
        border-radius: 6px;
    }}
    
    .streamlit-expanderContent {{
        border: 1px solid #E5E7EB;
        border-top: none;
        border-radius: 0 0 6px 6px;
    }}
    
    /* Ocultar texto fallback de iconos en expanders */
    [data-testid="stExpander"] [data-testid="stExpanderToggleIcon"],
    [data-testid="stExpander"] summary > div:first-child > span,
    .streamlit-expanderHeader > div:first-child {{
        font-size: 0 !important;
        line-height: 0 !important;
        width: 24px;
        height: 24px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
    }}
    
    /* Mostrar SVG de los expanders */
    [data-testid="stExpander"] svg,
    .streamlit-expanderHeader svg {{
        width: 20px !important;
        height: 20px !important;
        font-size: 20px !important;
    }}
    
    /* ============================================
       MENSAJES DE ESTADO
       ============================================ */
    .stAlert {{
        border-radius: 8px;
        border: none;
        font-size: 0.9rem;
        padding: 1rem 1.25rem;
    }}
    
    /* Success - Con toque corporativo */
    div[data-baseweb="notification"][kind="positive"],
    .stSuccess {{
        background: linear-gradient(90deg, rgba(16, 185, 129, 0.1) 0%, rgba(0, 180, 216, 0.05) 100%);
        border-left: 4px solid {VELORA_SUCCESS};
    }}
    
    /* Error */
    div[data-baseweb="notification"][kind="negative"],
    .stError {{
        background: linear-gradient(90deg, rgba(239, 68, 68, 0.1) 0%, rgba(239, 68, 68, 0.05) 100%);
        border-left: 4px solid {VELORA_ERROR};
    }}
    
    /* Warning */
    div[data-baseweb="notification"][kind="warning"],
    .stWarning {{
        background: linear-gradient(90deg, rgba(245, 158, 11, 0.1) 0%, rgba(245, 158, 11, 0.05) 100%);
        border-left: 4px solid {VELORA_WARNING};
    }}
    
    /* Info - Color corporativo */
    .stInfo {{
        background: linear-gradient(90deg, rgba(0, 180, 216, 0.1) 0%, rgba(0, 206, 209, 0.05) 100%);
        border-left: 4px solid {VELORA_PRIMARY};
    }}
    
    /* ============================================
       CHAT CONVERSACIONAL
       ============================================ */
    .chat-container {{
        background: {VELORA_LIGHT_GRAY};
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
    }}
    
    .chat-message-system {{
        background: {VELORA_WHITE};
        border-radius: 12px;
        padding: 1rem 1.25rem;
        margin: 0.75rem 0;
        border-left: 3px solid {VELORA_PRIMARY};
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }}
    
    .chat-message-user {{
        background: {VELORA_WHITE};
        border-radius: 12px;
        padding: 1rem 1.25rem;
        margin: 0.75rem 0;
        border-left: 3px solid {VELORA_SUCCESS};
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }}
    
    .chat-progress {{
        background: linear-gradient(135deg, {VELORA_PRIMARY}15, {VELORA_SECONDARY}15);
        border-radius: 8px;
        padding: 0.75rem 1rem;
        margin-bottom: 1rem;
        font-weight: 500;
        font-size: 0.9rem;
        color: {VELORA_DARK};
        border: 1px solid {VELORA_PRIMARY}30;
    }}
    
    /* ============================================
       INDICADORES DE REQUISITOS
       ============================================ */
    .req-obligatory {{
        color: {VELORA_ERROR};
        font-weight: 600;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }}
    
    .req-optional {{
        color: {VELORA_WARNING};
        font-weight: 600;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }}
    
    .confidence-high {{
        color: {VELORA_SUCCESS};
        font-weight: 500;
    }}
    
    .confidence-medium {{
        color: {VELORA_WARNING};
        font-weight: 500;
    }}
    
    .confidence-low {{
        color: {VELORA_ERROR};
        font-weight: 500;
    }}
    
    /* ============================================
       BARRA DE PROGRESO
       ============================================ */
    .stProgress > div > div > div {{
        background: linear-gradient(90deg, {VELORA_PRIMARY}, {VELORA_SECONDARY});
        border-radius: 4px;
    }}
    
    .stProgress > div > div {{
        background: #E5E7EB;
        border-radius: 4px;
    }}
    
    /* ============================================
       TABLA PROFESIONAL
       ============================================ */
    .stDataFrame {{
        border: 1px solid #E5E7EB;
        border-radius: 8px;
        overflow: hidden;
    }}
    
    /* ============================================
       DIVIDERS
       ============================================ */
    hr {{
        border: none;
        border-top: 1px solid #E5E7EB;
        margin: 1.5rem 0;
    }}
    
    /* ============================================
       SPINNER
       ============================================ */
    .stSpinner > div {{
        border-top-color: {VELORA_PRIMARY} !important;
    }}
    
    /* ============================================
       WARNING BOX - Sombreado amarillo profesional
       ============================================ */
    .warning-anthropic,
    .warning-box {{
        background: linear-gradient(135deg, rgba(255, 193, 7, 0.15) 0%, rgba(255, 235, 59, 0.08) 100%);
        border-left: 4px solid {VELORA_WARNING};
        border-radius: 6px;
        padding: 1rem 1.25rem;
        margin: 0.75rem 0;
        font-size: 0.9rem;
        color: #8B6914;
    }}
    
    .warning-box strong {{
        color: #7B5E00;
    }}
    
    /* File uploader - Localización a español */
    [data-testid="stFileUploader"] label {{
        text-align: center;
    }}
    
    /* Ocultar textos en inglés del file uploader */
    [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"] p {{
        font-size: 0 !important;
    }}
    
    [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"] p::after {{
        content: "Arrastra y suelta el archivo aquí";
        font-size: 0.9rem !important;
        color: {VELORA_GRAY};
    }}
    
    [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"] small {{
        font-size: 0 !important;
    }}
    
    [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"] small::after {{
        content: "Límite de 200 MB por archivo";
        font-size: 0.75rem !important;
        color: {VELORA_GRAY};
    }}
    
    [data-testid="stFileUploader"] button {{
        font-size: 0 !important;
    }}
    
    [data-testid="stFileUploader"] button::after {{
        content: "Examinar archivos";
        font-size: 0.875rem !important;
    }}
    
    /* ============================================
       RESPONSIVIDAD
       ============================================ */
    
    @media (max-width: 768px) {{
        .velora-header {{
            padding: 0.75rem !important;
        }}
        
        .velora-subtitle {{
            font-size: 1rem !important;
        }}
        
        .velora-description {{
            font-size: 0.85rem !important;
        }}
    }}
    
    /* ============================================
       FOCUS Y HOVER
       ============================================ */
    
    button:focus-visible,
    input:focus-visible {{
        outline: 2px solid {VELORA_PRIMARY};
        outline-offset: 2px;
    }}
    
    /* ============================================
       SISTEMA DE ESTADOS PROFESIONAL - Tamaños consistentes
       ============================================ */
    .status-approved {{
        background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%);
        color: #2E7D32;
        padding: 0.5rem 1.25rem;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.9375rem;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        text-transform: uppercase;
        letter-spacing: 0.03em;
        min-width: 100px;
        line-height: 1.2;
        vertical-align: middle;
    }}
    
    .status-rejected {{
        background: linear-gradient(135deg, #FFEBEE 0%, #FFCDD2 100%);
        color: #C62828;
        padding: 0.5rem 1.25rem;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.9375rem;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        text-transform: uppercase;
        letter-spacing: 0.03em;
        min-width: 100px;
        line-height: 1.2;
        vertical-align: middle;
    }}
    
    .status-pending {{
        background: linear-gradient(135deg, #FFF9C4 0%, #FFF59D 100%);
        color: #F57F17;
        padding: 0.5rem 1.25rem;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.9375rem;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        text-transform: uppercase;
        letter-spacing: 0.03em;
        min-width: 100px;
        line-height: 1.2;
        vertical-align: middle;
    }}
    
    .status-phase1 {{
        background: linear-gradient(135deg, rgba(0, 180, 216, 0.1) 0%, rgba(0, 206, 209, 0.15) 100%);
        color: {VELORA_PRIMARY};
        padding: 0.5rem 1.25rem;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.9375rem;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        text-transform: uppercase;
        letter-spacing: 0.03em;
        min-width: 100px;
        line-height: 1.2;
        vertical-align: middle;
    }}
    
    /* Contenedor para estado y fase alineados */
    .status-phase-container {{
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 1rem;
        margin: 0.5rem 0;
    }}
    
    /* ============================================
       SECCIONES DESTACADAS - Jerarquía visual
       ============================================ */
    .section-card {{
        background: {VELORA_WHITE};
        border: 1px solid rgba(0, 180, 216, 0.1);
        border-left: 4px solid {VELORA_PRIMARY};
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0, 180, 216, 0.06);
    }}
    
    .section-header {{
        font-size: 1.125rem;
        font-weight: 700;
        color: {VELORA_DARK};
        margin-bottom: 1rem;
        padding-bottom: 0.75rem;
        border-bottom: 2px solid;
        border-image: linear-gradient(90deg, {VELORA_PRIMARY}, transparent) 1;
    }}
    
    .section-highlight {{
        background: linear-gradient(135deg, rgba(0, 180, 216, 0.04) 0%, rgba(0, 206, 209, 0.02) 100%);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1.5rem 0;
        border: 1px solid rgba(0, 180, 216, 0.1);
    }}
    
    /* Títulos de sección amplificados */
    .stMarkdown h3 {{
        font-size: 1.25rem !important;
        font-weight: 700 !important;
        color: {VELORA_DARK} !important;
        margin-top: 2rem !important;
        margin-bottom: 1rem !important;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid rgba(0, 180, 216, 0.15);
    }}
    
    /* ============================================
       HISTORIAL - Expanders con fondo de color en título
       ============================================ */
    
    /* Variables CSS para colores de historial */
    :root {{
        --history-approved-bg: linear-gradient(90deg, rgba(76, 175, 80, 0.15) 0%, rgba(76, 175, 80, 0.08) 100%);
        --history-approved-border: #4CAF50;
        --history-rejected-bg: linear-gradient(90deg, rgba(244, 67, 54, 0.15) 0%, rgba(244, 67, 54, 0.08) 100%);
        --history-rejected-border: #EF5350;
        --history-phase1-bg: linear-gradient(90deg, rgba(0, 180, 216, 0.12) 0%, rgba(0, 180, 216, 0.05) 100%);
        --history-phase1-border: {VELORA_PRIMARY};
    }}
    
    /* Estilo base para expanders del historial */
    [data-testid="stExpander"] details {{
        border-radius: 10px !important;
        margin-bottom: 0.75rem !important;
        overflow: hidden;
    }}
    
    /* Header del expander más grande y con padding */
    [data-testid="stExpander"] summary {{
        padding: 1rem 1.25rem !important;
        font-size: 1rem !important;
        font-weight: 500 !important;
    }}
    
    /* Aprobado - Fondo verde en el título */
    .expander-approved {{
        background: linear-gradient(90deg, rgba(76, 175, 80, 0.18) 0%, rgba(76, 175, 80, 0.08) 100%) !important;
        border-left: 5px solid #4CAF50 !important;
        border-radius: 10px !important;
        margin-bottom: 0.75rem;
    }}
    
    /* Rechazado - Fondo rojo en el título */
    .expander-rejected {{
        background: linear-gradient(90deg, rgba(244, 67, 54, 0.18) 0%, rgba(244, 67, 54, 0.08) 100%) !important;
        border-left: 5px solid #EF5350 !important;
        border-radius: 10px !important;
        margin-bottom: 0.75rem;
    }}
    
    /* Solo Fase 1 - Fondo azul en el título */
    .expander-phase1 {{
        background: linear-gradient(90deg, rgba(0, 180, 216, 0.15) 0%, rgba(0, 180, 216, 0.06) 100%) !important;
        border-left: 5px solid {VELORA_PRIMARY} !important;
        border-radius: 10px !important;
        margin-bottom: 0.75rem;
    }}
    
    .eval-card:hover {{
        border-left-color: {VELORA_PRIMARY};
        box-shadow: 0 4px 12px rgba(0, 180, 216, 0.1);
    }}
    
    .eval-card-approved {{
        border-left-color: {VELORA_SUCCESS};
    }}
    
    .eval-card-rejected {{
        border-left-color: {VELORA_ERROR};
    }}
    
</style>
""", unsafe_allow_html=True)


# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

def load_environment_variables():
    """Carga variables de entorno desde .env si existe"""
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    key, value = line.strip().split("=", 1)
                    os.environ[key] = value


def format_requirement_type(req_type: str) -> str:
    """Formatea el tipo de requisito sin emoji"""
    if req_type == "obligatory":
        return '<span class="req-obligatory">OBLIGATORIO</span>'
    return '<span class="req-optional">OPCIONAL</span>'


def format_requirement_type_text(req_type: str) -> str:
    """Formatea el tipo de requisito como texto plano"""
    if req_type == "obligatory":
        return "OBLIGATORIO"
    return "OPCIONAL"


def format_confidence_badge(confidence: str) -> str:
    """Formatea el nivel de confianza como badge profesional"""
    badges = {
        "high": '<span class="confidence-high">Alta</span>',
        "medium": '<span class="confidence-medium">Media</span>',
        "low": '<span class="confidence-low">Baja</span>'
    }
    return badges.get(confidence, badges["medium"])


def format_confidence_text(confidence: str) -> str:
    """Formatea el nivel de confianza como texto"""
    texts = {
        "high": "Alta",
        "medium": "Media",
        "low": "Baja"
    }
    return texts.get(confidence, "Media")


def get_confidence_color(confidence: str) -> str:
    """Retorna el color CSS para el nivel de confianza"""
    colors = {
        "high": VELORA_SUCCESS,
        "medium": VELORA_WARNING,
        "low": VELORA_ERROR
    }
    return colors.get(confidence, VELORA_WARNING)


def render_velora_header():
    """Renderiza el header corporativo de Velora - Centrado perfecto"""
    # Contenedor del header con todo centrado via CSS
    st.markdown('<div class="velora-header">', unsafe_allow_html=True)
    
    # Logo centrado usando contenedor flex
    if VELORA_LOGO_LARGE.exists():
        import base64
        with open(str(VELORA_LOGO_LARGE), "rb") as f:
            logo_data = base64.b64encode(f.read()).decode()
        st.markdown(
            f'<img src="data:image/png;base64,{logo_data}" style="width:300px;margin:0 auto;display:block;">',
            unsafe_allow_html=True
        )
    else:
        st.markdown('<h1 style="text-align:center;color:#00B4D8;">VELORA</h1>', unsafe_allow_html=True)
    
    st.markdown("""
        <p class="velora-subtitle">
            Prueba técnica desarrollada por Carlos Vega para postularse a Ingeniero de IA Generativa en Velora
        </p>
        <p class="velora-description">
            Durante el desarrollo de este sistema he intentado superar los requisitos de la prueba y, simultáneamente, 
            demostrar competencias adicionales en Ingeniería de IA. Integré tecnologías como LangGraph, 
            hiperparametrización, RAG y LangSmith como extensiones coherentes para aportar valor, manteniendo 
            siempre el foco en los objetivos fundamentales de la prueba.
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar_logo():
    """Renderiza el logo reducido en el sidebar - Centrado perfecto"""
    if VELORA_LOGO_SMALL.exists():
        import base64
        with open(str(VELORA_LOGO_SMALL), "rb") as f:
            logo_data = base64.b64encode(f.read()).decode()
        st.markdown(
            f'<div style="text-align:center;padding:1rem 0 1.5rem 0;">'
            f'<img src="data:image/png;base64,{logo_data}" style="width:150px;margin:0 auto;">'
            f'</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown('<div style="text-align:center;padding:1rem;"><strong style="color:#00B4D8;font-size:2rem;">V</strong></div>', unsafe_allow_html=True)


def analyze_user_history(memory: UserMemory, user_id: str, query: str) -> str:
    """Analiza el historial del usuario y responde a consultas."""
    evaluations = memory.get_evaluations(user_id)
    if not evaluations:
        return "No tienes evaluaciones en tu historial."
    
    query_lower = query.lower()
    
    if "última" in query_lower or "último" in query_lower or "reciente" in query_lower:
        latest = memory.get_latest_evaluation(user_id)
        if latest:
            status = "DESCARTADO" if latest.get('discarded') else "APROBADO"
            date_str = latest.get('timestamp', 'N/A')
            if date_str and len(date_str) >= 10:
                date_str = date_str[:10]
            
            return f"""
**Última Evaluación:**
- **Puntuación:** {latest.get('score', 0):.1f}%
- **Estado:** {status}
- **Fecha:** {date_str}
- **Proveedor:** {latest.get('provider', 'N/A')}
- **Modelo:** {latest.get('model', 'N/A')}
"""
    
    if "rechazado" in query_lower or "descartado" in query_lower:
        rejected = memory.get_rejected_evaluations(user_id)
        if rejected:
            response = f"Has sido rechazado en {len(rejected)} evaluación(es).\n\n"
            for i, eval_data in enumerate(rejected[:3], 1):
                date_str = eval_data.get('timestamp', 'N/A')
                if date_str and len(date_str) >= 10:
                    date_str = date_str[:10]
                
                response += f"**Rechazo #{i}:**\n"
                response += f"- Puntuación: {eval_data.get('score', 0):.1f}%\n"
                response += f"- Fecha: {date_str}\n"
                eval_result = eval_data.get('evaluation_result', {})
                unfulfilled = eval_result.get('final_unfulfilled_requirements', [])
                if unfulfilled:
                    response += f"- Requisitos no cumplidos: {len(unfulfilled)}\n"
                response += "\n"
            return response
        return "No has sido rechazado en ninguna evaluación."
    
    if "promedio" in query_lower or "media" in query_lower:
        avg_score = sum(e.get("score", 0) for e in evaluations) / len(evaluations)
        return f"Tu puntuación promedio es **{avg_score:.1f}%** en {len(evaluations)} evaluación(es)."
    
    if "mejor" in query_lower or "mayor" in query_lower:
        best = max(evaluations, key=lambda x: x.get("score", 0))
        status = "DESCARTADO" if best.get('discarded') else "APROBADO"
        date_str = best.get('timestamp', 'N/A')
        if date_str and len(date_str) >= 10:
            date_str = date_str[:10]
        
        return f"""
**Tu mejor evaluación:**
- **Puntuación:** {best.get('score', 0):.1f}%
- **Fecha:** {date_str}
- **Estado:** {status}
"""
    
    latest = memory.get_latest_evaluation(user_id)
    avg = sum(e.get("score", 0) for e in evaluations) / len(evaluations)
    rejected_count = sum(1 for e in evaluations if e.get("discarded", False))
    
    return f"""
He analizado tu historial con {len(evaluations)} evaluación(es).

**Resumen:**
- Puntuación promedio: {avg:.1f}%
- Evaluaciones rechazadas: {rejected_count}
- Última evaluación: {latest.get('score', 0) if latest else 'N/A'}%

Puedes preguntar sobre:
- Tu última evaluación
- Por qué fuiste rechazado
- Tu puntuación promedio
- Tu mejor evaluación
"""


def display_phase1_results(phase1_result):
    """Muestra los resultados de la Fase 1 con diseño profesional"""
    st.markdown("### Resultados del Análisis Inicial")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Puntuación Inicial",
            f"{phase1_result.score:.1f}%"
        )
    
    with col2:
        status = "DESCARTADO" if phase1_result.discarded else "EN PROCESO"
        st.metric("Estado", status)
    
    with col3:
        total = len(phase1_result.fulfilled_requirements) + len(phase1_result.unfulfilled_requirements)
        st.metric(
            "Requisitos Cumplidos",
            f"{len(phase1_result.fulfilled_requirements)}/{total}"
        )
    
    # Requisitos cumplidos
    if phase1_result.fulfilled_requirements:
        with st.expander(f"Requisitos Cumplidos ({len(phase1_result.fulfilled_requirements)})", expanded=True):
            for req in phase1_result.fulfilled_requirements:
                confidence = getattr(req, 'confidence', None)
                if hasattr(confidence, 'value'):
                    confidence_val = confidence.value
                else:
                    confidence_val = str(confidence) if confidence else "medium"
                
                confidence_color = get_confidence_color(confidence_val)
                
                col_req, col_conf = st.columns([4, 1])
                with col_req:
                    st.markdown(f"**{req.description}**")
                with col_conf:
                    st.markdown(
                        f"<span style='color:{confidence_color};font-size:0.85rem;'>{format_confidence_text(confidence_val)}</span>", 
                        unsafe_allow_html=True
                    )
                
                if req.evidence:
                    st.caption(f"Evidencia: {req.evidence[:200]}...")
                
                reasoning = getattr(req, 'reasoning', None)
                if reasoning:
                    st.caption(f"Razonamiento: {reasoning}")
                
                st.markdown("---")
    
    # Requisitos no cumplidos
    if phase1_result.unfulfilled_requirements:
        with st.expander(f"Requisitos No Cumplidos ({len(phase1_result.unfulfilled_requirements)})"):
            for req in phase1_result.unfulfilled_requirements:
                req_type_val = req.type.value if hasattr(req.type, 'value') else str(req.type)
                tipo_text = format_requirement_type_text(req_type_val)
                
                confidence = getattr(req, 'confidence', None)
                if hasattr(confidence, 'value'):
                    confidence_val = confidence.value
                else:
                    confidence_val = str(confidence) if confidence else "medium"
                
                confidence_color = get_confidence_color(confidence_val)
                
                col_req, col_conf = st.columns([4, 1])
                with col_req:
                    color = VELORA_ERROR if req_type_val == "obligatory" else VELORA_WARNING
                    st.markdown(
                        f"<span style='color:{color};font-size:0.75rem;font-weight:600;'>[{tipo_text}]</span> **{req.description}**", 
                        unsafe_allow_html=True
                    )
                with col_conf:
                    st.markdown(
                        f"<span style='color:{confidence_color};font-size:0.85rem;'>{format_confidence_text(confidence_val)}</span>", 
                        unsafe_allow_html=True
                    )
                
                reasoning = getattr(req, 'reasoning', None)
                if reasoning:
                    st.caption(f"Razonamiento: {reasoning}")
                
                st.markdown("---")


def display_interview_responses(responses: list):
    """Muestra las respuestas de la entrevista con diseño profesional"""
    if responses:
        st.markdown("### Entrevista Realizada")
        
        for i, resp in enumerate(responses, 1):
            with st.container():
                st.markdown(f"""
                <div class="chat-message-system">
                    <strong>Pregunta {i}:</strong> {resp.question}<br>
                    <small style="color:{VELORA_GRAY};">Requisito: {resp.requirement_description}</small>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div class="chat-message-user">
                    <strong>Respuesta:</strong> {resp.answer}
                </div>
                """, unsafe_allow_html=True)


def display_final_results(result: EvaluationResult):
    """Muestra los resultados finales con diseño profesional"""
    st.markdown("### Resultado Final de la Evaluación")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        delta = None
        if result.phase2_completed:
            delta = f"{result.final_score - result.phase1_result.score:.1f}%"
        st.metric("Puntuación Final", f"{result.final_score:.1f}%", delta=delta)
    
    with col2:
        if result.final_discarded:
            status = "DESCARTADO"
        elif result.final_score >= 50:
            status = "APROBADO"
        else:
            status = "REVISIÓN"
        st.metric("Decisión Final", status)
    
    with col3:
        st.metric("Total Cumplidos", len(result.final_fulfilled_requirements))
    
    with col4:
        st.metric("Total No Cumplidos", len(result.final_unfulfilled_requirements))
    
    # Resumen ejecutivo
    st.markdown("#### Resumen Ejecutivo")
    st.info(result.evaluation_summary)
    
    # Requisitos cumplidos finales
    if result.final_fulfilled_requirements:
        with st.expander(f"Requisitos Cumplidos ({len(result.final_fulfilled_requirements)})"):
            for req in result.final_fulfilled_requirements:
                req_type_val = req.type.value if hasattr(req.type, 'value') else str(req.type)
                tipo = format_requirement_type_text(req_type_val)
                col_text, col_type = st.columns([4, 1])
                with col_text:
                    st.markdown(f"- **{req.description}**")
                with col_type:
                    st.caption(tipo)
                if req.evidence:
                    st.caption(f"   {req.evidence[:150]}...")
    
    # Requisitos no cumplidos finales
    if result.final_unfulfilled_requirements:
        with st.expander(f"Requisitos No Cumplidos ({len(result.final_unfulfilled_requirements)})"):
            for req in result.final_unfulfilled_requirements:
                req_type_val = req.type.value if hasattr(req.type, 'value') else str(req.type)
                tipo = format_requirement_type_text(req_type_val)
                color = VELORA_ERROR if req_type_val == "obligatory" else VELORA_WARNING
                st.markdown(
                    f"- <span style='color:{color};font-size:0.75rem;'>[{tipo}]</span> **{req.description}**", 
                    unsafe_allow_html=True
                )


def render_chat_interview():
    """
    Renderiza la interfaz de entrevista conversacional profesional.
    Una pregunta a la vez con Enter para enviar.
    """
    questions = st.session_state.get('interview_questions', [])
    current_idx = st.session_state.get('chat_current_question', 0)
    chat_history = st.session_state.get('chat_history', [])
    
    if not questions:
        st.error("No hay preguntas para la entrevista")
        return
    
    total_questions = len(questions)
    
    # Header con progreso
    st.markdown("### Entrevista con el Candidato")
    
    # Barra de progreso visual
    if total_questions > 0:
        progress = current_idx / total_questions
    else:
        progress = 0
        
    st.progress(progress)
    st.markdown(f"""
    <div class="chat-progress">
        Progreso: {current_idx} de {total_questions} preguntas completadas
    </div>
    """, unsafe_allow_html=True)
    
    # Contenedor del chat
    chat_container = st.container()
    
    with chat_container:
        # Mostrar historial de chat
        for entry in chat_history:
            st.markdown(f"""
            <div class="chat-message-system">
                <strong>Pregunta {entry['question_num']}/{total_questions}:</strong> {entry['question']}<br>
                <small style="color:{VELORA_GRAY};">Requisito: {entry['requirement']} | Tipo: {entry['type']}</small>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="chat-message-user">
                <strong>Respuesta:</strong> {entry['answer']}
            </div>
            """, unsafe_allow_html=True)
    
    # Si aún hay preguntas pendientes
    if current_idx < total_questions:
        current_question = questions[current_idx]
        
        st.markdown("---")
        
        # Mostrar pregunta actual
        req_type_val = current_question.requirement_type.value if hasattr(current_question.requirement_type, 'value') else str(current_question.requirement_type)
        tipo_text = format_requirement_type_text(req_type_val)
        
        st.markdown(f"""
        <div class="chat-message-system">
            <strong>Pregunta {current_idx + 1}/{total_questions}:</strong> {current_question.question}<br>
            <small style="color:{VELORA_GRAY};">Requisito: {current_question.requirement_description} | Tipo: {tipo_text}</small>
        </div>
        """, unsafe_allow_html=True)
        
        # Input para respuesta - Form con Enter para enviar
        with st.form(key=f"chat_form_{current_idx}", clear_on_submit=False):
            answer = st.text_input(
                "Tu respuesta:",
                placeholder="Escribe tu respuesta y presiona Enter para enviar...",
                key=f"chat_input_{current_idx}"
            )
            
            _, col_btn = st.columns([3, 1])
            with col_btn:
                submit = st.form_submit_button("Enviar", type="primary")
        
        if submit:
            if answer.strip():
                chat_history.append({
                    'question_num': current_idx + 1,
                    'question': current_question.question,
                    'requirement': current_question.requirement_description,
                    'type': tipo_text,
                    'answer': answer.strip(),
                    'requirement_type': current_question.requirement_type
                })
                
                st.session_state['chat_history'] = chat_history
                st.session_state['chat_current_question'] = current_idx + 1
                
                if current_idx + 1 >= total_questions:
                    st.session_state['chat_interview_complete'] = True
                
                st.rerun()
            else:
                st.error("Por favor, escribe una respuesta antes de continuar.")
    
    else:
        # Todas las preguntas completadas
        st.success("Entrevista completada. Todas las preguntas han sido respondidas.")
        
        if st.button("Generar Resultado Final", type="primary"):
            st.session_state['chat_interview_complete'] = True
            st.rerun()


def get_or_create_evaluator():
    """Recrea el evaluador usando la configuración de sesión."""
    if 'provider' in st.session_state and 'api_key' in st.session_state:
        return CandidateEvaluator(
            provider=st.session_state['provider'],
            model_name=st.session_state.get('model_name'),
            api_key=st.session_state['api_key']
        )
    return None

# =============================================================================
# FUNCIÓN PRINCIPAL
# =============================================================================

def main():
    """Función principal de la aplicación"""
    
    # Cargar variables de entorno
    load_environment_variables()
    
    # Header corporativo
    render_velora_header()
    
    # Sidebar - Configuración
    with st.sidebar:
        render_sidebar_logo()
        
        st.markdown('<p class="sidebar-title">Configuración</p>', unsafe_allow_html=True)
        
        # Identificación de usuario
        st.markdown("**Usuario**")
        user_id = st.text_input(
            "Nombre de usuario",
            value=st.session_state.get('user_id', ''),
            help="Ingresa tu nombre de usuario para guardar y consultar tu historial",
            key="user_id_sidebar",
            label_visibility="collapsed",
            placeholder="Tu nombre de usuario"
        )
        if user_id:
            st.session_state['user_id'] = user_id
            st.caption(f"Usuario activo: {user_id}")
        
        st.markdown("---")
        
        # Selección de proveedor
        st.markdown("**Proveedor de IA**")
        try:
            available_providers = LLMFactory.get_available_providers()
        except Exception:
            available_providers = []
        
        if not available_providers:
            st.warning("No se detectaron proveedores. Usando configuración por defecto.")
            available_providers = ["openai", "google", "anthropic"]
        
        provider = st.selectbox(
            "Proveedor",
            available_providers,
            index=0,
            help="Selecciona el proveedor de IA",
            label_visibility="collapsed"
        )
        # Guardar provider en session_state para uso en otras secciones
        st.session_state['provider'] = provider
        
        # Advertencia para Anthropic
        if provider == "anthropic":
            st.markdown("""
            <div class="warning-anthropic">
            <strong>Nota:</strong> Anthropic no ofrece API de embeddings. 
            Las funcionalidades semánticas quedan deshabilitadas con este proveedor.
            </div>
            """, unsafe_allow_html=True)
        
        # API Keys
        api_key = None
        
        if provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                api_key = st.text_input(
                    "OpenAI API Key",
                    type="password",
                    help="Tu API key de OpenAI",
                    key="openai_key",
                    placeholder="sk-..."
                )
                if api_key:
                    os.environ["OPENAI_API_KEY"] = api_key
        
        elif provider == "google":
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                api_key = st.text_input(
                    "Google API Key",
                    type="password",
                    help="Tu API key de Google (Gemini)",
                    key="google_key"
                )
                if api_key:
                    os.environ["GOOGLE_API_KEY"] = api_key
        
        elif provider == "anthropic":
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                api_key = st.text_input(
                    "Anthropic API Key",
                    type="password",
                    help="Tu API key de Anthropic",
                    key="anthropic_key"
                )
                if api_key:
                    os.environ["ANTHROPIC_API_KEY"] = api_key
        
        # Guardamos el estado de la API key (sin st.stop() aquí)
        api_key_valid = False
        if api_key:
            st.session_state['api_key'] = api_key
            st.caption("API Key configurada")
            api_key_valid = True
        else:
            st.warning("Se requiere API Key para continuar")
        
        st.markdown("---")
        
        # Modelo (solo si hay API key)
        model_name = None
        if api_key_valid:
            st.markdown("**Modelo**")
            available_models = LLMFactory.get_available_models(provider)
            if available_models:
                model_name = st.selectbox(
                    "Modelo",
                    available_models,
                    index=0,
                    help=f"Modelo de {provider}",
                    label_visibility="collapsed"
                )
                # Guardar model_name en session_state para uso en otras secciones
                st.session_state['model_name'] = model_name
            else:
                st.error(f"No hay modelos para {provider}")
        
        st.markdown("---")
        st.caption("Este sistema evalúa candidatos mediante análisis automático de CV vs Oferta con IA.")
    
    # Si no hay API key, mostrar contenido limitado (sin st.stop())
    if not api_key_valid:
        pass  # Continuar mostrando la interfaz
    
    # Contenedor principal
    tab1, tab2, tab3 = st.tabs(["Evaluación", "Mi Historial", "Instrucciones"])
    
    with tab1:
        # Sección de entrada de datos
        st.markdown("### Datos de Entrada")
        
        # Entrada de CV
        st.markdown("**1. Curriculum Vitae (CV)**")
        cv_option = st.radio(
            "Método de entrada del CV",
            ["Subir archivo", "Pegar texto"],
            horizontal=True,
            label_visibility="collapsed"
        )
        
        cv_text = None
        
        if cv_option == "Subir archivo":
            cv_file = st.file_uploader(
                "Sube el archivo del CV",
                type=["txt", "pdf", "docx"],
                help="Formatos: .txt, .pdf, .docx",
                key="cv_file_uploader"
            )
            
            if cv_file:
                extracted_text = None
                
                if cv_file.type == "text/plain":
                    extracted_text = cv_file.read().decode("utf-8")
                    st.success("Archivo de texto cargado")
                elif cv_file.type == "application/pdf":
                    try:
                        with st.spinner("Extrayendo texto del PDF..."):
                            pdf_bytes = cv_file.read()
                            extracted_text = extract_text_from_pdf(pdf_bytes)
                            if extracted_text:
                                st.success("PDF procesado")
                            else:
                                st.error("No se pudo extraer texto del PDF")
                    except Exception as e:
                        st.error(f"Error al procesar PDF: {str(e)}")
                elif cv_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                    st.warning("Los archivos .docx no están completamente soportados. Usa .txt o .pdf")
                else:
                    st.warning("Formato no soportado. Usa .txt o .pdf")
                
                if extracted_text:
                    if 'extracted_cv_text' not in st.session_state or st.session_state.get('cv_file_name') != cv_file.name:
                        st.session_state['extracted_cv_text'] = extracted_text
                        st.session_state['cv_file_name'] = cv_file.name
                    
                    cv_text = st.text_area(
                        "Contenido extraído (editable)",
                        value=st.session_state.get('extracted_cv_text', extracted_text),
                        height=250,
                        key="cv_extracted_editor"
                    )
                    st.caption(f"{len(cv_text)} caracteres")
            else:
                if 'extracted_cv_text' in st.session_state:
                    del st.session_state['extracted_cv_text']
                if 'cv_file_name' in st.session_state:
                    del st.session_state['cv_file_name']
        else:
            cv_text = st.text_area(
                "Contenido del CV",
                height=200,
                placeholder="Pega el texto completo del CV aquí...",
                label_visibility="collapsed"
            )
        
        st.markdown("---")
        
        # Entrada de Oferta
        st.markdown("**2. Oferta de Empleo**")
        offer_option = st.radio(
            "Método de entrada de la oferta",
            ["Pegar texto", "URL"],
            horizontal=True,
            label_visibility="collapsed"
        )
        
        job_offer_text = None
        
        if offer_option == "Pegar texto":
            job_offer_text = st.text_area(
                "Contenido de la oferta",
                height=200,
                placeholder="Pega el texto completo de la oferta aquí...",
                label_visibility="collapsed"
            )
        else:
            offer_url = st.text_input(
                "URL pública de la oferta",
                placeholder="https://ejemplo.com/oferta - URL pública accesible",
                help="Pega la URL pública de la oferta (debe permitir acceso directo sin autenticación)",
                label_visibility="collapsed"
            )
            
            # Auto-descarga con detección de URL válida
            if offer_url and offer_url.startswith("http"):
                if 'last_url' not in st.session_state or st.session_state['last_url'] != offer_url:
                    st.session_state['last_url'] = offer_url
                    with st.spinner("Descargando contenido..."):
                        scraped_text = scrape_job_offer_url(offer_url)
                        if scraped_text:
                            st.session_state['downloaded_offer'] = scraped_text
                            st.success("Oferta descargada")
                        else:
                            st.error("No se pudo descargar. Verifica que la URL sea pública y accesible.")
            
            if 'downloaded_offer' in st.session_state:
                job_offer_text = st.text_area(
                    "Contenido descargado (editable)",
                    value=st.session_state['downloaded_offer'],
                    height=250,
                    key="downloaded_offer_editor"
                )
        
        st.markdown("---")
        
        # Opciones avanzadas
        with st.expander("Opciones Avanzadas"):
            use_langgraph = st.checkbox(
                "Potenciar evaluación con LangGraph",
                value=False,
                help="Habilita arquitectura LangGraph avanzada para evaluación"
            )
            
            embeddings_disabled = not EmbeddingFactory.supports_embeddings(provider)
            embeddings_default = not embeddings_disabled
            
            use_semantic = st.checkbox(
                "Usar Embeddings Semánticos",
                value=embeddings_default,
                disabled=embeddings_disabled,
                help="Usa embeddings para encontrar evidencia semántica en el CV."
            )
            
            if embeddings_disabled:
                st.markdown('<div class="warning-box"><strong>Nota:</strong> Embeddings no disponibles con Anthropic.</div>', unsafe_allow_html=True)
        
        # Guardar textos
        if cv_text:
            st.session_state['cv_text'] = cv_text
        if job_offer_text:
            st.session_state['job_offer_text'] = job_offer_text
        
        # ===================================================================
        # FASE 1: Análisis inicial
        # ===================================================================
        
        can_evaluate = bool(cv_text and job_offer_text)
        
        if st.button("Iniciar Evaluación", type="primary", disabled=not can_evaluate):
            if not cv_text:
                st.error("Proporciona el CV del candidato")
                st.stop()
            
            if not job_offer_text:
                st.error("Proporciona la oferta de empleo")
                st.stop()
            
            # Resetear estado
            for key in ['evaluation_saved', 'evaluation_completed', 'phase2_started', 
                        'phase1_completed', 'chat_current_question', 'chat_history', 
                        'chat_interview_complete', 'interview_questions']:
                if key in st.session_state:
                    del st.session_state[key]
            
            st.session_state['cv_text'] = cv_text
            st.session_state['job_offer_text'] = job_offer_text
            st.session_state['provider'] = provider
            st.session_state['model_name'] = model_name
            
            try:
                with st.spinner("Inicializando evaluador..."):
                    # Instanciar evaluador localmente
                    evaluator = CandidateEvaluator(
                        provider=provider,
                        model_name=model_name,
                        api_key=api_key
                    )
                
                # Instancia separada para análisis fase 1
                phase1_analyzer = Phase1Analyzer(
                    provider=provider,
                    model_name=model_name,
                    api_key=api_key,
                    use_semantic_matching=use_semantic,
                    use_langgraph=use_langgraph
                )
                
                with st.status("Ejecutando Fase 1: Análisis de CV y oferta...", expanded=True) as status:
                    st.write("Inicializando análisis...")
                    progress_bar = st.progress(0, text="Preparando...")
                    
                    config_info = []
                    if use_langgraph:
                        config_info.append("LangGraph")
                    if use_semantic:
                        config_info.append("Embeddings")
                    if config_info:
                        st.caption(f"Configuración: {' + '.join(config_info)}")
                    
                    progress_bar.progress(20, text="Extrayendo requisitos...")
                    st.write("Analizando oferta de empleo...")
                    
                    progress_bar.progress(40, text="Evaluando CV...")
                    st.write("Comparando CV con requisitos...")
                    
                    phase1_result = phase1_analyzer.analyze(job_offer_text, cv_text)
                    
                    progress_bar.progress(90, text="Generando resultados...")
                    
                    total_reqs = len(phase1_result.fulfilled_requirements) + len(phase1_result.unfulfilled_requirements)
                    st.write(f"Análisis completado: {total_reqs} requisitos evaluados")
                    st.write(f"Score inicial: **{phase1_result.score:.1f}%**")
                    
                    progress_bar.progress(100, text="Completado")
                    status.update(label="Fase 1 completada", state="complete")
                    
                    st.session_state['phase1_result'] = phase1_result
                    st.session_state['phase1_completed'] = True
                
                # Guardar si no hay Fase 2
                user_id_phase1 = st.session_state.get('user_id', '')
                should_save_phase1 = phase1_result.discarded or not phase1_result.missing_requirements
                
                if user_id_phase1 and should_save_phase1:
                    try:
                        memory = UserMemory()
                        enriched = memory.save_phase1_evaluation(
                            user_id=user_id_phase1,
                            job_offer_text=job_offer_text,
                            cv_text=cv_text,
                            phase1_result=phase1_result,
                            provider=provider,
                            model=model_name
                        )
                        st.session_state['current_evaluation_id'] = enriched.evaluation_id
                        st.session_state['evaluation_saved'] = True
                    except Exception as save_error:
                        logger.warning(f"No se pudo guardar Fase 1: {save_error}")
                
                st.success("Fase 1 completada exitosamente")
                st.rerun()
                
            except Exception as e:
                st.error(f"Error durante la evaluación: {str(e)}")
                st.exception(e)
        
        # ===================================================================
        # Mostrar resultados de Fase 1
        # ===================================================================
        if st.session_state.get('phase1_completed') and not st.session_state.get('evaluation_completed'):
            phase1_result = st.session_state['phase1_result']
            
            st.markdown("---")
            display_phase1_results(phase1_result)
            
            if not phase1_result.discarded and phase1_result.missing_requirements:
                st.markdown("---")
                st.markdown("### Fase 2: Entrevista")
                st.info(f"Se encontraron **{len(phase1_result.missing_requirements)} requisito(s)** no verificables en el CV. "
                        f"Inicia una entrevista conversacional para obtener más información.")
                
                if st.button("Iniciar Entrevista", type="primary"):
                    evaluator = get_or_create_evaluator()
                    if evaluator:
                        with st.spinner("Generando preguntas..."):
                            questions = evaluator.phase2_interviewer.generate_questions(
                                phase1_result.missing_requirements,
                                phase1_result,
                                st.session_state.get('cv_text', '')
                            )
                            st.session_state['interview_questions'] = questions
                            st.session_state['chat_current_question'] = 0
                            st.session_state['chat_history'] = []
                            st.session_state['phase2_started'] = True
                        st.rerun()
                    else:
                        st.error("Error al recuperar el evaluador. Recarga la página.")
        
        # ===================================================================
        # FASE 2: Entrevista conversacional
        # ===================================================================
        if st.session_state.get('phase2_started') and not st.session_state.get('evaluation_completed'):
            st.markdown("---")
            render_chat_interview()
            
            if st.session_state.get('chat_interview_complete'):
                phase1_result = st.session_state['phase1_result']
                evaluator = get_or_create_evaluator()
                chat_history = st.session_state.get('chat_history', [])
                
                if evaluator:
                    with st.spinner("Procesando entrevista y generando resultado final..."):
                        
                        formatted_responses = [
                            InterviewResponse(
                                question=entry['question'],
                                answer=entry['answer'],
                                requirement_description=entry['requirement'],
                                requirement_type=entry['requirement_type']
                            )
                            for entry in chat_history
                        ]
                        
                        resultado = evaluator.reevaluate_with_interview(phase1_result, formatted_responses)
                        
                        st.session_state['evaluation_result'] = resultado
                        st.session_state['evaluation_completed'] = True
                        st.session_state['phase2_started'] = False
                    
                    st.success("Evaluación completada")
                    st.rerun()
                else:
                    st.error("Error crítico: Sesión perdida. Recargue la página.")
        
        # ===================================================================
        # Resultados finales
        # ===================================================================
        if st.session_state.get('evaluation_completed'):
            resultado = st.session_state['evaluation_result']
            
            st.markdown("---")
            
            if resultado.phase2_completed and resultado.interview_responses:
                display_interview_responses(resultado.interview_responses)
            
            st.markdown("---")
            display_final_results(resultado)
            
            user_id_for_save = st.session_state.get('user_id', '')
            evaluation_saved_flag = st.session_state.get('evaluation_saved', False)
            
            if user_id_for_save and not evaluation_saved_flag:
                try:
                    memory = UserMemory()
                    enriched = create_enriched_evaluation(
                        user_id=user_id_for_save,
                        job_offer_text=st.session_state.get('job_offer_text', ''),
                        cv_text=st.session_state.get('cv_text', ''),
                        phase1_result=resultado.phase1_result,
                        phase2_completed=resultado.phase2_completed,
                        evaluation_result=resultado,
                        provider=st.session_state.get('provider', provider),
                        model=st.session_state.get('model_name', model_name)
                    )
                    memory.save_evaluation(enriched)
                    st.session_state['evaluation_saved'] = True
                    st.success("Evaluación guardada en tu historial")
                except Exception as e:
                    st.error(f"Error al guardar: {str(e)}")
            
            st.markdown("---")
            if st.button("Nueva Evaluación"):
                keys_to_keep = ['user_id', 'provider', 'model_name', 'api_key', 'last_url']
                keys_to_clear = [k for k in st.session_state.keys() if k not in keys_to_keep]
                for key in keys_to_clear:
                    del st.session_state[key]
                st.rerun()
    
    with tab2:
        st.markdown("### Mi Historial de Evaluaciones")
        
        user_id = st.session_state.get('user_id', '')
        
        if not user_id:
            st.warning("Ingresa tu nombre de usuario en el panel lateral para ver tu historial.")
        else:
            try:
                memory = UserMemory()
                evaluations = memory.get_evaluations(user_id)
            except Exception as e:
                st.error(f"Error accediendo a memoria: {e}")
                evaluations = []

            total_evals = len(evaluations)
            
            if total_evals > 0:
                st.success(f"{total_evals} evaluación(es) encontrada(s)")
                
                st.markdown("#### Resumen de Evaluaciones")
                col1, col2, col3, col4 = st.columns(4)
                
                scores = [e.get("score", 0) for e in evaluations]
                avg_score = sum(scores) / len(scores) if scores else 0
                approved = sum(1 for e in evaluations if e.get("status") == "approved")
                rejected = sum(1 for e in evaluations if e.get("status") == "rejected")
                phase1_only = sum(1 for e in evaluations if e.get("status") == "phase1_only")
                
                with col1:
                    st.metric("Promedio", f"{avg_score:.1f}%")
                with col2:
                    st.metric("Aprobadas", approved)
                with col3:
                    st.metric("Rechazadas", rejected)
                with col4:
                    st.metric("Solo Fase 1", phase1_only)
                
                st.markdown("#### Historial Completo")
                
                display_evals = sorted(evaluations, key=lambda x: x.get('timestamp', ''), reverse=True)
                
                for i, eval_data in enumerate(display_evals[:10], 1):
                    title = eval_data.get('job_offer_title', 'Oferta de empleo')
                    score = eval_data.get('score', 0)
                    status = eval_data.get('status', 'unknown')
                    timestamp = eval_data.get('timestamp', 'N/A')
                    if timestamp and len(timestamp) >= 10:
                        timestamp = timestamp[:10]
                        
                    phase = eval_data.get('phase_completed', 'phase1')
                    
                    # Determinar color según estado
                    if status == "approved":
                        status_class = "status-approved"
                        status_label = "Aprobado"
                        bg_style = "linear-gradient(90deg, rgba(76, 175, 80, 0.18) 0%, rgba(76, 175, 80, 0.06) 100%)"
                        border_color = "#4CAF50"
                    elif status == "rejected":
                        status_class = "status-rejected"
                        status_label = "Rechazado"
                        bg_style = "linear-gradient(90deg, rgba(244, 67, 54, 0.18) 0%, rgba(244, 67, 54, 0.06) 100%)"
                        border_color = "#EF5350"
                    else:
                        status_class = "status-phase1"
                        status_label = "Solo Fase 1"
                        bg_style = "linear-gradient(90deg, rgba(0, 180, 216, 0.15) 0%, rgba(0, 180, 216, 0.06) 100%)"
                        border_color = "#00B4D8"
                    
                    # Título del expander
                    expander_title = f"#{i} · {title[:45]}... · {score:.1f}% · {timestamp}"
                    
                    # Contenedor con estilo de color
                    st.markdown(f'''<div style="
                        background: {bg_style};
                        border-left: 5px solid {border_color};
                        border-radius: 10px;
                        margin-bottom: 0.5rem;
                        overflow: hidden;
                    ">''', unsafe_allow_html=True)
                    
                    with st.expander(expander_title):
                        # Estado y fase con tamaños consistentes y alineados
                        met1, met2, met3, met4 = st.columns(4)
                        with met1:
                            st.metric("Puntuación", f"{score:.1f}%")
                        with met2:
                            st.markdown(f'<div class="{status_class}">{status_label}</div>', unsafe_allow_html=True)
                        with met3:
                            phase_class = "status-approved" if phase == "phase2" else "status-phase1"
                            phase_label = "Fase 2" if phase == "phase2" else "Fase 1"
                            st.markdown(f'<div class="{phase_class}">{phase_label}</div>', unsafe_allow_html=True)
                        with met4:
                            st.metric("Requisitos", f"{eval_data.get('fulfilled_count', 0)}/{eval_data.get('total_requirements', 0)}")
                        
                        st.markdown("---")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("**Detalles:**")
                            st.write(f"• Obligatorios: {eval_data.get('obligatory_requirements', 0)}")
                            st.write(f"• Opcionales: {eval_data.get('optional_requirements', 0)}")
                            st.write(f"• Cumplidos: {eval_data.get('fulfilled_count', 0)}")
                        with col2:
                            st.markdown("**Info:**")
                            st.write(f"• Fecha: {timestamp}")
                            st.write(f"• Proveedor: {eval_data.get('provider', 'N/A')}")
                            st.write(f"• Modelo: {eval_data.get('model', 'N/A')}")
                        
                        if eval_data.get('strengths_summary'):
                            st.success(f"**Fortalezas:** {eval_data.get('strengths_summary')}")
                        if eval_data.get('gap_summary'):
                            st.warning(f"**Brechas:** {eval_data.get('gap_summary')}")
                        if eval_data.get('rejection_reason'):
                            st.error(f"**Razón de rechazo:** {eval_data.get('rejection_reason')}")
                    
                    # Cerrar contenedor de color
                    st.markdown('</div>', unsafe_allow_html=True)
                
                st.markdown("---")
                st.markdown("#### Asistente de Historial")
                st.info("Pregunta lo que quieras sobre tu historial de evaluaciones.")
                
                query = st.text_input(
                    "Consulta",
                    placeholder="Ej: ¿Por qué fui rechazado? ¿Cuál es mi puntuación promedio? (Presiona Enter)",
                    key="rag_query",
                    label_visibility="collapsed"
                )
                
                if query:
                    with st.spinner("Buscando en tu historial..."):
                        response = ""
                        try:
                            llm = LLMFactory.create_llm(
                                provider=st.session_state.get('provider', 'openai'),
                                model_name=st.session_state.get('model_name', 'gpt-4o-mini'),
                                api_key=api_key
                            )
                            
                            chatbot = HistoryChatbot(user_id, llm, memory)
                            response = chatbot.query(query)
                            
                        except Exception as e:
                            st.warning(f"Modo básico (Error LLM: {str(e)})")
                            response = analyze_user_history(memory, user_id, query)
                        
                        st.markdown("**Respuesta:**")
                        st.markdown(response)
                
            else:
                st.info("No tienes evaluaciones guardadas. Realiza una evaluación en la pestaña 'Evaluación' para comenzar.")
    
    with tab3:
        st.markdown("### Instrucciones de Uso")
        
        st.markdown("""
        #### Cómo usar el sistema
        
        1. **Configuración inicial**
           - En el panel lateral, selecciona el proveedor de IA (OpenAI, Google, Anthropic)
           - Ingresa tu API Key correspondiente
           - Selecciona el modelo a utilizar
        
        2. **Proporcionar datos**
           - **CV**: Sube un archivo (.txt, .pdf) o pega el texto directamente
           - **Oferta**: Pega el texto o proporciona una URL pública (debe permitir acceso directo sin autenticación)
        
        3. **Fase 1 - Análisis automático**
           - Haz clic en "Iniciar Evaluación"
           - El sistema extraerá requisitos y los comparará con el CV
           - Verás qué requisitos se cumplen y cuáles no
        
        4. **Fase 2 - Entrevista conversacional** (si es necesario)
           - Si hay requisitos no verificables, podrás iniciar una entrevista
           - El sistema preguntará **una pregunta a la vez** en formato chat
           - Responde cada pregunta para continuar
           - Al finalizar, obtendrás el resultado final
        
        ---
        
        #### Reglas de puntuación
        
        - Todos los requisitos tienen el mismo peso
        - Si falta un requisito **obligatorio**: 0% (candidato descartado)
        - Si se cumplen todos los requisitos: 100%
        - En otros casos: proporcional al número de requisitos cumplidos
        
        ---
        
        #### Notas sobre proveedores
        
        | Proveedor | LLM | Embeddings |
        |-----------|-----|------------|
        | **OpenAI** | Sí | Sí |
        | **Google (Gemini)** | Sí | Sí |
        | **Anthropic (Claude)** | Sí | No |
        
        **Nota:** Al usar Anthropic, las funcionalidades de embeddings semánticos quedan deshabilitadas.
        """)


if __name__ == "__main__":
    main()