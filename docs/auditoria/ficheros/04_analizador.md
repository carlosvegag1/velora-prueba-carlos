# Documentación: `backend/nucleo/analisis/analizador.py`

## Información General

| Atributo | Valor |
|----------|-------|
| **Ruta** | `/backend/nucleo/analisis/analizador.py` |
| **Tipo** | Componente de núcleo |
| **Líneas** | ~400 |
| **Clase principal** | `AnalizadorFase1` |

---

## Propósito

Este archivo implementa la **lógica central de la Fase 1**: extraer requisitos de una oferta de trabajo y evaluarlos contra el CV de un candidato.

---

## Clase AnalizadorFase1

### Constructor

```python
class AnalizadorFase1:
    """
    Analizador que implementa la Fase 1 del proceso de evaluación.
    
    Responsabilidades:
    - Extraer requisitos de ofertas de trabajo
    - Evaluar CV contra requisitos
    - Calcular puntuación de compatibilidad
    """
    
    def __init__(
        self,
        llm=None,
        proveedor: str = "openai",
        modelo: str = "gpt-4o",
        temperatura: float = 0.0,
        api_key: Optional[str] = None,
        usar_matching_semantico: bool = True,
        usar_langgraph: bool = False
    ):
```

**Parámetros explicados**:

| Parámetro | Tipo | Propósito |
|-----------|------|-----------|
| `llm` | Objeto LLM | LLM pre-configurado (si se proporciona, ignora los siguientes) |
| `proveedor` | str | "openai", "google" o "anthropic" |
| `modelo` | str | Nombre del modelo (ej: "gpt-4o") |
| `temperatura` | float | 0.0 = determinista, más alto = más creativo |
| `api_key` | str | Clave API del proveedor |
| `usar_matching_semantico` | bool | Activar embeddings para mejor matching |
| `usar_langgraph` | bool | Usar orquestación con LangGraph |

### Inicialización Interna

```python
        # Guardar configuración
        self._proveedor = proveedor
        self._modelo = modelo
        self._temperatura = temperatura
        self._api_key = api_key
        
        # Crear LLM si no se proporcionó
        if llm is None:
            self._llm = FabricaLLM.crear_llm(
                proveedor=proveedor,
                modelo=modelo,
                temperatura=temperatura,
                api_key=api_key
            )
        else:
            self._llm = llm
```

**Inyección de dependencias**: Puede recibir un LLM o crearlo internamente.

```python
        # Inicializar comparador semántico si está habilitado
        self._usar_matching_semantico = usar_matching_semantico
        self._comparador_semantico = None
        if usar_matching_semantico:
            self._inicializar_comparador_semantico()
```

---

### Método: `_inicializar_comparador_semantico`

```python
    def _inicializar_comparador_semantico(self):
        """Inicializa el comparador con fallback de proveedor."""
        
        # Anthropic no tiene embeddings, necesitamos fallback
        proveedor_embeddings = self._proveedor
        if not FabricaEmbeddings.soporta_embeddings(self._proveedor):
            proveedor_embeddings = FabricaEmbeddings.obtener_proveedor_fallback(
                self._proveedor
            )
            logger.log_advertencia(
                f"Proveedor {self._proveedor} no soporta embeddings, "
                f"usando {proveedor_embeddings}"
            )
        
        # Crear embeddings
        embeddings = FabricaEmbeddings.crear_embeddings(
            proveedor=proveedor_embeddings,
            api_key=self._api_key
        )
        
        # Crear comparador
        self._comparador_semantico = ComparadorSemantico(embeddings)
```

**Flujo**:
1. Verifica si el proveedor soporta embeddings
2. Si no (Anthropic), busca un fallback (OpenAI o Google)
3. Crea embeddings con el proveedor disponible
4. Inicializa el comparador semántico

---

### Método: `extraer_requisitos`

```python
    def extraer_requisitos(self, oferta_trabajo: str) -> List[dict]:
        """
        Extrae requisitos de una oferta de trabajo.
        
        Args:
            oferta_trabajo: Texto de la oferta
            
        Returns:
            Lista de diccionarios con 'description' y 'type'
        """
        logger.log_fase1("Extrayendo requisitos de la oferta...")
```

