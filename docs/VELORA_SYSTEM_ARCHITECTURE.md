# VELORA - Sistema de Evaluación de Candidatos
## Documentación Técnico-Estratégica Completa v2.0

---

# PARTE I: VISIÓN TELEOLÓGICA Y RAZÓN DE SER

## 1.1 Propósito Fundamental del Sistema

Velora es un **Sistema de Evaluación de Candidatos Inteligente** cuyo objetivo final es **automatizar y humanizar simultáneamente** el proceso de filtrado de candidatos en procesos de selección de personal.

### Misión Teleológica
El sistema existe para resolver un problema fundamental en recursos humanos: **la brecha entre la objetividad necesaria en la evaluación técnica y la empatía requerida en la interacción humana**. Velora no busca reemplazar el juicio humano, sino potenciarlo mediante:

1. **Automatización del análisis objetivo**: Extracción sistemática de requisitos y matching con CVs
2. **Humanización de la interacción**: Entrevistas conversacionales naturales y empáticas
3. **Trazabilidad completa**: Auditoría y memoria histórica para mejora continua
4. **Democratización tecnológica**: Agnosticismo de proveedor para máxima flexibilidad

### El "Por Qué" Estratégico
```
┌─────────────────────────────────────────────────────────────────────┐
│                    VELORA - PROPÓSITO CENTRAL                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   INPUT                                                   OUTPUT    │
│   ┌──────────┐     ┌─────────────────────┐     ┌──────────────┐   │
│   │ Oferta   │     │                     │     │ Evaluación   │   │
│   │ + CV     │────▶│  ANÁLISIS + DIÁLOGO │────▶│ Objetiva     │   │
│   │ + Diálogo│     │  INTELIGENTE        │     │ + Humanizada │   │
│   └──────────┘     └─────────────────────┘     └──────────────┘   │
│                                                                     │
│   VALOR DIFERENCIAL:                                               │
│   • Objetividad → Reglas claras, sin sesgos                       │
│   • Empatía     → Conversaciones naturales                         │
│   • Memoria     → Aprendizaje del historial                        │
│   • Flexibilidad → Multi-proveedor IA                             │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

# PARTE II: ARQUITECTURA CONCEPTUAL

## 2.1 Filosofía Arquitectónica Central

El sistema se rige por **cinco principios filosóficos fundamentales** que guían cada decisión de diseño:

### Principio 1: SEPARACIÓN DE RESPONSABILIDADES POR FASE
```
┌─────────────────────────────────────────────────────────────────────┐
│                    PIPELINE DE DOS FASES                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   FASE 1: ANÁLISIS DETERMINISTA                                    │
│   ┌───────────────────────────────────────────────────────────┐    │
│   │ • Temperatura LLM: 0.0 - 0.1 (máximo determinismo)        │    │
│   │ • Propósito: Extracción precisa + Matching objetivo       │    │
│   │ • Output: Structured Data (Pydantic)                      │    │
│   │ • Tolerancia a error: CERO                                │    │
│   └───────────────────────────────────────────────────────────┘    │
│                              │                                      │
│                              ▼                                      │
│   FASE 2: INTERACCIÓN CONVERSACIONAL                               │
│   ┌───────────────────────────────────────────────────────────┐    │
│   │ • Temperatura LLM: 0.3 - 0.7 (creatividad controlada)     │    │
│   │ • Propósito: Diálogo natural + Empatía                    │    │
│   │ • Output: Streaming token-by-token                        │    │
│   │ • Tolerancia a error: Fallbacks elegantes                 │    │
│   └───────────────────────────────────────────────────────────┘    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Justificación**: Cada fase tiene requisitos diametralmente opuestos:
- Fase 1 requiere **reproducibilidad y precisión** → temperatura mínima
- Fase 2 requiere **naturalidad y variedad** → temperatura moderada

### Principio 2: AGNOSTICISMO DE PROVEEDOR
```
┌─────────────────────────────────────────────────────────────────────┐
│               ABSTRACCIÓN MULTI-PROVEEDOR                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│                        ┌─────────────┐                             │
│                        │  LLMFactory │                             │
│                        └──────┬──────┘                             │
│                               │                                     │
│              ┌────────────────┼────────────────┐                   │
│              ▼                ▼                ▼                   │
│        ┌──────────┐    ┌──────────┐    ┌──────────┐               │
│        │  OpenAI  │    │  Google  │    │ Anthropic│               │
│        │  GPT-4+  │    │  Gemini  │    │  Claude  │               │
│        └──────────┘    └──────────┘    └──────────┘               │
│                                                                     │
│   DECISIÓN ESTRATÉGICA:                                            │
│   ✓ El código de negocio NUNCA conoce el proveedor                │
│   ✓ Cambio de proveedor = 1 línea de configuración                │
│   ✓ Parámetros cross-provider únicamente                          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Justificación**: 
- El mercado de LLMs evoluciona constantemente
- Dependencia de un solo proveedor = riesgo empresarial
- Flexibilidad para optimizar costos y rendimiento

### Principio 3: STRUCTURED OUTPUT COMO CONTRATO
```
┌─────────────────────────────────────────────────────────────────────┐
│             GARANTÍA DE ESTRUCTURA VÍA PYDANTIC                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   ANTES (parsing manual):                                          │
│   ┌────────────────────────────────────────────────────┐           │
│   │  response = llm.invoke(prompt)                     │           │
│   │  try:                                              │           │
│   │      data = json.loads(response)  # ← PUEDE FALLAR │           │
│   │  except JSONDecodeError:                           │           │
│   │      # Manejo de error complejo                    │           │
│   └────────────────────────────────────────────────────┘           │
│                                                                     │
│   AHORA (structured output):                                       │
│   ┌────────────────────────────────────────────────────┐           │
│   │  llm = llm.with_structured_output(PydanticModel)   │           │
│   │  result: PydanticModel = chain.invoke(input)       │           │
│   │  # ← SIEMPRE un objeto Pydantic válido             │           │
│   └────────────────────────────────────────────────────┘           │
│                                                                     │
│   BENEFICIOS:                                                      │
│   • Eliminación de parsing frágil                                  │
│   • Validación automática por Pydantic                             │
│   • Type hints para IDE y documentación                            │
│   • Contrato explícito LLM ↔ código                               │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Principio 4: TRAZABILIDAD OPERACIONAL
```
┌─────────────────────────────────────────────────────────────────────┐
│              SISTEMA DE LOGGING ESTRATÉGICO                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   OperationalLogger (Singleton)                                    │
│   ┌────────────────────────────────────────────────────────────┐   │
│   │                                                            │   │
│   │  [14:32:15] [CFG] [CONFIG] LLM: OPENAI/gpt-4              │   │
│   │  [14:32:15] [CFG] [CONFIG] Embeddings: ACTIVADO           │   │
│   │  [14:32:16] [START] [FASE 1] Iniciando análisis...        │   │
│   │  [14:32:18] [OK] [EXTRACCION] 12 requisitos extraídos     │   │
│   │  [14:32:20] [OK] [MATCHING] 8/12 cumplidos → 66.7%        │   │
│   │  [14:32:20] [END] [FASE 1] Completada (4200ms)            │   │
│   │                                                            │   │
│   └────────────────────────────────────────────────────────────┘   │
│                                                                     │
│   FILOSOFÍA:                                                       │
│   • Logs INFORMATIVOS, no debug verbose                            │
│   • Timestamps + indicadores de estado                             │
│   • Coloreado ANSI para diferenciación visual                      │
│   • Sin emojis (producción profesional)                            │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Principio 5: COBERTURA GARANTIZADA
```
┌─────────────────────────────────────────────────────────────────────┐
│          GARANTÍA DE COBERTURA AL 100%                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   PROBLEMA: ¿Cómo garantizar que se pregunten TODOS los requisitos?│
│                                                                     │
│   SOLUCIÓN ARQUITECTÓNICA:                                         │
│   ┌────────────────────────────────────────────────────────────┐   │
│   │                                                            │   │
│   │   missing_requirements: List[str]                          │   │
│   │        │                                                   │   │
│   │        ▼                                                   │   │
│   │   ┌───────────────────────────────────────────┐           │   │
│   │   │  pending_requirements = []                │           │   │
│   │   │  for req in missing_requirements:         │           │   │
│   │   │      pending_requirements.append({        │           │   │
│   │   │          "description": req,              │           │   │
│   │   │          "asked": False,  ← TRACKING      │           │   │
│   │   │          "answered": False                │           │   │
│   │   │      })                                   │           │   │
│   │   └───────────────────────────────────────────┘           │   │
│   │                                                            │   │
│   │   VALIDACIÓN: validate_coverage() → coverage == 100%       │   │
│   │                                                            │   │
│   └────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2.2 Arquitectura de Capas

