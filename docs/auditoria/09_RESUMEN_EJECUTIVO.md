# Resumen Ejecutivo - Sistema Velora

## ¿Qué es Velora?

Velora es un **sistema de evaluación automatizada de candidatos** que analiza CVs contra ofertas de trabajo usando inteligencia artificial (LLMs).

---

## Proceso de Evaluación

```
┌─────────────────────────────────────────────────────────────────────┐
│                         VELORA                                       │
│                                                                     │
│   CV + Oferta de Trabajo                                           │
│         │                                                          │
│         ▼                                                          │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │                    FASE 1: Análisis Automático               │  │
│   │                                                             │  │
│   │   1. Extraer requisitos de la oferta                       │  │
│   │   2. Evaluar CV contra cada requisito                      │  │
│   │   3. Calcular puntuación inicial                           │  │
│   │                                                             │  │
│   │   Resultado: 0-100% + lista de requisitos cumplidos/no     │  │
│   └─────────────────────────────────────────────────────────────┘  │
│         │                                                          │
│         ▼                                                          │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │              ¿Hay requisitos no cumplidos?                   │  │
│   └─────────────────────────────────────────────────────────────┘  │
│         │                      │                                   │
│        SÍ                     NO                                   │
│         │                      │                                   │
│         ▼                      ▼                                   │
│   ┌─────────────┐      ┌─────────────┐                            │
│   │  FASE 2:    │      │  RESULTADO  │                            │
│   │  Entrevista │      │  FINAL      │                            │
│   │  Conversa-  │      │             │                            │
│   │  cional     │      │  Aprobado   │                            │
│   └─────────────┘      └─────────────┘                            │
│         │                                                          │
│         ▼                                                          │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │                    FASE 2: Entrevista                        │  │
│   │                                                             │  │
│   │   Por cada requisito no cumplido:                          │  │
│   │   1. Generar pregunta conversacional                       │  │
│   │   2. Recibir respuesta del candidato                       │  │
│   │   3. Evaluar si la respuesta demuestra cumplimiento        │  │
│   │                                                             │  │
│   │   Resultado: Puntuación recalculada                        │  │
│   └─────────────────────────────────────────────────────────────┘  │
│         │                                                          │
│         ▼                                                          │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │                    RESULTADO FINAL                           │  │
│   │                                                             │  │
│   │   - Puntuación: 0-100%                                     │  │
│   │   - Estado: Aprobado / No aprobado                         │  │
│   │   - Detalle de cada requisito                              │  │
│   └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Características Principales

### 1. Determinismo en Fase 1

- La misma oferta SIEMPRE produce los mismos requisitos
- La misma combinación CV+Oferta SIEMPRE produce la misma evaluación
- Logrado con `temperature=0.0` y Structured Output

### 2. Contexto Temporal

- Sistema referenciado a **enero 2026**
- Cálculos de experiencia correctos independientemente de cuándo se ejecute
- "Python 2020-Presente" = 6 años (no 4)

### 3. Multi-proveedor LLM

- Soporte para **OpenAI**, **Google** y **Anthropic**
- Cambiar de proveedor es cambiar un string
- Fallback automático para embeddings

### 4. Entrevista Conversacional

- Preguntas generadas en **tiempo real con streaming**
- Evaluación objetiva de respuestas
- Experiencia de usuario natural

### 5. RAG para Historial

- Búsqueda semántica en evaluaciones anteriores
- Chatbot que responde preguntas sobre el historial
- Indexación con FAISS

---

## Stack Tecnológico

| Tecnología | Propósito |
|------------|-----------|
| **LangChain** | Interacción con LLMs |
| **LangGraph** | Orquestación de flujos |
| **Pydantic** | Validación de datos |
| **FAISS** | Búsqueda vectorial |
| **Streamlit** | Interfaz de usuario |
| **Playwright** | Scraping web dinámico |
| **Docker** | Despliegue containerizado |

---

## Arquitectura

```
                    ┌─────────────────┐
                    │    FRONTEND     │
                    │   (Streamlit)   │
                    └─────────────────┘
                            │
                            ▼
                    ┌─────────────────┐
                    │  ORQUESTACIÓN   │
                    │  (Orquestador)  │
                    │  (LangGraph)    │
                    └─────────────────┘
                            │
            ┌───────────────┴───────────────┐
            │                               │
            ▼                               ▼
    ┌─────────────────┐           ┌─────────────────┐
    │     NÚCLEO      │           │     NÚCLEO      │
    │  (AnalizadorF1) │           │ (EntrevistadorF2│
    └─────────────────┘           └─────────────────┘
            │                               │
            └───────────────┬───────────────┘
                            │
                            ▼
                    ┌─────────────────┐
                    │ INFRAESTRUCTURA │
                    │  - LLM Factory  │
                    │  - Embeddings   │
                    │  - Extracción   │
                    └─────────────────┘
                            │
                            ▼
                    ┌─────────────────┐
                    │    RECURSOS     │
                    │   (Prompts)     │
                    └─────────────────┘
```

---

## Filosofía de Diseño

### Reduccionismo

- **Sin capas innecesarias**: Cada componente tiene una razón de existir
- **Sin abstracciones injustificadas**: No hay wrappers "por si acaso"
- **Sin duplicación**: DRY aplicado rigurosamente

### Explicabilidad

- **Razonamiento visible**: Cada evaluación incluye el "por qué"
- **Evidencia citada**: Se muestra qué parte del CV respalda cada decisión
- **Confianza indicada**: Alto/Medio/Bajo para cada evaluación

### Reproducibilidad

- **Determinismo**: Misma entrada → Misma salida
- **Versionado**: Sistema con versión semántica (3.1.0)
- **Docker**: Despliegue idéntico en cualquier máquina

---

## Métricas Clave

| Métrica | Valor |
|---------|-------|
| Archivos Python | ~20 |
| Líneas de código | ~3,000 |
| Dependencias directas | 16 |
| Proveedores LLM soportados | 3 |
| Temperatura Fase 1 | 0.0 |
| Temperatura Fase 2 | 0.3 |
| Año de referencia | 2026 |

---

## Puntos Fuertes

1. **Coherencia semántica**: Los prompts garantizan interpretaciones consistentes
2. **Flexibilidad de proveedores**: No hay lock-in a OpenAI
3. **UX de entrevista**: Streaming hace la conversación natural
4. **Trazabilidad**: LangSmith para debugging y evaluación
5. **Despliegue simple**: Un `docker-compose up` y funciona

---

## Limitaciones Conocidas

1. **PDFs escaneados**: No se puede extraer texto de imágenes
2. **Idioma**: Prompts optimizados para español/inglés
3. **Costo**: Cada evaluación consume tokens de API
4. **Velocidad**: Depende de latencia del proveedor LLM

---

## Para Más Información

- **Arquitectura completa**: `03_ARQUITECTURA_SISTEMA.md`
- **Decisiones de diseño**: `04_DECISIONES_DISENO.md`
- **Glosario**: `07_GLOSARIO_TERMINOS.md`
- **Documentación por archivo**: `ficheros/`

