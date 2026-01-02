# Buenas Prácticas Implementadas

## Introducción

Este documento detalla las buenas prácticas de desarrollo de software implementadas en Velora, explicando el razonamiento detrás de cada decisión.

---

## 1. Principio de Responsabilidad Única (SRP)

### Definición
Cada clase o módulo debe tener una única razón para cambiar.

### Implementación en Velora

```
backend/
├── nucleo/
│   ├── analisis/analizador.py    → Solo análisis de CV
│   ├── entrevista/entrevistador.py → Solo entrevista
│   └── historial/asistente.py    → Solo RAG historial
├── infraestructura/
│   ├── extraccion/pdf.py         → Solo extraer PDFs
│   ├── extraccion/web.py         → Solo scraping web
│   └── llm/llm_proveedor.py      → Solo crear LLMs
└── utilidades/
    ├── logger.py                 → Solo logging
    ├── procesamiento.py          → Solo cálculos
    └── normalizacion.py          → Solo normalización
```

**¿Por qué?**: Si cambia la forma de extraer PDFs, solo tocamos `pdf.py`. El resto del sistema no se ve afectado.

---

## 2. Inyección de Dependencias

### Definición
Las dependencias se pasan desde fuera, no se crean internamente.

### Ejemplo en Velora

```python
# ❌ MAL: Crea sus propias dependencias
class AnalizadorFase1:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o")  # Acoplado a OpenAI

# ✅ BIEN: Recibe dependencias desde fuera
class AnalizadorFase1:
    def __init__(self, llm, proveedor: str, modelo: str):
        self._llm = llm  # Puede ser cualquier LLM
        self._proveedor = proveedor
```

**¿Por qué?**: Permite cambiar entre OpenAI, Google o Anthropic sin modificar `AnalizadorFase1`.

---

## 3. Configuración Centralizada

### Definición
Todos los parámetros configurables en un solo lugar.

### Implementación en Velora

```python
# backend/infraestructura/llm/hiperparametros.py

@dataclass
class HiperparametrosLLM:
    temperature: float
    top_p: float
    max_tokens: int

# Configuraciones predefinidas
FASE1_EXTRACCION = HiperparametrosLLM(temperature=0.0, top_p=0.1, max_tokens=2000)
FASE2_ENTREVISTA = HiperparametrosLLM(temperature=0.3, top_p=0.7, max_tokens=500)
```

**¿Por qué?**: Si queremos ajustar la temperatura de Fase 1, hay UN solo lugar donde cambiarla.

---

## 4. Prompts como Recursos

### Definición
Los prompts son configuración, no código. Se mantienen separados.

### Implementación en Velora

```python
# backend/recursos/prompts.py

PROMPT_EXTRACCION_REQUISITOS = """
INSTRUCCIONES DE EXTRACCIÓN:
1. Extrae TODOS los requisitos de la oferta de trabajo
2. Clasifica cada requisito como 'obligatory' u 'optional'
...
"""

PROMPT_MATCHING_CV = """
CONTEXTO TEMPORAL CRÍTICO:
- Fecha del sistema: {fecha_sistema}
- Año de referencia: {anio_sistema}
...
"""
```

**¿Por qué?**: 
- Fácil de iterar y mejorar prompts sin tocar lógica
- Permite evaluación A/B de diferentes prompts
- Clara separación entre "qué hacer" (código) y "cómo pedirlo" (prompt)

---

## 5. Validación de Datos con Pydantic

### Definición
Validar todos los datos de entrada y salida con tipos estrictos.

### Implementación en Velora

```python
from pydantic import BaseModel, Field
from typing import Literal, Optional

class Requisito(BaseModel):
    descripcion: str = Field(..., min_length=1, alias="description")
    tipo: Literal["obligatory", "optional"] = Field(..., alias="type")
    cumplido: bool = Field(default=False, alias="fulfilled")
    evidencia: Optional[str] = Field(None, alias="evidence")
    confianza: Optional[Literal["high", "medium", "low"]] = Field(None, alias="confidence")
    puntuacion_semantica: Optional[float] = Field(None, alias="semantic_score", ge=0, le=1)
```

**¿Por qué?**:
- Errores detectados inmediatamente, no en producción
- Structured Output garantizado del LLM
- Auto-documentación del código

---