```
┌─────────────────────────────────────────────────────────────────────┐
│                      ARQUITECTURA DE CAPAS                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ╔═══════════════════════════════════════════════════════════════╗ │
│  ║                    CAPA DE PRESENTACIÓN                       ║ │
│  ║  ┌─────────────────────────────────────────────────────────┐  ║ │
│  ║  │              app/streamlit_app.py                       │  ║ │
│  ║  │  • UI moderna con diseño corporativo Velora             │  ║ │
│  ║  │  • Componente de chat con streaming real                │  ║ │
│  ║  │  • Gestión de estado de sesión                          │  ║ │
│  ║  │  • 3 tabs: Evaluación | Historial | Instrucciones       │  ║ │
│  ║  └─────────────────────────────────────────────────────────┘  ║ │
│  ╚═══════════════════════════════════════════════════════════════╝ │
│                              │                                      │
│                              ▼                                      │
│  ╔═══════════════════════════════════════════════════════════════╗ │
│  ║                    CAPA DE ORQUESTACIÓN                       ║ │
│  ║  ┌─────────────────────────────────────────────────────────┐  ║ │
│  ║  │              core/evaluator.py                          │  ║ │
│  ║  │  • CandidateEvaluator: Coordinador principal            │  ║ │
│  ║  │  • Gestión del flujo Fase 1 → Fase 2                    │  ║ │
│  ║  │  • Integración con LangSmith                            │  ║ │
│  ║  └─────────────────────────────────────────────────────────┘  ║ │
│  ╚═══════════════════════════════════════════════════════════════╝ │
│                              │                                      │
│                              ▼                                      │
│  ╔═══════════════════════════════════════════════════════════════╗ │
│  ║                    CAPA DE DOMINIO                            ║ │
│  ║  ┌───────────────┐  ┌──────────────────┐  ┌───────────────┐  ║ │
│  ║  │  analyzer.py  │  │ agentic_inter..  │  │   graph.py    │  ║ │
│  ║  │  Fase 1       │  │ Fase 2 Agéntica  │  │  LangGraph    │  ║ │
│  ║  │  Extraction   │  │ Streaming Chat   │  │  Multi-Agent  │  ║ │
│  ║  └───────────────┘  └──────────────────┘  └───────────────┘  ║ │
│  ║  ┌───────────────┐  ┌──────────────────┐                     ║ │
│  ║  │ embeddings.py │  │   chatbot.py     │                     ║ │
│  ║  │ Semantic      │  │   RAG Chatbot    │                     ║ │
│  ║  │ Matcher       │  │   Historial      │                     ║ │
│  ║  └───────────────┘  └──────────────────┘                     ║ │
│  ╚═══════════════════════════════════════════════════════════════╝ │
│                              │                                      │
│                              ▼                                      │
│  ╔═══════════════════════════════════════════════════════════════╗ │
│  ║                    CAPA DE INFRAESTRUCTURA                    ║ │
│  ║  ┌───────────────┐  ┌──────────────────┐  ┌───────────────┐  ║ │
│  ║  │  factory.py   │  │embeddings_fact..│  │   memory.py   │  ║ │
│  ║  │  LLM Factory  │  │ Embeddings Fact. │  │  User Memory  │  ║ │
│  ║  └───────────────┘  └──────────────────┘  └───────────────┘  ║ │
│  ║  ┌───────────────┐  ┌──────────────────┐  ┌───────────────┐  ║ │
│  ║  │  prompts.py   │  │ hyperparams.py   │  │vectorstore.py │  ║ │
│  ║  │  Centralized  │  │ Context-aware    │  │  FAISS Store  │  ║ │
│  ║  │  Prompts      │  │ Temperature      │  │               │  ║ │
│  ║  └───────────────┘  └──────────────────┘  └───────────────┘  ║ │
│  ╚═══════════════════════════════════════════════════════════════╝ │
│                              │                                      │
│                              ▼                                      │
│  ╔═══════════════════════════════════════════════════════════════╗ │
│  ║                    CAPA DE UTILIDADES                         ║ │
│  ║  ┌───────────────┐  ┌──────────────────┐  ┌───────────────┐  ║ │
│  ║  │    pdf.py     │  │     url.py       │  │ validation.py │  ║ │
│  ║  │  PDF Extract  │  │  Web Scraping    │  │  Score Calc   │  ║ │
│  ║  └───────────────┘  └──────────────────┘  └───────────────┘  ║ │
│  ╚═══════════════════════════════════════════════════════════════╝ │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

# PARTE III: ANÁLISIS DETALLADO DE COMPONENTES

## 3.1 Capa de Modelos de Datos (`models.py`)

### Propósito
Definir los **contratos de datos** del sistema mediante modelos Pydantic que garantizan:
- Validación automática de tipos
- Serialización/deserialización consistente
- Documentación auto-generada
- Compatibilidad con Structured Output de LangChain

### Taxonomía de Modelos

```
┌─────────────────────────────────────────────────────────────────────┐
│                    JERARQUÍA DE MODELOS                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ENUMS (Estados discretos)                                         │
│  ├── RequirementType: obligatory | optional                        │
│  └── ConfidenceLevel: high | medium | low                          │
│                                                                     │
│  MODELOS DE DOMINIO                                                │
│  ├── Requirement: Requisito individual completo                    │
│  ├── InterviewQuestion: Pregunta generada                          │
│  └── InterviewResponse: Respuesta del candidato                    │
│                                                                     │
│  MODELOS DE STRUCTURED OUTPUT (Contrato LLM)                       │
│  ├── ExtractedRequirement: Output de extracción                    │
│  ├── RequirementsExtractionResponse: Lista de requisitos           │
│  ├── RequirementMatch: Resultado de matching                       │
│  ├── CVMatchingResponse: Análisis completo                         │
│  ├── GeneratedQuestion: Pregunta para entrevista                   │
│  └── ResponseEvaluation: Evaluación de respuesta                   │
│                                                                     │
│  MODELOS DE RESULTADO                                              │
│  ├── Phase1Result: Resultado de Fase 1                             │
│  └── EvaluationResult: Resultado final completo                    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Decisión Estratégica: Literal vs Enum en Structured Output
```python
# En Structured Output usamos Literal para compatibilidad LLM:
type: Literal["obligatory", "optional"]  # El LLM genera strings

# En modelos de dominio usamos Enum para type-safety:
type: RequirementType  # El código trabaja con enums
```

