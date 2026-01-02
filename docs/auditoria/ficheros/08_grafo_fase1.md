# Documentación: `backend/orquestacion/grafo_fase1.py`

## Información General

| Atributo | Valor |
|----------|-------|
| **Ruta** | `/backend/orquestacion/grafo_fase1.py` |
| **Tipo** | Implementación LangGraph |
| **Líneas** | ~200 |
| **Framework** | LangGraph |

---

## Propósito

Este archivo implementa el flujo de **Fase 1 usando LangGraph**, un framework de orquestación basado en grafos de estados.

**¿Por qué LangGraph?**
- Control granular de cada paso
- Streaming de eventos por nodo
- Estado tipado (TypedDict)
- Visualización del flujo

---

## Concepto: LangGraph

### ¿Qué es un Grafo de Estados?

```
Estado Inicial
      │
      ▼
┌─────────────┐     Estado actualizado
│   Nodo 1    │ ─────────────────────────►
└─────────────┘
      │
      ▼
┌─────────────┐     Estado actualizado
│   Nodo 2    │ ─────────────────────────►
└─────────────┘
      │
      ▼
     END
```

Cada nodo:
1. Recibe el estado actual
2. Lo procesa/modifica
3. Devuelve el estado actualizado

---

## Definición del Estado

```python
from typing import TypedDict, List, Optional, Dict, Any

class EstadoFase1(TypedDict):
    """
    Estado canónico del grafo de Fase 1.
    
    TypedDict garantiza tipos en tiempo de desarrollo
    pero permite flexibilidad en runtime.
    """
    
    # Entradas
    oferta_trabajo: str
    cv: str
    
    # Configuración
    usar_embeddings: bool
    proveedor: str
    modelo: str
    api_key: Optional[str]
    
    # Resultados intermedios
    requisitos: List[dict]
    evidencia_semantica: Dict[str, dict]
    resultado_matching: Optional[dict]
    
    # Resultado final
    resultado_fase1: Optional[Any]  # ResultadoFase1
    
    # Metadatos
    errores: List[str]
```

### ¿Qué es TypedDict?

```python
from typing import TypedDict

# TypedDict define la estructura esperada
class Persona(TypedDict):
    nombre: str
    edad: int

# Uso
p: Persona = {"nombre": "Ana", "edad": 30}

# El IDE sabe que p["nombre"] es str
# p["apellido"]  # Error: no existe en TypedDict
```

---

## Nodos del Grafo

### Nodo 1: Extracción de Requisitos

```python
def crear_nodo_extraccion(llm, proveedor: str, modelo: str):
    """
    Factory que crea el nodo de extracción.
    
    Returns:
        Función que procesa el estado
    """
    
    def nodo_extraer_requisitos(estado: EstadoFase1) -> dict:
        """
        Extrae requisitos de la oferta de trabajo.
        
        Input del estado:
            - oferta_trabajo
            
        Output al estado:
            - requisitos: List[dict]
        """
        logger.log_langgraph("Nodo: extraer_requisitos")
        
        # Crear prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", PROMPT_EXTRACCION_REQUISITOS),
            ("human", "{job_offer}")
        ])
        
        # Structured Output
        llm_extraccion = llm.with_structured_output(RespuestaExtraccionRequisitos)
        chain = prompt | llm_extraccion
        
        try:
            resultado = chain.invoke({"job_offer": estado["oferta_trabajo"]})
            requisitos = [
                {"description": r.description, "type": r.type}
                for r in resultado.requirements
            ]
            return {"requisitos": requisitos}
        except Exception as e:
            logger.log_error(f"Error en extracción: {e}")
            return {
                "requisitos": [],
                "errores": estado.get("errores", []) + [str(e)]
            }
    
    return nodo_extraer_requisitos
```

**Patrón Factory**:
```python
# La función externa recibe configuración
def crear_nodo_extraccion(llm, proveedor, modelo):
    
    # La función interna usa esa configuración
    def nodo_extraer_requisitos(estado):
        # llm, proveedor, modelo están disponibles aquí
        ...
    
    return nodo_extraer_requisitos
```

---

### Nodo 2: Indexación de Embeddings

```python
def crear_nodo_embedding(embeddings):
    """Factory para el nodo de embedding."""
    
    def nodo_embeber_cv(estado: EstadoFase1) -> dict:
        """
        Indexa el CV con embeddings para búsqueda semántica.
        
        Input del estado:
            - cv
            - requisitos
            - usar_embeddings
            
        Output al estado:
            - evidencia_semantica: Dict[str, dict]
        """
        logger.log_langgraph("Nodo: embeber_cv")
        
        # Si no se usan embeddings, skip
        if not estado.get("usar_embeddings", False):
            return {"evidencia_semantica": {}}
        
        if not embeddings:
            return {"evidencia_semantica": {}}
        
        # Crear comparador
        comparador = ComparadorSemantico(embeddings)
        comparador.indexar_cv(estado["cv"])
        
        # Buscar evidencia para cada requisito
        evidencia = {}
        for req in estado["requisitos"]:
            resultado = comparador.encontrar_evidencia(req["description"], k=2)
            if resultado:
                evidencia[req["description"].lower()] = resultado
        
        comparador.limpiar()  # Liberar memoria
        
        return {"evidencia_semantica": evidencia}
    
    return nodo_embeber_cv
```

