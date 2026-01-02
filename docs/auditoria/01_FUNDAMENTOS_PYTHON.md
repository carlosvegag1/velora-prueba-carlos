# Fundamentos de Python para el Sistema Velora

## Introducción

Este documento explica los conceptos básicos de Python que necesitas conocer para entender el código del sistema Velora. Está pensado para personas con conocimientos básicos-intermedios de programación.

---

## 1. Tipos de Datos Básicos

### 1.1 Strings (Cadenas de Texto)

```python
# Una cadena es texto entre comillas
nombre = "Carlos"
oferta = """
    Esta es una cadena
    de múltiples líneas
"""

# f-strings: Insertar variables en texto
mensaje = f"Hola {nombre}"  # "Hola Carlos"
```

**En Velora**: Los prompts del LLM usan f-strings para insertar datos dinámicos.

### 1.2 Listas

```python
# Lista: colección ordenada y modificable
requisitos = ["Python", "Django", "SQL"]

# Acceso por índice (empieza en 0)
primer_requisito = requisitos[0]  # "Python"

# Añadir elementos
requisitos.append("Docker")

# Recorrer lista
for req in requisitos:
    print(req)
```

**En Velora**: Los requisitos extraídos se almacenan en listas.

### 1.3 Diccionarios

```python
# Diccionario: pares clave-valor
requisito = {
    "description": "5 años de Python",
    "type": "obligatory"
}

# Acceso por clave
descripcion = requisito["description"]

# Método .get() (evita errores si no existe)
tipo = requisito.get("type", "optional")
```

**En Velora**: Todo el sistema usa diccionarios para estructurar datos.

### 1.4 Tuplas

```python
# Tupla: colección ordenada INMUTABLE
coordenadas = (10, 20)
modelos = ("gpt-4o", "gpt-4o-mini")  # No se puede modificar

# Útil para datos que no deben cambiar
```

**En Velora**: La configuración de modelos disponibles usa tuplas.

---

## 2. Funciones

### 2.1 Definición Básica

```python
def calcular_puntuacion(total, cumplidos):
    """
    Calcula la puntuación porcentual.
    
    Args:
        total: Número total de requisitos
        cumplidos: Número de requisitos cumplidos
    
    Returns:
        float: Puntuación entre 0 y 100
    """
    if total == 0:
        return 100.0
    return (cumplidos / total) * 100.0
```

**Elementos clave**:
- `def`: Define una función
- Nombre descriptivo en minúsculas con guiones bajos
- `"""..."""`: Docstring que explica qué hace
- `return`: Devuelve un valor

### 2.2 Parámetros con Valores por Defecto

```python
def crear_llm(proveedor="openai", temperatura=0.1):
    """Crea un LLM con configuración opcional."""
    # Si no se especifica proveedor, usa "openai"
    # Si no se especifica temperatura, usa 0.1
    pass
```

**En Velora**: Muchas funciones tienen valores por defecto para simplificar uso.

### 2.3 Anotaciones de Tipo (Type Hints)

```python
from typing import List, Optional, Dict

def extraer_requisitos(oferta: str) -> List[dict]:
    """
    Args:
        oferta (str): Texto de la oferta
    
    Returns:
        List[dict]: Lista de requisitos extraídos
    """
    pass

def procesar(texto: Optional[str] = None) -> Dict[str, any]:
    """Optional significa que puede ser None"""
    pass
```

**Beneficios**:
- Documentación implícita del código
- Ayuda del IDE con autocompletado
- Detección de errores antes de ejecutar

---

## 3. Imports y Módulos

### 3.1 Estructura de Imports

```python
# Import de librería estándar
import os
import sys
from pathlib import Path
from typing import List, Optional

# Import de librería externa (instalada con pip)
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

# Import relativo (dentro del proyecto)
from .modelos import Requisito           # . = mismo paquete
from ..utilidades import calcular        # .. = paquete padre
from ...infraestructura import FabricaLLM  # ... = dos niveles arriba
```

### 3.2 Estructura de Paquetes

```
backend/
├── __init__.py          # Hace que backend sea un paquete
├── modelos.py
├── utilidades/
│   ├── __init__.py      # Hace que utilidades sea subpaquete
│   └── logger.py
```

**`__init__.py`**: Archivo que convierte una carpeta en un paquete Python importable.

---

## 4. Manejo de Excepciones

### 4.1 Try/Except Básico

```python
try:
    # Código que puede fallar
    resultado = 10 / 0
except ZeroDivisionError:
    # Qué hacer si falla
    resultado = 0
except Exception as e:
    # Cualquier otro error
    print(f"Error: {e}")
finally:
    # Se ejecuta SIEMPRE
    print("Limpieza")
```

### 4.2 Lanzar Excepciones

```python
def validar_cv(texto):
    if not texto:
        raise ValueError("El CV no puede estar vacío")
    return texto
```

**En Velora**: Se usa extensivamente para validar entradas y manejar errores de APIs.