**Justificación**: Los LLMs generan strings literales. Usar Literal en el modelo de structured output garantiza parsing correcto. La conversión a Enum ocurre en la capa de dominio.

---

## 3.2 Analizador de Fase 1 (`analyzer.py`)

### Propósito
Ejecutar el análisis objetivo CV vs Oferta con **máxima precisión y reproducibilidad**.

### Flujo de Procesamiento

```
┌─────────────────────────────────────────────────────────────────────┐
│                    FLUJO FASE 1: ANÁLISIS                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   INPUT                                                             │
│   ┌──────────────┐    ┌──────────────┐                             │
│   │ job_offer    │    │     cv       │                             │
│   │ (texto)      │    │   (texto)    │                             │
│   └──────┬───────┘    └──────┬───────┘                             │
│          │                   │                                      │
│          ▼                   │                                      │
│   ┌──────────────────────────┼──────────────────────────────────┐  │
│   │ PASO 1: EXTRACCIÓN DE REQUISITOS                            │  │
│   │ ┌────────────────────────────────────────────────────────┐  │  │
│   │ │ • LLM con Structured Output (RequirementsExtraction)   │  │  │
│   │ │ • Temperatura: 0.0 (máximo determinismo)               │  │  │
│   │ │ • Deduplicación por descripción normalizada            │  │  │
│   │ │ • Output: List[{description, type}]                    │  │  │
│   │ └────────────────────────────────────────────────────────┘  │  │
│   └─────────────────────────────┬───────────────────────────────┘  │
│                                 │                                   │
│                                 ▼                                   │
│   ┌─────────────────────────────┴───────────────────────────────┐  │
│   │ PASO 2: EVIDENCIA SEMÁNTICA (opcional)                      │  │
│   │ ┌────────────────────────────────────────────────────────┐  │  │
│   │ │ • SemanticMatcher indexa CV en FAISS                   │  │  │
│   │ │ • Busca chunks relevantes por requisito                │  │  │
│   │ │ • Añade "pistas semánticas" al prompt de matching      │  │  │
│   │ │ • Output: Dict[req_description, {text, score}]         │  │  │
│   │ └────────────────────────────────────────────────────────┘  │  │
│   └─────────────────────────────┬───────────────────────────────┘  │
│                                 │                                   │
│                                 ▼                                   │
│   ┌─────────────────────────────┴───────────────────────────────┐  │
│   │ PASO 3: MATCHING CV-REQUISITOS                              │  │
│   │ ┌────────────────────────────────────────────────────────┐  │  │
│   │ │ • LLM con Structured Output (CVMatchingResponse)       │  │  │
│   │ │ • Temperatura: 0.1 (mínima variabilidad)               │  │  │
│   │ │ • Evalúa: fulfilled, found_in_cv, evidence, confidence │  │  │
│   │ │ • Output: List[RequirementMatch]                       │  │  │
│   │ └────────────────────────────────────────────────────────┘  │  │
│   └─────────────────────────────┬───────────────────────────────┘  │
│                                 │                                   │
│                                 ▼                                   │
│   ┌─────────────────────────────┴───────────────────────────────┐  │
│   │ PASO 4: CÁLCULO DE SCORE                                    │  │
│   │ ┌────────────────────────────────────────────────────────┐  │  │
│   │ │ • Regla: Si hay obligatorio no cumplido → 0%           │  │  │
│   │ │ • Regla: Todos cumplidos → 100%                        │  │  │
│   │ │ • Regla: Caso general → (cumplidos/total) * 100        │  │  │
│   │ │ • CRÍTICO: missing_requirements incluye TODOS          │  │  │
│   │ │   los no cumplidos para garantizar cobertura Fase 2    │  │  │
│   │ └────────────────────────────────────────────────────────┘  │  │
│   └─────────────────────────────┬───────────────────────────────┘  │
│                                 │                                   │
│                                 ▼                                   │
│   OUTPUT                                                            │
│   ┌──────────────────────────────────────────────────────────┐     │
│   │ Phase1Result:                                            │     │
│   │  • score: float                                          │     │
│   │  • discarded: bool                                       │     │
│   │  • fulfilled_requirements: List[Requirement]             │     │
│   │  • unfulfilled_requirements: List[Requirement]           │     │
│   │  • missing_requirements: List[str] ← CLAVE para Fase 2   │     │
│   │  • analysis_summary: str                                 │     │
│   └──────────────────────────────────────────────────────────┘     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Decisión Estratégica: Semantic Matching como Potenciador

```python
# Sin embeddings: El LLM decide solo basándose en el texto
evidence = match.get("evidence")  # Puede ser impreciso

# Con embeddings: El LLM recibe "pistas" del vectorstore
# [PISTA SEMÁNTICA - Score: 0.78]: "5 años de Python..."
# → Guía al LLM hacia la evidencia más relevante
```

**Justificación**: Los embeddings no reemplazan al LLM; lo **potencian** al pre-filtrar información relevante. Reduce alucinaciones y mejora precision.

---

## 3.3 Entrevistador Agéntico (`agentic_interviewer.py`)

### Propósito
Implementar un **agente conversacional** que:
- Genera preguntas naturales y contextuales
- Mantiene fluidez en la conversación
- Garantiza cobertura del 100% de requisitos
- Produce streaming real token-by-token

### ¿Por Qué es un "Agente" y No Solo un "Sistema"?

```
┌─────────────────────────────────────────────────────────────────────┐
│           AGENTE vs SISTEMA: DIFERENCIAS CLAVE                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   SISTEMA TRADICIONAL:                                             │
│   ┌────────────────────────────────────────────────────────────┐   │
│   │  • Reglas fijas predefinidas                               │   │
│   │  • Input → Proceso determinista → Output                   │   │
│   │  • Sin capacidad de adaptación                             │   │
│   │  • Preguntas template: "¿Tienes experiencia en {X}?"       │   │
│   └────────────────────────────────────────────────────────────┘   │
│                                                                     │
│   AGENTE (AgenticInterviewer):                                     │
│   ┌────────────────────────────────────────────────────────────┐   │
│   │  ✓ AUTONOMÍA: Decide cómo formular cada pregunta           │   │
│   │  ✓ CONTEXTO: Considera CV, historial, respuestas previas   │   │
│   │  ✓ ADAPTACIÓN: Ajusta tono según el flujo conversacional   │   │
│   │  ✓ OBJETIVO: Orientado a completar tarea (cobertura 100%)  │   │
│   │  ✓ PERCEPCIÓN: Procesa respuestas del usuario              │   │
│   │  ✓ MEMORIA: Mantiene contexto de conversación              │   │
│   └────────────────────────────────────────────────────────────┘   │
│                                                                     │
│   CICLO AGÉNTICO:                                                  │
│                                                                     │
│        ┌─────────────────────────────────────────┐                 │
│        │           PERCIBIR                       │                 │
│        │    (respuesta del candidato)            │                 │
│        └──────────────────┬──────────────────────┘                 │
│                           │                                         │
│                           ▼                                         │
│        ┌──────────────────┴──────────────────────┐                 │
│        │            RAZONAR                       │                 │
│        │   (contexto + requisito pendiente)      │                 │
│        └──────────────────┬──────────────────────┘                 │
│                           │                                         │
│                           ▼                                         │
│        ┌──────────────────┴──────────────────────┐                 │
│        │            ACTUAR                        │                 │
│        │   (generar pregunta adaptada)           │                 │
│        └──────────────────┬──────────────────────┘                 │
│                           │                                         │
│                           └──────────► (siguiente ciclo)           │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Arquitectura del Streaming