## 6. Logging Estructurado

### Definición
Registrar eventos del sistema de forma consistente y útil.

### Implementación en Velora

```python
# backend/utilidades/logger.py

class RegistroOperacional:
    """Singleton para logging consistente."""
    
    def log_fase1(self, mensaje: str, nivel: str = "info"):
        prefijo = f"{Colores.AZUL}[FASE 1]{Colores.RESET}"
        self._log(f"{prefijo} {mensaje}", nivel)
    
    def log_fase2(self, mensaje: str, nivel: str = "info"):
        prefijo = f"{Colores.VERDE}[FASE 2]{Colores.RESET}"
        self._log(f"{prefijo} {mensaje}", nivel)
```

**¿Por qué?**:
- Fácil identificar qué fase generó cada mensaje
- Colores para rápida identificación visual
- Nivel de log configurable

---

## 7. Manejo de Errores Graceful

### Definición
Capturar errores sin que el sistema colapse, proporcionando fallbacks.

### Implementación en Velora

```python
# backend/infraestructura/extraccion/web.py

def extraer_oferta_web(url: str) -> str:
    """Extrae contenido de URL con fallback."""
    
    # Intento 1: requests (rápido)
    try:
        resultado = _scrape_con_requests(url)
        if resultado and parece_oferta_trabajo(resultado):
            return resultado
    except Exception as e:
        logger.log_advertencia(f"Nivel 1 falló: {e}")
    
    # Intento 2: Playwright (completo)
    try:
        resultado = _scrape_con_navegador(url)
        if resultado:
            return resultado
    except Exception as e:
        logger.log_error(f"Nivel 2 falló: {e}")
    
    return ""  # Graceful degradation
```

**¿Por qué?**: El sistema sigue funcionando aunque falle una parte.

---

## 8. Fallback de Proveedores

### Definición
Si un proveedor no está disponible, usar otro automáticamente.

### Implementación en Velora

```python
# backend/infraestructura/llm/embedding_proveedor.py

def obtener_proveedor_fallback(proveedor_llm: str) -> str:
    """Si Anthropic (sin embeddings), usa OpenAI o Google."""
    
    if proveedor_llm == "anthropic":
        # Anthropic no tiene embeddings
        if os.getenv("OPENAI_API_KEY"):
            return "openai"
        elif os.getenv("GOOGLE_API_KEY"):
            return "google"
    
    return proveedor_llm  # Mantener original si soporta embeddings
```

**¿Por qué?**: El usuario no tiene que saber que Anthropic no ofrece embeddings.

---

## 9. Documentación en Código

### Definición
Docstrings claros que explican qué hace cada función/clase.

### Implementación en Velora

```python
def extraer_requisitos(self, oferta_trabajo: str) -> List[dict]:
    """
    Extrae requisitos de una oferta de trabajo usando LLM.
    
    El proceso usa Structured Output para garantizar el formato
    de respuesta, con temperatura 0.0 para determinismo.
    
    Args:
        oferta_trabajo: Texto completo de la oferta de trabajo.
    
    Returns:
        Lista de diccionarios con claves:
        - 'description': Texto del requisito
        - 'type': 'obligatory' u 'optional'
    
    Raises:
        ValueError: Si la oferta está vacía.
    
    Example:
        >>> requisitos = analizador.extraer_requisitos("5 años Python...")
        >>> requisitos[0]
        {'description': '5 años de experiencia en Python', 'type': 'obligatory'}
    """
```

**¿Por qué?**: El código se documenta a sí mismo.

---

## 10. Type Hints Completos

### Definición
Anotaciones de tipo en todas las funciones públicas.

### Implementación en Velora

```python
def evaluar_cv_con_requisitos(
    self,
    cv: str,
    requisitos: List[dict],
    evidencia_semantica: Optional[Dict[str, dict]] = None
) -> dict:
    """..."""
```

**¿Por qué?**:
- IDEs pueden detectar errores antes de ejecutar
- Auto-completado inteligente
- Documentación implícita

---

## 11. Separación de Interfaces

### Definición
Las capas superiores no dependen de implementaciones concretas de capas inferiores.

### Implementación en Velora

