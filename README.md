# Velora - Sistema de Evaluación de Candidatos con IA

> **Prueba técnica para Ingeniero de IA Generativa**  
> Desarrollada por Carlos Vega | Diciembre 2024

---

## Cumplimiento de Requisitos

El sistema implementa **completamente** las dos fases especificadas:

| Requisito | Estado | Implementación |
|-----------|--------|----------------|
| Fase 1: Análisis CV vs Oferta | ✅ | Extracción de requisitos + matching con puntuación |
| Requisitos obligatorios vs opcionales | ✅ | Flag `discarded` cuando falta obligatorio |
| Puntuación proporcional | ✅ | `score = (cumplidos / total) * 100` |
| Fase 2: Entrevista por requisitos faltantes | ✅ | Conversación para requisitos no encontrados |
| Recalcular puntuación post-entrevista | ✅ | Reevaluación automática |
| LangChain con proveedores intercambiables | ✅ | OpenAI, Google, Anthropic |
| Proyecto ejecutable con dependencias | ✅ | `requirements.txt` |
| Docker | ✅ | `Dockerfile` + `docker-compose.yml` |
| Interfaz UI (valorable) | ✅ | Streamlit con diseño corporativo |

---

## Valor Diferencial Aportado

Más allá de los requisitos base, implementé funcionalidades adicionales para demostrar capacidades como ingeniero de IA:

### Arquitectura
- **Backend modular por capas**: Separación clara entre núcleo, orquestación, infraestructura
- **Configuración centralizada**: Cambios sin tocar código de negocio
- **Nomenclatura bilingüe**: Código en castellano con aliases en inglés para flexibilidad

### Tecnologías Avanzadas de LangChain
- **LangGraph**: Orquestación multi-agente con grafo de estados (activable/desactivable)
- **LangSmith**: Trazabilidad completa de llamadas LLM
- **Structured Output**: Respuestas garantizadas en formato Pydantic (sin parsing manual)

### Funcionalidades Adicionales
- **Embeddings semánticos con FAISS**: Búsqueda de evidencia en CV (opcional)
- **RAG para historial**: Chatbot que consulta evaluaciones previas
- **Hiperparametrización contextual**: Temperaturas diferenciadas por fase
- **Streaming real**: Entrevista con generación token-by-token
- **Scraping avanzado**: Playwright para URLs protegidas (LinkedIn, portales corporativos)
- **Niveles de confianza**: Cada match incluye `high/medium/low` con razonamiento
- **Logs operacionales**: Trazabilidad en tiempo real sin datos sensibles

---

## Quick Start

```bash
# Instalación
python -m venv venv
source venv/bin/activate  # Linux/Mac (o venv\Scripts\activate en Windows)
pip install -r requirements.txt

# Configurar API key
cp env.example .env
# Editar .env con OPENAI_API_KEY (o GOOGLE_API_KEY / ANTHROPIC_API_KEY)

# Ejecutar
streamlit run frontend/streamlit_app.py
```

**Con Docker:**
```bash
docker compose up --build
```

Acceder a **http://localhost:8501**

---

## Estructura del Proyecto

```
├── backend/
│   ├── modelos.py              # Modelos Pydantic
│   ├── nucleo/                 # Lógica: análisis, entrevista, historial
│   ├── orquestacion/           # Coordinadores + LangGraph
│   ├── infraestructura/        # LLM, embeddings, persistencia
│   └── recursos/               # Prompts centralizados
├── frontend/streamlit_app.py   # UI Streamlit
├── docs/
│   ├── DOCUMENTACION_TECNICA.md  # Detalles de implementación
│   └── GUION_DEMO_VIDEO.md       # Guión para demo
├── docker-compose.yml
└── Dockerfile
```

---

## Documentación

- **[Documentación Técnica](docs/DOCUMENTACION_TECNICA.md)**: Decisiones de diseño, arquitectura, valor diferencial
- **[Guión Demo](docs/GUION_DEMO_VIDEO.md)**: Estructura para vídeo demostrativo
- **[Demo en Vídeo](https://youtube.com/...)**: *(enlace pendiente)*

---

## Contacto

Disponible para discusión técnica, debugging o profundización sobre cualquier aspecto.

**Carlos Vega**