```
┌─────────────────────────────────────────────────────────────────────┐
│                    STREAMING TOKEN-BY-TOKEN                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   def stream_question(self, question_idx: int):                    │
│       """Genera pregunta con streaming real"""                     │
│                                                                     │
│       chain = prompt | self.llm | StrOutputParser()                │
│                                                                     │
│       for chunk in chain.stream({}):  ← STREAMING REAL DEL LLM    │
│           yield chunk                                               │
│                                                                     │
│   ┌────────────────────────────────────────────────────────────┐   │
│   │                                                            │   │
│   │   "¿" → "Podrías" → " " → "contarme" → " " → "sobre"...   │   │
│   │     │        │           │         │         │             │   │
│   │     ▼        ▼           ▼         ▼         ▼             │   │
│   │   ┌──────────────────────────────────────────────────┐     │   │
│   │   │  st.write_stream() → Renderizado progresivo      │     │   │
│   │   │                                                  │     │   │
│   │   │  UI: "¿Podrías|"  (cursor parpadeante)          │     │   │
│   │   │  UI: "¿Podrías con|"                             │     │   │
│   │   │  UI: "¿Podrías contarme|"                        │     │   │
│   │   │  UI: "¿Podrías contarme sobre|"                  │     │   │
│   │   │  ...                                             │     │   │
│   │   └──────────────────────────────────────────────────┘     │   │
│   │                                                            │   │
│   └────────────────────────────────────────────────────────────┘   │
│                                                                     │
│   BENEFICIO UX:                                                    │
│   • Sensación de "agente pensando"                                 │
│   • Feedback visual inmediato                                      │
│   • Experiencia tipo ChatGPT/Claude                                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3.4 Sistema de Factories (`factory.py`, `embeddings_factory.py`)

### Propósito
Implementar el patrón **Factory** para desacoplar la creación de objetos de su uso, permitiendo **agnosticismo de proveedor**.

### LLMFactory: Abstracción Multi-Proveedor

```
┌─────────────────────────────────────────────────────────────────────┐
│                    LLMFactory - DISEÑO                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   PROBLEMA:                                                        │
│   ┌────────────────────────────────────────────────────────────┐   │
│   │  # Código acoplado a proveedor                             │   │
│   │  from langchain_openai import ChatOpenAI                   │   │
│   │  llm = ChatOpenAI(model="gpt-4", api_key=key)              │   │
│   │                                                            │   │
│   │  # Cambiar a Anthropic requiere modificar código           │   │
│   │  from langchain_anthropic import ChatAnthropic             │   │
│   │  llm = ChatAnthropic(model="claude-3", api_key=key)        │   │
│   └────────────────────────────────────────────────────────────┘   │
│                                                                     │
│   SOLUCIÓN:                                                        │
│   ┌────────────────────────────────────────────────────────────┐   │
│   │  # Código desacoplado                                      │   │
│   │  llm = LLMFactory.create_llm(                              │   │
│   │      provider=config.provider,    # "openai" | "anthropic" │   │
│   │      model_name=config.model,                              │   │
│   │      temperature=config.temp                               │   │
│   │  )                                                         │   │
│   │                                                            │   │
│   │  # Cambio de proveedor = cambio de configuración           │   │
│   │  # El código de negocio NO cambia                          │   │
│   └────────────────────────────────────────────────────────────┘   │
│                                                                     │
│   DETECCIÓN DINÁMICA DE PROVEEDORES:                               │
│   ┌────────────────────────────────────────────────────────────┐   │
│   │  try:                                                      │   │
│   │      from langchain_google_genai import ChatGoogleGenAI    │   │
│   │      GOOGLE_AVAILABLE = True                               │   │
│   │  except ImportError:                                       │   │
│   │      GOOGLE_AVAILABLE = False                              │   │
│   │                                                            │   │
│   │  # Solo muestra proveedores con librerías instaladas       │   │
│   └────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### EmbeddingFactory: Gestión Inteligente de Embeddings

```
┌─────────────────────────────────────────────────────────────────────┐
│              EMBEDDINGS FACTORY - MAPEO 1:1                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   DECISIÓN ARQUITECTÓNICA:                                         │
│   "Un proveedor = Un modelo de embeddings (no configurable)"       │
│                                                                     │
│   MAPEO UNÍVOCO:                                                   │
│   ┌─────────────────────────────────────────────────────┐          │
│   │  openai  → text-embedding-3-small (óptimo costo)    │          │
│   │  google  → models/text-embedding-004 (última)       │          │
│   │  anthropic → NO SOPORTADO (sin API de embeddings)   │          │
│   └─────────────────────────────────────────────────────┘          │
│                                                                     │
│   JUSTIFICACIÓN:                                                   │
│   ✓ Simplifica configuración para usuarios                         │
│   ✓ Evita errores por selección incorrecta de modelo              │
│   ✓ Cada modelo está optimizado para su proveedor                 │
│   ✓ El sistema sabe qué funciona mejor                            │
│                                                                     │
│   FALLBACK INTELIGENTE:                                            │
│   ┌────────────────────────────────────────────────────────────┐   │
│   │  if provider == "anthropic":                               │   │
│   │      # Anthropic no tiene embeddings                       │   │
│   │      fallback = EmbeddingFactory.get_fallback_provider()   │   │
│   │      if fallback:  # Busca OpenAI o Google con API key     │   │
│   │          embeddings = create_embeddings(fallback)          │   │
│   │      else:                                                 │   │
│   │          # Sin embeddings, usar matching directo LLM       │   │
│   │          semantic_matcher = None                           │   │
│   └────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3.5 Sistema de Hiperparámetros (`hyperparameters.py`)

### Propósito
Centralizar y documentar la configuración de temperatura y otros parámetros LLM por **contexto de uso**, no por componente técnico.

### Filosofía de Diseño

```
┌─────────────────────────────────────────────────────────────────────┐
│          HIPERPARAMETRIZACIÓN POR CONTEXTO                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   PROBLEMA: Diferentes tareas requieren diferentes temperaturas    │
│                                                                     │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │  CONTEXTO         │  TEMP │  TOP_P │  JUSTIFICACIÓN         │  │
│   ├───────────────────┼───────┼────────┼────────────────────────┤  │
│   │  phase1_extraction │  0.0  │  0.95  │  Máximo determinismo   │  │
│   │  phase1_matching   │  0.1  │  0.95  │  Precisión en matching │  │
│   │  phase2_interview  │  0.3  │  0.9   │  Naturalidad preguntas │  │
│   │  phase2_evaluation │  0.2  │  0.95  │  Precisión + contexto  │  │
│   │  rag_chatbot       │  0.4  │  0.85  │  Conversación fluida   │  │
│   │  summary           │  0.3  │  0.9   │  Síntesis clara        │  │
│   └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
│   BENEFICIOS:                                                      │
│   • Ajuste centralizado sin tocar código de negocio                │
│   • Documentación de decisiones en un solo lugar                   │
│   • Compatibilidad cross-provider garantizada                      │
│   • Experimentación fácil con diferentes configuraciones           │
│                                                                     │
│   USO:                                                             │
│   ┌────────────────────────────────────────────────────────────┐   │
│   │  from llm.hyperparameters import HyperparametersConfig     │   │
│   │                                                            │   │
│   │  temp = HyperparametersConfig.get_temperature("phase1...")│   │
│   │  config = HyperparametersConfig.get_config("rag_chatbot")  │   │
│   └────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3.6 Sistema de Prompts (`prompts.py`)

