# Programación Orientada a Objetos en Velora

## Introducción

Este documento explica los conceptos de Programación Orientada a Objetos (POO) que se utilizan en el sistema Velora, con ejemplos directos del código.

---

## 1. Clases y Objetos

### 1.1 ¿Qué es una Clase?

Una **clase** es una plantilla o molde para crear objetos. Define:
- **Atributos**: Datos que almacena el objeto
- **Métodos**: Funciones que puede ejecutar el objeto

```python
class Requisito:
    """Clase que representa un requisito de una oferta."""
    
    def __init__(self, descripcion, tipo):
        """Constructor: se ejecuta al crear el objeto."""
        self.descripcion = descripcion  # Atributo
        self.tipo = tipo                # Atributo
        self.cumplido = False           # Atributo con valor inicial
    
    def marcar_cumplido(self, evidencia):
        """Método: acción que puede hacer el objeto."""
        self.cumplido = True
        self.evidencia = evidencia
```

### 1.2 ¿Qué es un Objeto?

Un **objeto** es una instancia de una clase:

```python
# Crear objetos (instancias) de la clase Requisito
req1 = Requisito("5 años Python", "obligatory")
req2 = Requisito("Docker", "optional")

# Usar métodos
req1.marcar_cumplido("CV menciona 6 años de Python")

# Acceder a atributos
print(req1.descripcion)  # "5 años Python"
print(req1.cumplido)     # True
```

---

## 2. El Constructor `__init__`

### 2.1 Propósito

El método `__init__` se ejecuta **automáticamente** cuando se crea un objeto:

```python
class AnalizadorFase1:
    def __init__(
        self,
        proveedor: str = None,
        nombre_modelo: str = None,
        api_key: str = None
    ):
        """
        Inicializa el analizador con configuración del LLM.
        
        self: Referencia al objeto que se está creando
        """
        self.proveedor = proveedor          # Guardamos en el objeto
        self._api_key = api_key             # _ indica "privado"
        self._registro = obtener_registro() # Inicializar componentes
```

### 2.2 Parámetros del Constructor

```python
# Valores por defecto permiten uso flexible
analizador1 = AnalizadorFase1()  # Usa defaults
analizador2 = AnalizadorFase1(proveedor="openai", nombre_modelo="gpt-4o")
```

---

## 3. `self` - La Referencia al Objeto

### 3.1 ¿Qué es `self`?

`self` es la referencia al objeto actual. Es el **primer parámetro** de todos los métodos de instancia:

```python
class EntrevistadorFase2:
    def __init__(self):
        self._nombre_candidato = ""  # Atributo de instancia
    
    def inicializar_entrevista(self, nombre_candidato):
        # self._nombre_candidato: atributo del objeto
        # nombre_candidato: parámetro del método
        self._nombre_candidato = nombre_candidato
        return self._generar_saludo()  # Llamar otro método
    
    def _generar_saludo(self):
        return f"Hola {self._nombre_candidato}"
```

### 3.2 Atributos de Instancia vs Clase

```python
class Configuracion:
    # Atributo de CLASE (compartido por todos)
    VERSION = "3.1.0"
    
    def __init__(self, usuario):
        # Atributo de INSTANCIA (único para cada objeto)
        self.usuario = usuario

# Uso
config1 = Configuracion("carlos")
config2 = Configuracion("marta")

print(config1.usuario)     # "carlos"
print(config2.usuario)     # "marta"
print(Configuracion.VERSION)  # "3.1.0" (atributo de clase)
```

---

## 4. Convenciones de Nomenclatura

### 4.1 Privacidad por Convención

Python no tiene privacidad real, usa convenciones:

```python
class MiClase:
    def __init__(self):
        self.publico = "Acceso libre"           # Público
        self._protegido = "Uso interno"         # "Protegido" (convención)
        self.__privado = "Muy privado"          # "Privado" (name mangling)
    
    # Método público
    def metodo_publico(self):
        pass
    
    # Método "privado" (convención)
    def _metodo_interno(self):
        pass
```

**En Velora**:
- `_registro`: Atributo interno del analizador
- `_vectorstore`: Almacén vectorial interno
- `_historial_conversacion`: Lista interna del entrevistador

