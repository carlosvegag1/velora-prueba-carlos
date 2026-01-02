# Documentación: `backend/utilidades/contexto_temporal.py`

## Información General

| Atributo | Valor |
|----------|-------|
| **Ruta** | `/backend/utilidades/contexto_temporal.py` |
| **Tipo** | Utilidad crítica |
| **Líneas** | ~100 |
| **Propósito** | Gestión del tiempo de referencia |

---

## Propósito

Este archivo es **CRÍTICO** para el funcionamiento correcto del sistema. Define el año de referencia (2026) y proporciona funciones para inyectar contexto temporal en los prompts.

---

## El Problema que Resuelve

### ¿Por qué es necesario?

Los LLMs tienen una **fecha de corte** (cuando fueron entrenados):

| Modelo | Fecha de corte aproximada |
|--------|---------------------------|
| GPT-4 | Septiembre 2021 |
| GPT-4 Turbo | Abril 2023 |
| GPT-4o | Octubre 2023 |
| Claude 3 | Agosto 2023 |

**Problema**:

```
CV: "Python 2020 - Presente"
Requisito: "5 años de experiencia en Python"

Sin contexto temporal:
- LLM piensa: estamos en 2024
- Cálculo: 2024 - 2020 = 4 años
- Resultado: NO CUMPLE ❌

Con contexto temporal (2026):
- LLM sabe: estamos en enero 2026
- Cálculo: 2026 - 2020 = 6 años
- Resultado: CUMPLE ✅
```

---

## Constante Principal

```python
ANIO_SISTEMA = 2026
"""
Año de referencia para todo el sistema.

CRÍTICO: Este valor define el "presente" para el sistema.
Todas las evaluaciones de experiencia se calculan respecto a este año.

Razón: El sistema debe comportarse como si estuviéramos en enero de 2026,
independientemente de cuándo se ejecute realmente.
"""
```

---

## Clase ContextoTemporal

```python
class ContextoTemporal:
    """
    Singleton que proporciona contexto temporal consistente.
    
    Implementa el patrón Singleton para garantizar que todo
    el sistema use el mismo contexto temporal.
    """
    
    _instancia = None
    
    def __new__(cls):
        """Garantiza una única instancia (Singleton)."""
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
            cls._instancia._inicializar()
        return cls._instancia
```

### ¿Qué es un Singleton?

Patrón que garantiza que solo existe UNA instancia de una clase:

```python
ctx1 = ContextoTemporal()
ctx2 = ContextoTemporal()

ctx1 is ctx2  # True - son el mismo objeto
```

**¿Por qué Singleton aquí?**

El contexto temporal debe ser CONSISTENTE en todo el sistema. Si cada componente tuviera su propia instancia, podrían usar años diferentes.

---

### Métodos de la Clase

```python
    def _inicializar(self):
        """Inicializa el contexto con valores por defecto."""
        self._anio_referencia = ANIO_SISTEMA
        self._mes_referencia = 1  # Enero
        self._dia_referencia = 2  # 2 de enero
    
    def obtener_fecha_referencia(self) -> str:
        """
        Devuelve la fecha de referencia formateada.
        
        Returns:
            "2 de enero de 2026"
        """
        meses = [
            "enero", "febrero", "marzo", "abril",
            "mayo", "junio", "julio", "agosto",
            "septiembre", "octubre", "noviembre", "diciembre"
        ]
        return f"{self._dia_referencia} de {meses[self._mes_referencia - 1]} de {self._anio_referencia}"
    
    def obtener_anio_sistema(self) -> int:
        """Devuelve el año de referencia."""
        return self._anio_referencia
```

### Métodos de Cálculo

