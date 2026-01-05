"""
Velora - Sistema de Evaluación de Candidatos con IA.

Prueba técnica desarrollada por Carlos Vega para Velora.
"""

import streamlit as st
import sys
import logging
import time
from pathlib import Path
import os
from typing import Generator

# Rutas de logos de Velora (imágenes PNG)
ASSETS_DIR = Path(__file__).resolve().parent / "assets"
VELORA_LOGO_LARGE = ASSETS_DIR / "Velora_logotipo_grande_Color.png"
VELORA_LOGO_SMALL = ASSETS_DIR / "Velora_logotipo_pequeño_Color.png"
VELORA_LOGO_APPLE_ICON = ASSETS_DIR / "Velora_logotipo_apple_icon.png"

# Configuración de página Streamlit
st.set_page_config(
    page_title="Prueba Técnica | Carlos Vega",
    page_icon=str(VELORA_LOGO_APPLE_ICON),
    layout="wide",
    initial_sidebar_state="expanded"
)

logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
try:
    from backend import (
        # Orquestación
        Orquestador, CandidateEvaluator,
        # Infraestructura - Proveedores LLM
        LLMFactory, EmbeddingFactory,
        # Modelos
        EvaluationResult,
        # Infraestructura - Extracción
        extract_text_from_pdf, scrape_job_offer_url,
        # Infraestructura - Persistencia
        UserMemory, create_enriched_evaluation,
        # Núcleo
        HistoryChatbot, Phase1Analyzer, AgenticInterviewer,
    )
except ImportError as e:
    st.error(f"Error importando módulos del backend: {e}. Asegúrate de ejecutar desde la raíz del proyecto.")
    st.stop()

# Paleta de colores Velora
VELORA_PRIMARY = "#00B4D8"      # Azul turquesa principal
VELORA_SECONDARY = "#00CED1"    # Turquesa secundario
VELORA_DARK = "#3D4043"         # Gris oscuro para texto
VELORA_GRAY = "#6B7280"         # Gris medio
VELORA_LIGHT_GRAY = "#F3F4F6"   # Gris claro para fondos
VELORA_WHITE = "#FFFFFF"
VELORA_SUCCESS = "#10B981"      # Verde para éxito
VELORA_ERROR = "#EF4444"        # Rojo para errores
VELORA_WARNING = "#F59E0B"

