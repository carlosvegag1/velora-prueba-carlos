# Flujo de Datos en el Sistema Velora

## Introducción

Este documento traza el camino completo de los datos desde que el usuario sube un CV hasta que recibe el resultado final. Cada transformación está documentada.

---

## 1. Visión General del Flujo

```
Usuario sube CV + Oferta
         │
         ▼
┌──────────────────────────────────────────────────────────────────┐
│                    ENTRADA DE DATOS                               │
│  CV: PDF/texto → texto plano                                      │
│  Oferta: texto/URL → texto plano                                  │
└──────────────────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────────┐
│              FASE 1: EXTRACCIÓN DE REQUISITOS                     │
│  Entrada: texto_oferta                                            │
│  Salida: List[{description, type}]                                │
└──────────────────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────────┐
│            FASE 1: INDEXACIÓN SEMÁNTICA (opcional)                │
│  Entrada: texto_cv                                                │
│  Salida: FAISS index + evidencia por requisito                    │
└──────────────────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────────┐
│                FASE 1: MATCHING CV-REQUISITOS                     │
│  Entrada: texto_cv + requisitos + evidencia_semantica             │
│  Salida: List[{fulfilled, evidence, confidence}]                  │
└──────────────────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────────┐
│               FASE 1: CÁLCULO DE PUNTUACIÓN                       │
│  Entrada: matches evaluados                                       │
│  Salida: ResultadoFase1(puntuacion, descartado, ...)              │
└──────────────────────────────────────────────────────────────────┘
         │
         ▼
    ¿Descartado? ──────────────► SÍ ──────► FIN: ResultadoEvaluacion
         │
         NO (y hay faltantes)
         │
         ▼
┌──────────────────────────────────────────────────────────────────┐
│              FASE 2: ENTREVISTA CONVERSACIONAL                    │
│  Por cada requisito faltante:                                     │
│    - Generar pregunta (streaming)                                 │
│    - Recibir respuesta                                            │
│    - Evaluar respuesta                                            │
│  Salida: List[RespuestaEntrevista]                                │
└──────────────────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────────┐
│                   RECÁLCULO FINAL                                 │
│  Entrada: ResultadoFase1 + respuestas_entrevista                  │
│  Salida: ResultadoEvaluacion(puntuacion_final, ...)               │
└──────────────────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────────┐
│                   PERSISTENCIA                                    │
│  - Guardar en memoria_usuario/{user_id}.json                      │
│  - Actualizar índice vectorial                                    │
└──────────────────────────────────────────────────────────────────┘
         │
         ▼
      FIN: ResultadoEvaluacion mostrado al usuario
```

---

## 2. Entrada de Datos

### 2.1 CV desde PDF

```python
# Flujo: archivo PDF → bytes → texto plano
from backend.infraestructura import extraer_texto_de_pdf

# Usuario sube archivo
pdf_bytes = archivo_subido.read()  # bytes

# Extracción de texto
texto_cv = extraer_texto_de_pdf(pdf_bytes)
# Usa pypdf para extraer texto de cada página

# Resultado: string con todo el contenido del CV
```

**Transformación**:
```
Archivo PDF (binario)
    ↓ pypdf.PdfReader()
Texto plano (str)
```

### 2.2 CV desde Texto

```python
# El usuario pega directamente el texto
texto_cv = st.text_area("Pega tu CV aquí")
# Ya es texto plano, no hay transformación
```

### 2.3 Oferta desde URL

```python
from backend.infraestructura import extraer_oferta_web

# Usuario proporciona URL
url = "https://empresa.com/oferta/123"

# Scraping (dos niveles)
texto_oferta = extraer_oferta_web(url)

# Nivel 1: requests + BeautifulSoup (rápido)
# Si falla o detecta JS...
# Nivel 2: Playwright headless (navegador completo)
```

**Transformación**:
```
URL
    ↓ requests.get()
HTML crudo
    ↓ BeautifulSoup / Playwright
Texto limpio (sin tags, scripts, nav)
```

---

## 3. Fase 1: Extracción de Requisitos

### 3.1 Entrada y Salida

