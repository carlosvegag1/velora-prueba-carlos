# Dockerfile Multi-Stage para Sistema de Evaluación de Candidatos con IA

FROM python:3.11-slim-bookworm AS base

LABEL description="Sistema de evaluacion de candidatos con LangChain, LangGraph y RAG"
LABEL version="2.1.0"

# Variables de entorno para Python y Playwright
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias para Playwright y compilacion
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Dependencias de compilacion
    build-essential \
    # Dependencias para Playwright (Chromium)
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
    # Utilidades
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

FROM base AS dependencies

# Copiar archivos de dependencias
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Instalar navegador Chromium para Playwright en directorio global
RUN playwright install chromium --with-deps \
    && chmod -R 755 /ms-playwright

FROM dependencies AS production

# Crear usuario no-root para seguridad
RUN groupadd --gid 1000 velora \
    && useradd --uid 1000 --gid 1000 --shell /bin/bash --create-home velora

# Copiar codigo fuente de la aplicacion
COPY --chown=velora:velora . .

# Dar permisos de ejecución al script de entrada
RUN chmod +x /app/entrypoint.sh

# Crear directorios para datos persistentes
RUN mkdir -p /app/data/memoria_usuario /app/data/vectores \
    && chown -R velora:velora /app/data

# Configurar Streamlit para produccion
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

# Cambiar al usuario no-root
USER velora

# Exponer puerto de Streamlit
EXPOSE 8501

# Health check para orquestadores
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Comando de inicio
ENTRYPOINT ["/app/entrypoint.sh"]

