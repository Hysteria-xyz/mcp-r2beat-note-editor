"""Pattern generator producing R2Beat note layouts on the 12-coords-per-beat grid."""

from __future__ import annotations

import random
from typing import Sequence

from .kinds import (
    KIND_TO_LEVEL,
    HOLD_LEVEL,
    resolve_single,
    resolve_hold,
    mirror_kind,
)
from .timing import COORDS_PER_BEAT, snap_to_grid

DIVISIONS: dict[int | float, float] = {
    1: float(COORDS_PER_BEAT),        # quarter (12 coords)
    2: float(COORDS_PER_BEAT // 2),   # eighth (6 coords)
    3: float(COORDS_PER_BEAT // 3),   # triplet (4 coords)
    4: float(COORDS_PER_BEAT // 4),   # sixteenth (3 coords)
    6: float(COORDS_PER_BEAT // 6),   # sixteenth triplet (2 coords)
    8: 1.5,                           # 32nd (1.5 coords)
    12: 1.0,                          # 64th (1 coord)
}


def division_step(division: int | float) -> float:
    """Return coord step for a given division (notes per beat, or raw coord step)."""
    if division in DIVISIONS:
        return DIVISIONS[division]
    step = float(division)
    if step <= 0:
        raise ValueError("division must be a positive coord step")
    return step


def build_stream(
    start: float,
    end: float,
    division: int | float,
    note_types: Sequence[str],
    strategy: str = "alternate",
    seed: int | None = None,
) -> list[tuple[float, int, int]]:
    """Generate a stream of notes between start and end coordinates.

    strategy can be:
    - alternate: repeat kinds in order [A, B, C, A, B, C...]
    - sequence: sequential order cycling through note_types
    - pingpong / zigzag: bounce back and forth [A, B, C, B, A, B...]
    - random: pick randomly without consecutive duplicate
    - walk: step up or down adjacent kinds in the list
    """
    step = division_step(division)
    positions: list[float] = []
    coord = float(start)
    end_val = float(end)
    while coord <= end_val + 1e-9:
        positions.append(round(coord, 6))
        coord += step

    if not positions:
        return []

    kinds = [resolve_single(n)[0] for n in note_types]
    if not kinds:
        raise ValueError("note_types must not be empty")

    strat = strategy.strip().lower()
    rng = random.Random(seed)
    order: list[int] = []

    if strat == "alternate":
        order = kinds * (len(positions) // len(kinds) + 1)
    elif strat == "sequence":
        i = 0
        while len(order) < len(positions):
            order.append(kinds[i % len(kinds)])
            i = (i + 1) % len(kinds) if len(kinds) > 1 else 0
    elif strat in ("pingpong", "zigzag", "bounce"):
        if len(kinds) <= 2:
            cycle = kinds
        else:
            cycle = kinds + kinds[-2:0:-1]
        order = cycle * (len(positions) // len(cycle) + 1)
    elif strat == "random":
        prev = None
        for _ in positions:
            pool = [k for k in kinds if k != prev] if len(kinds) > 1 else kinds
            pick = rng.choice(pool)
            order.append(pick)
            prev = pick
    elif strat == "walk":
        prev_idx = 0
        for _ in positions:
            if len(kinds) <= 1:
                idx = 0
            else:
                idx = (prev_idx + rng.choice([1, -1])) % len(kinds)
            order.append(kinds[idx])
            prev_idx = idx
    else:
        raise ValueError(
            f"Unknown strategy '{strategy}'. Valid: alternate, sequence, pingpong, random, walk"
        )

    result: list[tuple[float, int, int]] = []
    for pos, kind in zip(positions, order):
        result.append((pos, kind, KIND_TO_LEVEL.get(kind, 2)))
    return result


def build_hold(
    start: float,
    end: float,
    direction: str,
) -> list[tuple[float, int, int]]:
    """Build a hold note from start to end with correct start, mid, and end parts.

    Length is strictly snapped to multiples of COORDS_PER_BEAT (12 coords, min 1 beat).
    """
    off = resolve_hold(direction)
    start_coord = float(start)
    raw_end = float(end)

    # Snapped duration to multiple of 12 coords (min 1 beat = 12 coords)
    raw_len = max(float(COORDS_PER_BEAT), raw_end - start_coord)
    beats = max(1, round(raw_len / COORDS_PER_BEAT))
    snapped_len = float(beats * COORDS_PER_BEAT)
    end_coord = start_coord + snapped_len

    notes: list[tuple[float, int, int]] = [(round(start_coord, 6), off[0], HOLD_LEVEL)]

    # Intermediate notes every 12 coords
    mid = start_coord + COORDS_PER_BEAT
    while mid < end_coord - 1e-6:
        notes.append((round(mid, 6), off[1], HOLD_LEVEL))
        mid += COORDS_PER_BEAT

    notes.append((round(end_coord, 6), off[2], HOLD_LEVEL))
    return notes


def build_jump(coord: float, seed: int | None = None) -> list[tuple[float, int, int]]:
    """Generate a ramp jump obstacle at the given coordinate."""
    kind, lvl = resolve_single("ramp")
    return [(float(coord), kind, lvl)]


def snap_pattern_notes(
    notes: Sequence[tuple[float, int, int]],
    division: int | float,
) -> list[tuple[float, int, int]]:
    """Snap notes to a given division grid and eliminate exact coordinate collisions."""
    step = division_step(division)
    seen: set[float] = set()
    out: list[tuple[float, int, int]] = []
    for coord, kind, lvl in notes:
        snapped = round(snap_to_grid(coord, step), 6)
        if snapped in seen:
            continue
        seen.add(snapped)
        out.append((snapped, kind, lvl))
    return out


def mirror_pattern_notes(
    notes: Sequence[tuple[float, int, int]],
) -> list[tuple[float, int, int]]:
    """Mirror note kinds horizontally (e.g. left <-> right)."""
    return [(coord, mirror_kind(kind), lvl) for coord, kind, lvl in notes]
