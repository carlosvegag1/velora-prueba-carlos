# AgenticInterviewer: Arquitectura de Agente IA Conversacional

## Introducción

El módulo `agentic_interviewer.py` implementa un **agente de IA conversacional** para la Fase 2 del sistema de evaluación de candidatos. Este documento explica su arquitectura y por qué se clasifica como un **agente de IA** en lugar de un sistema de IA tradicional.

---

## ¿Qué diferencia un Agente de IA de un Sistema de IA?

### Sistema de IA Tradicional

Un sistema de IA tradicional es **reactivo** y **stateless**:

```
[Input] → [Procesamiento] → [Output]
```

**Características:**
- Responde a una entrada y produce una salida
- No mantiene memoria entre interacciones
- No tiene capacidad de planificación
- Flujo de ejecución predeterminado y lineal
- No adapta su comportamiento según el contexto

**Ejemplo:** Un clasificador de texto que recibe un documento y devuelve una categoría.

### Agente de IA

Un agente de IA es **proactivo**, **autónomo** y **stateful**:

```
[Objetivo] → [Percepción] → [Razonamiento] → [Acción] → [Observación] → (ciclo)
```

**Características:**
1. **Autonomía**: Toma decisiones independientes para lograr un objetivo
2. **Estado interno**: Mantiene memoria y contexto entre interacciones
3. **Planificación**: Descompone objetivos complejos en sub-tareas
4. **Adaptabilidad**: Modifica su comportamiento según el contexto
5. **Interacción continua**: Opera en ciclos de percepción-acción
6. **Orientación a objetivos**: Trabaja hacia metas específicas

---

## ¿Por qué AgenticInterviewer es un Agente?

### 1. Autonomía en la Toma de Decisiones

El `AgenticInterviewer` decide autónomamente:

- **Qué preguntar**: Genera preguntas contextualizadas basadas en el requisito y el historial
- **Cómo preguntar**: Adapta el tono y estilo según el tipo de requisito (obligatorio/opcional)
- **Cuándo transicionar**: Gestiona el flujo entre saludo → preguntas → cierre

```python
def stream_question(self, question_idx: int) -> Generator[str, None, None]:
    """
    El agente decide AUTÓNOMAMENTE:
    1. El contenido de la pregunta (basado en requisito)
    2. El estilo conversacional (basado en historial)
    3. Las transiciones entre temas
    """
    requirement = self._pending_requirements[question_idx]
    history_text = self._build_conversation_context()
    
    # El LLM actúa como "cerebro" del agente
    prompt = ChatPromptTemplate.from_messages([
        ("system", AGENTIC_SYSTEM_PROMPT.format(...)),
        ("human", AGENTIC_QUESTION_PROMPT.format(
            requirement=requirement["description"],
            conversation_history=history_text  # Contexto para decisiones
        ))
    ])
```

### 2. Estado Interno Persistente

El agente mantiene **estado entre interacciones**:

```python
class AgenticInterviewer:
    def __init__(self, ...):
        # Estado interno del agente
        self._candidate_name: str = ""           # Identidad del usuario
        self._cv_context: str = ""               # Conocimiento del contexto
        self._pending_requirements: List[...] = [] # Objetivos pendientes
        self._conversation_history: List[...] = [] # Memoria de interacciones
        self._current_idx: int = 0               # Progreso hacia el objetivo
```

**Comparación:**

| Sistema Tradicional | Agente (AgenticInterviewer) |
|---------------------|----------------------------|
| Sin memoria | `_conversation_history` guarda toda la conversación |
| Sin contexto | `_cv_context` y `_candidate_name` personalizan |
| Sin progreso | `_pending_requirements` rastrea objetivos |

### 3. Ciclo Percepción-Acción

El agente opera en un **loop interactivo continuo**:

```
┌─────────────────────────────────────────────────────────────┐
│                    CICLO DEL AGENTE                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   [Percepción]     →    [Razonamiento]    →    [Acción]    │
│   Recibe respuesta      Evalúa contexto       Genera       │
│   del candidato         Decide siguiente      pregunta/    │
│                         paso                  cierre       │
│        ↑                                          │        │
│        └──────────────────────────────────────────┘        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Implementación:**

```python
# PERCEPCIÓN: Recibe input del usuario
def register_response(self, question_idx: int, response: str):
    self._conversation_history.append({
        "role": "user",
        "content": response
    })
    
    # RAZONAMIENTO: Evalúa si continuar o terminar
    is_complete = question_idx + 1 >= len(self._pending_requirements)
    
    return {
        "next_question": None if is_complete else question_idx + 1,
        "is_complete": is_complete  # Decisión autónoma
    }

# ACCIÓN: Genera siguiente interacción
def stream_question(self, question_idx: int):
    # Usa el contexto acumulado para generar respuesta
    history_text = self._build_conversation_context()
    ...
```

### 4. Orientación a Objetivos con Garantía de Cobertura

El agente tiene un **objetivo claro** y trabaja sistemáticamente para lograrlo:

**Objetivo:** Cubrir el 100% de los requisitos faltantes

```python
def validate_coverage(self) -> Dict[str, Any]:
    """
    El agente verifica que TODOS sus objetivos se cumplan.
    Esta es una característica fundamental de agentes: 
    trabajan hacia metas específicas y verificables.
    """
    total = len(self._pending_requirements)
    answered = sum(1 for r in self._pending_requirements if r["answered"])
    
    uncovered = [
        r["description"] for r in self._pending_requirements
        if not r["answered"]
    ]
    
    return {
        "coverage_percentage": (answered / total * 100),
        "is_complete": len(uncovered) == 0  # ¿Objetivo cumplido?
    }
