# PROCESO DE VALIDACION DE REQUISITOS: EJEMPLOS REALES

Documentacion con trazabilidad paso a paso del proceso de validacion de requisitos en diferentes configuraciones.


## DATOS DE EJEMPLO

Para todos los ejemplos utilizaremos:

OFERTA DE EMPLEO: Desarrollador Python Backend Senior
- Requisito 1 (obligatorio): Experiencia minima de 3 años en desarrollo con Python
- Requisito 2 (obligatorio): Conocimientos solidos en frameworks web (Django o Flask)
- Requisito 3 (obligatorio): Experiencia trabajando con bases de datos relacionales (PostgreSQL o MySQL)
- Requisito 4 (obligatorio): Conocimientos de Git y control de versiones
- Requisito 5 (obligatorio): Experiencia en desarrollo de APIs REST
- Requisito 6 (opcional): Certificacion en AWS
- Requisito 7 (opcional): Experiencia con Docker y contenedores
- Requisito 8 (opcional): Conocimientos en Kubernetes

CV DE CANDIDATO: Carlos Rodriguez (Perfil DBA, no Python Developer)
- Formacion: Master en Administracion de Bases de Datos
- Experiencia: Senior Database Administrator (Oracle, SQL Server)
- Habilidades: Oracle RAC, Azure SQL, Python (scripting), PowerShell, Bash
- Certificaciones: AWS Certified Database, Oracle Certified Professional


## EJEMPLO 1: EVALUACION CON EMBEDDINGS (Sin LangGraph)

PASO 1: EXTRACCION DE REQUISITOS

El LLM recibe la oferta y extrae:
```
Input: Texto completo de la oferta
Output (via Structured Output):
{
  "requirements": [
    {"description": "Experiencia minima de 3 años en desarrollo con Python", "type": "obligatory"},
    {"description": "Conocimientos solidos en frameworks web (Django o Flask)", "type": "obligatory"},
    {"description": "Experiencia trabajando con bases de datos relacionales (PostgreSQL o MySQL)", "type": "obligatory"},
    {"description": "Conocimientos de Git y control de versiones", "type": "obligatory"},
    {"description": "Experiencia en desarrollo de APIs REST", "type": "obligatory"},
    {"description": "Certificacion en AWS", "type": "optional"},
    {"description": "Experiencia con Docker y contenedores", "type": "optional"},
    {"description": "Conocimientos en Kubernetes", "type": "optional"}
  ]
}
```

PASO 2: DIVISION DEL CV EN CHUNKS

El CV se divide en fragmentos semanticos:

Chunk 1 (DATOS + FORMACION):
"CURRICULUM VITAE DATOS PERSONALES Nombre: Carlos Rodriguez Fernandez... 
FORMACION ACADEMICA Master en Administracion de Bases de Datos (2018-2019)
Oracle Certified Professional DBA (2020) AWS Certified Database - Specialty (2023)"

Chunk 2 (EXPERIENCIA):
"EXPERIENCIA PROFESIONAL Senior Database Administrator Multinacional Financiera S.A.
Marzo 2021 - Actualidad Administracion de clusters Oracle RAC 19c
Implementacion y gestion de Oracle Dataguard Migracion de bases de datos a Azure SQL"

Chunk 3 (HABILIDADES):
"HABILIDADES TECNICAS Oracle: RAC 12c/19c, Dataguard, Grid Infrastructure, RMAN, ASM
Cloud: Azure SQL Database, Google Cloud SQL Sistemas: Linux Red Hat, Windows Server
Scripting: SQL, PL/SQL, Python, PowerShell, Bash"

PASO 3: BUSQUEDA DE EVIDENCIA SEMANTICA POR REQUISITO

Requisito: "Experiencia minima de 3 años en desarrollo con Python"
Busqueda vectorial en FAISS:
- Chunk 3 recuperado (score: 0.41): "Scripting: SQL, PL/SQL, Python, PowerShell, Bash"
- Score >= 0.2, se incluye como evidencia semantica