# Estilos CSS corporativos
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
       SIDEBAR - Panel lateral profesional y elegante
       ============================================ */
    section[data-testid="stSidebar"] {{
        background: linear-gradient(180deg, #FAFBFC 0%, rgba(0, 180, 216, 0.03) 100%) !important;
        border-right: 1px solid rgba(0, 180, 216, 0.15) !important;
        box-shadow: 2px 0 8px rgba(0, 0, 0, 0.04) !important;
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
       SISTEMA DE ESTADOS PROFESIONAL v1.0 - Unificado
       ============================================ */
    
    /* Card base para métricas del historial - dimensiones uniformes */
    .history-metric-card {{
        background: {VELORA_WHITE};
        border: 1px solid rgba(0, 180, 216, 0.12);
        border-radius: 10px;
        padding: 1rem 1.25rem;
        min-height: 85px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        transition: box-shadow 0.2s ease;
    }}
    
    .history-metric-card:hover {{
        box-shadow: 0 4px 12px rgba(0, 180, 216, 0.1);
    }}
    
    .history-metric-label {{
        font-size: 0.7rem;
        font-weight: 600;
        color: {VELORA_GRAY};
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 0.4rem;
    }}
    
    .history-metric-value {{
        font-size: 1.5rem;
        font-weight: 700;
        color: {VELORA_PRIMARY};
        line-height: 1.2;
    }}
    
    /* Status badge cards - APROBADO */
    .history-metric-card.status-approved {{
        background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%);
        border-color: rgba(76, 175, 80, 0.3);
    }}
    .history-metric-card.status-approved .history-metric-value {{
        color: #2E7D32;
        font-size: 1rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}
    
    /* Status badge cards - RECHAZADO */
    .history-metric-card.status-rejected {{
        background: linear-gradient(135deg, #FFEBEE 0%, #FFCDD2 100%);
        border-color: rgba(244, 67, 54, 0.3);
    }}
    .history-metric-card.status-rejected .history-metric-value {{
        color: #C62828;
        font-size: 1rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}
    
    /* Status badge cards - FASE 1 (turquesa corporativo) */
    .history-metric-card.status-phase1 {{
        background: linear-gradient(135deg, rgba(0, 180, 216, 0.12) 0%, rgba(0, 206, 209, 0.18) 100%);
        border-color: rgba(0, 180, 216, 0.3);
    }}
    .history-metric-card.status-phase1 .history-metric-value {{
        color: {VELORA_PRIMARY};
        font-size: 1rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}
    
    /* Status badge cards - FASE 2 (verde aprobado) */
    .history-metric-card.status-phase2 {{
        background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%);
        border-color: rgba(76, 175, 80, 0.3);
    }}
    .history-metric-card.status-phase2 .history-metric-value {{
        color: #2E7D32;
        font-size: 1rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
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
       HISTORIAL v1.0 - Sistema de expanders con estado
       ============================================ */
    
    /* Contenedor del historial - spacing ultra-compacto */
    .history-container {{
        display: flex;
        flex-direction: column;
        gap: 0.15rem;
    }}
    
    /* Contenedor individual de cada evaluación */
    .history-item {{
        border-radius: 8px;
        overflow: hidden;
        transition: all 0.2s ease;
        margin-bottom: 0.1rem !important;
    }}
    
    /* Contenido interno del historial más compacto */
    .history-item .stSuccess, .history-item .stWarning, .history-item .stError {{
        padding: 0.4rem 0.75rem !important;
        margin: 0.2rem 0 !important;
        font-size: 0.85rem !important;
    }}
    
    /* APROBADO - degradado verde */
    .history-item-approved {{
        background: linear-gradient(90deg, rgba(76, 175, 80, 0.2) 0%, rgba(76, 175, 80, 0.06) 100%);
        border-left: 4px solid #4CAF50;
    }}
    .history-item-approved:hover {{
        background: linear-gradient(90deg, rgba(76, 175, 80, 0.28) 0%, rgba(76, 175, 80, 0.1) 100%);
        box-shadow: 0 4px 12px rgba(76, 175, 80, 0.15);
    }}
    
    /* RECHAZADO - degradado rojo */
    .history-item-rejected {{
        background: linear-gradient(90deg, rgba(244, 67, 54, 0.2) 0%, rgba(244, 67, 54, 0.06) 100%);
        border-left: 4px solid #EF5350;
    }}
    .history-item-rejected:hover {{
        background: linear-gradient(90deg, rgba(244, 67, 54, 0.28) 0%, rgba(244, 67, 54, 0.1) 100%);
        box-shadow: 0 4px 12px rgba(244, 67, 54, 0.15);
    }}
    
    /* SOLO FASE 1 - degradado turquesa */
    .history-item-phase1 {{
        background: linear-gradient(90deg, rgba(0, 180, 216, 0.18) 0%, rgba(0, 180, 216, 0.05) 100%);
        border-left: 4px solid {VELORA_PRIMARY};
    }}
    .history-item-phase1:hover {{
        background: linear-gradient(90deg, rgba(0, 180, 216, 0.26) 0%, rgba(0, 180, 216, 0.1) 100%);
        box-shadow: 0 4px 12px rgba(0, 180, 216, 0.15);
    }}
    
    /* Expander dentro del contenedor - hereda background */
    .history-item [data-testid="stExpander"] {{
        background: transparent !important;
    }}
    .history-item [data-testid="stExpander"] details {{
        background: transparent !important;
        border: none !important;
        border-radius: 0 !important;
        margin-bottom: 0 !important;
    }}
    .history-item [data-testid="stExpander"] summary {{
        padding: 0.6rem 0.85rem !important;
        font-size: 0.9rem !important;
        font-weight: 500 !important;
        background: transparent !important;
    }}
    
    /* Grid de métricas dentro del expander expandido */
    .history-metrics-grid {{
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 0.75rem;
        padding: 0.5rem 0;
    }}
    
    /* ============================================
       RESPONSIVE - Adaptación mobile/tablet
       ============================================ */
    @media (max-width: 768px) {{
        .history-metric-card {{
            min-height: 70px;
            padding: 0.75rem 1rem;
        }}
        .history-metric-value {{
            font-size: 1.25rem;
        }}
        .history-item [data-testid="stExpander"] summary {{
            font-size: 0.85rem !important;
            padding: 0.75rem 0.85rem !important;
        }}
    }}
    
    @media (max-width: 480px) {{
        .history-metric-card {{
            min-height: 60px;
            padding: 0.5rem 0.75rem;
        }}
        .history-metric-label {{
            font-size: 0.6rem;
        }}
        .history-metric-value {{
            font-size: 1rem;
        }}
    }}
    
</style>
""", unsafe_allow_html=True)


# Funciones auxiliares

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
            Prueba técnica desarrollada por Carlos Vega para postularse como Ingeniero de IA Generativa en Velora
        </p>
        <p class="velora-description">
            He desarrollado este sistema con el ánimo de completar sus requisitos y, simultáneamente, 
            intentar demostrar competencias adicionales en IA Generativa. Integré tecnologías como LangGraph, 
            hiperparametrización, RAG y LangSmith como extensiones adicionales coherentes, intentando mantener 
            siempre el foco en los objetivos fundamentales de la prueba técnica.
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
    
    # Validación: query puede ser None o vacío
    if not query or not isinstance(query, str):
        query = ""
    
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
            f"{phase1_result.puntuacion:.1f}%"
        )
    
    with col2:
        if phase1_result.descartado:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #FFEBEE 0%, #FFCDD2 100%); 
                        padding: 0.75rem 1rem; border-radius: 8px; text-align: center;
                        border: 1px solid rgba(198, 40, 40, 0.2);">
                <p style="margin: 0; font-size: 0.7rem; color: #9E9E9E; text-transform: uppercase; letter-spacing: 0.05em;">Estado</p>
                <p style="margin: 0.25rem 0 0 0; font-size: 1.25rem; font-weight: 700; color: #C62828;">DESCARTADO</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.metric("Estado", "EN PROCESO")
    
    with col3:
        total = len(phase1_result.requisitos_cumplidos) + len(phase1_result.requisitos_no_cumplidos)
        st.metric(
            "Requisitos Cumplidos",
            f"{len(phase1_result.requisitos_cumplidos)}/{total}"
        )
    
    # Mensaje de estado semántico
    if phase1_result.descartado:
        st.markdown("""
        <div style="background: linear-gradient(90deg, rgba(198, 40, 40, 0.1) 0%, rgba(198, 40, 40, 0.02) 100%);
                    padding: 1rem 1.25rem; border-radius: 8px; margin: 1rem 0;
                    border-left: 4px solid #C62828;">
            <p style="margin: 0; color: #C62828; font-weight: 600; font-size: 1rem;">
                Candidato descartado - No cumple requisitos obligatorios
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background: linear-gradient(90deg, rgba(0, 180, 216, 0.1) 0%, rgba(0, 180, 216, 0.02) 100%);
                    padding: 1rem 1.25rem; border-radius: 8px; margin: 1rem 0;
                    border-left: 4px solid {VELORA_PRIMARY};">
            <p style="margin: 0; color: {VELORA_PRIMARY}; font-weight: 600; font-size: 1rem;">
                Candidato en proceso - Análisis inicial completado
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Requisitos cumplidos
    if phase1_result.requisitos_cumplidos:
        with st.expander(f"Requisitos Cumplidos ({len(phase1_result.requisitos_cumplidos)})", expanded=True):
            for req in phase1_result.requisitos_cumplidos:
                confidence = getattr(req, 'confianza', None)
                if hasattr(confidence, 'value'):
                    confidence_val = confidence.value
                else:
                    confidence_val = str(confidence) if confidence else "medium"
                
                confidence_color = get_confidence_color(confidence_val)
                
                col_req, col_conf = st.columns([4, 1])
                with col_req:
                    st.markdown(f"**{req.descripcion}**")
                with col_conf:
                    st.markdown(
                        f"<span style='color:{confidence_color};font-size:0.85rem;'>{format_confidence_text(confidence_val)}</span>", 
                        unsafe_allow_html=True
                    )
                
                if req.evidencia:
                    st.caption(f"Evidencia: {req.evidencia[:200]}...")
                
                reasoning = getattr(req, 'reasoning', None)
                if reasoning:
                    st.caption(f"Razonamiento: {reasoning}")
                
                st.markdown("---")
    
    # Requisitos no cumplidos
    if phase1_result.requisitos_no_cumplidos:
        with st.expander(f"Requisitos No Cumplidos ({len(phase1_result.requisitos_no_cumplidos)})"):
            for req in phase1_result.requisitos_no_cumplidos:
                req_type_val = req.tipo.value if hasattr(req.tipo, 'value') else str(req.tipo)
                tipo_text = format_requirement_type_text(req_type_val)
                
                confidence = getattr(req, 'confianza', None)
                if hasattr(confidence, 'value'):
                    confidence_val = confidence.value
                else:
                    confidence_val = str(confidence) if confidence else "medium"
                
                confidence_color = get_confidence_color(confidence_val)
                
                col_req, col_conf = st.columns([4, 1])
                with col_req:
                    color = VELORA_ERROR if req_type_val == "obligatory" else VELORA_WARNING
                    st.markdown(
                        f"<span style='color:{color};font-size:0.75rem;font-weight:600;'>[{tipo_text}]</span> **{req.descripcion}**", 
                        unsafe_allow_html=True
                    )
                with col_conf:
                    st.markdown(
                        f"<span style='color:{confidence_color};font-size:0.85rem;'>{format_confidence_text(confidence_val)}</span>", 
                        unsafe_allow_html=True
                    )
                
                if req.evidencia:
                    st.caption(f"Evidencia: {req.evidencia[:300]}...")
                
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
                    <strong>Pregunta {i}:</strong> {resp.pregunta}<br>
                    <small style="color:{VELORA_GRAY};">Requisito: {resp.descripcion_requisito}</small>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div class="chat-message-user">
                    <strong>Respuesta:</strong> {resp.respuesta}
                </div>
                """, unsafe_allow_html=True)


def display_final_results(result: EvaluationResult):
    """Muestra los resultados finales con diseño profesional"""
    st.markdown("### Resultado Final de la Evaluación")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Puntuación Final", f"{result.puntuacion_final:.1f}%")
    
    with col2:
        if result.descartado_final:
            # Estado DESCARTADO - Rojo
            st.markdown("""
            <div style="background: linear-gradient(135deg, #FFEBEE 0%, #FFCDD2 100%); 
                        padding: 0.75rem 1rem; border-radius: 8px; text-align: center;
                        border: 1px solid rgba(198, 40, 40, 0.2);">
                <p style="margin: 0; font-size: 0.7rem; color: #9E9E9E; text-transform: uppercase; letter-spacing: 0.05em;">Decisión Final</p>
                <p style="margin: 0.25rem 0 0 0; font-size: 1.25rem; font-weight: 700; color: #C62828;">DESCARTADO</p>
            </div>
            """, unsafe_allow_html=True)
        elif result.puntuacion_final >= 50:
            # Estado APROBADO - Verde
            st.markdown("""
            <div style="background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%); 
                        padding: 0.75rem 1rem; border-radius: 8px; text-align: center;
                        border: 1px solid rgba(76, 175, 80, 0.2);">
                <p style="margin: 0; font-size: 0.7rem; color: #9E9E9E; text-transform: uppercase; letter-spacing: 0.05em;">Decisión Final</p>
                <p style="margin: 0.25rem 0 0 0; font-size: 1.25rem; font-weight: 700; color: #2E7D32;">APROBADO</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Estado REVISIÓN - Neutro
            st.metric("Decisión Final", "REVISIÓN")
    
    with col3:
        st.metric("Total Cumplidos", len(result.requisitos_finales_cumplidos))
    
    with col4:
        st.metric("Total No Cumplidos", len(result.requisitos_finales_no_cumplidos))
    
    # Mensaje de estado semántico final
    if result.descartado_final:
        st.markdown("""
        <div style="background: linear-gradient(90deg, rgba(198, 40, 40, 0.1) 0%, rgba(198, 40, 40, 0.02) 100%);
                    padding: 1rem 1.25rem; border-radius: 8px; margin: 1rem 0;
                    border-left: 4px solid #C62828;">
            <p style="margin: 0; color: #C62828; font-weight: 600; font-size: 1rem;">
                Candidato descartado - No cumple requisitos obligatorios
            </p>
        </div>
        """, unsafe_allow_html=True)
    elif result.puntuacion_final >= 50:
        st.markdown("""
        <div style="background: linear-gradient(90deg, rgba(46, 125, 50, 0.1) 0%, rgba(46, 125, 50, 0.02) 100%);
                    padding: 1rem 1.25rem; border-radius: 8px; margin: 1rem 0;
                    border-left: 4px solid #2E7D32;">
            <p style="margin: 0; color: #2E7D32; font-weight: 600; font-size: 1rem;">
                Candidato aprobado - Cumple con el perfil requerido
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background: linear-gradient(90deg, rgba(255, 152, 0, 0.1) 0%, rgba(255, 152, 0, 0.02) 100%);
                    padding: 1rem 1.25rem; border-radius: 8px; margin: 1rem 0;
                    border-left: 4px solid #FF9800;">
            <p style="margin: 0; color: #E65100; font-weight: 600; font-size: 1rem;">
                Candidato en revisión - Requiere evaluación adicional
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Resumen ejecutivo
    st.markdown("#### Resumen Ejecutivo")
    st.info(result.resumen_evaluacion)
    
    # Requisitos cumplidos finales
    if result.requisitos_finales_cumplidos:
        with st.expander(f"Requisitos Cumplidos ({len(result.requisitos_finales_cumplidos)})"):
            for req in result.requisitos_finales_cumplidos:
                req_type_val = req.tipo.value if hasattr(req.tipo, 'value') else str(req.tipo)
                tipo = format_requirement_type_text(req_type_val)
                col_text, col_type = st.columns([4, 1])
                with col_text:
                    st.markdown(f"- **{req.descripcion}**")
                with col_type:
                    st.caption(tipo)
                if req.evidencia:
                    st.caption(f"   {req.evidencia[:150]}...")
    
    # Requisitos no cumplidos finales
    if result.requisitos_finales_no_cumplidos:
        with st.expander(f"Requisitos No Cumplidos ({len(result.requisitos_finales_no_cumplidos)})"):
            for req in result.requisitos_finales_no_cumplidos:
                req_type_val = req.tipo.value if hasattr(req.tipo, 'value') else str(req.tipo)
                tipo = format_requirement_type_text(req_type_val)
                color = VELORA_ERROR if req_type_val == "obligatory" else VELORA_WARNING
                st.markdown(
                    f"- <span style='color:{color};font-size:0.75rem;'>[{tipo}]</span> **{req.descripcion}**", 
                    unsafe_allow_html=True
                )


def stream_text(text: str, delay: float = 0.02) -> Generator[str, None, None]:
    """Genera texto carácter por carácter para efecto de streaming simulado (backup)."""
    for char in text:
        yield char
        time.sleep(delay)


def render_agentic_interview():
    """
    Chatbot agéntico conversacional con streaming REAL del LLM para Fase 2.
    Implementa streaming token-by-token desde el modelo de lenguaje.
    """
    # AgenticInterviewer ya importado a nivel de módulo desde backend
    
    # Obtener estado de la entrevista
    phase1_result = st.session_state.get('phase1_result')
    user_name = st.session_state.get('user_id', 'candidato')
    cv_context = st.session_state.get('cv_text', '')
    
    if not phase1_result:
        st.error("No hay resultados de Fase 1 disponibles")
        return
    
    # Inicializar entrevistador agéntico si no existe
    if 'agentic_interviewer' not in st.session_state:
        st.session_state['agentic_interviewer'] = AgenticInterviewer(
            proveedor=st.session_state.get('provider') or 'openai',
            nombre_modelo=st.session_state.get('model_name') or 'gpt-4o-mini',
            api_key=st.session_state.get('api_key'),
            temperatura=0.7
        )
        # Inicializar entrevista (usar alias compatible)
        st.session_state['agentic_interviewer'].inicializar_entrevista(
            nombre_candidato=user_name,
            resultado_fase1=phase1_result,
            contexto_cv=cv_context
        )
        st.session_state['agentic_chat_state'] = 'greeting'
        st.session_state['agentic_current_q'] = 0
        st.session_state['agentic_history'] = []
    
    interviewer: AgenticInterviewer = st.session_state['agentic_interviewer']
    state = interviewer.get_state()
    current_idx = st.session_state.get('agentic_current_q', 0)
    chat_history = st.session_state.get('agentic_history', [])
    total_questions = state['total_requirements']
    chat_state = st.session_state.get('agentic_chat_state', 'greeting')
    
    # CSS para el chat agéntico moderno
    st.markdown(f"""
    <style>
        .agent-header {{
            background: linear-gradient(135deg, {VELORA_PRIMARY}12 0%, {VELORA_SECONDARY}08 100%);
            border-radius: 12px;
            padding: 1rem 1.25rem;
            margin-bottom: 1.5rem;
            border-left: 4px solid {VELORA_PRIMARY};
        }}
        .agent-avatar {{
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, {VELORA_PRIMARY}, {VELORA_SECONDARY});
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 700;
            font-size: 1.1rem;
            margin-right: 0.75rem;
        }}
        .agent-message {{
            background: linear-gradient(135deg, #f8f9fa 0%, #f0f2f4 100%);
            border-radius: 0 16px 16px 16px;
            padding: 1rem 1.25rem;
            margin: 0.75rem 0;
            max-width: 88%;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
            border-left: 3px solid {VELORA_PRIMARY}40;
        }}
        .user-message {{
            background: linear-gradient(135deg, {VELORA_PRIMARY}15 0%, {VELORA_SECONDARY}20 100%);
            border-radius: 16px 16px 0 16px;
            padding: 1rem 1.25rem;
            margin: 0.75rem 0 1rem auto;
            max-width: 85%;
            margin-left: auto;
            text-align: right;
            border-right: 3px solid {VELORA_PRIMARY};
        }}
        .progress-pills {{
            display: flex;
            gap: 6px;
            margin: 0.5rem 0;
        }}
        .progress-pill {{
            width: 24px;
            height: 6px;
            border-radius: 3px;
            background: #e0e0e0;
            transition: all 0.3s ease;
        }}
        .progress-pill.completed {{ background: linear-gradient(90deg, {VELORA_PRIMARY}, {VELORA_SECONDARY}); }}
        .progress-pill.current {{ background: {VELORA_PRIMARY}; animation: pulse 1.5s ease-in-out infinite; }}
        @keyframes pulse {{
            0%, 100% {{ opacity: 0.6; }}
            50% {{ opacity: 1; }}
        }}
        .streaming-cursor {{
            display: inline-block;
            width: 2px;
            height: 1em;
            background: {VELORA_PRIMARY};
            animation: blink 1s infinite;
            margin-left: 2px;
        }}
        @keyframes blink {{
            0%, 50% {{ opacity: 1; }}
            51%, 100% {{ opacity: 0; }}
        }}
    </style>
    """, unsafe_allow_html=True)
    
    # Header del agente
    st.markdown(f"""
    <div class="agent-header">
        <div style="display: flex; align-items: center;">
            <div class="agent-avatar">V</div>
            <div>
                <p style="margin: 0; font-weight: 600; color: {VELORA_DARK}; font-size: 1rem;">Asistente de Entrevista Velora</p>
                <p style="margin: 0.15rem 0 0 0; color: {VELORA_GRAY}; font-size: 0.8rem;">
                    Evaluando {total_questions} requisitos pendientes - Streaming en tiempo real
                </p>
            </div>
        </div>
        <div class="progress-pills" style="margin-top: 0.75rem;">
            {"".join([f'<div class="progress-pill {"completed" if i < current_idx else "current" if i == current_idx else ""}"></div>' for i in range(total_questions)])}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Mostrar historial de conversación
    for entry in chat_history:
        if entry['role'] == 'assistant':
            st.markdown(f"""
            <div class="agent-message">
                <p style="margin: 0; color: #333; font-size: 0.95rem;">{entry['content']}</p>
                {f'<p style="margin: 0.5rem 0 0 0; font-size: 0.7rem; color: #888; font-style: italic;">Evaluando: {entry["requirement"]}</p>' if entry.get('requirement') else ''}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="user-message">
                <p style="margin: 0; color: #333;">{entry['content']}</p>
            </div>
            """, unsafe_allow_html=True)
    
    # === FASE: SALUDO ===
    if chat_state == 'greeting':
        st.markdown('<div class="agent-message">', unsafe_allow_html=True)
        message_container = st.empty()
        
        # Streaming REAL del LLM
        full_greeting = ""
        try:
            for token in interviewer.stream_greeting():
                full_greeting += token
                message_container.markdown(f"**{full_greeting}**<span class='streaming-cursor'></span>", unsafe_allow_html=True)
            message_container.markdown(f"**{full_greeting}**")
        except Exception as e:
            full_greeting = f"Hola {user_name}, he revisado tu CV y tengo {total_questions} pregunta(s) que necesito hacerte. Comenzamos?"
            message_container.markdown(f"**{full_greeting}**")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Guardar en historial y cambiar estado
        chat_history.append({'role': 'assistant', 'content': full_greeting})
        st.session_state['agentic_history'] = chat_history
        st.session_state['agentic_chat_state'] = 'questioning'
        time.sleep(0.8)
        st.rerun()
    
    # === FASE: PREGUNTAS ===
    elif chat_state == 'questioning' and current_idx < total_questions:
        # Verificar si necesitamos hacer streaming de la pregunta
        streaming_key = f'streamed_agentic_q_{current_idx}'
        
        if not st.session_state.get(streaming_key):
            st.markdown('<div class="agent-message">', unsafe_allow_html=True)
            question_container = st.empty()
            
            # Streaming REAL de la pregunta desde el LLM
            full_question = ""
            current_req = state['pending_requirements'][current_idx] if current_idx < len(state['pending_requirements']) else None
            
            try:
                for token in interviewer.stream_question(current_idx):
                    full_question += token
                    question_container.markdown(f"**{full_question}**<span class='streaming-cursor'></span>", unsafe_allow_html=True)
                question_container.markdown(f"**{full_question}**")
            except Exception as e:
                req_desc = current_req['description'] if current_req else "este requisito"
                full_question = f"¿Podrías contarme sobre tu experiencia con {req_desc}?"
                question_container.markdown(f"**{full_question}**")
            
            if current_req:
                st.markdown(f"""
                <p style="margin: 0.5rem 0 0 0; font-size: 0.7rem; color: #888; font-style: italic;">
                    Requisito: {current_req['description']}
                </p>
                """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Guardar pregunta en historial
            chat_history.append({
                'role': 'assistant',
                'content': full_question,
                'requirement': current_req['description'] if current_req else ''
            })
            st.session_state['agentic_history'] = chat_history
            st.session_state[streaming_key] = True
            st.session_state['current_question_text'] = full_question
            time.sleep(0.3)
            st.rerun()
        else:
            # Mostrar pregunta guardada
            current_req = state['pending_requirements'][current_idx] if current_idx < len(state['pending_requirements']) else None
            saved_question = st.session_state.get('current_question_text', '')
            
            # Input para respuesta
            with st.form(key=f"agentic_form_{current_idx}", clear_on_submit=True):
                answer = st.text_area(
                    "Tu respuesta:",
                    placeholder="Escribe tu respuesta aquí...",
                    key=f"agentic_input_{current_idx}",
                    label_visibility="collapsed",
                    height=100
                )
                
                col1, col2, col3 = st.columns([2, 1, 2])
                with col2:
                    submit = st.form_submit_button("Enviar", type="primary", use_container_width=True)
            
            if submit and answer.strip():
                # Registrar respuesta en el agente
                interviewer.register_response(current_idx, answer.strip())
                
                # Agregar al historial visual
                chat_history.append({
                    'role': 'user',
                    'content': answer.strip()
                })
                st.session_state['agentic_history'] = chat_history
                st.session_state['agentic_current_q'] = current_idx + 1
                
                # Verificar si terminamos
                if current_idx + 1 >= total_questions:
                    st.session_state['agentic_chat_state'] = 'closing'
                
                st.rerun()
            elif submit:
                st.warning("Por favor, escribe una respuesta antes de continuar.")
    
    # === FASE: CIERRE ===
    elif chat_state == 'closing':
        if not st.session_state.get('agentic_closing_shown'):
            st.markdown('<div class="agent-message">', unsafe_allow_html=True)
            closing_container = st.empty()
            
            # Streaming REAL del cierre
            full_closing = ""
            try:
                for token in interviewer.stream_closing():
                    full_closing += token
                    closing_container.markdown(f"**{full_closing}**<span class='streaming-cursor'></span>", unsafe_allow_html=True)
                closing_container.markdown(f"**{full_closing}**")
            except Exception:
                full_closing = f"Perfecto, {user_name}. Gracias por tus respuestas. Ahora procesare la informacion para completar tu evaluacion."
                closing_container.markdown(f"**{full_closing}**")
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            chat_history.append({'role': 'assistant', 'content': full_closing})
            st.session_state['agentic_history'] = chat_history
            st.session_state['agentic_closing_shown'] = True
            st.session_state['chat_interview_complete'] = True
            
            # Preparar respuestas formateadas para evaluación
            st.session_state['interview_responses_formatted'] = interviewer.get_interview_responses()
            
            time.sleep(1)
            st.rerun()
        else:
            # Ya mostrado el cierre, marcar como completo
            if not st.session_state.get('chat_interview_complete'):
                st.session_state['chat_interview_complete'] = True
                st.rerun()


def get_or_create_evaluator():
    """Recrea el evaluador usando la configuración de sesión."""
    if 'provider' in st.session_state and 'api_key' in st.session_state:
        return CandidateEvaluator(
            proveedor=st.session_state['provider'],
            nombre_modelo=st.session_state.get('model_name'),
            api_key=st.session_state['api_key']
        )
    return None

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
        st.caption("En caso de que se necesite información adicional, contáctenme sin problema o visiten el repositorio de GitHub :)")
    
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
        
        # Botón centrado
        _, col_btn_eval, _ = st.columns([1, 2, 1])
        with col_btn_eval:
            start_eval = st.button("Iniciar Evaluación", type="primary", disabled=not can_evaluate, use_container_width=True)
        
        if start_eval:
            if not cv_text:
                st.error("Proporciona el CV del candidato")
                st.stop()
            
            if not job_offer_text:
                st.error("Proporciona la oferta de empleo")
                st.stop()
            
            # Resetear estado completo (incluye todos los estados del agente)
            keys_to_reset = [
                'evaluation_saved', 'evaluation_completed', 'phase2_started', 
                'phase1_completed', 'chat_interview_complete',
                # Estados del nuevo agente
                'agentic_interviewer', 'agentic_chat_state', 'agentic_current_q',
                'agentic_history', 'agentic_closing_shown', 'interview_responses_formatted',
                'current_question_text'
            ]
            # Eliminar claves de streaming y estados temporales
            for key in list(st.session_state.keys()):
                if key in keys_to_reset or key.startswith('streamed_agentic_q_'):
                    del st.session_state[key]
            
            st.session_state['cv_text'] = cv_text
            st.session_state['job_offer_text'] = job_offer_text
            st.session_state['provider'] = provider
            st.session_state['model_name'] = model_name
            
            try:
                with st.spinner("Inicializando evaluador..."):
                    # Instanciar evaluador localmente
                    evaluator = CandidateEvaluator(
                        proveedor=provider,
                        nombre_modelo=model_name,
                        api_key=api_key
                    )
                
                # Instancia separada para análisis fase 1
                phase1_analyzer = Phase1Analyzer(
                    proveedor=provider,
                    nombre_modelo=model_name,
                    api_key=api_key,
                    usar_matching_semantico=use_semantic,
                    usar_langgraph=use_langgraph
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
                    
                    total_reqs = len(phase1_result.requisitos_cumplidos) + len(phase1_result.requisitos_no_cumplidos)
                    st.write(f"Análisis completado: {total_reqs} requisitos evaluados")
                    st.write(f"Score inicial: **{phase1_result.puntuacion:.1f}%**")
                    
                    progress_bar.progress(100, text="Completado")
                    status.update(label="Fase 1 completada", state="complete")
                    
                    st.session_state['phase1_result'] = phase1_result
                    st.session_state['phase1_completed'] = True
                
                # Guardar si no hay Fase 2
                user_id_phase1 = st.session_state.get('user_id', '')
                should_save_phase1 = phase1_result.descartado or not phase1_result.requisitos_faltantes
                
                if user_id_phase1 and should_save_phase1:
                    try:
                        memory = UserMemory()
                        enriched = memory.guardar_evaluacion_fase1(
                            id_usuario=user_id_phase1,
                            texto_oferta=job_offer_text,
                            texto_cv=cv_text,
                            resultado_fase1=phase1_result,
                            proveedor=provider,
                            modelo=model_name
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
            
            if not phase1_result.descartado and phase1_result.requisitos_faltantes:
                st.markdown("---")
                st.markdown("### Fase 2: Entrevista")
                st.info(f"Se encontraron **{len(phase1_result.requisitos_faltantes)} requisito(s)** no verificables en el CV. "
                        f"Inicia una entrevista conversacional para obtener más información.")
                
                # Botón centrado
                _, col_btn_int, _ = st.columns([1, 2, 1])
                with col_btn_int:
                    start_interview = st.button("Iniciar Entrevista Conversacional", type="primary", use_container_width=True)
                
                if start_interview:
                    # Limpiar estados previos del agente
                    keys_to_clean = [
                        'agentic_interviewer', 'agentic_chat_state', 'agentic_current_q',
                        'agentic_history', 'agentic_closing_shown', 'interview_responses_formatted'
                    ]
                    for key in list(st.session_state.keys()):
                        if key in keys_to_clean or key.startswith('streamed_agentic_q_'):
                            del st.session_state[key]
                    
                    st.session_state['phase2_started'] = True
                    st.rerun()
            
            elif phase1_result.descartado:
                # Candidato descartado en Fase 1 - Mostrar botón de Nueva Evaluación
                st.markdown("---")
                
                # Botón centrado con estilo consistente
                _, col_btn_new, _ = st.columns([1, 2, 1])
                with col_btn_new:
                    if st.button("Nueva Evaluación", type="primary", use_container_width=True, key="new_eval_phase1"):
                        keys_to_keep = ['user_id', 'provider', 'model_name', 'api_key', 'last_url']
                        keys_to_clear = [k for k in st.session_state.keys() if k not in keys_to_keep]
                        for key in keys_to_clear:
                            del st.session_state[key]
                        st.rerun()
        
        # ===================================================================
        # FASE 2: Entrevista conversacional
        # ===================================================================
        if st.session_state.get('phase2_started') and not st.session_state.get('evaluation_completed'):
            st.markdown("---")
            render_agentic_interview()
            
            if st.session_state.get('chat_interview_complete'):
                phase1_result = st.session_state['phase1_result']
                evaluator = get_or_create_evaluator()
                
                # Obtener respuestas del agente o del formato legacy
                formatted_responses = st.session_state.get('interview_responses_formatted')
                
                if not formatted_responses:
                    # Fallback: intentar obtener del agente
                    interviewer = st.session_state.get('agentic_interviewer')
                    if interviewer:
                        formatted_responses = interviewer.get_interview_responses()
                
                if evaluator and formatted_responses:
                    with st.spinner("Procesando entrevista y generando resultado final..."):
                        resultado = evaluator.reevaluate_with_interview(phase1_result, formatted_responses)
                        
                        st.session_state['evaluation_result'] = resultado
                        st.session_state['evaluation_completed'] = True
                        st.session_state['phase2_started'] = False
                    
                    st.success("Evaluación completada")
                    st.rerun()
                elif not formatted_responses:
                    st.error("No se encontraron respuestas de la entrevista.")
                else:
                    st.error("Error crítico: Sesión perdida. Recargue la página.")
        
        # ===================================================================
        # Resultados finales
        # ===================================================================
        if st.session_state.get('evaluation_completed'):
            resultado = st.session_state['evaluation_result']
            
            st.markdown("---")
            
            if resultado.fase2_completada and resultado.respuestas_entrevista:
                display_interview_responses(resultado.respuestas_entrevista)
            
            st.markdown("---")
            display_final_results(resultado)
            
            user_id_for_save = st.session_state.get('user_id', '')
            evaluation_saved_flag = st.session_state.get('evaluation_saved', False)
            
            if user_id_for_save and not evaluation_saved_flag:
                try:
                    memory = UserMemory()
                    enriched = create_enriched_evaluation(
                        id_usuario=user_id_for_save,
                        texto_oferta=st.session_state.get('job_offer_text', ''),
                        texto_cv=st.session_state.get('cv_text', ''),
                        resultado_fase1=resultado.resultado_fase1,
                        fase2_completada=resultado.fase2_completada,
                        resultado_evaluacion=resultado,
                        proveedor=st.session_state.get('provider', provider),
                        modelo=st.session_state.get('model_name', model_name)
                    )
                    memory.save_evaluation(enriched)
                    st.session_state['evaluation_saved'] = True
                    st.success("Evaluación guardada en tu historial")
                except Exception as e:
                    st.error(f"Error al guardar: {str(e)}")
            
            st.markdown("---")
            
            # Botón centrado con estilo consistente
            _, col_btn_new, _ = st.columns([1, 2, 1])
            with col_btn_new:
                if st.button("Nueva Evaluación", type="primary", use_container_width=True):
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
                
                # Contenedor del historial con spacing compacto
                st.markdown('<div class="history-container">', unsafe_allow_html=True)
                
                for i, eval_data in enumerate(display_evals[:10], 1):
                    title = eval_data.get('job_offer_title', 'Oferta de empleo')
                    score = eval_data.get('score', 0)
                    status = eval_data.get('status', 'unknown')
                    timestamp = eval_data.get('timestamp', 'N/A')
                    if timestamp and len(timestamp) >= 10:
                        timestamp = timestamp[:10]
                        
                    phase = eval_data.get('phase_completed', 'phase1')
                    
                    # Determinar clase CSS según estado
                    if status == "approved":
                        item_class = "history-item-approved"
                        status_card_class = "status-approved"
                        status_label = "APROBADO"
                    elif status == "rejected":
                        item_class = "history-item-rejected"
                        status_card_class = "status-rejected"
                        status_label = "RECHAZADO"
                    else:
                        item_class = "history-item-phase1"
                        status_card_class = "status-phase1"
                        status_label = "FASE 1"
                    
                    # Clase para fase
                    phase_card_class = "status-phase2" if phase == "phase2" else "status-phase1"
                    phase_label = "FASE 2" if phase == "phase2" else "FASE 1"
                    
                    # Título del expander
                    expander_title = f"#{i} · {title[:40]}... · {score:.1f}% · {timestamp}"
                    
                    # Contenedor con degradado según estado
                    st.markdown(f'<div class="history-item {item_class}">', unsafe_allow_html=True)
                    
                    with st.expander(expander_title):
                        # Grid de métricas uniformes
                        met1, met2, met3, met4 = st.columns(4)
                        
                        with met1:
                            st.markdown(f'''
                            <div class="history-metric-card">
                                <div class="history-metric-label">Puntuación</div>
                                <div class="history-metric-value">{score:.1f}%</div>
                            </div>
                            ''', unsafe_allow_html=True)
                        
                        with met2:
                            st.markdown(f'''
                            <div class="history-metric-card {status_card_class}">
                                <div class="history-metric-label">Estado</div>
                                <div class="history-metric-value">{status_label}</div>
                            </div>
                            ''', unsafe_allow_html=True)
                        
                        with met3:
                            st.markdown(f'''
                            <div class="history-metric-card {phase_card_class}">
                                <div class="history-metric-label">Fase</div>
                                <div class="history-metric-value">{phase_label}</div>
                            </div>
                            ''', unsafe_allow_html=True)
                        
                        with met4:
                            fulfilled = eval_data.get('fulfilled_count', 0)
                            total = eval_data.get('total_requirements', 0)
                            st.markdown(f'''
                            <div class="history-metric-card">
                                <div class="history-metric-label">Requisitos</div>
                                <div class="history-metric-value">{fulfilled}/{total}</div>
                            </div>
                            ''', unsafe_allow_html=True)
                        
                        st.markdown("---")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("**Detalles:**")
                            st.write(f"• Obligatorios: {eval_data.get('obligatory_requirements', 0)}")
                            st.write(f"• Opcionales: {eval_data.get('optional_requirements', 0)}")
                            st.write(f"• Cumplidos: {fulfilled}")
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
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                
                # Cerrar contenedor del historial
                st.markdown('</div>', unsafe_allow_html=True)
                
                st.markdown("---")
                st.markdown("#### Asistente de Historial")
                st.caption("Consulta información sobre tu historial de evaluaciones.")
                
                # Input para consulta directa
                query = st.text_input(
                    "Consulta",
                    placeholder="Ej: ¿Por qué fui rechazado? ¿Cuál es mi puntuación promedio?",
                    key="rag_query",
                    label_visibility="collapsed"
                )
                
                if query:
                    with st.spinner("Buscando en tu historial..."):
                        response = ""
                        try:
                            llm = LLMFactory.create_llm(
                                provider=st.session_state.get('provider') or 'openai',
                                model_name=st.session_state.get('model_name') or 'gpt-4o-mini',
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