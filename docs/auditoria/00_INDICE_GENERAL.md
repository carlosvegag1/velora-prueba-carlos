# Auditoría Técnica Integral - Sistema Velora

## Índice General de Documentación

---

## 📚 Documentos Teórico-Prácticos

Documentación general que explica conceptos, arquitectura y decisiones de diseño.

| # | Documento | Descripción |
|---|-----------|-------------|
| 01 | [Fundamentos de Python](./01_FUNDAMENTOS_PYTHON.md) | Variables, funciones, clases, imports |
| 02 | [Conceptos de POO](./02_CONCEPTOS_POO.md) | Clases, herencia, polimorfismo, patrones |
| 03 | [Arquitectura del Sistema](./03_ARQUITECTURA_SISTEMA.md) | Capas, estructura, dependencias |
| 04 | [Decisiones de Diseño](./04_DECISIONES_DISENO.md) | Justificación de cada decisión técnica |
| 05 | [Flujo de Datos](./05_FLUJO_DATOS.md) | Transformaciones de datos paso a paso |
| 06 | [Tecnologías Utilizadas](./06_TECNOLOGIAS_UTILIZADAS.md) | LangChain, FAISS, Streamlit, etc. |
| 07 | [Glosario de Términos](./07_GLOSARIO_TERMINOS.md) | Definiciones de términos técnicos |
| 08 | [Buenas Prácticas](./08_BUENAS_PRACTICAS.md) | Principios SOLID, DRY, patrones |

---

## 📁 Documentación por Fichero

Documentación detallada de cada archivo del proyecto.

### Raíz del Proyecto

| # | Archivo | Documento |
|---|---------|-----------|
| 01 | `main.py` | [Documentación](./ficheros/01_main.md) |
| 02 | `requirements.txt` | [Documentación](./ficheros/02_requirements.md) |
| 12 | `Dockerfile` + `docker-compose.yml` | [Documentación](./ficheros/12_docker.md) |

### Backend - Modelos y Núcleo

| # | Archivo | Documento |
|---|---------|-----------|
| 03 | `backend/modelos.py` | [Documentación](./ficheros/03_modelos.md) |
| 04 | `backend/nucleo/analisis/analizador.py` | [Documentación](./ficheros/04_analizador.md) |
| 05 | `backend/nucleo/entrevista/entrevistador.py` | [Documentación](./ficheros/05_entrevistador.md) |

### Backend - Recursos y Orquestación

| # | Archivo | Documento |
|---|---------|-----------|
| 06 | `backend/recursos/prompts.py` | [Documentación](./ficheros/06_prompts.md) |
| 07 | `backend/orquestacion/orquestador.py` | [Documentación](./ficheros/07_orquestador.md) |
| 08 | `backend/orquestacion/grafo_fase1.py` | [Documentación](./ficheros/08_grafo_fase1.md) |

### Backend - Infraestructura y Utilidades

| # | Archivo | Documento |
|---|---------|-----------|
| 09 | `backend/infraestructura/llm/llm_proveedor.py` | [Documentación](./ficheros/09_llm_proveedor.md) |
| 10 | `backend/utilidades/contexto_temporal.py` | [Documentación](./ficheros/10_contexto_temporal.md) |

### Frontend

| # | Archivo | Documento |
|---|---------|-----------|
| 11 | `frontend/streamlit_app.py` | [Documentación](./ficheros/11_streamlit_app.md) |

---

## 🗺️ Mapa de Lectura Recomendado

### Para entender el sistema desde cero:

```
1. Fundamentos de Python (si necesitas refrescar)
   └── 01_FUNDAMENTOS_PYTHON.md

2. Arquitectura general
   └── 03_ARQUITECTURA_SISTEMA.md

3. Flujo de datos
   └── 05_FLUJO_DATOS.md

4. Tecnologías utilizadas
   └── 06_TECNOLOGIAS_UTILIZADAS.md

5. Archivos clave en orden:
   ├── ficheros/03_modelos.md (estructuras de datos)
   ├── ficheros/06_prompts.md (instrucciones a LLMs)
   ├── ficheros/04_analizador.md (Fase 1)
   ├── ficheros/05_entrevistador.md (Fase 2)
   └── ficheros/07_orquestador.md (coordinación)
```

### Para defender decisiones de diseño:

