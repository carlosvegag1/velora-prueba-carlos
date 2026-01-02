# Glosario de Términos Técnicos

## Introducción

Este glosario define todos los términos técnicos utilizados en el proyecto Velora, explicados de forma accesible para usuarios con conocimiento intermedio de Python.

---

## A

### **API (Application Programming Interface)**
Interfaz que permite que dos programas se comuniquen. En Velora, usamos APIs de OpenAI, Google y Anthropic para acceder a sus LLMs.

**Ejemplo**: Cuando llamamos a `openai.chat.completions.create()`, estamos usando la API de OpenAI.

### **API Key**
Clave secreta que identifica tu cuenta al usar una API. Sin ella, el proveedor no te permite usar el servicio.

**En Velora**: Se configura en el sidebar de Streamlit o via variables de entorno.

### **Abstracción**
Ocultar detalles complejos detrás de una interfaz simple.

**Ejemplo en Velora**: `FabricaLLM.crear_llm("openai", "gpt-4o")` oculta todo el proceso de configuración.

---

## B

### **Backend**
La parte del sistema que procesa datos y ejecuta la lógica de negocio. El usuario no interactúa directamente con él.

**En Velora**: La carpeta `backend/` contiene toda la lógica de evaluación.

### **Batch**
Procesar múltiples elementos juntos en lugar de uno por uno.

**En Velora**: `_realizar_entrevista_batch()` procesa todas las respuestas de entrevista de una vez.

---

## C

### **Callback**
Función que se ejecuta cuando ocurre un evento específico.

**Ejemplo**: En Streamlit, el botón tiene un callback que se ejecuta al hacer clic.

### **Chain (Cadena)**
En LangChain, una secuencia de operaciones que se ejecutan en orden.

```python
# Esto es una chain: prompt | llm | parser
chain = prompt | llm | StrOutputParser()
resultado = chain.invoke({"input": "texto"})
```

### **Chunk**
Fragmento de texto. Los documentos largos se dividen en chunks para procesar.

**En Velora**: El CV se divide en chunks de ~500 caracteres para la búsqueda semántica.

### **Contexto**
Información adicional que se proporciona al LLM para ayudarlo a responder mejor.

**En Velora**: El contexto temporal ("Estamos en enero 2026") es crucial para calcular años de experiencia.

---

## D

### **Dataclass**
Clase de Python diseñada para almacenar datos con poco código.

```python
from dataclasses import dataclass

@dataclass
class Persona:
    nombre: str
    edad: int

p = Persona("Ana", 30)
print(p.nombre)  # "Ana"
```

### **Decorador (@)**
Función que modifica el comportamiento de otra función.

```python
@staticmethod  # Decorador que hace el método estático
def crear_llm(proveedor):
    ...
```

### **Determinismo**
Que siempre produce el mismo resultado para la misma entrada.

**En Velora**: Fase 1 usa `temperature=0.0` para garantizar que la misma oferta siempre genere los mismos requisitos.

### **Dict (Diccionario)**
Estructura de datos que almacena pares clave-valor.

```python
persona = {"nombre": "Ana", "edad": 30}
print(persona["nombre"])  # "Ana"
```

---

## E

### **Embedding**
Representación numérica de texto como un vector (lista de números). Textos similares tienen embeddings cercanos.

```python
# "Python" → [0.12, -0.45, 0.78, ...]
# "Java" → [0.11, -0.42, 0.75, ...]  # Similar a Python
# "Marketing" → [-0.67, 0.23, -0.12, ...]  # Muy diferente
```

### **Enum**
Tipo que define un conjunto fijo de valores posibles.

```python
from enum import Enum

class TipoRequisito(str, Enum):
    OBLIGATORIO = "obligatory"
    DESEABLE = "optional"

# Solo puede ser OBLIGATORIO o DESEABLE
```

---

## F

### **Factory Pattern (Patrón Fábrica)**
Patrón de diseño donde una clase se encarga de crear instancias de otras clases.

```python
class FabricaLLM:
    @staticmethod
    def crear_llm(proveedor, modelo):
        if proveedor == "openai":
            return ChatOpenAI(model=modelo)
        elif proveedor == "google":
            return ChatGoogleGenerativeAI(model=modelo)
```

### **FAISS (Facebook AI Similarity Search)**
Librería para búsqueda vectorial eficiente. Encuentra los vectores más parecidos a uno dado.

### **Field**
En Pydantic, define las propiedades de un atributo: valor por defecto, validaciones, alias, etc.

```python
nombre: str = Field(..., min_length=1, alias="name")
```

