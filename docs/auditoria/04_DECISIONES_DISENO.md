# Decisiones de Diseño del Sistema Velora

## Introducción

Este documento justifica cada decisión arquitectónica tomada durante el desarrollo. Cada decisión sigue el principio de **reduccionismo**: la solución más simple que cumpla los requisitos.

---

## 1. Elección de Tecnologías

### 1.1 ¿Por qué LangChain?

**Decisión**: Usar LangChain como framework principal para interacción con LLMs.

**Justificación**:
| Alternativa | Problema |
|-------------|----------|
| APIs directas (requests) | Código repetitivo, sin abstracción de proveedores |
| Haystack | Menos ecosistema, peor soporte multi-proveedor |
| LlamaIndex | Enfocado en RAG, no en orquestación general |

**Beneficios de LangChain**:
- Abstracción transparente de proveedores (OpenAI/Google/Anthropic)
- Structured Output nativo con Pydantic
- Integración directa con LangSmith para trazabilidad
- Ecosistema maduro y documentado

### 1.2 ¿Por qué LangGraph?

**Decisión**: Usar LangGraph para orquestación multi-agente.

**Justificación**:
- Control granular sobre el flujo de estados
- Estado tipado (TypedDict) para debugging
- Streaming de eventos por nodo
- Integración nativa con LangSmith

**Cuándo se usa**: Solo en Fase 1 cuando el usuario lo activa. Es opcional.

### 1.3 ¿Por qué FAISS?

**Decisión**: Usar FAISS para búsqueda vectorial.

**Justificación**:
| Alternativa | Problema |
|-------------|----------|
| Chroma | Requiere servidor separado |
| Pinecone | SaaS de pago, dependencia externa |
| Weaviate | Overkill para el caso de uso |

**Beneficios de FAISS**:
- Sin servidor: archivos locales
- Eficiente: búsqueda rápida
- Sin costes: open source
- Portable: funciona en Docker sin configuración

### 1.4 ¿Por qué Streamlit?

**Decisión**: Usar Streamlit como framework de frontend.

**Justificación**:
| Alternativa | Problema |
|-------------|----------|
| FastAPI + React | Doble codebase, más complejidad |
| Gradio | Menos control sobre UI |
| Flask + templates | Más código, sin reactividad |

**Beneficios de Streamlit**:
- Python puro: sin JavaScript
- Desarrollo rápido: prototipado eficiente
- Widgets reactivos: estado gestionado automáticamente
- Docker-friendly: despliegue simple

### 1.5 ¿Por qué Playwright?

**Decisión**: Usar Playwright para scraping web.

**Justificación**:
- Sitios modernos usan JavaScript (React, Vue, Angular)
- BeautifulSoup no ejecuta JavaScript
- Playwright renderiza páginas como un navegador real
- Evita bloqueos anti-bot mejor que Selenium

---

## 2. Decisiones Arquitectónicas

### 2.1 ¿Por qué Arquitectura por Capas?

**Decisión**: Separar el código en capas con responsabilidades únicas.

```
Frontend → Orquestación → Núcleo → Infraestructura
```

**Justificación**:
- **Testabilidad**: Cada capa se puede probar aisladamente
- **Mantenibilidad**: Cambios en infraestructura no afectan lógica de negocio
- **Claridad**: Fácil entender dónde está cada funcionalidad

**Ejemplo concreto**:
Si mañana cambiamos de FAISS a Pinecone:
- Solo modificamos `infraestructura/llm/comparador_semantico.py`
- El `nucleo/analisis/analizador.py` no cambia

### 2.2 ¿Por qué Fábricas (Factory Pattern)?

**Decisión**: Usar `FabricaLLM` y `FabricaEmbeddings` para crear instancias.

**Justificación**:
```python
# SIN Factory (acoplamiento alto)
if provider == "openai":
    llm = ChatOpenAI(model=model)
elif provider == "google":
    llm = ChatGoogleGenerativeAI(model=model)
# Este código se repite en muchos lugares

# CON Factory (centralizado)
llm = FabricaLLM.crear_llm(provider, model)
# Un único punto de cambio
```

