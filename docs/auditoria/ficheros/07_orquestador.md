# Documentación: `backend/orquestacion/orquestador.py`

## Información General

| Atributo | Valor |
|----------|-------|
| **Ruta** | `/backend/orquestacion/orquestador.py` |
| **Tipo** | Coordinador de alto nivel |
| **Líneas** | ~300 |
| **Clase principal** | `Orquestador` |

---

## Propósito

El **Orquestador** es el punto de entrada de alto nivel para ejecutar evaluaciones completas. Coordina:

1. Fase 1: Análisis automático
2. Transición condicional a Fase 2
3. Fase 2: Entrevista (si aplica)
4. Recálculo final de puntuación

---

## Diagrama de Responsabilidades

```
                        ┌─────────────────────┐
                        │    Orquestador      │
                        │ (Coordinador)       │
                        └─────────────────────┘
                                  │
                ┌─────────────────┴─────────────────┐
                │                                   │
                ▼                                   ▼
      ┌─────────────────┐               ┌─────────────────┐
      │ AnalizadorFase1 │               │EntrevistadorFase2│
      │ (nucleo)        │               │ (nucleo)        │
      └─────────────────┘               └─────────────────┘
```

---

## Constructor

```python
class Orquestador:
    """
    Coordina la ejecución completa del proceso de evaluación.
    
    Integra AnalizadorFase1 y EntrevistadorFase2, manejando
    la transición entre fases y el recálculo de puntuaciones.
    """
    
    def __init__(
        self,
        proveedor: str = "openai",
        modelo: str = "gpt-4o",
        api_key: Optional[str] = None,
        usar_matching_semantico: bool = True,
        usar_langgraph: bool = False
    ):
```

### Inicialización de Componentes

```python
        # Guardar configuración
        self._proveedor = proveedor
        self._modelo = modelo
        self._api_key = api_key
        
        # Crear analizador de Fase 1
        self._analizador = AnalizadorFase1(
            proveedor=proveedor,
            modelo=modelo,
            temperatura=0.0,  # Determinista
            api_key=api_key,
            usar_matching_semantico=usar_matching_semantico,
            usar_langgraph=usar_langgraph
        )
        
        # Crear entrevistador de Fase 2
        self._entrevistador = EntrevistadorFase2(
            proveedor=proveedor,
            modelo=modelo,
            api_key=api_key
        )
        
        logger.log_config(
            f"Orquestador inicializado: {proveedor}/{modelo}"
        )
```

---

## Método Principal: `evaluar_candidato`

```python
    def evaluar_candidato(
        self,
        cv: str,
        oferta_trabajo: str,
        nombre_candidato: str = "Candidato",
        modo_batch: bool = False,
        respuestas_batch: Optional[List[str]] = None
    ) -> ResultadoEvaluacion:
        """
        Ejecuta el proceso completo de evaluación.
        
        Args:
            cv: Texto del CV del candidato
            oferta_trabajo: Texto de la oferta de trabajo
            nombre_candidato: Nombre para la entrevista
            modo_batch: Si True, ejecuta Fase 2 automáticamente
            respuestas_batch: Respuestas predefinidas para modo batch
            
        Returns:
            ResultadoEvaluacion con puntuación final
        """
```

### Paso 1: Ejecutar Fase 1

```python
        logger.log_fase1("="*60)
        logger.log_fase1("INICIANDO EVALUACIÓN DE CANDIDATO")
        logger.log_fase1("="*60)
        
        # Ejecutar análisis de Fase 1
        resultado_fase1 = self._analizador.analizar(cv, oferta_trabajo)
        
        logger.log_fase1(
            f"Fase 1 completada: {resultado_fase1.puntuacion:.1f}% - "
            f"Descartado: {resultado_fase1.descartado}"
        )
```

### Paso 2: Verificar si necesita Fase 2

