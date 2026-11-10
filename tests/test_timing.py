import unittest
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from r2beat.chart import TempoPoint
from r2beat.timing import (
    COORDS_PER_BEAT,
    coords_per_second,
    coord_from_beats,
    coord_from_seconds,
    seconds_from_coord,
    frame_from_coord,
    coord_from_frame,
    snap_to_grid,
    coord_to_frame_multi,
    frame_to_coord_multi,
)


class TestTiming(unittest.TestCase):
    def test_basic_conversions(self):
        bpm = 180.0
        # coords per second = bpm / 5 = 36.0
        self.assertEqual(coords_per_second(bpm), 36.0)
        self.assertEqual(coord_from_beats(2), 24.0)
        self.assertEqual(coord_from_seconds(2.0, bpm), 72.0)
        self.assertEqual(seconds_from_coord(72.0, bpm), 2.0)

        # frame = coord * 300 / bpm
        frame = frame_from_coord(36.0, bpm)
        self.assertEqual(frame, 60.0)
        self.assertEqual(coord_from_frame(60.0, bpm), 36.0)

    def test_snapping(self):
        self.assertEqual(snap_to_grid(11.8, 12), 12.0)
        self.assertEqual(snap_to_grid(5.9, 6), 6.0)
        self.assertEqual(snap_to_grid(3.2, 3), 3.0)

    def test_multi_tempo_timeline(self):
        # Frame 0: BPM 150 -> 30 coords / sec (0.5 coord / frame)
        # Frame 300: BPM 300 -> 60 coords / sec (1.0 coord / frame)
        tempos = [
            TempoPoint(frame=0, bpm=150.0),
            TempoPoint(frame=300, bpm=300.0),
        ]
        # At frame 300: coord = 300 * 150 / 300 = 150.0
        self.assertAlmostEqual(frame_to_coord_multi(300, tempos), 150.0)
        self.assertAlmostEqual(coord_to_frame_multi(150.0, tempos), 300.0)

        # At frame 600: delta_frame = 300, delta_coord = 300 * 300 / 300 = 300
        # total coord = 150 + 300 = 450
        self.assertAlmostEqual(frame_to_coord_multi(600, tempos), 450.0)
        self.assertAlmostEqual(coord_to_frame_multi(450.0, tempos), 600.0)


if __name__ == "__main__":
    unittest.main()