```python
# Entrada
texto_oferta: str = """
Requisitos obligatorios:
- 5 años de experiencia en Python
- Conocimientos de Docker

Requisitos deseables:
- Experiencia con LangChain
"""

# Salida
requisitos: List[dict] = [
    {"description": "5 años de experiencia en Python", "type": "obligatory"},
    {"description": "Conocimientos de Docker", "type": "obligatory"},
    {"description": "Experiencia con LangChain", "type": "optional"}
]
```

### 3.2 Proceso Interno

```python
# 1. Construir prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", PROMPT_EXTRACCION_REQUISITOS),
    ("human", "{job_offer}")
])

# 2. Ejecutar con Structured Output
llm_estructurado = llm.with_structured_output(RespuestaExtraccionRequisitos)
resultado = llm_estructurado.invoke({"job_offer": texto_oferta})

# 3. resultado es un objeto Pydantic validado
# tipo: RespuestaExtraccionRequisitos
# con atributo: requirements: List[RequisitoExtraido]

# 4. Convertir a lista de diccionarios
requisitos = [
    {"description": req.description, "type": req.type}
    for req in resultado.requirements
]
```

**Transformación**:
```
texto_oferta (str)
    ↓ LLM + Structured Output
RespuestaExtraccionRequisitos (Pydantic)
    ↓ Conversión
List[dict] con requisitos
```

---

## 4. Fase 1: Indexación Semántica (Opcional)

### 4.1 Entrada y Salida

```python
# Entrada
texto_cv: str = "..."
requisitos: List[dict] = [...]

# Salida
evidencia_semantica: Dict[str, dict] = {
    "5 años de experiencia en python": {
        "text": "Desarrollador Python Senior - 2020-Presente...",
        "semantic_score": 0.87,
        "all_evidence": [...]
    }
}
```

### 4.2 Proceso Interno

```python
# 1. Dividir CV en chunks
chunks = comparador_semantico._dividir_cv_en_chunks(texto_cv)
# Chunks de ~500 caracteres, con solapamiento

# 2. Generar embeddings y crear índice
vectorstore = FAISS.from_texts(chunks, embeddings)

# 3. Por cada requisito, buscar chunks relevantes
for req in requisitos:
    resultados = vectorstore.similarity_search_with_score(
        req["description"], 
        k=2
    )
    # Guardar mejor coincidencia
```

**Transformación**:
```
texto_cv (str)
    ↓ Chunking
List[str] chunks
    ↓ Embeddings API
List[vector] embeddings (512 dims cada uno)
    ↓ FAISS.from_texts()
Índice FAISS en memoria
    ↓ similarity_search por requisito
Dict[requisito, evidencia]
```

---

## 5. Fase 1: Matching CV-Requisitos

### 5.1 Entrada y Salida

```python
# Entrada
texto_cv: str = "..."
requisitos: List[dict] = [...]
evidencia_semantica: Dict[str, dict] = {...}  # opcional

# Salida
resultado_matching: dict = {
    "matches": [
        {
            "requirement_description": "5 años de experiencia en Python",
            "fulfilled": True,
            "found_in_cv": True,
            "evidence": "CV menciona: Python 2020-Presente (6 años)",
            "confidence": "high",
            "reasoning": "2026 - 2020 = 6 años > 5 requeridos",
            "semantic_score": 0.87
        },
        ...
    ],
    "analysis_summary": "El candidato cumple 2/3 requisitos..."
}
```

### 5.2 Proceso Interno

```python
# 1. Construir lista de requisitos con pistas semánticas
texto_requisitos = ""
for req in requisitos:
    linea = f"- [{req['type'].upper()}] {req['description']}"
    if evidencia_semantica.get(req['description'].lower()):
        ev = evidencia_semantica[req['description'].lower()]
        linea += f"\n  [PISTA: \"{ev['text'][:100]}...\"]"
    texto_requisitos += linea + "\n"

# 2. Inyectar contexto temporal obligatorio
contexto = obtener_contexto_prompt()  # "FECHA: 2 enero 2026..."

# 3. Construir prompt completo
prompt = ChatPromptTemplate.from_messages([
    ("system", PROMPT_MATCHING_CV),
    ("human", f"{contexto}\n\nCV:\n{cv}\n\nRequisitos:\n{texto_requisitos}")
])

# 4. Ejecutar con Structured Output
llm_matching = llm.with_structured_output(RespuestaMatchingCV)
resultado = llm_matching.invoke(...)
```

