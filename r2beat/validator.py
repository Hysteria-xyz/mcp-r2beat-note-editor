"""Validation and fixing helpers for R2Beat charts."""

from __future__ import annotations

from typing import Any

from .chart import Chart, Note
from .kinds import (
    HOLD_OFFSETS,
    HOLD_LEVEL,
    KIND_TO_LEVEL,
    HOLD_STARTS,
    HOLD_MIDS,
    HOLD_ENDS,
    ALL_HOLD_KINDS,
    is_hold_start,
    is_hold_mid,
    is_hold_end,
    hold_for_start,
    level_for,
    kind_name,
)
from .timing import (
    COORDS_PER_BEAT,
    coord_to_frame_multi,
    seconds_from_coord,
    coords_per_second,
)


def validate(chart: Chart) -> dict[str, Any]:
    """Validate chart structure and return errors, warnings, and comprehensive stats."""
    issues: list[tuple[str, str]] = []
    notes = sorted(chart.notes, key=lambda n: n.coord)

    # 1. Validate BPM / Tempo points
    if not chart.tempos:
        issues.append(("error", "chart has no BPM points"))
    else:
        if chart.tempos[0].frame != 0:
            issues.append(("error", f"first BPM frame must be 0, got {chart.tempos[0].frame}"))
        frames = [t.frame for t in chart.tempos]
        if frames != sorted(frames):
            issues.append(("error", "BPM frames are not sorted in ascending order"))
        for t in chart.tempos:
            if t.bpm <= 0:
                issues.append(("error", f"invalid non-positive BPM {t.bpm} at frame {t.frame}"))

    # 2. Validate individual notes & duplicate coords
    prev: Note | None = None
    for n in notes:
        if n.coord < 0:
            issues.append(("error", f"note at negative coord {n.coord}"))

        expected_lvl = level_for(n.kind)
        if n.level != expected_lvl:
            issues.append(
                (
                    "warn",
                    f"kind {n.kind} ({kind_name(n.kind)}) uses level {n.level}, expected {expected_lvl}",
                )
            )

        if prev is not None and abs(n.coord - prev.coord) < 1e-6:
            issues.append(
                (
                    "error",
                    f"duplicate note collision at coord {n.coord}: kinds {prev.kind} and {n.kind}",
                )
            )
        prev = n

    # 3. Validate Holds (well-formed chains, no orphaned mid/end notes)
    _validate_holds(notes, issues)

    # 4. Compute statistics & difficulty estimation
    stats = _calculate_stats(chart, notes)

    errors = [msg for severity, msg in issues if severity == "error"]
    warnings = [msg for severity, msg in issues if severity == "warn"]

    return {
        "ok": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "stats": stats,
    }


def _validate_holds(notes: list[Note], issues: list[tuple[str, str]]) -> None:
    """Validate hold chains and check for orphaned hold segments."""
    visited_hold_indices: set[int] = set()
    i = 0

    while i < len(notes):
        n = notes[i]
        hit = hold_for_start(n.kind)
        if hit is None:
            i += 1
            continue

        visited_hold_indices.add(i)
        name, (start, mid, end) = hit
        group = [n]
        expected = round(n.coord + COORDS_PER_BEAT, 6)
        j = i + 1

        # Look for intermediate mid notes
        while j < len(notes) and notes[j].coord < expected - 1e-6:
            j += 1

        while j < len(notes) and abs(notes[j].coord - expected) < 1e-6:
            if notes[j].kind == mid:
                group.append(notes[j])
                visited_hold_indices.add(j)
                expected = round(expected + COORDS_PER_BEAT, 6)
                j += 1
            else:
                break

        # Look for hold end note
        if j < len(notes) and notes[j].kind == end and abs(notes[j].coord - expected) < 1e-6:
            group.append(notes[j])
            visited_hold_indices.add(j)
        else:
            issues.append(("error", f"hold {name} starting at coord {n.coord} has no matching end note at {expected}"))

        if len(group) == 1:
            issues.append(("warn", f"hold {name} at {n.coord} is too short"))

        for m in group:
            if m.level != HOLD_LEVEL:
                issues.append(
                    ("warn", f"hold note at {m.coord} level {m.level} should be {HOLD_LEVEL}")
                )

        i += 1

    # Check for orphaned mid or end hold notes
    for idx, n in enumerate(notes):
        if idx not in visited_hold_indices:
            if n.kind in HOLD_MIDS:
                issues.append(("error", f"orphaned hold mid note (kind {n.kind}) at coord {n.coord}"))
            elif n.kind in HOLD_ENDS:
                issues.append(("error", f"orphaned hold end note (kind {n.kind}) at coord {n.coord}"))


