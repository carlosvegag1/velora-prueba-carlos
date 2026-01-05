# FLUJOS DE MATCHING CV-REQUISITOS

Documentacion tecnica del proceso de evaluacion de candidatos segun las cuatro configuraciones posibles del sistema Velora.


## VISION GENERAL DEL SISTEMA

El matching CV-requisitos es el proceso central de evaluacion. Compara el contenido del curriculum vitae de un candidato contra los requisitos extraidos de una oferta de empleo.

El sistema tiene dos dimensiones de configuracion independientes:

1. EMBEDDINGS SEMANTICOS: Pre-filtrado vectorial que enriquece el contexto antes del matching
2. LANGGRAPH: Orquestacion de flujo mediante grafos de estado

Estas dimensiones generan cuatro configuraciones posibles que se detallan a continuacion.


## ARQUITECTURA DE COMPONENTES

Archivos principales involucrados:

- backend/nucleo/analisis/analizador.py: Clase AnalizadorFase1, punto de entrada
- backend/orquestacion/grafo_fase1.py: Flujo LangGraph con nodos especializados
- backend/infraestructura/llm/comparador_semantico.py: Embeddings FAISS
- backend/recursos/prompts.py: Prompts del sistema
- backend/utilidades/procesamiento.py: Funciones de puntuacion y procesamiento


## CONFIGURACION 1: SOLO EMBEDDINGS (Sin LangGraph)

Parametros: usar_matching_semantico=True, usar_langgraph=False

FLUJO DE EJECUCION

1. EXTRACCION DE REQUISITOS (analizador.py lineas 137-162)
   - El LLM recibe PROMPT_EXTRACCION_REQUISITOS
   - Extrae requisitos clasificandolos como obligatory/optional
   - Se eliminan duplicados por normalizacion de texto

2. OBTENCION DE EVIDENCIA SEMANTICA (analizador.py lineas 166-191)
   - El CV se divide en chunks semanticos (800 caracteres, 150 solapamiento)
   - Se indexa en FAISS creando vectorstore temporal
   - Para cada requisito se buscan los k=2 fragmentos mas similares
   - Se retiene evidencia con score > 0.2

3. EVALUACION CON CONTEXTO ENRIQUECIDO (analizador.py lineas 193-253)
   - Se construye lista de requisitos con pistas semanticas
   - Si score semantico > 0.4, se incluye hint al LLM:
     "[PISTA SEMANTICA - Score: 0.65]: fragmento del CV..."
   - El LLM evalua cada requisito con PROMPT_MATCHING_CV
   - Retorna fulfilled, evidence, confidence, reasoning por requisito

4. CALCULO DE PUNTUACION (procesamiento.py lineas 12-27)
   - Si cualquier requisito obligatorio no cumplido: 0%
   - En caso contrario: (cumplidos/total) * 100

QUE HACEN LOS EMBEDDINGS

Los embeddings NO deciden si un requisito se cumple. Proporcionan contexto adicional al LLM en forma de "pistas semanticas". El LLM siempre:
- Recibe el CV completo
- Evalua con comprension global
- Tiene la ultima palabra sobre cumplimiento

Los embeddings aceleran y enfocan la atencion del LLM hacia fragmentos potencialmente relevantes.


## CONFIGURACION 2: NADA ACTIVADO (Sin Embeddings, Sin LangGraph)

Parametros: usar_matching_semantico=False, usar_langgraph=False

FLUJO DE EJECUCION

1. EXTRACCION DE REQUISITOS
   - Identico a Configuracion 1

2. SIN PRE-FILTRADO SEMANTICO
   - evidencia_semantica = {} (diccionario vacio)
   - No se indexa el CV
   - No hay vectorstore FAISS

3. EVALUACION DIRECTA
   - El LLM recibe requisitos sin pistas semanticas
   - Formato: "- [OBLIGATORY] Experiencia en Python"
   - El LLM debe analizar el CV completo sin guia
   - Mayor carga cognitiva para el LLM

4. CALCULO DE PUNTUACION
   - Identico a Configuracion 1

DIFERENCIA PRACTICA

Sin embeddings, el LLM trabaja "a ciegas" sobre el CV. Esto puede causar:
- Mayor variabilidad en resultados
- Posibles omisiones de evidencia implicita
- Tiempos de procesamiento similares (la indexacion FAISS es rapida)

El LLM sigue siendo capaz de encontrar evidencia, pero sin el "foco" que proporcionan los embeddings.


## CONFIGURACION 3: SOLO LANGGRAPH (Sin Embeddings)

Parametros: usar_matching_semantico=False, usar_langgraph=True

FLUJO DE EJECUCION

LangGraph organiza el flujo en nodos secuenciales (grafo_fase1.py):

1. NODO extraer_requisitos (lineas 47-97)
   - Ejecuta extraccion via LLM
   - Actualiza estado con requisitos extraidos
   - Registra mensajes de progreso

2. NODO embeber_cv (lineas 103-149)
   - Si comparador_semantico es None: SKIP
   - Retorna evidencia_semantica = {}
   - Mensaje: "[SKIP] Embeddings deshabilitados"

3. NODO matching_semantico (lineas 155-239)
   - Sin pistas semanticas (score threshold no aplica)
   - LLM evalua requisitos contra CV completo
   - Construye lista de coincidencias

4. NODO calcular_puntuacion (lineas 245-292)
   - Procesa coincidencias
   - Determina descartado si obligatorio no cumplido
   - Genera resultado final

