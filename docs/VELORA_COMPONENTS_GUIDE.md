# VELORA - Guía de Componentes y Desarrollo
## Referencia Técnica para AI Engineers

---

# 1. INVENTARIO COMPLETO DE COMPONENTES

## 1.1 Árbol de Directorios Anotado

```
velora_auto/
│
├── 📁 app/                              # CAPA DE PRESENTACIÓN
│   ├── __init__.py
│   ├── streamlit_app.py                 # UI principal (2355 líneas)
│   │   ├── render_velora_header()       # Header corporativo
│   │   ├── render_sidebar_logo()        # Logo sidebar
│   │   ├── render_agentic_interview()   # Chat Fase 2 con streaming
│   │   ├── display_phase1_results()     # Resultados Fase 1
│   │   ├── display_final_results()      # Resultados finales
│   │   └── main()                       # Orquestador de tabs
│   │
│   └── 📁 assets/                       # Recursos estáticos
│       ├── Velora_logotipo_*.png        # Logos corporativos
│       └── README.md
│
├── 📁 src/evaluator/                    # NÚCLEO DEL SISTEMA
│   │
│   ├── __init__.py                      # Exports públicos del paquete
│   │   └── __version__ = "2.0.0"
│   │
│   ├── models.py                        # MODELOS DE DATOS (149 líneas)
│   │   ├── RequirementType (Enum)       # obligatory | optional
│   │   ├── ConfidenceLevel (Enum)       # high | medium | low
│   │   ├── Requirement                  # Modelo de requisito
│   │   ├── ExtractedRequirement         # Structured Output: extracción
│   │   ├── RequirementMatch             # Structured Output: matching
│   │   ├── ResponseEvaluation           # Structured Output: evaluación
│   │   ├── Phase1Result                 # Resultado Fase 1
│   │   └── EvaluationResult             # Resultado final completo
│   │
│   ├── 📁 core/                         # LÓGICA DE NEGOCIO
│   │   ├── __init__.py                  # Exports: Evaluator, Analyzer, Interviewer
│   │   │
│   │   ├── evaluator.py                 # ORQUESTADOR (402 líneas)
│   │   │   └── CandidateEvaluator
│   │   │       ├── __init__()           # Inicializa Analyzer + Interviewer
│   │   │       ├── evaluate_candidate() # Flujo completo
│   │   │       ├── reevaluate_with_interview()  # Re-cálculo post Fase 2
│   │   │       └── record_feedback()    # LangSmith feedback
│   │   │
│   │   ├── analyzer.py                  # FASE 1 (516 líneas)
│   │   │   └── Phase1Analyzer
│   │   │       ├── __init__()           # Config LLM, semantic matcher
│   │   │       ├── extract_requirements()       # Extracción de oferta
│   │   │       ├── match_cv_with_requirements() # Matching CV
│   │   │       ├── analyze()            # Flujo completo Fase 1
│   │   │       └── _analyze_traditional() / _analyze_with_langgraph()
│   │   │
│   │   ├── agentic_interviewer.py       # FASE 2 AGÉNTICA (503 líneas)
│   │   │   └── AgenticInterviewer
│   │   │       ├── initialize_interview()       # Setup estado
│   │   │       ├── stream_greeting()    # Saludo con streaming
│   │   │       ├── stream_question()    # Pregunta con streaming
│   │   │       ├── stream_closing()     # Cierre con streaming
│   │   │       ├── register_response()  # Registrar respuesta
│   │   │       ├── evaluate_response()  # Evaluar cumplimiento
│   │   │       └── validate_coverage()  # Auditoría de cobertura
│   │   │
│   │   ├── embeddings.py                # SEMANTIC MATCHER (234 líneas)
│   │   │   └── SemanticMatcher
│   │   │       ├── index_cv()           # Indexar CV en FAISS
│   │   │       ├── find_evidence()      # Buscar evidencia semántica
│   │   │       └── clear()              # Limpiar vectorstore
│   │   │
│   │   ├── graph.py                     # LANGGRAPH (505 líneas)
│   │   │   ├── Phase1State (TypedDict)  # Estado compartido
│   │   │   ├── create_extract_node()    # Agente extractor
│   │   │   ├── create_embed_node()      # Agente embedder
│   │   │   ├── create_match_node()      # Agente matcher
│   │   │   ├── create_score_node()      # Agente scorer
│   │   │   ├── create_phase1_graph()    # Construcción del grafo
│   │   │   └── run_phase1_graph_streaming()  # Ejecución con streaming
│   │   │
│   │   └── logging_config.py            # LOGGING OPERACIONAL (375 líneas)
│   │       └── OperationalLogger (Singleton)
│   │           ├── config_*()           # Logs de configuración
│   │           ├── phase1_*()           # Logs de Fase 1
│   │           ├── phase2_*()           # Logs de Fase 2
│   │           └── rag_*()              # Logs de RAG
│   │
│   ├── 📁 llm/                          # CAPA LLM
│   │   ├── __init__.py                  # Exports: LLMFactory, EmbeddingFactory
│   │   │
│   │   ├── factory.py                   # LLM FACTORY (249 líneas)
│   │   │   ├── configure_langsmith()    # Setup LangSmith
│   │   │   └── LLMFactory
│   │   │       ├── create_llm()         # Crear instancia LLM
│   │   │       ├── get_available_providers()
│   │   │       └── get_available_models()
│   │   │
│   │   ├── embeddings_factory.py        # EMBEDDINGS FACTORY (233 líneas)
│   │   │   └── EmbeddingFactory
│   │   │       ├── create_embeddings()  # Crear instancia embeddings
│   │   │       ├── supports_embeddings()
│   │   │       └── get_fallback_provider()
│   │   │
│   │   ├── hyperparameters.py           # CONFIGURACIÓN TEMP (223 líneas)
│   │   │   ├── LLMHyperparameters (dataclass)
│   │   │   ├── PHASE1_EXTRACTION        # temp=0.0
│   │   │   ├── PHASE1_MATCHING          # temp=0.1
│   │   │   ├── PHASE2_INTERVIEW         # temp=0.3
│   │   │   ├── RAG_CHATBOT              # temp=0.4
│   │   │   └── HyperparametersConfig    # Acceso centralizado
│   │   │
│   │   └── prompts.py                   # PROMPTS CENTRALIZADOS (164 líneas)
│   │       ├── EXTRACT_REQUIREMENTS_PROMPT
│   │       ├── MATCH_CV_REQUIREMENTS_PROMPT
│   │       ├── GENERATE_QUESTIONS_PROMPT
│   │       ├── EVALUATE_RESPONSE_PROMPT
│   │       ├── AGENTIC_SYSTEM_PROMPT
│   │       ├── AGENTIC_GREETING_PROMPT
│   │       ├── AGENTIC_QUESTION_PROMPT
│   │       └── AGENTIC_CLOSING_PROMPT
│   │
│   ├── 📁 rag/                          # RETRIEVAL AUGMENTED GENERATION
│   │   ├── __init__.py
│   │   │
│   │   ├── chatbot.py                   # RAG CHATBOT (309 líneas)
│   │   │   └── HistoryChatbot
│   │   │       ├── query()              # Consulta simple
│   │   │       ├── query_with_history() # Con contexto conversación
│   │   │       └── get_quick_summary()  # Stats sin LLM
│   │   │
│   │   └── vectorstore.py               # VECTORSTORE (330 líneas)
│   │       ├── normalize_text_for_embedding()
│   │       └── HistoryVectorStore
│   │           ├── index_evaluations()  # Indexar historial
│   │           ├── search()             # Búsqueda semántica
│   │           └── rebuild_index()      # Re-indexar
│   │
│   ├── 📁 storage/                      # PERSISTENCIA
│   │   ├── __init__.py
│   │   │
│   │   └── memory.py                    # USER MEMORY (513 líneas)
│   │       ├── EnrichedEvaluation (Pydantic)
│   │       ├── extract_job_title()      # Heurística de título
│   │       ├── create_enriched_evaluation()
│   │       └── UserMemory
│   │           ├── save_evaluation()
│   │           ├── get_evaluations()
│   │           └── get_searchable_texts()
│   │
│   ├── 📁 extraction/                   # UTILIDADES DE ENTRADA
│   │   ├── __init__.py
│   │   │
│   │   ├── pdf.py                       # PDF EXTRACTOR (50 líneas)
│   │   │   └── extract_text_from_pdf()
│   │   │
│   │   └── url.py                       # WEB SCRAPER (504 líneas)
│   │       ├── _scrape_with_requests()  # HTTP básico
│   │       ├── _scrape_with_browser()   # Playwright
│   │       └── scrape_job_offer_url()   # API pública
│   │
│   └── 📁 processing/                   # UTILIDADES DE PROCESO
│       ├── __init__.py
│       │
│       └── validation.py                # VALIDACIONES (55 líneas)
│           ├── calculate_score()        # Cálculo de puntuación
│           └── load_text_file()
│
├── 📁 data/                             # DATOS PERSISTENTES
│   ├── 📁 user_memory/                  # JSON por usuario
│   │   └── {user_id}.json
│   │
│   └── 📁 vectors/                      # Índices FAISS por usuario
│       └── {user_id}/
│           ├── index.faiss
│           ├── index.pkl
│           └── embedding_provider.txt   # Compatibilidad
│
├── 📁 docs/                             # DOCUMENTACIÓN
│   ├── VELORA_SYSTEM_ARCHITECTURE.md    # Este documento
│   ├── AGENTIC_INTERVIEWER.md
│   ├── EMBEDDINGS_ARCHITECTURE.md
│   ├── HYPERPARAMETERS_GUIDE.md
│   └── ...
│
├── requirements.txt                     # Dependencias pip
├── pyproject.toml                       # Configuración proyecto
├── run_app.py                           # Script de ejecución
└── README.md
```