### Propósito
Centralizar todos los prompts del sistema para:
- Mantenibilidad única
- Consistencia de estilo
- Versionado de prompts
- A/B testing facilitado

### Taxonomía de Prompts

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ARQUITECTURA DE PROMPTS                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   FASE 1: PROMPTS DE PRECISIÓN                                     │
│   ┌────────────────────────────────────────────────────────────┐   │
│   │  EXTRACT_REQUIREMENTS_PROMPT                               │   │
│   │  • Objetivo: Extraer requisitos de oferta                  │   │
│   │  • Estilo: Instrucciones detalladas y restrictivas         │   │
│   │  • Constraints: NO inventes, NO incluyas descripción       │   │
│   └────────────────────────────────────────────────────────────┘   │
│   ┌────────────────────────────────────────────────────────────┐   │
│   │  MATCH_CV_REQUIREMENTS_PROMPT                              │   │
│   │  • Objetivo: Evaluar cumplimiento de requisitos            │   │
│   │  • Estilo: Criterios objetivos, niveles de confianza       │   │
│   │  • Constraints: No asumas, cita evidencia específica       │   │
│   └────────────────────────────────────────────────────────────┘   │
│                                                                     │
│   FASE 2: PROMPTS CONVERSACIONALES (AGÉNTICOS)                     │
│   ┌────────────────────────────────────────────────────────────┐   │
│   │  AGENTIC_SYSTEM_PROMPT                                     │   │
│   │  • Objetivo: Definir personalidad del agente               │   │
│   │  • Estilo: Profesional, empático, cercano                  │   │
│   │  • Contexto: Nombre candidato, CV, requisitos pendientes   │   │
│   └────────────────────────────────────────────────────────────┘   │
│   ┌────────────────────────────────────────────────────────────┐   │
│   │  AGENTIC_GREETING_PROMPT                                   │   │
│   │  • Objetivo: Saludo personalizado                          │   │
│   │  • Estilo: Cálido, informativo, máximo 3 oraciones         │   │
│   └────────────────────────────────────────────────────────────┘   │
│   ┌────────────────────────────────────────────────────────────┐   │
│   │  AGENTIC_QUESTION_PROMPT                                   │   │
│   │  • Objetivo: Pregunta conversacional sobre requisito       │   │
│   │  • Estilo: Natural, con transición fluida                  │   │
│   │  • Contexto: Historial conversación, CV, tipo requisito    │   │
│   └────────────────────────────────────────────────────────────┘   │
│   ┌────────────────────────────────────────────────────────────┐   │
│   │  AGENTIC_CLOSING_PROMPT                                    │   │
│   │  • Objetivo: Cierre positivo                               │   │
│   │  • Estilo: Agradecimiento, próximos pasos                  │   │
│   └────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3.7 Sistema RAG (`rag/chatbot.py`, `rag/vectorstore.py`)

### Propósito
Implementar **Retrieval-Augmented Generation** para consultas inteligentes sobre el historial de evaluaciones.

### Arquitectura RAG

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ARQUITECTURA RAG                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   FLUJO DE INDEXACIÓN:                                             │
│   ┌────────────────────────────────────────────────────────────┐   │
│   │                                                            │   │
│   │   UserMemory.get_searchable_texts(user_id)                 │   │
│   │         │                                                  │   │
│   │         ▼                                                  │   │
│   │   ┌─────────────────────────────────────────┐              │   │
│   │   │  Textos searchables + Metadatos          │              │   │
│   │   │  • "Evaluación para: AI Engineer..."    │              │   │
│   │   │  • metadata: {score, status, date...}   │              │   │
│   │   └───────────────────┬─────────────────────┘              │   │
│   │                       │                                    │   │
│   │                       ▼                                    │   │
│   │   ┌─────────────────────────────────────────┐              │   │
│   │   │  EmbeddingFactory.create_embeddings()   │              │   │
│   │   │  → Vectorización                        │              │   │
│   │   └───────────────────┬─────────────────────┘              │   │
│   │                       │                                    │   │
│   │                       ▼                                    │   │
│   │   ┌─────────────────────────────────────────┐              │   │
│   │   │  FAISS.from_texts()                     │              │   │
│   │   │  → VectorStore en data/vectors/{user}/  │              │   │
│   │   └─────────────────────────────────────────┘              │   │
│   │                                                            │   │
│   └────────────────────────────────────────────────────────────┘   │
│                                                                     │
│   FLUJO DE CONSULTA:                                               │
│   ┌────────────────────────────────────────────────────────────┐   │
│   │                                                            │   │
│   │   "¿Por qué fui rechazado en mi última evaluación?"        │   │
│   │         │                                                  │   │
│   │         ▼                                                  │   │
│   │   ┌─────────────────────────────────────────┐              │   │
│   │   │  vectorstore.search(query, k=5)         │              │   │
│   │   │  → Top 5 documentos más similares       │              │   │
│   │   └───────────────────┬─────────────────────┘              │   │
│   │                       │                                    │   │
│   │                       ▼                                    │   │
│   │   ┌─────────────────────────────────────────┐              │   │
│   │   │  _format_context(docs)                  │              │   │
│   │   │  → Contexto estructurado para LLM       │              │   │
│   │   └───────────────────┬─────────────────────┘              │   │
│   │                       │                                    │   │
│   │                       ▼                                    │   │
│   │   ┌─────────────────────────────────────────┐              │   │
│   │   │  LLM.invoke({context, question})        │              │   │
│   │   │  → Respuesta contextualizada            │              │   │
│   │   └─────────────────────────────────────────┘              │   │
│   │                                                            │   │
│   └────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Compatibilidad de Embeddings

