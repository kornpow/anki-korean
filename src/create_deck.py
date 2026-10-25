"""Build repeatable Anki decks from Duolingo or older OCR vocabulary CSVs."""

import argparse
import csv
import hashlib
import html
import unicodedata
from pathlib import Path

from genanki import Deck, Model, Note, Package, guid_for


def stable_id(value: str) -> int:
    return (1 << 30) + int.from_bytes(hashlib.sha256(value.encode()).digest()[:4]) % (1 << 30)


def read_words(path: Path) -> tuple[list[tuple[str, str]], int]:
    pairs = []
    seen = set()
    duplicates = 0
    with path.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        columns = set(reader.fieldnames or [])
        if {"korean", "english"} <= columns:
            korean_key, english_key = "korean", "english"
        elif {"korean_text", "english_text"} <= columns:
            korean_key, english_key = "korean_text", "english_text"
        else:
            raise ValueError("CSV needs korean,english or korean_text,english_text columns")
        for number, row in enumerate(reader, 2):
            korean = unicodedata.normalize("NFC", (row.get(korean_key) or "").strip())
            english = (row.get(english_key) or "").strip()
            if not korean or not english:
                raise ValueError(f"Row {number} has an empty word or translation")
            pair = (korean, english)
            if pair in seen:
                duplicates += 1
            else:
                seen.add(pair)
                pairs.append(pair)
    if not pairs:
        raise ValueError("CSV contains no words")
    return pairs, duplicates


def remove_duplicates_from_csv(csv_file_path):
    """Compatibility entry point for the original OCR pipeline."""
    words, _ = read_words(Path(csv_file_path))
    unique = {}
    for korean, english in words:
        unique.setdefault((korean, english.casefold()), (korean, english))
    return list(unique.values())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path, nargs="?", default=Path("korean_english_pairs.csv"))
    parser.add_argument("--csv", type=Path, dest="csv_option", help="Input CSV (legacy option)")
    parser.add_argument("--output", type=Path, default=Path("korean_vocabulary.apkg"))
    parser.add_argument("--name", default="Korean Vocabulary")
    parser.add_argument("--sort", choices=["source", "korean", "english"], default="korean")
    parser.add_argument(
        "--reverse", action="store_true", help="Also generate English to Korean cards"
    )
    args = parser.parse_args()
    words, duplicates = read_words(args.csv_option or args.csv)
    if args.sort != "source":
        index = 0 if args.sort == "korean" else 1
        words.sort(key=lambda pair: (pair[index].casefold(), pair[1 - index].casefold()))

    templates = [
        {
            "name": "Korean to English",
            "qfmt": '<div class="korean">{{Korean}}</div>',
            "afmt": '{{FrontSide}}<hr id="answer"><div>{{English}}</div>',
        }
    ]
    if args.reverse:
        templates.append(
            {
                "name": "English to Korean",
                "qfmt": "{{English}}",
                "afmt": '{{FrontSide}}<hr id="answer"><div class="korean">{{Korean}}</div>',
            }
        )
    variant = "both" if args.reverse else "recognition"
    model = Model(
        stable_id(f"anki-korean:words:v1:{variant}"),
        f"Korean Words v1 {variant}",
        fields=[{"name": "Korean"}, {"name": "English"}],
        templates=templates,
        css=".card { font-family: Arial, sans-serif; text-align: center; font-size: 26px; } "
        '.korean { font-family: "Apple SD Gothic Neo", "Noto Sans KR", sans-serif; '
        "font-size: 42px; margin: 24px 0; }",
    )
    deck = Deck(stable_id(f"anki-korean:deck:{args.name}"), args.name)
    for korean, english in words:
        deck.add_note(
            Note(
                model=model,
                fields=[html.escape(korean), html.escape(english)],
                guid=guid_for("anki-korean:words:v1", variant, korean, english),
                tags=["korean", "vocabulary"],
            )
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    Package(deck).write_to_file(str(args.output))
    sorted_csv = args.output.with_suffix(".csv")
    with sorted_csv.open("w", encoding="utf-8-sig", newline="") as target:
        writer = csv.writer(target)
        writer.writerow(["korean", "english"])
        writer.writerows(words)
    print(f"Created {len(words)} notes / {len(words) * len(templates)} cards")
    print(f"Removed {duplicates} exact duplicate pairs; sort: {args.sort}")
    print(f"Deck: {args.output}\nWord list: {sorted_csv}")


if __name__ == "__main__":
    main()