```python
# backend/__init__.py exporta interfaces limpias
from backend.nucleo import AnalizadorFase1, EntrevistadorFase2
from backend.infraestructura import FabricaLLM, extraer_texto_de_pdf

# El frontend solo importa lo que necesita
from backend import AnalizadorFase1, FabricaLLM
```

**¿Por qué?**: El frontend no necesita saber cómo está organizado el backend internamente.

---

## 12. Inmutabilidad Donde Sea Posible

### Definición
Preferir estructuras de datos que no cambien una vez creadas.

### Implementación en Velora

```python
@dataclass(frozen=True)  # Inmutable
class HiperparametrosLLM:
    temperature: float
    top_p: float
    max_tokens: int

# Una vez creado, no se puede modificar
config = HiperparametrosLLM(0.0, 0.1, 2000)
# config.temperature = 0.5  # ERROR: frozen
```

**¿Por qué?**: Evita bugs por modificaciones accidentales.

---

## 13. Principio DRY (Don't Repeat Yourself)

### Definición
No duplicar código ni lógica.

### Implementación en Velora

```python
# ❌ MAL: Código duplicado
def analizar_con_langgraph(self, ...):
    contexto = obtener_contexto_prompt()
    instrucciones = generar_instrucciones_experiencia()
    # ... resto de lógica

def analizar_tradicional(self, ...):
    contexto = obtener_contexto_prompt()
    instrucciones = generar_instrucciones_experiencia()
    # ... misma lógica duplicada

# ✅ BIEN: Reutilizar
def _inyectar_contexto_temporal(self, prompt: str) -> str:
    contexto = obtener_contexto_prompt()
    instrucciones = generar_instrucciones_experiencia()
    return f"{contexto}\n{instrucciones}\n{prompt}"
```

---

## 14. Consistencia en Nombrado

### Definición
Usar convenciones de nombres consistentes en todo el proyecto.

### Implementación en Velora

```python
# Clases: PascalCase
class AnalizadorFase1:
    ...

# Funciones y métodos: snake_case
def extraer_requisitos(self, oferta_trabajo: str):
    ...

# Constantes: UPPER_SNAKE_CASE
ANIO_REFERENCIA_SISTEMA = 2026

# Variables privadas: prefijo _
self._llm = llm
self._proveedor = proveedor
```

---

## 15. Tests de Funcionalidad

### Definición
Aunque no hay tests unitarios formales, la arquitectura permite pruebas manuales aisladas.

### Implementación en Velora

```python
# Cada componente puede probarse independientemente
from backend import FabricaLLM, AnalizadorFase1

# 1. Probar fábrica de LLM
llm = FabricaLLM.crear_llm("openai", "gpt-4o", api_key="...")

# 2. Probar analizador con ese LLM
analizador = AnalizadorFase1(llm=llm, proveedor="openai", modelo="gpt-4o")
requisitos = analizador.extraer_requisitos("Requisitos: 5 años Python")
print(requisitos)
```

---

## 16. Seguridad

### Definición
Proteger credenciales y datos sensibles.

### Implementación en Velora

```python
# 1. API keys nunca en código
api_key = os.getenv("OPENAI_API_KEY")

# 2. Inputs en Streamlit con type="password"
api_key = st.text_input("API Key", type="password")

# 3. Docker con usuario no-root
RUN useradd --uid 1000 velora
USER velora

# 4. .env en .gitignore
# .gitignore
.env
```

---

## Resumen de Principios

| Principio | Implementación | Beneficio |
|-----------|----------------|-----------|
| SRP | Un archivo = una responsabilidad | Fácil mantenimiento |
| Inyección de dependencias | LLM se pasa, no se crea | Flexibilidad |
| Configuración centralizada | `hiperparametros.py` | Un lugar para cambios |
| Prompts como recursos | `prompts.py` | Iteración rápida |
| Validación Pydantic | Modelos tipados | Errores tempranos |
| Logging estructurado | `RegistroOperacional` | Debugging fácil |
| Manejo de errores | Try/except con fallback | Resiliencia |
| Fallback de proveedores | Anthropic → OpenAI | UX transparente |
| Documentación | Docstrings | Auto-explicativo |
| Type hints | Anotaciones completas | IDE inteligente |
| DRY | Funciones reutilizables | No duplicación |
| Consistencia | Convenciones de nombrado | Legibilidad |
| Seguridad | Env vars, no-root | Protección de datos |

