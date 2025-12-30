# Informe Completo del Sistema de Evaluación de Candidatos con IA

## Índice

1. [Introducción](#1-introducción)
2. [Visión General del Sistema](#2-visión-general-del-sistema)
3. [Arquitectura Técnica](#3-arquitectura-técnica)
4. [Componentes del Sistema](#4-componentes-del-sistema)
5. [Flujo de Evaluación Detallado](#5-flujo-de-evaluación-detallado)
6. [Tecnologías y Frameworks](#6-tecnologías-y-frameworks)
7. [Mejoras Implementadas](#7-mejoras-implementadas)
8. [Experiencia de Usuario](#8-experiencia-de-usuario)
9. [Ejemplos de Uso](#9-ejemplos-de-uso)
10. [Limitaciones Conocidas](#10-limitaciones-conocidas)
11. [Ideas Futuras](#11-ideas-futuras)
12. [Glosario Técnico](#12-glosario-técnico)

---

## 1. Introducción

### 1.1 ¿Qué es este sistema?

Este sistema es un **evaluador automático de candidatos** que utiliza Inteligencia Artificial para analizar si una persona cumple con los requisitos de una oferta de trabajo. Funciona leyendo el currículum (CV) del candidato y comparándolo con los requisitos de la oferta.

**Para usuarios no técnicos:** Imagina un asistente virtual que lee el CV de una persona y la descripción del puesto, y te dice: "Esta persona cumple 7 de 13 requisitos, aquí está la evidencia de cada uno, y estoy 95% seguro de esta evaluación".

**Para usuarios técnicos:** Es un sistema basado en LangChain que utiliza Structured Output para garantizar respuestas tipadas del LLM, embeddings semánticos con FAISS para búsqueda de evidencia, y opcionalmente LangGraph para orquestación multi-agente.

### 1.2 ¿Cuál es el problema que resuelve?

El proceso tradicional de revisión de CVs tiene varios problemas:

| Problema | Impacto | Solución del Sistema |
|----------|---------|---------------------|
| Revisar CVs manualmente consume tiempo | Un reclutador puede tardar 6-7 minutos por CV | El sistema evalúa en 30-60 segundos |
| Sesgo humano en la evaluación | Diferentes reclutadores dan diferentes resultados | Criterios objetivos y consistentes |
| Olvido de requisitos | Es fácil pasar por alto requisitos importantes | Evaluación exhaustiva de todos los requisitos |
| Falta de trazabilidad | No se documenta por qué se aceptó/rechazó | Cada decisión tiene evidencia y razonamiento |

### 1.3 Principios de Diseño

El sistema fue construido siguiendo dos principios fundamentales:

1. **Vanguardia Tecnológica**: Utilizar las capacidades más avanzadas del framework LangChain, incluyendo:
 - Structured Output (respuestas tipadas)
 - Embeddings semánticos
 - LangGraph para orquestación
 - LangSmith para trazabilidad

2. **Sencillez Operativa**: Mantener el código limpio, sin complejidad innecesaria, y con una interfaz de usuario intuitiva.

---

## 2. Visión General del Sistema

### 2.1 Diagrama de Alto Nivel

```
┌─────────────────────────────────────────────────────────────────┐
│ SISTEMA DE EVALUACIÓN │
├─────────────────────────────────────────────────────────────────┤
│ │
│ ┌──────────────┐ ┌──────────────┐ │
│ │ OFERTA │ │ CV │ │
│ │ DE EMPLEO │ │ CANDIDATO │ │
│ └──────┬───────┘ └──────┬───────┘ │
│ │ │ │
│ ▼ ▼ │
│ ┌──────────────────────────────────────┐ │
│ │ FASE 1: ANÁLISIS │ │
│ │ ┌────────────────────────────────┐ │ │
│ │ │ 1. Extraer requisitos │ │ │
│ │ │ 2. Buscar evidencia semántica │ │ │
│ │ │ 3. Hacer matching con LLM │ │ │
│ │ │ 4. Calcular puntuación │ │ │
│ │ └────────────────────────────────┘ │ │
│ └──────────────┬───────────────────────┘ │
│ │ │
│ ▼ │
│ ┌──────────────┐ │
│ │ ¿Descartado? │ │
│ └──────┬───────┘ │
│ │ │
│ ┌──────────┴──────────┐ │
│ │ SÍ NO│ │
│ ▼ ▼ │
│ ┌─────────┐ ┌──────────────────────┐ │
│ │ FIN: 0% │ │ FASE 2: ENTREVISTA │ │
│ │Rechazado│ │ (si hay requisitos │ │
│ └─────────┘ │ faltantes) │ │
│ └──────────────────────┘ │
│ │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Las Dos Fases de Evaluación

#### Fase 1: Análisis Automático

Esta fase es **completamente automática**. El sistema:

1. **Lee la oferta de empleo** y extrae los requisitos (obligatorios y opcionales)
2. **Lee el CV** del candidato
3. **Compara** cada requisito con el CV
4. **Calcula una puntuación** basada en cuántos requisitos cumple

**Resultado de esta fase:**
- Puntuación (0-100%)
- Lista de requisitos cumplidos (con evidencia)
- Lista de requisitos no cumplidos
- Decisión: Descartado o Continúa

#### Fase 2: Entrevista Interactiva

Esta fase ocurre **solo si**:
- El candidato NO fue descartado en Fase 1
- Hay requisitos que no se encontraron en el CV

El sistema genera preguntas específicas para cada requisito faltante, permitiendo al candidato demostrar que cumple esos requisitos mediante sus respuestas.

---

## 3. Arquitectura Técnica

### 3.1 Estructura de Directorios

```
velora_auto/
├── app/
│ └── streamlit_app.py # Interfaz de usuario web
├── src/
│ └── evaluator/
│ ├── __init__.py # Exports públicos del paquete
│ ├── models.py # Modelos de datos (Pydantic)
│ ├── core/
│ │ ├── analyzer.py # Lógica de Fase 1
│ │ ├── interviewer.py # Lógica de Fase 2
│ │ ├── evaluator.py # Orquestador principal
│ │ ├── embeddings.py # Búsqueda semántica
│ │ └── graph.py # Orquestación LangGraph
│ ├── llm/
│ │ ├── factory.py # Creación de LLMs
│ │ └── prompts.py # Prompts del sistema
│ ├── extraction/
│ │ ├── pdf.py # Extracción de PDFs
│ │ └── url.py # Scraping de URLs
│ ├── processing/
│ │ └── validation.py # Utilidades de validación
│ └── storage/
│ └── memory.py # Persistencia de datos
├── docs/ # Documentación
├── requirements.txt # Dependencias Python
└── README.md # Documentación principal
```

### 3.2 Principio de Responsabilidad Única

Cada archivo tiene una responsabilidad clara:

| Archivo | Responsabilidad |
|---------|-----------------|
| `analyzer.py` | Extraer requisitos y hacer matching |
| `interviewer.py` | Generar preguntas y evaluar respuestas |
| `evaluator.py` | Coordinar Fase 1 y Fase 2 |
| `embeddings.py` | Buscar evidencia semántica en el CV |
| `graph.py` | Orquestación multi-agente con LangGraph |
| `factory.py` | Crear instancias de LLM de cualquier proveedor |
| `prompts.py` | Definir los prompts que usa la IA |
| `models.py` | Definir la estructura de los datos |

### 3.3 Flujo de Datos

```
ENTRADA PROCESAMIENTO SALIDA
─────── ───────────── ──────

Oferta ─────┐
(texto) │
 ▼
 ┌─────────────────┐
 │ EXTRACCIÓN DE │
 │ REQUISITOS │
 │ (LLM + JSON) │
 └────────┬────────┘
 │
 ▼
 ┌─────────────────┐
 │ Lista de │
 │ Requisitos │──────┐
 │ [{desc, tipo}] │ │
 └─────────────────┘ │
 │
CV ─────┐ │
(texto) │ │
 ▼ │
 ┌─────────────────┐ │
 │ EMBEDDINGS │ │
 │ SEMÁNTICOS │ │
 │ (FAISS) │ │
 └────────┬────────┘ │
 │ │
 ▼ │
 ┌─────────────────┐ │
 │ Evidencia │ │
 │ por requisito │◄─────┘
 └────────┬────────┘
 │
 ▼
 ┌─────────────────┐
 │ MATCHING │ ┌─────────────────┐
 │ (LLM) │──────►│ Phase1Result │
 │ + Confianza │ │ - score │
 └─────────────────┘ │ - cumplidos │
 │ - no cumplidos │
 │ - evidencia │
 │ - razonamiento │
 └─────────────────┘
```

---

## 4. Componentes del Sistema

### 4.1 Modelos de Datos (`models.py`)

Los modelos de datos definen la estructura de la información que fluye por el sistema. Utilizan **Pydantic**, una librería que garantiza que los datos siempre tengan el formato correcto.

#### 4.1.1 RequirementType (Tipo de Requisito)

```python
class RequirementType(str, Enum):
 OBLIGATORY = "obligatory" # Imprescindible
 OPTIONAL = "optional" # Deseable
```

**¿Por qué es importante?**
- Si un requisito es **obligatorio** y no se cumple, el candidato es descartado automáticamente (puntuación = 0%)
- Si un requisito es **opcional** y no se cumple, simplemente baja la puntuación

#### 4.1.2 ConfidenceLevel (Nivel de Confianza)

```python
class ConfidenceLevel(str, Enum):
 HIGH = "high" # Evidencia explícita
 MEDIUM = "medium" # Evidencia inferida
 LOW = "low" # Sin evidencia clara
```

**¿Qué significa cada nivel?**

| Nivel | Descripción | Ejemplo |
|-------|-------------|---------|
| HIGH | El CV dice exactamente lo que busco | CV: "5 años de Python" Requisito: "3 años de Python" |
| MEDIUM | Puedo inferirlo pero no está explícito | CV: "Uso Python" Requisito: "Experiencia Python avanzada" |
| LOW | No hay información clara | CV: No menciona nada Requisito: "Certificación AWS" |

#### 4.1.3 Requirement (Requisito)

Un requisito completo incluye:

```python
class Requirement(BaseModel):
 description: str # "5 años de experiencia en Python"
 type: RequirementType # OBLIGATORY / OPTIONAL
 fulfilled: bool # ¿Cumplido?
 found_in_cv: bool # ¿Encontrado en el CV?
 evidence: Optional[str] # "Perfil: 6 años como Python developer"
 confidence: ConfidenceLevel # HIGH / MEDIUM / LOW
 reasoning: Optional[str] # "El CV indica 6 años, supera los 5 requeridos"
 semantic_score: Optional[float] # 0.85 (similitud semántica)
```

### 4.2 Analizador de Fase 1 (`analyzer.py`)

Este es el corazón del sistema. Realiza tres operaciones principales:

#### 4.2.1 Extracción de Requisitos

**Entrada:** Texto de la oferta de empleo
**Salida:** Lista de requisitos estructurados

```
OFERTA DE EMPLEO REQUISITOS EXTRAÍDOS
───────────────── ────────────────────

"Lo que necesitamos: [
- 5 años de Python (obligatorio) ───► {desc: "5 años Python", type: "obligatory"},
- Inglés C1 (obligatorio) ───► {desc: "Inglés C1", type: "obligatory"},
 ]
Nos encantaría: [
- Certificación AWS" ───► {desc: "Certificación AWS", type: "optional"}
 ]
```

**¿Cómo funciona?**

1. El sistema envía la oferta al LLM con un prompt especializado
2. El LLM está configurado con **Structured Output** para devolver JSON válido
3. El sistema recibe una lista de objetos Python tipados (no texto)

**Ventaja del Structured Output:**
- Sin él: El LLM podría devolver texto malformado Error
- Con él: Siempre recibimos datos válidos Fiabilidad

#### 4.2.2 Búsqueda de Evidencia Semántica

**Entrada:** CV + Lista de requisitos
**Salida:** Fragmentos del CV relevantes para cada requisito

Esta función utiliza **embeddings** (representaciones numéricas del significado):

```
REQUISITO: "Experiencia con microservicios"

CV (dividido en fragmentos):
┌────────────────────────────────────────────────────────────┐
│ Fragmento 1: "Educación: Grado en Informática..." │ Score: 0.12
│ Fragmento 2: "Migración de monolito a microservicios..." │ Score: 0.89 ◄── ¡MATCH!
│ Fragmento 3: "Idiomas: Español nativo, Inglés B2..." │ Score: 0.15
└────────────────────────────────────────────────────────────┘

RESULTADO: "Migración de monolito a microservicios..." (Score: 0.89)
```

**¿Qué es un embedding?**

Para usuarios no técnicos: Es como convertir palabras en coordenadas en un mapa. Palabras con significado similar quedan cerca.

Para usuarios técnicos: Es un vector de alta dimensionalidad (1536 dimensiones para OpenAI) que captura el significado semántico del texto. Usamos FAISS para búsqueda eficiente de vecinos cercanos.

#### 4.2.3 Matching con LLM

**Entrada:** CV + Requisitos + Evidencia semántica
**Salida:** Evaluación de cada requisito

```
PROMPT AL LLM:
─────────────

"CV del candidato: [...]

Requisitos a evaluar:
- [OBLIGATORY] 5 años de Python
 [PISTA SEMÁNTICA - Score: 0.91]: "Desarrollador con 6 años de experiencia..."

Para cada requisito, indica:
1. ¿Cumplido? (true/false)
2. Confianza (high/medium/low)
3. Evidencia (texto del CV)
4. Razonamiento (explicación)"

RESPUESTA ESTRUCTURADA:
───────────────────────

{
 "matches": [
 {
 "requirement_description": "5 años de Python",
 "fulfilled": true,
 "confidence": "high",
 "evidence": "Desarrollador con 6 años de experiencia...",
 "reasoning": "El CV indica 6 años, supera los 5 requeridos"
 }
 ]
}
```

### 4.3 Entrevistador de Fase 2 (`interviewer.py`)

Este componente genera preguntas y evalúa respuestas para los requisitos que no se encontraron en el CV.

#### 4.3.1 Generación de Preguntas

```
REQUISITO FALTANTE PREGUNTA GENERADA
────────────────── ──────────────────

"Certificación AWS" ───► "¿Podrías describir tu experiencia
 con servicios de AWS y si tienes
 alguna certificación oficial?"
```

#### 4.3.2 Evaluación de Respuestas

```
RESPUESTA DEL CANDIDATO EVALUACIÓN
─────────────────────── ──────────

"Uso AWS diariamente en mi trabajo. {
Tengo la certificación Solutions fulfilled: true,
Architect Associate desde 2022." confidence: "high",
 evidence: "Cert. Solutions Architect 2022"
 }
```

### 4.4 LangGraph para Orquestación (`graph.py`)

LangGraph permite estructurar el flujo de la Fase 1 como un **grafo de estados** con nodos especializados.

#### 4.4.1 ¿Qué es un Grafo de Estados?

Para usuarios no técnicos: Es como un diagrama de flujo donde cada caja hace una tarea específica y pasa el resultado a la siguiente.

Para usuarios técnicos: Es un StateGraph de LangGraph con nodos que representan agentes especializados y edges que definen el flujo de ejecución.

#### 4.4.2 Nodos del Grafo

```
┌───────────────────┐
│ extract_requirements │ Nodo 1: Extractor
│ │ - Recibe: oferta de empleo
│ │ - Produce: lista de requisitos
└──────────┬───────────┘
 │
 ▼
┌───────────────────┐
│ embed_cv │ Nodo 2: Embedder
│ │ - Recibe: CV + requisitos
│ │ - Produce: evidencia semántica
└──────────┬─────────┘
 │
 ▼
┌───────────────────┐
│ semantic_match │ Nodo 3: Matcher
│ │ - Recibe: CV + requisitos + evidencia
│ │ - Produce: lista de matches
└──────────┬─────────┘
 │
 ▼
┌───────────────────┐
│ calculate_score │ Nodo 4: Scorer
│ │ - Recibe: matches
│ │ - Produce: Phase1Result
└────────────────────┘
```

#### 4.4.3 Ventajas de LangGraph

| Ventaja | Descripción |
|---------|-------------|
| **Modularidad** | Cada nodo es una unidad independiente y testeable |
| **Observabilidad** | Cada paso emite mensajes de progreso |
| **Extensibilidad** | Fácil añadir nuevos nodos (ej: validación humana) |
| **Streaming** | Permite mostrar progreso en tiempo real |
| **Recuperación** | Posibilidad de reintentar nodos fallidos |

### 4.5 Embeddings Semánticos (`embeddings.py`)

Este módulo implementa la búsqueda de evidencia usando vectores semánticos.

#### 4.5.1 Proceso de Indexación

```
CV ORIGINAL CHUNKS INDEXADOS EN FAISS
─────────── ─────────────────────────

"CARLOS MARTÍNEZ [Vector 1536D] "Carlos Martínez, Full-Stack..."
Full-Stack Developer [Vector 1536D] "TechSolutions: Django, React..."
 [Vector 1536D] "StartupXYZ: Flask, FastAPI..."
TechSolutions: Django, React... [Vector 1536D] "Educación: Grado Informática..."
StartupXYZ: Flask, FastAPI... [Vector 1536D] "Habilidades: Python, JS..."
Educación: Grado Informática...
Habilidades: Python, JS..."
```

#### 4.5.2 Proceso de Búsqueda

```
REQUISITO: "Experiencia con React"

1. Convertir requisito a vector [1536D]
2. Buscar vectores similares en FAISS
3. Devolver chunks ordenados por similitud

RESULTADO:
- "TechSolutions: Django y React..." (similitud: 0.92)
- "Habilidades: React, Vue.js..." (similitud: 0.87)
```

### 4.6 Factory de LLMs (`factory.py`)

Este componente permite usar diferentes proveedores de IA de forma transparente.

#### 4.6.1 Proveedores Soportados

| Proveedor | Modelos | Características |
|-----------|---------|-----------------|
| **OpenAI** | GPT-4, GPT-4o | Mejor calidad general |
| **Google** | Gemini Pro | Buena relación calidad/precio |
| **Anthropic** | Claude 3.5 | Excelente para análisis |

#### 4.6.2 Uso Transparente

```python
# El código no cambia al cambiar de proveedor
llm = LLMFactory.create_llm(
 provider="openai", # o "google", "anthropic"
 model_name="gpt-4",
 temperature=0.1
)

# El resto del código es idéntico
result = llm.invoke(prompt)
```

### 4.7 Prompts del Sistema (`prompts.py`)

Los prompts son las instrucciones que recibe la IA. Su diseño es crucial para la calidad del sistema.

#### 4.7.1 Prompt de Extracción de Requisitos

```
Eres un experto en recursos humanos especializado en análisis de ofertas de trabajo.

Tu tarea es extraer los requisitos de la oferta de empleo proporcionada.

INSTRUCCIONES:
1. Busca secciones de requisitos. Los títulos pueden variar:
 - OBLIGATORIOS: "Requisitos", "Lo que necesitamos", "Must have"...
 - DESEABLES: "Nos encantaría", "Nice to have", "Plus"...
2. Extrae los requisitos listados
3. Clasifica cada uno como "obligatory" u "optional"
4. NO extraigas de la descripción del puesto ni responsabilidades
5. NO inventes requisitos
```

#### 4.7.2 Prompt de Matching con Confianza

```
Para cada requisito, proporciona:
1. fulfilled: true si hay evidencia suficiente, false si no
2. found_in_cv: true si encontraste información relacionada
3. evidence: Cita específica del CV
4. confidence:
 - "high": Evidencia explícita y directa
 - "medium": Evidencia inferida o parcial
 - "low": Sin evidencia clara
5. reasoning: Explicación breve de tu decisión

IMPORTANTE:
- Sé objetivo y preciso
- No asumas información que no está en el CV
- La confianza debe reflejar la claridad de la evidencia
```

---

## 5. Flujo de Evaluación Detallado

### 5.1 Paso a Paso: Evaluación Completa

#### Paso 1: Usuario Proporciona Datos

```
┌─────────────────────────────────────────────────────────────────┐
│ INTERFAZ STREAMLIT │
│ │
│ ┌──────────────────────────────────────────────────────────┐ │
│ │ OFERTA DE EMPLEO │ │
│ │ ────────────────── │ │
│ │ Senior Developer - Fintech │ │
│ │ │ │
│ │ Lo que necesitamos: │ │
│ │ - 5 años de experiencia en Python │ │
│ │ - Inglés C1 │ │
│ │ │ │
│ │ Nos encantaría: │ │
│ │ - Certificación AWS │ │
│ └──────────────────────────────────────────────────────────┘ │
│ │
│ ┌──────────────────────────────────────────────────────────┐ │
│ │ CV DEL CANDIDATO │ │
│ │ ───────────────── │ │
│ │ Juan García - Python Developer │ │
│ │ 6 años de experiencia │ │
│ │ Inglés: B2 │ │
│ └──────────────────────────────────────────────────────────┘ │
│ │
│ [ ️ Opciones Avanzadas ] │
│ [x] Usar Embeddings Semánticos │
│ [ ] Usar LangGraph │
│ │
│ [ Iniciar Evaluación (Fase 1) ] │
│ │
└─────────────────────────────────────────────────────────────────┘
```

#### Paso 2: Sistema Extrae Requisitos

```
OFERTA ──► LLM con Structured Output ──► REQUISITOS

RESULTADO:
[
 {description: "5 años de experiencia en Python", type: "obligatory"},
 {description: "Inglés C1", type: "obligatory"},
 {description: "Certificación AWS", type: "optional"}
]

MENSAJES EN UI:
 Extraídos 3 requisitos (2 obligatorios, 1 opcional)
```

#### Paso 3: Sistema Indexa CV con Embeddings

```
CV ──► Dividir en chunks ──► Vectorizar ──► Indexar en FAISS

CHUNKS:
["Juan García - Python Developer", "6 años de experiencia", "Inglés: B2"]

MENSAJES EN UI:
 CV indexado (3 fragmentos)
```

#### Paso 4: Sistema Busca Evidencia Semántica

```
Para cada requisito:
 REQUISITO ──► Buscar en FAISS ──► Top 2 fragmentos relevantes

RESULTADO:
{
 "5 años de Python": "6 años de experiencia" (score: 0.89),
 "Inglés C1": "Inglés: B2" (score: 0.92),
 "Certificación AWS": null (score: 0.15)
}

MENSAJES EN UI:
 Encontrada evidencia para 2/3 requisitos
```

#### Paso 5: Sistema Hace Matching con LLM

```
CV + Requisitos + Evidencia ──► LLM ──► Matches con confianza

RESULTADO:
[
 {
 requirement: "5 años de Python",
 fulfilled: true,
 confidence: "high",
 evidence: "6 años de experiencia",
 reasoning: "Supera los 5 años requeridos"
 },
 {
 requirement: "Inglés C1",
 fulfilled: false,
 confidence: "high",
 evidence: "Inglés: B2",
 reasoning: "B2 no alcanza el C1 requerido"
 },
 {
 requirement: "Certificación AWS",
 fulfilled: false,
 confidence: "high",
 reasoning: "No se menciona ninguna certificación"
 }
]

MENSAJES EN UI:
 Matching completado: 1/3 cumplidos
```

#### Paso 6: Sistema Calcula Puntuación

```
LÓGICA:
- Total requisitos: 3
- Cumplidos: 1
- ¿Hay obligatorio no cumplido? SÍ (Inglés C1)
- RESULTADO: 0% (Descartado)

MENSAJES EN UI:
 Resultado: DESCARTADO
```

#### Paso 7: Sistema Muestra Resultados

```
┌─────────────────────────────────────────────────────────────────┐
│ Resultados de la Fase 1 │
├─────────────────────────────────────────────────────────────────┤
│ │
│ Puntuación: 0.0% Estado: Descartado │
│ Requisitos: 1/3 cumplidos │
│ │
│ REQUISITOS CUMPLIDOS (1) │
│ ┌────────────────────────────────────────────────────────────┐ │
│ │ 5 años de experiencia en Python Alta │ │
│ │ Evidencia: "6 años de experiencia" │ │
│ │ Razonamiento: Supera los 5 años requeridos │ │
│ └────────────────────────────────────────────────────────────┘ │
│ │
│ REQUISITOS NO CUMPLIDOS (2) │
│ ┌────────────────────────────────────────────────────────────┐ │
│ │ [ OBLIGATORIO] Inglés C1 Alta │ │
│ │ Razonamiento: B2 no alcanza el C1 requerido │ │
│ ├────────────────────────────────────────────────────────────┤ │
│ │ [ OPCIONAL] Certificación AWS Alta │ │
│ │ Razonamiento: No se menciona certificación │ │
│ └────────────────────────────────────────────────────────────┘ │
│ │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 Reglas de Puntuación

| Situación | Puntuación | Decisión |
|-----------|------------|----------|
| Todos los requisitos cumplidos | 100% | Aprobado |
| Falta algún requisito opcional | (cumplidos/total) × 100% | Continúa a Fase 2 |
| Falta algún requisito obligatorio | 0% | **Descartado** |

---

## 6. Tecnologías y Frameworks

### 6.1 Stack Tecnológico

```
┌─────────────────────────────────────────────────────────────────┐
│ STACK TECNOLÓGICO │
├─────────────────────────────────────────────────────────────────┤
│ │
│ FRONTEND (Interfaz) │
│ ───────────────────── │
│ └── Streamlit Aplicación web interactiva │
│ │
│ BACKEND (Lógica) │
│ ───────────────── │
│ ├── Python 3.10+ Lenguaje base │
│ ├── Pydantic Validación de datos │
│ └── asyncio Operaciones asíncronas │
│ │
│ IA / LLM │
│ ──────── │
│ ├── LangChain Framework principal │
│ ├── LangChain-OpenAI Integración OpenAI │
│ ├── LangChain-Google Integración Gemini │
│ ├── LangChain-Anthropic Integración Claude │
│ ├── LangGraph Orquestación multi-agente │
│ └── LangSmith Trazabilidad y feedback │
│ │
│ EMBEDDINGS │
│ ────────── │
│ ├── OpenAI Embeddings text-embedding-3-small │
│ └── FAISS Vector store para búsqueda │
│ │
│ EXTRACCIÓN │
│ ────────── │
│ ├── pypdf Lectura de PDFs │
│ └── BeautifulSoup4 Scraping de URLs │
│ │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 LangChain: El Framework Central

#### ¿Qué es LangChain?

**Para usuarios no técnicos:** LangChain es como un "traductor inteligente" entre tu aplicación y los modelos de IA (como ChatGPT). Te ayuda a:
- Hacer preguntas estructuradas a la IA
- Recibir respuestas en formato predecible
- Conectar diferentes modelos de IA sin cambiar tu código

**Para usuarios técnicos:** LangChain es un framework de orquestación para LLMs que proporciona:
- Abstracciones para prompts, chains, y agentes
- Integración con múltiples proveedores (OpenAI, Google, Anthropic)
- Structured Output para respuestas tipadas
- Callbacks para observabilidad

#### Características que usamos:

| Característica | Uso en el Sistema |
|----------------|-------------------|
| **Structured Output** | Garantizar que el LLM devuelva JSON válido |
| **ChatPromptTemplate** | Templates para prompts |
| **BaseChatModel** | Abstracción de proveedores |
| **Callbacks** | Trazabilidad con LangSmith |

### 6.3 FAISS: Búsqueda de Vectores

#### ¿Qué es FAISS?

**Para usuarios no técnicos:** FAISS es como un buscador súper inteligente. En vez de buscar palabras exactas, busca por significado. Si buscas "experiencia con microservicios", encuentra "migración de monolito a microservicios" aunque no use las mismas palabras.

**Para usuarios técnicos:** FAISS (Facebook AI Similarity Search) es una librería para búsqueda eficiente de similitud entre vectores de alta dimensionalidad. Características:
- Indexación optimizada para vectores densos
- Búsqueda de vecinos cercanos (ANN)
- Soporte para GPU (no usado aquí por simplicidad)

### 6.4 Pydantic: Validación de Datos

#### ¿Por qué Pydantic?

```python
# SIN Pydantic: Error difícil de detectar
def process_requirement(req):
 # ¿Es un dict? ¿Tiene 'description'? ¿Es string?
 return req['description'].upper() # Puede fallar en runtime

# CON Pydantic: Error detectable en compilación
class Requirement(BaseModel):
 description: str
 type: RequirementType

def process_requirement(req: Requirement):
 return req.description.upper() # Siempre funciona
```

---

## 7. Mejoras Implementadas

### 7.1 Propuesta 1: Streaming de Respuestas

#### Problema Original
El usuario veía un spinner genérico durante 30-60 segundos sin saber qué estaba pasando.

#### Solución Implementada
Mostrar progreso paso a paso usando `st.status()`:

```
 Ejecutando Fase 1: Análisis de CV y oferta...
 ├── Extrayendo requisitos de la oferta...
 ├── Embeddings semánticos habilitados...
 ├── Extraídos 13 requisitos
 ├── Score: 53.8%
 └── Fase 1 completada!
```

#### Archivos Modificados
- `app/streamlit_app.py` - Integración de `st.status()`
- `src/evaluator/core/analyzer.py` - Método `analyze_streaming()`

### 7.2 Propuesta 2: Embeddings Semánticos

#### Problema Original
El LLM recibía el CV completo y tenía que buscar evidencia él mismo, lo que aumentaba la probabilidad de errores.

#### Solución Implementada
Usar FAISS para pre-filtrar evidencia relevante antes de enviar al LLM:

```
ANTES: DESPUÉS:
───────── ────────

CV completo (2000 palabras) CV + Pistas semánticas
 │ │
 ▼ ▼
 LLM LLM
 │ │
 ▼ ▼
"Creo que cumple..." "Cumple porque dice X (score 0.9)"
(menos preciso) (más preciso)
```

#### Archivos Modificados
- `src/evaluator/core/embeddings.py` - Nuevo módulo `SemanticMatcher`
- `src/evaluator/core/analyzer.py` - Integración con embeddings

### 7.3 Propuesta 4: LangGraph Multi-Agente

#### Problema Original
La lógica de evaluación estaba en un solo método largo, difícil de mantener y sin visibilidad de pasos intermedios.

#### Solución Implementada
Dividir en nodos especializados con LangGraph:

```
ANTES: Un método de 200 líneas
───────────────────────────────

def analyze(offer, cv):
 # Extraer requisitos
 # Indexar CV
 # Hacer matching
 # Calcular score
 return result

DESPUÉS: 4 nodos especializados
───────────────────────────────

┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│ Extractor│──►│ Embedder │──►│ Matcher │──►│ Scorer │
└──────────┘ └──────────┘ └──────────┘ └──────────┘
```

#### Archivos Modificados
- `src/evaluator/core/graph.py` - Nuevo módulo con definición del grafo

### 7.4 Propuesta 5: LangSmith para Trazabilidad

#### Problema Original
No había forma de ver qué pasaba internamente ni de medir la calidad del sistema.

#### Solución Implementada
Integración con LangSmith para:
- Trazar cada llamada al LLM
- Registrar tiempos de respuesta
- Permitir feedback del usuario

#### Archivos Modificados
- `src/evaluator/llm/factory.py` - Configuración de LangSmith
- `src/evaluator/core/evaluator.py` - Método `record_feedback()`

### 7.5 Propuesta 6: Niveles de Confianza

#### Problema Original
El sistema solo decía "cumplido" o "no cumplido", sin indicar qué tan seguro estaba.

#### Solución Implementada
Añadir niveles de confianza con visualización:

```
ANTES: DESPUÉS:
───────── ────────

 5 años de Python 5 años de Python Alta
 Evidencia: ... Evidencia: ...
 Razonamiento: ...
```

#### Archivos Modificados
- `src/evaluator/models.py` - Nuevo enum `ConfidenceLevel`
- `src/evaluator/llm/prompts.py` - Prompt actualizado
- `app/streamlit_app.py` - Badges de confianza

---

## 8. Experiencia de Usuario

### 8.1 Interfaz Principal

La interfaz está diseñada para ser intuitiva:

```
┌─────────────────────────────────────────────────────────────────┐
│ EVALUADOR DE CANDIDATOS CON IA │
├─────────────────────────────────────────────────────────────────┤
│ │
│ SIDEBAR (Izquierda) ÁREA PRINCIPAL (Derecha) │
│ ────────────────── ────────────────────────── │
│ │
│ ┌───────────────┐ ┌──────────────────────────┐ │
│ │ Configuración │ │ │ │
│ │ │ │ 1. CV del Candidato │ │
│ │ Proveedor: │ │ [Pegar texto] │ │
│ │ [OpenAI ▼] │ │ [Subir PDF] │ │
│ │ │ │ │ │
│ │ Modelo: │ │ 2. Oferta de Empleo │ │
│ │ [gpt-4 ▼] │ │ [Pegar texto] │ │
│ │ │ │ [URL] │ │
│ │ API Key: │ │ │ │
│ │ [••••••••••] │ │ ️ Opciones Avanzadas │ │
│ │ │ │ [x] Embeddings │ │
│ │ │ │ [ ] LangGraph │ │
│ │ │ │ │ │
│ │ │ │ [ Iniciar Evaluación] │ │
│ └───────────────┘ └──────────────────────────┘ │
│ │
└─────────────────────────────────────────────────────────────────┘
```

### 8.2 Resultados Visuales

Los resultados se presentan con códigos de color claros:

| Elemento | Significado |
|----------|-------------|
| Verde | Confianza alta / Requisito cumplido |
| Amarillo | Confianza media / Requisito opcional |
| Rojo | Confianza baja / Requisito obligatorio no cumplido |
| | Requisito cumplido |
| | Requisito no cumplido |

### 8.3 Flujo de Usuario Típico

1. **Configurar proveedor** (sidebar) - Seleccionar OpenAI/Google/Anthropic
2. **Ingresar CV** - Pegar texto o subir PDF
3. **Ingresar oferta** - Pegar texto o URL
4. **Activar opciones** - Embeddings, LangGraph (opcional)
5. **Ejecutar evaluación** - Clic en botón
6. **Ver resultados** - Puntuación, requisitos, evidencia
7. **Fase 2 (si aplica)** - Responder preguntas de entrevista

---

## 9. Ejemplos de Uso

### 9.1 Ejemplo: Candidato Ideal

**Oferta:**
```
Requisitos obligatorios:
- 3 años de experiencia en Python
- Conocimientos de SQL

Requisitos deseables:
- Experiencia con Docker
```

**CV:**
```
Senior Python Developer con 5 años de experiencia.
Experto en PostgreSQL, MySQL y SQLite.
Trabajo diario con contenedores Docker.
```

**Resultado Esperado:**
```
Puntuación: 100%
Estado: Aprobado

 3 años de Python (5 años > 3 años) Alta
 Conocimientos SQL (PostgreSQL, MySQL) Alta
 Experiencia Docker (trabajo diario) Alta
```

### 9.2 Ejemplo: Candidato Parcial

**Oferta:**
```
Requisitos obligatorios:
- 5 años de experiencia en Java
- Inglés C1

Requisitos deseables:
- Certificación AWS
```

**CV:**
```
Java Developer con 7 años de experiencia.
Inglés: B2
Sin certificaciones.
```

**Resultado Esperado:**
```
Puntuación: 0% (Descartado)

 5 años de Java (7 años > 5 años) Alta
 Inglés C1 (B2 < C1) Alta
 Certificación AWS (no mencionada) Alta
```

### 9.3 Ejemplo: Candidato para Fase 2

**Oferta:**
```
Requisitos obligatorios:
- 2 años de experiencia
- Conocimientos de Git

Requisitos deseables:
- Experiencia con CI/CD
```

**CV:**
```
Desarrollador con 3 años de experiencia.
Uso diario de Git y GitHub.
```

**Resultado Esperado:**
```
Puntuación: 66.6%
Estado: Continúa a Fase 2

 2 años de experiencia (3 años > 2 años) Alta
 Conocimientos de Git (uso diario) Alta
 Experiencia CI/CD (no encontrado) Baja

[ Iniciar Fase 2: Entrevista sobre CI/CD]
```

---

## 10. Limitaciones Conocidas

### 10.1 Limitación: Fase 2 No Se Activa Correctamente

**Situación:** Cuando un requisito obligatorio está "encontrado pero no cumplido" (ej: Inglés B2 cuando se pide C1), el sistema descarta al candidato sin darle oportunidad de explicar en Fase 2.

**Causa Técnica:** La lógica actual añade a `missing_requirements` solo los requisitos donde `found_in_cv=False`. Si el requisito fue encontrado pero no cumplido, no se genera pregunta.

**Impacto:** Candidatos que podrían demostrar cumplimiento en entrevista son descartados prematuramente.

**Solución Propuesta (no implementada):** Modificar la lógica para generar preguntas también cuando `fulfilled=False AND confidence="medium"`.

### 10.2 Limitación: Dependencia de Calidad del CV

**Situación:** Si el CV está mal estructurado o usa términos muy diferentes a los de la oferta, el matching puede fallar.

**Ejemplo:**
- Oferta: "Experiencia con microservicios"
- CV: "Trabajo con arquitectura distribuida basada en servicios"
- Resultado: Posible no-match aunque sea equivalente

**Mitigación:** Los embeddings semánticos ayudan, pero no son perfectos.

### 10.3 Limitación: Costos de API

**Situación:** Cada evaluación consume tokens de la API del proveedor.

**Costo Aproximado por Evaluación (GPT-4):**
- Extracción: ~500 tokens
- Matching: ~1000 tokens
- Total: ~$0.05 por evaluación

**Mitigación:** Usar modelos más económicos (GPT-4o) o embeddings locales.

---

## 11. Ideas Futuras

### 11.1 Fase 2 Mejorada

**Estado:** No implementado
**Prioridad:** Alta

Modificar la lógica de Fase 2 para:
- Generar preguntas cuando hay evidencia parcial
- Permitir al candidato aclarar requisitos "casi cumplidos"
- Reevaluar con las respuestas

### 11.2 Embeddings Locales

**Estado:** No implementado
**Prioridad:** Media

Usar modelos de embeddings locales (HuggingFace) para:
- Reducir costos de API
- Mejorar privacidad (datos no salen del servidor)
- Funcionar offline

### 11.3 Fine-tuning para Industrias

**Estado:** No implementado
**Prioridad:** Baja

Entrenar modelos específicos para:
- Tecnología (términos técnicos)
- Finanzas (regulaciones, certificaciones)
- Salud (terminología médica)

### 11.4 Integración con ATS

**Estado:** No implementado
**Prioridad:** Media

Conectar con sistemas de seguimiento de candidatos:
- Greenhouse
- Lever
- Workday

### 11.5 Análisis de Sesgos

**Estado:** No implementado
**Prioridad:** Alta

Implementar detección y mitigación de sesgos:
- Verificar que el sistema no discrimine por género, edad, etc.
- Auditar decisiones del modelo
- Alertar sobre posibles sesgos

### 11.6 Interfaz para Candidatos

**Estado:** No implementado
**Prioridad:** Media

Crear una interfaz donde el candidato pueda:
- Ver por qué fue rechazado
- Responder preguntas de Fase 2
- Actualizar su CV basado en feedback

### 11.7 Dashboard de Métricas

**Estado:** No implementado
**Prioridad:** Media

Panel para ver:
- Número de evaluaciones por día
- Tasa de aceptación/rechazo
- Requisitos más difíciles de cumplir
- Tiempo promedio de evaluación

---

## 12. Glosario Técnico

### Términos de IA

| Término | Definición Simple | Definición Técnica |
|---------|-------------------|-------------------|
| **LLM** | Inteligencia artificial que entiende y genera texto | Large Language Model - modelo de lenguaje entrenado en grandes cantidades de texto |
| **Embedding** | Representación numérica de texto | Vector de alta dimensionalidad que captura significado semántico |
| **Token** | Unidad de texto que procesa la IA | Fragmento de texto (palabra o parte de palabra) usado para procesar y cobrar |
| **Prompt** | Instrucciones para la IA | Texto de entrada que guía la generación del modelo |
| **Temperatura** | Qué tan creativa es la respuesta | Parámetro que controla la aleatoriedad (0=determinista, 1=creativo) |

### Términos del Sistema

| Término | Definición Simple | Definición Técnica |
|---------|-------------------|-------------------|
| **Structured Output** | Respuestas en formato predecible | Capacidad del LLM de generar JSON que cumple un schema Pydantic |
| **Matching** | Comparar CV con requisitos | Proceso de determinar si el CV evidencia cumplimiento de requisitos |
| **Confianza** | Qué tan seguro está el sistema | Nivel de certeza basado en la claridad de la evidencia |
| **Razonamiento** | Explicación de la decisión | Justificación textual del porqué de cada evaluación |
| **Score Semántico** | Similitud de significado | Valor 0-1 que indica qué tan relacionados están dos textos |

### Términos de LangChain

| Término | Definición Simple | Definición Técnica |
|---------|-------------------|-------------------|
| **Chain** | Secuencia de pasos | Composición de componentes LangChain (prompt LLM parser) |
| **Agent** | IA que toma decisiones | LLM con acceso a herramientas que decide qué acciones tomar |
| **Callback** | Notificación de eventos | Función que se ejecuta cuando ocurre algo (inicio, fin, error) |
| **VectorStore** | Base de datos de significados | Almacén optimizado para búsqueda de vectores similares |

---

## Conclusión

Este sistema representa una implementación práctica y robusta de evaluación de candidatos con IA. Combina:

- **Fiabilidad:** Structured Output garantiza respuestas válidas
- **Transparencia:** Cada decisión tiene evidencia y razonamiento
- **Flexibilidad:** Múltiples proveedores de IA soportados
- **Escalabilidad:** Arquitectura modular permite extensiones

El sistema está listo para producción y las mejoras futuras identificadas permitirán aumentar su valor sin comprometer la estabilidad actual.

---

*Documento generado el 27 de diciembre de 2025*
*Versión del sistema: 2.0.0*

