import os
import tempfile
import unittest
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from r2beat.musictxt import (
    format_entry,
    parse_entries,
    append_entry,
    read_next_index,
    find_entry_by_name,
    path_for_chart,
)


class TestMusicTxt(unittest.TestCase):
    def test_format_and_parse(self):
        entry = format_entry(
            index=10,
            name="MySong",
            image="MySong/MySong.bmp",
            file="MySong/MySong.xml",
            level=15,
            genre="Rock",
            artist="Band",
        )
        self.assertIn('Index="10"', entry)
        self.assertIn('Name="MySong"', entry)

        entries = parse_entries(entry)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["Index"], "10")
        self.assertEqual(entries[0]["Name"], "MySong")

    def test_file_operations(self):
        tmp = os.path.join(tempfile.gettempdir(), "test_music_suite.txt")
        if os.path.exists(tmp):
            os.remove(tmp)

        try:
            self.assertEqual(read_next_index(tmp, base=1), 1)

            entry1 = format_entry(index=1, name="Song1", image="i1", file="f1", level=5, genre="Pop")
            append_entry(tmp, entry1)

            entry2 = format_entry(index=2, name="Song2", image="i2", file="f2", level=10, genre="Club")
            append_entry(tmp, entry2)

            self.assertEqual(read_next_index(tmp), 3)

            found = find_entry_by_name(tmp, "Song1")
            self.assertIsNotNone(found)
            self.assertEqual(found["Index"], "1")

            not_found = find_entry_by_name(tmp, "Unknown")
            self.assertIsNone(not_found)
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)

    def test_path_for_chart(self):
        self.assertEqual(path_for_chart("rnr_music/Song/Song.xml"), "Song/Song.xml")
        self.assertEqual(path_for_chart("Song/Song.xml"), "Song/Song.xml")


if __name__ == "__main__":
    unittest.main()
