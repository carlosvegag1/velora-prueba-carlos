# Tecnologías Utilizadas en el Sistema Velora

## Introducción

Este documento explica cada tecnología utilizada en el proyecto, su propósito y cómo se integra en el sistema.

---

## 1. LangChain

### ¿Qué es?

LangChain es un framework de Python para construir aplicaciones con LLMs (Large Language Models). Proporciona abstracciones para interactuar con diferentes proveedores de IA.

### ¿Por qué lo usamos?

1. **Abstracción de proveedores**: Mismo código para OpenAI, Google, Anthropic
2. **Structured Output**: Respuestas garantizadas en formato Pydantic
3. **Chains**: Composición de prompts y modelos
4. **Integración con LangSmith**: Trazabilidad automática

### Uso en Velora

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

# 1. Crear instancia de LLM
llm = ChatOpenAI(model="gpt-4o", temperature=0.0)

# 2. Crear prompt template
prompt = ChatPromptTemplate.from_messages([
    ("system", "Eres un extractor de requisitos..."),
    ("human", "{job_offer}")
])

# 3. Crear chain (composición)
chain = prompt | llm

# 4. Ejecutar
resultado = chain.invoke({"job_offer": texto_oferta})
```

### Structured Output

```python
from pydantic import BaseModel

class RespuestaExtraccion(BaseModel):
    requirements: list

# El LLM SIEMPRE devuelve este formato
llm_estructurado = llm.with_structured_output(RespuestaExtraccion)
resultado = llm_estructurado.invoke(prompt)
# resultado.requirements es una lista garantizada
```

### Componentes Usados

| Componente | Paquete | Uso |
|------------|---------|-----|
| `ChatOpenAI` | `langchain-openai` | LLM de OpenAI |
| `ChatGoogleGenerativeAI` | `langchain-google-genai` | LLM de Google |
| `ChatAnthropic` | `langchain-anthropic` | LLM de Anthropic |
| `ChatPromptTemplate` | `langchain-core` | Templates de prompts |
| `StrOutputParser` | `langchain-core` | Parsear salida como string |

---

## 2. LangGraph

### ¿Qué es?

LangGraph es un framework de orquestación que permite definir flujos de trabajo como grafos de estados. Cada nodo es una operación y las aristas definen transiciones.

### ¿Por qué lo usamos?

1. **Control granular**: Cada paso es un nodo independiente
2. **Estado tipado**: TypedDict para garantizar estructura
3. **Streaming**: Eventos por nodo para feedback en tiempo real
4. **Debugging**: Visualización del flujo

### Uso en Velora

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, List

# 1. Definir estado del grafo
class EstadoFase1(TypedDict):
    oferta_trabajo: str
    cv: str
    requisitos: List[dict]
    puntuacion: float
    descartado: bool

# 2. Crear grafo
grafo = StateGraph(EstadoFase1)

# 3. Añadir nodos (funciones que procesan el estado)
grafo.add_node("extraer_requisitos", nodo_extraccion)
grafo.add_node("matching", nodo_matching)
grafo.add_node("calcular_puntuacion", nodo_puntuacion)

# 4. Definir aristas (flujo)
grafo.set_entry_point("extraer_requisitos")
grafo.add_edge("extraer_requisitos", "matching")
grafo.add_edge("matching", "calcular_puntuacion")
grafo.add_edge("calcular_puntuacion", END)

# 5. Compilar y ejecutar
app = grafo.compile()
resultado = app.invoke(estado_inicial)
```

### Nodos del Grafo en Velora

```
┌─────────────────────┐
│ extraer_requisitos  │  Extrae requisitos de la oferta
└─────────────────────┘
          │
          ▼
┌─────────────────────┐
│     embeber_cv      │  Indexa CV con embeddings (opcional)
└─────────────────────┘
          │
          ▼
┌─────────────────────┐
│ matching_semantico  │  Evalúa requisitos contra CV
└─────────────────────┘
          │
          ▼
┌─────────────────────┐
│ calcular_puntuacion │  Genera resultado final
└─────────────────────┘
          │
          ▼
        END
```

---

## 3. FAISS (Facebook AI Similarity Search)

### ¿Qué es?

FAISS es una librería de búsqueda vectorial eficiente. Permite encontrar vectores similares en grandes conjuntos de datos.

### ¿Por qué lo usamos?

1. **Sin servidor**: Funciona con archivos locales
2. **Eficiente**: Búsqueda rápida incluso con miles de vectores
3. **Gratuito**: Open source
4. **Portable**: Funciona en Docker sin configuración

### Uso en Velora

```python
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

# 1. Crear embeddings
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# 2. Crear índice desde textos
chunks = ["Experiencia en Python...", "Docker y Kubernetes...", ...]
vectorstore = FAISS.from_texts(chunks, embeddings)

# 3. Buscar similares
resultados = vectorstore.similarity_search("Python", k=3)
# Devuelve los 3 chunks más similares a "Python"

# 4. Persistir en disco
vectorstore.save_local("data/vectores/usuario1")

# 5. Cargar desde disco
vectorstore = FAISS.load_local("data/vectores/usuario1", embeddings)
```