### **Float**
Número con decimales.

```python
puntuacion: float = 85.5
```

### **Frontend**
La parte del sistema con la que el usuario interactúa directamente.

**En Velora**: Streamlit es nuestro frontend.

---

## G

### **Generator**
Función que produce valores uno a uno (lazy evaluation), usando `yield` en lugar de `return`.

```python
def contar_hasta(n):
    for i in range(n):
        yield i  # Produce un valor y pausa

for num in contar_hasta(5):
    print(num)  # 0, 1, 2, 3, 4
```

### **Graph (Grafo)**
Estructura de datos con nodos conectados por aristas. En LangGraph, los nodos son funciones y las aristas definen el flujo.

---

## H

### **Headless**
Ejecutar un navegador sin interfaz gráfica.

```python
browser = playwright.chromium.launch(headless=True)
```

### **Hiperparámetro**
Configuración que controla el comportamiento del modelo, pero que no se aprende del datos.

**En Velora**: `temperature` y `top_p` son hiperparámetros del LLM.

---

## I

### **Import**
Cargar código de otro módulo/archivo.

```python
from backend.modelos import Requisito
import os
```

### **Indexar**
Crear una estructura que permite búsquedas rápidas.

**En Velora**: Indexamos el CV con FAISS para encontrar rápidamente evidencia relevante.

### **Instance (Instancia)**
Un objeto creado a partir de una clase.

```python
class Perro:
    def __init__(self, nombre):
        self.nombre = nombre

fido = Perro("Fido")  # fido es una instancia de Perro
```

---

## J

### **JSON (JavaScript Object Notation)**
Formato de texto para almacenar datos estructurados.

```json
{
    "nombre": "Ana",
    "edad": 30,
    "habilidades": ["Python", "SQL"]
}
```

---

## K

### **K (en búsqueda vectorial)**
El número de resultados a devolver en una búsqueda.

```python
vectorstore.similarity_search("Python", k=5)  # Top 5 resultados
```

---

## L

### **LangChain**
Framework de Python para construir aplicaciones con LLMs.

### **LangGraph**
Framework para orquestar flujos de trabajo como grafos de estados.

### **LangSmith**
Plataforma de observabilidad para aplicaciones LLM.

### **LLM (Large Language Model)**
Modelo de inteligencia artificial entrenado para entender y generar texto.

**Ejemplos**: GPT-4, Claude, Gemini.

### **Literal**
Tipo que restringe un valor a opciones específicas.

```python
from typing import Literal

nivel: Literal["alto", "medio", "bajo"]  # Solo estos tres valores
```

---

## M

### **Matching**
Proceso de comparar y encontrar correspondencias entre dos conjuntos de datos.

**En Velora**: Matching CV-Requisitos compara el CV con cada requisito.

### **Method (Método)**
Función definida dentro de una clase.

```python
class Calculadora:
    def sumar(self, a, b):  # método
        return a + b
```

### **Module (Módulo)**
Un archivo Python que puede ser importado.

---

## N

### **Namespace**
Contenedor que da contexto a los nombres para evitar conflictos.

**Ejemplo**: `backend.modelos.Requisito` vs `otro_paquete.Requisito`

### **Node (Nodo)**
En LangGraph, una función que procesa el estado.

```python
def nodo_extraccion(estado):
    # Procesar
    return {"requisitos": [...]}
```

---

## O

### **Optional**
Tipo que indica que un valor puede ser None.

```python
from typing import Optional

email: Optional[str] = None  # Puede ser string o None
```

### **Override**
Redefinir un método heredado en una subclase.

---

## P

### **Parser**
Componente que analiza y transforma datos de un formato a otro.

```python
# Convierte la respuesta del LLM a string
from langchain_core.output_parsers import StrOutputParser
```

### **Patrón**
Solución reutilizable a un problema común en diseño de software.

**Ejemplos en Velora**: Factory, Singleton.

### **Prompt**
Instrucciones que se envían al LLM para obtener una respuesta.

```python
prompt = "Eres un extractor de requisitos. Extrae los requisitos de: ..."
```

### **Property (Propiedad)**
Atributo de una clase que puede tener lógica de obtención/establecimiento.

```python
class Persona:
    @property
    def edad(self):
        return 2026 - self._anio_nacimiento
```

### **Pydantic**
Librería de validación de datos usando anotaciones de tipo.

---

## R

### **RAG (Retrieval-Augmented Generation)**
Técnica que combina búsqueda de información con generación de texto.

