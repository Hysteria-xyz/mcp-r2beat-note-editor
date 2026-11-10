import unittest
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from r2beat.patterns import (
    division_step,
    build_stream,
    build_hold,
    snap_pattern_notes,
    mirror_pattern_notes,
)


class TestPatterns(unittest.TestCase):
    def test_division_step(self):
        self.assertEqual(division_step(1), 12.0)
        self.assertEqual(division_step(2), 6.0)
        self.assertEqual(division_step(3), 4.0)
        self.assertEqual(division_step(4), 3.0)
        self.assertEqual(division_step(6), 2.0)
        self.assertEqual(division_step(8), 1.5)
        self.assertEqual(division_step(12), 1.0)
        self.assertEqual(division_step(5.0), 5.0)

        with self.assertRaises(ValueError):
            division_step(0)

    def test_build_stream_strategies(self):
        # alternate
        stream = build_stream(0, 12, division=4, note_types=["left", "right"], strategy="alternate")
        # positions: 0, 3, 6, 9, 12 (5 notes)
        self.assertEqual(len(stream), 5)
        kinds = [k for _, k, _ in stream]
        self.assertEqual(kinds, [18, 19, 18, 19, 18])

        # pingpong
        pp = build_stream(0, 18, division=2, note_types=["left", "down", "up"], strategy="pingpong")
        pp_kinds = [k for _, k, _ in pp]
        # cycle is [left, down, up, down]
        self.assertEqual(pp_kinds[:4], [18, 17, 16, 17])

        # random
        rnd = build_stream(0, 24, division=4, note_types=["left", "down", "up", "right"], strategy="random", seed=42)
        self.assertEqual(len(rnd), 9)

    def test_build_hold_snapping(self):
        # Even if raw end is 18 (1.5 beats), it should snap to nearest multiple of 12 (e.g. 24)
        hold = build_hold(start=0, end=18, direction="up")
        self.assertEqual(hold[0][0], 0.0)    # start
        self.assertEqual(hold[0][1], 134)    # up start
        self.assertEqual(hold[1][0], 12.0)   # mid
        self.assertEqual(hold[1][1], 135)    # up mid
        self.assertEqual(hold[2][0], 24.0)   # end
        self.assertEqual(hold[2][1], 136)    # up end

    def test_mirror_pattern_notes(self):
        notes = [(0.0, 18, 2), (6.0, 20, 5)]  # left, up_left
        mirrored = mirror_pattern_notes(notes)
        self.assertEqual(mirrored[0][1], 19)  # right
        self.assertEqual(mirrored[1][1], 21)  # up_right


if __name__ == "__main__":
    unittest.main()
