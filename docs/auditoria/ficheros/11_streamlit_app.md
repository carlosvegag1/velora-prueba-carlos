# Documentación: `frontend/streamlit_app.py`

## Información General

| Atributo | Valor |
|----------|-------|
| **Ruta** | `/frontend/streamlit_app.py` |
| **Tipo** | Interfaz de usuario |
| **Líneas** | ~800 |
| **Framework** | Streamlit |

---

## Propósito

Este archivo implementa la **interfaz de usuario completa** de Velora usando Streamlit. Maneja:

1. Configuración de API keys
2. Carga de CVs y ofertas
3. Visualización de resultados de Fase 1
4. Entrevista conversacional de Fase 2
5. Historial de evaluaciones

---

## Conceptos de Streamlit

### ¿Qué es Streamlit?

Framework de Python para crear apps web sin JavaScript:

```python
import streamlit as st

st.title("Mi App")
nombre = st.text_input("Tu nombre")
if st.button("Saludar"):
    st.write(f"Hola, {nombre}!")
```

### Session State

Streamlit re-ejecuta el script en cada interacción. `session_state` persiste datos:

```python
# Inicializar si no existe
if 'contador' not in st.session_state:
    st.session_state['contador'] = 0

# Usar
st.session_state['contador'] += 1
st.write(f"Contador: {st.session_state['contador']}")
```

---

## Estructura del Archivo

### 1. Configuración de Página

```python
st.set_page_config(
    page_title="Velora - Evaluador de Candidatos",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded"
)
```

| Parámetro | Valor | Descripción |
|-----------|-------|-------------|
| `page_title` | Velora... | Título en pestaña del navegador |
| `page_icon` | 🔮 | Favicon |
| `layout` | wide | Usa todo el ancho de pantalla |
| `initial_sidebar_state` | expanded | Sidebar abierta por defecto |

### 2. Estilos CSS

```python
st.markdown("""
<style>
    /* Variables CSS (paleta corporativa) */
    :root {
        --velora-primary: #6366F1;
        --velora-secondary: #8B5CF6;
        --velora-success: #10B981;
        --velora-danger: #EF4444;
    }
    
    /* Estilos personalizados */
    .stButton > button {
        background: linear-gradient(135deg, var(--velora-primary), var(--velora-secondary));
        color: white;
        border: none;
        border-radius: 8px;
    }
    
    /* Más estilos... */
</style>
""", unsafe_allow_html=True)
```

**¿Por qué `unsafe_allow_html=True`?**

Por defecto, Streamlit sanitiza HTML por seguridad. Este flag permite inyectar CSS/HTML personalizado.

---

### 3. Sidebar de Configuración

```python
with st.sidebar:
    render_sidebar_logo()
    
    st.header("⚙️ Configuración")
    
    # Selección de proveedor
    proveedor = st.selectbox(
        "Proveedor LLM",
        options=["openai", "google", "anthropic"],
        index=0
    )
    
    # Selección de modelo
    modelos = FabricaLLM.obtener_modelos_disponibles(proveedor)
    modelo = st.selectbox("Modelo", options=modelos)
    
    # API Key
    api_key = st.text_input(
        f"API Key de {proveedor.title()}",
        type="password",
        help="Tu clave API. No se almacena."
    )
```

**Componentes usados**:

| Componente | Propósito |
|------------|-----------|
| `st.selectbox` | Dropdown de opciones |
| `st.text_input` | Campo de texto |
| `type="password"` | Oculta el texto |
| `help=` | Tooltip de ayuda |

---

### 4. Pestañas Principales

```python
tab1, tab2, tab3 = st.tabs([
    "📝 Evaluación",
    "📊 Historial",
    "ℹ️ Información"
])
```

Crea tres pestañas. El contenido de cada una va dentro de `with tab1:`, etc.

---

### 5. Pestaña de Evaluación

```python
with tab1:
    st.header("Evaluación de Candidato")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📄 CV del Candidato")
        
        # Opción 1: Subir archivo
        cv_file = st.file_uploader(
            "Sube tu CV",
            type=["pdf", "txt"],
            help="Formatos aceptados: PDF, TXT"
        )
        
        # Opción 2: Pegar texto
        cv_texto = st.text_area(
            "O pega el texto del CV",
            height=300
        )
```

**`st.columns`**: Divide el espacio en columnas.

**`st.file_uploader`**: Widget para subir archivos.

```python
    with col2:
        st.subheader("💼 Oferta de Trabajo")
        
        # Opción 1: URL
        url_oferta = st.text_input(
            "URL de la oferta",
            placeholder="https://ejemplo.com/oferta/123"
        )
        
        # Opción 2: Texto
        oferta_texto = st.text_area(
            "O pega el texto de la oferta",
            height=300
        )
```

---

### 6. Procesamiento del CV

```python
def obtener_texto_cv():
    """Extrae texto del CV según la fuente."""
    
    if cv_file is not None:
        # Si es PDF
        if cv_file.name.endswith('.pdf'):
            from backend.infraestructura import extraer_texto_de_pdf
            return extraer_texto_de_pdf(cv_file.read())
        else:
            # Si es TXT
            return cv_file.read().decode('utf-8')
    
    elif cv_texto:
        return cv_texto
    
    return None
```

