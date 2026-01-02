# Documentación: `backend/nucleo/entrevista/entrevistador.py`

## Información General

| Atributo | Valor |
|----------|-------|
| **Ruta** | `/backend/nucleo/entrevista/entrevistador.py` |
| **Tipo** | Componente de núcleo |
| **Líneas** | ~350 |
| **Clase principal** | `EntrevistadorFase2` |

---

## Propósito

Este archivo implementa la **Fase 2 del proceso de evaluación**: una entrevista conversacional que verifica requisitos que no pudieron confirmarse automáticamente en la Fase 1.

---

## Arquitectura de Dos LLMs

```python
class EntrevistadorFase2:
    """
    Entrevistador conversacional para Fase 2.
    
    Usa DOS LLMs con diferentes configuraciones:
    - LLM de conversación: temperatura alta para respuestas naturales
    - LLM de evaluación: temperatura baja para análisis objetivo
    """
```

**¿Por qué dos LLMs?**

| Tarea | LLM | Temperatura | Razón |
|-------|-----|-------------|-------|
| Generar preguntas | Conversación | 0.3 | Necesita ser natural y variado |
| Saludar/despedir | Conversación | 0.3 | Tono humano y empático |
| Evaluar respuestas | Evaluación | 0.0 | Determinista y objetivo |

---

## Constructor

```python
    def __init__(
        self,
        llm=None,
        proveedor: str = "openai",
        modelo: str = "gpt-4o",
        api_key: Optional[str] = None
    ):
        self._proveedor = proveedor
        self._modelo = modelo
        self._api_key = api_key
```

### Configuración de LLMs

```python
        # Hiperparámetros de configuración
        config_conversacion = ConfiguracionHiperparametros.obtener_fase2_entrevista()
        config_evaluacion = ConfiguracionHiperparametros.obtener_fase1_matching()
        
        # LLM para conversación (más creativo)
        if llm is None:
            self._llm_conversacion = FabricaLLM.crear_llm(
                proveedor=proveedor,
                modelo=modelo,
                temperatura=config_conversacion.temperature,  # 0.3
                api_key=api_key
            )
        else:
            self._llm_conversacion = llm
        
        # LLM para evaluación (determinista)
        self._llm_evaluacion = FabricaLLM.crear_llm(
            proveedor=proveedor,
            modelo=modelo,
            temperatura=config_evaluacion.temperature,  # 0.0
            api_key=api_key
        )
```

### Estado de la Entrevista

```python
        # Estado interno
        self._nombre_candidato: Optional[str] = None
        self._requisitos_pendientes: List[dict] = []
        self._contexto_cv: str = ""
        self._historial: List[dict] = []
        self._respuestas: List[RespuestaEntrevista] = []
```

---

## Método: `inicializar_entrevista`

```python
    def inicializar_entrevista(
        self,
        nombre_candidato: str,
        resultado_fase1: ResultadoFase1,
        contexto_cv: str = ""
    ) -> None:
        """
        Inicializa una nueva sesión de entrevista.
        
        Args:
            nombre_candidato: Nombre para dirigirse al candidato
            resultado_fase1: Resultados de Fase 1 (para saber qué preguntar)
            contexto_cv: Texto del CV para contexto
        """
        self._nombre_candidato = nombre_candidato
        self._contexto_cv = contexto_cv
        self._historial = []
        self._respuestas = []
```

### Preparar Requisitos Pendientes

```python
        # Convertir requisitos no cumplidos a lista de pendientes
        self._requisitos_pendientes = []
        for req in resultado_fase1.requisitos_no_cumplidos:
            self._requisitos_pendientes.append({
                "description": req.descripcion,
                "type": req.tipo.value if hasattr(req.tipo, 'value') else req.tipo,
                "original_evidence": req.evidencia,
                "original_confidence": req.confianza
            })
        
        logger.log_fase2(
            f"Entrevista inicializada para {nombre_candidato}. "
            f"{len(self._requisitos_pendientes)} requisitos a verificar."
        )
```

---

## Métodos de Streaming

### `transmitir_saludo`

```python
    def transmitir_saludo(self):
        """
        Genera saludo inicial con streaming.
        
        Yields:
            Tokens del saludo uno por uno
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", PROMPT_SISTEMA_AGENTE),
            ("human", PROMPT_SALUDO_AGENTE.format(
                nombre=self._nombre_candidato,
                num_requisitos=len(self._requisitos_pendientes)
            ))
        ])
        
        chain = prompt | self._llm_conversacion | StrOutputParser()
        
        # Streaming token por token
        saludo_completo = ""
        for token in chain.stream({}):
            saludo_completo += token
            yield token
        
        # Guardar en historial
        self._historial.append({
            "role": "assistant",
            "content": saludo_completo
        })
```

**¿Qué es streaming?**