---

## 5. Comprehensions (Comprensiones)

### 5.1 List Comprehension

```python
# Forma tradicional
obligatorios = []
for req in requisitos:
    if req["type"] == "obligatory":
        obligatorios.append(req)

# Con comprehension (más Pythónico)
obligatorios = [req for req in requisitos if req["type"] == "obligatory"]
```

### 5.2 Dict Comprehension

```python
# Crear diccionario desde lista
mapa_requisitos = {req["description"]: req for req in requisitos}
```

**En Velora**: Se usan comprehensions para transformar datos de forma concisa.

---

## 6. Context Managers (with)

### 6.1 Manejo de Archivos

```python
# Sin context manager (riesgo de no cerrar archivo)
f = open("archivo.txt", "r")
contenido = f.read()
f.close()

# Con context manager (cierre automático)
with open("archivo.txt", "r", encoding="utf-8") as f:
    contenido = f.read()
# El archivo se cierra automáticamente al salir del bloque
```

**En Velora**: Todos los archivos se manejan con `with`.

---

## 7. Generadores

### 7.1 Función Generadora

```python
def generar_tokens(texto):
    """Genera tokens uno por uno (streaming)."""
    for char in texto:
        yield char  # Pausa y devuelve un valor
        # La función continúa desde aquí en la siguiente llamada

# Uso
for token in generar_tokens("Hola"):
    print(token)  # H, o, l, a (uno por uno)
```

**En Velora**: El streaming de respuestas del LLM usa generadores.

### 7.2 Generator Expression

```python
# Similar a list comprehension pero perezoso (lazy)
suma = sum(req["score"] for req in requisitos)
```

---

## 8. Decoradores Básicos

### 8.1 @staticmethod

```python
class FabricaLLM:
    @staticmethod
    def crear_llm(proveedor, modelo):
        """Método que no necesita acceso a self."""
        # No usa self, funciona como función normal
        pass

# Llamada sin instanciar la clase
llm = FabricaLLM.crear_llm("openai", "gpt-4o")
```

### 8.2 @classmethod

```python
class ConfiguracionHiperparametros:
    _CONFIGS = {...}
    
    @classmethod
    def obtener_config(cls, contexto):
        """Método que accede a atributos de clase (cls)."""
        return cls._CONFIGS.get(contexto)
```

### 8.3 @property

```python
class Almacen:
    def __init__(self):
        self._vectorstore = None
    
    @property
    def esta_inicializado(self):
        """Accesible como atributo, no como método."""
        return self._vectorstore is not None

# Uso
almacen = Almacen()
if almacen.esta_inicializado:  # Sin paréntesis
    pass
```

---

## 9. Variables Especiales

### 9.1 `__name__`

```python
# En main.py
if __name__ == "__main__":
    main()  # Solo se ejecuta si este archivo es el principal
```

**Explicación**: 
- Si ejecutas `python main.py`, `__name__` es `"__main__"`
- Si importas el módulo, `__name__` es el nombre del módulo

### 9.2 `__all__`

```python
# En __init__.py
__all__ = ["FabricaLLM", "crear_llm"]
# Define qué se exporta con "from modulo import *"
```

---

## 10. Operador Walrus (:=)

```python
# Asigna y usa en la misma línea
if (resultado := procesar()) is not None:
    print(resultado)

# Equivalente a:
resultado = procesar()
if resultado is not None:
    print(resultado)
```

**En Velora**: Se usa ocasionalmente para código más conciso.

---

## 11. Unpacking (Desempaquetado)

### 11.1 Desempaquetado Básico

```python
# Tuplas
texto, score = ("evidencia", 0.85)

# Listas
primero, *resto = [1, 2, 3, 4]  # primero=1, resto=[2,3,4]
```

### 11.2 Desempaquetado en Funciones

```python
def funcion(*args, **kwargs):
    # args: tupla con argumentos posicionales extra
    # kwargs: diccionario con argumentos nombrados extra
    pass

# Llamada
funcion(1, 2, 3, nombre="Carlos", edad=30)
# args = (1, 2, 3)
# kwargs = {"nombre": "Carlos", "edad": 30}
```

---

## Resumen de Conceptos Clave en Velora

| Concepto | Uso en Velora |
|----------|---------------|
| f-strings | Construcción de prompts dinámicos |
| Type Hints | Documentación de tipos en todo el código |
| Diccionarios | Estructuración de requisitos y resultados |
| Comprehensions | Transformación de listas de requisitos |
| Generadores | Streaming de respuestas del LLM |
| Context Managers | Lectura de archivos PDF/texto |
| Excepciones | Manejo de errores de APIs externas |
| @staticmethod | Métodos de fábrica (Factory pattern) |
| @property | Acceso a estado interno como atributo |

---

## Próximo Documento

Continúa con [02_CONCEPTOS_POO.md](./02_CONCEPTOS_POO.md) para entender la Programación Orientada a Objetos aplicada al proyecto.

