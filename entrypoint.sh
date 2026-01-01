#!/bin/sh
# Script de inicio con mensaje informativo

cat << "EOF"

╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║               🚀 Velora - Sistema de Evaluación              ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

EOF

echo "✓ Aplicación iniciada correctamente"
echo ""
echo "📍 Accede desde tu navegador:"
echo "   → http://localhost:8501"
echo ""
echo "💡 Puerto configurado: ${VELORA_PORT:-8501}"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo ""

# Iniciar Streamlit
exec streamlit run frontend/streamlit_app.py --server.port=8501 --server.address=0.0.0.0

