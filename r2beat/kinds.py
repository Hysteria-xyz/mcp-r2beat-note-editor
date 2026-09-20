"""R2Beat obstacle kinds and levels (based on real charts and community docs)."""

SINGLE_KINDS = {
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

HOLD_OFFSETS = {
    "up_left": (128, 129, 130),
    "up_right": (131, 132, 133),
    "up": (134, 135, 136),
    "down": (137, 138, 139),
    "left": (140, 141, 142),
    "right": (143, 144, 145),
}

HOLD_LEVEL = 5

KIND_TO_NAME = {kind: name for name, (kind, _lvl) in SINGLE_KINDS.items()}
KIND_TO_LEVEL = {kind: lvl for name, (kind, lvl) in SINGLE_KINDS.items()}

NAME_ALIASES = {
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


def normalize(name):
    key = name.strip().lower().replace(" ", "_")
    return NAME_ALIASES.get(key, key)


def resolve_single(name):
    key = normalize(name)
    if key not in SINGLE_KINDS:
        raise ValueError(
            f"Unknown obstacle '{name}'. Valid: {sorted(SINGLE_KINDS)} or {sorted(HOLD_OFFSETS)} holds."
        )
    return SINGLE_KINDS[key]


def resolve_hold(name):
    key = normalize(name)
    if key not in HOLD_OFFSETS:
        raise ValueError(f"Unknown hold '{name}'. Valid: {sorted(HOLD_OFFSETS)}")
    return HOLD_OFFSETS[key]


def kind_name(kind):
    return KIND_TO_NAME.get(kind, f"kind{kind}")


def is_hold_start(kind):
    return any(kind == off[0] for off in HOLD_OFFSETS.values())


def is_hold_end(kind):
    return any(kind == off[2] for off in HOLD_OFFSETS.values())


def hold_for_start(kind):
    for name, off in HOLD_OFFSETS.items():
        if kind == off[0]:
            return name, off
    return None


def level_for(kind):
    if kind in (kind_val for kind_val, lvl in SINGLE_KINDS.values()):
        for k, lvl in SINGLE_KINDS.values():
            if k == kind:
                return lvl
    return HOLD_LEVEL