```
Sin streaming:
    Esperar 3 segundos → "¡Hola Carlos! Vamos a verificar algunos requisitos..."

Con streaming:
    0.1s → "¡"
    0.2s → "Hola"
    0.3s → " Carlos"
    0.4s → "!"
    ...
```

El usuario ve el texto aparecer progresivamente, mejorando la experiencia.

---

### `transmitir_pregunta`

```python
    def transmitir_pregunta(self, indice: int):
        """
        Genera pregunta para un requisito específico con streaming.
        
        Args:
            indice: Índice del requisito en la lista de pendientes
            
        Yields:
            Tokens de la pregunta
        """
        if indice >= len(self._requisitos_pendientes):
            return
        
        requisito = self._requisitos_pendientes[indice]
```

**Construir contexto de conversación**:

```python
        # Incluir historial previo para coherencia
        mensajes = [
            ("system", PROMPT_SISTEMA_AGENTE)
        ]
        
        # Añadir historial de la conversación
        for entrada in self._historial:
            mensajes.append((
                "assistant" if entrada["role"] == "assistant" else "human",
                entrada["content"]
            ))
```

**Añadir instrucción para la pregunta**:

```python
        # Instrucción para generar pregunta
        mensajes.append((
            "human",
            PROMPT_PREGUNTA_AGENTE.format(
                requisito=requisito["description"],
                tipo=requisito["type"],
                contexto_cv=self._contexto_cv[:500] if self._contexto_cv else "No disponible"
            )
        ))
        
        prompt = ChatPromptTemplate.from_messages(mensajes)
        chain = prompt | self._llm_conversacion | StrOutputParser()
        
        pregunta_completa = ""
        for token in chain.stream({}):
            pregunta_completa += token
            yield token
        
        # Guardar en historial
        self._historial.append({
            "role": "assistant",
            "content": pregunta_completa
        })
```

---

### `transmitir_cierre`

```python
    def transmitir_cierre(self, aprobado: bool):
        """
        Genera mensaje de cierre con streaming.
        
        Args:
            aprobado: Si el candidato fue aprobado o no
            
        Yields:
            Tokens del mensaje de cierre
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", PROMPT_SISTEMA_AGENTE),
            ("human", PROMPT_CIERRE_AGENTE.format(
                nombre=self._nombre_candidato,
                resultado="aprobado" if aprobado else "no aprobado"
            ))
        ])
        
        chain = prompt | self._llm_conversacion | StrOutputParser()
        
        for token in chain.stream({}):
            yield token
```

---

## Método: `registrar_respuesta`

```python
    def registrar_respuesta(
        self,
        indice: int,
        respuesta: str
    ) -> RespuestaEntrevista:
        """
        Registra la respuesta del candidato a una pregunta.
        
        Args:
            indice: Índice del requisito
            respuesta: Texto de la respuesta del candidato
            
        Returns:
            Objeto RespuestaEntrevista con la información
        """
        if indice >= len(self._requisitos_pendientes):
            raise ValueError(f"Índice {indice} fuera de rango")
        
        requisito = self._requisitos_pendientes[indice]
        
        # Crear objeto de pregunta
        pregunta = PreguntaEntrevista(
            requisito=requisito["description"],
            tipo_requisito=TipoRequisito(requisito["type"]),
            pregunta=self._historial[-1]["content"] if self._historial else "",
            indice=indice
        )
        
        # Crear objeto de respuesta
        respuesta_entrevista = RespuestaEntrevista(
            pregunta=pregunta,
            respuesta=respuesta,
            evaluacion=None  # Se evalúa después
        )
        
        # Guardar en historial
        self._historial.append({
            "role": "user",
            "content": respuesta
        })
        
        self._respuestas.append(respuesta_entrevista)
        
        return respuesta_entrevista
```

---

## Método: `evaluar_respuesta`

```python
    def evaluar_respuesta(
        self,
        descripcion_requisito: str,
        tipo_requisito: TipoRequisito,
        contexto_cv: str,
        respuesta_candidato: str
    ) -> dict:
        """
        Evalúa si una respuesta demuestra cumplimiento del requisito.
        
        Usa Structured Output para garantizar formato de evaluación.
        """
        logger.log_fase2(f"Evaluando respuesta para: {descripcion_requisito[:50]}...")
```

**Crear prompt de evaluación**:

```python
        prompt = ChatPromptTemplate.from_messages([
            ("system", PROMPT_EVALUAR_RESPUESTA),
            ("human", f"""
REQUISITO A EVALUAR:
- Descripción: {descripcion_requisito}
- Tipo: {tipo_requisito.value}

CONTEXTO DEL CV:
{contexto_cv[:1000] if contexto_cv else "No disponible"}

RESPUESTA DEL CANDIDATO:
{respuesta_candidato}

Evalúa si la respuesta demuestra cumplimiento del requisito.
""")
        ])
```