### Casos de Uso en Velora

1. **Matching semántico**: Encontrar evidencia en el CV para cada requisito
2. **RAG historial**: Buscar evaluaciones relevantes para consultas del usuario

---

## 4. Pydantic

### ¿Qué es?

Pydantic es una librería de validación de datos usando anotaciones de tipo Python.

### ¿Por qué lo usamos?

1. **Validación automática**: Tipos verificados en tiempo de ejecución
2. **Valores por defecto**: Declarativos y claros
3. **Serialización**: `.model_dump()` → dict, `.model_dump_json()` → JSON
4. **Structured Output**: LangChain lo usa para garantizar respuestas del LLM

### Uso en Velora

```python
from pydantic import BaseModel, Field
from typing import Optional, Literal

class Requisito(BaseModel):
    """Modelo de un requisito."""
    
    descripcion: str = Field(..., alias="description")
    # ... es obligatorio
    # alias permite usar "description" en JSON
    
    tipo: Literal["obligatory", "optional"] = Field(..., alias="type")
    # Literal restringe valores posibles
    
    cumplido: bool = Field(default=False, alias="fulfilled")
    # default=False si no se proporciona
    
    puntuacion_semantica: Optional[float] = Field(
        None, 
        alias="semantic_score",
        ge=0,  # >= 0
        le=1   # <= 1
    )
    
    class Config:
        populate_by_name = True  # Acepta nombre o alias

# Uso
req = Requisito(
    descripcion="5 años Python",
    tipo="obligatory"
)
# cumplido es False automáticamente
# puntuacion_semantica es None

# Validación
req_invalido = Requisito(
    descripcion="test",
    tipo="invalid"  # ERROR: no es "obligatory" ni "optional"
)
```

---

## 5. Streamlit

### ¿Qué es?

Streamlit es un framework de Python para crear aplicaciones web interactivas sin escribir JavaScript.

### ¿Por qué lo usamos?

1. **Python puro**: No necesita conocimientos de frontend
2. **Reactivo**: El estado se actualiza automáticamente
3. **Rápido**: Ideal para prototipos y MVPs
4. **Widgets**: Botones, inputs, file uploaders integrados

### Uso en Velora

```python
import streamlit as st

# Configuración de página
st.set_page_config(page_title="Velora", layout="wide")

# Estilos CSS
st.markdown("<style>...</style>", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    provider = st.selectbox("Proveedor", ["openai", "google"])
    api_key = st.text_input("API Key", type="password")

# Contenido principal
st.title("Evaluador de Candidatos")

# Tabs
tab1, tab2 = st.tabs(["Evaluación", "Historial"])

with tab1:
    # File uploader
    cv_file = st.file_uploader("Sube tu CV", type=["pdf", "txt"])
    
    # Botón
    if st.button("Iniciar Evaluación"):
        with st.spinner("Procesando..."):
            # Lógica de evaluación
            resultado = evaluar(cv_file)
        st.success("Completado!")
        st.metric("Puntuación", f"{resultado.puntuacion}%")
```

### Gestión de Estado

```python
# session_state persiste entre recargas
if 'phase1_result' not in st.session_state:
    st.session_state['phase1_result'] = None

# Guardar resultado
st.session_state['phase1_result'] = resultado

# Leer resultado
resultado = st.session_state.get('phase1_result')
```

---

## 6. Playwright

### ¿Qué es?

Playwright es una herramienta de automatización de navegadores que permite controlar Chrome, Firefox y Safari programáticamente.

### ¿Por qué lo usamos?

1. **JavaScript rendering**: Sitios modernos (React, Vue) necesitan ejecutar JS
2. **Anti-bot bypass**: Simula un navegador real
3. **Headless**: Funciona sin interfaz gráfica (ideal para Docker)

### Uso en Velora

```python
from playwright.sync_api import sync_playwright

def scrape_con_playwright(url):
    with sync_playwright() as p:
        # Lanzar navegador headless
        browser = p.chromium.launch(headless=True)
        
        # Crear contexto con headers de navegador real
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
            viewport={"width": 1920, "height": 1080}
        )
        
        # Navegar
        page = context.new_page()
        page.goto(url, wait_until="domcontentloaded")
        
        # Simular comportamiento humano
        page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
        
        # Obtener HTML renderizado
        html = page.content()
        
        browser.close()
        return html
```

### Estrategia de Dos Niveles en Velora

```
URL de oferta
    │
    ▼
┌──────────────────────┐
│ Nivel 1: requests    │  Rápido, sin JavaScript
└──────────────────────┘
    │
    ▼ ¿Falla o detecta JS?
    │
┌──────────────────────┐
│ Nivel 2: Playwright  │  Renderiza JS completo
└──────────────────────┘
    │
    ▼
Texto de la oferta
```

