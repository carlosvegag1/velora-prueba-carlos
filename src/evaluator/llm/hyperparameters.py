"""
Configuración Centralizada de Hiperparámetros para LLMs.

Este módulo define los hiperparámetros óptimos para cada contexto de uso del sistema.
La configuración es independiente del proveedor (OpenAI, Google, Anthropic).

PRINCIPIOS DE DISEÑO:
- Determinismo para tareas críticas (evaluación, extracción, matching)
- Creatividad controlada para interacción natural (entrevistas, chatbot)
- Compatibilidad cross-provider garantizada
- Ajuste centralizado sin tocar lógica de negocio
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class LLMHyperparameters:
    """
    Hiperparámetros para configuración de LLM.
    
    Attributes:
        temperature: Control de aleatoriedad (0.0 = determinista, 1.0 = creativo)
        top_p: Nucleus sampling (0.0-1.0, menor = más enfocado)
        max_tokens: Límite de tokens de salida (None = sin límite explícito)
        
    Compatibilidad:
        - temperature: Soportado por OpenAI, Google, Anthropic
        - top_p: Soportado por OpenAI, Google, Anthropic
        - max_tokens: Soportado por todos (nombre puede variar internamente)
    """
    temperature: float
    top_p: Optional[float] = None
    max_tokens: Optional[int] = None
    
    def to_dict(self) -> dict:
        """Convierte a diccionario, excluyendo valores None."""
        result = {"temperature": self.temperature}
        if self.top_p is not None:
            result["top_p"] = self.top_p
        if self.max_tokens is not None:
            result["max_tokens"] = self.max_tokens
        return result


# =============================================================================
# CONFIGURACIONES POR CONTEXTO
# =============================================================================

# FASE 1: Extracción y Matching (ALTA PRECISIÓN)
# - Temperature muy baja para respuestas consistentes y predecibles
# - Crítico: Errores aquí afectan toda la evaluación
PHASE1_EXTRACTION = LLMHyperparameters(
    temperature=0.0,  # Máxima determinismo
    top_p=0.95,       # Enfocado pero no restrictivo
)

PHASE1_MATCHING = LLMHyperparameters(
    temperature=0.1,  # Mínima variabilidad para matching preciso
    top_p=0.95,
)

# FASE 2: Entrevista Interactiva (CONVERSACIONAL)
# - Temperature más alta para preguntas naturales y variadas
# - Equilibrio entre coherencia y naturalidad
PHASE2_INTERVIEW = LLMHyperparameters(
    temperature=0.3,  # Algo de creatividad para fluidez
    top_p=0.9,
)

PHASE2_EVALUATION = LLMHyperparameters(
    temperature=0.2,  # Evaluación de respuestas: preciso pero contextual
    top_p=0.95,
)

# RAG CHATBOT: Consultas de Historial (CONVERSACIONAL)
# - Temperature moderada-alta para respuestas naturales
# - El contexto RAG ya proporciona estructura
RAG_CHATBOT = LLMHyperparameters(
    temperature=0.4,  # Creativo pero coherente
    top_p=0.85,       # Diversidad en vocabulario
)

# RESÚMENES Y ANÁLISIS (BALANCEADO)
# - Temperature moderada para síntesis clara
SUMMARY_ANALYSIS = LLMHyperparameters(
    temperature=0.3,
    top_p=0.9,
)


# =============================================================================
# ACCESO CENTRALIZADO
# =============================================================================

class HyperparametersConfig:
    """
    Configuración centralizada de hiperparámetros.
    
    Uso:
        from src.evaluator.llm.hyperparameters import HyperparametersConfig
        
        # Obtener temperatura para extracción
        temp = HyperparametersConfig.get_temperature("phase1_extraction")
        
        # Obtener config completa
        config = HyperparametersConfig.get_config("rag_chatbot")
    """
    
    # Mapeo de contextos a configuraciones
    _CONFIGS = {
        "phase1_extraction": PHASE1_EXTRACTION,
        "phase1_matching": PHASE1_MATCHING,
        "phase2_interview": PHASE2_INTERVIEW,
        "phase2_evaluation": PHASE2_EVALUATION,
        "rag_chatbot": RAG_CHATBOT,
        "summary": SUMMARY_ANALYSIS,
    }
    
    # Defaults por fase (compatibilidad con código existente)
    _PHASE_DEFAULTS = {
        "phase1": PHASE1_MATCHING,
        "phase2": PHASE2_INTERVIEW,
        "rag": RAG_CHATBOT,
    }
    
    @classmethod
    def get_config(cls, context: str) -> LLMHyperparameters:
        """
        Obtiene la configuración de hiperparámetros para un contexto.
        
        Args:
            context: Nombre del contexto (ej: 'phase1_extraction', 'rag_chatbot')
            
        Returns:
            LLMHyperparameters para ese contexto
        """
        if context in cls._CONFIGS:
            return cls._CONFIGS[context]
        elif context in cls._PHASE_DEFAULTS:
            return cls._PHASE_DEFAULTS[context]
        else:
            # Default conservador
            return PHASE1_MATCHING
    
    @classmethod
    def get_temperature(cls, context: str) -> float:
        """
        Obtiene solo la temperatura para un contexto.
        
        Args:
            context: Nombre del contexto
            
        Returns:
            Valor de temperatura
        """
        return cls.get_config(context).temperature
    
    @classmethod
    def list_contexts(cls) -> list:
        """Retorna lista de contextos disponibles."""
        return list(cls._CONFIGS.keys())
    
    @classmethod
    def get_all_configs(cls) -> dict:
        """Retorna todas las configuraciones como diccionario."""
        return {k: v.to_dict() for k, v in cls._CONFIGS.items()}


# =============================================================================
# DOCUMENTACIÓN DE JUSTIFICACIONES
# =============================================================================

HYPERPARAMETER_JUSTIFICATIONS = """
## Justificación de Hiperparámetros por Contexto

