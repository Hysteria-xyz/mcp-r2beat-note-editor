"""Validation / helpers for R2Beat charts."""

from .chart import Chart, Note
from .kinds import (
    HOLD_OFFSETS,
    HOLD_LEVEL,
    KIND_TO_LEVEL,
    is_hold_start,
    is_hold_end,
    hold_for_start,
    level_for,
)


def validate(chart):
    issues = []
    notes = sorted(chart.notes, key=lambda n: n.coord)
    if not chart.tempos:
        issues.append(("error", "chart has no BPM points"))
    else:
        if chart.tempos[0].frame != 0:
            issues.append(("error", "first BPM frame must be 0"))
        frames = [t.frame for t in chart.tempos]
        if frames != sorted(frames):
            issues.append(("error", "BPM frames are not sorted"))

    prev = None
    for n in notes:
        if n.coord < 0:
            issues.append(("error", f"note at negative coord {n.coord}"))
        if n.level != level_for(n.kind):
            issues.append(
                (
                    "warn",
                    f"kind {n.kind} uses level {n.level}, expected {level_for(n.kind)}",
                )
            )
        if prev is not None and abs(n.coord - prev.coord) < 1e-9:
            issues.append(("error", f"duplicate note at coord {n.coord}"))
        prev = n

    _validate_holds(notes, issues)

    stats = {
        "num_notes": len(notes),
        "num_holds": sum(1 for n in notes if is_hold_start(n.kind)),
        "first_coord": notes[0].coord if notes else None,
        "last_coord": notes[-1].coord if notes else None,
        "bpm_points": len(chart.tempos),
    }
    errors = [i[1] for i in issues if i[0] == "error"]
    warnings = [i[1] for i in issues if i[0] == "warn"]
    return {"ok": not errors, "errors": errors, "warnings": warnings, "stats": stats}


def _validate_holds(notes, issues):
    by_coord = {(round(n.coord, 6), n.kind): n for n in notes}
    i = 0
    while i < len(notes):
        n = notes[i]
        hit = hold_for_start(n.kind)
        if hit is None:
            i += 1
            continue
        name, (start, mid, end) = hit
        group = [n]
        expected = n.coord + 12
        j = i + 1
        while j < len(notes) and notes[j].coord < expected:
            j += 1
        while j < len(notes) and abs(notes[j].coord - expected) < 1e-6:
            if notes[j].kind == mid:
                group.append(notes[j])
                expected += 12
                j += 1
            else:
                break
        if j < len(notes) and notes[j].kind == end and abs(notes[j].coord - expected) < 1e-6:
            group.append(notes[j])
        else:
            issues.append(("error", f"hold {name} at {n.coord} has no end note at {expected}"))
        if len(group) == 1:
            issues.append(("warn", f"hold {name} at {n.coord} is too short"))
        for m in group:
            if m.level != HOLD_LEVEL:
                issues.append(
                    ("warn", f"hold note at {m.coord} level {m.level} should be {HOLD_LEVEL}")
                )
        i = j


def auto_fix_length(chart):
    """LENGTH is frames; use the last note coord converted to frames."""
    if chart.tempos and chart.notes:
        last = max(n.coord for n in chart.notes)
        frame = last * 300 / chart.tempos[0].bpm
        chart.length = max(chart.length, int(frame) + 60)


def auto_fix_levels(chart):
    for n in chart.notes:
        expected = level_for(n.kind)
        if n.kind in KIND_TO_LEVEL or is_hold_start(n.kind) or is_hold_end(n.kind):
            n.level = expected
    return chart