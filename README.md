# Velora - Sistema de Evaluación de Candidatos con IA

> **Prueba técnica para Ingeniero de IA Generativa**  
> Desarrollada por Carlos Vega | Diciembre 2024

---

## 🚀 Inicio Rápido con Docker (Recomendado)

La forma más sencilla de ejecutar el sistema es con Docker. **Todo se configura automáticamente**, incluyendo Playwright Chromium para scraping avanzado.

### ⚡ 3 Pasos para Ejecutar

```bash
# 1. Clonar y entrar
git clone <repo_url>
cd carlos_prueba_tecnica

# 2. Configurar API key
cp .env.example .env  # Windows: copy .env.example .env
# Editar .env y añadir: OPENAI_API_KEY=sk-...

# 3. ¡Ejecutar!
docker compose up --build
```

**Acceder a**: http://localhost:8501

> 💡 **Primera vez**: Tarda 3-5 minutos (descarga dependencias + **instala Chromium automáticamente**)  
> 📘 **Guía paso a paso completa**: [INICIO_RAPIDO_DOCKER.md](docs/INICIO_RAPIDO_DOCKER.md)

### Detener

```bash
Ctrl+C → docker compose down
```

---

## Instalación Manual (Alternativa)

Si prefieres ejecutar sin Docker:

### Requisitos
- Python 3.9+
- API Key de OpenAI (u otro proveedor)

### Instalación

```bash
# 1. Crear entorno virtual
python -m venv venv

# 2. Activar entorno
# En Linux/Mac:
source venv/bin/activate
# En Windows:
venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Instalar Chromium para Playwright (necesario para scraping)
playwright install chromium

# 5. Configurar variables de entorno
cp .env.example .env
# Editar .env con tu API key
```

### Ejecución

```bash
# Opción 1: Con Streamlit directamente
streamlit run frontend/streamlit_app.py

# Opción 2: Con el script principal
python main.py
```

Acceder a **http://localhost:8501**

---

## Cumplimiento de Requisitos

El sistema implementa **completamente** las dos fases especificadas:

| Requisito | Estado | Implementación |
|-----------|--------|----------------|
| Fase 1: Análisis CV vs Oferta | ✅ | Extracción de requisitos + matching con puntuación |
| Requisitos obligatorios vs opcionales | ✅ | Flag `discarded` cuando falta obligatorio |
| Puntuación proporcional | ✅ | `score = (cumplidos / total) * 100` |
| Fase 2: Entrevista por requisitos faltantes | ✅ | Conversación para requisitos no encontrados |
| Recalcular puntuación post-entrevista | ✅ | Reevaluación automática |
| LangChain con proveedores intercambiables | ✅ | OpenAI, Google, Anthropic |
| Proyecto ejecutable con dependencias | ✅ | `requirements.txt` |
| Docker | ✅ | `Dockerfile` + `docker-compose.yml` |
| Interfaz UI (valorable) | ✅ | Streamlit con diseño corporativo |

---

## Valor Diferencial Aportado

Más allá de los requisitos base, implementé funcionalidades adicionales:

### Arquitectura
- **Backend modular por capas**: Separación clara entre núcleo, orquestación, infraestructura
- **Configuración centralizada**: Cambios sin tocar código de negocio
- **Nomenclatura bilingüe**: Código en castellano con aliases en inglés

### Tecnologías Avanzadas de LangChain
- **LangGraph**: Orquestación multi-agente con grafo de estados (activable/desactivable)
- **LangSmith**: Trazabilidad completa de llamadas LLM
- **Structured Output**: Respuestas garantizadas en formato Pydantic (sin parsing manual)

### Funcionalidades Adicionales
- **Embeddings semánticos con FAISS**: Búsqueda de evidencia en CV (opcional)
- **RAG para historial**: Chatbot que consulta evaluaciones previas
- **Hiperparametrización contextual**: Temperaturas diferenciadas por fase
- **Streaming real**: Entrevista con generación token-by-token
- **Scraping avanzado**: Playwright para URLs protegidas (LinkedIn, portales corporativos)
- **Niveles de confianza**: Cada match incluye `high/medium/low` con razonamiento
- **Logs operacionales**: Trazabilidad en tiempo real

---

## Estructura del Proyecto

```
├── backend/
│   ├── modelos.py              # Modelos Pydantic
│   ├── nucleo/                 # Lógica: análisis, entrevista, historial
│   ├── orquestacion/           # Coordinadores + LangGraph
│   ├── infraestructura/        # LLM, embeddings, persistencia
│   └── recursos/               # Prompts centralizados
├── frontend/streamlit_app.py   # UI Streamlit
├── data/                       # Persistencia (creada automáticamente)
├── docs/
│   ├── DOCUMENTACION_TECNICA.md  # Detalles de implementación
│   ├── GUION_DEMO_VIDEO.md       # Guión para demo
│   └── DOCKER_DEPLOYMENT.md      # Guía detallada de Docker
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

---

## 📚 Documentación

| Documento | Descripción |
|-----------|-------------|
| **[Inicio Rápido Docker](docs/INICIO_RAPIDO_DOCKER.md)** | Guía paso a paso para ejecutar con Docker (recomendado para evaluadores) |
| **[Documentación Técnica](docs/DOCUMENTACION_TECNICA.md)** | Decisiones de diseño, arquitectura, valor diferencial |
| **[Guión Demo](docs/GUION_DEMO_VIDEO.md)** | Estructura para vídeo demostrativo |
| **[Guía Docker Avanzada](docs/DOCKER_DEPLOYMENT.md)** | Despliegue detallado, troubleshooting, producción |

---

## Solución de Problemas

### Error: "API key not found"
```bash
# Verificar que .env existe y contiene la API key
cat .env  # Linux/Mac
type .env # Windows

# Debe contener:
# OPENAI_API_KEY=sk-...
```

### Docker: "Port 8501 already in use"
```bash
# Cambiar puerto en .env
echo "VELORA_PORT=8502" >> .env

# O detener el proceso que usa el puerto
docker compose down
```

### Error de Playwright en instalación manual
```bash
# Reinstalar Chromium
playwright install chromium --with-deps
```

---

## Contacto

Disponible para discusión técnica, debugging o profundización sobre cualquier aspecto.

**Carlos Vega**
