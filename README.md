# mcp-r2beat note editor

Servidor MCP (Model Context Protocol) para generar charts nativos de **R2Beat / R2Note** desde audio o descripciones en lenguaje natural.

Permite a un asistente tipo Claude/opencode detectar el BPM y los onsets de un mp3, crear patrones de notas, añadir holds, validar la estructura y guardar el `.xml` compatible con el juego, además de registrarlo en el `music.txt`.

## Características

- Análisis de audio: duración, BPM, onsets, silencio inicial (sugerencia de delay).
- Generación de notas por patrones (alternate, sequence, random, walk) con división desde negras hasta semicorcheas.
- Notas largas (holds) con dirección y duración configurables.
- Notas especiales: salto (ramp), estrellas.
- Validación estructural: duplicados, niveles, BPM ordenados, holds bien cerradas.
- Guardado en formato XML de R2Beat (`<TITLE>` / `<AREA>`) con codificación `gb18030`.
- Registro de la canción en `rnr_script/music.txt` (auto-deriva índice, imagen y archivo).

## Tooles disponibles

| Tool | Descripción |
|---|---|
| `create_chart` | Crea un workspace de chart vacío |
| `load_chart` | Carga un `.xml` existente |
| `get_chart` | Devuelve todo el contenido del chart |
| `set_metadata` | Modifica título, bgm, volumen, delay, length |
| `set_tempo` | Añade/cambia un punto de tempo (frame 0 = base) |
| `add_pattern` | Coloca una sucesión de notas |
| `add_hold` | Añade una nota larga (mín. 12 coords) |
| `add_note` | Añade una nota simple en una coord exacta |
| `analyze_audio` | Analiza mp3/wav (BPM, onsets, silencio) |
| `onsets_to_notes` | Coloca notas automáticas sobre los onsets |
| `remove_notes` | Borra notas por rango o todas |
| `snap_chart` | Ajusta todas las notas a una rejilla |
| `validate_chart` | Valida estructura y devuelve errores/warnings |
| `save_chart` | Guarda el `.xml` del chart |
| `write_music_entry` | Registra la canción en `music.txt` |

## Rejilla de tiempo

- 1 pulso (beat) = **12 coords**; R2Beat va a 60 fps.
- coords por segundo = `BPM / 5`
- `Frame = Coord * 300 / BPM`
- `Coord = Frame * BPM / 300`

| División | Paso en coords |
|---|---|
| 1 (negra) | 12 |
| 2 (corchea) | 6 |
| 3 (tresillo) | 4 |
| 4 (semicorchea) | 3 |

## Tipos de nota

- **Singles:** up=16/L3, down=17/L3, left=18/L2, right=19/L2, up_left=20/L5, up_right=21/L5, down_left=22/L4, down_right=23/L4, ramp=24/L4 (salto), star_left=26/L1, star_right=27/L1.
- **Holds (largas):** up_left=128/129/130, up_right=131/132/133, up=134/135/136, down=137/138/139, left=140/141/142, right=143/144/145. Mínimo 12 coords; nota intermedia cada 12 coords.

## Instalación

```bash
pip install -r requirements.txt
```

## Configuración en opencode

Añade al `opencode.json` (o `~/.config/opencode/opencode.jsonc`):

```jsonc
{
  "mcp": {
    "r2beat": {
      "type": "local",
      "command": [
        "C:\\ruta\\a\\mcp r2beat\\.venv\\Scripts\\python.exe",
        "C:\\ruta\\a\\mcp r2beat\\server.py"
      ],
      "cwd": "C:\\ruta\\a\\mcp r2beat",
      "enabled": true,
      "timeout": 120000
    }
  }
}
```

> En Windows usa rutas absolutas con doble barra. Si cambias el código, reinicia opencode para que recargue el servidor MCP.

Para ejecutarlo manualmente:

```bash
python server.py        # queda esperando mensajes MCP por stdio
```

## Tests

```bash
python tests/test_mcp.py   # lista las 15 tools
python tests/test_e2e.py   # flujo completo (crea, patrón, hold, guarda, recarga)
```

## Formato de salida

```xml
<?xml version="1.0" encoding="gb18030"?>
<TITLE Name="NombreCancion">
<BPM Frame="0" BPM="175"></BPM>
<BGM Name="carpeta/cancion.mp3" Volume="1.00"></BGM>
<DELAY Value="0"></DELAY>
<LENGTH Value="9000"></LENGTH>
<AREA Coord="48" Kind="18" Level="2" FxSndIndex="0"></AREA>
</TITLE>
```

## Estructura del proyecto

```
server.py            # entrada MCP (FastMCP)
r2beat/
  chart.py           # modelo + codec XML del chart
  kinds.py           # tipos de nota y niveles
  patterns.py        # generador de patrones
  timing.py          # rejilla de tiempo (12 coords/beat)
  audio.py           # análisis de audio (BPM, onsets)
  validator.py       # validación estructural
  musictxt.py        # lectura/escritura de music.txt
```