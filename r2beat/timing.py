"""Timing conversions between coords, frames, seconds and beats for R2Beat.

Grid: 1 beat = 12 coords. R2Beat runs at 60 fps.
coords-per-second = bpm / 5.
Frame<->coord conversion used by the community: F = Coord * 300 / BPM.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .chart import TempoPoint

COORDS_PER_BEAT = 12
FPS = 60
FRAME_FACTOR = 300  # 60 fps * 5


def coords_per_second(bpm: float) -> float:
    return float(bpm) / 5.0


def coord_from_beats(beats: float) -> float:
    return float(beats) * COORDS_PER_BEAT


def coord_from_seconds(seconds: float, bpm: float) -> float:
    return float(seconds) * coords_per_second(bpm)


def seconds_from_coord(coord: float, bpm: float) -> float:
    cps = coords_per_second(bpm)
    if cps <= 0:
        return 0.0
    return float(coord) / cps


def frame_from_coord(coord: float, bpm: float) -> float:
    if bpm <= 0:
        return 0.0
    return float(coord) * FRAME_FACTOR / float(bpm)


def coord_from_frame(frame: float, bpm: float) -> float:
    return float(frame) * float(bpm) / FRAME_FACTOR


def beat_from_frame(frame: float, bpm: float) -> float:
    return float(frame) * float(bpm) / (FPS * COORDS_PER_BEAT)


def frame_from_seconds(seconds: float) -> float:
    return float(seconds) * FPS


def snap_to_grid(coord: float, division: float = COORDS_PER_BEAT) -> float:
    if division <= 0:
        return coord
    return round(float(coord) / float(division)) * float(division)


def snap_to_grid_floor(coord: float, division: float = COORDS_PER_BEAT) -> float:
    if division <= 0:
        return coord
    return (float(coord) // float(division)) * float(division)


def snap_to_grid_ceil(coord: float, division: float = COORDS_PER_BEAT) -> float:
    if division <= 0:
        return coord
    return ((float(coord) // float(division)) + 1) * float(division)


def coord_to_frame_multi(coord: float, tempos: list[Any]) -> float:
    """Accurately convert a coord to frame accounting for multiple tempo changes.

    tempos should be sorted by frame.
    """
    if not tempos:
        return float(coord) * FRAME_FACTOR / 192.0

    # Build segments: [(start_frame, start_coord, bpm), ...]
    segments: list[tuple[float, float, float]] = []
    curr_coord = 0.0
    for i, t in enumerate(tempos):
        t_frame = float(t.frame)
        t_bpm = float(t.bpm)
        if i == 0:
            segments.append((t_frame, 0.0, t_bpm))
        else:
            prev_frame, prev_coord, prev_bpm = segments[-1]
            delta_frame = max(0.0, t_frame - prev_frame)
            delta_coord = delta_frame * prev_bpm / FRAME_FACTOR
            curr_coord = prev_coord + delta_coord
            segments.append((t_frame, curr_coord, t_bpm))

    # Find which segment contains coord
    for i in range(len(segments) - 1, -1, -1):
        seg_frame, seg_coord, seg_bpm = segments[i]
        if coord >= seg_coord or i == 0:
            delta_c = coord - seg_coord
            delta_f = (delta_c * FRAME_FACTOR / seg_bpm) if seg_bpm > 0 else 0.0
            return max(0.0, seg_frame + delta_f)

    return 0.0


def frame_to_coord_multi(frame: float, tempos: list[Any]) -> float:
    """Accurately convert a frame to coord accounting for multiple tempo changes."""
    if not tempos:
        return float(frame) * 192.0 / FRAME_FACTOR

    segments: list[tuple[float, float, float]] = []
    curr_coord = 0.0
    for i, t in enumerate(tempos):
        t_frame = float(t.frame)
        t_bpm = float(t.bpm)
        if i == 0:
            segments.append((t_frame, 0.0, t_bpm))
        else:
            prev_frame, prev_coord, prev_bpm = segments[-1]
            delta_frame = max(0.0, t_frame - prev_frame)
            delta_coord = delta_frame * prev_bpm / FRAME_FACTOR
            curr_coord = prev_coord + delta_coord
            segments.append((t_frame, curr_coord, t_bpm))

    for i in range(len(segments) - 1, -1, -1):
        seg_frame, seg_coord, seg_bpm = segments[i]
        if frame >= seg_frame or i == 0:
            delta_f = frame - seg_frame
            delta_c = delta_f * seg_bpm / FRAME_FACTOR
            return max(0.0, seg_coord + delta_c)

    return 0.0