**Beneficios**:
- Añadir nuevo proveedor = modificar solo la fábrica
- Lógica de creación en un solo lugar
- Fácil mock en tests

### 2.3 ¿Por qué Singleton para Logger y Contexto Temporal?

**Decisión**: `RegistroOperacional` y `ContextoTemporal` son Singletons.

**Justificación**:
- **Logger**: Un único stream de logs para todo el sistema
- **Contexto Temporal**: Una única fuente de verdad para el año de referencia

```python
# Cualquier módulo obtiene la misma instancia
from backend.utilidades import obtener_registro_operacional
logger = obtener_registro_operacional()  # Siempre el mismo objeto
```

### 2.4 ¿Por qué Aliases Castellano/Inglés?

**Decisión**: Proporcionar nombres en ambos idiomas.

```python
class AnalizadorFase1:
    pass

Phase1Analyzer = AnalizadorFase1  # Alias
```

**Justificación**:
- Código interno en castellano (requisito del proyecto)
- Compatibilidad con código que use nombres en inglés
- Flexibilidad para el equipo

---

## 3. Decisiones de Delegación al LLM

### 3.1 ¿Por qué Delegar Interpretación Semántica al LLM?

**Decisión**: No implementar reglas hardcodeadas para agrupación/separación de requisitos.

**Alternativa rechazada**:
```python
# RECHAZADO: Diccionarios de sinónimos
SINONIMOS = {
    "python": ["python3", "py"],
    "ia": ["inteligencia artificial", "ml", "machine learning"],
}
```

**Justificación**:
| Problema con reglas | Solución con LLM |
|---------------------|------------------|
| Mantenimiento constante | Cero mantenimiento |
| No escala a nuevos dominios | Generaliza automáticamente |
| Falsos positivos/negativos | Contexto semántico completo |

**Implementación**:
Los prompts en `prompts.py` guían al LLM:
```
>>> AGRUPAR COMO 1 REQUISITO (lógica OR):
- Alternativas con "o": "Python, Java o C++"
- Sinónimos: "IA o Machine Learning"
```

El LLM decide, el código solo formatea la entrada/salida.

### 3.2 ¿Por qué Temperature 0 para Fase 1?

**Decisión**: Usar `temperature=0.0` para extracción y matching.

**Justificación**:
- **Reproducibilidad absoluta**: misma entrada = misma salida
- **Determinismo**: evaluaciones consistentes entre ejecuciones
- **Auditabilidad**: se puede verificar el comportamiento

**Cuándo usar temperatura > 0**:
- Fase 2 (entrevista): `temperature=0.3` para variedad en preguntas
- RAG chatbot: `temperature=0.4` para respuestas conversacionales

### 3.3 ¿Por qué Contexto Temporal Explícito?

**Decisión**: Inyectar `ANIO_REFERENCIA_SISTEMA = 2026` en todos los prompts.

**Problema**:
```
CV: "Python: 2020 - Presente"
¿Cuántos años de experiencia?
```

Sin contexto, el LLM podría usar su fecha de corte de entrenamiento.

**Solución**:
```
>>> CONTEXTO TEMPORAL OBLIGATORIO <<<
FECHA ACTUAL DEL SISTEMA: 2 de enero de 2026
ANIO DE REFERENCIA: 2026
```

**Resultado**: `2026 - 2020 = 6 años` (consistente y reproducible).

---

## 4. Decisiones de Structured Output

### 4.1 ¿Por qué Pydantic para Modelos?

**Decisión**: Todos los modelos de datos usan `pydantic.BaseModel`.

**Justificación**:
```python
class Requisito(BaseModel):
    descripcion: str
    tipo: TipoRequisito
    cumplido: bool = False
    puntuacion_semantica: Optional[float] = Field(ge=0, le=1)
```

**Beneficios**:
- Validación automática de tipos
- Valores por defecto declarativos
- Serialización JSON automática
- Compatibilidad con `.with_structured_output()`

### 4.2 ¿Por qué Structured Output en Lugar de Parsing?

**Decisión**: Usar `.with_structured_output(ModeloPydantic)` en lugar de parsear texto.