**Transformación**:
```
cv + requisitos + evidencia_semantica
    ↓ Construcción de prompt con contexto temporal
Prompt completo (str)
    ↓ LLM + Structured Output
RespuestaMatchingCV (Pydantic)
    ↓ Extracción
Dict con matches y summary
```

---

## 6. Fase 1: Cálculo de Puntuación

### 6.1 Entrada y Salida

```python
# Entrada
coincidencias: List[dict] = [...]  # Del paso anterior
requisitos: List[dict] = [...]

# Salida
resultado_fase1: ResultadoFase1 = ResultadoFase1(
    puntuacion=66.67,  # 2/3 cumplidos
    descartado=False,
    requisitos_cumplidos=[Requisito(...), Requisito(...)],
    requisitos_no_cumplidos=[Requisito(...)],
    requisitos_faltantes=["Experiencia con LangChain"],
    resumen_analisis="El candidato cumple 2 de 3 requisitos..."
)
```

### 6.2 Proceso Interno

```python
# 1. Procesar coincidencias
req_cumplidos, req_no_cumplidos, req_faltantes, procesados = \
    procesar_coincidencias(coincidencias, requisitos, evidencia_semantica)

# 2. Verificar requisitos obligatorios no cumplidos
tiene_obligatorio_no_cumplido = any(
    req.tipo == TipoRequisito.OBLIGATORIO
    for req in req_no_cumplidos
)

# 3. Calcular puntuación
if tiene_obligatorio_no_cumplido:
    puntuacion = 0.0  # Descartado
else:
    puntuacion = (len(req_cumplidos) / total_requisitos) * 100

# 4. Construir resultado
resultado_fase1 = ResultadoFase1(
    puntuacion=puntuacion,
    descartado=tiene_obligatorio_no_cumplido,
    requisitos_cumplidos=req_cumplidos,
    ...
)
```

**Transformación**:
```
List[dict] coincidencias
    ↓ procesar_coincidencias()
(cumplidos, no_cumplidos, faltantes)
    ↓ calcular_puntuacion()
float puntuacion
    ↓ Construcción
ResultadoFase1 (Pydantic)
```

---

## 7. Fase 2: Entrevista Conversacional

### 7.1 Inicialización

```python
# Entrada
nombre_candidato: str = "Carlos"
resultado_fase1: ResultadoFase1 = ...
contexto_cv: str = "..."

# Proceso
entrevistador.inicializar_entrevista(
    nombre_candidato=nombre_candidato,
    resultado_fase1=resultado_fase1,
    contexto_cv=contexto_cv
)

# Estado interno del entrevistador
self._requisitos_pendientes = [
    {"description": "Experiencia con LangChain", "type": "optional", ...}
]
```

### 7.2 Generación de Preguntas (Streaming)

```python
# Por cada requisito pendiente
for token in entrevistador.transmitir_pregunta(indice=0):
    yield token  # Token por token al frontend

# Ejemplo de salida progresiva:
# "¿" → "Podrías" → " contarme" → " sobre" → " tu" → ...
```

**Transformación**:
```
requisito_pendiente + contexto_cv + historial
    ↓ LLM streaming
Generator[str] tokens
    ↓ Acumulación
str pregunta_completa
```

### 7.3 Evaluación de Respuestas

```python
# Entrada
respuesta_candidato: str = "Sí, he usado LangChain en 2 proyectos..."

# Evaluación
evaluacion = entrevistador.evaluar_respuesta(
    descripcion_requisito="Experiencia con LangChain",
    tipo_requisito=TipoRequisito.DESEABLE,
    contexto_cv=contexto_cv,
    respuesta_candidato=respuesta_candidato
)

# Salida
evaluacion: dict = {
    "fulfilled": True,
    "evidence": "Menciona 2 proyectos con LangChain",
    "confidence": "high"
}
```

---

## 8. Recálculo Final

### 8.1 Entrada y Salida

```python
# Entrada
resultado_fase1: ResultadoFase1 = ...
respuestas_entrevista: List[RespuestaEntrevista] = [...]

# Salida
resultado_evaluacion: ResultadoEvaluacion = ResultadoEvaluacion(
    resultado_fase1=resultado_fase1,
    fase2_completada=True,
    respuestas_entrevista=respuestas_entrevista,
    puntuacion_final=100.0,  # Ahora todos cumplidos
    requisitos_finales_cumplidos=[...],
    requisitos_finales_no_cumplidos=[],
    descartado_final=False,
    resumen_evaluacion="Candidato aprobado..."
)
```

