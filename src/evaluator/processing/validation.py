"""
Funciones de validación y utilidades generales.
Simplificado para uso con Structured Output de LangChain.
"""

from pathlib import Path


def calculate_score(
    total_requirements: int,
    fulfilled_count: int,
    has_unfulfilled_obligatory: bool
) -> float:
    """
    Calcula la puntuación del candidato según las reglas del sistema.
    
    Reglas:
    - Si falta un requisito obligatorio: 0%
    - Si todos los requisitos se cumplen: 100%
    - En otros casos: proporcional al número de requisitos cumplidos
    
    Args:
        total_requirements: Número total de requisitos
        fulfilled_count: Número de requisitos cumplidos
        has_unfulfilled_obligatory: Si hay algún requisito obligatorio no cumplido
        
    Returns:
        Puntuación entre 0 y 100
    """
    if total_requirements == 0:
        return 100.0
    
    if has_unfulfilled_obligatory:
        return 0.0
    
    return (fulfilled_count / total_requirements) * 100.0


def load_text_file(file_path: str) -> str:
    """
    Carga el contenido de un archivo de texto.
    
    Args:
        file_path: Ruta al archivo de texto
        
    Returns:
        Contenido del archivo como string
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"El archivo no existe: {file_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()
