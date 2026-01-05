# JUSTIFICACION TECNICA: AUSENCIA DE TOOLS EN EL SISTEMA

Documentacion que fundamenta por que el sistema Velora no implementa tools (herramientas) para sus agentes LLM, basada en evidencia del codigo y la arquitectura del sistema.


## CONTEXTO: QUE SON LAS TOOLS EN SISTEMAS AGENTIVOS

En frameworks como LangChain y LangGraph, las tools son funciones que un agente puede invocar autonomamente durante su razonamiento. El agente decide si usar una tool, cual usar, y como interpretar su resultado.

Ejemplo tipico de uso de tools:
- Agente de busqueda: decide si consultar Google, Wikipedia o una base de datos
- Agente de codigo: decide si ejecutar codigo, leer archivos o hacer git commits
- Agente conversacional: decide si consultar APIs externas o bases de conocimiento


## POR QUE VELORA NO USA TOOLS: EVIDENCIA DEL CODIGO

RAZON 1: FLUJO DETERMINISTA Y PREDECIBLE

El sistema sigue un flujo de ejecucion fijo, no hay decisiones autonomas:

Evidencia en analizador.py (lineas 257-280):
```python
def analizar(self, oferta_trabajo: str, cv: str) -> ResultadoFase1:
    if self.usar_langgraph and self._grafo:
        resultado = self._analizar_con_langgraph(oferta_trabajo, cv)
    else:
        resultado = self._analizar_tradicional(oferta_trabajo, cv)
    return resultado
```

El flujo se decide en tiempo de configuracion (flags del usuario), no en tiempo de ejecucion por el LLM. No hay punto donde el LLM deba elegir entre multiples acciones posibles.


RAZON 2: STRUCTURED OUTPUT REEMPLAZA TOOLS PARA EXTRACCION

Velora usa Structured Output de LangChain en lugar de tools para garantizar respuestas validas:

Evidencia en analizador.py (lineas 73-74):
```python
self.llm_extraccion = self.llm.with_structured_output(RespuestaExtraccionRequisitos)
self.llm_matching = self.llm.with_structured_output(RespuestaMatchingCV)
```

Evidencia en modelos.py (lineas 49-67):
```python
class RespuestaExtraccionRequisitos(BaseModel):
    requirements: List[RequisitoExtraido] = Field(default_factory=list)

class RespuestaMatchingCV(BaseModel):
    matches: List[ResultadoMatching] = Field(...)
    analysis_summary: str = Field(...)
```

El LLM no necesita una tool para "extraer requisitos" porque la extraccion es inherente a su respuesta estructurada. La tool seria redundante.


RAZON 3: EMBEDDINGS SON INFRAESTRUCTURA, NO TOOLS

Los embeddings podrian haberse implementado como tool ("buscar_en_cv"), pero esto seria contraproducente:

Evidencia en comparador_semantico.py (lineas 100-125):
```python
def indexar_cv(self, texto_cv: str) -> int:
    self._chunks = self._dividir_cv_en_chunks(texto_cv)
    self._vectorstore = FAISS.from_texts(self._chunks, self.embeddings)
    return len(self._chunks)

def encontrar_evidencia(self, requisito: str, k: int = 3) -> List[Tuple[str, float]]:
    resultados = self._vectorstore.similarity_search_with_score(requisito, k=k)
    # ...
```

Los embeddings se ejecutan sistematicamente para TODOS los requisitos antes del matching. No hay decision del LLM involucrada. Convertirlos en tool implicaria:
- Overhead de razonamiento del LLM para decidir usarlos
- Posibilidad de que el LLM omita buscar evidencia para algun requisito
- Mayor latencia por ciclo adicional de LLM

El pre-filtrado sistematico es mas eficiente y consistente que la decision autonoma.


RAZON 4: LANGGRAPH USA NODOS, NO TOOLS