```python
    def calcular_anios_desde(self, anio_inicio: int) -> int:
        """
        Calcula años transcurridos desde un año hasta el presente (2026).
        
        Args:
            anio_inicio: Año de inicio
            
        Returns:
            Años transcurridos
            
        Example:
            calcular_anios_desde(2020)  # → 6
        """
        return self._anio_referencia - anio_inicio
    
    def calcular_anios_entre(self, anio_inicio: int, anio_fin: int) -> int:
        """
        Calcula años entre dos fechas específicas.
        
        Args:
            anio_inicio: Año de inicio
            anio_fin: Año de fin
            
        Returns:
            Años transcurridos
        """
        return anio_fin - anio_inicio
    
    def interpretar_presente(self) -> int:
        """
        Interpreta 'presente', 'actualidad', 'actual' como el año del sistema.
        
        Returns:
            2026
        """
        return self._anio_referencia
```

---

## Funciones de Acceso Global

Para no tener que instanciar el Singleton cada vez:

```python
def obtener_contexto_prompt() -> str:
    """
    Genera el contexto temporal para inyectar en prompts.
    
    Returns:
        Texto formateado para incluir en el prompt
    """
    ctx = ContextoTemporal()
    
    return f"""
CONTEXTO TEMPORAL CRÍTICO:
==========================
FECHA ACTUAL DEL SISTEMA: {ctx.obtener_fecha_referencia()}
AÑO DE REFERENCIA: {ctx.obtener_anio_sistema()}

IMPORTANTE: Usa SIEMPRE {ctx.obtener_anio_sistema()} como el año actual para 
cualquier cálculo de experiencia o fechas relativas.
"""
```

**Ejemplo de salida**:
```
CONTEXTO TEMPORAL CRÍTICO:
==========================
FECHA ACTUAL DEL SISTEMA: 2 de enero de 2026
AÑO DE REFERENCIA: 2026

IMPORTANTE: Usa SIEMPRE 2026 como el año actual para 
cualquier cálculo de experiencia o fechas relativas.
```

```python
def generar_instrucciones_experiencia() -> str:
    """
    Genera instrucciones detalladas para calcular experiencia.
    
    Returns:
        Instrucciones de cálculo formateadas
    """
    ctx = ContextoTemporal()
    anio = ctx.obtener_anio_sistema()
    
    return f"""
INSTRUCCIONES DE CÁLCULO DE EXPERIENCIA:
========================================

FÓRMULA OBLIGATORIA:
- años_experiencia = {anio} - año_inicio

INTERPRETACIÓN DE "PRESENTE":
- "actualidad", "presente", "actual", "ahora" = {anio}
- "hasta la fecha", "hasta hoy" = {anio}

EJEMPLOS DE CÁLCULO:
1. "Python 2018-2023" = 2023 - 2018 = 5 años
2. "Python desde 2020" = {anio} - 2020 = {anio - 2020} años
3. "Python 2020-actualidad" = {anio} - 2020 = {anio - 2020} años
4. "Python 2015-presente" = {anio} - 2015 = {anio - 2015} años

NUNCA uses el año de tu entrenamiento. USA {anio}.
"""
```

**Ejemplo de salida**:
```
INSTRUCCIONES DE CÁLCULO DE EXPERIENCIA:
========================================

FÓRMULA OBLIGATORIA:
- años_experiencia = 2026 - año_inicio

INTERPRETACIÓN DE "PRESENTE":
- "actualidad", "presente", "actual", "ahora" = 2026
- "hasta la fecha", "hasta hoy" = 2026

EJEMPLOS DE CÁLCULO:
1. "Python 2018-2023" = 2023 - 2018 = 5 años
2. "Python desde 2020" = 2026 - 2020 = 6 años
3. "Python 2020-actualidad" = 2026 - 2020 = 6 años
4. "Python 2015-presente" = 2026 - 2015 = 11 años

NUNCA uses el año de tu entrenamiento. USA 2026.
```

---

## Dónde se Usa

### En el Matching de CV (`analizador.py`)

```python
def evaluar_cv_con_requisitos(self, cv, requisitos, ...):
    # Inyectar contexto temporal
    contexto = obtener_contexto_prompt()
    instrucciones = generar_instrucciones_experiencia()
    
    prompt = f"""
{contexto}

{instrucciones}

CV:
{cv}

Requisitos:
{requisitos}
"""
```

### En el Grafo LangGraph (`grafo_fase1.py`)