---

### Nodo 3: Matching CV-Requisitos

```python
def crear_nodo_matching(llm):
    """Factory para el nodo de matching."""
    
    def nodo_matching_semantico(estado: EstadoFase1) -> dict:
        """
        Evalúa el CV contra cada requisito.
        
        CRÍTICO: Inyecta contexto temporal.
        """
        logger.log_langgraph("Nodo: matching_semantico")
        
        # Contexto temporal OBLIGATORIO
        from backend.utilidades import (
            obtener_contexto_prompt,
            generar_instrucciones_experiencia
        )
        
        contexto_temporal = obtener_contexto_prompt()
        instrucciones = generar_instrucciones_experiencia()
```

**Construcción del prompt con evidencia semántica**:

```python
        # Construir texto de requisitos con pistas
        texto_requisitos = ""
        evidencia = estado.get("evidencia_semantica", {})
        
        for req in estado["requisitos"]:
            linea = f"- [{req['type'].upper()}] {req['description']}"
            
            # Añadir pista semántica si existe
            key = req['description'].lower()
            if key in evidencia:
                pista = evidencia[key].get('text', '')[:100]
                linea += f"\n  [PISTA: \"{pista}...\"]"
            
            texto_requisitos += linea + "\n"
        
        # Crear prompt con contexto temporal
        prompt = ChatPromptTemplate.from_messages([
            ("system", PROMPT_MATCHING_CV),
            ("human", f"""
{contexto_temporal}

{instrucciones}

## CV:
{estado['cv']}

## REQUISITOS:
{texto_requisitos}
""")
        ])
        
        # Ejecutar
        llm_matching = llm.with_structured_output(RespuestaMatchingCV)
        resultado = (prompt | llm_matching).invoke({})
        
        return {
            "resultado_matching": {
                "matches": [m.model_dump() for m in resultado.matches],
                "analysis_summary": resultado.analysis_summary
            }
        }
    
    return nodo_matching_semantico
```

---

### Nodo 4: Cálculo de Puntuación

```python
def crear_nodo_puntuacion():
    """Factory para el nodo de puntuación."""
    
    def nodo_calcular_puntuacion(estado: EstadoFase1) -> dict:
        """
        Calcula la puntuación final basándose en los matches.
        """
        logger.log_langgraph("Nodo: calcular_puntuacion")
        
        requisitos = estado["requisitos"]
        resultado_matching = estado["resultado_matching"]
        evidencia = estado.get("evidencia_semantica", {})
        
        # Procesar coincidencias
        req_cumplidos, req_no_cumplidos, req_faltantes, procesados = \
            procesar_coincidencias(
                resultado_matching["matches"],
                requisitos,
                evidencia
            )
        
        # Verificar obligatorios
        tiene_obligatorio_no_cumplido = any(
            req.tipo == TipoRequisito.OBLIGATORIO
            for req in req_no_cumplidos
        )
        
        # Calcular puntuación
        puntuacion = calcular_puntuacion(
            total=len(requisitos),
            cumplidos=len(req_cumplidos),
            tiene_obligatorio_no_cumplido=tiene_obligatorio_no_cumplido
        )
        
        # Construir resultado
        resultado_fase1 = ResultadoFase1(
            puntuacion=puntuacion,
            descartado=tiene_obligatorio_no_cumplido,
            requisitos_cumplidos=req_cumplidos,
            requisitos_no_cumplidos=req_no_cumplidos,
            requisitos_faltantes=req_faltantes,
            resumen_analisis=resultado_matching.get("analysis_summary", "")
        )
        
        return {"resultado_fase1": resultado_fase1}
    
    return nodo_calcular_puntuacion
```

---

## Construcción del Grafo

```python
def crear_grafo_fase1(
    llm,
    proveedor: str,
    modelo: str,
    embeddings=None
) -> CompiledGraph:
    """
    Construye y compila el grafo de Fase 1.
    
    Returns:
        Grafo compilado listo para ejecutar
    """
    # Crear grafo con estado tipado
    grafo = StateGraph(EstadoFase1)
    
    # Crear nodos
    nodo_extraccion = crear_nodo_extraccion(llm, proveedor, modelo)
    nodo_embedding = crear_nodo_embedding(embeddings)
    nodo_matching = crear_nodo_matching(llm)
    nodo_puntuacion = crear_nodo_puntuacion()
    
    # Añadir nodos al grafo
    grafo.add_node("extraer_requisitos", nodo_extraccion)
    grafo.add_node("embeber_cv", nodo_embedding)
    grafo.add_node("matching_semantico", nodo_matching)
    grafo.add_node("calcular_puntuacion", nodo_puntuacion)
    
    # Definir flujo (aristas)
    grafo.set_entry_point("extraer_requisitos")
    grafo.add_edge("extraer_requisitos", "embeber_cv")
    grafo.add_edge("embeber_cv", "matching_semantico")
    grafo.add_edge("matching_semantico", "calcular_puntuacion")
    grafo.add_edge("calcular_puntuacion", END)
    
    # Compilar
    return grafo.compile()
```