```

### 5. Personalidad y Comportamiento Adaptativo

El agente tiene una **"personalidad"** definida que guía su comportamiento:

```python
AGENTIC_SYSTEM_PROMPT = """Eres Velora, un asistente de entrevistas profesional y empático.

TU PERSONALIDAD:
- Profesional pero cercano y amable
- Empático y motivador
- Claro y directo en tus preguntas
- Genuinamente interesado en conocer al candidato

REGLAS:
1. Mantén un tono conversacional natural, NO un cuestionario rígido
2. Haz transiciones fluidas entre temas
3. Sé conciso (2-3 oraciones máximo por mensaje)
4. Usa emojis con moderación (máximo 1-2 por mensaje)"""
```

---

## Arquitectura del Agente

```
┌─────────────────────────────────────────────────────────────────────┐
│                      AgenticInterviewer                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐  │
│  │   MEMORIA    │    │   CEREBRO    │    │      ACTUADORES      │  │
│  │              │    │    (LLM)     │    │                      │  │
│  │ • Historia   │◄──►│ • Reasoning  │───►│ • stream_greeting()  │  │
│  │ • Contexto   │    │ • Generation │    │ • stream_question()  │  │
│  │ • Objetivos  │    │ • Evaluation │    │ • stream_closing()   │  │
│  └──────────────┘    └──────────────┘    └──────────────────────┘  │
│         ▲                                          │                │
│         │                                          │                │
│         │            ┌──────────────┐              │                │
│         └────────────│   SENSORES   │◄─────────────┘                │
│                      │              │                               │
│                      │ • Respuestas │                               │
│                      │ • Estado     │                               │
│                      └──────────────┘                               │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Componentes del Agente

| Componente | Implementación | Función |
|------------|----------------|---------|
| **Memoria** | `_conversation_history`, `_pending_requirements` | Almacena experiencias y objetivos |
| **Cerebro** | LLM (GPT-4, Gemini, Claude) | Razonamiento y generación |
| **Sensores** | `register_response()`, `get_state()` | Percibe el entorno |
| **Actuadores** | `stream_*()` methods | Ejecuta acciones en el mundo |

---

## Streaming: UX de Agente Moderno

El streaming token-by-token es una característica de **agentes modernos** que simula el proceso de "pensamiento" en tiempo real:

```python
def stream_question(self, question_idx: int) -> Generator[str, None, None]:
    """
    Genera respuesta token por token.
    
    Beneficios:
    1. UX natural - simula pensamiento humano
    2. Feedback inmediato - usuario ve progreso
    3. Reduce latencia percibida
    4. Característica estándar de ChatGPT, Claude, Gemini
    """
    chain = prompt | self.llm | StrOutputParser()
    
    for chunk in chain.stream({}):
        yield chunk  # Cada token se envía inmediatamente
```

---

## Comparativa: Antes vs Después

### Phase2Interviewer Antiguo (Sistema Tradicional)

```python
# Flujo lineal, sin estado, sin adaptación
def generate_questions(self, missing_requirements, ...):
    # Genera TODAS las preguntas de una vez
    result = chain.invoke({...})
    return result.questions  # Output fijo

def conduct_interview(self, ...):
    # Flujo rígido predeterminado
    for question in questions:
        response = input(question)  # Sin adaptación
```

**Problemas:**
- ❌ Sin personalización por contexto
- ❌ Sin memoria entre preguntas
- ❌ Flujo rígido tipo cuestionario
- ❌ Sin streaming (respuestas instantáneas)

### AgenticInterviewer Nuevo (Agente)

```python
# Ciclo interactivo con estado y adaptación
def stream_question(self, question_idx):
    # Considera historial para generar pregunta contextualizada
    history = self._build_conversation_context()
    
    # Streaming token-by-token
    for chunk in chain.stream({...}):
        yield chunk
    
    # Actualiza estado interno
    self._conversation_history.append(...)
```

**Ventajas:**
- ✅ Personalización dinámica
- ✅ Memoria conversacional
- ✅ Flujo natural adaptativo
- ✅ Streaming en tiempo real
- ✅ Orientación a objetivos verificable

---

## Conclusión

El `AgenticInterviewer` se clasifica como un **agente de IA** porque implementa las características fundamentales de la arquitectura de agentes:

1. **Autonomía**: Decide qué preguntar y cómo adaptarse
2. **Estado persistente**: Mantiene memoria y contexto
3. **Ciclo percepción-acción**: Opera en un loop interactivo
4. **Orientación a objetivos**: Garantiza cobertura del 100%
5. **Adaptabilidad**: Personaliza según el candidato y la conversación

Esta arquitectura representa la evolución de sistemas de IA reactivos hacia **agentes conversacionales autónomos**, alineándose con las tendencias modernas de IA agéntica implementadas en productos como ChatGPT, Claude y Gemini.

---

## Referencias

- **LangChain Agents**: https://python.langchain.com/docs/modules/agents/
- **Agentic AI Patterns**: https://www.anthropic.com/research/building-effective-agents
- **ReAct Pattern**: Reasoning + Acting in Language Models

