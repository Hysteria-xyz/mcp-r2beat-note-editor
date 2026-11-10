import unittest
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from r2beat.kinds import (
    normalize,
    resolve_single,
    resolve_hold,
    kind_name,
    is_hold_start,
    is_hold_mid,
    is_hold_end,
    is_hold_note,
    level_for,
    mirror_kind,
)


class TestKinds(unittest.TestCase):
    def test_normalize_and_aliases(self):
        self.assertEqual(normalize("Up-Left"), "up_left")
        self.assertEqual(normalize("ul"), "up_left")
        self.assertEqual(normalize("star"), "star_left")
        self.assertEqual(normalize("jump"), "ramp")
        self.assertEqual(normalize("slide"), "ramp")

    def test_resolve_single(self):
        self.assertEqual(resolve_single("up"), (16, 3))
        self.assertEqual(resolve_single("down"), (17, 3))
        self.assertEqual(resolve_single("left"), (18, 2))
        self.assertEqual(resolve_single("right"), (19, 2))
        self.assertEqual(resolve_single("ramp"), (24, 4))
        self.assertEqual(resolve_single("star_left"), (26, 1))

        with self.assertRaises(ValueError):
            resolve_single("nonexistent_kind")

    def test_resolve_hold(self):
        self.assertEqual(resolve_hold("up"), (134, 135, 136))
        self.assertEqual(resolve_hold("left"), (140, 141, 142))
        with self.assertRaises(ValueError):
            resolve_hold("invalid_hold")

    def test_hold_predicates(self):
        self.assertTrue(is_hold_start(134))
        self.assertTrue(is_hold_mid(135))
        self.assertTrue(is_hold_end(136))
        self.assertTrue(is_hold_note(134))
        self.assertTrue(is_hold_note(135))
        self.assertTrue(is_hold_note(136))
        self.assertFalse(is_hold_note(16))

    def test_mirror_kind(self):
        self.assertEqual(mirror_kind(18), 19)  # left -> right
        self.assertEqual(mirror_kind(19), 18)  # right -> left
        self.assertEqual(mirror_kind(20), 21)  # up_left -> up_right
        self.assertEqual(mirror_kind(26), 27)  # star_left -> star_right
        self.assertEqual(mirror_kind(16), 16)  # up remains up
        self.assertEqual(mirror_kind(24), 24)  # ramp remains ramp
        self.assertEqual(mirror_kind(140), 143)  # hold left start -> hold right start

    def test_level_for(self):
        self.assertEqual(level_for(16), 3)
        self.assertEqual(level_for(18), 2)
        self.assertEqual(level_for(20), 5)
        self.assertEqual(level_for(24), 4)
        self.assertEqual(level_for(26), 1)
        self.assertEqual(level_for(134), 5)  # hold


if __name__ == "__main__":
    unittest.main()