```python
def nodo_matching_semantico(estado):
    contexto = obtener_contexto_prompt()
    instrucciones = generar_instrucciones_experiencia()
    
    # Mismo patrón: inyectar en el prompt
```

### En los Prompts (`prompts.py`)

```python
PROMPT_MATCHING_CV = """
...

{contexto_temporal}

{instrucciones_experiencia}

...
"""
```

---

## Casos de Prueba Implícitos

```python
# Caso 1: Experiencia con fecha de fin
cv = "Python 2018-2023"
# Esperado: 5 años (2023 - 2018)

# Caso 2: Experiencia hasta "presente"
cv = "Python desde 2020"
# Esperado: 6 años (2026 - 2020)

# Caso 3: Experiencia con "actualidad"
cv = "Python 2015-actualidad"
# Esperado: 11 años (2026 - 2015)

# Caso 4: Verificar requisito de años
requisito = "5 años de experiencia en Python"
cv = "Python desde 2020"
# 2026 - 2020 = 6 años >= 5 → CUMPLE
```

---

## Diagrama de Uso

```
┌──────────────────────────────────────────────────────────────────┐
│                    SISTEMA VELORA                                 │
│                                                                   │
│   ┌─────────────────────────────────────────────────────────┐    │
│   │              ContextoTemporal (Singleton)                │    │
│   │              ANIO_SISTEMA = 2026                        │    │
│   └─────────────────────────────────────────────────────────┘    │
│                              │                                    │
│              ┌───────────────┼───────────────┐                   │
│              │               │               │                   │
│              ▼               ▼               ▼                   │
│   ┌──────────────┐ ┌──────────────┐ ┌──────────────┐           │
│   │ analizador.py│ │grafo_fase1.py│ │  prompts.py  │           │
│   │              │ │              │ │              │           │
│   │obtener_      │ │obtener_      │ │PROMPT_       │           │
│   │contexto_     │ │contexto_     │ │MATCHING_CV   │           │
│   │prompt()      │ │prompt()      │ │incluye       │           │
│   └──────────────┘ └──────────────┘ │{contexto}    │           │
│              │               │       └──────────────┘           │
│              │               │               │                   │
│              └───────────────┴───────────────┘                   │
│                              │                                    │
│                              ▼                                    │
│              ┌───────────────────────────────┐                   │
│              │           LLM                  │                   │
│              │  "Usa 2026 como año actual"   │                   │
│              └───────────────────────────────┘                   │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## Justificación de Diseño

### ¿Por qué 2026?

El sistema está diseñado para evaluarse en enero de 2026. Este año específico:
- Es futuro respecto a la fecha de corte de los LLMs
- Permite calcular experiencia de forma consistente
- Es la fecha de la prueba técnica

### ¿Por qué Singleton?

**Sin Singleton**:
```python
# Archivo 1
ctx1 = ContextoTemporal()
ctx1._anio_referencia = 2026

# Archivo 2
ctx2 = ContextoTemporal()
ctx2._anio_referencia = 2025  # ¡Inconsistencia!
```

**Con Singleton**:
```python
# Archivo 1
ctx1 = ContextoTemporal()

# Archivo 2
ctx2 = ContextoTemporal()

ctx1 is ctx2  # True - misma instancia, mismo año
```

### ¿Por qué inyectar en cada prompt?

Los LLMs no tienen "memoria" entre llamadas. Cada llamada es independiente:

```python
# Llamada 1: Extracción (no necesita contexto temporal)
llm.invoke("Extrae requisitos de: ...")

# Llamada 2: Matching (SÍ necesita contexto temporal)
llm.invoke("""
CONTEXTO: Estamos en 2026
Evalúa si el CV cumple: ...
""")
```

Sin inyectar el contexto en cada llamada relevante, el LLM usaría su año de entrenamiento.

### ¿Por qué funciones globales?

```python
# Más ergonómico
contexto = obtener_contexto_prompt()

# En lugar de
contexto = ContextoTemporal().obtener_contexto_prompt()
```

Las funciones globales encapsulan el acceso al Singleton.

