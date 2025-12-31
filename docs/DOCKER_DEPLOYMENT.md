# Velora - Guia de Despliegue con Docker

## Descripcion General

Esta guia documenta el proceso de despliegue de Velora usando Docker y Docker Compose.

## Requisitos Previos

- Docker >= 20.10
- Docker Compose >= 2.0
- Al menos 4GB de RAM disponible
- Al menos una API key de proveedor LLM (OpenAI, Google, o Anthropic)

## Estructura de Archivos Docker

```
prueba_tecnica_carlos/
├── Dockerfile              # Imagen multi-stage optimizada
├── docker-compose.yml      # Orquestacion principal
├── docker-compose.prod.yml # Override para produccion
├── .dockerignore           # Exclusiones del contexto de build
└── env.example             # Plantilla de variables de entorno
```

## Inicio Rapido

### 1. Configurar Variables de Entorno

```bash
# Copiar plantilla
cp env.example .env

# Editar con tus API keys
nano .env
```

Configuracion minima requerida:
```env
OPENAI_API_KEY=sk-tu-clave-aqui
```

### 2. Construir y Ejecutar

```bash
# Desarrollo (con logs visibles)
docker compose up --build

# Produccion (en segundo plano)
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

### 3. Acceder a la Aplicacion

Abre en tu navegador: http://localhost:8501

## Comandos Utiles

### Gestion del Contenedor

```bash
# Ver logs en tiempo real
docker compose logs -f velora

# Detener servicios
docker compose down

# Detener y eliminar volumenes (CUIDADO: borra datos)
docker compose down -v

# Reiniciar servicio
docker compose restart velora

# Ver estado
docker compose ps
```

### Mantenimiento

```bash
# Reconstruir sin cache
docker compose build --no-cache

# Limpiar imagenes no utilizadas
docker image prune -f

# Verificar salud del contenedor
docker inspect --format='{{.State.Health.Status}}' velora-app
```

## Configuracion Avanzada

### Puerto Personalizado

En `.env`:
```env
VELORA_PORT=8080
```

O directamente:
```bash
VELORA_PORT=8080 docker compose up
```

### Recursos del Contenedor

Editar `docker-compose.yml`:
```yaml
deploy:
  resources:
    limits:
      cpus: '4.0'
      memory: 8G
```

### Persistencia de Datos

Los datos se almacenan en el volumen `velora-data`:

```bash
# Ver volumenes
docker volume ls

# Inspeccionar volumen
docker volume inspect velora-persistent-data

# Backup de datos
docker run --rm -v velora-persistent-data:/data -v $(pwd):/backup \
  alpine tar czf /backup/velora-backup.tar.gz /data
```

## Arquitectura Docker

### Imagen Multi-Stage

El Dockerfile usa 3 etapas para optimizar el tamano:

1. **base**: Dependencias del sistema (librerías para Playwright)
2. **dependencies**: Instalacion de paquetes Python + Chromium
3. **production**: Codigo de la aplicacion + usuario no-root

### Seguridad

- Usuario no-root (`velora:velora`)
- XSRF protection habilitada
- Health checks configurados
- Recursos limitados por defecto

## Solucion de Problemas

### Error: Puerto en uso

```bash
# Verificar que proceso usa el puerto
lsof -i :8501

# Usar puerto alternativo
VELORA_PORT=8502 docker compose up
```

### Error: Memoria insuficiente

Aumentar recursos en docker-compose.yml o reducir uso:
```yaml
resources:
  limits:
    memory: 6G
```

### Playwright no funciona

El navegador Chromium se instala automaticamente. Si hay problemas:
```bash
# Entrar al contenedor
docker compose exec velora bash

# Verificar instalacion
playwright install chromium --with-deps
```

### Logs de depuracion

```bash
# Ver ultimas 100 lineas
docker compose logs --tail=100 velora

# Filtrar por errores
docker compose logs velora 2>&1 | grep -i error
```

## Integracion con LangSmith

Para habilitar trazabilidad, agregar a `.env`:
```env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=tu-clave
LANGCHAIN_PROJECT=velora-production
```

## Produccion con HTTPS

Para HTTPS, usar un reverse proxy como Nginx o Traefik:

```yaml
# docker-compose.prod.yml (ejemplo con Traefik)
services:
  velora:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.velora.rule=Host(`velora.tudominio.com`)"
      - "traefik.http.routers.velora.tls.certresolver=letsencrypt"
```

## Metricas de Rendimiento

Recursos tipicos de la aplicacion:
- **CPU**: 0.5-2 cores (picos durante analisis LLM)
- **RAM**: 1-3 GB (dependiendo de PDFs procesados)
- **Disco**: 500MB base + datos de usuarios

## Contacto y Soporte

Para problemas o mejoras, consultar la documentacion tecnica en `/docs/`.