**Paso 1: Crear prompt**

```python
        prompt = ChatPromptTemplate.from_messages([
            ("system", PROMPT_EXTRACCION_REQUISITOS),
            ("human", "{job_offer}")
        ])
```

`ChatPromptTemplate` crea un template con variables que se rellenan después.

**Paso 2: Configurar Structured Output**

```python
        # LLM con Structured Output garantizado
        llm_extraccion = self._llm.with_structured_output(
            RespuestaExtraccionRequisitos
        )
```

**¿Qué hace `with_structured_output`?**

```
Sin Structured Output:
    Prompt → LLM → "Requisitos:\n1. Python\n2. Docker..." (texto libre)

Con Structured Output:
    Prompt → LLM → RespuestaExtraccionRequisitos(requirements=[...])
```

El LLM es FORZADO a devolver el formato exacto del modelo Pydantic.

**Paso 3: Ejecutar chain**

```python
        # Crear y ejecutar chain
        chain = prompt | llm_extraccion
        resultado = chain.invoke({"job_offer": oferta_trabajo})
```

El operador `|` (pipe) encadena: prompt → llm → resultado.

**Paso 4: Procesar resultado**

```python
        # Convertir a lista de diccionarios
        requisitos = [
            {
                "description": req.description,
                "type": req.type
            }
            for req in resultado.requirements
        ]
        
        logger.log_fase1(f"Extraídos {len(requisitos)} requisitos")
        return requisitos
```

---

### Método: `_obtener_evidencia_semantica`

```python
    def _obtener_evidencia_semantica(
        self, 
        cv: str, 
        requisitos: List[dict]
    ) -> Dict[str, dict]:
        """
        Usa embeddings para encontrar evidencia relevante en el CV.
        """
        if not self._comparador_semantico:
            return {}
        
        logger.log_fase1("Indexando CV con embeddings...")
        
        # Indexar el CV (dividir en chunks y crear vectores)
        self._comparador_semantico.indexar_cv(cv)
        
        # Buscar evidencia para cada requisito
        evidencia = {}
        for req in requisitos:
            descripcion = req["description"].lower()
            resultado = self._comparador_semantico.encontrar_evidencia(
                requisito=req["description"],
                k=2  # Top 2 chunks más relevantes
            )
            if resultado:
                evidencia[descripcion] = resultado
        
        return evidencia
```

**¿Cómo funciona la búsqueda semántica?**

```
CV: "He trabajado 6 años como desarrollador Python en Django..."

                    ┌──────────────┐
                    │   INDEXAR    │
                    └──────────────┘
                          │
                          ▼
            ┌──────────────────────────┐
            │   FAISS Index            │
            │   [0.12, -0.45, ...]     │  ← Vector del CV chunk 1
            │   [0.08, -0.32, ...]     │  ← Vector del CV chunk 2
            │   ...                     │
            └──────────────────────────┘

Requisito: "5 años de experiencia en Python"
                          │
                          ▼
            ┌──────────────────────────┐
            │   BUSCAR                  │
            │   Vector del requisito    │
            │   [0.11, -0.43, ...]     │
            └──────────────────────────┘
                          │
                          ▼
            Chunk más similar: "...6 años como desarrollador Python..."
```

---

### Método: `evaluar_cv_con_requisitos`

```python
    def evaluar_cv_con_requisitos(
        self,
        cv: str,
        requisitos: List[dict],
        evidencia_semantica: Optional[Dict[str, dict]] = None
    ) -> dict:
        """
        Evalúa un CV contra una lista de requisitos.
        
        CRÍTICO: Inyecta contexto temporal para cálculos correctos de experiencia.
        """
```

**Paso 1: Obtener contexto temporal**

```python
        # Contexto temporal OBLIGATORIO
        from backend.utilidades import (
            obtener_contexto_prompt,
            generar_instrucciones_experiencia
        )
        
        contexto_temporal = obtener_contexto_prompt()
        instrucciones_experiencia = generar_instrucciones_experiencia()
```

**¿Por qué es crítico?**

Sin contexto temporal:
- LLM piensa que estamos en 2024 (su fecha de corte)
- "Python 2020-Presente" = 4 años

