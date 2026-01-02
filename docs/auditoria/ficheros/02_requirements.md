# Documentación: `requirements.txt`

## Información General

| Atributo | Valor |
|----------|-------|
| **Ruta** | `/requirements.txt` |
| **Tipo** | Archivo de configuración |
| **Propósito** | Lista de dependencias Python |

---

## ¿Qué es `requirements.txt`?

Es el archivo estándar de Python para declarar las dependencias de un proyecto. Cuando alguien clona el repositorio, puede instalar todo con:

```bash
pip install -r requirements.txt
```

---

## Contenido Completo Explicado

### Core LangChain

```
# Core LangChain
langchain>=0.1.0
langchain-core>=0.1.23
langchain-community>=0.0.10
pydantic>=2.5.3
python-dotenv>=1.0.0
```

| Paquete | Versión | Propósito |
|---------|---------|-----------|
| `langchain` | ≥0.1.0 | Framework principal para LLMs |
| `langchain-core` | ≥0.1.23 | Componentes base (prompts, output parsers) |
| `langchain-community` | ≥0.0.10 | Integraciones comunitarias (FAISS, etc.) |
| `pydantic` | ≥2.5.3 | Validación de datos y Structured Output |
| `python-dotenv` | ≥1.0.0 | Cargar variables de entorno desde `.env` |

**¿Por qué estos paquetes?**
- `langchain` es el framework elegido para trabajar con LLMs
- `pydantic` v2 es requerido para Structured Output
- `python-dotenv` permite configurar API keys sin hardcodear

---

### Multi-provider LLM

```
# Multi-provider LLM support
langchain-openai>=0.0.2
langchain-google-genai>=0.0.6
langchain-anthropic>=0.1.0
```

| Paquete | Versión | Propósito |
|---------|---------|-----------|
| `langchain-openai` | ≥0.0.2 | Integración con OpenAI (GPT-4, etc.) |
| `langchain-google-genai` | ≥0.0.6 | Integración con Google (Gemini) |
| `langchain-anthropic` | ≥0.1.0 | Integración con Anthropic (Claude) |

**¿Por qué tres proveedores?**
- **Flexibilidad**: El usuario elige según su preferencia/presupuesto
- **Resiliencia**: Si un proveedor tiene problemas, hay alternativas
- **Comparación**: Permite evaluar diferentes modelos

---

### LangGraph

```
# LangGraph for agent orchestration
langgraph>=0.0.20
```

| Paquete | Versión | Propósito |
|---------|---------|-----------|
| `langgraph` | ≥0.0.20 | Orquestación de flujos como grafos de estados |

**¿Por qué LangGraph?**
- Define el flujo de Fase 1 como un grafo
- Permite streaming de eventos por nodo
- Control granular del estado

---

### LangSmith

```
# LangSmith for observability
langsmith>=0.0.80
```

| Paquete | Versión | Propósito |
|---------|---------|-----------|
| `langsmith` | ≥0.0.80 | Observabilidad y debugging de LLMs |

**¿Por qué LangSmith?**
- Ver cada llamada al LLM en tiempo real
- Analizar tiempos y costos
- Evaluar calidad de prompts

---

### Embeddings y Búsqueda Vectorial

```
# Embeddings and vector search
faiss-cpu>=1.7.4
```

| Paquete | Versión | Propósito |
|---------|---------|-----------|
| `faiss-cpu` | ≥1.7.4 | Búsqueda vectorial eficiente (sin GPU) |

**¿Por qué `faiss-cpu`?**
- `faiss-gpu` requiere CUDA/GPU, no disponible en todos los sistemas
- `faiss-cpu` es suficiente para volúmenes pequeños/medianos
- Funciona en Docker sin configuración especial

---

### Web Application

```
# Web application
streamlit>=1.28.0
```

| Paquete | Versión | Propósito |
|---------|---------|-----------|
| `streamlit` | ≥1.28.0 | Framework de frontend en Python |

**¿Por qué Streamlit?**
- Crear interfaces web sin JavaScript
- Widgets interactivos integrados
- Ideal para prototipos y MVPs

---

### HTTP y Web Scraping

```
# HTTP and web scraping
requests>=2.31.0
beautifulsoup4>=4.12.0
playwright>=1.40.0
```

| Paquete | Versión | Propósito |
|---------|---------|-----------|
| `requests` | ≥2.31.0 | Peticiones HTTP simples |
| `beautifulsoup4` | ≥4.12.0 | Parsear HTML |
| `playwright` | ≥1.40.0 | Automatización de navegador (JavaScript) |

**¿Por qué dos niveles de scraping?**
- `requests` + `beautifulsoup4`: Rápido, para páginas estáticas
- `playwright`: Para páginas que requieren JavaScript

---

### Document Processing

```
# Document processing
pypdf>=3.0.0
```

| Paquete | Versión | Propósito |
|---------|---------|-----------|
| `pypdf` | ≥3.0.0 | Extraer texto de PDFs |

**¿Por qué pypdf?**
- Ligero, sin dependencias pesadas
- Funciona para PDFs con texto (no escaneados)
- Antes se llamaba PyPDF2, ahora es `pypdf`

---

## Sintaxis del Archivo

### Especificadores de Versión

