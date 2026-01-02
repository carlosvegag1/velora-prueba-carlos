# Documentación: `Dockerfile` y `docker-compose.yml`

## Información General

| Archivo | Propósito |
|---------|-----------|
| `Dockerfile` | Define cómo construir la imagen |
| `docker-compose.yml` | Define cómo ejecutar los servicios |

---

## ¿Qué es Docker?

Docker permite **empaquetar** una aplicación con todas sus dependencias en un **contenedor** que funciona igual en cualquier máquina.

```
Sin Docker:
- "En mi máquina funciona" 🤷
- Diferentes versiones de Python
- Dependencias conflictivas

Con Docker:
- Mismo entorno en desarrollo y producción ✅
- Todas las dependencias incluidas
- Despliegue reproducible
```

---

## Dockerfile Explicado

### Línea por Línea

```dockerfile
# ============================================
# IMAGEN BASE
# ============================================
FROM python:3.11-slim-bookworm AS base
```

| Parte | Significado |
|-------|-------------|
| `FROM` | Imagen de partida |
| `python:3.11-slim-bookworm` | Python 3.11 en Debian 12 (mínimo) |
| `AS base` | Nombre de esta etapa |

**¿Por qué `slim`?**
- `python:3.11` → ~900MB
- `python:3.11-slim` → ~120MB

---

```dockerfile
# ============================================
# DEPENDENCIAS DEL SISTEMA
# ============================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Para Playwright
    libnss3 \
    libnspr4 \
    libdbus-1-3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    # Utilidades
    curl \
    && rm -rf /var/lib/apt/lists/*
```

**¿Qué son estas librerías?**

Son dependencias de Chromium (usado por Playwright):
- `libnss3`: Seguridad de red
- `libatk*`: Accesibilidad
- `libdrm2`: Renderizado
- etc.

**¿Por qué `--no-install-recommends`?**

Solo instala dependencias estrictas, no "recomendadas". Reduce tamaño.

**¿Por qué `rm -rf /var/lib/apt/lists/*`?**

Elimina la caché de apt. Ya no la necesitamos y ocupa espacio.

---

```dockerfile
# ============================================
# DIRECTORIO DE TRABAJO
# ============================================
WORKDIR /app
```

Establece `/app` como directorio actual. Todos los comandos siguientes se ejecutan aquí.

---

```dockerfile
# ============================================
# DEPENDENCIAS PYTHON
# ============================================
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
```

**¿Por qué copiar requirements.txt separado?**

Docker usa **capas** con caché. Si el código cambia pero requirements.txt no, esta capa se reutiliza y no reinstala todo.

```
Cambio en código:
  COPY requirements.txt → ✓ Caché (no reinstala)
  pip install → ✓ Caché
  COPY . → ✗ Rebuild
  
Cambio en requirements.txt:
  COPY requirements.txt → ✗ Rebuild
  pip install → ✗ Rebuild (reinstala todo)
  COPY . → ✗ Rebuild
```

**¿Por qué `--no-cache-dir`?**

Pip guarda paquetes descargados en caché. En Docker no lo necesitamos, ahorra espacio.

---

```dockerfile
# ============================================
# PLAYWRIGHT
# ============================================
RUN playwright install chromium --with-deps
```

Instala Chromium para Playwright. `--with-deps` instala dependencias adicionales de sistema que puedan faltar.

---

```dockerfile
# ============================================
# USUARIO NO-ROOT
# ============================================
RUN useradd --create-home --uid 1000 velora
USER velora
```

**¿Por qué usuario no-root?**

- **Seguridad**: Si alguien explota una vulnerabilidad, tiene permisos limitados
- **Buenas prácticas**: Estándar en contenedores de producción

```
Como root:
- Puede modificar cualquier archivo del sistema
- Puede instalar software malicioso
- Más impacto si hay un exploit

Como velora (no-root):
- Solo puede acceder a /app y /home/velora
- No puede instalar software del sistema
- Daño limitado si hay un exploit
```

---

```dockerfile
# ============================================
# CÓDIGO DE APLICACIÓN
# ============================================
COPY --chown=velora:velora . .
```

