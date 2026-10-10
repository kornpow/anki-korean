#!/usr/bin/env python3
"""Extract auditable Korean/English vocabulary from screenshots, video, or OCR text."""

import argparse
import csv
import json
import math
import re
import sys
import unicodedata
from dataclasses import asdict, dataclass
from pathlib import Path

HANGUL = re.compile(r"[\u1100-\u11ff\u3130-\u318f\uac00-\ud7af]")
LATIN = re.compile(r"[A-Za-z]")
SEPARATOR = re.compile(r"\s*(?:=>|->|→|:|\||\t|—|–|-)\s*")
BOUNDARY = re.compile(r"(?<=[가-힣])\s+(?=[A-Za-z])|(?<=[A-Za-z])\s+(?=[가-힣])")
IMAGES = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}
VIDEOS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"}


@dataclass
class Line:
    text: str
    confidence: float | None = None
    left: int = 0
    top: int = 0
    width: int = 0
    height: int = 0
    block: int = 0


def normalize(text):
    return " ".join(unicodedata.normalize("NFC", text).split()).strip(" •●▪")


def language(text):
    korean, english = bool(HANGUL.search(text)), bool(LATIN.search(text))
    return "ko" if korean and not english else "en" if english and not korean else None


def orient(left, right):
    left, right = normalize(left), normalize(right)
    if language(left) == "ko" and language(right) == "en":
        return left, right
    if language(left) == "en" and language(right) == "ko":
        return right, left
    return None


def inline_pair(text):
    """Require exactly one unambiguous bilingual split; retain spelling/punctuation."""
    candidates = set()
    for pattern in (SEPARATOR, BOUNDARY):
        for match in pattern.finditer(text):
            pair = orient(text[: match.start()], text[match.end() :])
            if pair:
                candidates.add(pair)
    return next(iter(candidates)) if len(candidates) == 1 else None


def nearby(first, second):
    """Stacked pairing is restricted to adjacent, aligned lines in one OCR block."""
    return (
        first.block == second.block
        and first.height > 0
        and 0 <= second.top - (first.top + first.height) <= 1.5 * max(first.height, second.height)
        and abs(first.left - second.left) <= 2 * max(first.height, second.height)
    )


def parse_lines(lines, layout="auto", minimum=65, geometry=True):
    accepted, review = [], []
    index = 0
    while index < len(lines):
        line = lines[index]
        pair = inline_pair(line.text)
        used = [line]
        method = "inline"
        if not pair and layout != "inline" and index + 1 < len(lines):
            following = lines[index + 1]
            if (geometry and nearby(line, following)) or (
                not geometry and layout == "stacked" and line.block == following.block
            ):
                pair = orient(line.text, following.text)
                if pair:
                    used.append(following)
                    method = "stacked"
        confidence = min((x.confidence for x in used if x.confidence is not None), default=None)
        evidence = {"lines": [asdict(x) for x in used], "method": method, "confidence": confidence}
        if pair:
            evidence.update(korean_text=pair[0], english_text=pair[1])
        if pair and (confidence is None or confidence >= minimum):
            accepted.append(evidence)
        else:
            evidence["reason"] = "low_confidence" if pair else "no_unambiguous_pair"
            review.append(evidence)
        index += len(used)
    return accepted, review


def ocr_lines(data):
    """Keep Tesseract line positions and conservative minimum word confidence."""
    groups = {}
    for i, raw in enumerate(data["text"]):
        if not raw.strip():
            continue
        key = tuple(data[k][i] for k in ("page_num", "block_num", "par_num", "line_num"))
        groups.setdefault(key, []).append(i)
    lines = []
    for key, indexes in groups.items():
        indexes.sort(key=lambda i: data["left"][i])
        left = min(data["left"][i] for i in indexes)
        top = min(data["top"][i] for i in indexes)
        right = max(data["left"][i] + data["width"][i] for i in indexes)
        bottom = max(data["top"][i] + data["height"][i] for i in indexes)
        confidence = min(float(data["conf"][i]) for i in indexes)
        lines.append(
            Line(
                " ".join(data["text"][i] for i in indexes),
                confidence,
                left,
                top,
                right - left,
                bottom - top,
                key[1],
            )
        )
    return sorted(lines, key=lambda line: (line.top, line.left))