```python
        # Si está descartado, no continuar a Fase 2
        if resultado_fase1.descartado:
            logger.log_fase1("Candidato descartado. No se requiere Fase 2.")
            return ResultadoEvaluacion(
                resultado_fase1=resultado_fase1,
                fase2_completada=False,
                respuestas_entrevista=[],
                puntuacion_final=0.0,
                requisitos_finales_cumplidos=resultado_fase1.requisitos_cumplidos,
                requisitos_finales_no_cumplidos=resultado_fase1.requisitos_no_cumplidos,
                descartado_final=True,
                resumen_evaluacion="Candidato descartado por no cumplir requisitos obligatorios."
            )
```

**Lógica de descarte**:
- Si falta un requisito OBLIGATORIO → descartado
- No tiene sentido hacer entrevista si ya sabemos que no pasa

### Paso 3: Verificar si hay requisitos pendientes

```python
        # Si no hay requisitos no cumplidos, terminar
        if not resultado_fase1.requisitos_no_cumplidos:
            logger.log_fase1("Todos los requisitos cumplidos. No se requiere Fase 2.")
            return ResultadoEvaluacion(
                resultado_fase1=resultado_fase1,
                fase2_completada=False,
                respuestas_entrevista=[],
                puntuacion_final=resultado_fase1.puntuacion,
                requisitos_finales_cumplidos=resultado_fase1.requisitos_cumplidos,
                requisitos_finales_no_cumplidos=[],
                descartado_final=False,
                resumen_evaluacion=self._generar_resumen(resultado_fase1, [])
            )
```

### Paso 4: Ejecutar Fase 2 (si aplica)

```python
        # Inicializar entrevista
        logger.log_fase2("="*60)
        logger.log_fase2("INICIANDO FASE 2: ENTREVISTA")
        logger.log_fase2("="*60)
        
        self._entrevistador.inicializar_entrevista(
            nombre_candidato=nombre_candidato,
            resultado_fase1=resultado_fase1,
            contexto_cv=cv
        )
        
        # Ejecutar según modo
        if modo_batch:
            respuestas = self._realizar_entrevista_batch(respuestas_batch or [])
        else:
            # En modo interactivo, el frontend maneja la entrevista
            # y llama a reevaluar_con_entrevista después
            return ResultadoEvaluacion(
                resultado_fase1=resultado_fase1,
                fase2_completada=False,  # Pendiente
                respuestas_entrevista=[],
                puntuacion_final=resultado_fase1.puntuacion,
                requisitos_finales_cumplidos=resultado_fase1.requisitos_cumplidos,
                requisitos_finales_no_cumplidos=resultado_fase1.requisitos_no_cumplidos,
                descartado_final=resultado_fase1.descartado,
                resumen_evaluacion="Fase 2 pendiente de completar."
            )
```

---

## Método: `_realizar_entrevista_batch`

```python
    def _realizar_entrevista_batch(
        self,
        respuestas: List[str]
    ) -> List[RespuestaEntrevista]:
        """
        Ejecuta la entrevista en modo batch (sin interacción).
        
        Útil para:
        - Tests automatizados
        - Evaluación masiva de candidatos
        - Simulación con respuestas predefinidas
        """
        resultados = []
        requisitos_pendientes = self._entrevistador._requisitos_pendientes
        
        for i, req in enumerate(requisitos_pendientes):
            # Usar respuesta proporcionada o genérica
            respuesta = respuestas[i] if i < len(respuestas) else "Sin respuesta"
            
            # Registrar respuesta
            resp_entrevista = self._entrevistador.registrar_respuesta(i, respuesta)
            
            # Evaluar respuesta
            evaluacion = self._entrevistador.evaluar_respuesta(
                descripcion_requisito=req["description"],
                tipo_requisito=TipoRequisito(req["type"]),
                contexto_cv="",
                respuesta_candidato=respuesta
            )
            
            # Actualizar con evaluación
            resp_entrevista.evaluacion = evaluacion
            resultados.append(resp_entrevista)
            
            logger.log_fase2(
                f"Requisito {i+1}: {'✓' if evaluacion['fulfilled'] else '✗'} - "
                f"{req['description'][:40]}..."
            )
        
        return resultados
```

---

## Método: `reevaluar_con_entrevista`

