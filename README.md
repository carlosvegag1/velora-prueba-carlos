# Sistema de Evaluacion de Candidatos con IA

Prueba tecnica para Ingeniero de IA Generativa | Carlos Vega | Enero 2025

---

## Inicio Rapido con Docker

```bash
 git clone https://github.com/carlosvegag1/velora-prueba-carlos.git
cd carlos_prueba_tecnica
cp .env.example .env
# Editar .env con tu API key: OPENAI_API_KEY=sk-...
docker compose up --build
```

Acceder a http://localhost:8501

Primera ejecucion tarda 3-5 minutos (instalacion de dependencias y Chromium).

---

## Instalacion Manual

### Requisitos
- Python 3.9+
- API Key de OpenAI (o Google/Anthropic)

### Pasos

```bash
python -m venv venv
# Linux/Mac: source venv/bin/activate
# Windows: venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
cp .env.example .env
# Editar .env con API key
streamlit run frontend/streamlit_app.py
```

---

## Cumplimiento de Requisitos

| Requisito | Implementacion |
|-----------|----------------|
| Fase 1: Analisis CV vs Oferta | Extraccion de requisitos + matching con puntuacion |
| Requisitos obligatorios vs opcionales | Flag `discarded` cuando falta obligatorio |
| Puntuacion proporcional | `score = (cumplidos / total) * 100` |
| Fase 2: Entrevista conversacional | Conversacion para requisitos no encontrados |
| Recalculo post-entrevista | Reevaluacion automatica |
| LangChain con proveedores intercambiables | OpenAI, Google, Anthropic |
| Docker | Dockerfile + docker-compose.yml |
| Interfaz UI | Streamlit con diseno corporativo |

---

## Stack Tecnologico

- **Backend**: Python 3.11, LangChain, LangGraph
- **Frontend**: Streamlit
- **LLM**: OpenAI (default), Google Gemini, Anthropic Claude
- **Embeddings**: FAISS con OpenAI/Google embeddings
- **Scraping**: Playwright + BeautifulSoup
- **Trazabilidad**: LangSmith (opcional)

---

## Estructura del Proyecto

```
backend/
  modelos.py              # Modelos Pydantic
  nucleo/                 # Logica: analisis, entrevista, historial
  orquestacion/           # Coordinadores + LangGraph
  infraestructura/        # LLM, embeddings, persistencia
  recursos/               # Prompts centralizados
frontend/
  streamlit_app.py        # UI Streamlit
docs/
  ejemplos/               # CVs y ofertas de prueba
```

---

## Solucion de Problemas

**Error: "API key not found"**
```bash
# Verificar .env contiene: OPENAI_API_KEY=sk-...
```

**Docker: "Port 8501 already in use"**
```bash
# Cambiar puerto en .env: VELORA_PORT=8502
# O detener contenedor: docker compose down
```

---

Para documentacion tecnica detallada, ver [README-EXTENSO.md](README-EXTENSO.md).

**Carlos Vega**