def aggregate(observations, sort="korean"):
    entries = {}
    for row in observations:
        key = (normalize(row["korean_text"]), normalize(row["english_text"]).casefold())
        if key not in entries:
            entries[key] = {
                "korean_text": key[0],
                "english_text": normalize(row["english_text"]),
                "observations": [],
            }
        entries[key]["observations"].append(row)
    result = list(entries.values())
    if sort != "source":
        field = "korean_text" if sort == "korean" else "english_text"
        result.sort(
            key=lambda row: (row[field].casefold(), row["korean_text"], row["english_text"])
        )
    return result


def ensure_ocr():
    import pytesseract

    try:
        languages = set(pytesseract.get_languages(config=""))
    except pytesseract.TesseractNotFoundError as error:
        raise ValueError(
            "Install Tesseract with Korean and English language data (kor, eng)."
        ) from error
    missing = {"kor", "eng"} - languages
    if missing:
        raise ValueError(
            f"Missing Tesseract languages: {', '.join(sorted(missing))}. No English-only fallback."
        )
    return pytesseract


def image_inputs(source, output, interval):
    if source.is_dir():
        files = sorted(x for x in source.iterdir() if x.suffix.lower() in IMAGES and x.is_file())
        if not files:
            raise ValueError("No supported images in the input directory.")
        for file in files:
            yield file, None
    elif source.suffix.lower() in IMAGES:
        yield source, None
    elif source.suffix.lower() in VIDEOS:
        import cv2

        capture = cv2.VideoCapture(str(source), cv2.CAP_FFMPEG, [cv2.CAP_PROP_N_THREADS, 2])
        try:
            if not capture.isOpened():
                raise ValueError(f"Cannot open video: {source}")
            fps = capture.get(cv2.CAP_PROP_FPS)
            if not math.isfinite(fps) or fps <= 0:
                raise ValueError("Video has no usable frame rate; extract screenshots first.")
            step = max(1, round(interval * fps))
            frames = output / "frames"
            frames.mkdir()
            index, count = 0, 0
            while capture.grab():
                if index % step == 0:
                    ok, frame = capture.retrieve()
                    if not ok:
                        raise ValueError(f"Could not decode frame {index}.")
                    path = frames / f"frame_{index:09d}.png"
                    if not cv2.imwrite(str(path), frame):
                        raise OSError(f"Could not write frame: {path}")
                    count += 1
                    yield path, index / fps
                index += 1
            if not count:
                raise ValueError("No frames could be decoded.")
        finally:
            capture.release()
    else:
        raise ValueError(
            "Input must be a video, screenshot, image directory, or .txt OCR transcript."
        )