```python
    def reevaluar_con_entrevista(
        self,
        resultado_fase1: ResultadoFase1,
        respuestas_entrevista: List[RespuestaEntrevista]
    ) -> ResultadoEvaluacion:
        """
        Recalcula la puntuación final después de la entrevista.
        
        Se llama desde el frontend después de completar la Fase 2
        interactiva.
        """
        logger.log_fase2("Recalculando puntuación con resultados de entrevista...")
```

### Procesar Resultados de Entrevista

```python
        # Identificar requisitos cumplidos en la entrevista
        cumplidos_entrevista = []
        no_cumplidos_finales = []
        
        for resp in respuestas_entrevista:
            req = resp.pregunta
            evaluacion = resp.evaluacion
            
            if evaluacion and evaluacion.get("fulfilled", False):
                # Convertir a Requisito
                requisito_cumplido = Requisito(
                    descripcion=req.requisito,
                    tipo=req.tipo_requisito,
                    cumplido=True,
                    evidencia=evaluacion.get("evidence", ""),
                    confianza=NivelConfianza(evaluacion.get("confidence", "medium")),
                    razonamiento="Verificado en entrevista"
                )
                cumplidos_entrevista.append(requisito_cumplido)
            else:
                # No cumplido
                requisito_no_cumplido = Requisito(
                    descripcion=req.requisito,
                    tipo=req.tipo_requisito,
                    cumplido=False,
                    evidencia=evaluacion.get("evidence", "") if evaluacion else "",
                    razonamiento="No verificado en entrevista"
                )
                no_cumplidos_finales.append(requisito_no_cumplido)
```

### Calcular Puntuación Final

```python
        # Combinar con resultados de Fase 1
        todos_cumplidos = resultado_fase1.requisitos_cumplidos + cumplidos_entrevista
        
        # Los no cumplidos finales son solo los que fallaron en la entrevista
        # (los que estaban cumplidos en Fase 1 siguen cumplidos)
        
        # Verificar si quedó algún obligatorio sin cumplir
        tiene_obligatorio_no_cumplido = any(
            req.tipo == TipoRequisito.OBLIGATORIO
            for req in no_cumplidos_finales
        )
        
        # Calcular puntuación
        total_requisitos = (
            len(resultado_fase1.requisitos_cumplidos) +
            len(resultado_fase1.requisitos_no_cumplidos)
        )
        
        puntuacion_final = calcular_puntuacion(
            total=total_requisitos,
            cumplidos=len(todos_cumplidos),
            tiene_obligatorio_no_cumplido=tiene_obligatorio_no_cumplido
        )
```

### Construir Resultado Final

```python
        return ResultadoEvaluacion(
            resultado_fase1=resultado_fase1,
            fase2_completada=True,
            respuestas_entrevista=respuestas_entrevista,
            puntuacion_final=puntuacion_final,
            requisitos_finales_cumplidos=todos_cumplidos,
            requisitos_finales_no_cumplidos=no_cumplidos_finales,
            descartado_final=tiene_obligatorio_no_cumplido,
            resumen_evaluacion=self._generar_resumen(
                resultado_fase1, 
                respuestas_entrevista
            )
        )
```

---

## Método: `_generar_resumen`

```python
    def _generar_resumen(
        self,
        resultado_fase1: ResultadoFase1,
        respuestas_entrevista: List[RespuestaEntrevista]
    ) -> str:
        """
        Genera un resumen ejecutivo de la evaluación.
        """
        lineas = []
        
        # Resumen Fase 1
        lineas.append(f"## Fase 1: Análisis Automático")
        lineas.append(f"- Puntuación: {resultado_fase1.puntuacion:.1f}%")
        lineas.append(f"- Requisitos cumplidos: {len(resultado_fase1.requisitos_cumplidos)}")
        lineas.append(f"- Requisitos no cumplidos: {len(resultado_fase1.requisitos_no_cumplidos)}")
        
        # Resumen Fase 2 (si aplica)
        if respuestas_entrevista:
            lineas.append(f"\n## Fase 2: Entrevista")
            cumplidos_f2 = sum(
                1 for r in respuestas_entrevista 
                if r.evaluacion and r.evaluacion.get("fulfilled")
            )
            lineas.append(f"- Preguntas realizadas: {len(respuestas_entrevista)}")
            lineas.append(f"- Requisitos verificados: {cumplidos_f2}")
        
        return "\n".join(lineas)
```

