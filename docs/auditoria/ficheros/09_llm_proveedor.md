# Documentación: `backend/infraestructura/llm/llm_proveedor.py`

## Información General

| Atributo | Valor |
|----------|-------|
| **Ruta** | `/backend/infraestructura/llm/llm_proveedor.py` |
| **Tipo** | Factory / Fábrica |
| **Líneas** | ~150 |
| **Clase principal** | `FabricaLLM` |

---

## Propósito

Proporciona una **fábrica centralizada** para crear instancias de LLM de diferentes proveedores. Abstrae la complejidad de configuración.

---

## Patrón Factory

### ¿Qué es el Patrón Factory?

Una clase que se encarga de crear objetos de otras clases:

```python
# Sin Factory: cada lugar crea su propio LLM
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

# En archivo 1
llm = ChatOpenAI(model="gpt-4o", temperature=0.0, api_key="...")

# En archivo 2 (duplicación)
llm = ChatOpenAI(model="gpt-4o", temperature=0.0, api_key="...")

# Con Factory: creación centralizada
llm = FabricaLLM.crear_llm("openai", "gpt-4o", temperatura=0.0)
```

---

## Clase FabricaLLM

```python
class FabricaLLM:
    """
    Fábrica centralizada para crear instancias de LLM.
    
    Beneficios:
    - Un solo lugar para configurar proveedores
    - Manejo consistente de errores
    - Fácil añadir nuevos proveedores
    """
```

### Método: `crear_llm`

```python
    @staticmethod
    def crear_llm(
        proveedor: str,
        modelo: str,
        temperatura: float = 0.0,
        api_key: Optional[str] = None,
        **kwargs
    ):
        """
        Crea una instancia de LLM según el proveedor especificado.
        
        Args:
            proveedor: "openai", "google" o "anthropic"
            modelo: Nombre del modelo (ej: "gpt-4o")
            temperatura: 0.0-2.0
            api_key: Clave API (o usa variable de entorno)
            **kwargs: Parámetros adicionales
            
        Returns:
            Instancia de LLM configurada
            
        Raises:
            ValueError: Si el proveedor no es soportado
        """
        proveedor = proveedor.lower()
        
        logger.log_config(f"Creando LLM: {proveedor}/{modelo} (temp={temperatura})")
```

### Creación por Proveedor

```python
        if proveedor == "openai":
            from langchain_openai import ChatOpenAI
            
            return ChatOpenAI(
                model=modelo,
                temperature=temperatura,
                api_key=api_key or os.getenv("OPENAI_API_KEY"),
                **kwargs
            )
```

**OpenAI**: El proveedor más usado. Modelos: gpt-4o, gpt-4-turbo, gpt-3.5-turbo.

```python
        elif proveedor == "google":
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
            except ImportError:
                raise ImportError(
                    "langchain-google-genai no instalado. "
                    "Instala con: pip install langchain-google-genai"
                )
            
            return ChatGoogleGenerativeAI(
                model=modelo,
                temperature=temperatura,
                google_api_key=api_key or os.getenv("GOOGLE_API_KEY"),
                **kwargs
            )
```

**Google**: Modelos Gemini. Nota: usa `google_api_key`, no `api_key`.

```python
        elif proveedor == "anthropic":
            try:
                from langchain_anthropic import ChatAnthropic
            except ImportError:
                raise ImportError(
                    "langchain-anthropic no instalado. "
                    "Instala con: pip install langchain-anthropic"
                )
            
            return ChatAnthropic(
                model=modelo,
                temperature=temperatura,
                anthropic_api_key=api_key or os.getenv("ANTHROPIC_API_KEY"),
                **kwargs
            )
```

**Anthropic**: Modelos Claude. Nota: usa `anthropic_api_key`.

```python
        else:
            raise ValueError(
                f"Proveedor '{proveedor}' no soportado. "
                f"Usa: {FabricaLLM.obtener_proveedores_disponibles()}"
            )
```

---

### Métodos de Información

```python
    @staticmethod
    def obtener_proveedores_disponibles() -> List[str]:
        """Lista de proveedores soportados."""
        return ["openai", "google", "anthropic"]
    
    @staticmethod
    def obtener_proveedor_desde_modelo(modelo: str) -> str:
        """
        Infiere el proveedor a partir del nombre del modelo.
        
        Args:
            modelo: Nombre del modelo
            
        Returns:
            Nombre del proveedor inferido
        """
        modelo_lower = modelo.lower()
        
        if any(x in modelo_lower for x in ["gpt", "o1"]):
            return "openai"
        elif any(x in modelo_lower for x in ["gemini", "palm"]):
            return "google"
        elif any(x in modelo_lower for x in ["claude", "haiku", "sonnet", "opus"]):
            return "anthropic"
        else:
            # Por defecto OpenAI
            return "openai"
```

**Ejemplo de uso**:
```python
proveedor = FabricaLLM.obtener_proveedor_desde_modelo("claude-3-opus")
# → "anthropic"

proveedor = FabricaLLM.obtener_proveedor_desde_modelo("gpt-4-turbo")
# → "openai"
```

```python
    @staticmethod
    def obtener_modelos_disponibles(proveedor: str) -> List[str]:
        """Lista de modelos disponibles para un proveedor."""
        modelos = {
            "openai": ["gpt-4o", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"],
            "google": ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro"],
            "anthropic": ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"]
        }
        return modelos.get(proveedor.lower(), [])
    
    @staticmethod
    def obtener_modelo_por_defecto(proveedor: str) -> str:
        """Modelo por defecto para un proveedor."""
        defaults = {
            "openai": "gpt-4o",
            "google": "gemini-1.5-pro",
            "anthropic": "claude-3-sonnet-20240229"
        }
        return defaults.get(proveedor.lower(), "gpt-4o")
```

