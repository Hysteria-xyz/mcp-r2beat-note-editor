# mcp-r2beat note editor

Servidor MCP (Model Context Protocol) y suite de utilidades para generar charts nativos de **R2Beat / R2Note** desde audio o descripciones en lenguaje natural.

Permite a un asistente de IA (como Claude u OpenCode) detectar el BPM y los onsets de una canción, crear patrones rítmicos, colocar notas largas (holds), validar la estructura según el formato del juego, guardar el archivo `.xml` compatible (codificación `gb18030`) y registrar la canción en `rnr_script/music.txt`.

---

## Novedades y Mejoras (v0.2.0)

- **Snapping estricto y seguro de notas largas (Holds):** Las holds ahora ajustan automáticamente su longitud a múltiplos exactos de 12 coords (mínimo 1 beat), garantizando notas válidas y sin roturas de validación.
- **Validación avanzada de Holds:** Detección de notas intermedias y finales huérfanas (sin inicio correspondiente).
- **Cálculo multi-tempo preciso:** Conversión exacta de coordenadas a frames a lo largo de múltiples cambios de BPM en la canción.
- **Dificultad estimada y métricas de juego:** Cálculo automático de estrellas de dificultad (1 a 20), densidad media y pico de notas por segundo (NPS).
- **Herramienta CLI integrada (`cli.py`):** Inspecciona, valida, espeja (mirror) y desplaza notas directamente desde la terminal.
- **Nuevas Tools MCP:**
  - `list_charts`: Lista todos los charts activos en memoria.
  - `delete_chart`: Libera un workspace de chart.
  - `duplicate_chart`: Clona un chart para crear variaciones de dificultad (Normal, Hard, Club).
  - `shift_notes`: Desplaza notas en tiempo (adelantar/retrasar coordenadas).
  - `mirror_chart`: Espeja notas horizontalmente (izquierda <-> derecha).
  - `scale_chart`: Escala el espaciado temporal de las notas (acelerar / ralentizar).
  - `auto_fix_chart`: Limpieza automática de duplicados, niveles y longitud total.
  - `get_chart_summary`: Resumen detallado con métricas y nivel de dificultad.
- **Suite de pruebas unitarias:** 25 pruebas unitarias estándar con `unittest` sin dependencias externas obligatorias.

---

## Tools MCP Disponibles (23 Tools)

| Tool | Descripción |
|---|---|
| `create_chart` | Crea un workspace de chart vacío (rejilla: 12 coords = 1 beat, 60 fps). |
| `load_chart` | Carga un `.xml` existente de R2Beat. |
| `get_chart` | Devuelve todo el contenido del chart (metadata, tempos, notas). |
| `list_charts` | Lista los workspaces en memoria con información resumida. |
| `delete_chart` | Elimina un chart de la memoria. |
| `duplicate_chart` | Clona un chart existente para generar nuevas variantes. |
| `set_metadata` | Modifica título, BGM, volumen, delay y longitud. |
| `set_tempo` | Añade o modifica un punto de tempo (frame 0 = base). |
| `add_pattern` | Coloca una secuencia de notas (`alternate`, `sequence`, `pingpong`, `random`, `walk`). |
| `add_hold` | Añade una nota larga con auto-ajuste de longitud y notas intermedias. |
| `add_note` | Añade una nota simple en una coordenada exacta. |
| `shift_notes` | Desplaza notas en el rango de coordenadas especificado. |
| `mirror_chart` | Espeja las notas horizontalmente (ej. `left` ↔ `right`, `star_left` ↔ `star_right`). |
| `scale_chart` | Escala el espaciado de coordenadas por un factor. |
| `analyze_audio` | Analiza audio MP3/WAV (BPM, duración, onsets, silencio inicial). |
| `onsets_to_notes` | Mapea automáticamente los golpes del audio a notas en la rejilla. |
| `remove_notes` | Elimina notas por rango de coordenadas o todas. |
| `snap_chart` | Ajusta todas las notas a una división rítmica específica. |
| `validate_chart` | Valida estructura y devuelve errores, advertencias y estadísticas. |
| `auto_fix_chart` | Limpia duplicados, normaliza niveles y ajusta `LENGTH` automáticamente. |
| `get_chart_summary` | Obtiene resumen con dificultad calculada (1 a 20 estrellas) y NPS. |
| `save_chart` | Guarda el `.xml` del chart en formato nativo R2Beat (`gb18030`). |
| `write_music_entry` | Registra la canción en `rnr_script/music.txt`. |

---

## Rejilla de Tiempo

- **1 pulso (beat)** = **12 coords**; R2Beat corre a **60 fps**.
- Coords por segundo = `BPM / 5`
- `Frame = Coord * 300 / BPM`
- `Coord = Frame * BPM / 300`

| División | Paso en coords | Nota musical |
|---|---|---|
| 1 | 12 | Negra |
| 2 | 6 | Corchea |
| 3 | 4 | Tresillo de negra |
| 4 | 3 | Semicorchea |
| 6 | 2 | Tresillo de corchea |
| 8 | 1.5 | Fusa |
| 12 | 1.0 | Rejilla máxima |

---

## Tipos de Nota

- **Singles:**
  - `up`: 16 (Nivel 3)
  - `down`: 17 (Nivel 3)
  - `left`: 18 (Nivel 2)
  - `right`: 19 (Nivel 2)
  - `up_left`: 20 (Nivel 5)
  - `up_right`: 21 (Nivel 5)
  - `down_left`: 22 (Nivel 4)
  - `down_right`: 23 (Nivel 4)
  - `ramp`: 24 (Nivel 4, salto)
  - `star_left`: 26 (Nivel 1, estrella izquierda)
  - `star_right`: 27 (Nivel 1, estrella derecha)
- **Holds (Notas Largas):**
  - Direcciones: `up`, `down`, `left`, `right`, `up_left`, `up_right` (Nivel 5).
  - Tienen inicio, nodos intermedios cada 12 coords y nodo de cierre.

---

## Instalación

```bash
# Instalación base
pip install -r requirements.txt

# O como paquete editable:
pip install -e .
```

---

## Uso desde Línea de Comandos (CLI)

El proyecto incluye la utilidad `cli.py`:

```bash
# Ver información y dificultad calculada de un chart:
python cli.py info ruta/al/chart.xml

# Validar integridad estructural:
python cli.py validate ruta/al/chart.xml

# Espejar notas horizontalmente:
python cli.py mirror entrada.xml salida.xml

# Desplazar notas 12 coordenadas (1 pulso):
python cli.py shift entrada.xml salida.xml --coords 12

# Corregir duplicados, niveles y longitud automáticamente:
python cli.py autofix entrada.xml salida.xml
```

---

## Ejecución de Tests

```bash
# Ejecutar toda la suite de pruebas unitarias:
python -m unittest discover -s tests -p "test_*.py"

# Ejecutar test de flujo de integración (end-to-end):
python tests/test_e2e.py

# Probar conexión MCP (requiere mcp instalado):
python tests/test_mcp.py
```
