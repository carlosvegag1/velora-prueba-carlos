# Documentación: `main.py`

## Información General

| Atributo | Valor |
|----------|-------|
| **Ruta** | `/main.py` |
| **Tipo** | Punto de entrada |
| **Líneas** | ~20 |
| **Dependencias** | `os`, `subprocess`, `sys`, `pathlib` |

---

## Propósito

Este archivo es el **punto de entrada principal** de la aplicación Velora. Su única responsabilidad es iniciar el servidor Streamlit.

---

## Código Completo Explicado

```python
"""
Punto de entrada principal de la aplicación Velora.

Este módulo inicia el servidor Streamlit que aloja la interfaz de usuario.
Puede ser ejecutado directamente o importado como módulo.
"""
```

**¿Qué es esto?**
- Es un **docstring** (cadena de documentación)
- Aparece al principio del archivo para explicar su propósito
- Se puede acceder con `import main; help(main)`

---

```python
import os
import subprocess
import sys
from pathlib import Path
```

**¿Qué hacen estos imports?**

| Import | Propósito |
|--------|-----------|
| `os` | Acceder a variables de entorno (`HOST`, `PORT`) |
| `subprocess` | Ejecutar comandos externos (Streamlit) |
| `sys` | Acceder a `sys.executable` (ruta del Python actual) |
| `pathlib.Path` | Manipular rutas de archivos de forma multiplataforma |

---

```python
def main():
    """Inicia la aplicación Streamlit."""
```

**¿Qué es esto?**
- Define una función llamada `main`
- `def` = **define** una función
- `():` = no recibe parámetros
- El docstring explica qué hace

---

```python
    # Obtener la ruta del archivo actual
    ruta_actual = Path(__file__).parent.resolve()
```

**¿Qué hace esta línea?**

1. `__file__` → Es una variable especial que contiene la ruta del archivo actual (`main.py`)
2. `Path(__file__)` → Convierte esa ruta en un objeto `Path` (multiplataforma)
3. `.parent` → Obtiene el directorio padre (donde está `main.py`)
4. `.resolve()` → Convierte a ruta absoluta (ej: `/home/user/velora`)

**Ejemplo**:
- Si `main.py` está en `/home/user/velora/main.py`
- `ruta_actual` será `/home/user/velora`

---

```python
    # Ruta al archivo de Streamlit
    streamlit_app = ruta_actual / "frontend" / "streamlit_app.py"
```

**¿Qué hace esta línea?**

- El operador `/` con objetos `Path` **concatena** rutas
- Es equivalente a `ruta_actual + "/frontend/streamlit_app.py"`
- Pero `/` funciona en Windows y Linux automáticamente

**Resultado**: `/home/user/velora/frontend/streamlit_app.py`

---

```python
    # Configuración del servidor
    host = os.environ.get("STREAMLIT_SERVER_ADDRESS", "0.0.0.0")
    port = os.environ.get("STREAMLIT_SERVER_PORT", "8501")
```

**¿Qué hacen estas líneas?**

- `os.environ.get(clave, valor_por_defecto)` busca una variable de entorno
- Si la variable existe, usa su valor
- Si no existe, usa el valor por defecto

| Variable | Propósito | Por Defecto |
|----------|-----------|-------------|
| `STREAMLIT_SERVER_ADDRESS` | IP del servidor | `0.0.0.0` (todas las interfaces) |
| `STREAMLIT_SERVER_PORT` | Puerto | `8501` |

**¿Por qué `0.0.0.0`?**
- `0.0.0.0` significa "escucha en todas las interfaces de red"
- Necesario para Docker (el contenedor tiene una IP interna)
- `localhost` solo funcionaría dentro del contenedor

---

```python
    # Ejecutar Streamlit
    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        str(streamlit_app),
        "--server.address", host,
        "--server.port", port
    ])
```

**¿Qué hace `subprocess.run`?**

- Ejecuta un comando externo como si escribieras en la terminal
- `[...]` es una lista con el comando y sus argumentos

**Desglose del comando**:

| Parte | Significado |
|-------|-------------|
| `sys.executable` | Ruta al Python actual (ej: `/usr/bin/python3.11`) |
| `"-m", "streamlit"` | Ejecutar el módulo `streamlit` |
| `"run"` | Subcomando de Streamlit para ejecutar una app |
| `str(streamlit_app)` | Ruta al archivo a ejecutar |
| `"--server.address", host` | IP donde escuchar |
| `"--server.port", port` | Puerto donde escuchar |

**Comando equivalente en terminal**:
```bash
python -m streamlit run frontend/streamlit_app.py --server.address 0.0.0.0 --server.port 8501
```

---

```python
if __name__ == "__main__":
    main()
```

**¿Qué es esto?**

Este es el "**idiom**" estándar de Python para ejecutar código solo cuando el archivo se ejecuta directamente.