---

## 5. Patrones de Diseño en Velora

### 5.1 Singleton (Instancia Única)

Garantiza que solo exista **una instancia** de una clase:

```python
class RegistroOperacional:
    """Logger único para todo el sistema."""
    
    _instancia: Optional['RegistroOperacional'] = None
    _inicializado: bool = False
    
    def __new__(cls) -> 'RegistroOperacional':
        """Se ejecuta ANTES de __init__."""
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
        return cls._instancia
    
    def __init__(self):
        if RegistroOperacional._inicializado:
            return  # Ya inicializado, no hacer nada
        RegistroOperacional._inicializado = True
        # Inicialización real...

# Uso: siempre obtienes la misma instancia
logger1 = RegistroOperacional()
logger2 = RegistroOperacional()
print(logger1 is logger2)  # True
```

**¿Por qué?**: Un único logger para todo el sistema garantiza consistencia.

### 5.2 Factory (Fábrica)

Crea objetos sin exponer la lógica de creación:

```python
class FabricaLLM:
    """Fábrica para crear LLMs de diferentes proveedores."""
    
    @staticmethod
    def crear_llm(proveedor: str, nombre_modelo: str, api_key: str):
        """Método de fábrica."""
        if proveedor == "openai":
            return ChatOpenAI(model=nombre_modelo, api_key=api_key)
        elif proveedor == "google":
            return ChatGoogleGenerativeAI(model=nombre_modelo)
        elif proveedor == "anthropic":
            return ChatAnthropic(model=nombre_modelo)
        raise ValueError(f"Proveedor no válido: {proveedor}")

# Uso: el cliente no sabe qué clase concreta se crea
llm = FabricaLLM.crear_llm("openai", "gpt-4o", api_key)
```

**¿Por qué?**: Centraliza la creación y permite cambiar la implementación sin afectar el código cliente.

### 5.3 Dataclass (Clase de Datos)

Para clases que principalmente almacenan datos:

```python
from dataclasses import dataclass

@dataclass(frozen=True)  # frozen=True hace la clase inmutable
class HiperparametrosLLM:
    """Configuración de hiperparámetros."""
    temperature: float
    top_p: Optional[float] = None
    max_tokens: Optional[int] = None
    
    def to_dict(self) -> dict:
        resultado = {"temperature": self.temperature}
        if self.top_p is not None:
            resultado["top_p"] = self.top_p
        return resultado

# Uso
config = HiperparametrosLLM(temperature=0.0, top_p=0.95)
print(config.temperature)  # 0.0
```

**Beneficios**:
- `__init__` generado automáticamente
- `frozen=True`: Objeto inmutable (no se puede modificar)

---

## 6. Pydantic: Modelos con Validación

### 6.1 BaseModel

Pydantic extiende dataclasses con **validación automática**:

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class Requisito(BaseModel):
    """Modelo Pydantic con validación."""
    
    descripcion: str = Field(..., alias="description")
    tipo: str = Field(..., alias="type")
    cumplido: bool = Field(default=False, alias="fulfilled")
    evidencia: Optional[str] = Field(None, alias="evidence")
    puntuacion_semantica: Optional[float] = Field(
        None, 
        alias="semantic_score",
        ge=0,  # Mayor o igual a 0
        le=1   # Menor o igual a 1
    )
    
    class Config:
        populate_by_name = True  # Permite usar nombre o alias

# Uso con validación automática
req = Requisito(
    descripcion="5 años Python",
    tipo="obligatory"
)
# Si pasas puntuacion_semantica=1.5, lanza error de validación
```

### 6.2 Structured Output

El LLM puede responder directamente con objetos Pydantic:

```python
class RespuestaExtraccionRequisitos(BaseModel):
    """Schema para respuesta del LLM."""
    requirements: List[RequisitoExtraido] = Field(default_factory=list)

# Uso con LangChain
llm_estructurado = llm.with_structured_output(RespuestaExtraccionRequisitos)
resultado = llm_estructurado.invoke(prompt)
# resultado es un objeto RespuestaExtraccionRequisitos validado
```

---

## 7. Enumeraciones (Enum)

```python
from enum import Enum

