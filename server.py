"""MCP server exposing R2Beat chart generation as Claude/Agent tools."""

from __future__ import annotations

import os
from typing import Any

try:
    from mcp.server.fastmcp import FastMCP as _Server
except ImportError:
    try:
        from mcp.server.mcpserver import MCPServer as _Server
    except ImportError:
        class _Server:  # type: ignore
            """Lightweight fallback server when mcp package is not installed."""
            def __init__(self, name: str = "r2beat"):
                self.name = name

            def tool(self):
                def decorator(fn):
                    return fn
                return decorator

            def run(self, *args, **kwargs):
                raise RuntimeError(
                    "The 'mcp' package is required to run the MCP server over stdio. "
                    "Please run: pip install mcp"
                )

from r2beat.chart import (
    Chart,
    Note,
    TempoPoint,
    chart_from_dict,
    chart_to_bytes,
    chart_to_dict,
    parse_xml,
)
from r2beat.kinds import resolve_single
from r2beat import patterns
from r2beat import audio as audio_mod
from r2beat import musictxt as musictxt_mod
from r2beat import validator
from r2beat.timing import COORDS_PER_BEAT

mcp = _Server("r2beat")

CHARTS: dict[str, Chart] = {}


def _get(chart_id: str) -> Chart:
    if chart_id not in CHARTS:
        raise ValueError(
            f"Unknown chart_id '{chart_id}'. Existing charts: {list(CHARTS.keys())}. "
            "Call create_chart or load_chart first."
        )
    return CHARTS[chart_id]


def _result(chart: Chart, **extra) -> dict[str, Any]:
    res = chart_to_dict(chart)
    res.update(extra)
    return res


@mcp.tool()
def create_chart(
    chart_id: str,
    name: str,
    bpm: float = 192.0,
    bgm: str = "",
    volume: float = 1.0,
    delay: int = 0,
    length: int = 0,
    encoding: str = "gb18030",
) -> dict[str, Any]:
    """Create a new chart workspace. Grid: 12 coords = 1 beat, 60fps."""
    chart = Chart(
        name=name,
        bgm=bgm,
        volume=volume,
        delay=delay,
        length=length,
        encoding=encoding,
        tempos=[TempoPoint(frame=0, bpm=bpm, original_bpm=bpm)],
    )
    CHARTS[chart_id] = chart
    return _result(chart)


