# Assets - Velora Auto Evaluator

Este directorio contiene los recursos visuales de la aplicación.

## Logos (Implementados como SVG inline)

Los logos de Velora están implementados directamente en el código como SVG inline para evitar dependencias de archivos externos:

- **Logo Principal**: .png del texto "velora" con gradiente turquesa en la V y A
- **Logo Reducido**: Icono "VA" compacto para el sidebar

## Paleta de Colores Velora

| Color | Hex | Uso |
|-------|-----|-----|
| Primary | `#00B4D8` | Turquesa principal, acentos |
| Secondary | `#00CED1` | Turquesa secundario, gradientes |
| Dark | `#3D4043` | Texto principal |
| Gray | `#6B7280` | Texto secundario |
| Light Gray | `#F3F4F6` | Fondos |
| Success | `#10B981` | Estados positivos |
| Error | `#EF4444` | Estados de error |
| Warning | `#F59E0B` | Advertencias |

## Tipografía

- **Font Family**: Inter (Google Fonts)
- **Fallback**: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif

## Notas de Implementación

- Los logos SVG se renderizan inline para máxima compatibilidad
- El gradiente usa `linearGradient` para transiciones suaves
- Los colores están definidos como constantes Python en `streamlit_app.py`