**Alternativa rechazada**:
```python
# RECHAZADO: Parsing manual
respuesta_texto = llm.invoke(prompt)
import json
datos = json.loads(respuesta_texto)  # Puede fallar
```

**Solución**:
```python
llm_estructurado = llm.with_structured_output(RespuestaExtraccionRequisitos)
resultado = llm_estructurado.invoke(prompt)
# resultado es un objeto tipado, garantizado
```

---

## 5. Decisiones de Persistencia

### 5.1 ¿Por qué JSON para Memoria de Usuario?

**Decisión**: Almacenar evaluaciones en archivos JSON por usuario.

**Alternativa rechazada**:
| Alternativa | Problema |
|-------------|----------|
| SQLite | Overkill para estructura simple |
| PostgreSQL | Requiere servidor |
| Redis | Datos efímeros, no persistentes |

**Justificación**:
- Estructura simple: lista de evaluaciones
- Sin servidor: archivos locales
- Legible: JSON humano-leíble para debugging
- Portable: fácil backup y migración

### 5.2 ¿Por qué Índices FAISS Separados por Usuario?

**Decisión**: `data/vectores/{user_id}/index.faiss`

**Justificación**:
- Aislamiento de datos entre usuarios
- Escalabilidad: cada índice crece independientemente
- Privacidad: fácil eliminar datos de un usuario

---

## 6. Decisiones de API y Configuración

### 6.1 ¿Por qué API Keys en Frontend?

**Decisión**: Las API keys se introducen desde la interfaz web, no desde `.env`.

**Justificación**:
- Flexibilidad: cambiar de proveedor sin reiniciar
- Seguridad: no se guardan en repositorio
- UX: el usuario controla sus credenciales

### 6.2 ¿Por qué Hiperparámetros Centralizados?

**Decisión**: Todos los hiperparámetros en `hiperparametros.py`.

```python
FASE1_EXTRACCION = HiperparametrosLLM(temperature=0.0, top_p=0.1)
FASE1_MATCHING = HiperparametrosLLM(temperature=0.0, top_p=0.1)
FASE2_ENTREVISTA = HiperparametrosLLM(temperature=0.3, top_p=0.9)
```

**Justificación**:
- Configuración en un solo lugar
- Fácil ajustar para nuevos modelos
- Documentación implícita del comportamiento esperado

---

## 7. Decisiones de Streaming

### 7.1 ¿Por qué Streaming Real en Fase 2?

**Decisión**: Las respuestas del entrevistador se muestran token-by-token.

**Justificación**:
- UX: feedback inmediato al usuario
- Naturalidad: simula conversación humana
- Técnico: los LLMs generan tokens secuencialmente

**Implementación**:
```python
def transmitir_pregunta(self, indice):
    chain = prompt | self.llm | StrOutputParser()
    for chunk in chain.stream({}):  # Generator
        yield chunk  # Token por token
```

---

## 8. Decisiones NO Tomadas (Reduccionismo)

### 8.1 No Implementamos Caché de Embeddings

**Razón**: Añade complejidad sin beneficio claro para el caso de uso.

### 8.2 No Implementamos Autenticación de Usuario

**Razón**: Fuera del alcance de la prueba técnica. El `user_id` es identificador simple.

### 8.3 No Implementamos Rate Limiting

**Razón**: Las APIs de LLMs ya tienen sus propios límites. Duplicar lógica.

### 8.4 No Implementamos Tests Unitarios

**Razón**: Fuera del alcance de la prueba técnica. La documentación extensiva compensa.

---

## 9. Resumen de Principios

| Principio | Aplicación |
|-----------|------------|
| **Reduccionismo** | Código mínimo necesario |
| **Delegación al LLM** | Interpretación semántica vía prompts |
| **Determinismo** | Temperature 0 para evaluaciones |
| **Separación de capas** | Responsabilidad única por módulo |
| **Configuración externa** | Hiperparámetros y prompts centralizados |
| **Sin duplicidad** | Una sola fuente de verdad |

---

## Próximo Documento

Continúa con [05_FLUJO_DATOS.md](./05_FLUJO_DATOS.md) para ver cómo fluyen los datos a través del sistema.