**¿Cómo funciona?**

1. Cuando ejecutas `python main.py`, Python asigna `__name__ = "__main__"`
2. Cuando importas `import main`, Python asigna `__name__ = "main"`

**¿Por qué es importante?**

```python
# Si ejecutas: python main.py
# → __name__ == "__main__" → True → ejecuta main()

# Si importas: from main import main
# → __name__ == "main" → False → NO ejecuta main()
```

**Beneficio**: Puedes importar funciones de `main.py` sin que se ejecute automáticamente.

---

## Diagrama de Flujo

```
python main.py
      │
      ▼
¿__name__ == "__main__"?
      │
      SÍ
      │
      ▼
main() se ejecuta
      │
      ▼
Calcula ruta de streamlit_app.py
      │
      ▼
Lee HOST y PORT de variables de entorno
      │
      ▼
subprocess.run([python, -m, streamlit, run, ...])
      │
      ▼
Streamlit inicia servidor en http://host:port
```

---

## Conceptos Python Aplicados

### 1. Variables Especiales (`__file__`, `__name__`)

Python define automáticamente ciertas variables:

| Variable | Contenido |
|----------|-----------|
| `__file__` | Ruta del archivo actual |
| `__name__` | `"__main__"` si se ejecuta directamente, nombre del módulo si se importa |
| `__doc__` | Docstring del módulo |

### 2. Pathlib vs os.path

**Antiguo (os.path)**:
```python
import os
ruta = os.path.join(os.path.dirname(__file__), "frontend", "app.py")
```

**Moderno (pathlib)**:
```python
from pathlib import Path
ruta = Path(__file__).parent / "frontend" / "app.py"
```

`pathlib` es más legible y funciona igual en Windows y Linux.

### 3. Variables de Entorno

Las variables de entorno son valores configurables desde fuera del código:

```bash
# En terminal
export STREAMLIT_SERVER_PORT=9000
python main.py  # Usará puerto 9000

# O directamente
STREAMLIT_SERVER_PORT=9000 python main.py
```

### 4. subprocess vs os.system

| Método | Pros | Contras |
|--------|------|---------|
| `os.system("cmd")` | Simple | No captura salida, inseguro |
| `subprocess.run([...])` | Seguro, control total | Más verboso |

`subprocess.run` es el estándar moderno porque:
- Cada argumento es un elemento de lista (evita inyección de comandos)
- Permite capturar stdout/stderr
- Devuelve código de salida

---

## Preguntas Frecuentes

### ¿Por qué no ejecutar Streamlit directamente?

**Opción A** (lo que hacemos):
```python
# main.py
subprocess.run([sys.executable, "-m", "streamlit", ...])
```

**Opción B** (alternativa):
```bash
streamlit run frontend/streamlit_app.py
```

**Razones para Opción A**:
1. `sys.executable` garantiza usar el Python correcto (importante en venvs)
2. Permite añadir lógica antes de iniciar (validaciones, setup)
3. Un único punto de entrada documentado

### ¿Qué pasa si `streamlit_app.py` no existe?

`subprocess.run` devolvería un error, pero no crashea `main.py`. Streamlit mostraría un mensaje de error indicando que no encuentra el archivo.

### ¿Por qué `str(streamlit_app)`?

`Path` es un objeto, no un string. Algunos programas necesitan strings:

```python
streamlit_app = Path("/ruta/al/archivo.py")  # Objeto Path
str(streamlit_app)  # "/ruta/al/archivo.py"  # String
```

---

## Relación con Otros Archivos

```
main.py
   │
   └─── frontend/streamlit_app.py
           │
           └─── backend/__init__.py
                    │
                    ├── nucleo/...
                    ├── infraestructura/...
                    └── utilidades/...
```

`main.py` solo conoce la existencia de `streamlit_app.py`. Todo lo demás es responsabilidad de Streamlit y el backend.

---

## Justificación de Diseño

### ¿Por qué un archivo separado?

**Alternativa**: Poner el código de inicio en `streamlit_app.py`:
```python
# streamlit_app.py
if __name__ == "__main__":
    import streamlit.cli
    streamlit.cli.main()
```

**Razones para `main.py` separado**:
1. **Claridad**: El punto de entrada es obvio
2. **Configuración**: Permite configurar antes de iniciar Streamlit
3. **Convención**: Es estándar tener `main.py` como entrada
4. **Docker**: `CMD python main.py` es más intuitivo que `CMD streamlit run ...`

### ¿Por qué tan pocas líneas?

Este archivo sigue el principio de **responsabilidad única**: solo inicia la aplicación. No contiene lógica de negocio, validaciones complejas, ni configuración extensa.

**Filosofía**: Si el archivo hace una sola cosa bien, es más fácil de entender y mantener.