def run(args):
    source = args.input.resolve()
    if not source.exists():
        raise ValueError(f"Input does not exist: {source}")
    text_input = source.is_file() and source.suffix.lower() == ".txt"
    neural = None
    ocr = None
    if not text_input:
        if args.engine == "rapidocr":
            from duolingo_rows import KoreanOCR

            neural = KoreanOCR()
        else:
            ocr = ensure_ocr()
    output = args.output_dir.resolve()
    if output.exists() and any(output.iterdir()):
        raise ValueError(
            "Output directory is not empty. Choose a new directory "
            "to avoid stale or overwritten results."
        )
    output.mkdir(parents=True, exist_ok=True)
    observations, pending, raw, failures = [], [], [], []
    inputs = [(source, None)] if text_input else image_inputs(source, output, args.interval)
    iterator = iter(inputs)
    while True:
        try:
            file, timestamp = next(iterator)
        except StopIteration:
            break
        except (ValueError, OSError) as error:
            failures.append({"filename": str(source), "error": str(error)})
            break
        evidence = {"filename": str(file), "timestamp_seconds": timestamp}
        try:
            if text_input:
                # Blank lines prevent accidental pairing across separate cards or sections.
                groups = re.split(r"\n\s*\n", file.read_text(encoding="utf-8-sig"))
                lines = [
                    Line(line.strip(), block=i)
                    for i, group in enumerate(groups)
                    for line in group.splitlines()
                    if line.strip()
                ]
                data = None
            else:
                from PIL import Image, ImageOps

                with Image.open(file) as original:
                    image = ImageOps.exif_transpose(original).convert("RGB")
                    if args.crop:
                        x, y, width, height = args.crop
                        if x + width > image.width or y + height > image.height:
                            raise ValueError("Crop extends beyond image bounds.")
                        image = image.crop((x, y, x + width, y + height))
                    if args.scale != 1:
                        image = image.resize(
                            (round(image.width * args.scale), round(image.height * args.scale))
                        )
                    if neural:
                        import cv2
                        import numpy as np

                        extracted, data = neural.lines(
                            cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                        )
                        lines = [Line(**line) for line in extracted]
                    else:
                        data = ocr.image_to_data(
                            image,
                            lang="kor+eng",
                            config=f"--psm {args.psm}",
                            output_type=ocr.Output.DICT,
                            timeout=args.ocr_timeout,
                        )
                        lines = ocr_lines(data)
            raw.append(dict(evidence, lines=[asdict(line) for line in lines], ocr_data=data))
            good, uncertain = parse_lines(lines, args.layout, args.min_confidence, not text_input)
            observations.extend(dict(evidence, **row) for row in good)
            pending.extend(dict(evidence, **row) for row in uncertain)
        except (OSError, ValueError, RuntimeError) as error:
            failures.append(dict(evidence, error=str(error)))
    entries = aggregate(observations, args.sort)
    with (output / "vocabulary.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["filename", "korean_text", "english_text"])
        writer.writeheader()
        for entry in entries:
            writer.writerow(
                {
                    "filename": entry["observations"][0]["filename"],
                    "korean_text": entry["korean_text"],
                    "english_text": entry["english_text"],
                }
            )
    result = {
        "schema_version": 1,
        "input": str(source),
        "settings": {
            key: str(value) if isinstance(value, Path) else value
            for key, value in vars(args).items()
        },
        "entries": entries,
        "needs_review": pending,
        "failures": failures,
        "summary": {
            "unique_pairs": len(entries),
            "observations": len(observations),
            "review_items": len(pending),
            "failed_images": len(failures),
        },
    }
    (output / "vocabulary.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    (output / "ocr_raw.json").write_text(json.dumps(raw, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result["summary"]))
    print(f"Results: {output}")
    return 1 if failures or not entries else 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Video, image, image directory, or UTF-8 OCR text")
    parser.add_argument("--output-dir", type=Path, default=Path("imports/duolingo"))
    parser.add_argument(
        "--interval", type=float, default=1, help="Video sampling interval in seconds"
    )
    parser.add_argument(
        "--layout",
        choices=["auto", "inline", "stacked"],
        default="auto",
        help="Stacked text imports must opt in; images also require geometric alignment",
    )
    parser.add_argument(
        "--engine",
        choices=["tesseract", "rapidocr"],
        default="tesseract",
        help="rapidocr uses CPU Korean PP-OCRv5 and Duolingo bordered-row detection",
    )
    parser.add_argument("--sort", choices=["korean", "english", "source"], default="korean")
    parser.add_argument("--min-confidence", type=float, default=65)
    parser.add_argument("--crop", nargs=4, type=int, metavar=("X", "Y", "WIDTH", "HEIGHT"))
    parser.add_argument("--scale", type=float, default=2, help="Image resize factor before OCR")
    parser.add_argument("--psm", type=int, choices=[3, 4, 6, 11, 12], default=6)
    parser.add_argument("--ocr-timeout", type=float, default=30)
    args = parser.parse_args(argv)
    for name in ("interval", "scale", "ocr_timeout"):
        if not math.isfinite(getattr(args, name)) or getattr(args, name) <= 0:
            parser.error(f"--{name.replace('_', '-')} must be a positive finite number")
    if not math.isfinite(args.min_confidence) or not 0 <= args.min_confidence <= 100:
        parser.error("--min-confidence must be between 0 and 100")
    if args.crop and (min(args.crop[:2]) < 0 or min(args.crop[2:]) <= 0):
        parser.error("Crop requires nonnegative X/Y and positive WIDTH/HEIGHT")
    try:
        return run(args)
    except (ValueError, OSError, ImportError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