Requisito: "Conocimientos solidos en frameworks web (Django o Flask)"
Busqueda vectorial:
- Chunk 3 recuperado (score: 0.18): No supera umbral 0.2
- Sin evidencia semantica para este requisito

Requisito: "Experiencia trabajando con bases de datos relacionales"
Busqueda vectorial:
- Chunk 2 recuperado (score: 0.78): "Administracion de clusters Oracle RAC... bases de datos a Azure SQL"
- Alta similitud, evidencia incluida

Requisito: "Conocimientos de Git y control de versiones"
Busqueda vectorial:
- Ningun chunk supera umbral 0.2
- Sin evidencia semantica

Requisito: "Experiencia en desarrollo de APIs REST"
Busqueda vectorial:
- Score mas alto: 0.15
- Sin evidencia semantica

Requisito: "Certificacion en AWS"
Busqueda vectorial:
- Chunk 1 recuperado (score: 0.85): "AWS Certified Database - Specialty (2023)"
- Alta similitud

Mapa de evidencia semantica generado:
```
{
  "experiencia minima de 3 años en desarrollo con python": {
    "text": "Scripting: SQL, PL/SQL, Python, PowerShell, Bash",
    "semantic_score": 0.41
  },
  "experiencia trabajando con bases de datos relacionales": {
    "text": "Administracion de clusters Oracle RAC... Azure SQL",
    "semantic_score": 0.78
  },
  "certificacion en aws": {
    "text": "AWS Certified Database - Specialty (2023)",
    "semantic_score": 0.85
  }
}
```

PASO 4: CONSTRUCCION DEL PROMPT PARA MATCHING

Se construye la lista de requisitos con pistas semanticas (solo si score > 0.4):

```
CONTEXTO TEMPORAL: FECHA ACTUAL: 5 de enero de 2026 (año 2026)

CV del candidato:
[CV COMPLETO]

Requisitos a evaluar:
- [OBLIGATORY] Experiencia minima de 3 años en desarrollo con Python
  [PISTA SEMANTICA - Score: 0.41]: "Scripting: SQL, PL/SQL, Python, PowerShell, Bash..."
- [OBLIGATORY] Conocimientos solidos en frameworks web (Django o Flask)
- [OBLIGATORY] Experiencia trabajando con bases de datos relacionales (PostgreSQL o MySQL)
  [PISTA SEMANTICA - Score: 0.78]: "Administracion de clusters Oracle RAC... Azure SQL..."
- [OBLIGATORY] Conocimientos de Git y control de versiones
- [OBLIGATORY] Experiencia en desarrollo de APIs REST
- [OPTIONAL] Certificacion en AWS
  [PISTA SEMANTICA - Score: 0.85]: "AWS Certified Database - Specialty (2023)..."
- [OPTIONAL] Experiencia con Docker y contenedores
- [OPTIONAL] Conocimientos en Kubernetes
```

PASO 5: EVALUACION LLM

El LLM evalua cada requisito con el CV completo y las pistas:

```json
{
  "matches": [
    {
      "requirement_description": "Experiencia minima de 3 años en desarrollo con Python",
      "fulfilled": false,
      "found_in_cv": true,
      "evidence": "El CV menciona Python en la seccion de scripting junto con Bash y PowerShell. Sin embargo, el contexto indica uso para scripts de administracion de sistemas, no desarrollo de software. No hay proyectos de desarrollo Python ni frameworks asociados.",
      "confidence": "high",
      "reasoning": "El candidato conoce Python pero para scripting de DBA, no para desarrollo backend."
    },
    {
      "requirement_description": "Conocimientos solidos en frameworks web (Django o Flask)",
      "fulfilled": false,
      "found_in_cv": false,
      "evidence": "No se encontro mencion de Django, Flask ni ningun framework web en el CV. El candidato tiene perfil de administrador de bases de datos, no desarrollador web.",
      "confidence": "high",
      "reasoning": "Sin evidencia de frameworks web."
    },
    {
      "requirement_description": "Experiencia trabajando con bases de datos relacionales",
      "fulfilled": true,
      "found_in_cv": true,
      "evidence": "Experiencia extensiva con Oracle RAC 12c/19c, SQL Server 2016/2017/2019, Azure SQL Database. Administracion de bases de datos desde enero 2019 hasta la actualidad (7 años).",
      "confidence": "high",
      "reasoning": "Amplia experiencia en multiples RDBMS incluyendo Oracle y SQL Server, que son relacionales aunque no PostgreSQL/MySQL especificos."
    },
    {
      "requirement_description": "Conocimientos de Git y control de versiones",
      "fulfilled": false,
      "found_in_cv": false,
      "evidence": "No hay mencion de Git, GitHub, GitLab ni sistemas de control de versiones en el CV.",
      "confidence": "high",
      "reasoning": "Sin evidencia de control de versiones."
    },
    {
      "requirement_description": "Experiencia en desarrollo de APIs REST",
      "fulfilled": false,
      "found_in_cv": false,
      "evidence": "El CV no menciona desarrollo de APIs, REST, endpoints ni arquitecturas de servicios web.",
      "confidence": "high",
      "reasoning": "Sin evidencia de desarrollo de APIs."
    },
    {
      "requirement_description": "Certificacion en AWS",
      "fulfilled": true,
      "found_in_cv": true,
      "evidence": "AWS Certified Database - Specialty (2023)",
      "confidence": "high",
      "reasoning": "Certificacion AWS especifica mencionada, aunque es de base de datos y no general."
    },
    {
      "requirement_description": "Experiencia con Docker y contenedores",
      "fulfilled": false,
      "found_in_cv": false,
      "evidence": "No hay mencion de Docker, contenedores ni tecnologias de containerizacion.",
      "confidence": "high",
      "reasoning": "Sin evidencia de Docker."
    },
    {
      "requirement_description": "Conocimientos en Kubernetes",
      "fulfilled": false,
      "found_in_cv": false,
      "evidence": "No hay mencion de Kubernetes, K8s ni orquestacion de contenedores.",
      "confidence": "high",
      "reasoning": "Sin evidencia de Kubernetes."
    }
  ],
  "analysis_summary": "Candidato con perfil DBA senior, no desarrollador Python. Cumple requisitos de bases de datos y tiene certificacion AWS, pero carece de experiencia en desarrollo backend, frameworks web, APIs REST y herramientas de desarrollo como Git."
}
```

PASO 6: CALCULO DE PUNTUACION

- Total requisitos: 8
- Requisitos cumplidos: 2 (bases de datos, certificacion AWS)
- Requisitos obligatorios no cumplidos: 4 (Python dev, Django/Flask, Git, APIs REST)
- Tiene obligatorio no cumplido: SI

Puntuacion final: 0% (candidato descartado)

RESULTADO FINAL:
```
ResultadoFase1(
  puntuacion=0.0,
  descartado=True,
  requisitos_cumplidos=[BD_relacionales, AWS_cert],
  requisitos_no_cumplidos=[Python_dev, Django_Flask, Git, APIs_REST, Docker, Kubernetes],
  resumen_analisis="Candidato con perfil DBA senior..."
)
```


## EJEMPLO 2: EVALUACION SIN EMBEDDINGS (Sin LangGraph)

PASOS 1-2: Identicos al Ejemplo 1 (extraccion de requisitos)

PASO 3: OMITIDO (Sin busqueda semantica)

evidencia_semantica = {} (diccionario vacio)

PASO 4: CONSTRUCCION DEL PROMPT PARA MATCHING