Copia todo el código al contenedor. `--chown=velora:velora` hace que los archivos pertenezcan al usuario velora.

---

```dockerfile
# ============================================
# CONFIGURACIÓN DE STREAMLIT
# ============================================
RUN mkdir -p /home/velora/.streamlit

COPY --chown=velora:velora <<EOF /home/velora/.streamlit/config.toml
[server]
headless = true
enableCORS = false
enableXsrfProtection = false
address = "0.0.0.0"
port = 8501

[browser]
gatherUsageStats = false
EOF
```

**¿Qué es este archivo de configuración?**

| Setting | Valor | Significado |
|---------|-------|-------------|
| `headless` | true | Sin navegador (servidor) |
| `enableCORS` | false | Desactiva CORS (simplifica despliegue) |
| `address` | 0.0.0.0 | Escucha en todas las interfaces |
| `port` | 8501 | Puerto estándar de Streamlit |
| `gatherUsageStats` | false | No enviar telemetría |

---

```dockerfile
# ============================================
# PUERTOS Y HEALTH CHECK
# ============================================
EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1
```

**EXPOSE**: Documenta qué puerto usa la aplicación (no abre el puerto realmente).

**HEALTHCHECK**: Docker verifica periódicamente si la app está viva.

| Parámetro | Valor | Significado |
|-----------|-------|-------------|
| `--interval` | 30s | Verificar cada 30 segundos |
| `--timeout` | 10s | Máximo 10 segundos para responder |
| `--start-period` | 5s | Esperar 5s antes de empezar a verificar |
| `--retries` | 3 | 3 fallos = contenedor unhealthy |

---

```dockerfile
# ============================================
# COMANDO DE INICIO
# ============================================
CMD ["python", "-m", "streamlit", "run", "frontend/streamlit_app.py"]
```

Comando por defecto al iniciar el contenedor.

---

## docker-compose.yml Explicado

```yaml
version: '3.8'

services:
  velora:
    build:
      context: .
      dockerfile: Dockerfile
```

| Campo | Significado |
|-------|-------------|
| `version` | Versión del formato de compose |
| `services` | Lista de contenedores |
| `velora` | Nombre del servicio |
| `build.context` | Directorio de build (donde está el Dockerfile) |

---

```yaml
    container_name: velora-evaluator
    
    env_file:
      - .env
```

| Campo | Significado |
|-------|-------------|
| `container_name` | Nombre del contenedor (en `docker ps`) |
| `env_file` | Archivo con variables de entorno |

**¿Qué hay en `.env`?**
```
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=AIza...
ANTHROPIC_API_KEY=sk-ant-...
LANGSMITH_API_KEY=ls-...
```

---

```yaml
    environment:
      - STREAMLIT_SERVER_ADDRESS=0.0.0.0
      - STREAMLIT_SERVER_PORT=8501
```

Variables de entorno adicionales (sobrescriben las de `.env` si hay conflicto).

---

```yaml
    ports:
      - "8501:8501"
```

**Mapeo de puertos**: `puerto_host:puerto_contenedor`

```
Host (tu máquina)    Contenedor
      8501    ─────►    8501
      
Accedes en: http://localhost:8501
```

---

```yaml
    volumes:
      - velora-data:/app/data
```

**Volume**: Persiste datos entre reinicios del contenedor.

```
Contenedor                    Host
/app/data/  ◄─────────────► velora-data (volume Docker)
```

Sin volume, si el contenedor se elimina, los datos de `/app/data` se pierden.

---

```yaml
    deploy:
      resources:
        limits:
          memory: 4G
        reservations:
          memory: 1G
```

| Campo | Valor | Significado |
|-------|-------|-------------|
| `limits.memory` | 4G | Máximo 4GB de RAM |
| `reservations.memory` | 1G | Garantiza al menos 1GB |

---

```yaml
    restart: unless-stopped
```

Política de reinicio:

| Valor | Comportamiento |
|-------|----------------|
| `no` | Nunca reinicia |
| `always` | Siempre reinicia |
| `on-failure` | Solo si falla (exit code != 0) |
| `unless-stopped` | Reinicia a menos que se detenga manualmente |

