"""Persistent review edits and upload endpoint validation."""

import json
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps/korean_learning/media/scripts"))
from import_video import VideoImports, write_json
from serve_review import Handler
from word_types import annotate_word


class VideoImportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.manager = VideoImports(self.root / "imports")
        self.server = ThreadingHTTPServer(
            ("127.0.0.1", 0), partial(Handler, directory=str(self.root / "public"))
        )
        self.server.imports = self.manager
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.manager.pool.shutdown()
        self.temp.cleanup()

    def seed(self, id):
        directory = self.manager.directory / id
        directory.mkdir()
        write_json(
            directory / "job.json",
            {
                "id": id,
                "status": "ready",
                "candidates": [
                    {
                        "id": 0,
                        "korean_text": "먹다",
                        "english_text": "eat",
                        "frame": "frame_000000000.png",
                        "timestamp_seconds": 0,
                    }
                ],
            },
        )

    def test_corrections_replace_only_current_import(self):
        a, b = "a" * 32, "b" * 32
        self.seed(a)
        self.seed(b)
        rows = [{"id": 0, "korean_text": "먹다", "english_text": "eat"}]
        self.manager.save_words(a, rows)
        self.manager.save_words(b, rows)
        self.manager.save_words(a, rows)
        library = json.loads((self.manager.directory / "vocabulary.json").read_text())
        self.assertEqual(len(library["entries"]), 1)
        self.assertEqual(len(library["entries"][0]["sources"]), 2)
        rows[0]["english_text"] = "to eat"
        self.manager.save_words(a, rows)
        library = json.loads((self.manager.directory / "vocabulary.json").read_text())
        self.assertEqual(len(library["entries"]), 2)
        self.assertEqual(self.manager.read(a)["saved_selection"][0]["english_text"], "to eat")
        with self.assertRaises(ValueError):
            self.manager.save_words(a, [None])
        with self.assertRaises(ValueError):
            self.manager.save_words(a, rows + rows)

    def test_http_save_and_private_uploads(self):
        id = "a" * 32
        self.seed(id)
        request = urllib.request.Request(
            self.url + "/api/imports/" + id + "/vocabulary",
            data=json.dumps(
                {"entries": [{"id": 0, "korean_text": "먹다", "english_text": "to eat"}]}
            ).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request) as response:
            self.assertEqual(json.load(response)["saved_count"], 1)
        with urllib.request.urlopen(self.url + "/import") as response:
            self.assertIn(b"Upload and extract words", response.read())
        for path in ["/imports/vocabulary.json", "/api/imports/" + id + "/frames/job.json"]:
            with self.assertRaises(urllib.error.HTTPError) as error:
                urllib.request.urlopen(self.url + path)
            self.assertEqual(error.exception.code, 404)

    def test_reject_unsupported_and_cross_origin_upload(self):
        for headers, suffix, code in [
            ({}, "exe", 400),
            ({"Origin": "https://elsewhere.example"}, "mp4", 403),
        ]:
            request = urllib.request.Request(
                self.url + "/api/imports?filename=recording." + suffix,
                data=b"not a video",
                headers=headers,
            )
            with self.assertRaises(urllib.error.HTTPError) as error:
                urllib.request.urlopen(request)
            self.assertEqual(error.exception.code, code)
        self.assertEqual(list(self.manager.directory.iterdir()), [])

    def test_candidates_merge_repeats_and_keep_best_evidence(self):
        def observation(filename, confidence, korean="풀다", english="untie, unwrap"):
            return {
                "filename": filename,
                "confidence": confidence,
                "korean_text": korean,
                "english_text": english,
                "timestamp_seconds": 0,
            }

        first = observation("frame_000000000.png", 91)
        best = observation("frame_000000060.png", 99)
        weak = observation("frame_000000120.png", 50, english="untie,unwrap")
        report = {
            "entries": [
                {
                    "korean_text": "풀다",
                    "english_text": "untie, unwrap",
                    "observations": [first, best],
                }
            ],
            "needs_review": [weak],
        }
        candidates = self.manager.review_candidates(report)
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["frame"], best["filename"])
        self.assertEqual(candidates[0]["observation_count"], 3)
        self.assertFalse(candidates[0]["needs_review"])
        report["needs_review"].append(observation("frame_000000180.png", 50, english="unwind"))
        self.assertTrue(all(x["needs_review"] for x in self.manager.review_candidates(report)))

    def test_study_ratings_are_persistent_and_retry_safe(self):
        id = "a" * 32
        self.seed(id)
        event = {"card_id": 0, "rating": "again", "event_id": "1" * 32}
        first = self.manager.rate_word(id, event)
        retry = self.manager.rate_word(id, event)
        self.assertEqual(first, retry)
        self.assertTrue(retry["words"]["0"]["difficult"])
        self.assertEqual(retry["words"]["0"]["reviews"], 1)
        event.update(rating="gotit", event_id="2" * 32)
        self.manager.rate_word(id, event)
        reopened = VideoImports(self.manager.directory)
        try:
            state = reopened.study_state(id)
            self.assertFalse(state["words"]["0"]["difficult"])
            self.assertEqual(state["words"]["0"]["reviews"], 2)
            self.assertEqual(state["words"]["0"]["again_count"], 1)
        finally:
            reopened.pool.shutdown()
        with self.assertRaises(ValueError):
            self.manager.rate_word(id, dict(event, card_id=99))
        with self.assertRaises(ValueError):
            self.manager.rate_word(id, dict(event, card_id=True))
        with urllib.request.urlopen(self.url + "/api/imports/" + id + "/study") as response:
            self.assertEqual(json.load(response)["words"]["0"]["reviews"], 2)
        request = urllib.request.Request(
            self.url + "/api/imports/" + id + "/study",
            data=json.dumps(dict(event, event_id="3" * 32, rating="again")).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request) as response:
            self.assertTrue(json.load(response)["words"]["0"]["difficult"])
        with urllib.request.urlopen(self.url + "/study") as response:
            self.assertIn(b"Show answer", response.read())

    def test_word_types_follow_korean_and_survive_saving(self):
        def tags(korean):
            return annotate_word({"korean_text": korean, "english_text": "bad OCR"})

        self.assertEqual(tags("귀엽다")["parts_of_speech"], ["adjective"])
        self.assertEqual(tags("그립다")["parts_of_speech"], ["adjective"])
        self.assertEqual(tags("준비")["parts_of_speech"], ["noun"])
        self.assertEqual(tags("준비하다")["parts_of_speech"], ["verb"])
        self.assertEqual(tags("서요")["lemma"], "서다")
        self.assertEqual(tags("깔끔하게")["parts_of_speech"], ["adverb"])
        self.assertEqual(tags("깔끔하게")["lemma"], "깔끔하다")
        self.assertEqual(tags("소식.")["parts_of_speech"], ["noun"])
        self.assertTrue(tags("늦다")["pos_needs_review"])
        self.assertEqual(tags("구 경 하다")["parts_of_speech"], ["unknown"])
        self.assertEqual(tags("미등록하다")["parts_of_speech"], ["unknown"])
        id = "a" * 32
        self.seed(id)
        self.manager.save_words(id, [{"id": 0, "korean_text": "귀엽다", "english_text": "cute"}])
        saved = self.manager.read(id)["saved_selection"][0]
        self.assertEqual(saved["parts_of_speech"], ["adjective"])
        library = json.loads((self.manager.directory / "vocabulary.json").read_text())
        self.assertEqual(library["entries"][0]["lemma"], "귀엽다")
        reopened = VideoImports(self.manager.directory)
        try:
            migrated = reopened.read(id)
            self.assertEqual(migrated["candidates"][0]["parts_of_speech"], ["verb"])
            self.assertEqual(migrated["saved_selection"][0]["parts_of_speech"], ["adjective"])
        finally:
            reopened.pool.shutdown()

    def test_restart_marks_interrupted_job(self):
        id = "a" * 32
        self.seed(id)
        self.manager.update(id, status="processing")
        restarted = VideoImports(self.manager.directory)
        try:
            self.assertEqual(restarted.read(id)["status"], "failed")
        finally:
            restarted.pool.shutdown()


if __name__ == "__main__":
    unittest.main()
