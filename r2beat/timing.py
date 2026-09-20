"""Timing conversions between coords, frames, seconds and beats for R2Beat.

Grid: 1 beat = 12 coords. R2Beat runs at 60 fps.
coords-per-second = bpm / 5.
Frame<->coord conversion used by the community: F = Coord * 300 / BPM.
"""

COORDS_PER_BEAT = 12
FPS = 60
FRAME_FACTOR = 300  # 60 fps * 5


def coords_per_second(bpm):
    return bpm / 5.0


def coord_from_beats(beats):
    return beats * COORDS_PER_BEAT


def coord_from_seconds(seconds, bpm):
    return seconds * coords_per_second(bpm)


def seconds_from_coord(coord, bpm):
    return coord / coords_per_second(bpm)


def frame_from_coord(coord, bpm):
    return coord * FRAME_FACTOR / bpm


def coord_from_frame(frame, bpm):
    return frame * bpm / FRAME_FACTOR


def beat_from_frame(frame, bpm):
    return frame * bpm / (FPS * COORDS_PER_BEAT)


def frame_from_seconds(seconds):
    return seconds * FPS


def snap_to_grid(coord, division=COORDS_PER_BEAT):
    return round(coord / division) * division


def snap_to_grid_floor(coord, division=COORDS_PER_BEAT):
    return int(coord // division) * division


def snap_to_grid_ceil(coord, division=COORDS_PER_BEAT):
    return (int(coord // division) + 1) * division