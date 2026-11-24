# Arquitectura

| Módulo | Responsabilidad | Entrada → Salida |
|---|---|---|
| `autopilot/ingest.py` | Leer y normalizar | carpeta → `DataFrame` con columnas canónicas |
| `autopilot/quality.py` | Validar y separar | `DataFrame` → `QualityResult(clean, issues)` |
| `autopilot/report.py` | Presentar | `QualityResult` → `.xlsx` + `.html` |
| `autopilot/__main__.py` | Orquestar (CLI + logging) | argumentos → archivos |

## Principios

- **Separación de responsabilidades**: cada módulo hace una sola cosa y se testea por separado.
- **Nunca borrar en silencio**: toda fila excluida queda registrada con su regla (`issues`).
- **Configuración como datos**: sinónimos de columnas (`COLUMN_ALIASES`) y reglas (`RULES`) son diccionarios; extender no requiere tocar la lógica.

## Reglas de calidad

| Regla | Condición |
|---|---|
| `fecha_invalida` | fecha vacía o imposible (p. ej. 31/02) |
| `unidades_invalidas` | vacío, 0 o negativo |
| `precio_invalido` | vacío, 0 o negativo |
| `campo_vacio` | sucursal, región o producto vacíos |
| `duplicado` | misma fecha, sucursal, producto, unidades y precio |
