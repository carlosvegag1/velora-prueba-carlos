# Documentación: `backend/recursos/prompts.py`

## Información General

| Atributo | Valor |
|----------|-------|
| **Ruta** | `/backend/recursos/prompts.py` |
| **Tipo** | Configuración / Recursos |
| **Líneas** | ~400 |
| **Propósito** | Definir TODOS los prompts del sistema |

---

## Propósito

Este archivo es el **cerebro interpretativo** del sistema. Contiene todas las instrucciones que se envían a los LLMs.

**Filosofía**: Los prompts son configuración, no código. Separarlos permite:
- Iterar prompts sin cambiar lógica
- Evaluar diferentes versiones
- Documentar claramente las instrucciones

---

## Constantes Globales

```python
ANIO_REFERENCIA_SISTEMA = 2026
"""
Año de referencia para cálculos temporales.

CRÍTICO: Este valor DEBE coincidir con el definido en
backend/utilidades/contexto_temporal.py
"""
```

**¿Por qué 2026?**

El sistema debe evaluar candidatos como si estuviéramos en enero de 2026. Esto es crucial para calcular años de experiencia correctamente.

---

## PROMPT_EXTRACCION_REQUISITOS

### Propósito
Extraer requisitos de una oferta de trabajo de forma estructurada.

### Código Completo

```python
PROMPT_EXTRACCION_REQUISITOS = """
Eres un experto en análisis de ofertas de trabajo. Tu tarea es extraer
TODOS los requisitos de la oferta proporcionada.

## REGLAS DE EXTRACCIÓN:

### Clasificación de Requisitos:
- **obligatory**: Requisitos OBLIGATORIOS (palabras clave: "requerido", "imprescindible", 
  "obligatorio", "necesario", "must have", "required")
- **optional**: Requisitos DESEABLES (palabras clave: "deseable", "valorable", 
  "preferible", "nice to have", "plus")

### Reglas de Agrupación/Separación:

1. **AGRUPAR cuando**:
   - Son variantes del mismo concepto: "Python/Django" → un requisito
   - Son alternativas explícitas: "AWS o GCP" → un requisito
   - Son complementarios inseparables: "diseño e implementación de APIs" → un requisito

2. **SEPARAR cuando**:
   - Son habilidades distintas: "Python y Docker" → dos requisitos
   - Tienen contextos diferentes: "experiencia en backend y conocimientos de frontend" → dos
   - Se evalúan independientemente

### Reglas de Interpretación de Experiencia:

- "X años de experiencia" → requisito concreto
- "Experiencia en X" (sin años) → requisito cualitativo
- "Senior/Lead/Principal" → implica experiencia significativa

## GARANTÍA DE DETERMINISMO:

Para la MISMA oferta de trabajo, SIEMPRE debes producir EXACTAMENTE los mismos 
requisitos. No añadas variabilidad ni interpretaciones alternativas.

## FORMATO DE RESPUESTA:

Devuelve una lista de requisitos, cada uno con:
- description: Texto del requisito (máximo 100 caracteres)
- type: "obligatory" u "optional"
"""
```

### Análisis del Prompt

**Sección 1: Rol**
```
Eres un experto en análisis de ofertas de trabajo.
```
Define el rol del LLM. Esto mejora la calidad de las respuestas.

**Sección 2: Clasificación**
```
obligatory vs optional
```
Define las dos categorías y las palabras clave asociadas.

**Sección 3: Agrupación/Separación**
```
AGRUPAR cuando: variantes, alternativas, complementarios
SEPARAR cuando: habilidades distintas, contextos diferentes
```
Esto es CRÍTICO. Sin estas reglas, el LLM podría:
- Convertir "Python, Django y FastAPI" en un requisito
- O convertir "Python/Django" en dos requisitos

**Sección 4: Determinismo**
```
Para la MISMA oferta, SIEMPRE los mismos requisitos
```
Fundamental para reproducibilidad. La Fase 1 debe ser determinista.

---

## PROMPT_MATCHING_CV

### Propósito
Evaluar si un CV cumple con una lista de requisitos.

### Código Completo (Fragmentos Clave)