---

```yaml
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
```

Igual que en el Dockerfile, pero configurable desde compose.

---

```yaml
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

| Campo | Valor | Significado |
|-------|-------|-------------|
| `driver` | json-file | Formato de logs |
| `max-size` | 10m | Máximo 10MB por archivo |
| `max-file` | 3 | Máximo 3 archivos de log |

Sin esto, los logs podrían crecer indefinidamente.

---

```yaml
volumes:
  velora-data:
    driver: local

networks:
  default:
    name: velora-network
```

Declara el volume y la red usados.

---

## Comandos de Uso

### Construir Imagen

```bash
docker-compose build
```

O con Docker puro:
```bash
docker build -t velora:latest .
```

### Iniciar Servicio

```bash
docker-compose up -d
```

| Flag | Significado |
|------|-------------|
| `-d` | Detached (en segundo plano) |

### Ver Logs

```bash
docker-compose logs -f velora
```

| Flag | Significado |
|------|-------------|
| `-f` | Follow (mostrar en tiempo real) |

### Detener

```bash
docker-compose down
```

### Detener y Eliminar Datos

```bash
docker-compose down -v
```

`-v` elimina los volumes (pierde datos persistidos).

---

## Diagrama de Arquitectura

```
┌──────────────────────────────────────────────────────────────────┐
│                         HOST                                      │
│                                                                   │
│   ┌───────────────────────────────────────────────────────────┐  │
│   │                    DOCKER                                  │  │
│   │                                                           │  │
│   │   ┌───────────────────────────────────────────────────┐   │  │
│   │   │              CONTENEDOR VELORA                     │   │  │
│   │   │                                                   │   │  │
│   │   │   ┌─────────────────────────────────────────────┐ │   │  │
│   │   │   │              STREAMLIT                       │ │   │  │
│   │   │   │              :8501                           │ │   │  │
│   │   │   └─────────────────────────────────────────────┘ │   │  │
│   │   │                       │                           │   │  │
│   │   │   ┌─────────────────────────────────────────────┐ │   │  │
│   │   │   │              BACKEND                         │ │   │  │
│   │   │   │   - LLM Providers                           │ │   │  │
│   │   │   │   - Playwright/Chromium                     │ │   │  │
│   │   │   │   - FAISS                                   │ │   │  │
│   │   │   └─────────────────────────────────────────────┘ │   │  │
│   │   │                       │                           │   │  │
│   │   │   ┌─────────────────────────────────────────────┐ │   │  │
│   │   │   │          /app/data (volume)                  │ │   │  │
│   │   │   │   - memoria_usuario/                        │ │   │  │
│   │   │   │   - vectores/                               │ │   │  │
│   │   │   └─────────────────────────────────────────────┘ │   │  │
│   │   │                                                   │   │  │
│   │   └───────────────────────────────────────────────────┘   │  │
│   │                           │                               │  │
│   │                     velora-data                           │  │
│   │                     (volume)                              │  │
│   └───────────────────────────────────────────────────────────┘  │
│                               │                                   │
│                         puerto 8501                              │
│                               │                                   │
└───────────────────────────────┼───────────────────────────────────┘
                                │
                                ▼
                        http://localhost:8501
```

---

## Justificación de Diseño

### ¿Por qué imagen multi-stage?

En este caso no usamos multi-stage (build separado), pero podríamos:

```dockerfile
# Stage 1: Build
FROM python:3.11 AS builder
RUN pip install ...

# Stage 2: Runtime (más ligero)
FROM python:3.11-slim
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
```

No lo hacemos porque Playwright necesita las mismas dependencias en build y runtime.

### ¿Por qué usuario no-root?

Principio de **mínimo privilegio**. El contenedor solo necesita leer/escribir en `/app` y `/home/velora`.

### ¿Por qué healthcheck?

Docker (y orquestadores como Kubernetes) pueden:
- Reiniciar contenedores unhealthy automáticamente
- No enviar tráfico a contenedores unhealthy
- Alertar si hay problemas