```
1. Decisiones de Diseño
   └── 04_DECISIONES_DISENO.md

2. Buenas Prácticas
   └── 08_BUENAS_PRACTICAS.md

3. Justificaciones en cada fichero
   └── Sección "Justificación de Diseño" al final de cada documento
```

### Para entender términos técnicos:

```
1. Glosario
   └── 07_GLOSARIO_TERMINOS.md
```

---

## 📊 Estructura del Proyecto

```
carlos_prueba_tecnica/
├── main.py                           # Punto de entrada
├── requirements.txt                  # Dependencias
├── Dockerfile                        # Imagen Docker
├── docker-compose.yml               # Orquestación Docker
│
├── backend/
│   ├── __init__.py                  # Exportaciones públicas
│   ├── modelos.py                   # Modelos Pydantic
│   │
│   ├── nucleo/                      # Lógica de negocio
│   │   ├── analisis/
│   │   │   └── analizador.py        # Fase 1
│   │   ├── entrevista/
│   │   │   └── entrevistador.py     # Fase 2
│   │   └── historial/
│   │       ├── almacen_vectorial.py # FAISS
│   │       └── asistente.py         # RAG chatbot
│   │
│   ├── orquestacion/                # Coordinación
│   │   ├── orquestador.py           # Coordinador principal
│   │   ├── grafo_fase1.py           # LangGraph
│   │   └── coordinador_grafo.py     # Wrapper OOP
│   │
│   ├── infraestructura/             # Servicios externos
│   │   ├── llm/
│   │   │   ├── llm_proveedor.py     # Fábrica de LLMs
│   │   │   ├── embedding_proveedor.py
│   │   │   ├── hiperparametros.py
│   │   │   └── comparador_semantico.py
│   │   ├── extraccion/
│   │   │   ├── pdf.py               # Extracción de PDFs
│   │   │   └── web.py               # Scraping web
│   │   └── persistencia/
│   │       └── memoria_usuario.py   # JSON storage
│   │
│   ├── utilidades/                  # Funciones transversales
│   │   ├── logger.py
│   │   ├── procesamiento.py
│   │   ├── normalizacion.py
│   │   └── contexto_temporal.py     # CRÍTICO: año 2026
│   │
│   └── recursos/                    # Configuración
│       └── prompts.py               # Todos los prompts
│
└── frontend/
    └── streamlit_app.py             # Interfaz de usuario
```

---

## 🎯 Puntos Clave para Auditoría

### 1. Determinismo en Fase 1

- Temperatura 0.0 para extracción y matching
- Misma oferta → Mismos requisitos SIEMPRE
- Documentado en: `04_analizador.md`, `06_prompts.md`

### 2. Contexto Temporal

- Sistema referenciado a enero 2026
- Crítico para cálculos de experiencia
- Documentado en: `10_contexto_temporal.md`

### 3. Structured Output

- LLM forzado a responder en formato Pydantic
- Garantiza estructura de datos válida
- Documentado en: `03_modelos.md`, `04_analizador.md`

### 4. Multi-proveedor LLM

- Soporte para OpenAI, Google, Anthropic
- Fábrica centralizada
- Documentado en: `09_llm_proveedor.md`

### 5. Arquitectura por Capas

- Núcleo → Orquestación → Infraestructura → Recursos
- Sin dependencias circulares
- Documentado en: `03_ARQUITECTURA_SISTEMA.md`

### 6. Reduccionismo

- Sin capas innecesarias
- Sin abstracciones no justificadas
- Documentado en: `04_DECISIONES_DISENO.md`

---

## 📝 Cómo Usar Esta Documentación

### Para Entender el Sistema

1. Lee `03_ARQUITECTURA_SISTEMA.md` para visión general
2. Lee `05_FLUJO_DATOS.md` para entender el proceso
3. Consulta archivos específicos según necesites

### Para Defender Decisiones

1. Cada archivo tiene sección "Justificación de Diseño"
2. `04_DECISIONES_DISENO.md` tiene justificaciones globales
3. `08_BUENAS_PRACTICAS.md` explica principios aplicados

### Para Consultar Términos

1. `07_GLOSARIO_TERMINOS.md` tiene definiciones
2. Cada documento explica términos en contexto

---

## 👤 Autor

Documentación generada para auditoría técnica del sistema Velora.

**Versión del sistema**: 3.1.0

**Fecha de documentación**: Enero 2026
