# Guía de Inicio Rápido - Docker

> **Para evaluadores y usuarios nuevos**  
> Ejecuta el sistema en 3 pasos sin instalar nada excepto Docker

---

## ¿Por Qué Docker?

✅ **Instalación automática de TODO**:
- Python 3.11
- Todas las dependencias (LangChain, LangGraph, FAISS, etc.)
- Playwright + Chromium (para scraping avanzado)
- Configuración de Streamlit

✅ **Sin conflictos**: Entorno aislado, no afecta tu sistema

✅ **Reproducible**: Misma configuración en cualquier máquina

---

## Requisitos Previos

**Solo necesitas Docker instalado**:

- **Windows**: [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- **Mac**: [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- **Linux**: 
  ```bash
  curl -fsSL https://get.docker.com -o get-docker.sh
  sudo sh get-docker.sh
  ```

**Verificar instalación**:
```bash
docker --version
docker compose version
```

---

## Paso 1: Obtener el Código

```bash
# Clonar repositorio
git clone <repo_url>
cd carlos_prueba_tecnica

# O descargar y descomprimir ZIP
```

---

## Paso 2: Configurar API Key

### 2.1 Copiar Archivo de Ejemplo

**Linux/Mac**:
```bash
cp .env.example .env
```

**Linux/Mac**:
```bash
cp .env.example .env
```

**Windows (CMD)**:
```cmd
copy .env.example .env
```

**Windows (PowerShell)**:
```powershell
Copy-Item .env.example .env
```

### 2.2 Editar con tu API Key

**Linux/Mac**:
```bash
nano .env
```

**Windows**:
```cmd
notepad .env
```

O si prefieres VS Code:
```bash
code .env
```

### 2.3 Añadir tu API Key

Busca la línea:
```env
OPENAI_API_KEY=tu_api_key_aqui
```

Reemplaza `tu_api_key_aqui` con tu API key real:
```env
OPENAI_API_KEY=sk-proj-abc123...
```

**Guardar y cerrar** el archivo.

> 💡 **¿No tienes API key?** Obtén una en [platform.openai.com](https://platform.openai.com/api-keys)

---

## Paso 3: Ejecutar con Docker

### 3.1 Construir y Ejecutar

```bash
docker compose up --build
```

### 3.2 Esperar (Primera Vez)

Verás salida como:
```
[+] Building 123.4s (15/15) FINISHED
=> [base 1/4] FROM docker.io/library/python:3.11-slim-bookworm
=> [dependencies 2/3] RUN pip install -r requirements.txt
=> [dependencies 3/3] RUN playwright install chromium --with-deps  ← Automático
```

**Tiempo estimado**: 3-5 minutos la primera vez

### 3.3 Sistema Listo

Cuando veas:
```
velora-app  |   You can now view your Streamlit app in your browser.
velora-app  |   URL: http://0.0.0.0:8501
```

---

## Paso 4: Acceder al Sistema

1. **Abrir navegador**
2. **Ir a**: http://localhost:8501
3. **¡Listo!** El sistema está funcionando

---

## Uso del Sistema

### Configurar Usuario

1. En el **sidebar izquierdo**, introduce tu nombre de usuario (ej: "carlos")
2. El proveedor por defecto es **OpenAI** con el modelo **gpt-4o-mini**

### Evaluar un Candidato

1. **Tab "Evaluación"**
2. **CV**: Pegar texto o subir PDF
3. **Oferta**: Pegar texto o URL
4. **Click "Iniciar Evaluación"**
5. Ver resultados de Fase 1
6. Si hay requisitos faltantes, **Click "Iniciar Entrevista"**
7. Responder preguntas
8. Ver resultado final

### Consultar Historial

1. **Tab "Mi Historial"**
2. Ver evaluaciones previas
3. Usar el chatbot RAG: "¿Por qué me rechazaron?"

---

## Detener el Sistema

1. En la terminal donde ejecutaste `docker compose up`:
   - **Presionar**: `Ctrl+C`
2. Luego ejecutar:
   ```bash
   docker compose down
   ```

---

## Comandos Útiles

### Ejecutar en Segundo Plano

```bash
# Iniciar detached
docker compose up -d

# Ver logs
docker compose logs -f
```

### Ver Estado

```bash
docker compose ps
```

Debe mostrar:
```
NAME       STATUS    PORTS
velora-app healthy   0.0.0.0:8501->8501/tcp
```

### Reiniciar

```bash
docker compose restart
```

### Logs en Tiempo Real

```bash
docker compose logs -f velora
```

---

## Solución de Problemas Comunes

### ❌ Error: "port 8501 is already allocated"

**Solución 1** - Cambiar puerto:
```bash
# Editar .env y añadir:
echo "VELORA_PORT=8502" >> .env

# Reiniciar
docker compose down
docker compose up
```

**Solución 2** - Liberar puerto:
```bash
# Linux/Mac
lsof -ti:8501 | xargs kill -9

# Windows (PowerShell como admin)
Get-Process -Id (Get-NetTCPConnection -LocalPort 8501).OwningProcess | Stop-Process
```

### ❌ Error: "Cannot connect to Docker daemon"

**Linux**:
```bash
sudo systemctl start docker
```

**Windows/Mac**: Abrir Docker Desktop

### ❌ Error: "API key not found"

Verificar `.env`:
```bash
cat .env  # Linux/Mac
type .env # Windows
```

Debe contener:
```env
OPENAI_API_KEY=sk-...
```

### ❌ El sistema no carga / pantalla blanca

1. Verificar logs:
   ```bash
   docker compose logs velora
   ```

2. Verificar health:
   ```bash
   docker compose ps
   ```

3. Reconstruir imagen:
   ```bash
   docker compose down
   docker compose up --build
   ```

---

## Siguientes Ejecuciones

Después de la primera vez, es más rápido:

```bash
# 1. Iniciar (usa imagen existente)
docker compose up

# 2. Acceder a http://localhost:8501

# 3. Detener
Ctrl+C
docker compose down
```

---

## Limpieza Completa

Si quieres eliminar todo y empezar de cero:

```bash
# Detener y eliminar contenedores
docker compose down

# Eliminar volúmenes (datos persistentes)
docker compose down -v

# Eliminar imagen
docker rmi carlos_prueba_tecnica-velora

# Volver a construir
docker compose up --build
```

---

## ¿Prefieres Instalación Manual?

Si no quieres usar Docker, consulta:
- [README.md](../README.md) - Sección "Instalación Manual"

**Nota**: Con instalación manual debes ejecutar manualmente:
```bash
playwright install chromium
```

---

## Soporte

Si encuentras problemas:

1. **Revisar logs**: `docker compose logs -f`
2. **Consultar**: [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md) - Guía detallada
3. **Contactar**: Carlos Vega

---

*Guía rápida de inicio para prueba técnica de Velora*  
*Carlos Vega | Diciembre 2024*

