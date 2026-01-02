# Arquitectura del Sistema Velora

## Visión General

El sistema Velora es un **evaluador de candidatos con IA** que automatiza el proceso de matching entre CVs y ofertas de empleo, complementado con una entrevista conversacional.

---

## 1. Diagrama de Capas

```
┌─────────────────────────────────────────────────────────────────────┐
│                           FRONTEND                                   │
│                        (streamlit_app.py)                           │
│   Interfaz de usuario: upload CV/oferta, visualización resultados   │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         ORQUESTACIÓN                                 │
│           (orquestador.py, grafo_fase1.py, coordinador_grafo.py)    │
│   Coordina el flujo entre Fase 1 y Fase 2, gestiona estados         │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                            NÚCLEO                                    │
│  ┌──────────────┐  ┌──────────────────┐  ┌─────────────────────┐   │
│  │  Analizador  │  │  Entrevistador   │  │     Historial       │   │
│  │  (Fase 1)    │  │    (Fase 2)      │  │  (RAG + VectorDB)   │   │
│  └──────────────┘  └──────────────────┘  └─────────────────────┘   │
│   Lógica de negocio pura, sin dependencias de infraestructura       │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        INFRAESTRUCTURA                               │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────────────┐ │
│  │     LLM     │  │  Extracción  │  │      Persistencia          │ │
│  │  (fábricas, │  │  (PDF, Web)  │  │   (JSON, VectorStore)      │ │
│  │ embeddings) │  │              │  │                            │ │
│  └─────────────┘  └──────────────┘  └────────────────────────────┘ │
│   Integraciones con servicios externos (APIs, archivos, BD)         │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          RECURSOS                                    │
│                         (prompts.py)                                 │
│   Configuración centralizada: prompts, constantes temporales         │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          UTILIDADES                                  │
│     (logger.py, procesamiento.py, normalizacion.py, contexto_temporal.py)      │
│   Funciones transversales usadas por todas las capas                │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                           MODELOS                                    │
│                         (modelos.py)                                 │
│   Estructuras de datos Pydantic para tipado y validación            │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Estructura de Carpetas

```
carlos_prueba_tecnica/
├── main.py                    # Punto de entrada
├── requirements.txt           # Dependencias
├── Dockerfile                 # Contenedor Docker
├── docker-compose.yml         # Orquestación Docker
│
├── backend/
│   ├── __init__.py           # Exporta componentes públicos
│   ├── modelos.py            # Modelos Pydantic
│   │
│   ├── utilidades/           # Funciones transversales
│   │   ├── logger.py         # Sistema de logging
│   │   ├── procesamiento.py  # Cálculos de puntuación
│   │   ├── normalizacion.py  # Limpieza de texto
│   │   └── contexto_temporal.py  # Fecha de referencia (2026)
│   │
│   ├── recursos/             # Configuración centralizada
│   │   └── prompts.py        # Prompts del LLM
│   │
│   ├── infraestructura/      # Integraciones externas
│   │   ├── llm/
│   │   │   ├── llm_proveedor.py       # Fábrica de LLMs
│   │   │   ├── embedding_proveedor.py # Fábrica de Embeddings
│   │   │   ├── hiperparametros.py     # Configuración temp/top_p
│   │   │   ├── comparador_semantico.py # FAISS wrapper
│   │   │   └── configuracion_modelos.py # Modelos disponibles
│   │   ├── extraccion/
│   │   │   ├── pdf.py        # Lectura de PDFs
│   │   │   └── web.py        # Scraping de ofertas
│   │   └── persistencia/
│   │       └── memoria_usuario.py  # Almacenamiento JSON
│   │
│   ├── nucleo/               # Lógica de negocio
│   │   ├── analisis/
│   │   │   └── analizador.py # Fase 1: extracción + matching
│   │   ├── entrevista/
│   │   │   └── entrevistador.py # Fase 2: conversación
│   │   └── historial/
│   │       ├── almacen_vectorial.py # FAISS para historial
│   │       └── asistente.py  # RAG chatbot
│   │
│   └── orquestacion/         # Coordinación de flujos
│       ├── orquestador.py    # Coordinador principal
│       ├── grafo_fase1.py    # Grafo LangGraph
│       └── coordinador_grafo.py # Interfaz OOP para grafo
│
├── frontend/
│   ├── streamlit_app.py      # Interfaz de usuario
│   └── assets/               # Logos y recursos
│
├── data/                     # Datos persistentes
│   ├── memoria_usuario/      # JSONs por usuario
│   └── vectores/             # Índices FAISS
│
└── docs/
    └── ejemplos/             # CVs y ofertas de prueba