QUE APORTA LANGGRAPH SIN EMBEDDINGS

LangGraph proporciona:
- Estado tipado (EstadoFase1) que persiste entre nodos
- Manejo de errores por nodo sin detener el flujo
- Trazabilidad: cada nodo registra mensajes
- Capacidad de streaming via astream()
- Observabilidad integrada con LangSmith

Sin embeddings, el nodo embeber_cv simplemente propaga el estado sin modificacion.


## CONFIGURACION 4: LANGGRAPH + EMBEDDINGS

Parametros: usar_matching_semantico=True, usar_langgraph=True

FLUJO DE EJECUCION

Esta es la configuracion mas completa:

1. NODO extraer_requisitos
   - Identico a Configuracion 3

2. NODO embeber_cv (lineas 103-149)
   - Indexa CV en FAISS
   - Busca evidencia para cada requisito
   - Almacena en estado: evidencia_semantica

3. NODO matching_semantico
   - Construye requisitos CON pistas semanticas
   - Formato enriquecido si score > 0.4:
     "- [OBLIGATORY] Experiencia Python
      [PISTA SEMANTICA - Score: 0.72]: 'Desarrollo backend con Python y Django...'"
   - LLM evalua con contexto completo

4. NODO calcular_puntuacion
   - Identico a Configuracion 3

FLUJO DEL GRAFO

```
extraer_requisitos --> embeber_cv --> matching_semantico --> calcular_puntuacion --> END
```

El grafo se compila con StateGraph y se ejecuta via invoke() o astream().


## COMPARATIVA TECNICA

                          | Sin LangGraph        | Con LangGraph
--------------------------|----------------------|----------------------
Sin Embeddings            | Flujo lineal simple  | Flujo en nodos
                          | Sin trazabilidad     | Trazabilidad completa
                          | Sin streaming        | Streaming disponible
--------------------------|----------------------|----------------------
Con Embeddings            | Evidencia como hints | Evidencia en estado
                          | Evaluacion directa   | Evaluacion por nodo
                          | Sin estado tipado    | Estado tipado


## CUANDO USAR CADA CONFIGURACION

SOLO EMBEDDINGS (Configuracion 1)
- Uso: Evaluaciones rapidas sin necesidad de trazabilidad
- Ventaja: Simplicidad, menor overhead
- Desventaja: Sin streaming ni observabilidad detallada

NADA ACTIVADO (Configuracion 2)
- Uso: Proveedores sin soporte embeddings (Anthropic)
- Ventaja: Funciona con cualquier LLM
- Desventaja: Sin pre-filtrado semantico

SOLO LANGGRAPH (Configuracion 3)
- Uso: Cuando se requiere trazabilidad sin embeddings disponibles
- Ventaja: Streaming y observabilidad
- Desventaja: Sin enriquecimiento semantico

LANGGRAPH + EMBEDDINGS (Configuracion 4)
- Uso: Evaluaciones completas con maxima observabilidad
- Ventaja: Todas las capacidades activas
- Desventaja: Mayor complejidad, requiere proveedor con embeddings


## DETALLE TECNICO: QUE PASA INTERNAMENTE EN CADA PASO

PASO 1: DIVISION DEL CV EN CHUNKS (comparador_semantico.py lineas 42-74)

El CV se divide por:
1. Secciones naturales (EXPERIENCIA, FORMACION, etc.)
2. Dobles saltos de linea
3. Si no hay secciones claras: division por tamano (800 chars)

Ejemplo de chunks para el CV de Carlos Rodriguez:
- Chunk 1: "DATOS PERSONALES... FORMACION ACADEMICA..."
- Chunk 2: "EXPERIENCIA PROFESIONAL... Senior Database Administrator..."
- Chunk 3: "HABILIDADES TECNICAS... Oracle: RAC 12c/19c..."

PASO 2: INDEXACION VECTORIAL (comparador_semantico.py lineas 100-106)

Cada chunk se convierte en vector mediante el modelo de embeddings del proveedor.
Se crea un indice FAISS in-memory para busqueda de similitud.

PASO 3: BUSQUEDA DE EVIDENCIA (comparador_semantico.py lineas 110-125)

Para el requisito "Experiencia en Python":
1. Se vectoriza el requisito
2. Se buscan los k=2 chunks mas cercanos
3. Se calcula similitud: 1 / (1 + distancia_coseno)
4. Si similitud >= 0.2, se incluye como evidencia

PASO 4: EVALUACION LLM (analizador.py lineas 193-253)

El LLM recibe:
- CV completo
- Lista de requisitos (con/sin pistas semanticas)
- Contexto temporal ("FECHA ACTUAL: 5 de enero de 2026")

El LLM retorna para cada requisito:
- fulfilled: true/false
- found_in_cv: true/false
- evidence: fragmento del CV que justifica
- confidence: high/medium/low
- reasoning: explicacion breve


## NOTA SOBRE EMBEDDINGS Y DECISION FINAL

Los embeddings NUNCA determinan si un requisito se cumple.

Flujo de decision:
1. Embeddings encuentran fragmentos candidatos (pre-filtrado)
2. Se envian como "pistas" al LLM
3. El LLM analiza el CV COMPLETO
4. El LLM decide fulfilled=true/false

Si los embeddings encuentran un fragmento con score 0.9 pero el LLM determina que no hay evidencia suficiente, el requisito se marca como no cumplido.

Los embeddings son asistentes, no decisores.