---

# 2. GUÍA DE PATRONES IMPLEMENTADOS

## 2.1 Singleton Pattern - OperationalLogger

```python
# logging_config.py
class OperationalLogger:
    _instance: Optional['OperationalLogger'] = None
    _initialized: bool = False
    
    def __new__(cls) -> 'OperationalLogger':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if OperationalLogger._initialized:
            return  # Evita re-inicialización
        OperationalLogger._initialized = True
        # ... setup ...

# Uso global
op_logger = OperationalLogger()

def get_operational_logger() -> OperationalLogger:
    return op_logger
```

**Justificación**: Un único logger para todo el sistema garantiza:
- Consistencia en formato
- Sin duplicación de handlers
- Estado compartido

---

## 2.2 Factory Pattern - LLMFactory / EmbeddingFactory

```python
# factory.py
class LLMFactory:
    @staticmethod
    def create_llm(
        provider: str,      # "openai" | "google" | "anthropic"
        model_name: str,
        temperature: float = 0.1,
        api_key: Optional[str] = None
    ) -> BaseChatModel:
        
        if provider == "openai":
            return ChatOpenAI(model=model_name, temperature=temperature, ...)
        elif provider == "google":
            return ChatGoogleGenerativeAI(model=model_name, ...)
        elif provider == "anthropic":
            return ChatAnthropic(model=model_name, ...)
        else:
            raise ValueError(f"Proveedor no válido: {provider}")
```