```

---

## 3. Flujo de Datos Principal

```
                    ┌──────────────┐
                    │    Usuario   │
                    └──────────────┘
                           │
                    CV + Oferta
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    FASE 1: ANÁLISIS AUTOMÁTICO                       │
│                                                                      │
│  1. Extracción de Requisitos (LLM)                                  │
│     oferta_texto → [requisitos] (obligatorios/opcionales)           │
│                                                                      │
│  2. Indexación Semántica (opcional)                                 │
│     cv_texto → embeddings → FAISS index                             │
│                                                                      │
│  3. Matching CV vs Requisitos (LLM)                                 │
│     cv + requisitos → evaluación por requisito                      │
│                                                                      │
│  4. Cálculo de Puntuación                                           │
│     - Si falta obligatorio → 0% (DESCARTADO)                        │
│     - Si todo cumple → 100%                                         │
│     - Sino → proporcional                                           │
│                                                                      │
│  Resultado: puntuación + requisitos_cumplidos + requisitos_faltantes│
└─────────────────────────────────────────────────────────────────────┘
                           │
                           │ ¿Descartado?
                           │
        ┌──────────────────┴──────────────────┐
        │ SÍ                                  │ NO (y hay faltantes)
        ▼                                     ▼
┌───────────────┐              ┌─────────────────────────────────────┐
│   FIN: 0%     │              │      FASE 2: ENTREVISTA             │
│  DESCARTADO   │              │                                     │
└───────────────┘              │  Por cada requisito faltante:       │
                               │  1. Generar pregunta (LLM streaming)│
                               │  2. Recibir respuesta del candidato │
                               │  3. Evaluar respuesta (LLM)         │
                               │                                     │
                               │  Resultado: requisitos verificados  │
                               └─────────────────────────────────────┘
                                              │
                                              ▼
                               ┌─────────────────────────────────────┐
                               │      RECÁLCULO FINAL                │
                               │                                     │
                               │  Combinar resultados Fase1 + Fase2  │
                               │  Calcular puntuación final          │
                               │  Guardar en historial               │
                               └─────────────────────────────────────┘
```

---

## 4. Responsabilidad de Cada Capa

### 4.1 Frontend (`frontend/`)

**Responsabilidad**: Interfaz de usuario

- Recoger inputs (CV, oferta, configuración)
- Mostrar resultados (métricas, requisitos)
- Gestionar la conversación de Fase 2
- No contiene lógica de negocio

### 4.2 Orquestación (`orquestacion/`)

**Responsabilidad**: Coordinar el flujo de trabajo

- Decidir si ejecutar Fase 2
- Gestionar estados del proceso
- Combinar resultados de ambas fases
- Integrar con LangSmith (trazabilidad)

### 4.3 Núcleo (`nucleo/`)

**Responsabilidad**: Lógica de negocio pura

- `analisis/`: Extracción de requisitos + matching
- `entrevista/`: Generación de preguntas + evaluación
- `historial/`: RAG para consultas sobre evaluaciones previas

**Característica clave**: No tiene dependencias de infraestructura directas.

### 4.4 Infraestructura (`infraestructura/`)

**Responsabilidad**: Integraciones externas

- `llm/`: Crear instancias de LLMs y embeddings
- `extraccion/`: Leer PDFs, hacer scraping web
- `persistencia/`: Guardar/cargar datos JSON

### 4.5 Recursos (`recursos/`)

**Responsabilidad**: Configuración centralizada

- Prompts del sistema
- Constantes temporales (año 2026)

### 4.6 Utilidades (`utilidades/`)

**Responsabilidad**: Funciones transversales

- Logging estructurado
- Cálculo de puntuaciones
- Normalización de texto
- Contexto temporal

### 4.7 Modelos (`modelos.py`)

**Responsabilidad**: Estructuras de datos

- Definición de tipos con Pydantic
- Validación automática
- Schemas para Structured Output

---

## 5. Principios Arquitectónicos

### 5.1 Separación de Responsabilidades

Cada módulo tiene una única responsabilidad clara. No hay "módulos dios" que hagan todo.

### 5.2 Dependencias Unidireccionales

```
Frontend → Orquestación → Núcleo → Infraestructura
                ↓
            Utilidades
                ↓
             Modelos