```python
PROMPT_MATCHING_CV = """
Eres un evaluador experto de CVs. Tu tarea es determinar si el candidato
cumple cada requisito de la oferta de trabajo.

## CONTEXTO TEMPORAL CRÍTICO:

{contexto_temporal}

## INSTRUCCIONES DE CÁLCULO DE EXPERIENCIA:

{instrucciones_experiencia}

## REGLAS DE EVALUACIÓN:

### Criterios para fulfilled=true:
1. **Evidencia explícita**: El CV menciona directamente la habilidad/experiencia
2. **Inferencia razonable**: La experiencia descrita implica claramente la habilidad
3. **Cumplimiento cuantitativo**: Si se piden X años, el CV demuestra ≥X años

### Criterios para fulfilled=false:
1. **Sin mención**: El CV no menciona nada relacionado
2. **Insuficiente**: Experiencia menor a la requerida
3. **Incompatible**: La experiencia es en un área diferente

### Niveles de Confianza:
- **high**: Evidencia directa y clara
- **medium**: Inferencia razonable o evidencia parcial
- **low**: Suposición basada en contexto limitado

## INSTRUCCIONES ESPECIALES:

1. **Temporal**: Usa SIEMPRE el año {anio_sistema} como referencia
2. **"Presente"**: Interpreta "actualidad", "presente", "actual" como {anio_sistema}
3. **Cálculo**: años_experiencia = {anio_sistema} - año_inicio

## FORMATO DE RESPUESTA:

Para cada requisito, proporciona:
- requirement_description: Texto del requisito
- fulfilled: true/false
- found_in_cv: true/false (si se encontró algo relacionado)
- evidence: Texto del CV que respalda la decisión (si aplica)
- confidence: high/medium/low
- reasoning: Explicación del razonamiento
- semantic_score: Score semántico (si se proporciona pista)
"""
```

### Análisis del Prompt

**Sección Crítica: Contexto Temporal**
```python
{contexto_temporal}
```
Se reemplaza dinámicamente por:
```
FECHA ACTUAL DEL SISTEMA: 2 de enero de 2026
AÑO DE REFERENCIA: 2026
```

**¿Por qué es crítico?**

Sin esto:
```
CV: "Python desde 2020 hasta presente"
LLM piensa: estamos en 2024 → 4 años
Realidad: estamos en 2026 → 6 años
```

**Sección: Instrucciones de Experiencia**
```python
{instrucciones_experiencia}
```
Se reemplaza por:
```
FÓRMULA DE CÁLCULO:
- años_experiencia = 2026 - año_inicio
- "2020-Presente" = 2026 - 2020 = 6 años

EJEMPLOS:
- "Python 2018-2023" = 5 años (2023-2018)
- "Python desde 2020" = 6 años (2026-2020)
- "Python 2020-actualidad" = 6 años
```

**Sección: Niveles de Confianza**

| Nivel | Significado | Ejemplo |
|-------|-------------|---------|
| high | Evidencia directa | "5 años de Python" en CV |
| medium | Inferencia | "Django" implica Python |
| low | Suposición | "Desarrollo web" podría incluir Python |

---

## PROMPT_EVALUAR_RESPUESTA

### Propósito
Evaluar si la respuesta de un candidato en la entrevista demuestra cumplimiento.

```python
PROMPT_EVALUAR_RESPUESTA = """
Eres un evaluador objetivo de entrevistas técnicas.

## TAREA:
Determina si la respuesta del candidato demuestra cumplimiento del requisito.

## CRITERIOS DE EVALUACIÓN:

### Para fulfilled=true:
- La respuesta menciona experiencia concreta con la tecnología/habilidad
- Proporciona ejemplos específicos de proyectos o tareas
- Demuestra conocimiento técnico del tema

### Para fulfilled=false:
- La respuesta es vaga o genérica
- No menciona experiencia directa
- El conocimiento parece teórico sin práctica

### Niveles de Confianza:
- **high**: Respuesta detallada con ejemplos concretos
- **medium**: Respuesta general pero coherente
- **low**: Respuesta poco específica

## IMPORTANTE:
- Sé objetivo, no asumas información no proporcionada
- Si la respuesta es evasiva, fulfilled=false
- Evalúa SOLO lo que el candidato dice, no lo que podría saber
"""
```

### Análisis

Este prompt es más estricto que el de matching porque:
- El candidato tiene la oportunidad de explicar
- Si no proporciona detalles, es señal de no cumplimiento
- No hay "beneficio de la duda" como en el CV

---

## Prompts de Personalidad

### PROMPT_SISTEMA_AGENTE

