# Documentación: `backend/modelos.py`

## Información General

| Atributo | Valor |
|----------|-------|
| **Ruta** | `/backend/modelos.py` |
| **Tipo** | Módulo de definición de datos |
| **Líneas** | ~250 |
| **Dependencias** | `pydantic`, `typing`, `enum` |

---

## Propósito

Este archivo define **todos los modelos de datos** del sistema usando Pydantic. Estos modelos:

1. Validan datos automáticamente
2. Habilitan Structured Output de LLMs
3. Documentan la estructura de datos del sistema

---

## Conceptos Previos

### ¿Qué es Pydantic?

Pydantic es una librería de validación de datos:

```python
from pydantic import BaseModel

class Usuario(BaseModel):
    nombre: str
    edad: int

# Válido
u1 = Usuario(nombre="Ana", edad=30)

# Error automático
u2 = Usuario(nombre="Ana", edad="treinta")
# ValidationError: Input should be a valid integer
```

### ¿Qué es un Enum?

Un Enum (enumeración) define un conjunto fijo de valores posibles:

```python
from enum import Enum

class Color(str, Enum):
    ROJO = "red"
    VERDE = "green"
    AZUL = "blue"

# Solo puede ser ROJO, VERDE o AZUL
mi_color = Color.ROJO
```

---

## Enumeraciones

### TipoRequisito

```python
class TipoRequisito(str, Enum):
    """Clasificación de requisitos de una oferta de trabajo."""
    OBLIGATORIO = "obligatory"
    DESEABLE = "optional"
```

**¿Por qué `str, Enum`?**

Al heredar de `str` además de `Enum`, los valores pueden compararse con strings:

```python
tipo = TipoRequisito.OBLIGATORIO

# Esto funciona gracias a heredar de str
tipo == "obligatory"  # True

# Y también funciona como Enum
tipo == TipoRequisito.OBLIGATORIO  # True
```

**Uso en el sistema**:
- `OBLIGATORIO`: El candidato DEBE cumplir este requisito
- `DESEABLE`: Es preferible pero no eliminatorio

---

### NivelConfianza

```python
class NivelConfianza(str, Enum):
    """Nivel de confianza en una evaluación."""
    ALTO = "high"
    MEDIO = "medium"
    BAJO = "low"
```

**Uso en el sistema**:
- `ALTO`: Evidencia clara y directa en el CV
- `MEDIO`: Evidencia parcial o indirecta
- `BAJO`: Inferencia sin evidencia explícita

---

## Modelos de Requisitos

### Requisito (Modelo Principal)

```python
class Requisito(BaseModel):
    """
    Modelo completo de un requisito evaluado.
    
    Este modelo representa un requisito después de ser extraído
    de la oferta y evaluado contra el CV del candidato.
    """
    
    descripcion: str = Field(
        ...,
        alias="description",
        description="Descripción textual del requisito"
    )
```

**Desglose del Field**:

| Parámetro | Significado |
|-----------|-------------|
| `...` | Campo obligatorio (no tiene valor por defecto) |
| `alias="description"` | En JSON se llama "description", en Python es "descripcion" |
| `description=` | Documentación del campo |

```python
    tipo: TipoRequisito = Field(
        ...,
        alias="type",
        description="Tipo de requisito: obligatorio o deseable"
    )
```

El tipo es un Enum, solo puede ser OBLIGATORIO o DESEABLE.

```python
    cumplido: bool = Field(
        default=False,
        alias="fulfilled",
        description="Si el candidato cumple el requisito"
    )
```

**`default=False`**: Si no se proporciona valor, es False.

```python
    evidencia: Optional[str] = Field(
        None,
        alias="evidence",
        description="Texto del CV que evidencia el cumplimiento"
    )
```

**`Optional[str]`**: Puede ser un string o None.

```python
    confianza: Optional[NivelConfianza] = Field(
        None,
        alias="confidence",
        description="Nivel de confianza en la evaluación"
    )
```

**`Optional[NivelConfianza]`**: Puede ser un enum o None.

```python
    razonamiento: Optional[str] = Field(
        None,
        alias="reasoning",
        description="Explicación del proceso de evaluación"
    )
```

El razonamiento explica POR QUÉ el LLM tomó esa decisión.

```python
    puntuacion_semantica: Optional[float] = Field(
        None,
        alias="semantic_score",
        ge=0,
        le=1,
        description="Score de similitud semántica (0-1)"
    )
```

**Validaciones adicionales**:
- `ge=0`: Greater or Equal (≥0)
- `le=1`: Less or Equal (≤1)

```python
    class Config:
        populate_by_name = True
        use_enum_values = True
```

**Configuración del modelo**:
- `populate_by_name = True`: Acepta tanto "descripcion" como "description"
- `use_enum_values = True`: Serializa enums como strings ("obligatory") en lugar de objetos

