"""
Hiperparámetros centralizados para LLMs por contexto de uso.
Independiente del proveedor (OpenAI, Google, Anthropic).
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class HiperparametrosLLM:
    """Hiperparámetros cross-provider: temperature, top_p, max_tokens."""
    temperature: float
    top_p: Optional[float] = None
    max_tokens: Optional[int] = None
    
    def to_dict(self) -> dict:
        resultado = {"temperature": self.temperature}
        if self.top_p is not None:
            resultado["top_p"] = self.top_p
        if self.max_tokens is not None:
            resultado["max_tokens"] = self.max_tokens
        return resultado


LLMHyperparameters = HiperparametrosLLM


# Configuraciones por contexto
FASE1_EXTRACCION = HiperparametrosLLM(temperature=0.0, top_p=0.95)
FASE1_MATCHING = HiperparametrosLLM(temperature=0.1, top_p=0.95)
FASE2_ENTREVISTA = HiperparametrosLLM(temperature=0.3, top_p=0.9)
FASE2_EVALUACION = HiperparametrosLLM(temperature=0.2, top_p=0.95)
RAG_CHATBOT = HiperparametrosLLM(temperature=0.4, top_p=0.85)
RESUMEN_ANALISIS = HiperparametrosLLM(temperature=0.3, top_p=0.9)


class ConfiguracionHiperparametros:
    """Acceso centralizado a hiperparámetros."""
    
    _CONFIGS = {
        "phase1_extraction": FASE1_EXTRACCION,
        "phase1_matching": FASE1_MATCHING,
        "phase2_interview": FASE2_ENTREVISTA,
        "phase2_evaluation": FASE2_EVALUACION,
        "rag_chatbot": RAG_CHATBOT,
        "summary": RESUMEN_ANALISIS,
    }
    
    _DEFAULTS_FASE = {
        "phase1": FASE1_MATCHING,
        "phase2": FASE2_ENTREVISTA,
        "rag": RAG_CHATBOT,
    }
    
    @classmethod
    def obtener_config(cls, contexto: str) -> HiperparametrosLLM:
        if contexto in cls._CONFIGS:
            return cls._CONFIGS[contexto]
        elif contexto in cls._DEFAULTS_FASE:
            return cls._DEFAULTS_FASE[contexto]
        return FASE1_MATCHING
    
    @classmethod
    def get_config(cls, context: str) -> HiperparametrosLLM:
        return cls.obtener_config(context)
    
    @classmethod
    def obtener_temperatura(cls, contexto: str) -> float:
        return cls.obtener_config(contexto).temperature
    
    @classmethod
    def get_temperature(cls, context: str) -> float:
        return cls.obtener_temperatura(context)
    
    @classmethod
    def listar_contextos(cls) -> list:
        return list(cls._CONFIGS.keys())
    
    @classmethod
    def list_contexts(cls) -> list:
        return cls.listar_contextos()
    
    @classmethod
    def obtener_todas_las_configs(cls) -> dict:
        return {k: v.to_dict() for k, v in cls._CONFIGS.items()}
    
    @classmethod
    def get_all_configs(cls) -> dict:
        return cls.obtener_todas_las_configs()


HyperparametersConfig = ConfiguracionHiperparametros
