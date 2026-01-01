# Guía de Despliegue con Docker

> **Sistema de Evaluación de Candidatos con IA**  
> Guía completa para ejecución con Docker

---

## Inicio Rápido (3 Pasos)

### 1. Configurar API Key

```bash
# Copiar archivo de ejemplo
cp .env.example .env

# Editar y añadir tu API key
# Windows: notepad .env
# Linux/Mac: nano .env
```

Contenido mínimo:
```env
OPENAI_API_KEY=sk-tu_api_key_aqui
```

### 2. Construir y Ejecutar

```bash
docker compose up --build
```

### 3. Acceder

Abrir navegador en **http://localhost:8501**

> 💡 **Primera ejecución**: Tarda 3-5 minutos (descarga dependencias + Chromium)

---

## Qué Se Instala Automáticamente

El Dockerfile gestiona **todas las dependencias**:

| Componente | ¿Manual? | En Docker |
|------------|----------|-----------|
| Python 3.11 | ✅ Sí | ✅ Automático |
| Dependencias pip | ✅ Sí | ✅ Automático |
| Playwright | ✅ Sí | ✅ Automático |
| Chromium | ✅ Sí (comando extra) | ✅ **Automático** |
| Configuración Streamlit | ✅ Manual | ✅ Automático |

**Resultado**: No necesitas instalar nada excepto Docker.

---

## Arquitectura del Dockerfile

### Multi-Stage Build

El Dockerfile usa 3 etapas para optimizar:

```dockerfile
# Etapa 1: Base
FROM python:3.11-slim-bookworm AS base
# Instala dependencias del sistema (librerías para Chromium)

# Etapa 2: Dependencies
FROM base AS dependencies
RUN pip install -r requirements.txt
RUN playwright install chromium --with-deps  # ← Automático

# Etapa 3: Production
FROM dependencies AS production
# Copia código y configura usuario no-root
```

### Playwright Chromium

La línea clave:
```dockerfile
RUN playwright install chromium --with-deps
```

Esto instala automáticamente:
- Navegador Chromium headless
- Todas las dependencias del sistema necesarias
- Drivers para Playwright

**Beneficio**: Funciona el scraping de URLs protegidas (LinkedIn, Indeed, portales corporativos) sin configuración adicional.

---

## Comandos Docker Compose

### Iniciar el Sistema

```bash
# Primera vez (construye la imagen)
docker compose up --build

# Siguientes veces (usa imagen existente)
docker compose up

# En segundo plano (detached)
docker compose up -d
```

### Detener el Sistema

```bash
# Si está en primer plano
Ctrl+C

# Luego, detener servicios
docker compose down

# Detener y eliminar volúmenes (reinicio completo)
docker compose down -v
```

### Ver Logs

```bash
# Logs en tiempo real
docker compose logs -f

# Logs del servicio velora
docker compose logs -f velora

# Últimas 100 líneas
docker compose logs --tail=100 velora
```

### Reconstruir Imagen

```bash
# Reconstruir sin caché (si cambias Dockerfile o requirements.txt)
docker compose build --no-cache

# Reconstruir y ejecutar
docker compose up --build
```

---

## Configuración Avanzada

### Variables de Entorno

Todas en `.env`:

```env
# ===== OBLIGATORIO =====
OPENAI_API_KEY=sk-...

# ===== OPCIONAL =====
# Otros proveedores
GOOGLE_API_KEY=...
ANTHROPIC_API_KEY=...

# Observabilidad
LANGSMITH_API_KEY=...
LANGCHAIN_PROJECT=velora-evaluator

# Puerto (default: 8501)
VELORA_PORT=8502
```

### Cambiar Puerto

```env
# En .env
VELORA_PORT=8080
```

Luego:
```bash
docker compose down
docker compose up
```

Acceder a: **http://localhost:8080**

### Recursos del Contenedor

Por defecto en `docker-compose.yml`:

```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 4G
    reservations:
      cpus: '0.5'
      memory: 1G
```

**Modificar si necesitas**:
```yaml
# Más memoria para embeddings grandes
memory: 8G
```

---

## Persistencia de Datos

### Volumen de Datos

Docker crea un volumen persistente:

```yaml
volumes:
  velora-data:
    driver: local
    name: velora-persistent-data
```

**Datos guardados**:
- `data/memoria_usuario/*.json` - Historial de evaluaciones
- `data/vectores/*/` - Índices FAISS de embeddings

### Ubicación del Volumen

```bash
# Ver volúmenes
docker volume ls | grep velora

# Inspeccionar ubicación
docker volume inspect velora-persistent-data
```

### Backup de Datos

```bash
# Copiar datos del contenedor al host
docker cp $(docker compose ps -q velora):/app/data ./backup_data

# Restaurar datos
docker cp ./backup_data/. $(docker compose ps -q velora):/app/data
```

---

## Health Check

El contenedor tiene health check automático:

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1
```

**Ver estado**:
```bash
docker compose ps

# Output:
# NAME       STATUS              PORTS
# velora-app healthy           0.0.0.0:8501->8501/tcp
```

---

## Solución de Problemas

### Puerto Ya en Uso

**Error**: `bind: address already in use`

**Solución**:
```bash
# Opción 1: Cambiar puerto en .env
echo "VELORA_PORT=8502" >> .env

# Opción 2: Encontrar y detener proceso
# Linux/Mac:
lsof -ti:8501 | xargs kill -9
# Windows:
netstat -ano | findstr :8501
taskkill /PID <PID> /F
```

### Imagen No Se Actualiza

**Problema**: Cambios en código no reflejan

**Solución**:
```bash
# Reconstruir sin caché
docker compose build --no-cache
docker compose up
```

### Error de Permisos en data/

**Problema**: No puede escribir en `data/memoria_usuario`

**Causa**: Usuario no-root en contenedor

**Solución**:
```bash
# Dar permisos al directorio data/ en host
chmod -R 777 data/
```

### Chromium No Funciona

**Problema**: Scraping de URLs falla

**Verificación**:
```bash
# Entrar al contenedor
docker compose exec velora bash

# Verificar Playwright
playwright --version

# Verificar Chromium
ls /home/velora/.cache/ms-playwright/
```

**Solución**: Reconstruir imagen
```bash
docker compose build --no-cache
```

---

## Ejecución en Producción

### Docker Compose para Producción

Crear `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  velora:
    restart: always
    
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
    
    deploy:
      replicas: 1
      update_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
```

**Ejecutar**:
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Con Nginx (Reverse Proxy)

```nginx
server {
    listen 80;
    server_name velora.ejemplo.com;
    
    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

---

## Comandos Útiles

```bash
# Ver uso de recursos
docker stats velora-app

# Entrar al contenedor (debugging)
docker compose exec velora bash

# Ver logs de Streamlit
docker compose logs -f velora | grep "Streamlit"

# Reiniciar solo el servicio
docker compose restart velora

# Ver configuración efectiva
docker compose config

# Limpiar todo (imágenes, volúmenes, redes)
docker system prune -a --volumes
```

---

## Comparación: Docker vs Manual

| Aspecto | Docker | Manual |
|---------|--------|--------|
| **Instalación** | 1 comando | 4-5 comandos |
| **Chromium** | Automático | Manual (`playwright install`) |
| **Python** | Incluido | Debe estar instalado |
| **Dependencias** | Aisladas | En sistema/venv |
| **Portabilidad** | Alta (misma imagen) | Media (depende del sistema) |
| **Tiempo inicial** | 3-5 min (primera vez) | 2-3 min |
| **Updates** | Rebuild | Reinstalar dependencias |

**Recomendación**: Docker para evaluadores, manual para desarrollo.

---

*Guía de despliegue para prueba técnica de Velora*  
*Carlos Vega | Diciembre 2024*
