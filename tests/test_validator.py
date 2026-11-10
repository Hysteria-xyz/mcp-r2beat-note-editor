import unittest
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from r2beat.chart import Chart, Note, TempoPoint
from r2beat.validator import validate, auto_fix_all, auto_fix_length


class TestValidator(unittest.TestCase):
    def test_valid_chart(self):
        chart = Chart(
            name="Valid",
            tempos=[TempoPoint(frame=0, bpm=180.0)],
            notes=[
                Note(coord=0.0, kind=18, level=2),
                Note(coord=12.0, kind=19, level=2),
            ],
        )
        res = validate(chart)
        self.assertTrue(res["ok"])
        self.assertEqual(len(res["errors"]), 0)
        self.assertIn("difficulty_level", res["stats"])

    def test_invalid_tempo(self):
        chart = Chart(
            name="No Tempos",
            notes=[Note(coord=0.0, kind=18, level=2)],
        )
        res = validate(chart)
        self.assertFalse(res["ok"])
        self.assertTrue(any("no BPM points" in e for e in res["errors"]))

    def test_broken_and_orphaned_holds(self):
        # Hold start without end
        chart = Chart(
            name="Broken Hold",
            tempos=[TempoPoint(frame=0, bpm=180.0)],
            notes=[
                Note(coord=0.0, kind=134, level=5),  # hold up start
            ],
        )
        res = validate(chart)
        self.assertFalse(res["ok"])
        self.assertTrue(any("no matching end note" in e for e in res["errors"]))

        # Orphaned end note
        chart_orphaned = Chart(
            name="Orphaned End",
            tempos=[TempoPoint(frame=0, bpm=180.0)],
            notes=[
                Note(coord=12.0, kind=136, level=5),  # hold up end without start
            ],
        )
        res_orphaned = validate(chart_orphaned)
        self.assertFalse(res_orphaned["ok"])
        self.assertTrue(any("orphaned" in e for e in res_orphaned["errors"]))

    def test_duplicate_coords(self):
        chart = Chart(
            name="Dup",
            tempos=[TempoPoint(frame=0, bpm=180.0)],
            notes=[
                Note(coord=12.0, kind=18, level=2),
                Note(coord=12.0, kind=19, level=2),
            ],
        )
        res = validate(chart)
        self.assertFalse(res["ok"])
        self.assertTrue(any("duplicate note collision" in e for e in res["errors"]))

    def test_auto_fix_all(self):
        chart = Chart(
            name="To Fix",
            tempos=[TempoPoint(frame=0, bpm=180.0)],
            notes=[
                Note(coord=24.0, kind=18, level=99),  # bad level
                Note(coord=12.0, kind=18, level=2),
                Note(coord=12.0, kind=18, level=2),   # duplicate
            ],
        )
        fix_res = auto_fix_all(chart)
        self.assertEqual(fix_res["removed_duplicates"], 1)
        self.assertEqual(chart.notes[-1].level, 2)  # fixed level
        self.assertTrue(chart.length > 0)


if __name__ == "__main__":
    unittest.main()