---

## Integración con LangSmith

```python
def configurar_langsmith() -> None:
    """
    Configura LangSmith para trazabilidad.
    
    LangSmith registra todas las llamadas a LLM para:
    - Debugging
    - Análisis de costos
    - Evaluación de prompts
    """
    langsmith_key = os.getenv("LANGSMITH_API_KEY")
    
    if langsmith_key:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_PROJECT"] = os.getenv(
            "LANGCHAIN_PROJECT", 
            "velora-evaluator"
        )
        logger.log_config("LangSmith habilitado para trazabilidad")
    else:
        logger.log_advertencia(
            "LANGSMITH_API_KEY no configurada. "
            "Trazabilidad deshabilitada."
        )
```

**¿Cómo funciona?**

1. Si existe `LANGSMITH_API_KEY` en variables de entorno
2. Activa `LANGCHAIN_TRACING_V2`
3. Todas las llamadas a LLM se registran automáticamente
4. Visible en https://smith.langchain.com

---

## Diagrama de Flujo

```
┌──────────────────────────────────────────────────────────────────┐
│                    FabricaLLM.crear_llm()                         │
│                                                                   │
│  proveedor = "openai"                                            │
│  modelo = "gpt-4o"                                               │
│  temperatura = 0.0                                               │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────────┐
                    │ ¿Qué proveedor?     │
                    └─────────────────────┘
                   /          │          \
                  /           │           \
                 ▼            ▼            ▼
        ┌──────────┐  ┌──────────┐  ┌──────────┐
        │ OpenAI   │  │ Google   │  │ Anthropic│
        └──────────┘  └──────────┘  └──────────┘
              │             │             │
              ▼             ▼             ▼
        ┌──────────┐  ┌──────────┐  ┌──────────┐
        │ChatOpenAI│  │ChatGoogle│  │ChatAnthr.│
        │ (LLM)    │  │ (LLM)    │  │ (LLM)    │
        └──────────┘  └──────────┘  └──────────┘
              │             │             │
              └─────────────┴─────────────┘
                            │
                            ▼
                    ┌─────────────────────┐
                    │ Instancia de LLM    │
                    │ lista para usar     │
                    └─────────────────────┘
```

---

## Uso Práctico

### Creación Básica

```python
from backend.infraestructura import FabricaLLM

# OpenAI
llm = FabricaLLM.crear_llm("openai", "gpt-4o")

# Google
llm = FabricaLLM.crear_llm("google", "gemini-1.5-pro")

# Anthropic
llm = FabricaLLM.crear_llm("anthropic", "claude-3-sonnet-20240229")
```

### Con Parámetros

```python
# Determinista (para Fase 1)
llm = FabricaLLM.crear_llm(
    proveedor="openai",
    modelo="gpt-4o",
    temperatura=0.0,
    api_key="sk-..."
)

# Creativo (para Fase 2)
llm = FabricaLLM.crear_llm(
    proveedor="openai",
    modelo="gpt-4o",
    temperatura=0.3
)
```

### Inferir Proveedor

```python
modelo = "claude-3-opus"
proveedor = FabricaLLM.obtener_proveedor_desde_modelo(modelo)
llm = FabricaLLM.crear_llm(proveedor, modelo)
```

---

## Manejo de Errores

### API Key Faltante

```python
# Si no hay API key configurada
llm = FabricaLLM.crear_llm("openai", "gpt-4o")
# → Error al hacer la primera llamada, no al crear
```

### Proveedor No Instalado

```python
# Si langchain-google-genai no está instalado
llm = FabricaLLM.crear_llm("google", "gemini-pro")
# → ImportError con instrucciones de instalación
```

### Proveedor Desconocido

```python
llm = FabricaLLM.crear_llm("azure", "gpt-4")
# → ValueError: Proveedor 'azure' no soportado
```

---

## Justificación de Diseño

### ¿Por qué una Fábrica?

| Sin Fábrica | Con Fábrica |
|-------------|-------------|
| Importar diferentes clases en cada lugar | Un solo punto de importación |
| Repetir configuración | Configuración centralizada |
| Difícil cambiar proveedor | Cambiar un string |
| Cada lugar maneja errores | Manejo de errores centralizado |

### ¿Por qué @staticmethod?

```python
class FabricaLLM:
    @staticmethod
    def crear_llm(...):
        ...
```

- No necesita estado de instancia (`self`)
- Se puede llamar sin crear objeto: `FabricaLLM.crear_llm(...)`
- Semánticamente correcto: es una utilidad, no un objeto con estado

### ¿Por qué imports dentro del método?

```python
if proveedor == "google":
    from langchain_google_genai import ChatGoogleGenerativeAI
```

- **Lazy loading**: Solo importa si se necesita
- **Errores claros**: Si falta el paquete, el error indica qué instalar
- **Menor tiempo de carga**: No importa todos los proveedores al inicio

### ¿Por qué variables de entorno como fallback?

```python
api_key=api_key or os.getenv("OPENAI_API_KEY")
```

- **Flexibilidad**: Pasar explícitamente o usar env var
- **Seguridad**: No hardcodear keys en código
- **Docker**: Fácil inyectar via docker-compose