```

Las capas superiores pueden usar las inferiores, **nunca al revés**.

### 5.3 Inyección de Dependencias

Los componentes reciben sus dependencias, no las crean:

```python
class AnalizadorFase1:
    def __init__(
        self,
        llm=None,  # Se puede inyectar un LLM
        proveedor=None,  # O dejar que el analizador lo cree
    ):
        if llm is None:
            self.llm = FabricaLLM.crear_llm(proveedor, ...)
```

### 5.4 Configuración Externalizada

- Hiperparámetros en `hiperparametros.py`
- Prompts en `prompts.py`
- Modelos disponibles en `configuracion_modelos.py`

Ningún valor hardcodeado en la lógica de negocio.

---

## 6. Comunicación entre Componentes

### 6.1 Datos de Entrada → Fase 1

```python
# El frontend prepara los datos
cv_texto = extraer_texto_de_pdf(archivo_cv)
oferta_texto = scrape_job_offer_url(url_oferta)

# El orquestador coordina
resultado_fase1 = analizador.analizar(oferta_texto, cv_texto)
```

### 6.2 Fase 1 → Fase 2

```python
# El resultado de Fase 1 contiene:
resultado_fase1.requisitos_faltantes  # Lista de requisitos no verificados
resultado_fase1.descartado            # Si el candidato fue descartado

# El entrevistador usa esta información
entrevistador.inicializar_entrevista(
    nombre_candidato="Carlos",
    resultado_fase1=resultado_fase1,
    contexto_cv=cv_texto
)
```

### 6.3 Fase 2 → Resultado Final

```python
# Las respuestas de la entrevista
respuestas = entrevistador.obtener_respuestas_entrevista()

# El orquestador recalcula
resultado_final = orquestador.reevaluar_con_entrevista(
    resultado_fase1,
    respuestas
)
```

---

## 7. Almacenamiento de Datos

### 7.1 Memoria de Usuario (`data/memoria_usuario/`)

Archivos JSON por usuario:
```
data/memoria_usuario/
├── carlos.json
├── marta.json
└── ...
```

Contenido:
```json
[
  {
    "evaluation_id": "uuid-...",
    "timestamp": "2026-01-02T...",
    "score": 85.0,
    "status": "approved",
    "job_offer_title": "Senior Python Developer",
    "searchable_text": "Texto para embeddings...",
    ...
  }
]
```

### 7.2 Índices Vectoriales (`data/vectores/`)

Índices FAISS por usuario:
```
data/vectores/
├── carlos/
│   ├── index.faiss        # Índice vectorial
│   ├── index.pkl          # Metadatos
│   └── embedding_provider.txt  # Proveedor usado
└── marta/
    └── ...
```

---

## 8. Mapa de Dependencias entre Ficheros

```
streamlit_app.py
    │
    ├──► Orquestador (orquestador.py)
    │       ├──► AnalizadorFase1 (analizador.py)
    │       │       ├──► FabricaLLM (llm_proveedor.py)
    │       │       ├──► ComparadorSemantico (comparador_semantico.py)
    │       │       └──► prompts.py
    │       │
    │       └──► EntrevistadorFase2 (entrevistador.py)
    │               ├──► FabricaLLM
    │               └──► prompts.py
    │
    ├──► MemoriaUsuario (memoria_usuario.py)
    │
    ├──► AsistenteHistorial (asistente.py)
    │       └──► AlmacenVectorialHistorial (almacen_vectorial.py)
    │               └──► FabricaEmbeddings (embedding_proveedor.py)
    │
    └──► Extractores
            ├──► extraer_texto_de_pdf (pdf.py)
            └──► extraer_oferta_web (web.py)
```

---

## Próximo Documento

Continúa con [04_DECISIONES_DISENO.md](./04_DECISIONES_DISENO.md) para entender por qué se tomaron estas decisiones arquitectónicas.