---

### 7. Botón de Evaluación

```python
if st.button("🚀 Iniciar Evaluación", use_container_width=True):
    # Validaciones
    texto_cv = obtener_texto_cv()
    texto_oferta = obtener_texto_oferta()
    
    if not texto_cv:
        st.error("Por favor, proporciona un CV")
        st.stop()
    
    if not texto_oferta:
        st.error("Por favor, proporciona una oferta de trabajo")
        st.stop()
    
    if not api_key:
        st.error(f"Por favor, introduce tu API key de {proveedor}")
        st.stop()
```

**`st.stop()`**: Detiene la ejecución del script sin error.

---

### 8. Ejecución con Spinner

```python
    with st.spinner("Analizando CV..."):
        # Crear orquestador
        orquestador = Orquestador(
            proveedor=proveedor,
            modelo=modelo,
            api_key=api_key
        )
        
        # Ejecutar evaluación
        resultado = orquestador.evaluar_candidato(
            cv=texto_cv,
            oferta_trabajo=texto_oferta,
            nombre_candidato=nombre_candidato
        )
        
        # Guardar en session_state
        st.session_state['resultado_fase1'] = resultado.resultado_fase1
        st.session_state['texto_cv'] = texto_cv
```

**`st.spinner`**: Muestra un indicador de carga mientras procesa.

---

### 9. Visualización de Resultados Fase 1

```python
def display_phase1_results(resultado: ResultadoFase1):
    """Renderiza los resultados de Fase 1."""
    
    # Métricas principales
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="Puntuación",
            value=f"{resultado.puntuacion:.1f}%",
            delta=None
        )
    
    with col2:
        st.metric(
            label="Requisitos Cumplidos",
            value=len(resultado.requisitos_cumplidos)
        )
    
    with col3:
        st.metric(
            label="Requisitos No Cumplidos",
            value=len(resultado.requisitos_no_cumplidos)
        )
```

**`st.metric`**: Widget para mostrar KPIs con formato bonito.

```python
    # Detalles de requisitos
    st.subheader("Requisitos Cumplidos ✅")
    for req in resultado.requisitos_cumplidos:
        with st.expander(f"{req.descripcion}"):
            st.write(f"**Tipo**: {format_tipo(req.tipo)}")
            st.write(f"**Confianza**: {format_confianza(req.confianza)}")
            if req.evidencia:
                st.write(f"**Evidencia**: {req.evidencia}")
    
    st.subheader("Requisitos No Cumplidos ❌")
    for req in resultado.requisitos_no_cumplidos:
        with st.expander(f"{req.descripcion}"):
            # Similar...
```

**`st.expander`**: Sección colapsable.

---

### 10. Entrevista Conversacional (Fase 2)

Esta es la parte más compleja del frontend.

```python
def render_agentic_interview(
    entrevistador: EntrevistadorFase2,
    resultado_fase1: ResultadoFase1,
    contexto_cv: str
):
    """
    Renderiza la entrevista conversacional con streaming.
    """
    
    # Inicializar estado del chat
    if 'chat_messages' not in st.session_state:
        st.session_state['chat_messages'] = []
    
    if 'current_question_index' not in st.session_state:
        st.session_state['current_question_index'] = 0
    
    # Contenedor del chat
    chat_container = st.container()
```

### Streaming del Saludo

```python
    # Si es el inicio, mostrar saludo
    if st.session_state['current_question_index'] == 0 and not st.session_state['chat_messages']:
        with chat_container:
            with st.chat_message("assistant"):
                # Streaming del saludo
                saludo_placeholder = st.empty()
                saludo_completo = ""
                
                for token in entrevistador.transmitir_saludo():
                    saludo_completo += token
                    saludo_placeholder.markdown(saludo_completo + "▌")
                
                saludo_placeholder.markdown(saludo_completo)
        
        # Guardar en historial
        st.session_state['chat_messages'].append({
            "role": "assistant",
            "content": saludo_completo
        })
```

**¿Cómo funciona el streaming?**

1. `st.empty()` crea un placeholder vacío
2. El loop recibe tokens uno a uno
3. Actualiza el placeholder con el texto acumulado
4. El "▌" simula un cursor mientras escribe

### Streaming de Preguntas

```python
    # Mostrar siguiente pregunta
    if st.session_state['current_question_index'] < len(requisitos_pendientes):
        with chat_container:
            with st.chat_message("assistant"):
                pregunta_placeholder = st.empty()
                pregunta_completa = ""
                
                for token in entrevistador.transmitir_pregunta(
                    st.session_state['current_question_index']
                ):
                    pregunta_completa += token
                    pregunta_placeholder.markdown(pregunta_completa + "▌")
                
                pregunta_placeholder.markdown(pregunta_completa)
        
        st.session_state['chat_messages'].append({
            "role": "assistant",
            "content": pregunta_completa
        })
```