**Justificación**: Desacopla creación de uso:
- Código de negocio no conoce el proveedor
- Cambio de proveedor = cambio de config
- Detección dinámica de disponibilidad

---

## 2.3 Pydantic Structured Output Pattern

```python
# models.py
class CVMatchingResponse(BaseModel):
    """Respuesta del LLM para matching CV-requisitos"""
    matches: List[RequirementMatch] = Field(
        ..., description="Lista de resultados de matching"
    )
    analysis_summary: str = Field(..., description="Resumen del análisis")

# analyzer.py
class Phase1Analyzer:
    def __init__(self, ...):
        # Crear LLM con structured output
        self.matching_llm = self.llm.with_structured_output(CVMatchingResponse)
    
    def match_cv_with_requirements(self, cv, requirements):
        chain = prompt | self.matching_llm
        result: CVMatchingResponse = chain.invoke({...})
        # result es SIEMPRE un CVMatchingResponse válido
        return result.matches
```

**Justificación**: Elimina parsing manual:
- Garantía de estructura
- Validación automática
- Type hints para IDE

---

## 2.4 Generator/Streaming Pattern

```python
# agentic_interviewer.py
def stream_question(self, question_idx: int) -> Generator[str, None, None]:
    """Genera pregunta con streaming token-by-token"""
    
    chain = prompt | self.llm | StrOutputParser()
    
    question_text = ""
    for chunk in chain.stream({}):  # STREAMING REAL
        question_text += chunk
        yield chunk  # Token a token
    
    # Post-procesamiento después del streaming
    self._conversation_history.append({...})

# streamlit_app.py
for token in interviewer.stream_question(idx):
    full_question += token
    container.markdown(f"**{full_question}**|")  # Cursor parpadeante
```

**Justificación**: UX moderna tipo ChatGPT:
- Feedback visual inmediato
- Sensación de "agente pensando"
- Latencia percibida reducida

---

## 2.5 State Machine Pattern - AgenticInterviewer