@mcp.tool()
def load_chart(chart_id: str, path: str) -> dict[str, Any]:
    """Load an existing R2Beat XML chart file into the workspace."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Chart file not found: {path}")
    with open(path, "rb") as f:
        data = f.read()
    chart = parse_xml(data)
    CHARTS[chart_id] = chart
    return _result(chart)


@mcp.tool()
def get_chart(chart_id: str) -> dict[str, Any]:
    """Return the full chart contents (notes, tempos, metadata)."""
    return _result(_get(chart_id))


@mcp.tool()
def list_charts() -> list[dict[str, Any]]:
    """List all active chart workspaces in memory with basic statistics."""
    items: list[dict[str, Any]] = []
    for cid, c in CHARTS.items():
        base_bpm = c.tempos[0].bpm if c.tempos else 0.0
        items.append({
            "chart_id": cid,
            "name": c.name,
            "bpm": base_bpm,
            "notes_count": len(c.notes),
            "bgm": c.bgm,
            "delay": c.delay,
        })
    return items


@mcp.tool()
def delete_chart(chart_id: str) -> dict[str, Any]:
    """Delete a chart workspace from memory."""
    if chart_id in CHARTS:
        del CHARTS[chart_id]
        return {"status": "deleted", "chart_id": chart_id}
    return {"status": "not_found", "chart_id": chart_id}


@mcp.tool()
def duplicate_chart(source_chart_id: str, new_chart_id: str) -> dict[str, Any]:
    """Duplicate an existing chart into a new workspace (useful for Easy/Hard difficulty variations)."""
    src = _get(source_chart_id)
    cloned = src.clone()
    CHARTS[new_chart_id] = cloned
    return _result(cloned, cloned_from=source_chart_id, new_chart_id=new_chart_id)


@mcp.tool()
def set_metadata(
    chart_id: str,
    name: str | None = None,
    bgm: str | None = None,
    volume: float | None = None,
    delay: int | None = None,
    length: int | None = None,
) -> dict[str, Any]:
    """Update metadata: name, bgm path, volume, delay (frames), length (frames)."""
    c = _get(chart_id)
    if name is not None:
        c.name = name
    if bgm is not None:
        c.bgm = bgm
    if volume is not None:
        c.volume = volume
    if delay is not None:
        c.delay = int(delay)
    if length is not None:
        c.length = int(length)
    return _result(c)


@mcp.tool()
def set_tempo(chart_id: str, frame: int, bpm: float, original_bpm: float | None = None) -> dict[str, Any]:
    """Add/update a tempo change at a frame. Use frame 0 for the base tempo."""
    c = _get(chart_id)
    c.tempos = [t for t in c.tempos if t.frame != int(frame)]
    c.tempos.append(TempoPoint(frame=int(frame), bpm=bpm, original_bpm=original_bpm))
    c.sorted()
    return _result(c)


@mcp.tool()
def add_pattern(
    chart_id: str,
    start_coord: float,
    end_coord: float,
    division: int | float = 4,
    note_types: list[str] | None = None,
    strategy: str = "alternate",
    seed: int | None = None,
) -> dict[str, Any]:
    """Place a stream of notes from start_coord to end_coord.

    division = notes per beat (1..12) or a raw coord step.
    note_types = ["up","down","left","right","up_left","up_right","down_left",
    "down_right","ramp","star_left","star_right"].
    strategy = alternate | sequence | pingpong | random | walk.
    """
    if note_types is None:
        note_types = ["left", "down", "up", "right"]
    c = _get(chart_id)
    added = patterns.build_stream(start_coord, end_coord, division, note_types, strategy, seed)
    for coord, kind, lvl in added:
        c.notes.append(Note(coord=coord, kind=kind, level=lvl))
    c.sorted()
    return _result(c, added="count", count=len(added))


@mcp.tool()
def add_hold(chart_id: str, direction: str, start_coord: float, end_coord: float) -> dict[str, Any]:
    """Add a long note. direction in [up,down,left,right,up_left,up_right].

    Min length is 12 coords (1 beat); length is auto-snapped to multiples of 12."""
    c = _get(chart_id)
    added = patterns.build_hold(start_coord, end_coord, direction)
    for coord, kind, lvl in added:
        c.notes.append(Note(coord=coord, kind=kind, level=lvl))
    c.sorted()
    return _result(c, added="count", count=len(added))


@mcp.tool()
def add_note(chart_id: str, note_type: str, coord: float) -> dict[str, Any]:
    """Add a single note at an exact coord."""
    c = _get(chart_id)
    kind, lvl = resolve_single(note_type)
    c.notes.append(Note(coord=float(coord), kind=kind, level=lvl))
    c.sorted()
    return _result(c)


@mcp.tool()
def shift_notes(
    chart_id: str,
    delta_coord: float,
    start_coord: float | None = None,
    end_coord: float | None = None,
) -> dict[str, Any]:
    """Shift notes forward or backward in the given coordinate range."""
    c = _get(chart_id)
    shifted = c.shift_notes(float(delta_coord), start_coord, end_coord)
    return _result(c, shifted_count=shifted)


@mcp.tool()
def mirror_chart(
    chart_id: str,
    start_coord: float | None = None,
    end_coord: float | None = None,
) -> dict[str, Any]:
    """Mirror notes horizontally (left <-> right, up_left <-> up_right, down_left <-> down_right)."""
    c = _get(chart_id)
    mirrored = c.mirror_notes(start_coord, end_coord)
    return _result(c, mirrored_count=mirrored)


@mcp.tool()
def scale_chart(
    chart_id: str,
    factor: float,
    origin_coord: float = 0.0,
) -> dict[str, Any]:
    """Scale chart note coordinates by factor (e.g. 2.0 = half speed, 0.5 = double speed)."""
    c = _get(chart_id)
    scaled = c.scale_coords(float(factor), float(origin_coord))
    return _result(c, scaled_count=scaled)


@mcp.tool()
def analyze_audio(path: str) -> dict[str, Any]:
    """Analyze an audio file: BPM, duration, onsets, leading silence (framed @60fps)."""
    return audio_mod.summary(path)


@mcp.tool()
def onsets_to_notes(
    chart_id: str,
    audio_path: str,
    note_type: str = "down",
    division: int | float = 4,
    max_notes: int = 500,
    offset_coord: float = 0.0,
) -> dict[str, Any]:
    """Detect onsets and place notes on the nearest grid coord.

    division = notes per beat to snap to. Returns counts per note."""
    c = _get(chart_id)
    bpm = c.tempos[0].bpm if c.tempos else 192.0
    onsets = audio_mod.detect_onsets(audio_path, top_n=max_notes)
    coords = audio_mod.onsets_to_coords(onsets, bpm)
    step = patterns.division_step(division)
    kind, lvl = resolve_single(note_type)
    placed = 0
    seen = set()
    for raw in coords:
        snapped = round(raw / step) * step + float(offset_coord)
        if snapped in seen:
            continue
        if snapped < 0:
            continue
        seen.add(snapped)
        c.notes.append(Note(coord=snapped, kind=kind, level=lvl))
        placed += 1
    c.sorted()
    return _result(c, added="count", count=placed)


@mcp.tool()
def remove_notes(chart_id: str, start_coord: float | None = None, end_coord: float | None = None) -> dict[str, Any]:
    """Remove notes between start_coord and end_coord (inclusive); defaults to all."""
    c = _get(chart_id)
    before = len(c.notes)
    if start_coord is None and end_coord is None:
        c.notes = []
    else:
        kept = [
            n
            for n in c.notes
            if (start_coord is not None and n.coord < float(start_coord))
            or (end_coord is not None and n.coord > float(end_coord))
        ]
        c.notes = kept
    return _result(c, removed=before - len(c.notes))


@mcp.tool()
def snap_chart(chart_id: str, division: int | float = 4) -> dict[str, Any]:
    """Snap all notes to the grid of `division` notes per beat."""
    c = _get(chart_id)
    step = patterns.division_step(division)
    for n in c.notes:
        n.coord = round(n.coord / step) * step
    c.sorted()
    return _result(c)


@mcp.tool()
def validate_chart(chart_id: str) -> dict[str, Any]:
    """Validate structure. Returns ok/errors/warnings and stats."""
    return validator.validate(_get(chart_id))


@mcp.tool()
def auto_fix_chart(chart_id: str) -> dict[str, Any]:
    """Automatically fix common issues: sort notes, normalize levels, remove duplicate coords, and update length."""
    c = _get(chart_id)
    fix_res = validator.auto_fix_all(c)
    val_res = validator.validate(c)
    return {**fix_res, "validation": val_res}


@mcp.tool()
def get_chart_summary(chart_id: str) -> dict[str, Any]:
    """Get rich chart metrics including estimated difficulty star level, NPS, and obstacle counts."""
    c = _get(chart_id)
    val = validator.validate(c)
    return {
        "chart_id": chart_id,
        "name": c.name,
        "stats": val["stats"],
        "is_valid": val["ok"],
    }


@mcp.tool()
def save_chart(chart_id: str, path: str) -> dict[str, Any]:
    """Save chart to an .xml file using the R2Beat TITLE format (mb encoding)."""
    c = _get(chart_id)
    validator.auto_fix_length(c)
    validator.auto_fix_levels(c)
    data = chart_to_bytes(c)
    dir_name = os.path.dirname(os.path.abspath(path))
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)
    return {"saved_to": path, "bytes": len(data), **validator.validate(c)}


@mcp.tool()
def write_music_entry(
    chart_id: str,
    music_txt_path: str,
    index: int | None = None,
    image: str | None = None,
    file: str | None = None,
    level: int = 17,
    genre: str = "Electronica",
    artist: str = "",
    coin: str = "0",
) -> dict[str, Any]:
    """Append a <Music> entry to rnr_script/music.txt."""
    c = _get(chart_id)
    folder = os.path.dirname(c.bgm.replace("\\", "/")).replace("\\", "/")
    file = file or (f"{folder}/{c.name}.xml" if folder else f"{c.name}/{c.name}.xml")
    image = image or (f"{folder}/{c.name}.bmp" if folder else f"{c.name}/{c.name}.bmp")
    if index is None:
        index = musictxt_mod.read_next_index(music_txt_path)
    entry = musictxt_mod.format_entry(
        index=index,
        name=c.name,
        image=image,
        file=file,
        level=level,
        genre=genre,
        artist=artist,
        coin=coin,
    )
    musictxt_mod.append_entry(music_txt_path, entry, c.encoding)
    return {
        "index": index,
        "entry": entry,
        "appended_to": os.path.abspath(music_txt_path),
    }


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