---

## 7. pypdf

### ¿Qué es?

pypdf (antes PyPDF2) es una librería para leer y manipular archivos PDF.

### Uso en Velora

```python
from pypdf import PdfReader
import io

def extraer_texto_pdf(pdf_bytes):
    # Crear reader desde bytes
    archivo = io.BytesIO(pdf_bytes)
    reader = PdfReader(archivo)
    
    # Extraer texto de cada página
    texto = ""
    for pagina in reader.pages:
        texto += pagina.extract_text() + "\n"
    
    return texto.strip()
```

---

## 8. LangSmith

### ¿Qué es?

LangSmith es una plataforma de observabilidad para aplicaciones LLM. Permite ver todas las llamadas al LLM, tiempos, costos, etc.

### ¿Por qué lo usamos?

1. **Debugging**: Ver exactamente qué prompt se envió y qué respuesta volvió
2. **Evaluación**: Comparar diferentes prompts/modelos
3. **Costos**: Trackear uso de tokens

### Configuración en Velora

```python
import os

def configurar_langsmith():
    api_key = os.getenv("LANGSMITH_API_KEY")
    if api_key:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_PROJECT"] = "velora-evaluator"
        # A partir de aquí, todas las llamadas se registran
```

---

## 9. Embeddings

### ¿Qué son?

Los embeddings son representaciones numéricas de texto. Textos similares tienen embeddings cercanos en el espacio vectorial.

### Uso en Velora

```python
from langchain_openai import OpenAIEmbeddings

# Crear embeddings
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    dimensions=512  # Reducido de 1536 para velocidad
)

# Vectorizar texto
vector = embeddings.embed_query("5 años de Python")
# vector es una lista de 512 floats

# Vectorizar múltiples textos
vectores = embeddings.embed_documents([
    "Experiencia en Django",
    "Conocimientos de Docker"
])
# vectores es una lista de listas
```

### Proveedores Soportados

| Proveedor | Modelo | Dimensiones |
|-----------|--------|-------------|
| OpenAI | text-embedding-3-small | 512 (optimizado) |
| Google | text-embedding-004 | 768 |
| Anthropic | N/A | No ofrece embeddings |

---

## 10. Docker

### ¿Qué es?

Docker es una plataforma de contenedorización que permite empaquetar aplicaciones con todas sus dependencias.

### Uso en Velora

```dockerfile
# Multi-stage build
FROM python:3.11-slim-bookworm AS base

# Instalar dependencias del sistema para Playwright
RUN apt-get update && apt-get install -y \
    libnss3 libnspr4 ...

# Instalar dependencias Python
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN playwright install chromium

# Usuario no-root (seguridad)
RUN useradd --uid 1000 velora
USER velora

# Comando de inicio
CMD streamlit run frontend/streamlit_app.py
```

### docker-compose.yml

```yaml
services:
  velora:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8501:8501"
    volumes:
      - velora-data:/app/data  # Persistencia
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
```

---

## 11. Resumen de Dependencias

### requirements.txt

```
# Core LangChain
langchain>=0.1.0
langchain-core>=0.1.23
langchain-community>=0.0.10

# Multi-provider LLM
langchain-openai>=0.0.2
langchain-google-genai>=0.0.6
langchain-anthropic>=0.1.0

# Orquestación
langgraph>=0.0.20

# Observabilidad
langsmith>=0.0.80

# Búsqueda vectorial
faiss-cpu>=1.7.4

# Frontend
streamlit>=1.28.0

# Scraping
requests>=2.31.0
beautifulsoup4>=4.12.0
playwright>=1.40.0

# PDF
pypdf>=3.0.0

# Validación
pydantic>=2.5.3
```

---

## 12. Mapa de Tecnologías por Capa

| Capa | Tecnología | Propósito |
|------|------------|-----------|
| Frontend | Streamlit | Interfaz web |
| Orquestación | LangGraph | Flujo de estados |
| Núcleo | LangChain | Interacción con LLMs |
| Infraestructura | FAISS, pypdf, Playwright | Búsqueda vectorial, extracción |
| Persistencia | JSON, FAISS local | Almacenamiento |
| Observabilidad | LangSmith | Trazabilidad |
| Despliegue | Docker | Contenedorización |

---

## Conclusión

Cada tecnología fue elegida por ser la solución más simple que cumple el requisito:

- **LangChain**: Abstracción de LLMs sin reinventar la rueda
- **LangGraph**: Orquestación opcional para flujos complejos
- **FAISS**: Búsqueda vectorial sin servidor
- **Streamlit**: Frontend sin JavaScript
- **Docker**: Despliegue reproducible

No se añadieron tecnologías "por si acaso". Cada una tiene un propósito claro y justificado.