class TipoRequisito(str, Enum):
    """Clasificación de requisitos."""
    OBLIGATORIO = "obligatory"
    DESEABLE = "optional"

class NivelConfianza(str, Enum):
    """Nivel de certeza en evaluación."""
    ALTO = "high"
    MEDIO = "medium"
    BAJO = "low"

# Uso
req_tipo = TipoRequisito.OBLIGATORIO
print(req_tipo.value)  # "obligatory"
print(req_tipo.name)   # "OBLIGATORIO"
```

**¿Por qué Enum?**:
- Valores limitados y conocidos
- Evita errores tipográficos
- Autocompletado del IDE

---

## 8. Herencia y Composición

### 8.1 Herencia (str, Enum)

```python
class TipoRequisito(str, Enum):
    # Hereda de str Y de Enum
    # Permite usar el enum como string
    pass
```

### 8.2 Composición (Preferida en Velora)

En lugar de heredar, Velora usa **composición**:

```python
class AnalizadorFase1:
    def __init__(self):
        # Composición: tiene un comparador (no hereda de él)
        self.comparador_semantico = ComparadorSemantico()
        self._registro = obtener_registro_operacional()
```

**¿Por qué composición?**: Más flexible, menos acoplamiento.

---

## 9. Métodos Estáticos y de Clase

### 9.1 @staticmethod

```python
class FabricaLLM:
    @staticmethod
    def crear_llm(proveedor, modelo):
        """No necesita self ni cls."""
        pass

# Llamada sin instancia
FabricaLLM.crear_llm("openai", "gpt-4")
```

### 9.2 @classmethod

```python
class ConfiguracionHiperparametros:
    _CONFIGS = {
        "phase1_extraction": HiperparametrosLLM(temperature=0.0)
    }
    
    @classmethod
    def obtener_config(cls, contexto: str):
        """cls es la clase, no la instancia."""
        return cls._CONFIGS.get(contexto)

# Llamada
config = ConfiguracionHiperparametros.obtener_config("phase1_extraction")
```

### 9.3 @property

```python
class AlmacenVectorial:
    def __init__(self):
        self._vectorstore = None
    
    @property
    def esta_inicializado(self) -> bool:
        """Accesible como atributo."""
        return self._vectorstore is not None
    
    @property
    def cantidad_documentos(self) -> int:
        if self._vectorstore is None:
            return 0
        return self._vectorstore.index.ntotal

# Uso: como atributos, no como métodos
almacen = AlmacenVectorial()
if almacen.esta_inicializado:      # Sin paréntesis
    print(almacen.cantidad_documentos)  # Sin paréntesis
```

---

## 10. TypedDict

Para diccionarios con estructura conocida:

```python
from typing import TypedDict, List, Optional

class EstadoFase1(TypedDict):
    """Estado tipado del grafo LangGraph."""
    oferta_trabajo: str
    cv: str
    requisitos: List[dict]
    evidencia_semantica: dict
    puntuacion: float
    descartado: bool
    error: Optional[str]
```

**En Velora**: El estado del grafo LangGraph usa TypedDict.

---

## 11. Resumen de Patrones en Velora

| Patrón | Clase | Propósito |
|--------|-------|-----------|
| Singleton | `RegistroOperacional`, `ContextoTemporal` | Instancia única global |
| Factory | `FabricaLLM`, `FabricaEmbeddings` | Crear objetos sin exponer implementación |
| Dataclass | `HiperparametrosLLM`, `ConfiguracionProveedor` | Datos inmutables |
| BaseModel | Todos los modelos en `modelos.py` | Validación automática |
| Composición | `AnalizadorFase1`, `Orquestador` | Combinar funcionalidades |

---

## 12. Aliases para Compatibilidad

```python
# En modelos.py
class Requisito(BaseModel):
    pass

# Alias en inglés para compatibilidad
Requirement = Requisito

# En analizador.py  
class AnalizadorFase1:
    pass

# Alias
Phase1Analyzer = AnalizadorFase1
```

**¿Por qué?**: Permite usar nombres en castellano o inglés según preferencia.

---

## Próximo Documento

Continúa con [03_ARQUITECTURA_SISTEMA.md](./03_ARQUITECTURA_SISTEMA.md) para entender la estructura global del sistema.

