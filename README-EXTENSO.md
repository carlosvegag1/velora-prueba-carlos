# Documentacion Tecnica Extendida

Sistema de Evaluacion de Candidatos con IA | Carlos Vega

---

## 1. Analisis de Requisitos

La prueba tecnica especifica un sistema de dos fases para evaluar candidatos:

### Fase 1: Analisis Automatico
El sistema recibe una oferta de empleo y un CV, extrae los requisitos de la oferta (clasificandolos como obligatorios u opcionales), y evalua el cumplimiento del CV contra cada requisito.

**Mi implementacion**:
- Uso Structured Output de LangChain para garantizar respuestas en formato Pydantic, evitando parsing manual y errores de formato.
- El analisis genera puntuacion proporcional: si hay 4 requisitos y se cumplen 3, el score es 75%.
- Si falta un requisito obligatorio, el candidato queda descartado con score 0%.

### Fase 2: Entrevista Conversacional
Si el candidato no fue descartado pero hay requisitos no encontrados en el CV, el sistema inicia una conversacion para recopilar esa informacion.

**Mi implementacion**:
- Entrevista conversacional preguntando por cada requisito faltante.
- Tras recopilar respuestas, el sistema recalcula la puntuacion final.
- Implemente streaming real para mejor experiencia de usuario.

---

## 2. Decisiones de Diseno

### Arquitectura por Capas

Opte por una arquitectura modular con separacion clara de responsabilidades:

```
backend/
  nucleo/           # Logica de negocio pura
  orquestacion/     # Coordinacion y flujos
  infraestructura/  # Integraciones externas (LLM, persistencia)
  recursos/         # Configuracion (prompts)
```

**Justificacion**: Esta estructura permite modificar la infraestructura (cambiar de OpenAI a Anthropic, por ejemplo) sin afectar la logica de negocio. Tambien facilita testing y mantenimiento.

### LangGraph para Orquestacion

Implemente orquestacion con LangGraph, definiendo un grafo de estados donde cada nodo representa una operacion (extraccion, matching, etc.).

**Justificacion**: LangGraph ofrece control granular sobre el flujo, manejo nativo de estados, y facilita debugging con trazabilidad. Aunque anade complejidad, lo considere valioso para demostrar competencia en herramientas avanzadas del ecosistema LangChain.

### Structured Output

Todas las respuestas del LLM usan Structured Output con modelos Pydantic.

**Justificacion**: Elimina la necesidad de parsing manual de respuestas, reduce errores de formato, y proporciona validacion automatica de tipos.

### Nomenclatura Bilingue

El codigo usa nomenclatura en castellano con aliases en ingles.

**Justificacion**: Balance entre legibilidad para el contexto espanol de la prueba y compatibilidad con convenciones internacionales.

---

## 3. Funcionalidades Adicionales

Mas alla de los requisitos base, implemente:

### Embeddings Semanticos con FAISS
Busqueda de evidencia en el CV usando similitud semantica, complementando el analisis del LLM.

**Justificacion**: Mejora la precision del matching al encontrar coincidencias semanticas que el LLM podria pasar por alto en descripciones largas.

### RAG para Historial
Chatbot que consulta evaluaciones previas del usuario mediante Retrieval-Augmented Generation.

**Justificacion**: Permite al usuario explorar su historial de evaluaciones con lenguaje natural.

### Scraping con Playwright
Extraccion de ofertas desde URLs, incluyendo sitios con JavaScript y proteccion basica.

**Justificacion**: Mejora la usabilidad permitiendo pegar URLs directamente en lugar de copiar texto manualmente.

### LangSmith
Integracion opcional para trazabilidad completa de llamadas LLM.

**Justificacion**: Facilita debugging y analisis de costes en desarrollo.

---

## 4. Trade-offs Tecnicos

### Docker vs Instalacion Nativa
Opte por priorizar Docker como metodo de instalacion recomendado.

**Trade-off**: Mayor tiempo de primera ejecucion (instalacion de Chromium), pero garantiza reproducibilidad y elimina problemas de dependencias del sistema.

### Streamlit vs FastAPI + Frontend Separado
Elegi Streamlit para la interfaz.

**Trade-off**: Menor control sobre la UI comparado con React/Vue, pero desarrollo significativamente mas rapido y suficiente para demostrar funcionalidad.

### Temperatura Diferenciada
Use temperaturas distintas por fase: baja (0.1) para extraccion/matching, media (0.5) para entrevista.

**Trade-off**: Extraccion requiere determinismo; entrevista se beneficia de variabilidad para conversaciones naturales.

---

## 5. Escalabilidad y Mantenibilidad

### Configuracion Centralizada
Toda la configuracion de modelos, temperaturas y prompts esta centralizada en archivos dedicados, evitando valores hardcodeados.

### Proveedores Intercambiables
La fabrica de LLM permite cambiar entre OpenAI, Google y Anthropic con un parametro, cumpliendo el requisito de intercambiabilidad.

### Persistencia Modular
La capa de persistencia usa abstraccion que permite migrar de archivos JSON a base de datos sin cambiar logica de negocio.

---

## 6. Posibles Mejoras Futuras

- **Base de datos**: Migrar de JSON a PostgreSQL para escalabilidad.
- **Autenticacion**: Implementar sistema de usuarios con OAuth.
- **Cache de embeddings**: Reducir costes reutilizando embeddings de ofertas recurrentes.
- **Batch processing**: Evaluar multiples candidatos en paralelo.

---

Carlos Vega | Enero 2025

