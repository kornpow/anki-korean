import csv
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from duolingo_parse import Line, aggregate, inline_pair, ocr_lines, parse_lines

SCRIPT = Path(__file__).resolve().parents[1] / "src/duolingo_parse.py"


class PairTests(unittest.TestCase):
    def test_separator_and_order(self):
        for text in ["apple - 사과", "사과: apple", "apple→사과", "사과\tapple", "사과 apple"]:
            with self.subTest(text=text):
                self.assertEqual(inline_pair(text), ("사과", "apple"))

    def test_punctuation_and_hyphenated_english(self):
        self.assertEqual(inline_pair("아이스크림 - ice-cream"), ("아이스크림", "ice-cream"))
        self.assertEqual(inline_pair("괜찮아요? | Is it okay?"), ("괜찮아요?", "Is it okay?"))

    def test_mixed_or_monolingual_rejected(self):
        for text in ["Continue", "word list - hello", "고양이 cat 개 dog", "hello 사과 world"]:
            self.assertIsNone(inline_pair(text))

    def test_stacked_geometry(self):
        good = [Line("먹다", 95, 10, 10, 100, 20, 1), Line("to eat", 93, 10, 35, 100, 20, 1)]
        accepted, pending = parse_lines(good)
        self.assertEqual(accepted[0]["korean_text"], "먹다")
        self.assertEqual(pending, [])
        for line in [
            Line("to eat", 93, 300, 35, 100, 20, 1),
            Line("to eat", 93, 10, 300, 100, 20, 1),
            Line("to eat", 93, 10, 35, 100, 20, 2),
        ]:
            self.assertEqual(parse_lines([good[0], line])[0], [])

    def test_low_confidence_flagged_not_silently_accepted(self):
        accepted, pending = parse_lines([Line("먹다 - to eat", 24)])
        self.assertFalse(accepted)
        self.assertEqual(pending[0]["reason"], "low_confidence")
        self.assertEqual(pending[0]["korean_text"], "먹다")

    def test_text_stacking_opt_in_and_blank_boundaries(self):
        lines = [Line("먹다"), Line("to eat")]
        self.assertFalse(parse_lines(lines, geometry=False)[0])
        self.assertEqual(len(parse_lines(lines, layout="stacked", geometry=False)[0]), 1)
        lines[1].block = 1
        self.assertFalse(parse_lines(lines, layout="stacked", geometry=False)[0])

    def test_unicode_dedup_preserves_different_meanings(self):
        rows = [
            {"korean_text": ko, "english_text": en, "filename": name}
            for ko, en, name in [("눈", "Eye", "a"), ("눈", "eye", "b"), ("눈", "snow", "c")]
        ]
        entries = aggregate(rows)
        self.assertEqual(len(entries), 2)
        self.assertEqual(len(entries[0]["observations"]), 2)

    def test_sorting(self):
        rows = [
            {"korean_text": "사과", "english_text": "apple"},
            {"korean_text": "개", "english_text": "dog"},
        ]
        self.assertEqual(aggregate(rows)[0]["korean_text"], "개")
        self.assertEqual(aggregate(rows, "english")[0]["english_text"], "apple")
        self.assertEqual(aggregate(rows, "source")[0]["korean_text"], "사과")

    def test_ocr_grouping(self):
        data = {
            "text": ["", "to", "eat", "먹다"],
            "conf": [-1, 95, 80, 99],
            "page_num": [1] * 4,
            "block_num": [1] * 4,
            "par_num": [1] * 4,
            "line_num": [0, 2, 2, 1],
            "left": [0, 10, 40, 10],
            "top": [0, 40, 40, 10],
            "width": [0, 20, 25, 60],
            "height": [0, 20, 20, 20],
        }
        lines = ocr_lines(data)
        self.assertEqual([x.text for x in lines], ["먹다", "to eat"])
        self.assertEqual(lines[1].confidence, 80)


class CliTests(unittest.TestCase):
    def invoke(self, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True
        )

    def test_csv_json_and_no_stale_rerun(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "input.txt"
            output = root / "out"
            source.write_text("눈 - eye\n눈 - snow\n눈 - EYE\n아이스크림 - ice-cream\nContinue\n")
            result = self.invoke(source, "--output-dir", output)
            self.assertEqual(result.returncode, 0, result.stderr)
            with (output / "vocabulary.csv").open(encoding="utf-8-sig") as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(len(rows), 3)
            self.assertEqual(set(rows[0]), {"filename", "korean_text", "english_text"})
            report = json.loads((output / "vocabulary.json").read_text())
            self.assertEqual(report["summary"]["observations"], 4)
            self.assertEqual(report["summary"]["review_items"], 1)
            before = (output / "vocabulary.csv").read_bytes()
            self.assertEqual(self.invoke(source, "--output-dir", output).returncode, 2)
            self.assertEqual((output / "vocabulary.csv").read_bytes(), before)

    def test_no_pairs_and_missing_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "input.txt"
            source.write_text("Continue\n")
            self.assertEqual(self.invoke(source, "--output-dir", Path(tmp) / "out").returncode, 1)
            self.assertEqual(self.invoke(Path(tmp) / "missing.txt").returncode, 2)

    def test_invalid_options(self):
        for option, value in [("--interval", "0"), ("--scale", "nan"), ("--min-confidence", "101")]:
            self.assertEqual(self.invoke("input.txt", option, value).returncode, 2)

    @unittest.skipUnless(importlib.util.find_spec("genanki"), "genanki not installed")
    def test_deck_consumer_preserves_meanings(self):
        from create_deck import remove_duplicates_from_csv

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "input.csv"
            path.write_text("korean_text,english_text\n눈,eye\n눈,snow\n눈,Eye\n")
            self.assertEqual(remove_duplicates_from_csv(path), [("눈", "eye"), ("눈", "snow")])


if __name__ == "__main__":
    unittest.main()