---

## Visualización del Grafo

```
┌──────────────────────────────────────────────────────────────────┐
│                    GRAFO FASE 1                                   │
└──────────────────────────────────────────────────────────────────┘

                    ┌─────────────────────┐
                    │   ENTRY POINT       │
                    └─────────────────────┘
                              │
                              ▼
                    ┌─────────────────────┐
                    │ extraer_requisitos  │
                    │ ─────────────────── │
                    │ Input: oferta       │
                    │ Output: requisitos  │
                    └─────────────────────┘
                              │
                              ▼
                    ┌─────────────────────┐
                    │ embeber_cv          │
                    │ ─────────────────── │
                    │ Input: cv, reqs     │
                    │ Output: evidencia   │
                    └─────────────────────┘
                              │
                              ▼
                    ┌─────────────────────┐
                    │ matching_semantico  │
                    │ ─────────────────── │
                    │ Input: cv, reqs,    │
                    │        evidencia    │
                    │ Output: matches     │
                    └─────────────────────┘
                              │
                              ▼
                    ┌─────────────────────┐
                    │ calcular_puntuacion │
                    │ ─────────────────── │
                    │ Input: matches      │
                    │ Output: resultado   │
                    └─────────────────────┘
                              │
                              ▼
                    ┌─────────────────────┐
                    │        END          │
                    └─────────────────────┘
```

---

## Ejecución del Grafo

### Ejecución Simple

```python
def ejecutar_grafo_fase1(
    grafo: CompiledGraph,
    oferta_trabajo: str,
    cv: str,
    usar_embeddings: bool = True,
    proveedor: str = "openai",
    modelo: str = "gpt-4o",
    api_key: Optional[str] = None
) -> ResultadoFase1:
    """
    Ejecuta el grafo y devuelve el resultado.
    """
    # Estado inicial
    estado_inicial: EstadoFase1 = {
        "oferta_trabajo": oferta_trabajo,
        "cv": cv,
        "usar_embeddings": usar_embeddings,
        "proveedor": proveedor,
        "modelo": modelo,
        "api_key": api_key,
        "requisitos": [],
        "evidencia_semantica": {},
        "resultado_matching": None,
        "resultado_fase1": None,
        "errores": []
    }
    
    # Ejecutar
    estado_final = grafo.invoke(estado_inicial)
    
    return estado_final["resultado_fase1"]
```

### Ejecución con Streaming

```python
def ejecutar_grafo_fase1_streaming(
    grafo: CompiledGraph,
    estado_inicial: EstadoFase1
):
    """
    Ejecuta el grafo con streaming de eventos.
    
    Yields:
        Tuplas (nombre_nodo, estado_parcial)
    """
    for evento in grafo.stream(estado_inicial):
        for nodo, estado in evento.items():
            yield (nodo, estado)
```

**Uso**:
```python
for nodo, estado in ejecutar_grafo_fase1_streaming(grafo, estado):
    print(f"Completado: {nodo}")
    if nodo == "extraer_requisitos":
        print(f"  Requisitos: {len(estado['requisitos'])}")
    elif nodo == "matching_semantico":
        print(f"  Matches: {len(estado['resultado_matching']['matches'])}")
```

---

## Justificación de Diseño

### ¿Por qué LangGraph?

| Alternativa | Problema |
|-------------|----------|
| Funciones secuenciales | No hay streaming de eventos |
| Async/await | Complejidad innecesaria |
| **LangGraph** | ✅ Streaming por nodo, estado tipado |

### ¿Por qué factories para nodos?

```python
# Sin factory: el LLM tendría que pasarse en el estado
def nodo_extraccion(estado):
    llm = estado["llm"]  # ❌ Contamina el estado

# Con factory: la configuración está encapsulada
def crear_nodo_extraccion(llm):
    def nodo(estado):
        # llm está capturado en el closure ✅
        ...
    return nodo
```

### ¿Por qué TypedDict?

- Documenta la estructura del estado
- IDEs pueden autocompletar
- Errores de tipo detectados antes

### ¿Por qué grafo lineal?

El flujo de Fase 1 es naturalmente secuencial:
1. Extraer requisitos
2. Indexar CV
3. Evaluar requisitos
4. Calcular puntuación

No hay bifurcaciones condicionales complejas que justifiquen un grafo más elaborado.