---

## Modelos para Structured Output

Estos modelos definen el formato EXACTO que esperamos del LLM.

### RequisitoExtraido

```python
class RequisitoExtraido(BaseModel):
    """Requisito extraído de una oferta de trabajo."""
    
    description: str = Field(
        ...,
        description="Descripción del requisito"
    )
    type: Literal["obligatory", "optional"] = Field(
        ...,
        description="Tipo: 'obligatory' u 'optional'"
    )
```

**¿Por qué `Literal["obligatory", "optional"]`?**

Es más estricto que `str`. El LLM DEBE responder exactamente uno de esos dos valores.

```python
# Válido
req = RequisitoExtraido(description="Python", type="obligatory")

# Error
req = RequisitoExtraido(description="Python", type="required")
# ValidationError: Input should be 'obligatory' or 'optional'
```

### RespuestaExtraccionRequisitos

```python
class RespuestaExtraccionRequisitos(BaseModel):
    """Respuesta estructurada para extracción de requisitos."""
    
    requirements: List[RequisitoExtraido] = Field(
        ...,
        description="Lista de requisitos extraídos"
    )
```

**Uso con LLM**:

```python
llm_estructurado = llm.with_structured_output(RespuestaExtraccionRequisitos)
resultado = llm_estructurado.invoke(prompt)
# resultado.requirements es SIEMPRE una lista de RequisitoExtraido
```

---

### ResultadoMatching

```python
class ResultadoMatching(BaseModel):
    """Resultado del matching de un requisito contra el CV."""
    
    requirement_description: str = Field(
        ...,
        description="Descripción del requisito evaluado"
    )
    fulfilled: bool = Field(
        ...,
        description="Si el candidato cumple el requisito"
    )
    found_in_cv: bool = Field(
        ...,
        description="Si se encontró evidencia en el CV"
    )
    evidence: Optional[str] = Field(
        None,
        description="Texto del CV que evidencia el cumplimiento"
    )
    confidence: Literal["high", "medium", "low"] = Field(
        ...,
        description="Nivel de confianza"
    )
    reasoning: str = Field(
        ...,
        description="Explicación del razonamiento"
    )
    semantic_score: Optional[float] = Field(
        None,
        ge=0,
        le=1,
        description="Score semántico si se usó embedding"
    )
```

Este modelo contiene TODO lo que necesitamos saber sobre la evaluación de un requisito.

### RespuestaMatchingCV

```python
class RespuestaMatchingCV(BaseModel):
    """Respuesta estructurada del matching CV-requisitos."""
    
    matches: List[ResultadoMatching] = Field(
        ...,
        description="Lista de resultados de matching"
    )
    analysis_summary: str = Field(
        ...,
        description="Resumen ejecutivo del análisis"
    )
```

---

## Modelos de Evaluación

### EvaluacionRespuesta

```python
class EvaluacionRespuesta(BaseModel):
    """Evaluación estructurada de una respuesta de entrevista."""
    
    fulfilled: bool = Field(
        ...,
        description="Si la respuesta demuestra cumplimiento"
    )
    evidence: str = Field(
        ...,
        description="Evidencia de la respuesta"
    )
    confidence: Literal["high", "medium", "low"] = Field(
        ...,
        description="Nivel de confianza"
    )
```

**Uso**: Cuando el candidato responde en la entrevista, el LLM evalúa si cumple el requisito.

---

## Modelos de Resultados

### ResultadoFase1

```python
class ResultadoFase1(BaseModel):
    """Resultado completo de la Fase 1 de análisis."""
    
    puntuacion: float = Field(
        ...,
        ge=0,
        le=100,
        description="Puntuación (0-100)"
    )
    descartado: bool = Field(
        ...,
        description="Si el candidato fue descartado"
    )
    requisitos_cumplidos: List[Requisito] = Field(
        default_factory=list,
        description="Requisitos que cumple"
    )
    requisitos_no_cumplidos: List[Requisito] = Field(
        default_factory=list,
        description="Requisitos que no cumple"
    )
    requisitos_faltantes: List[str] = Field(
        default_factory=list,
        description="Requisitos sin evaluar (solo descripciones)"
    )
    resumen_analisis: str = Field(
        default="",
        description="Resumen ejecutivo"
    )
```

**`default_factory=list`**: Crea una lista vacía nueva para cada instancia.

**¿Por qué no `default=[]`?**

```python
# PELIGROSO: Todas las instancias comparten la misma lista
class Malo(BaseModel):
    items: List[str] = []

# SEGURO: Cada instancia tiene su propia lista
class Bueno(BaseModel):
    items: List[str] = Field(default_factory=list)
```

---

### PreguntaEntrevista y RespuestaEntrevista