```
┌─────────────────────────────────────────────────────────────────────┐
│         GESTIÓN DE COMPATIBILIDAD DE VECTORES                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   PROBLEMA: Diferentes proveedores generan vectores de diferentes  │
│   dimensiones. Un índice creado con OpenAI no puede consultarse    │
│   con embeddings de Google (dimensiones incompatibles).            │
│                                                                     │
│   SOLUCIÓN:                                                        │
│   ┌────────────────────────────────────────────────────────────┐   │
│   │  # Al guardar el índice:                                   │   │
│   │  provider_file = store_path / "embedding_provider.txt"     │   │
│   │  provider_file.write_text(self.embedding_provider)         │   │
│   │                                                            │   │
│   │  # Al cargar:                                              │   │
│   │  saved_provider = provider_file.read_text()                │   │
│   │  if saved_provider != self.embedding_provider:             │   │
│   │      logger.warning("Índice incompatible, re-indexando")  │   │
│   │      return  # No cargar, forzar re-indexación             │   │
│   └────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3.8 Memoria de Usuario (`storage/memory.py`)

### Propósito
Persistir y gestionar el historial de evaluaciones por usuario, optimizado para:
- Consultas RAG (texto searchable)
- Estadísticas rápidas
- Auditoría completa

### Modelo EnrichedEvaluation

```
┌─────────────────────────────────────────────────────────────────────┐
│              ENRIQUECIMIENTO DE EVALUACIONES                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   INPUT: EvaluationResult (datos crudos)                           │
│                                                                     │
│   PROCESO DE ENRIQUECIMIENTO:                                      │
│   ┌────────────────────────────────────────────────────────────┐   │
│   │                                                            │   │
│   │  1. Extracción de título:                                  │   │
│   │     • Detecta keywords: "AI Engineer", "Data Scientist"    │   │
│   │     • Busca patrones: "Buscamos un...", "Puesto:..."       │   │
│   │     • Fallback: "Oferta de empleo"                         │   │
│   │                                                            │   │
│   │  2. Cálculo de métricas:                                   │   │
│   │     • fulfilled_count, unfulfilled_obligatory_count        │   │
│   │     • total_requirements, obligatory vs optional           │   │
│   │                                                            │   │
│   │  3. Generación de resúmenes:                               │   │
│   │     • gap_summary: Brechas detectadas                      │   │
│   │     • strengths_summary: Fortalezas                        │   │
│   │     • rejection_reason: Por qué fue rechazado              │   │
│   │                                                            │   │
│   │  4. Texto searchable (para RAG):                           │   │
│   │     • Concatenación de metadatos + requisitos              │   │
│   │     • Formato optimizado para embeddings                   │   │
│   │                                                            │   │
│   └────────────────────────────────────────────────────────────┘   │
│                                                                     │
│   OUTPUT: EnrichedEvaluation (datos listos para storage + RAG)     │
│                                                                     │
│   ALMACENAMIENTO:                                                  │
│   data/user_memory/{user_id}.json                                  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3.9 LangGraph Multi-Agente (`core/graph.py`)

### Propósito
Orquestar la Fase 1 como un **grafo de agentes especializados** usando LangGraph, permitiendo:
- Paralelización potencial
- Streaming de estados intermedios
- Arquitectura extensible

### Grafo de Fase 1

```
┌─────────────────────────────────────────────────────────────────────┐
│              LANGGRAPH - GRAFO DE FASE 1                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│                     ┌─────────────────────┐                        │
│                     │    START            │                        │
│                     └──────────┬──────────┘                        │
│                                │                                    │
│                                ▼                                    │
│                     ┌─────────────────────┐                        │
│                     │ extract_requirements │                        │
│                     │ (Agente Extractor)  │                        │
│                     └──────────┬──────────┘                        │
│                                │                                    │
│                                ▼                                    │
│                     ┌─────────────────────┐                        │
│                     │    embed_cv         │                        │
│                     │ (Agente Embedder)   │                        │
│                     └──────────┬──────────┘                        │
│                                │                                    │
│                                ▼                                    │
│                     ┌─────────────────────┐                        │
│                     │  semantic_match     │                        │
│                     │ (Agente Matcher)    │                        │
│                     └──────────┬──────────┘                        │
│                                │                                    │
│                                ▼                                    │
│                     ┌─────────────────────┐                        │
│                     │  calculate_score    │                        │
│                     │ (Agente Scorer)     │                        │
│                     └──────────┬──────────┘                        │
│                                │                                    │
│                                ▼                                    │
│                     ┌─────────────────────┐                        │
│                     │       END           │                        │
│                     └─────────────────────┘                        │
│                                                                     │
│   ESTADO COMPARTIDO (Phase1State):                                 │
│   ┌────────────────────────────────────────────────────────────┐   │
│   │  job_offer, cv                     ← Inputs                │   │
│   │  requirements                       ← Post-extracción      │   │
│   │  semantic_evidence                  ← Post-embeddings      │   │
│   │  matches                            ← Post-matching        │   │
│   │  score, discarded, fulfilled_...    ← Post-scoring         │   │
│   │  messages: Annotated[List, add]     ← Log acumulativo      │   │
│   └────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Ventaja: Streaming de Estados

```python
# Con LangGraph podemos hacer streaming de estados intermedios:
async for update in graph.astream(initial_state):
    for node_name, node_output in update.items():
        yield {
            "node": node_name,
            "messages": node_output.get("messages", []),
            "state": node_output
        }
        # UI puede mostrar: "Extrayendo requisitos...", "Aplicando embeddings..."
```

---

## 3.10 Extracción de Contenido (`extraction/`)

### URL Scraper (`url.py`)

```
┌─────────────────────────────────────────────────────────────────────┐
│              SCRAPING INTELIGENTE DE OFERTAS                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   ESTRATEGIA DE FALLBACK:                                          │
│                                                                     │
│   ┌──────────────────────────────────────────────────────────────┐ │
│   │                                                              │ │
│   │   1. REQUESTS (HTTP clásico)                                 │ │
│   │      │                                                       │ │
│   │      ├── ¿Contenido JS renderizado? ────────────┐           │ │
│   │      ├── ¿Bloqueo de bots detectado? ───────────┤           │ │
│   │      ├── ¿Sin keywords de oferta? ──────────────┤           │ │
│   │      │                                          │           │ │
│   │      │  ┌───────────────────────────────────────┘           │ │
│   │      │  ▼                                                    │ │
│   │      │  2. PLAYWRIGHT (navegador headless)                   │ │
│   │      │     • Lanza Chromium en modo headless                │ │
│   │      │     • Anti-detección de bots                         │ │
│   │      │     • Scroll para cargar contenido dinámico          │ │
│   │      │     • Espera: networkidle + delays aleatorios        │ │
│   │      │                                                       │ │
│   │      └──────────────────────────────────────────────────────│ │
│   │                                                              │ │
│   └──────────────────────────────────────────────────────────────┘ │
│                                                                     │
│   DETECCIÓN SEMÁNTICA:                                             │
│   ┌────────────────────────────────────────────────────────────┐   │
│   │  JOB_KEYWORDS = [                                          │   │
│   │      "responsabilidades", "requisitos", "experiencia",     │   │
│   │      "ofrecemos", "qué buscamos", "perfil"...              │   │
│   │  ]                                                         │   │
│   │                                                            │   │
│   │  def looks_like_job_offer(text):                           │   │
│   │      matches = sum(1 for kw in JOB_KEYWORDS if kw in text) │   │
│   │      return matches >= 2  # Al menos 2 keywords            │   │
│   └────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

# PARTE IV: EXPERIENCIA DE USUARIO ÓPTIMA

## 4.1 Journey del Usuario

