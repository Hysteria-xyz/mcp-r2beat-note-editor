#!/usr/bin/env python3
"""CLI utility for inspecting, validating, and transforming R2Beat XML charts."""

from __future__ import annotations

import argparse
import os
import sys

from r2beat.chart import parse_xml, chart_to_bytes
from r2beat.validator import validate, auto_fix_all
from r2beat.musictxt import format_entry, append_entry, read_next_index, path_for_chart


def cmd_info(args):
    with open(args.chart, "rb") as f:
        chart = parse_xml(f.read())
    base_bpm = chart.tempos[0].bpm if chart.tempos else 0.0
    val = validate(chart)
    stats = val["stats"]

    print(f"=== R2Beat Chart: {chart.name or '(No Title)'} ===")
    print(f"BGM:              {chart.bgm or '(None)'} (Vol: {chart.volume:.2f})")
    print(f"Base BPM:         {base_bpm}")
    print(f"Tempo Points:     {len(chart.tempos)}")
    print(f"Delay:            {chart.delay} frames")
    print(f"Length:           {chart.length} frames")
    print(f"Total Notes:      {stats['num_notes']}")
    print(f"  - Singles:      {stats['num_singles']}")
    print(f"  - Holds:        {stats['num_holds']}")
    print(f"  - Ramps (Jump): {stats['num_ramps']}")
    print(f"  - Stars:        {stats['num_stars']}")
    print(f"Duration:         {stats['duration_sec']}s")
    print(f"Avg / Peak NPS:   {stats['avg_nps']} / {stats['peak_nps']}")
    print(f"Difficulty Star:  {'★' * stats['difficulty_level']} ({stats['difficulty_level']}/20)")
    print(f"Valid:            {'YES' if val['ok'] else 'NO'}")


def cmd_validate(args):
    with open(args.chart, "rb") as f:
        chart = parse_xml(f.read())
    val = validate(chart)

    if val["ok"]:
        print(f"✓ Chart '{args.chart}' is structurally VALID.")
    else:
        print(f"✗ Chart '{args.chart}' has {len(val['errors'])} ERROR(S):")
        for err in val["errors"]:
            print(f"  - [ERROR] {err}")

    if val["warnings"]:
        print(f"⚠ {len(val['warnings'])} WARNING(S):")
        for warn in val["warnings"]:
            print(f"  - [WARN]  {warn}")

    stats = val["stats"]
    print(f"\nStats: {stats['num_notes']} notes, ~{stats['duration_sec']}s, Difficulty: {stats['difficulty_level']}/20")
    if not val["ok"]:
        sys.exit(1)


def cmd_mirror(args):
    with open(args.input, "rb") as f:
        chart = parse_xml(f.read())
    flipped = chart.mirror_notes()
    out_path = args.output or args.input
    data = chart_to_bytes(chart)
    with open(out_path, "wb") as f:
        f.write(data)
    print(f"✓ Mirrored {flipped} notes. Saved to: {out_path}")


def cmd_shift(args):
    with open(args.input, "rb") as f:
        chart = parse_xml(f.read())
    shifted = chart.shift_notes(delta_coord=args.coords)
    out_path = args.output or args.input
    data = chart_to_bytes(chart)
    with open(out_path, "wb") as f:
        f.write(data)
    print(f"✓ Shifted {shifted} notes by {args.coords} coords. Saved to: {out_path}")


def cmd_autofix(args):
    with open(args.input, "rb") as f:
        chart = parse_xml(f.read())
    fix_res = auto_fix_all(chart)
    out_path = args.output or args.input
    data = chart_to_bytes(chart)
    with open(out_path, "wb") as f:
        f.write(data)
    print(f"✓ Autofix complete. Removed duplicates: {fix_res['removed_duplicates']}, Length: {fix_res['fixed_length']}. Saved to: {out_path}")


def main():
    parser = argparse.ArgumentParser(description="R2Beat Chart Editor CLI Tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Info
    p_info = subparsers.add_parser("info", help="Display chart metadata and stats")
    p_info.add_argument("chart", help="Path to .xml chart")
    p_info.set_defaults(func=cmd_info)

    # Validate
    p_val = subparsers.add_parser("validate", help="Validate chart structure")
    p_val.add_argument("chart", help="Path to .xml chart")
    p_val.set_defaults(func=cmd_validate)

    # Mirror
    p_mir = subparsers.add_parser("mirror", help="Horizontally mirror notes")
    p_mir.add_argument("input", help="Path to input .xml")
    p_mir.add_argument("output", nargs="?", help="Path to output .xml (default: overwrite input)")
    p_mir.set_defaults(func=cmd_mirror)

    # Shift
    p_shift = subparsers.add_parser("shift", help="Shift notes in time by coords")
    p_shift.add_argument("input", help="Path to input .xml")
    p_shift.add_argument("output", nargs="?", help="Path to output .xml (default: overwrite input)")
    p_shift.add_argument("--coords", type=float, required=True, help="Delta coordinates (12 coords = 1 beat)")
    p_shift.set_defaults(func=cmd_shift)

    # Autofix
    p_fix = subparsers.add_parser("autofix", help="Auto-fix levels, duplicate coords, and length")
    p_fix.add_argument("input", help="Path to input .xml")
    p_fix.add_argument("output", nargs="?", help="Path to output .xml (default: overwrite input)")
    p_fix.set_defaults(func=cmd_autofix)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
