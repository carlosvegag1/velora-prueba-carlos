#!/usr/bin/env python3
"""
Velora - Sistema de Evaluación de Candidatos con IA
Punto de entrada principal para ejecución local y Docker.
"""

import os
import subprocess
import sys
from pathlib import Path


def main():
    """Inicia la aplicación Streamlit."""
    app_path = Path(__file__).parent / "frontend" / "streamlit_app.py"
    
    if not app_path.exists():
        print(f"Error: No se encontró la aplicación en {app_path}")
        sys.exit(1)
    
    server_address = os.environ.get("STREAMLIT_SERVER_ADDRESS", "localhost")
    server_port = os.environ.get("STREAMLIT_SERVER_PORT", "8501")
    
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", str(app_path),
        f"--server.port={server_port}",
        f"--server.address={server_address}"
    ], check=False)


if __name__ == "__main__":
    main()