### Entrada del Usuario

```python
    # Campo de respuesta
    respuesta = st.chat_input("Tu respuesta...")
    
    if respuesta:
        # Mostrar respuesta del usuario
        with chat_container:
            with st.chat_message("user"):
                st.write(respuesta)
        
        st.session_state['chat_messages'].append({
            "role": "user",
            "content": respuesta
        })
        
        # Registrar y evaluar respuesta
        idx = st.session_state['current_question_index']
        resp_entrevista = entrevistador.registrar_respuesta(idx, respuesta)
        
        # Evaluar
        requisito = requisitos_pendientes[idx]
        evaluacion = entrevistador.evaluar_respuesta(
            descripcion_requisito=requisito["description"],
            tipo_requisito=TipoRequisito(requisito["type"]),
            contexto_cv=contexto_cv,
            respuesta_candidato=respuesta
        )
        
        resp_entrevista.evaluacion = evaluacion
        
        # Siguiente pregunta
        st.session_state['current_question_index'] += 1
        st.rerun()  # Re-ejecutar para mostrar siguiente pregunta
```

**`st.chat_input`**: Input especial para chats, siempre en la parte inferior.

**`st.chat_message`**: Contenedor con avatar y estilo de chat.

**`st.rerun()`**: Re-ejecuta el script desde el inicio (con session_state actualizado).

---

### 11. Cierre de Entrevista

```python
    # Si se completaron todas las preguntas
    if st.session_state['current_question_index'] >= len(requisitos_pendientes):
        # Recalcular puntuación
        respuestas = entrevistador.obtener_respuestas_entrevista()
        resultado_final = orquestador.reevaluar_con_entrevista(
            resultado_fase1, respuestas
        )
        
        # Streaming del cierre
        with chat_container:
            with st.chat_message("assistant"):
                cierre_placeholder = st.empty()
                cierre_completo = ""
                
                for token in entrevistador.transmitir_cierre(
                    aprobado=not resultado_final.descartado_final
                ):
                    cierre_completo += token
                    cierre_placeholder.markdown(cierre_completo + "▌")
                
                cierre_placeholder.markdown(cierre_completo)
        
        # Mostrar resultado final
        display_final_results(resultado_final)
```

---

## Flujo de la Aplicación

```
┌──────────────────────────────────────────────────────────────────┐
│                    streamlit_app.py                               │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────────┐
                    │ Configurar página   │
                    │ (set_page_config)   │
                    └─────────────────────┘
                              │
                              ▼
                    ┌─────────────────────┐
                    │ Inyectar CSS        │
                    │ (st.markdown)       │
                    └─────────────────────┘
                              │
                              ▼
                    ┌─────────────────────┐
                    │ Sidebar:            │
                    │ - Proveedor         │
                    │ - Modelo            │
                    │ - API Key           │
                    └─────────────────────┘
                              │
                              ▼
                    ┌─────────────────────┐
                    │ Pestañas:           │
                    │ - Evaluación        │
                    │ - Historial         │
                    │ - Info              │
                    └─────────────────────┘
                              │
          ┌───────────────────┴───────────────────┐
          │                                       │
          ▼                                       ▼
┌─────────────────────┐               ┌─────────────────────┐
│ Tab Evaluación      │               │ Tab Historial       │
│ - Cargar CV         │               │ - Ver evaluaciones  │
│ - Cargar Oferta     │               │ - RAG chatbot       │
│ - Ejecutar          │               │                     │
└─────────────────────┘               └─────────────────────┘
          │
          ▼
┌─────────────────────┐
│ Fase 1: Análisis    │
│ (st.spinner)        │
└─────────────────────┘
          │
          ▼
┌─────────────────────┐
│ Mostrar resultados  │
│ (display_phase1)    │
└─────────────────────┘
          │
          ▼
┌─────────────────────┐
│ ¿Necesita Fase 2?   │
└─────────────────────┘
     │           │
    SÍ          NO
     │           │
     ▼           ▼
┌──────────┐  ┌──────────┐
│ render_  │  │ Resultado│
│ agentic_ │  │ final    │
│ interview│  │          │
└──────────┘  └──────────┘
```

---

## Justificación de Diseño

### ¿Por qué Streamlit?

| Alternativa | Desventaja |
|-------------|------------|
| Flask + HTML | Requiere JavaScript, más código |
| Django | Demasiado pesado para este caso |
| FastAPI + React | Dos lenguajes, más complejidad |
| **Streamlit** | ✅ Python puro, rápido desarrollo |

### ¿Por qué streaming en la entrevista?

Sin streaming:
1. Usuario hace pregunta
2. Espera 3-5 segundos sin feedback
3. Respuesta aparece de golpe

Con streaming:
1. Usuario hace pregunta
2. Ve la respuesta escribirse en tiempo real
3. Experiencia más natural

### ¿Por qué session_state para el chat?

Streamlit re-ejecuta todo el script en cada interacción. Sin session_state:
- El historial del chat se perdería
- Las respuestas anteriores desaparecerían
- No habría continuidad