### FASE 1: Extracción y Matching
| Parámetro | Valor | Justificación |
|-----------|-------|---------------|
| temperature | 0.0-0.1 | Respuestas deterministas y reproducibles |
| top_p | 0.95 | Enfocado pero permite vocabulario técnico variado |

**Por qué baja temperatura:**
- Los requisitos extraídos deben ser consistentes entre ejecuciones
- El matching CV-requisito debe ser preciso y objetivo
- Errores en esta fase se propagan a todo el análisis

### FASE 2: Entrevista Interactiva
| Parámetro | Valor | Justificación |
|-----------|-------|---------------|
| temperature | 0.2-0.3 | Preguntas naturales sin perder coherencia |
| top_p | 0.9 | Diversidad controlada en formulación |

**Por qué temperature moderada:**
- Las preguntas deben sentirse naturales, no robóticas
- Variedad en la formulación mejora la experiencia
- La evaluación de respuestas necesita algo de flexibilidad interpretativa

### RAG Chatbot
| Parámetro | Valor | Justificación |
|-----------|-------|---------------|
| temperature | 0.4 | Respuestas conversacionales y amigables |
| top_p | 0.85 | Mayor diversidad en vocabulario |

**Por qué temperature más alta:**
- El contexto RAG ya proporciona los datos concretos
- El LLM solo necesita "vestir" la información de forma natural
- Las consultas del usuario pueden ser ambiguas

### Compatibilidad Cross-Provider

Todos estos parámetros funcionan idénticamente en:
- **OpenAI**: Soportado nativamente
- **Google Gemini**: Soportado nativamente  
- **Anthropic Claude**: Soportado nativamente

No usamos parámetros provider-specific como:
- `frequency_penalty` (OpenAI only)
- `presence_penalty` (OpenAI only)
- `top_k` (Varía entre proveedores)
"""

