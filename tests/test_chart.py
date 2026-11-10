import unittest
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from r2beat.chart import (
    Chart,
    Note,
    TempoPoint,
    chart_to_xml,
    chart_to_bytes,
    parse_xml,
)


class TestChart(unittest.TestCase):
    def test_roundtrip_xml(self):
        chart = Chart(
            name="Sample Track",
            bgm="Sample/track.mp3",
            volume=0.9,
            delay=15,
            length=1200,
            star="5",
            tempos=[TempoPoint(frame=0, bpm=175.0, original_bpm=175.0)],
            notes=[
                Note(coord=0.0, kind=18, level=2),
                Note(coord=12.0, kind=19, level=2),
            ],
        )

        xml = chart_to_xml(chart)
        self.assertIn('<TITLE Name="Sample Track"', xml)
        self.assertIn('<BPM Frame="0" BPM="175"', xml)
        self.assertIn('<AREA Coord="0" Kind="18"', xml)

        # Parse string
        parsed = parse_xml(xml)
        self.assertEqual(parsed.name, "Sample Track")
        self.assertEqual(len(parsed.notes), 2)
        self.assertEqual(parsed.tempos[0].bpm, 175.0)

        # Parse bytes
        raw_bytes = chart_to_bytes(chart)
        parsed_b = parse_xml(raw_bytes)
        self.assertEqual(parsed_b.name, "Sample Track")

    def test_shift_and_mirror(self):
        chart = Chart(
            name="Mod Test",
            notes=[
                Note(coord=10.0, kind=18, level=2),  # left
                Note(coord=20.0, kind=19, level=2),  # right
            ],
        )

        # Shift
        shifted = chart.shift_notes(delta_coord=5.0)
        self.assertEqual(shifted, 2)
        self.assertEqual(chart.notes[0].coord, 15.0)
        self.assertEqual(chart.notes[1].coord, 25.0)

        # Mirror
        mirrored = chart.mirror_notes()
        self.assertEqual(mirrored, 2)
        self.assertEqual(chart.notes[0].kind, 19)  # left -> right
        self.assertEqual(chart.notes[1].kind, 18)  # right -> left


if __name__ == "__main__":
    unittest.main()
