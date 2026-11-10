import unittest
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import server


class TestServer(unittest.TestCase):
    def setUp(self):
        server.CHARTS.clear()

    def test_workspace_management(self):
        # Create
        c1 = server.create_chart(chart_id="s1", name="Track 1", bpm=160.0)
        self.assertEqual(c1["name"], "Track 1")

        # List
        lst = server.list_charts()
        self.assertEqual(len(lst), 1)
        self.assertEqual(lst[0]["chart_id"], "s1")

        # Duplicate
        c2 = server.duplicate_chart(source_chart_id="s1", new_chart_id="s2")
        self.assertEqual(len(server.CHARTS), 2)

        # Delete
        del_res = server.delete_chart("s1")
        self.assertEqual(del_res["status"], "deleted")
        self.assertEqual(len(server.CHARTS), 1)

    def test_note_manipulation(self):
        server.create_chart(chart_id="s1", name="Track 1", bpm=160.0)
        server.add_note(chart_id="s1", note_type="left", coord=10.0)
        server.add_note(chart_id="s1", note_type="right", coord=20.0)

        # Shift
        res_shift = server.shift_notes(chart_id="s1", delta_coord=5.0)
        self.assertEqual(res_shift["shifted_count"], 2)
        notes = res_shift["notes"]
        self.assertEqual(notes[0]["coord"], 15.0)
        self.assertEqual(notes[1]["coord"], 25.0)

        # Mirror
        res_mirror = server.mirror_chart(chart_id="s1")
        self.assertEqual(res_mirror["mirrored_count"], 2)
        self.assertEqual(res_mirror["notes"][0]["kind"], 19)  # left -> right

        # Summary
        summary = server.get_chart_summary("s1")
        self.assertEqual(summary["name"], "Track 1")
        self.assertIn("stats", summary)


if __name__ == "__main__":
    unittest.main()
