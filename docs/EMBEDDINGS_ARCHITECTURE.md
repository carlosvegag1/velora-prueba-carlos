# Arquitectura de Embeddings v1.0 - Velora Auto Evaluator

## Resumen Ejecutivo

Este documento detalla la arquitectura **simplificada** de embeddings del sistema. La versión 1.0 implementa un **mapeo unívoco 1:1 entre proveedor y modelo de embedding**, eliminando complejidad innecesaria y centralizando las decisiones técnicas.

---

## 🎯 Arquitectura Simplificada: Mapeo 1:1

### Principio Fundamental

**Cada proveedor tiene UN único modelo de embedding predefinido y optimizado.**

| Proveedor | Modelo de Embedding | Dimensiones | Notas |
|-----------|---------------------|-------------|-------|
| **OpenAI** | `text-embedding-3-small` | 1536 | Óptimo costo/rendimiento |
| **Google** | `models/text-embedding-004` | 768 | Última versión disponible |
| **Anthropic** | ❌ NO DISPONIBLE | - | Sin API de embeddings |

### Beneficios de esta Arquitectura

1. **Eliminación de complejidad**: No hay selección múltiple de modelos
2. **Decisiones técnicas predefinidas**: Los modelos óptimos ya están seleccionados
3. **Menor superficie de error**: Sin configuración incorrecta posible
4. **Mantenibilidad superior**: Cambios centralizados en un único lugar

---

## ⚠️ Gestión de Anthropic (Sin Embeddings)

### El Problema
Anthropic **no ofrece API de embeddings** consumible directamente.

### La Solución

Cuando el usuario selecciona Anthropic como proveedor LLM:

1. **Notificación proactiva en UI**:
   ```
   ⚠️ Anthropic no ofrece API de embeddings propia. 
   Las funcionalidades de embeddings semánticos quedan deshabilitadas con este proveedor.
   ```

2. **Deshabilitación automática del toggle "Embeddings Semánticos"**:
   - El checkbox aparece deshabilitado (grayed out)
   - Tooltip explicativo al hover

3. **Fallback automático** (si hay otra API key disponible):
   - Si existe `OPENAI_API_KEY` → usa embeddings de OpenAI
   - Si existe `GOOGLE_API_KEY` → usa embeddings de Google
   - Si no hay ninguna → funcionalidades de embeddings deshabilitadas

### Escenarios de Configuración

| LLM Seleccionado | API Keys Disponibles | Embeddings Usados |
|-----------------|---------------------|-------------------|
| OpenAI | OPENAI_API_KEY | OpenAI ✅ |
| Google | GOOGLE_API_KEY | Google ✅ |
| Anthropic | Solo ANTHROPIC_API_KEY | ❌ Deshabilitados |
| Anthropic | + OPENAI_API_KEY | OpenAI (fallback) ✅ |
| Anthropic | + GOOGLE_API_KEY | Google (fallback) ✅ |

---

## 🔧 Arquitectura de Código

### Estructura de Archivos

```
src/evaluator/
├── llm/
│   ├── factory.py              # LLMFactory - Crea instancias de LLM
│   ├── embeddings_factory.py   # EmbeddingFactory - Mapeo 1:1 simplificado
│   └── prompts.py              # Prompts para extracción y matching
├── core/
│   ├── analyzer.py             # Phase1Analyzer - Gestión elegante de Anthropic
│   ├── embeddings.py           # SemanticMatcher - Arquitectura simplificada
│   └── interviewer.py          # Phase2Interviewer - Cobertura 100% garantizada
├── rag/
│   ├── vectorstore.py          # HistoryVectorStore - FAISS para historial
│   └── chatbot.py              # HistoryChatbot - RAG conversacional
└── storage/
    └── memory.py               # EnrichedEvaluation - Datos para RAG
```

### API del EmbeddingFactory