```python
class PreguntaEntrevista(BaseModel):
    """Pregunta generada para la entrevista."""
    
    requisito: str = Field(...)
    tipo_requisito: TipoRequisito = Field(...)
    pregunta: str = Field(...)
    indice: int = Field(...)

class RespuestaEntrevista(BaseModel):
    """Respuesta del candidato a una pregunta."""
    
    pregunta: PreguntaEntrevista = Field(...)
    respuesta: str = Field(...)
    evaluacion: Optional[dict] = Field(None)
```

**Composición de modelos**: `RespuestaEntrevista` contiene un `PreguntaEntrevista`.

---

### ResultadoEvaluacion (Modelo Final)

```python
class ResultadoEvaluacion(BaseModel):
    """Resultado final de todo el proceso de evaluación."""
    
    resultado_fase1: ResultadoFase1 = Field(
        ...,
        description="Resultados de la Fase 1"
    )
    fase2_completada: bool = Field(
        default=False,
        description="Si se completó la Fase 2"
    )
    respuestas_entrevista: List[RespuestaEntrevista] = Field(
        default_factory=list,
        description="Respuestas de la entrevista"
    )
    puntuacion_final: float = Field(
        ...,
        ge=0,
        le=100
    )
    requisitos_finales_cumplidos: List[Requisito] = Field(
        default_factory=list
    )
    requisitos_finales_no_cumplidos: List[Requisito] = Field(
        default_factory=list
    )
    descartado_final: bool = Field(
        ...
    )
    resumen_evaluacion: str = Field(
        default=""
    )
```

Este modelo agrupa TODOS los resultados del proceso completo.

---

## Aliases en Inglés

```python
# Aliases para compatibilidad internacional
RequirementType = TipoRequisito
ConfidenceLevel = NivelConfianza
Requirement = Requisito
# ... etc
```

**¿Por qué?**

- Los prompts están en inglés (mejor rendimiento con LLMs)
- El código interno usa español (coherencia con el equipo)
- Los aliases permiten usar ambos

---

## Diagrama de Relaciones

```
                    ┌─────────────────────┐
                    │ ResultadoEvaluacion │
                    └─────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
          ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────────┐
│ ResultadoFase1  │ │List[Respuesta   │ │ List[Requisito]     │
│                 │ │    Entrevista]  │ │ (finales)           │
└─────────────────┘ └─────────────────┘ └─────────────────────┘
          │                   │
          │                   │
          ▼                   ▼
┌─────────────────┐ ┌─────────────────┐
│ List[Requisito] │ │ PreguntaEntre   │
│ (cumplidos/no)  │ │    vista        │
└─────────────────┘ └─────────────────┘
```

---

## Serialización

### Python → JSON

```python
requisito = Requisito(
    descripcion="5 años Python",
    tipo=TipoRequisito.OBLIGATORIO,
    cumplido=True
)

# A diccionario (con aliases)
requisito.model_dump(by_alias=True)
# {'description': '5 años Python', 'type': 'obligatory', 'fulfilled': True, ...}

# A JSON
requisito.model_dump_json(by_alias=True)
# '{"description": "5 años Python", "type": "obligatory", "fulfilled": true, ...}'
```

### JSON → Python

```python
data = {
    "description": "Docker",
    "type": "optional",
    "fulfilled": False
}

requisito = Requisito(**data)
# O usando model_validate
requisito = Requisito.model_validate(data)
```

---

## Validación en Acción

```python
# Validación de tipo
Requisito(descripcion=123, tipo="obligatory")
# ValidationError: Input should be a valid string

# Validación de rango
Requisito(
    descripcion="Python",
    tipo="obligatory",
    puntuacion_semantica=1.5  # Fuera de rango
)
# ValidationError: Input should be less than or equal to 1

# Validación de Literal
ResultadoMatching(
    requirement_description="Python",
    fulfilled=True,
    found_in_cv=True,
    confidence="muy_alto"  # No es high/medium/low
)
# ValidationError: Input should be 'high', 'medium' or 'low'
```

---

## Justificación de Diseño

### ¿Por qué tantos modelos?

Cada modelo tiene un propósito específico:

| Modelo | Propósito |
|--------|-----------|
| `RequisitoExtraido` | Output del LLM para extracción |
| `ResultadoMatching` | Output del LLM para matching |
| `Requisito` | Modelo interno unificado |
| `ResultadoFase1` | Agrupa resultados de Fase 1 |
| `ResultadoEvaluacion` | Agrupa resultados de todo el proceso |

### ¿Por qué aliases español/inglés?

- **Prompts en inglés**: Los LLMs rinden mejor con prompts en inglés
- **Código en español**: Coherencia con el equipo de desarrollo
- **Aliases**: Puente entre ambos mundos

### ¿Por qué Pydantic v2?

- Structured Output de LangChain requiere Pydantic v2
- Mejor rendimiento que v1
- API más limpia (`model_dump` vs `dict`)

