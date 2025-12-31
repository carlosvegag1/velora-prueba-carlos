# Guión para Demo en Vídeo

> **Duración**: 5-8 minutos  
> **Enfoque**: Valor diferencial y decisiones técnicas (el evaluador ya conoce los requisitos base)

---

## Objetivo

El evaluador conoce la prueba: dos fases, puntuación proporcional, obligatorios descartan. Esta demo debe mostrar:

1. **Que funciona** según lo especificado
2. **Qué aporté más allá** de los requisitos
3. **Por qué tomé cada decisión**

---

## Estructura

### 1. INTRODUCCIÓN (30 segundos)

**Qué decir:**
> "Hola, soy Carlos Vega. Esta es mi prueba técnica para Ingeniero de IA Generativa.
>
> El sistema implementa las dos fases especificadas: análisis automático y entrevista conversacional.
>
> En esta demo me centraré en el **valor diferencial**: qué hice más allá de los requisitos y por qué."

**Qué mostrar:**
- Pantalla principal de Velora

---

### 2. DEMOSTRACIÓN RÁPIDA DE REQUISITOS BASE (1 minuto)

**Qué decir:**
> "Primero, una demostración rápida de que cumple los requisitos."

**Qué mostrar:**

1. **Cargar CV y oferta de ejemplo**
2. **Click en Evaluar**
3. **Mostrar resultado Fase 1:**
   - Score proporcional
   - Requisitos cumplidos/no cumplidos
   - Requisitos no encontrados

> "El sistema separa obligatorios de opcionales. Si falta un obligatorio, score cero y descartado."

4. **Iniciar Fase 2:**
   - Pregunta por requisitos faltantes
   - Responder brevemente
   - Mostrar recalculo de puntuación

> "Exactamente lo especificado: pregunta por lo que no encontró y recalcula."

---

### 3. VALOR DIFERENCIAL: ARQUITECTURA (1 minuto)

**Qué decir:**
> "Ahora, lo que aporté más allá de los requisitos.
>
> Primero, arquitectura. En lugar de un script monolítico, diseñé capas separadas."

**Qué mostrar:**
- Estructura de carpetas (breve)

> "Núcleo con lógica de negocio, orquestación con coordinadores, infraestructura con integraciones.
>
> ¿Por qué importa? Porque puedo cambiar el proveedor de LLM sin tocar el analizador. O agregar un nuevo tipo de extracción sin modificar la entrevista."

**Qué mostrar:**
- `LLMFactory` brevemente

> "Factory pattern para proveedores. Cambio de OpenAI a Anthropic es una línea de configuración."

---

### 4. VALOR DIFERENCIAL: LANGGRAPH (1 minuto)

**Qué decir:**
> "La prueba no pedía LangGraph, pero lo implementé porque un chain lineal es rígido.
>
> Con LangGraph, el análisis es un grafo de nodos: extracción, embeddings, matching, score. Puedo activar o desactivar nodos sin reescribir el flujo."

**Qué mostrar:**
- Checkbox "Potenciar con LangGraph" en UI
- Activar/desactivar
- Logs mostrando nodos ejecutándose

> "El usuario decide si quiere el análisis avanzado o el básico."

---

### 5. VALOR DIFERENCIAL: EMBEDDINGS SEMÁNTICOS (1 minuto)

**Qué decir:**
> "Otra funcionalidad adicional: embeddings semánticos con FAISS.
>
> En lugar de que el LLM analice el CV completo buscando cada requisito, primero indexo el CV en vectores. Cuando evalúo un requisito, busco los fragmentos más relevantes y se los paso al LLM como contexto."

**Qué mostrar:**
- Checkbox "Usar Embeddings Semánticos"
- Logs mostrando "CV indexado en FAISS: 12 chunks"

> "Es opcional porque hay un trade-off: mejora precisión pero añade latencia. El usuario decide."

---

### 6. VALOR DIFERENCIAL: ENTREVISTA CON STREAMING (1 minuto)

**Qué decir:**
> "La Fase 2 podía ser por terminal, pero implementé una interfaz conversacional con streaming real.
>
> Las preguntas se generan token por token, como ChatGPT. No es solo estético: da feedback inmediato y sensación de agente pensando."

**Qué mostrar:**
- Iniciar entrevista
- Observar streaming del saludo
- Streaming de pregunta

> "El sistema garantiza cobertura del 100%. Internamente trackea cada requisito preguntado. No es posible terminar sin cubrir todos."

---

### 7. VALOR DIFERENCIAL: FUNCIONALIDADES ADICIONALES (30 segundos)

**Qué decir:**
> "Otras funcionalidades que añadí:
>
> - **RAG para historial**: Un chatbot que consulta evaluaciones previas. '¿Por qué me rechazaron?' y te responde con contexto.
> - **Niveles de confianza**: Cada match tiene `alto/medio/bajo` con razonamiento.
> - **LangSmith**: Trazabilidad completa de llamadas LLM.
> - **Scraping con Playwright**: Para URLs de portales que bloquean requests básicos."

**Qué mostrar:**
- Tab "Mi Historial" con chatbot
- O mencionar brevemente

---

### 8. DECISIÓN TÉCNICA REAL: LATENCIA (45 segundos)

**Qué decir:**
> "Les cuento un problema real que encontré.
>
> Al activar embeddings, la latencia subía mucho. Gracias a la arquitectura modular, localicé el problema en 5 minutos: el modelo de embeddings era antiguo.
>
> Cambié `ada-002` por `text-embedding-3-small`. Una línea de código. Latencia bajó 40%.
>
> Esto es la diferencia entre código funcional y arquitectura bien diseñada: los problemas se resuelven localmente."

**Qué mostrar:**
- Abrir `embedding_proveedor.py` y señalar la línea

---

### 9. CIERRE (30 segundos)

**Qué decir:**
> "En resumen:
>
> - El sistema cumple los requisitos especificados
> - Aporté arquitectura modular, LangGraph, embeddings semánticos, streaming, RAG, observabilidad
> - Cada decisión tiene justificación
>
> La documentación técnica está en el repositorio. Estoy disponible para cualquier pregunta o debugging en tiempo real.
>
> Gracias."

---

## Tiempos

| Sección | Duración |
|---------|----------|
| Introducción | 30s |
| Requisitos base | 60s |
| Arquitectura | 60s |
| LangGraph | 60s |
| Embeddings | 60s |
| Streaming | 60s |
| Funcionalidades | 30s |
| Latencia | 45s |
| Cierre | 30s |
| **Total** | **~7 min** |

---

## Notas

- **No explicar qué es la prueba**: El evaluador lo sabe
- **Enfocarse en el "más allá"**: Valor diferencial
- **Justificar decisiones**: "Lo hice porque..."
- **Tono directo**: Sin rodeos, técnico pero accesible
- **Si algo falla**: Mostrar cómo debuggear demuestra madurez

---

*Guión para prueba técnica de Velora*  
*Carlos Vega | Diciembre 2024*