Sin pistas semanticas:
```
CONTEXTO TEMPORAL: FECHA ACTUAL: 5 de enero de 2026 (año 2026)

CV del candidato:
[CV COMPLETO]

Requisitos a evaluar:
- [OBLIGATORY] Experiencia minima de 3 años en desarrollo con Python
- [OBLIGATORY] Conocimientos solidos en frameworks web (Django o Flask)
- [OBLIGATORY] Experiencia trabajando con bases de datos relacionales (PostgreSQL o MySQL)
- [OBLIGATORY] Conocimientos de Git y control de versiones
- [OBLIGATORY] Experiencia en desarrollo de APIs REST
- [OPTIONAL] Certificacion en AWS
- [OPTIONAL] Experiencia con Docker y contenedores
- [OPTIONAL] Conocimientos en Kubernetes
```

El LLM debe analizar el CV completo sin guia previa.

PASO 5: EVALUACION LLM

El resultado deberia ser muy similar al Ejemplo 1, pero:
- Sin el score semantico en cada requisito
- Posible mayor variabilidad entre ejecuciones
- El LLM tiene que "descubrir" la evidencia sin pistas

Diferencias potenciales:
- Para Python, sin la pista el LLM podria no notar la mencion en Scripting
- La evaluacion depende mas de la atencion del LLM

PASO 6: CALCULO DE PUNTUACION

Identico al Ejemplo 1.


## EJEMPLO 3: EVALUACION CON LANGGRAPH + EMBEDDINGS

FLUJO POR NODOS:

NODO 1: extraer_requisitos
```
Input: oferta_trabajo
Output: {
  "requisitos": [...8 requisitos...],
  "mensajes": ["[OK] Extraidos 8 requisitos"]
}
Estado actualizado: requisitos = [...]
```

NODO 2: embeber_cv
```
Input: cv, requisitos
Proceso:
  - Dividir CV en 3 chunks
  - Indexar en FAISS
  - Buscar evidencia para cada requisito
Output: {
  "evidencia_semantica": {
    "experiencia minima de 3 años en desarrollo con python": {...},
    "experiencia trabajando con bases de datos relacionales": {...},
    "certificacion en aws": {...}
  },
  "mensajes": ["[OK] Evidencia semantica para 3 requisitos"]
}
Estado actualizado: evidencia_semantica = {...}
```

NODO 3: matching_semantico
```
Input: cv, requisitos, evidencia_semantica
Proceso:
  - Construir lista de requisitos con pistas (si score > 0.4)
  - Invocar LLM con PROMPT_MATCHING_CV
  - Parsear respuesta estructurada
Output: {
  "coincidencias": [...8 matches...],
  "resumen_analisis": "Candidato DBA senior...",
  "mensajes": ["[OK] Matching completado: 2/8 cumplidos"]
}
Estado actualizado: coincidencias = [...], resumen_analisis = "..."
```

NODO 4: calcular_puntuacion
```
Input: requisitos, coincidencias, evidencia_semantica
Proceso:
  - Procesar coincidencias
  - Contar obligatorios no cumplidos
  - Calcular puntuacion
Output: {
  "puntuacion": 0.0,
  "descartado": True,
  "requisitos_cumplidos": [...],
  "requisitos_no_cumplidos": [...],
  "mensajes": ["[END] Resultado: DESCARTADO"]
}
```

MENSAJES ACUMULADOS (via Annotated[List[str], add]):
```
[
  "[OK] Extraidos 8 requisitos",
  "[OK] Evidencia semantica para 3 requisitos",
  "[OK] Matching completado: 2/8 cumplidos",
  "[END] Resultado: DESCARTADO"
]
```

TRAZABILIDAD EN LANGSMITH:

Si LangSmith esta configurado, cada nodo aparece como span separado con:
- Duracion
- Inputs
- Outputs
- Errores si los hay


## EJEMPLO 4: REQUISITO QUE SE CUMPLE VS QUE NO SE CUMPLE

