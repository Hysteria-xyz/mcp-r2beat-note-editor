"""Pattern generator producing R2Beat note layouts on the 12-coords-per-beat grid."""

import random

from .kinds import KIND_TO_LEVEL, HOLD_LEVEL, resolve_single, resolve_hold
from .timing import COORDS_PER_BEAT, snap_to_grid

DIVISIONS = {
    1: COORDS_PER_BEAT,        # quarter (12 coords)
    2: COORDS_PER_BEAT // 2,   # eighth (6 coords)
    3: COORDS_PER_BEAT // 3,   # triplet (4 coords)
    4: COORDS_PER_BEAT // 4,   # sixteenth (3 coords)
    6: COORDS_PER_BEAT // 6,   # sixteenth triplet (2 coords)
    8: 1.5,                    # 32nd (1.5 coords)
    12: 1.0,                   # 64th (1 coord)
}


def division_step(division):
    if division in DIVISIONS:
        return DIVISIONS[division]
    step = float(division)
    if step <= 0:
        raise ValueError("division must be a positive coord step")
    return step


def build_stream(start, end, division, note_types, strategy="alternate", seed=None):
    step = division_step(division)
    positions = []
    coord = float(start)
    while coord <= float(end) + 1e-9:
        positions.append(coord)
        coord += step
    if not positions:
        return []
    kinds = [resolve_single(n)[0] for n in note_types]
    if not kinds:
        raise ValueError("note_types must not be empty")
    rng = random.Random(seed)
    result = []
    order = []
    if strategy == "alternate":
        order = kinds * (len(positions) // len(kinds) + 1)
    elif strategy == "sequence":
        order = []
        i = 0
        while len(order) < len(positions):
            order.append(kinds[i % len(kinds)])
            i = (i + 1) % len(kinds) if len(kinds) > 1 else 0
    elif strategy == "random":
        prev = None
        for _ in positions:
            pool = [k for k in kinds if k != prev]
            pick = rng.choice(pool)
            order.append(pick)
            prev = pick if len(kinds) > 1 else None
    elif strategy == "walk":
        base = kinds
        prev_idx = 0
        for _ in positions:
            idx = (prev_idx + rng.choice([1, -1])) % len(base)
            order.append(base[idx])
            prev_idx = idx
    else:
        raise ValueError(f"Unknown strategy '{strategy}'. Valid: alternate, sequence, random, walk")
    for coord, kind in zip(positions, order):
        result.append((coord, kind, KIND_TO_LEVEL[kind]))
    return result


def build_hold(start, end, direction):
    off = resolve_hold(direction)
    start_coord = float(start)
    end_coord = float(end)
    if end_coord - start_coord < COORDS_PER_BEAT:
        end_coord = start_coord + COORDS_PER_BEAT
    notes = [(start_coord, off[0], HOLD_LEVEL)]
    mid = start_coord + COORDS_PER_BEAT
    while mid < end_coord:
        notes.append((mid, off[1], HOLD_LEVEL))
        mid += COORDS_PER_BEAT
    notes.append((end_coord, off[2], HOLD_LEVEL))
    return notes


def build_jump(coord, seed=None):
    rng = random.Random(seed)
    kinds = ["up", "down", "left", "right"]
    return [(coord, resolve_single(rng.choice(kinds))[0], resolve_single(rng.choice(kinds))[1])]


def snap_pattern_notes(notes, division):
    step = division_step(division)
    seen = set()
    out = []
    for coord, kind, lvl in notes:
        snapped = snap_to_grid(coord, step)
        if snapped in seen:
            continue
        seen.add(snapped)
        out.append((snapped, kind, lvl))
    return out