def _calculate_stats(chart: Chart, notes: list[Note]) -> dict[str, Any]:
    """Calculate rich stats and difficulty metrics."""
    base_bpm = chart.tempos[0].bpm if chart.tempos else 192.0
    first_c = notes[0].coord if notes else 0.0
    last_c = notes[-1].coord if notes else 0.0

    duration_sec = (last_c - first_c) / coords_per_second(base_bpm) if base_bpm > 0 else 0.0

    num_holds = sum(1 for n in notes if is_hold_start(n.kind))
    num_ramps = sum(1 for n in notes if n.kind == 24)
    num_stars = sum(1 for n in notes if n.kind in (26, 27))
    num_singles = len(notes) - sum(1 for n in notes if is_hold_mid(n.kind) or is_hold_end(n.kind))

    avg_nps = round(len(notes) / duration_sec, 2) if duration_sec > 1.0 else 0.0

    # Calculate peak NPS using rolling 1-second window
    peak_nps = 0.0
    if notes and base_bpm > 0:
        times = [seconds_from_coord(n.coord, base_bpm) for n in notes]
        left_idx = 0
        max_in_window = 0
        for right_idx in range(len(times)):
            while times[right_idx] - times[left_idx] > 1.0:
                left_idx += 1
            max_in_window = max(max_in_window, right_idx - left_idx + 1)
        peak_nps = float(max_in_window)

    # Estimate difficulty rating (1 to 20 stars)
    # Based on base_bpm, average NPS, peak NPS, ramp density, and hold complexity
    score = (avg_nps * 1.5) + (peak_nps * 0.8) + (base_bpm / 40.0)
    difficulty_level = min(20, max(1, round(score / 2.2)))

    return {
        "num_notes": len(notes),
        "num_singles": num_singles,
        "num_holds": num_holds,
        "num_ramps": num_ramps,
        "num_stars": num_stars,
        "first_coord": first_c if notes else None,
        "last_coord": last_c if notes else None,
        "bpm_points": len(chart.tempos),
        "base_bpm": base_bpm,
        "duration_sec": round(duration_sec, 2),
        "avg_nps": avg_nps,
        "peak_nps": peak_nps,
        "difficulty_level": difficulty_level,
    }


def auto_fix_length(chart: Chart) -> None:
    """Calculate and set LENGTH in frames using multi-tempo conversion."""
    if chart.tempos and chart.notes:
        last = max(n.coord for n in chart.notes)
        frame = coord_to_frame_multi(last, chart.tempos)
        chart.length = max(chart.length, int(frame) + 60)


def auto_fix_levels(chart: Chart) -> Chart:
    """Ensure all note levels strictly conform to their canonical obstacle levels."""
    for n in chart.notes:
        n.level = level_for(n.kind)
    return chart


def auto_fix_all(chart: Chart) -> dict[str, Any]:
    """Perform full automatic cleanup: sorts, fixes levels, removes duplicates, and updates length."""
    chart.sorted()
    auto_fix_levels(chart)
    removed_dupes = chart.remove_duplicates()
    auto_fix_length(chart)
    return {
        "removed_duplicates": removed_dupes,
        "fixed_length": chart.length,
        "notes_count": len(chart.notes),
    }
