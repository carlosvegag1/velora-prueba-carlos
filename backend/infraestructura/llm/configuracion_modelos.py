"""
Configuración centralizada de modelos LLM por proveedor.
Externaliza lista de modelos para actualizaciones sin modificar lógica.
"""

from typing import List, Optional, Dict
from dataclasses import dataclass


@dataclass(frozen=True)
class ConfiguracionProveedor:
    """Configuración de un proveedor de LLM."""
    models: tuple
    default_model: str
    recommended_for_structured_output: str
    supports_streaming: bool = True
    supports_structured_output: bool = True


ProviderConfig = ConfiguracionProveedor


CONFIGURACIONES_PROVEEDORES: Dict[str, ConfiguracionProveedor] = {
    "openai": ConfiguracionProveedor(
        models=("gpt-4o", "gpt-4o-mini", "o1-preview", "o1-mini", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"),
        default_model="gpt-4o",
        recommended_for_structured_output="gpt-4o",
    ),
    "google": ConfiguracionProveedor(
        models=("gemini-2.0-flash-exp", "gemini-1.5-pro", "gemini-1.5-flash", "gemini-1.5-flash-8b"),
        default_model="gemini-1.5-pro",
        recommended_for_structured_output="gemini-1.5-pro",
    ),
    "anthropic": ConfiguracionProveedor(
        models=("claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022", "claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"),
        default_model="claude-3-5-sonnet-20241022",
        recommended_for_structured_output="claude-3-5-sonnet-20241022",
    ),
}

PROVIDER_CONFIGS = CONFIGURACIONES_PROVEEDORES


def obtener_modelos_disponibles(proveedor: str) -> List[str]:
    config = CONFIGURACIONES_PROVEEDORES.get(proveedor.lower())
    return list(config.models) if config else []


get_available_models = obtener_modelos_disponibles


def obtener_modelo_por_defecto(proveedor: str) -> Optional[str]:
    config = CONFIGURACIONES_PROVEEDORES.get(proveedor.lower())
    return config.default_model if config else None


get_default_model = obtener_modelo_por_defecto


def obtener_modelo_recomendado(proveedor: str) -> Optional[str]:
    config = CONFIGURACIONES_PROVEEDORES.get(proveedor.lower())
    return config.recommended_for_structured_output if config else None


get_recommended_model = obtener_modelo_recomendado


def obtener_configuracion_proveedor(proveedor: str) -> Optional[ConfiguracionProveedor]:
    return CONFIGURACIONES_PROVEEDORES.get(proveedor.lower())


get_provider_config = obtener_configuracion_proveedor


def obtener_todos_los_proveedores() -> List[str]:
    return list(CONFIGURACIONES_PROVEEDORES.keys())


get_all_providers = obtener_todos_los_proveedores


def es_modelo_valido(proveedor: str, modelo: str) -> bool:
    return modelo in obtener_modelos_disponibles(proveedor)


is_valid_model = es_modelo_valido
