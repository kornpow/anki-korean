"""Exercise layout boundaries without network access or downloaded model weights."""

import sys
import unittest
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from duolingo_rows import row_regions


class RowLayoutTests(unittest.TestCase):
    def screen(self, factor=1):
        image = np.full((2000, 920, 3), 255, np.uint8)
        # Six uniform cells and one incomplete cell behind the fixed header.
        borders = [400, 480, 680, 880, 1080, 1280, 1480, 1680]
        for y in borders:
            cv2.line(image, (30, y), (890, y), (220, 220, 220), 4)
        for top, bottom in zip(borders, borders[1:]):
            if bottom - top < 150:
                continue
            # Disconnected vertical glyph strokes must stay in the same line.
            cv2.rectangle(image, (170, top + 40), (260, top + 58), (65, 65, 65), -1)
            cv2.rectangle(image, (170, top + 62), (260, top + 75), (65, 65, 65), -1)
            cv2.rectangle(image, (170, top + 110), (440, top + 135), (165, 165, 165), -1)
            cv2.circle(image, (90, top + 80), 20, (230, 180, 40), -1)
        return cv2.resize(image, None, fx=factor, fy=factor)

    def test_complete_rows_and_separate_lines(self):
        for scale in (1, 0.5, 1.5):
            with self.subTest(scale=scale):
                rows = row_regions(self.screen(scale))
                self.assertEqual(len(rows), 6)
                for row in rows:
                    self.assertEqual(len(row["lines"]), 2)
                    self.assertGreater(row["lines"][0][0], 150 * scale)
                    self.assertLess(row["lines"][0][1], row["lines"][1][1])

    def test_unsupported_screen_has_no_rows(self):
        self.assertEqual(row_regions(np.full((2000, 920, 3), 255, np.uint8)), [])
        self.assertEqual(row_regions(np.zeros((2000, 920, 3), np.uint8)), [])


if __name__ == "__main__":
    unittest.main()