```python
from src.evaluator.llm.embeddings_factory import EmbeddingFactory

# Verificar si un proveedor soporta embeddings
EmbeddingFactory.supports_embeddings("anthropic")  # False
EmbeddingFactory.supports_embeddings("openai")     # True

# Obtener el modelo asignado (mapeo 1:1)
EmbeddingFactory.get_embedding_model("openai")     # "text-embedding-3-small"
EmbeddingFactory.get_embedding_model("google")     # "models/text-embedding-004"

# Crear instancia de embeddings
embeddings = EmbeddingFactory.create_embeddings(
    provider="openai",
    api_key="sk-..."  # Opcional, puede venir del entorno
)

# Obtener mensaje de advertencia para proveedores sin embeddings
msg = EmbeddingFactory.get_embedding_provider_message("anthropic")
# "⚠️ Anthropic no ofrece API de embeddings..."

# Buscar proveedor fallback
fallback = EmbeddingFactory.get_fallback_provider(exclude_provider="anthropic")
# Retorna "openai" o "google" si tienen API key disponible
```

---

## 📊 Flujo de Embeddings en el Sistema

### 1. Matching Semántico CV vs Requisitos

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ CV (texto)  │────▶│ SemanticMatcher  │────▶│ FAISS VectorDB  │
└─────────────┘     │  - chunk CV      │     │  - similarity   │
                    │  - embed chunks  │     │    search       │
                    └──────────────────┘     └─────────────────┘
                            │                        │
                            ▼                        ▼
                    ┌──────────────────┐     ┌─────────────────┐
                    │ Para c/requisito │     │ Evidencia       │
                    │ buscar evidencia │────▶│ semántica       │
                    └──────────────────┘     └─────────────────┘
```

**¿Cuándo se usa?**
- Solo cuando el toggle "Embeddings Semánticos" está **ACTIVADO**
- Mejora la precisión del matching al pre-filtrar información relevante del CV

### 2. RAG para Historial de Evaluaciones

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ Consulta        │────▶│ HistoryChatbot   │────▶│ FAISS Index     │
│ "¿Por qué me    │     │ - embed query    │     │ - retrieve top  │
│  rechazaron?"   │     │ - search history │     │   evaluaciones  │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                │                        │
                                ▼                        ▼
                        ┌──────────────────┐     ┌─────────────────┐
                        │ LLM genera       │◀────│ Contexto        │
                        │ respuesta        │     │ recuperado      │
                        └──────────────────┘     └─────────────────┘
```

---

## 💾 Almacenamiento de Vectores

```
data/
└── vectors/
    └── {user_id}/
        ├── index.faiss   # Índice FAISS binario
        └── index.pkl     # Metadata de documentos
```

**Características:**
- Un índice por usuario
- Persistencia automática tras cada evaluación
- Recarga automática al iniciar la aplicación

---

## ✅ Variables de Entorno

```bash
# Para LLM
OPENAI_API_KEY=sk-...           # OpenAI GPT-*
GOOGLE_API_KEY=AIza...          # Google Gemini
ANTHROPIC_API_KEY=sk-ant-...    # Anthropic Claude (sin embeddings)

# Los embeddings usan las mismas API keys que los LLM
# OpenAI Embeddings: OPENAI_API_KEY
# Google Embeddings: GOOGLE_API_KEY

# Opcional: LangSmith Tracing
LANGSMITH_API_KEY=ls-...
```

---

## 📈 Rendimiento

| Operación | Tiempo Típico | Notas |
|-----------|---------------|-------|
| Crear embeddings (1 chunk) | ~50ms | Depende del proveedor |
| Indexar CV (10 chunks) | ~500ms | Incluye chunking + embeddings |
| Búsqueda semántica (1 query) | ~100ms | FAISS es muy rápido |
| Indexar historial (50 evals) | ~2s | Una sola vez por sesión |

---

## ✅ Checklist de Configuración

- [ ] Tengo al menos una API key de embeddings (`OPENAI_API_KEY` o `GOOGLE_API_KEY`)
- [ ] Si uso Anthropic Claude, tengo otra API key para embeddings (o los desactivo)
- [ ] El directorio `data/vectors/` tiene permisos de escritura
- [ ] El toggle "Embeddings Semánticos" está configurado según mis necesidades

---

**Versión del documento:** 1.0  
**Última actualización:** Diciembre 2024