Con contexto temporal (2026):
- LLM sabe que estamos en enero 2026
- "Python 2020-Presente" = 6 años

**Paso 2: Construir texto de requisitos con pistas semánticas**

```python
        # Construir texto de requisitos
        texto_requisitos = ""
        for req in requisitos:
            linea = f"- [{req['type'].upper()}] {req['description']}"
            
            # Añadir pista semántica si existe
            if evidencia_semantica:
                key = req['description'].lower()
                if key in evidencia_semantica:
                    ev = evidencia_semantica[key]
                    pista = ev.get('text', '')[:100]
                    linea += f"\n  [PISTA SEMÁNTICA: \"{pista}...\"]"
            
            texto_requisitos += linea + "\n"
```

**Ejemplo de texto generado**:

```
- [OBLIGATORY] 5 años de experiencia en Python
  [PISTA SEMÁNTICA: "Desarrollador Python Senior desde 2020..."]
- [OBLIGATORY] Conocimientos de Docker
- [OPTIONAL] Experiencia con LangChain
```

Las pistas semánticas ayudan al LLM a encontrar la evidencia correcta.

**Paso 3: Crear prompt completo**

```python
        # Crear prompt con contexto temporal
        prompt = ChatPromptTemplate.from_messages([
            ("system", PROMPT_MATCHING_CV),
            ("human", f"""
{contexto_temporal}

{instrucciones_experiencia}

## CV DEL CANDIDATO:
{cv}

## REQUISITOS A EVALUAR:
{texto_requisitos}
""")
        ])
```

**Paso 4: Ejecutar con Structured Output**

```python
        llm_matching = self._llm.with_structured_output(RespuestaMatchingCV)
        chain = prompt | llm_matching
        resultado = chain.invoke({})
        
        return {
            "matches": [m.model_dump() for m in resultado.matches],
            "analysis_summary": resultado.analysis_summary
        }
```

---

### Método Principal: `analizar`

```python
    def analizar(
        self,
        cv: str,
        oferta_trabajo: str
    ) -> ResultadoFase1:
        """
        Ejecuta el análisis completo de Fase 1.
        
        Proceso:
        1. Extraer requisitos de la oferta
        2. Obtener evidencia semántica (opcional)
        3. Evaluar CV contra requisitos
        4. Calcular puntuación
        """
        logger.log_fase1("="*50)
        logger.log_fase1("INICIANDO ANÁLISIS FASE 1")
        logger.log_fase1("="*50)
```

**Flujo con LangGraph (si está habilitado)**:

```python
        if self._usar_langgraph and self._grafo:
            return self._analizar_con_langgraph(cv, oferta_trabajo)
        
        return self._analizar_tradicional(cv, oferta_trabajo)
```

**Flujo tradicional**:

```python
    def _analizar_tradicional(
        self,
        cv: str,
        oferta_trabajo: str
    ) -> ResultadoFase1:
        """Implementación tradicional (sin LangGraph)."""
        
        # 1. Extraer requisitos
        requisitos = self.extraer_requisitos(oferta_trabajo)
        
        if not requisitos:
            return ResultadoFase1(
                puntuacion=0.0,
                descartado=True,
                resumen_analisis="No se pudieron extraer requisitos"
            )
        
        # 2. Obtener evidencia semántica
        evidencia_semantica = {}
        if self._usar_matching_semantico:
            evidencia_semantica = self._obtener_evidencia_semantica(
                cv, requisitos
            )
        
        # 3. Evaluar CV
        resultado_matching = self.evaluar_cv_con_requisitos(
            cv, requisitos, evidencia_semantica
        )
        
        # 4. Procesar resultados
        return self._procesar_resultados(
            requisitos,
            resultado_matching,
            evidencia_semantica
        )
```

---

### Método: `_procesar_resultados`

