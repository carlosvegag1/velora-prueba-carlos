# Multi-stage build para optimizar tamaño final de imagen

FROM python:3.11-slim-bookworm AS base

LABEL description="Sistema de evaluacion de candidatos con LangChain, LangGraph y RAG"
LABEL version="2.1.0"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app

# Dependencias del sistema para Playwright (Chromium) y compilacion
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

FROM base AS dependencies

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install chromium --with-deps \
    && chmod -R 755 /ms-playwright

FROM dependencies AS production

# Usuario no-root por seguridad
RUN groupadd --gid 1000 velora \
    && useradd --uid 1000 --gid 1000 --shell /bin/bash --create-home velora

COPY --chown=velora:velora . .

RUN mkdir -p /app/data/memoria_usuario /app/data/vectores \
    && chown -R velora:velora /app/data

# Configuracion Streamlit para produccion
RUN mkdir -p /home/velora/.streamlit
COPY --chown=velora:velora <<EOF /home/velora/.streamlit/config.toml
[server]
port = 8501
address = "0.0.0.0"
headless = true
enableCORS = false
enableXsrfProtection = true
maxUploadSize = 10

[browser]
gatherUsageStats = false

[theme]
base = "light"
primaryColor = "#00B4D8"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"
EOF

USER velora
EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1

CMD streamlit run frontend/streamlit_app.py --server.port=8501 --server.address=0.0.0.0
