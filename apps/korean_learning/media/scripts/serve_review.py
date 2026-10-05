#!/usr/bin/env python3
"""Serve the gallery and persist its single-reviewer feedback outside static files."""

import argparse
import json
import os
import tempfile
import threading
from datetime import datetime, timezone
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from import_video import VideoImports

COLLECTIONS = {
    "korean-starter-50": "",
    "korean-useful-language-10": "sample-10",
    "korean-useful-language-20": "sample-20",
}
LOCK = threading.Lock()


def now():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def save(path, payload):
    fd, name = tempfile.mkstemp(dir=path.parent, prefix=".feedback-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as output:
            json.dump(payload, output, ensure_ascii=False, indent=2)
            output.write("\n")
            output.flush()
            os.fsync(output.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def collection(self):
        name = parse_qs(urlsplit(self.path).query).get("collection", [""])[0]
        if name not in COLLECTIONS:
            raise ValueError("Unknown collection")
        return name

    def read_feedback(self, name):
        path = self.server.feedback_dir / (name + ".json")
        if path.exists():
            return json.loads(path.read_text())
        manifest = self.server.manifests[name]
        # Explicit approvals from the conversation, not implicit browser defaults.
        payload = {
            "schema_version": 1,
            "collection": name,
            "reviews": {
                str(x["pageid"]): {
                    "decision": x["review_default"],
                    "notes": "",
                    "updated_at": "2026-10-02T00:00:00.000Z",
                    "source": "conversation",
                }
                for x in manifest
                if x.get("review_default") in ("keep", "maybe", "reject")
            },
        }
        save(path, payload)
        return payload

    def do_GET(self):
        if urlsplit(self.path).path in ("/import", "/import.html"):
            body = Path(__file__).with_name("import_template.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if getattr(self.server, "imports", None) and self.server.imports.handle_get(self):
            return
        if urlsplit(self.path).path != "/api/reviews":
            return super().do_GET()
        try:
            name = self.collection()
            with LOCK:
                payload = self.read_feedback(name)
            self.send_json(200, payload)
        except ValueError as error:
            self.send_json(400, {"error": str(error)})

    def do_POST(self):
        if getattr(self.server, "imports", None) and self.server.imports.handle_post(self):
            return
        if urlsplit(self.path).path != "/api/reviews":
            return self.send_json(404, {"error": "Unknown endpoint"})
        origin = self.headers.get("Origin")
        if origin and urlsplit(origin).netloc != self.headers.get("Host"):
            return self.send_json(403, {"error": "Origin mismatch"})
        try:
            name = self.collection()
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 262144:
                raise ValueError("Invalid request size")
            if self.headers.get_content_type() != "application/json":
                raise ValueError("Expected JSON")
            body = json.loads(self.rfile.read(length))
            rows = body.get("reviews")
            valid_ids = {str(x["pageid"]) for x in self.server.manifests[name]}
            if not isinstance(rows, dict) or len(rows) > len(valid_ids):
                raise ValueError("Invalid reviews")
            clean = {}
            for id, row in rows.items():
                if id not in valid_ids or not isinstance(row, dict):
                    raise ValueError("Unknown image")
                if row.get("decision") not in ("keep", "maybe", "reject", "unreviewed"):
                    raise ValueError("Invalid decision")
                if not isinstance(row.get("notes"), str) or len(row["notes"]) > 10000:
                    raise ValueError("Invalid notes")
                timestamp = datetime.fromisoformat(row["updated_at"].replace("Z", "+00:00"))
                if timestamp.tzinfo is None:
                    raise ValueError("Timestamp requires timezone")
                clean[id] = {
                    "decision": row["decision"],
                    "notes": row["notes"],
                    "updated_at": timestamp.astimezone(timezone.utc)
                    .isoformat(timespec="milliseconds")
                    .replace("+00:00", "Z"),
                }
            with LOCK:
                payload = self.read_feedback(name)
                for id, row in clean.items():
                    old = payload["reviews"].get(id)
                    if not old or row["updated_at"] > old["updated_at"]:
                        payload["reviews"][id] = dict(row, received_at=now(), source="browser")
                save(self.server.feedback_dir / (name + ".json"), payload)
            self.send_json(200, payload)
        except (ValueError, KeyError, TypeError, AttributeError) as error:
            self.send_json(400, {"error": str(error)})


def main():
    parser = argparse.ArgumentParser()
    media = Path(__file__).resolve().parents[1]
    parser.add_argument("--root", type=Path, default=media / "starter-50")
    parser.add_argument("--feedback-dir", type=Path, default=media / "feedback")
    parser.add_argument("--imports-dir", type=Path, default=media / "imports")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    args.feedback_dir.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer(
        ("127.0.0.1", args.port), partial(Handler, directory=str(args.root))
    )
    server.imports = VideoImports(args.imports_dir)
    server.feedback_dir = args.feedback_dir
    server.manifests = {
        name: json.loads((args.root / folder / "manifest.json").read_text())
        for name, folder in COLLECTIONS.items()
    }
    print(f"Reviewer listening on {args.port}; feedback: {args.feedback_dir}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