```
┌─────────────────────────────────────────────────────────────────────┐
│                    USER JOURNEY - VELORA                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. CONFIGURACIÓN INICIAL                                          │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐   │  │
│  │  │ Sidebar     │  │ Usuario:    │  │ Proveedor + Modelo  │   │  │
│  │  │ ← Config    │  │ "carlos"    │  │ OpenAI / gpt-4      │   │  │
│  │  │             │  │             │  │                     │   │  │
│  │  └─────────────┘  └─────────────┘  └─────────────────────┘   │  │
│  │                                                              │  │
│  │  → Usuario identifica para historial                        │  │
│  │  → Selección de proveedor IA transparente                   │  │
│  │  → Modelo seleccionable dinámicamente                       │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  2. CARGA DE DATOS                                                 │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                                                              │  │
│  │  ┌─────────────────────┐    ┌─────────────────────┐         │  │
│  │  │ CV                  │    │ OFERTA              │         │  │
│  │  │ ○ Subir archivo     │    │ ○ Pegar texto       │         │  │
│  │  │ ○ Pegar texto       │    │ ○ URL (auto-scrape) │         │  │
│  │  └─────────────────────┘    └─────────────────────┘         │  │
│  │                                                              │  │
│  │  → Múltiples métodos de entrada                             │  │
│  │  → Preview editable del contenido                           │  │
│  │  → Extracción automática de PDF                             │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  3. FASE 1 - ANÁLISIS AUTOMÁTICO                                   │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                                                              │  │
│  │  ┌──────────────────────────────────────────────────────┐   │  │
│  │  │  [████████████████░░░░] 75%                          │   │  │
│  │  │  "Evaluando CV contra 12 requisitos..."             │   │  │
│  │  └──────────────────────────────────────────────────────┘   │  │
│  │                                                              │  │
│  │  → Barra de progreso con mensajes de estado                 │  │
│  │  → Resultados en expanders (cumplidos / no cumplidos)       │  │
│  │  → Score visual con colores semánticos                      │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  4. FASE 2 - ENTREVISTA CONVERSACIONAL                             │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                                                              │  │
│  │  ┌──────────────────────────────────────────────────────┐   │  │
│  │  │ ┌───┐                                                │   │  │
│  │  │ │ V │ Velora: ¡Hola Carlos! 👋 He revisado tu CV...  │   │  │
│  │  │ └───┘ ████████|  (streaming cursor)                 │   │  │
│  │  └──────────────────────────────────────────────────────┘   │  │
│  │                                                              │  │
│  │  ┌──────────────────────────────────────────────────────┐   │  │
│  │  │        Carlos: Tengo 3 años de experiencia con...    │   │  │
│  │  │                                           [Enviar]   │   │  │
│  │  └──────────────────────────────────────────────────────┘   │  │
│  │                                                              │  │
│  │  → Streaming real token-by-token                            │  │
│  │  → Indicador de progreso (pregunta 2/5)                     │  │
│  │  → Pills visuales de avance                                 │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  5. RESULTADO FINAL                                                │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                                                              │  │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐         │  │
│  │  │  78.5%  │  │ APROBADO│  │  11/14  │  │  3/14   │         │  │
│  │  │ Score   │  │ Estado  │  │Cumplidos│  │No cumpli│         │  │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘         │  │
│  │                                                              │  │
│  │  → Métricas visuales claras                                 │  │
│  │  → Desglose de requisitos                                   │  │
│  │  → Guardado automático en historial                         │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  6. MI HISTORIAL (RAG)                                             │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                                                              │  │
│  │  "¿Por qué fui rechazado en mi última evaluación?"          │  │
│  │                                                              │  │
│  │  Velora: Según tu historial, en la evaluación del           │  │
│  │  15/12/2024 para "AI Engineer" fuiste rechazado             │  │
│  │  porque no cumplías el requisito obligatorio de             │  │
│  │  "5 años de experiencia con PyTorch"...                     │  │
│  │                                                              │  │
│  │  → Consulta natural en lenguaje humano                      │  │
│  │  → Búsqueda semántica en historial                          │  │
│  │  → Respuesta contextualizada                                │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

# PARTE V: MAPAS CONCEPTUALES

## 5.1 Mapa de Dependencias entre Módulos

```
┌─────────────────────────────────────────────────────────────────────┐
│               MAPA DE DEPENDENCIAS                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│                        streamlit_app.py                             │
│                              │                                      │
│              ┌───────────────┼───────────────┐                     │
│              │               │               │                     │
│              ▼               ▼               ▼                     │
│        evaluator.py    HistoryChatbot   UserMemory                 │
│              │               │               │                     │
│     ┌────────┼────────┐      │               │                     │
│     │        │        │      │               │                     │
│     ▼        ▼        ▼      ▼               │                     │
│ analyzer  agentic_   graph  vectorstore ─────┘                     │
│    │     interviewer   │        │                                   │
│    │        │         │        │                                   │
│    │    ┌───┴───┐     │        │                                   │
│    │    │       │     │        │                                   │
│    ▼    ▼       │     ▼        ▼                                   │
│ embeddings   prompts  │   EmbeddingFactory                         │
│    │            │     │        │                                   │
│    │            │     │        │                                   │
│    ▼            ▼     ▼        ▼                                   │
│    └────────────┴─────┴────────┘                                   │
│                   │                                                 │
│                   ▼                                                 │
│              LLMFactory                                            │
│                   │                                                 │
│      ┌────────────┼────────────┐                                   │
│      ▼            ▼            ▼                                   │
│   OpenAI      Google      Anthropic                                │
│                                                                     │
│                                                                     │
│   LEYENDA:                                                         │
│   ─────── Dependencia directa (import)                             │
│   ═══════ Dependencia de datos (modelos compartidos)               │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## 5.2 Mapa de Flujo de Datos