| Sintaxis | Significado | Ejemplo |
|----------|-------------|---------|
| `==1.0.0` | Exactamente esa versión | `pydantic==2.5.3` |
| `>=1.0.0` | Esa versión o superior | `langchain>=0.1.0` |
| `<=1.0.0` | Esa versión o inferior | `numpy<=1.24.0` |
| `>=1.0.0,<2.0.0` | Rango de versiones | `pydantic>=2.0.0,<3.0.0` |
| `~=1.0.0` | Compatible (≥1.0.0,<1.1.0) | `requests~=2.31.0` |

### Comentarios

```
# Esto es un comentario
langchain>=0.1.0  # También puede ir al final
```

---

## Instalación

### Instalación Básica

```bash
pip install -r requirements.txt
```

### Instalación con Virtual Environment (Recomendado)

```bash
# Crear venv
python -m venv venv

# Activar (Linux/Mac)
source venv/bin/activate

# Activar (Windows)
venv\Scripts\activate

# Instalar
pip install -r requirements.txt
```

### Post-instalación de Playwright

Playwright requiere instalar los navegadores después de pip:

```bash
playwright install chromium
```

---

## Dependencias Transitivas

Cuando instalas un paquete, también se instalan sus dependencias:

```
langchain
    ├── langchain-core
    ├── pydantic
    ├── aiohttp
    ├── tenacity
    └── ...muchos más
```

No necesitas listar las dependencias transitivas; pip las resuelve automáticamente.

---

## Versiones Mínimas vs Exactas

### ¿Por qué `>=` en lugar de `==`?

**Con `==` (exacto)**:
```
langchain==0.1.0
```
- ✅ Reproducibilidad perfecta
- ❌ Conflictos si otra dependencia necesita otra versión
- ❌ No recibes parches de seguridad

**Con `>=` (mínimo)**:
```
langchain>=0.1.0
```
- ✅ Flexibilidad para resolver dependencias
- ✅ Actualizaciones automáticas de seguridad
- ❌ Posibles incompatibilidades con versiones muy nuevas

**Decisión de Velora**: Usar `>=` para balance entre flexibilidad y estabilidad.

---

## Generación Automática

### Crear desde Instalación Actual

```bash
pip freeze > requirements.txt
```

Esto genera versiones exactas:
```
langchain==0.1.15
langchain-anthropic==0.1.1
langchain-community==0.0.27
...
```

### ¿Por qué no usar `pip freeze`?

- Incluye TODAS las dependencias (transitivas incluidas)
- Genera archivos de 100+ líneas difíciles de mantener
- Mejor: mantener manualmente solo las dependencias directas

---

## Alternativas Modernas

### pyproject.toml

```toml
[project]
dependencies = [
    "langchain>=0.1.0",
    "streamlit>=1.28.0",
]
```

### Poetry (poetry.lock)

```toml
[tool.poetry.dependencies]
langchain = "^0.1.0"
streamlit = "^1.28.0"
```

**¿Por qué usamos `requirements.txt`?**
- Es el estándar más universal
- Funciona con cualquier versión de pip
- Más simple para proyectos pequeños/medianos
- Compatible con Docker sin configuración adicional

---

## Troubleshooting

### Error: "Could not find a version that satisfies the requirement"

```
ERROR: Could not find a version that satisfies the requirement langchain>=99.0.0
```

**Causa**: La versión especificada no existe o no es compatible con tu Python.

**Solución**: Verificar versiones disponibles:
```bash
pip index versions langchain
```

### Error: "Conflicting dependencies"

```
ERROR: langchain 0.1.0 requires pydantic>=2.0, but you have pydantic 1.10.0
```

**Causa**: Dos paquetes requieren versiones incompatibles.

**Solución**: Actualizar el paquete conflictivo:
```bash
pip install --upgrade pydantic
```

### Error: "FAISS installation failed"

```
ERROR: Failed building wheel for faiss-cpu
```

**Causa**: Faltan dependencias de sistema para compilar.

**Solución en Linux**:
```bash
apt-get install -y build-essential
```

---

## Relación con Docker

En el `Dockerfile`:

```dockerfile
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
```

`--no-cache-dir` evita guardar el caché de pip, reduciendo el tamaño de la imagen.

---

## Justificación de Diseño

### ¿Por qué tan pocas dependencias?

**Filosofía de Velora**: Solo incluir lo estrictamente necesario.

| Categoría | Paquetes | Justificación |
|-----------|----------|---------------|
| Core | 5 | Base mínima para LangChain |
| Proveedores LLM | 3 | Multi-proveedor requerido |
| Orquestación | 1 | LangGraph para flujos |
| Observabilidad | 1 | LangSmith opcional pero útil |
| Vectores | 1 | FAISS es el estándar |
| Frontend | 1 | Streamlit es suficiente |
| Scraping | 3 | Dos niveles necesarios |
| PDF | 1 | pypdf es ligero |

**Total**: 16 dependencias directas (el mínimo viable).

### ¿Qué NO incluimos?

| Paquete | Razón de Exclusión |
|---------|---------------------|
| `pandas` | No procesamos datos tabulares |
| `numpy` | Solo se usa como transitiva de FAISS |
| `scikit-learn` | No hacemos ML tradicional |
| `torch` | Demasiado pesado, no necesario |
| `transformers` | Usamos APIs, no modelos locales |