### 8.2 Proceso Interno

```python
# 1. Evaluar cada respuesta de la entrevista
cumplidos_entrevista = []
for resp in respuestas_entrevista:
    evaluacion = entrevistador.evaluar_respuesta(...)
    if evaluacion["fulfilled"]:
        cumplidos_entrevista.append(...)

# 2. Combinar con resultados de Fase 1
todos_cumplidos = resultado_fase1.requisitos_cumplidos + cumplidos_entrevista

# 3. Recalcular puntuación
puntuacion_final = calcular_puntuacion(
    total_requisitos,
    len(todos_cumplidos),
    tiene_obligatorio_no_cumplido
)
```

---

## 9. Persistencia

### 9.1 Guardar Evaluación

```python
# Crear evaluación enriquecida para RAG
enriquecida = crear_evaluacion_enriquecida(
    id_usuario="carlos",
    texto_oferta=oferta,
    texto_cv=cv,
    resultado_fase1=resultado_fase1,
    fase2_completada=True,
    resultado_evaluacion=resultado_evaluacion
)

# Guardar en JSON
memoria = MemoriaUsuario()
memoria.guardar_evaluacion(enriquecida)
# Escribe en: data/memoria_usuario/carlos.json
```

### 9.2 Actualizar Índice Vectorial

```python
# Si el usuario tiene historial activo
almacen = AlmacenVectorialHistorial(
    id_usuario="carlos",
    proveedor_embeddings="openai"
)

# Añadir al índice existente
almacen.agregar_evaluacion(
    texto_busqueda=enriquecida.searchable_text,
    metadata={...}
)
# Actualiza: data/vectores/carlos/index.faiss
```

---

## 10. Tipos de Datos en Cada Etapa

| Etapa | Tipo de Entrada | Tipo de Salida |
|-------|-----------------|----------------|
| Entrada CV | `bytes` (PDF) / `str` | `str` texto plano |
| Entrada Oferta | `str` (URL/texto) | `str` texto plano |
| Extracción | `str` oferta | `List[dict]` requisitos |
| Indexación | `str` cv | `Dict[str, dict]` evidencia |
| Matching | `str` cv + requisitos | `RespuestaMatchingCV` |
| Puntuación | matches | `ResultadoFase1` |
| Entrevista | requisitos_faltantes | `List[RespuestaEntrevista]` |
| Recálculo | Fase1 + Entrevista | `ResultadoEvaluacion` |
| Persistencia | `ResultadoEvaluacion` | JSON + FAISS |

---

## 11. Modelos Pydantic en el Flujo

```
RespuestaExtraccionRequisitos
    └── List[RequisitoExtraido]
            ├── description: str
            └── type: Literal["obligatory", "optional"]

RespuestaMatchingCV
    ├── matches: List[ResultadoMatching]
    │       ├── requirement_description: str
    │       ├── fulfilled: bool
    │       ├── found_in_cv: bool
    │       ├── evidence: Optional[str]
    │       ├── confidence: Literal["high", "medium", "low"]
    │       └── reasoning: str
    └── analysis_summary: str

ResultadoFase1
    ├── puntuacion: float
    ├── descartado: bool
    ├── requisitos_cumplidos: List[Requisito]
    ├── requisitos_no_cumplidos: List[Requisito]
    ├── requisitos_faltantes: List[str]
    └── resumen_analisis: str

ResultadoEvaluacion
    ├── resultado_fase1: ResultadoFase1
    ├── fase2_completada: bool
    ├── respuestas_entrevista: List[RespuestaEntrevista]
    ├── puntuacion_final: float
    ├── requisitos_finales_cumplidos: List[Requisito]
    ├── requisitos_finales_no_cumplidos: List[Requisito]
    ├── descartado_final: bool
    └── resumen_evaluacion: str
```

---

## Próximo Documento

Continúa con [06_TECNOLOGIAS_UTILIZADAS.md](./06_TECNOLOGIAS_UTILIZADAS.md) para entender en detalle cada tecnología.