---

## Método: `registrar_feedback`

```python
    def registrar_feedback(
        self,
        resultado: ResultadoEvaluacion,
        feedback_positivo: bool,
        comentario: Optional[str] = None
    ) -> None:
        """
        Registra feedback del usuario en LangSmith.
        
        Útil para:
        - Evaluar calidad de las evaluaciones
        - Mejorar prompts basándose en feedback
        - Trazabilidad de decisiones
        """
        from langsmith import Client
        
        try:
            client = Client()
            client.create_feedback(
                run_id=...,  # ID del run actual
                key="user_feedback",
                score=1.0 if feedback_positivo else 0.0,
                comment=comentario
            )
            logger.log_config(f"Feedback registrado: {'✓' if feedback_positivo else '✗'}")
        except Exception as e:
            logger.log_advertencia(f"No se pudo registrar feedback: {e}")
```

---

## Flujo Completo de Evaluación

```
┌──────────────────────────────────────────────────────────────────┐
│                    evaluar_candidato()                            │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                    FASE 1: Análisis                               │
│                    analizador.analizar()                          │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────────┐
                    │ ¿Descartado?        │
                    │ (obligatorio falta) │
                    └─────────────────────┘
                         │           │
                        SÍ          NO
                         │           │
                         ▼           ▼
              ┌──────────────┐  ┌─────────────────────┐
              │ Retornar     │  │ ¿Hay requisitos     │
              │ descartado   │  │ no cumplidos?       │
              └──────────────┘  └─────────────────────┘
                                     │           │
                                    SÍ          NO
                                     │           │
                                     ▼           ▼
                        ┌──────────────┐  ┌──────────────┐
                        │ FASE 2       │  │ Retornar     │
                        │ Entrevista   │  │ aprobado     │
                        └──────────────┘  └──────────────┘
                              │
                              ▼
                ┌─────────────────────────┐
                │ ¿Modo batch?            │
                └─────────────────────────┘
                     │           │
                    SÍ          NO
                     │           │
                     ▼           ▼
         ┌──────────────┐  ┌──────────────────┐
         │ Ejecutar     │  │ Retornar         │
         │ automático   │  │ fase2_pendiente  │
         └──────────────┘  │ (frontend maneja)│
                │          └──────────────────┘
                ▼
    ┌────────────────────────┐
    │ reevaluar_con_         │
    │ entrevista()           │
    └────────────────────────┘
                │
                ▼
    ┌────────────────────────┐
    │ ResultadoEvaluacion    │
    │ (puntuación final)     │
    └────────────────────────┘
```

---

## Justificación de Diseño

### ¿Por qué un Orquestador separado?

| Alternativa | Problema |
|-------------|----------|
| Todo en AnalizadorFase1 | Violación de SRP, acoplamiento |
| Todo en Streamlit | Lógica de negocio en frontend |
| **Orquestador dedicado** | ✅ Coordinación limpia, reusable |

### ¿Por qué modo batch?

- **Testing**: Probar el flujo completo sin UI
- **Evaluación masiva**: Procesar muchos candidatos
- **CI/CD**: Validar que el sistema funciona

### ¿Por qué transición condicional?

No tiene sentido hacer entrevista si:
1. El candidato está descartado (falta obligatorio)
2. Todos los requisitos están cumplidos

Esto ahorra tiempo y costos de API.

### ¿Por qué reevaluación separada?

En modo interactivo:
1. `evaluar_candidato()` retorna con Fase 2 pendiente
2. Frontend maneja la conversación
3. `reevaluar_con_entrevista()` calcula resultado final

Esto permite que el frontend tenga control total sobre la UX de la entrevista.

