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