```python
# Estados del agente
class AgenticInterviewer:
    def initialize_interview(...):
        # Estado: INITIALIZED
        self._pending_requirements = [...]
        self._current_idx = 0
        self._conversation_history = []
    
    def stream_greeting(...):
        # Estado: GREETING → QUESTIONING
        ...
        
    def stream_question(question_idx):
        # Estado: QUESTIONING (iterativo)
        self._pending_requirements[question_idx]["asked"] = True
        ...
    
    def register_response(question_idx, response):
        # Transición condicional
        self._pending_requirements[question_idx]["answered"] = True
        is_complete = question_idx + 1 >= len(self._pending_requirements)
        # Si complete → Estado: CLOSING
    
    def stream_closing(...):
        # Estado: CLOSING → COMPLETE
        ...
```

```
┌─────────────────────────────────────────────────────────────────────┐
│              MÁQUINA DE ESTADOS - ENTREVISTA                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌───────────┐    ┌───────────┐    ┌───────────┐    ┌───────────┐ │
│  │INITIALIZED│───▶│ GREETING  │───▶│QUESTIONING│───▶│  CLOSING  │ │
│  └───────────┘    └───────────┘    └─────┬─────┘    └─────┬─────┘ │
│                                          │                 │       │
│                                          │ (loop)          │       │
│                                          ▼                 ▼       │
│                                    ┌───────────┐    ┌───────────┐ │
│                                    │  WAITING  │    │ COMPLETE  │ │
│                                    │ RESPONSE  │    │           │ │
│                                    └───────────┘    └───────────┘ │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

# 3. CÓMO EXTENDER EL SISTEMA

## 3.1 Agregar Nuevo Proveedor LLM

```python
# 1. Verificar disponibilidad (factory.py)
try:
    from langchain_nuevo_proveedor import ChatNuevoProveedor
    NUEVO_AVAILABLE = True
except ImportError:
    NUEVO_AVAILABLE = False
    ChatNuevoProveedor = None

# 2. Agregar a la factory
class LLMFactory:
    NUEVO_MODELS = ["modelo-1", "modelo-2"]
    
    @staticmethod
    def create_llm(...):
        ...
        elif provider == "nuevo":
            if not NUEVO_AVAILABLE:
                raise ImportError("...")
            return ChatNuevoProveedor(model=model_name, ...)

# 3. Actualizar UI (streamlit_app.py)
# La UI detecta automáticamente via get_available_providers()
```

## 3.2 Agregar Nueva Fase de Evaluación

```python
# 1. Crear nuevo módulo en core/
# core/phase3_technical.py
class Phase3TechnicalTest:
    def __init__(self, llm, ...):
        ...
    
    def generate_test(self, requirements: List[Requirement]):
        """Genera test técnico basado en requisitos"""
        ...
    
    def evaluate_test(self, candidate_answers: List[str]):
        """Evalúa respuestas del test técnico"""
        ...

# 2. Integrar en evaluator.py
class CandidateEvaluator:
    def __init__(self, ...):
        ...
        self.phase3_tester = Phase3TechnicalTest(...)
    
    def evaluate_with_technical_test(self, phase2_result, test_responses):
        """Ejecuta Fase 3 si se requiere"""
        ...

# 3. Agregar modelos necesarios en models.py
class TechnicalQuestion(BaseModel):
    ...

class Phase3Result(BaseModel):
    ...

# 4. Agregar prompts en prompts.py
GENERATE_TECHNICAL_TEST_PROMPT = """..."""
```

## 3.3 Agregar Nuevo Tipo de Entrada

```python
# 1. Crear extractor en extraction/
# extraction/linkedin.py
def extract_from_linkedin_url(url: str) -> Optional[str]:
    """Extrae perfil de LinkedIn"""
    ...

# 2. Exportar en extraction/__init__.py
from .linkedin import extract_from_linkedin_url

# 3. Integrar en UI
if input_type == "linkedin":
    cv_text = extract_from_linkedin_url(url)
```

---

# 4. GUÍA DE TROUBLESHOOTING

## 4.1 Errores Comunes y Soluciones

### Error: "Structured Output failed"
```
LangChain error: Output parsing failed
```

**Causa**: El LLM no generó JSON válido para el modelo Pydantic.

**Solución**:
1. Verificar que el modelo soporta structured output
2. Bajar la temperatura para mayor determinismo
3. Revisar el prompt por ambigüedades

```python
# Verificar modelo
print(f"Modelo: {model_name}")
print(f"Temp: {temperature}")

