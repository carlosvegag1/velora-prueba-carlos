#!/usr/bin/env python3
"""
Script para ejecutar la aplicación Streamlit
"""

import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    app_path = Path(__file__).parent / "app" / "streamlit_app.py"
    
    if not app_path.exists():
        print(f"Error: No se encontró la aplicación en {app_path}")
        sys.exit(1)
    
    # Ejecutar Streamlit
    subprocess.run([
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app_path),
        "--server.port=8501",
        "--server.address=localhost"
    ])