LangGraph distingue entre nodos (funciones fijas en el grafo) y tools (funciones invocables por el agente). Velora usa exclusivamente nodos:

Evidencia en grafo_fase1.py (lineas 298-320):
```python
def crear_grafo_fase1(llm, comparador_semantico) -> StateGraph:
    grafo = StateGraph(EstadoFase1)
    
    grafo.add_node("extraer_requisitos", nodo_extraccion)
    grafo.add_node("embeber_cv", nodo_embedding)
    grafo.add_node("matching_semantico", nodo_matching)
    grafo.add_node("calcular_puntuacion", nodo_puntuacion)
    
    grafo.set_entry_point("extraer_requisitos")
    grafo.add_edge("extraer_requisitos", "embeber_cv")
    grafo.add_edge("embeber_cv", "matching_semantico")
    grafo.add_edge("matching_semantico", "calcular_puntuacion")
    grafo.add_edge("calcular_puntuacion", END)
```

El grafo tiene edges fijos entre nodos. No hay conditional_edges basados en decision del LLM. No hay ToolNode. El flujo es deterministico.


RAZON 5: EL LLM SOLO TRANSFORMA DATOS

En Velora, el LLM tiene un rol transformador, no decisor:

- Entrada: oferta de empleo (texto)
- Salida: requisitos estructurados (JSON via Pydantic)

- Entrada: CV + requisitos
- Salida: evaluacion estructurada (matches con fulfilled/evidence)

El LLM no decide QUE hacer, solo COMO transformar la informacion dada.


## COMPARATIVA: SISTEMAS CON TOOLS VS VELORA

SISTEMA CON TOOLS (Agente de investigacion):
```
Usuario: "Investiga sobre Python"
Agente razona: "Necesito buscar informacion"
Agente invoca: tool_buscar_web("Python tutorial")
Agente recibe: resultados de busqueda
Agente razona: "Necesito mas detalles"
Agente invoca: tool_leer_url(url_1)
Agente sintetiza: respuesta final
```

El agente DECIDE que tools usar y cuando.

VELORA (Flujo determinista):
```
Usuario: CV + Oferta
Sistema ejecuta: extraer_requisitos(oferta) --> requisitos
Sistema ejecuta: indexar_cv(cv) --> embeddings
Sistema ejecuta: encontrar_evidencia(requisitos) --> hints
Sistema ejecuta: evaluar_matching(cv, requisitos, hints) --> resultado
```

El sistema EJECUTA pasos predefinidos. El LLM transforma datos pero no decide el flujo.


## CUANDO SERIA APROPIADO AGREGAR TOOLS

Tools serian justificables si Velora necesitara:

1. BUSQUEDA EXTERNA: Verificar certificaciones en registros oficiales
   - Tool: verificar_certificacion_oracle(nombre, numero)
   
2. NAVEGACION WEB: Obtener informacion adicional de LinkedIn
   - Tool: scrape_linkedin_profile(url)
   
3. EJECUCION DE CODIGO: Evaluar conocimientos tecnicos
   - Tool: ejecutar_codigo_candidato(codigo, lenguaje)

4. DECISION CONDICIONAL: Elegir entre multiples estrategias de evaluacion
   - Tool: seleccionar_estrategia_evaluacion(tipo_puesto)

Actualmente, ninguna de estas capacidades es requerida. El sistema evalua informacion estatica (CV + Oferta) sin necesidad de acciones externas.


## CONCLUSION

La ausencia de tools en Velora no es una limitacion sino una decision arquitectonica fundamentada:

1. El flujo es determinista y predefinido
2. Structured Output proporciona extraccion estructurada sin tools
3. Los embeddings son infraestructura sistematica, no decisiones del agente
4. LangGraph orquesta nodos fijos, no tools invocables
5. El LLM transforma datos, no decide acciones

Agregar tools introduciria complejidad innecesaria, overhead de razonamiento y variabilidad no deseada en un proceso que se beneficia de la consistencia y predictibilidad.