# Test con temperatura 0
llm = LLMFactory.create_llm(provider, model, temperature=0.0)
```

### Error: "Embedding dimension mismatch"
```
FAISS error: Index dimension mismatch
```

**Causa**: El índice fue creado con un proveedor de embeddings diferente.

**Solución**:
```python
# Forzar re-indexación
vectorstore = HistoryVectorStore(user_id, embedding_provider="openai")
vectorstore.rebuild_index(evaluations)

# O eliminar índice manualmente
# data/vectors/{user_id}/ → DELETE
```

### Error: "API key not found"
```
AuthenticationError: No API key provided
```

**Solución**:
```python
# 1. Via variable de entorno
export OPENAI_API_KEY="sk-..."

# 2. Via archivo .env en raíz
OPENAI_API_KEY=sk-...

# 3. Via parámetro explícito
llm = LLMFactory.create_llm(..., api_key="sk-...")
```

### Error: "Playwright not installed"
```
Error: Playwright chromium not installed
```

**Solución**:
```bash
pip install playwright
playwright install chromium
```

---

# 5. MÉTRICAS Y OBSERVABILIDAD

## 5.1 LangSmith Integration

```python
# Habilitado por defecto si hay LANGSMITH_API_KEY
from llm.factory import configure_langsmith, get_langsmith_client

# En evaluator.py
langsmith = configure_langsmith(project_name="velora-evaluator")

# Registro de feedback
evaluator.record_feedback(
    score=0.9,  # 0-1
    comment="Evaluación precisa",
    run_id=last_run_id
)
```

## 5.2 Logs Operacionales

```python
# Habilitar/deshabilitar
from core.logging_config import get_operational_logger
op_logger = get_operational_logger()
op_logger.enabled = False  # Silenciar logs

# Logs disponibles
op_logger.phase1_start(mode="langgraph")
op_logger.extraction_complete(total=12, obligatory=5, optional=7)
op_logger.matching_complete(fulfilled=8, unfulfilled=4, score=66.7)
op_logger.phase1_complete(discarded=False, score=66.7, duration_ms=4200)
```

## 5.3 Métricas de Cobertura

```python
# Validar cobertura de entrevista
coverage = interviewer.validate_coverage()
print(f"Cobertura: {coverage['coverage_percentage']:.1f}%")
print(f"Sin preguntar: {coverage['uncovered_requirements']}")
assert coverage['is_complete'], "Cobertura incompleta!"
```

---

# 6. CHECKLIST DE CONTRIBUCIÓN

## 6.1 Antes de Cada PR

- [ ] Ejecutar `python -m pytest` (si hay tests)
- [ ] Verificar imports en `__init__.py`
- [ ] Actualizar `__all__` si se agregan exports
- [ ] Documentar nuevas funciones con docstrings
- [ ] Verificar que no hay API keys hardcodeadas
- [ ] Probar con múltiples proveedores (OpenAI, Google)
- [ ] Verificar que UI no se rompe con errores

## 6.2 Convenciones de Commit

```
feat: Nueva funcionalidad
fix: Corrección de bug
docs: Documentación
refactor: Refactorización sin cambio funcional
test: Tests
chore: Mantenimiento

Ejemplo:
feat(phase2): Agregar streaming en preguntas de entrevista
fix(analyzer): Corregir parsing de requisitos duplicados
docs: Actualizar guía de contribución
```

---

# 7. REFERENCIAS RÁPIDAS

## 7.1 Comandos de Desarrollo

```bash
# Ejecutar aplicación
python run_app.py

# O directamente
streamlit run app/streamlit_app.py

# Instalar dependencias
pip install -r requirements.txt

# Instalar Playwright (para scraping)
playwright install chromium
```

## 7.2 Variables de Entorno

```bash
# Requeridas (al menos una)
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...
ANTHROPIC_API_KEY=sk-ant-...

# Opcionales
LANGSMITH_API_KEY=...              # Para trazabilidad
LANGCHAIN_TRACING_V2=true          # Auto-habilitado por LangSmith
LANGCHAIN_PROJECT=velora-evaluator # Nombre proyecto LangSmith
```

## 7.3 Rutas de Datos

```
data/user_memory/{user_id}.json    # Historial de evaluaciones
data/vectors/{user_id}/            # Índices FAISS
  ├── index.faiss
  ├── index.pkl
  └── embedding_provider.txt
```

---

*Guía de Componentes - Velora v2.0*
*Para uso interno de AI Engineers*

