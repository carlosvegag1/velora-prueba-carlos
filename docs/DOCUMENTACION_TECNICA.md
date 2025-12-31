# Documentación Técnica - Valor Diferencial

> **Prueba técnica para Ingeniero de IA Generativa**  
> Este documento detalla las decisiones técnicas y funcionalidades adicionales implementadas más allá de los requisitos base.

---

## Índice

1. [Enfoque de la Prueba](#1-enfoque-de-la-prueba)
2. [Cumplimiento de Requisitos Base](#2-cumplimiento-de-requisitos-base)
3. [Valor Diferencial: Arquitectura](#3-valor-diferencial-arquitectura)
4. [Valor Diferencial: Tecnologías Avanzadas](#4-valor-diferencial-tecnologías-avanzadas)
5. [Valor Diferencial: Funcionalidades Adicionales](#5-valor-diferencial-funcionalidades-adicionales)
6. [Decisiones Técnicas Justificadas](#6-decisiones-técnicas-justificadas)
7. [Ejemplo de Impacto: Resolución de Latencia](#7-ejemplo-de-impacto-resolución-de-latencia)

---

## 1. Enfoque de la Prueba

Mi estrategia fue clara: **cumplir los requisitos especificados y, simultáneamente, demostrar cómo diseñaría un sistema de producción real**.

La prueba define un sistema de dos fases con reglas de puntuación específicas. Implementé exactamente eso, pero quise ir más allá porque:

1. **Demostrar criterio arquitectónico**: No solo código funcional, sino mantenible y escalable
2. **Mostrar conocimiento del ecosistema LangChain**: LangGraph, LangSmith, Structured Output
3. **Anticipar necesidades reales**: Observabilidad, flexibilidad, trazabilidad

---

## 2. Cumplimiento de Requisitos Base

### Fase 1: Análisis Automático

La prueba especifica:
- Recibir requisitos de oferta (obligatorios/opcionales) y CV en texto
- Identificar requisitos cumplidos/no cumplidos
- Puntuación: `(cumplidos / total) * 100`
- Si falta obligatorio → `score = 0`, `discarded = true`

**Mi implementación**:

```python
# backend/nucleo/analisis/analizador.py
class AnalizadorFase1:
    def analyze(self, job_offer: str, cv: str) -> ResultadoFase1:
        # 1. Extraer requisitos con Structured Output
        requisitos = self._extraer_requisitos(job_offer)
        
        # 2. Matching CV-Requisitos
        coincidencias = self._matching_cv(requisitos, cv)
        
        # 3. Calcular puntuación según reglas
        score, discarded = self._calcular_puntuacion(coincidencias)
        
        return ResultadoFase1(
            puntuacion=score,
            descartado=discarded,
            requisitos_cumplidos=cumplidos,
            requisitos_no_cumplidos=no_cumplidos,
            requisitos_faltantes=faltantes  # Para Fase 2
        )
```

El output sigue exactamente el formato especificado:
```json
{
  "score": 50,
  "discarded": false,
  "matching_requirements": ["3 años de experiencia en Python", ...],
  "unmatching_requirements": [],
  "not_found_requirements": ["Conocimientos en FastAPI", "Conocimientos en LangChain"]
}
```

### Fase 2: Entrevista Conversacional

La prueba especifica:
- Si no descartado, preguntar por requisitos no encontrados
- Recalcular puntuación con respuestas

**Mi implementación**:

```python
# backend/nucleo/entrevista/entrevistador.py
class EntrevistadorFase2:
    def inicializar_entrevista(self, resultado_fase1, contexto_cv):
        # Configura preguntas para cada requisito faltante
        self._requisitos_pendientes = [
            {"description": req, "asked": False, "answered": False}
            for req in resultado_fase1.requisitos_faltantes
        ]
    
    def transmitir_pregunta(self, indice) -> Generator[str, None, None]:
        # Genera pregunta con streaming
        for token in chain.stream({...}):
            yield token
    
    def obtener_respuestas_entrevista(self) -> List[RespuestaEntrevista]:
        # Respuestas formateadas para reevaluación
```

### Intercambiabilidad de Proveedores

La prueba requiere LangChain con proveedores intercambiables.

**Mi implementación**:

```python
# backend/infraestructura/llm/llm_proveedor.py
class FabricaLLM:
    @staticmethod
    def crear_llm(proveedor: str, nombre_modelo: str, ...) -> BaseChatModel:
        if proveedor == "openai":
            return ChatOpenAI(model=nombre_modelo, ...)
        elif proveedor == "google":
            return ChatGoogleGenerativeAI(model=nombre_modelo, ...)
        elif proveedor == "anthropic":
            return ChatAnthropic(model=nombre_modelo, ...)
```

Cambio de proveedor = **1 línea de configuración**, no refactorización.

---

## 3. Valor Diferencial: Arquitectura

### 3.1 Backend Modular por Capas

En lugar de un script monolítico, diseñé una arquitectura por capas:

```
backend/
├── modelos.py                 # Contratos de datos (Pydantic)
├── nucleo/                    # LÓGICA DE NEGOCIO
│   ├── analisis/             # Fase 1
│   ├── entrevista/           # Fase 2
│   └── historial/            # RAG (adicional)
├── orquestacion/              # COORDINACIÓN
│   ├── orquestador.py        # CandidateEvaluator
│   └── coordinador_grafo.py  # LangGraph (adicional)
├── infraestructura/           # INTEGRACIONES
│   ├── llm/                  # Factories + config
│   ├── extraccion/           # PDF, URLs
│   └── persistencia/         # UserMemory
└── recursos/                  # PROMPTS CENTRALIZADOS
```

**Beneficio**: Cada componente tiene responsabilidad única. Puedo modificar la extracción de PDFs sin tocar el analizador.

### 3.2 Configuración Centralizada

Todos los hiperparámetros en un archivo:

```python
# backend/infraestructura/llm/hiperparametros.py
FASE1_EXTRACCION = HiperparametrosLLM(temperature=0.0)  # Máximo determinismo
FASE1_MATCHING = HiperparametrosLLM(temperature=0.1)
FASE2_ENTREVISTA = HiperparametrosLLM(temperature=0.3)  # Naturalidad
```

**Beneficio**: Ajustar comportamiento sin buscar en todo el código.

### 3.3 Nomenclatura Bilingüe

El código usa español con aliases en inglés:

```python
class AnalizadorFase1:
    def analyze(self, ...):  # Alias inglés
        return self.analizar(...)
    
    def analizar(self, oferta_trabajo: str, cv: str):  # Implementación
        ...

Phase1Analyzer = AnalizadorFase1  # Alias de clase
```

**Beneficio**: Código legible en español, pero compatible con convenciones internacionales.

---

## 4. Valor Diferencial: Tecnologías Avanzadas

### 4.1 LangGraph (Orquestación Multi-Agente)

La prueba no requiere LangGraph, pero lo implementé porque:

- **Flujo como grafo**: Nodos especializados que pueden activarse/desactivarse
- **Estado tipado**: Cada nodo tiene inputs/outputs definidos
- **Extensibilidad**: Agregar nodos sin reescribir el flujo

```python
# backend/orquestacion/coordinador_grafo.py
grafo.add_node("extraer_requisitos", self._extraer_requisitos)
grafo.add_node("embeber_cv", self._embeber_cv)  # Opcional
grafo.add_node("matching_semantico", self._matching_semantico)
grafo.add_node("calcular_puntuacion", self._calcular_puntuacion)

grafo.set_entry_point("extraer_requisitos")
grafo.add_edge("extraer_requisitos", "embeber_cv")
grafo.add_edge("embeber_cv", "matching_semantico")
grafo.add_edge("matching_semantico", "calcular_puntuacion")
```

**Toggle en UI**: El usuario puede activar/desactivar LangGraph según necesidad.

### 4.2 Structured Output (Sin Parsing Manual)

En lugar de:
```python
response = llm.invoke(prompt)
data = json.loads(response)  # Puede fallar
```

Uso:
```python
llm_estructurado = llm.with_structured_output(RespuestaExtraccionRequisitos)
resultado: RespuestaExtraccionRequisitos = chain.invoke({...})
# Siempre un objeto Pydantic válido
```

**Beneficio**: Eliminación de errores de parsing, tipado fuerte, validación automática.

### 4.3 LangSmith (Observabilidad)

Integré trazabilidad completa:

```python
# backend/infraestructura/llm/llm_proveedor.py
def configurar_langsmith(nombre_proyecto: str = "velora-evaluator"):
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_PROJECT"] = nombre_proyecto
```

**Beneficio**: En producción, puedo ver cada prompt enviado, tokens generados, latencia, costos.

---

## 5. Valor Diferencial: Funcionalidades Adicionales

### 5.1 Embeddings Semánticos con FAISS

La prueba pide matching CV-requisitos. Yo añadí búsqueda semántica opcional:

```python
# Indexa CV en chunks vectorizados
fragmentos = self.comparador_semantico.indexar_cv(cv)

# Busca evidencia semántica por requisito
for req in requisitos:
    evidencia = self.comparador_semantico.buscar_evidencia(req.description)
    # Añade "pistas" al prompt de matching
```

**Beneficio**: El LLM recibe contexto relevante pre-filtrado, mejora precisión.

### 5.2 RAG para Historial de Evaluaciones

Añadí un chatbot que consulta evaluaciones previas:

- "¿Por qué me rechazaron la última vez?"
- "¿Cuáles son mis puntos fuertes?"
- "Compara mis últimas evaluaciones"

```python
# backend/nucleo/historial/asistente.py
class AsistenteHistorial:
    def query(self, pregunta: str) -> str:
        docs = self.vectorstore.search(pregunta, k=5)
        contexto = self._formatear_contexto(docs)
        return self.llm.invoke(contexto + pregunta)
```

### 5.3 Streaming Real en Entrevista

La Fase 2 genera preguntas con streaming token-by-token:

```python
def transmitir_pregunta(self, indice) -> Generator[str, None, None]:
    chain = prompt | self.llm | StrOutputParser()
    for chunk in chain.stream({}):
        yield chunk  # Token por token
```

**Beneficio**: Experiencia tipo ChatGPT, feedback inmediato al usuario.

### 5.4 Niveles de Confianza en Matching

Cada requisito evaluado incluye confianza:

```python
class ResultadoMatching(BaseModel):
    requirement_description: str
    fulfilled: bool
    confidence: Literal["high", "medium", "low"]
    reasoning: str  # Explicación del LLM
    evidence: Optional[str]  # Cita del CV
```

**Beneficio**: Trazabilidad de decisiones, auditoría posible.

### 5.5 Scraping Avanzado con Playwright

Para URLs de portales que bloquean scraping básico:

```python
# backend/infraestructura/extraccion/web.py
# Fallback: requests → Playwright con Chromium headless
async with async_playwright() as p:
    browser = await p.chromium.launch(headless=True)
    page = await browser.new_page()
    await page.goto(url)
    content = await page.content()
```

**Beneficio**: Funciona con LinkedIn, Indeed, portales corporativos.

---

## 6. Decisiones Técnicas Justificadas

### ¿Por qué LangGraph si no lo pedían?

Un chain lineal es rígido. Si quiero agregar/quitar el paso de embeddings, debo reescribir. Con LangGraph, es un toggle.

### ¿Por qué embeddings opcionales?

Trade-off consciente: mejoran precisión pero añaden latencia. El usuario decide.

### ¿Por qué temperaturas diferenciadas?

- Fase 1 (extracción): `temperature=0.0` → Máximo determinismo
- Fase 2 (entrevista): `temperature=0.3` → Naturalidad en preguntas

### ¿Por qué Streamlit y no terminal?

La prueba dice "valorable interfaz UI". Streamlit permite UI rápida en Python puro, sin frontend separado.

### ¿Por qué persistencia en JSON y no base de datos?

Simplicidad para la prueba. Pero la abstracción `UserMemory` permite migrar sin tocar código de negocio.

---

## 7. Ejemplo de Impacto: Resolución de Latencia

**Problema**: Al activar embeddings, latencia subía 3-4 segundos.

**Diagnóstico**: Gracias a arquitectura modular, localicé en 5 minutos:
```
backend/infraestructura/llm/embedding_proveedor.py
```

**Solución**: Cambiar modelo de embeddings (1 línea):
```python
# Antes: "text-embedding-ada-002"
# Después: "text-embedding-3-small"
```

**Resultado**: -40% latencia, sin efectos colaterales.

**Moraleja**: Buena arquitectura convierte problemas complejos en cambios localizados.

---

## Resumen de Valor Aportado

| Categoría | Valor Diferencial |
|-----------|-------------------|
| **Arquitectura** | Capas modulares, configuración centralizada, nomenclatura bilingüe |
| **LangChain Avanzado** | LangGraph, LangSmith, Structured Output |
| **Funcionalidades** | Embeddings semánticos, RAG historial, streaming, confianza en matches |
| **Producción** | Docker, logs operacionales, scraping avanzado |
| **Código** | Tipado fuerte, prompts centralizados, hiperparámetros por contexto |

---

*Documentación técnica para prueba de Velora*  
*Carlos Vega | Diciembre 2024*