1. **Retrieval**: Buscar documentos relevantes
2. **Augmented**: Añadirlos al contexto
3. **Generation**: El LLM genera respuesta usando ese contexto

### **Return**
Devolver un valor desde una función.

```python
def sumar(a, b):
    return a + b
```

---

## S

### **Schema (Esquema)**
Definición de la estructura de datos.

**En Velora**: Los modelos Pydantic definen el esquema de los datos.

### **Scraping**
Extraer datos de páginas web automáticamente.

### **Singleton**
Patrón que garantiza que solo existe una instancia de una clase.

```python
class Logger:
    _instancia = None
    
    def __new__(cls):
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
        return cls._instancia
```

### **State (Estado)**
En LangGraph, el diccionario que contiene toda la información del flujo.

### **Static Method**
Método que no necesita acceso a la instancia (`self`).

```python
class Utilidades:
    @staticmethod
    def sumar(a, b):
        return a + b

# Se llama sin crear instancia
Utilidades.sumar(2, 3)
```

### **Streaming**
Enviar datos progresivamente en lugar de todo de una vez.

```python
for token in llm.stream("Hola"):
    print(token, end="")  # Imprime token por token
```

### **String (str)**
Tipo de dato para texto.

```python
nombre: str = "Velora"
```

### **Structured Output**
Respuestas del LLM en formato estructurado (validado por Pydantic).

```python
llm_estructurado = llm.with_structured_output(MiModelo)
# El resultado SIEMPRE tiene la estructura de MiModelo
```

---

## T

### **Temperature**
Hiperparámetro que controla la creatividad del LLM.

- `0.0`: Determinista, siempre la misma respuesta
- `0.3-0.7`: Equilibrio entre creatividad y consistencia
- `1.0+`: Muy creativo, respuestas variadas

### **Token**
Unidad básica de texto para el LLM. Aproximadamente 4 caracteres en inglés.

```
"Hola mundo" → ["Hola", " mundo"] → 2 tokens
```

### **Type Hint (Anotación de Tipo)**
Indicación del tipo de dato esperado.

```python
def saludar(nombre: str) -> str:
    return f"Hola, {nombre}"
```

### **TypedDict**
Diccionario con estructura definida.

```python
from typing import TypedDict

class Usuario(TypedDict):
    nombre: str
    edad: int

user: Usuario = {"nombre": "Ana", "edad": 30}
```

---

## V

### **Validación**
Verificar que los datos cumplen ciertas reglas.

```python
class Edad(BaseModel):
    valor: int = Field(ge=0, le=150)  # Entre 0 y 150
```

### **Variable de Entorno**
Variable configurada en el sistema operativo, no en el código.

```python
import os
api_key = os.getenv("OPENAI_API_KEY")
```

### **Vector**
Lista de números que representa algo (texto, imagen, etc.).

```python
embedding = [0.12, -0.45, 0.78, ...]  # Vector de 512 dimensiones
```

### **Vectorstore**
Base de datos que almacena y busca vectores.

**En Velora**: FAISS es nuestro vectorstore.

---

## Y

### **Yield**
Palabra clave para crear generators.

```python
def generar_numeros():
    yield 1
    yield 2
    yield 3
```

---

## Siglas Comunes

| Sigla | Significado | Descripción |
|-------|-------------|-------------|
| API | Application Programming Interface | Interfaz de comunicación entre programas |
| CV | Curriculum Vitae | Documento con experiencia laboral |
| FAISS | Facebook AI Similarity Search | Librería de búsqueda vectorial |
| LLM | Large Language Model | Modelo de lenguaje grande |
| OOP | Object-Oriented Programming | Programación orientada a objetos |
| POO | Programación Orientada a Objetos | OOP en español |
| RAG | Retrieval-Augmented Generation | Técnica de IA |
| UI | User Interface | Interfaz de usuario |
| UX | User Experience | Experiencia de usuario |

---

## Términos Específicos de Velora

### **Fase 1**
Análisis automático del CV contra los requisitos de la oferta.

### **Fase 2**
Entrevista conversacional para verificar requisitos no cumplidos.

### **Requisito Obligatorio**
Requisito que debe cumplirse. Si no se cumple → descartado.

### **Requisito Deseable**
Requisito preferido pero no eliminatorio.

### **Contexto Temporal**
Información sobre la fecha actual (2026) para calcular experiencia correctamente.

### **Evidencia**
Texto del CV que demuestra el cumplimiento de un requisito.

### **Puntuación**
Porcentaje de requisitos cumplidos (0-100%).

### **Descartado**
Candidato que no cumple algún requisito obligatorio → 0%.