**Ejecutar con Structured Output**:

```python
        # LLM de evaluación (temperatura 0.0)
        llm_eval = self._llm_evaluacion.with_structured_output(EvaluacionRespuesta)
        chain = prompt | llm_eval
        
        try:
            resultado = chain.invoke({})
            evaluacion = {
                "fulfilled": resultado.fulfilled,
                "evidence": resultado.evidence,
                "confidence": resultado.confidence
            }
        except Exception as e:
            logger.log_error(f"Error en evaluación: {e}")
            evaluacion = {
                "fulfilled": False,
                "evidence": "Error en evaluación",
                "confidence": "low"
            }
        
        return evaluacion
```

---

## Método: `obtener_respuestas_entrevista`

```python
    def obtener_respuestas_entrevista(self) -> List[RespuestaEntrevista]:
        """
        Devuelve todas las respuestas registradas.
        
        Returns:
            Lista de RespuestaEntrevista con evaluaciones
        """
        return self._respuestas.copy()
```

---

## Diagrama del Flujo de Entrevista

```
┌──────────────────────────────────────────────────────────────────┐
│                    ENTREVISTA FASE 2                              │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                 ┌────────────────────────┐
                 │ inicializar_entrevista │
                 │ - Cargar req pendientes│
                 │ - Guardar contexto CV  │
                 └────────────────────────┘
                              │
                              ▼
                 ┌────────────────────────┐
                 │ transmitir_saludo()    │
                 │ → "Hola Carlos, vamos  │
                 │    a verificar..."     │
                 └────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    POR CADA REQUISITO                            │
├─────────────────────────────────────────────────────────────────┤
│                              │                                   │
│              ┌───────────────┴───────────────┐                  │
│              │ transmitir_pregunta(indice)   │                  │
│              │ → "¿Podrías contarme sobre    │                  │
│              │    tu experiencia con X?"     │                  │
│              └───────────────────────────────┘                  │
│                              │                                   │
│                              ▼                                   │
│              ┌───────────────────────────────┐                  │
│              │ Usuario responde              │                  │
│              │ → "Sí, he trabajado con X     │                  │
│              │    durante 2 años..."         │                  │
│              └───────────────────────────────┘                  │
│                              │                                   │
│                              ▼                                   │
│              ┌───────────────────────────────┐                  │
│              │ registrar_respuesta(i, resp)  │                  │
│              │ - Guardar en historial        │                  │
│              └───────────────────────────────┘                  │
│                              │                                   │
│                              ▼                                   │
│              ┌───────────────────────────────┐                  │
│              │ evaluar_respuesta()           │                  │
│              │ - LLM analiza si cumple       │                  │
│              │ → {fulfilled: true/false}     │                  │
│              └───────────────────────────────┘                  │
│                              │                                   │
└─────────────────────────────┼───────────────────────────────────┘
                              │
                              ▼
                 ┌────────────────────────┐
                 │ transmitir_cierre()    │
                 │ → "Gracias Carlos,     │
                 │    has sido aprobado"  │
                 └────────────────────────┘
```

---

## Historial de Conversación

El historial permite que el LLM mantenga coherencia:

```python
self._historial = [
    {"role": "assistant", "content": "¡Hola Carlos! Vamos a..."},
    {"role": "user", "content": "Claro, adelante"},
    {"role": "assistant", "content": "¿Podrías contarme sobre Python?"},
    {"role": "user", "content": "Sí, tengo 5 años..."},
    {"role": "assistant", "content": "Excelente. Ahora sobre Docker..."},
    ...
]
```

Cada pregunta incluye todo el historial previo, permitiendo:
- Referencias a respuestas anteriores
- Tono consistente
- Conversación natural

---

## Justificación de Diseño

### ¿Por qué streaming?

1. **UX mejorada**: El usuario ve la respuesta en tiempo real
2. **Percepción de velocidad**: No hay "lag" visible
3. **Engagement**: La conversación se siente más natural

### ¿Por qué dos temperaturas?

| LLM | Temp | Razón |
|-----|------|-------|
| Conversación | 0.3 | Preguntas variadas, tono natural |
| Evaluación | 0.0 | Decisiones objetivas y reproducibles |

Si usáramos 0.0 para todo, las preguntas serían robóticas y repetitivas.

### ¿Por qué historial completo?

El LLM necesita contexto para:
- No repetir preguntas
- Hacer follow-ups relevantes
- Mantener coherencia de tono

### ¿Por qué Structured Output en evaluación?

La evaluación DEBE ser:
- `fulfilled`: boolean exacto
- `evidence`: texto de evidencia
- `confidence`: high/medium/low

Sin Structured Output, el LLM podría responder "Sí, parece que cumple" y tendríamos que parsearlo.

