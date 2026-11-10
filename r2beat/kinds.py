"""R2Beat obstacle kinds and levels (based on real charts and community docs)."""

from __future__ import annotations

SINGLE_KINDS: dict[str, tuple[int, int]] = {
    "up": (16, 3),
    "down": (17, 3),
    "left": (18, 2),
    "right": (19, 2),
    "up_left": (20, 5),
    "up_right": (21, 5),
    "down_left": (22, 4),
    "down_right": (23, 4),
    "ramp": (24, 4),
    "star_left": (26, 1),
    "star_right": (27, 1),
}

HOLD_OFFSETS: dict[str, tuple[int, int, int]] = {
    "up_left": (128, 129, 130),
    "up_right": (131, 132, 133),
    "up": (134, 135, 136),
    "down": (137, 138, 139),
    "left": (140, 141, 142),
    "right": (143, 144, 145),
}

HOLD_LEVEL = 5

KIND_TO_NAME: dict[int, str] = {kind: name for name, (kind, _lvl) in SINGLE_KINDS.items()}
KIND_TO_LEVEL: dict[int, int] = {kind: lvl for name, (kind, lvl) in SINGLE_KINDS.items()}

# Pre-computed sets for fast O(1) checks
HOLD_STARTS: set[int] = {off[0] for off in HOLD_OFFSETS.values()}
HOLD_MIDS: set[int] = {off[1] for off in HOLD_OFFSETS.values()}
HOLD_ENDS: set[int] = {off[2] for off in HOLD_OFFSETS.values()}
ALL_HOLD_KINDS: set[int] = HOLD_STARTS | HOLD_MIDS | HOLD_ENDS

# Horizontal mirroring pairs
MIRROR_KINDS: dict[int, int] = {
    18: 19, 19: 18,  # left <-> right
    20: 21, 21: 20,  # up_left <-> up_right
    22: 23, 23: 22,  # down_left <-> down_right
    26: 27, 27: 26,  # star_left <-> star_right
    # Holds: start, mid, end
    128: 131, 129: 132, 130: 133,  # up_left -> up_right
    131: 128, 132: 129, 133: 130,  # up_right -> up_left
    140: 143, 141: 144, 142: 145,  # left -> right
    143: 140, 144: 141, 145: 142,  # right -> left
}

NAME_ALIASES: dict[str, str] = {
    "ul": "up_left",
    "up-left": "up_left",
    "ur": "up_right",
    "up-right": "up_right",
    "dl": "down_left",
    "down-left": "down_left",
    "dr": "down_right",
    "down-right": "down_right",
    "star": "star_left",
    "jump": "ramp",
    "slide": "ramp",
    "": "left",
}


def normalize(name: str) -> str:
    """Normalize note name string (lowercase, stripped, aliased)."""
    if not isinstance(name, str):
        name = str(name)
    key = name.strip().lower().replace(" ", "_")
    return NAME_ALIASES.get(key, key)


def resolve_single(name: str) -> tuple[int, int]:
    """Resolve single note name to (kind, level)."""
    key = normalize(name)
    if key not in SINGLE_KINDS:
        raise ValueError(
            f"Unknown obstacle '{name}'. Valid: {sorted(SINGLE_KINDS)} or {sorted(HOLD_OFFSETS)} holds."
        )
    return SINGLE_KINDS[key]


def resolve_hold(name: str) -> tuple[int, int, int]:
    """Resolve hold direction name to (start_kind, mid_kind, end_kind)."""
    key = normalize(name)
    if key not in HOLD_OFFSETS:
        raise ValueError(f"Unknown hold '{name}'. Valid: {sorted(HOLD_OFFSETS)}")
    return HOLD_OFFSETS[key]


def kind_name(kind: int) -> str:
    """Return descriptive name of a kind ID."""
    if kind in KIND_TO_NAME:
        return KIND_TO_NAME[kind]
    for h_name, (s, m, e) in HOLD_OFFSETS.items():
        if kind == s:
            return f"hold_{h_name}_start"
        if kind == m:
            return f"hold_{h_name}_mid"
        if kind == e:
            return f"hold_{h_name}_end"
    return f"kind_{kind}"


def is_hold_start(kind: int) -> bool:
    """Check if kind is the start of any hold."""
    return kind in HOLD_STARTS


def is_hold_mid(kind: int) -> bool:
    """Check if kind is an intermediate segment of any hold."""
    return kind in HOLD_MIDS


def is_hold_end(kind: int) -> bool:
    """Check if kind is the end of any hold."""
    return kind in HOLD_ENDS


def is_hold_note(kind: int) -> bool:
    """Check if kind belongs to any hold note (start, mid, or end)."""
    return kind in ALL_HOLD_KINDS


def hold_for_start(kind: int) -> tuple[str, tuple[int, int, int]] | None:
    """Return (direction_name, (start, mid, end)) if kind is a hold start, else None."""
    for name, off in HOLD_OFFSETS.items():
        if kind == off[0]:
            return name, off
    return None


def level_for(kind: int) -> int:
    """Return canonical level for any kind."""
    if kind in KIND_TO_LEVEL:
        return KIND_TO_LEVEL[kind]
    if kind in ALL_HOLD_KINDS:
        return HOLD_LEVEL
    return HOLD_LEVEL


def mirror_kind(kind: int) -> int:
    """Return the horizontally mirrored kind ID (e.g. left <-> right), or self if symmetrical."""
    return MIRROR_KINDS.get(kind, kind)