```python
PROMPT_SISTEMA_AGENTE = """
Eres Velora, una asistente de evaluación de candidatos.

## TU PERSONALIDAD:
- Profesional pero amable
- Empática sin ser condescendiente
- Directa sin ser brusca
- Técnicamente competente

## TONO:
- Usa lenguaje formal pero accesible
- Tutea al candidato si es apropiado en el contexto
- Evita jerga innecesaria
- Sé concisa en las respuestas

## OBJETIVO:
Crear una experiencia de entrevista cómoda donde el candidato
pueda demostrar sus conocimientos sin sentirse intimidado.
"""
```

### PROMPT_SALUDO_AGENTE

```python
PROMPT_SALUDO_AGENTE = """
Saluda al candidato {nombre} para iniciar la entrevista.

Contexto:
- Hay {num_requisitos} requisitos por verificar
- Es una conversación técnica pero amigable
- El candidato ya pasó la Fase 1 y solo necesita aclarar algunos puntos

Genera un saludo breve (2-3 oraciones) que:
1. Salude por nombre
2. Explique brevemente el propósito
3. Invite a comenzar
"""
```

### PROMPT_PREGUNTA_AGENTE

```python
PROMPT_PREGUNTA_AGENTE = """
Genera una pregunta para verificar el siguiente requisito:

REQUISITO: {requisito}
TIPO: {tipo}

CONTEXTO DEL CV:
{contexto_cv}

INSTRUCCIONES:
- Haz una pregunta abierta que invite a explicar
- No seas interrogativo ni intimidante
- Si hay algo en el CV relacionado, puedes mencionarlo
- Máximo 2 oraciones

EJEMPLO:
❌ "¿Tienes experiencia con Docker?" (cerrada)
✅ "¿Podrías contarme sobre tu experiencia trabajando con contenedores?" (abierta)
"""
```

### PROMPT_CIERRE_AGENTE

```python
PROMPT_CIERRE_AGENTE = """
Cierra la entrevista con {nombre}.

RESULTADO: {resultado}

Si aprobado:
- Agradece su tiempo
- Felicita brevemente
- Menciona siguientes pasos genéricos

Si no aprobado:
- Agradece su tiempo
- Sé empático sin dar falsas esperanzas
- Anima a seguir desarrollándose

Máximo 3 oraciones.
"""
```

---

## Funciones de Acceso

```python
def obtener_prompt_extraccion() -> str:
    """Devuelve el prompt de extracción de requisitos."""
    return PROMPT_EXTRACCION_REQUISITOS

def obtener_prompt_matching() -> str:
    """Devuelve el prompt de matching CV-requisitos."""
    return PROMPT_MATCHING_CV

# ... más funciones similares
```

**¿Por qué funciones en lugar de acceso directo?**

1. **Encapsulación**: Podríamos añadir lógica (logging, versionado)
2. **Testing**: Más fácil de mockear en tests
3. **Evolución**: Podríamos cargar prompts de archivos externos

---

## Aliases en Inglés

```python
# Para compatibilidad y preferencias de equipos
PROMPT_REQUIREMENT_EXTRACTION = PROMPT_EXTRACCION_REQUISITOS
PROMPT_CV_MATCHING = PROMPT_MATCHING_CV
PROMPT_RESPONSE_EVALUATION = PROMPT_EVALUAR_RESPUESTA
PROMPT_AGENT_SYSTEM = PROMPT_SISTEMA_AGENTE
```

---

## Justificación de Diseño

### ¿Por qué un archivo separado?

| Alternativa | Problema |
|-------------|----------|
| Prompts en cada clase | Duplicación, difícil de mantener |
| Prompts en base de datos | Complejidad innecesaria |
| Prompts en archivos .txt | Perdemos Python features |
| **Archivo Python dedicado** | ✅ Centralizado, versionable, documentable |

### ¿Por qué prompts tan detallados?

**Prompt corto**:
```
Extrae los requisitos de esta oferta.
```
Resultado: Inconsistente, vago, no determinista.

**Prompt detallado**:
- Reglas claras de clasificación
- Ejemplos de agrupación/separación
- Garantía de determinismo
- Formato de salida específico

### ¿Por qué contexto temporal inyectado?

Los LLMs tienen una fecha de corte (cuando fueron entrenados). Sin indicarles la fecha actual:
- GPT-4 podría pensar que estamos en 2023
- Claude podría asumir 2024
- Los cálculos de experiencia serían incorrectos

### ¿Por qué prompts en español e inglés?

- **Prompts técnicos en inglés**: Los LLMs rinden mejor
- **Prompts de interfaz en español**: Coherencia con el usuario
- **Aliases**: Permiten elegir según preferencia