```python
    def _procesar_resultados(
        self,
        requisitos: List[dict],
        resultado_matching: dict,
        evidencia_semantica: Dict[str, dict]
    ) -> ResultadoFase1:
        """Procesa los resultados del matching y calcula puntuación."""
        
        # Convertir matches a objetos Requisito
        req_cumplidos, req_no_cumplidos, req_faltantes, procesados = \
            procesar_coincidencias(
                resultado_matching["matches"],
                requisitos,
                evidencia_semantica
            )
        
        # Agregar requisitos no procesados por el LLM
        req_no_cumplidos = agregar_requisitos_no_procesados(
            requisitos, procesados, req_no_cumplidos, evidencia_semantica
        )
        
        # Verificar si hay obligatorio no cumplido
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
        
        return ResultadoFase1(
            puntuacion=puntuacion,
            descartado=tiene_obligatorio_no_cumplido,
            requisitos_cumplidos=req_cumplidos,
            requisitos_no_cumplidos=req_no_cumplidos,
            requisitos_faltantes=req_faltantes,
            resumen_analisis=resultado_matching.get("analysis_summary", "")
        )
```

---

### Método: `analizar_streaming`

```python
    def analizar_streaming(
        self,
        cv: str,
        oferta_trabajo: str
    ):
        """
        Versión con streaming para feedback en tiempo real.
        
        Yields:
            Tuplas (tipo_evento, datos)
        """
        yield ("inicio", {"mensaje": "Iniciando análisis..."})
        
        # Extracción
        yield ("extraccion_inicio", {"mensaje": "Extrayendo requisitos..."})
        requisitos = self.extraer_requisitos(oferta_trabajo)
        yield ("extraccion_fin", {"requisitos": len(requisitos)})
        
        # Indexación semántica
        if self._usar_matching_semantico:
            yield ("indexacion_inicio", {"mensaje": "Indexando CV..."})
            evidencia = self._obtener_evidencia_semantica(cv, requisitos)
            yield ("indexacion_fin", {"chunks": len(evidencia)})
        
        # Matching
        yield ("matching_inicio", {"mensaje": "Evaluando requisitos..."})
        resultado_matching = self.evaluar_cv_con_requisitos(
            cv, requisitos, evidencia
        )
        yield ("matching_fin", {"matches": len(resultado_matching["matches"])})
        
        # Resultado final
        resultado = self._procesar_resultados(requisitos, resultado_matching, evidencia)
        yield ("fin", {"resultado": resultado})
```

---

## Diagrama del Flujo de Análisis

```
                    ┌─────────────────────┐
                    │   analizar()        │
                    └─────────────────────┘
                              │
                              ▼
                    ┌─────────────────────┐
                    │ extraer_requisitos()│
                    │ - Prompt template   │
                    │ - Structured Output │
                    └─────────────────────┘
                              │
                              ▼
                    ┌─────────────────────┐
                    │ _obtener_evidencia_ │
                    │ _semantica()        │
                    │ - Dividir CV chunks │
                    │ - Crear embeddings  │
                    │ - Buscar similares  │
                    └─────────────────────┘
                              │
                              ▼
                    ┌─────────────────────┐
                    │ evaluar_cv_con_     │
                    │ requisitos()        │
                    │ - Contexto temporal │
                    │ - Pistas semánticas │
                    │ - Structured Output │
                    └─────────────────────┘
                              │
                              ▼
                    ┌─────────────────────┐
                    │ _procesar_          │
                    │ resultados()        │
                    │ - Clasificar reqs   │
                    │ - Calcular puntuac. │
                    └─────────────────────┘
                              │
                              ▼
                    ┌─────────────────────┐
                    │   ResultadoFase1    │
                    └─────────────────────┘
```

---

## Justificación de Diseño

### ¿Por qué temperatura 0.0?

La extracción y matching requieren **determinismo**. La misma oferta debe producir siempre los mismos requisitos.

### ¿Por qué Structured Output?

Garantiza que el LLM devuelve EXACTAMENTE el formato esperado. Sin esto, tendríamos que parsear texto libre y manejar errores de formato.

### ¿Por qué contexto temporal?

Los LLMs tienen una fecha de corte. Sin indicarles la fecha actual, calcularían mal los años de experiencia.

### ¿Por qué pistas semánticas?

Reducen el trabajo del LLM y mejoran la precisión. En lugar de buscar en todo el CV, el LLM ya sabe dónde mirar.

### ¿Por qué dos modos (tradicional vs LangGraph)?

- **Tradicional**: Simple, directo, fácil de debuggear
- **LangGraph**: Mejor trazabilidad, eventos por nodo, preparado para flujos complejos