REQUISITO QUE SE CUMPLE: "Certificacion en AWS"

1. Busqueda semantica:
   - Chunk encontrado: "AWS Certified Database - Specialty (2023)"
   - Score: 0.85 (alta similitud)

2. Pista enviada al LLM:
   ```
   - [OPTIONAL] Certificacion en AWS
     [PISTA SEMANTICA - Score: 0.85]: "AWS Certified Database - Specialty (2023)..."
   ```

3. Evaluacion LLM:
   ```json
   {
     "requirement_description": "Certificacion en AWS",
     "fulfilled": true,
     "found_in_cv": true,
     "evidence": "AWS Certified Database - Specialty (2023)",
     "confidence": "high",
     "reasoning": "Certificacion AWS especifica mencionada."
   }
   ```

4. Procesamiento:
   - Se añade a requisitos_cumplidos
   - semantic_score = 0.85


REQUISITO QUE NO SE CUMPLE: "Conocimientos de Git y control de versiones"

1. Busqueda semantica:
   - Ningun chunk supera umbral 0.2
   - Sin pista semantica

2. Enviado al LLM sin pista:
   ```
   - [OBLIGATORY] Conocimientos de Git y control de versiones
   ```

3. Evaluacion LLM:
   ```json
   {
     "requirement_description": "Conocimientos de Git y control de versiones",
     "fulfilled": false,
     "found_in_cv": false,
     "evidence": "No hay mencion de Git, GitHub, GitLab ni sistemas de control de versiones en el CV. Las herramientas mencionadas son Oracle Enterprise Manager, Azure Portal y Terraform para infraestructura.",
     "confidence": "high",
     "reasoning": "Sin evidencia de control de versiones."
   }
   ```

4. Procesamiento:
   - Se añade a requisitos_no_cumplidos
   - Se añade descripcion a requisitos_faltantes
   - semantic_score = None (sin embedding disponible)


## UMBRALES Y CRITERIOS DE DECISION

UMBRAL SEMANTICO (comparador_semantico.py):
- Umbral para incluir evidencia: 0.2 (bajo para capturar contexto implicito)
- El score se calcula: similitud = 1 / (1 + distancia_coseno)
- Un score de 0.2 significa baja similitud pero posible relevancia

UMBRAL PARA PISTAS AL LLM (analizador.py):
- Umbral para incluir pista en prompt: 0.4
- Solo evidencia con score > 0.4 se muestra al LLM
- Evita confundir al LLM con fragmentos irrelevantes

CRITERIO DE CUMPLIMIENTO:
- Decidido exclusivamente por el LLM
- fulfilled = true/false
- Los embeddings son sugerencias, nunca determinantes

CRITERIO DE DESCARTE:
- Un solo requisito OBLIGATORY con fulfilled=false descarta al candidato
- Puntuacion = 0% si hay obligatorio no cumplido
- Puntuacion = (cumplidos/total) * 100 si todos obligatorios cumplen


## EVIDENCIAS PARA REQUISITOS NO CUMPLIDOS

Cuando un requisito NO se cumple, el sistema ahora proporciona:

1. Si el LLM proporciono evidence explicando la ausencia:
   ```
   evidence: "El CV menciona Python en la seccion de scripting junto con Bash y PowerShell. 
   Sin embargo, el contexto indica uso para scripts de administracion de sistemas, 
   no desarrollo de software."
   ```

2. Si hay evidencia semantica cercana pero insuficiente:
   ```
   evidence: "[Fragmento mas cercano encontrado (score: 0.35): 'Scripting: SQL, PL/SQL, 
   Python, PowerShell, Bash...'] - Contenido insuficiente para cumplir el requisito."
   ```

3. Si no hay evidencia de ningun tipo:
   ```
   evidence: "No se encontro informacion relacionada en el CV para evaluar este requisito."
   ```

Esto permite auditar por que un requisito no fue validado.