```
┌─────────────────────────────────────────────────────────────────────┐
│                    FLUJO DE DATOS END-TO-END                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                     DATOS DE ENTRADA                         │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │   │
│  │  │ CV (txt) │  │ CV (pdf) │  │ Oferta   │  │ Oferta   │     │   │
│  │  │          │  │          │  │ (texto)  │  │ (URL)    │     │   │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘     │   │
│  │       │             │             │             │            │   │
│  │       ▼             ▼             │             ▼            │   │
│  │  ┌─────────┐  ┌───────────┐       │       ┌──────────┐      │   │
│  │  │ string  │  │ pdf.py    │       │       │ url.py   │      │   │
│  │  │         │  │ extract   │       │       │ scrape   │      │   │
│  │  └────┬────┘  └─────┬─────┘       │       └────┬─────┘      │   │
│  │       │             │             │            │             │   │
│  │       └─────────────┴─────────────┴────────────┘             │   │
│  │                         │                                    │   │
│  │                         ▼                                    │   │
│  │              ┌───────────────────────┐                      │   │
│  │              │  cv_text, offer_text  │                      │   │
│  │              └───────────┬───────────┘                      │   │
│  └──────────────────────────┼──────────────────────────────────┘   │
│                             │                                       │
│                             ▼                                       │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                        FASE 1                                 │  │
│  │                                                              │  │
│  │  offer_text ──▶ extract_requirements() ──▶ requirements[]   │  │
│  │                                                              │  │
│  │  cv_text ──────▶ index_cv() ──────────────▶ FAISS vectors   │  │
│  │                                                              │  │
│  │  requirements + cv + vectors ──▶ match() ──▶ matches[]      │  │
│  │                                                              │  │
│  │  matches[] ──▶ calculate_score() ──▶ Phase1Result           │  │
│  │                                                              │  │
│  └──────────────────────────┬───────────────────────────────────┘  │
│                             │                                       │
│              ┌──────────────┴──────────────┐                       │
│              │                             │                       │
│              ▼                             ▼                       │
│    ┌──────────────────┐          ┌──────────────────┐             │
│    │ discarded=True   │          │ missing_reqs > 0 │             │
│    │ → Guardar y fin  │          │ → Ir a FASE 2    │             │
│    └──────────────────┘          └────────┬─────────┘             │
│                                           │                        │
│                                           ▼                        │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                        FASE 2                                 │  │
│  │                                                              │  │
│  │  for req in missing_requirements:                           │  │
│  │      question = stream_question(req) ──────▶ UI (streaming) │  │
│  │      answer = user_input() ◀────────────── UI              │  │
│  │      register_response(answer)                              │  │
│  │                                                              │  │
│  │  interview_responses[] ──▶ reevaluate() ──▶ EvaluationResult│  │
│  │                                                              │  │
│  └──────────────────────────┬───────────────────────────────────┘  │
│                             │                                       │
│                             ▼                                       │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                     PERSISTENCIA                              │  │
│  │                                                              │  │
│  │  EvaluationResult ──▶ create_enriched_evaluation()          │  │
│  │                               │                              │  │
│  │                               ▼                              │  │
│  │                       EnrichedEvaluation                     │  │
│  │                       • searchable_text (RAG)               │  │
│  │                       • metadata (stats)                    │  │
│  │                               │                              │  │
│  │              ┌────────────────┴────────────────┐            │  │
│  │              │                                 │            │  │
│  │              ▼                                 ▼            │  │
│  │  ┌───────────────────────┐       ┌────────────────────────┐│  │
│  │  │ data/user_memory/     │       │ data/vectors/{user}/   ││  │
│  │  │ {user}.json           │       │ index.faiss            ││  │
│  │  │ (JSON completo)       │       │ (embeddings)           ││  │
│  │  └───────────────────────┘       └────────────────────────┘│  │
│  │                                                              │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

# PARTE VI: DECISIONES TÉCNICAS CLAVE

## 6.1 Tabla de Decisiones Arquitectónicas

| # | Decisión | Alternativas Consideradas | Elección | Justificación |
|---|----------|---------------------------|----------|---------------|
| 1 | Framework LLM | LangChain, LlamaIndex, raw APIs | **LangChain** | Structured Output nativo, multi-provider, LangGraph integrado |
| 2 | Validación datos | JSON parsing manual, Marshmallow | **Pydantic** | Integración nativa LangChain, type hints, auto-docs |
| 3 | Vector store | Pinecone, Weaviate, Chroma, FAISS | **FAISS** | Local (sin cloud), rápido, suficiente para scale actual |
| 4 | Frontend | Flask + React, FastAPI + Vue, Gradio | **Streamlit** | Prototipado rápido, Python puro, suficiente para POC |
| 5 | Multi-agente | Custom orchestration, AutoGen | **LangGraph** | Grafo de estados tipado, streaming nativo, mismo ecosistema |
| 6 | Temperatura | Fija global, por componente | **Por contexto** | Diferentes tareas requieren diferentes creatividades |
| 7 | Embeddings | Modelo configurable | **Mapeo 1:1** | Simplifica UX, evita errores de selección |
| 8 | Logging | print, logging estándar | **OperationalLogger** | Trazabilidad estructurada, colores ANSI, singleton |
| 9 | Persistencia | SQLite, MongoDB | **JSON files** | Simplicidad, suficiente para POC, fácil debug |
| 10 | Scraping | BeautifulSoup only | **Requests + Playwright** | Fallback para SPAs y sitios con JS |

---

## 6.2 Trade-offs Conscientes

### Trade-off 1: Simplicidad vs Escalabilidad
```
ELECCIÓN: JSON files para persistencia

✓ GANAMOS: 
  • Cero configuración de BD
  • Debug fácil (archivos legibles)
  • Sin dependencias externas

✗ SACRIFICAMOS:
  • Queries complejas
  • Concurrencia de escritura
  • Escalabilidad a millones de usuarios

MITIGACIÓN:
  → Abstracción via UserMemory permite migrar a BD sin tocar dominio
```

### Trade-off 2: Precisión vs Latencia
```
ELECCIÓN: Embeddings opcionales con fallback

✓ GANAMOS:
  • Mejor precisión en matching (cuando disponible)
  • Funcionalidad básica garantizada (sin embeddings)

✗ SACRIFICAMOS:
  • Latencia adicional (indexación + búsqueda)
  • Dependencia de proveedor de embeddings

MITIGACIÓN:
  → Checkbox en UI para habilitar/deshabilitar
  → Fallback automático si proveedor no soporta
```

### Trade-off 3: Flexibilidad vs Complejidad
```
ELECCIÓN: Multi-proveedor desde día 1

✓ GANAMOS:
  • Sin vendor lock-in
  • Optimización de costos posible
  • A/B testing de modelos

✗ SACRIFICAMOS:
  • Complejidad en factories
  • Testing de más combinaciones
  • Features provider-specific no usables

MITIGACIÓN:
  → Factories encapsulan complejidad
  → Solo parámetros cross-provider
```

---

# PARTE VII: GLOSARIO Y CONVENCIONES

## 7.1 Glosario del Sistema

| Término | Definición |
|---------|------------|
| **Fase 1** | Análisis automático CV vs Oferta sin interacción del usuario |
| **Fase 2** | Entrevista conversacional para requisitos no verificables |
| **Requisito Obligatorio** | Requisito que si no se cumple → candidato descartado (score 0%) |
| **Requisito Opcional** | Requisito deseable que afecta score pero no descarta |
| **Structured Output** | Respuesta del LLM garantizada en formato Pydantic |
| **Semantic Matching** | Uso de embeddings para encontrar evidencia semántica |
| **Cobertura** | % de requisitos pendientes que fueron preguntados en Fase 2 |
| **EnrichedEvaluation** | Evaluación con metadatos adicionales para RAG |
| **OperationalLogger** | Sistema de logging estratégico del sistema |

## 7.2 Convenciones de Código

```python
# IMPORTS: Orden estándar
import logging              # 1. Standard library
from typing import ...      # 2. Typing

from langchain_core import  # 3. Third-party
from pydantic import        

from ..models import        # 4. Local (relative)
from .logging_config import 

# CLASES: PascalCase
class CandidateEvaluator:
class Phase1Analyzer:

# FUNCIONES: snake_case
def extract_requirements():
def stream_greeting():

# CONSTANTES: UPPER_SNAKE_CASE
EXTRACT_REQUIREMENTS_PROMPT = """..."""
VELORA_PRIMARY = "#00B4D8"

# MÉTODOS PRIVADOS: _prefijo
def _init_semantic_matcher():
def _generate_summary():

# LOGGER: Módulo-level
logger = logging.getLogger(__name__)
```

---

# PARTE VIII: CONCLUSIÓN

## El Sistema Velora encapsula una filosofía de diseño que prioriza:

1. **Objetividad + Empatía**: Análisis preciso con interacción humana
2. **Flexibilidad + Simplicidad**: Multi-proveedor sin complejidad expuesta
3. **Robustez + Elegancia**: Garantías fuertes con UX fluida
4. **Trazabilidad + Privacidad**: Logs operacionales sin datos sensibles
5. **Extensibilidad + Coherencia**: Arquitectura modular unificada

El sistema está diseñado para evolucionar: de POC a producción, de single-user a multi-tenant, de JSON a bases de datos, **sin reescrituras fundamentales**.

---

*Documentación generada como análisis exhaustivo del sistema Velora v2.0*
*Última actualización: Diciembre 2024*

