"""Manage personal vocabulary lists, stored as Anki-compatible CSV files."""

import argparse
import csv
import re
import unicodedata
from pathlib import Path

LISTS_DIR = Path(__file__).resolve().parents[1] / "wordlist" / "custom"
FIELDS = ["korean", "english", "example", "example_english"]


def list_path(name):
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
        raise ValueError(
            "Use a list name like counting-words (lowercase letters, numbers, hyphens)"
        )
    return LISTS_DIR / f"{name}.csv"


def read_list(path):
    with path.open(encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def save_list(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".csv.tmp")
    with temporary.open("w", encoding="utf-8-sig", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("lists", help="Show saved lists")
    for command in ("create", "show", "add", "remove"):
        sub = commands.add_parser(command)
        sub.add_argument("name")
        if command in ("add", "remove"):
            sub.add_argument("korean")
        if command == "add":
            sub.add_argument("english")
            sub.add_argument("--example", default="")
            sub.add_argument("--example-english", default="")
    args = parser.parse_args()
    try:
        if args.command == "lists":
            for path in sorted(LISTS_DIR.glob("*.csv")):
                print(f"{path.stem}: {len(read_list(path))} words")
            return
        path = list_path(args.name)
        if args.command == "create":
            if path.exists():
                raise ValueError("That list already exists")
            save_list(path, [])
        else:
            rows = read_list(path)
            if args.command == "show":
                for row in rows:
                    print(f"{row['korean']} — {row['english']}")
                    if row.get("example"):
                        print(f"  {row['example']} — {row.get('example_english', '')}")
                return
            korean = unicodedata.normalize("NFC", args.korean.strip())
            if not korean:
                raise ValueError("Korean word cannot be empty")
            matches = [row for row in rows if row["korean"] == korean]
            if args.command == "add":
                if matches:
                    raise ValueError("Word already exists; remove it before replacing it")
                if not args.english.strip():
                    raise ValueError("English meaning cannot be empty")
                rows.append(
                    dict(
                        zip(
                            FIELDS,
                            [
                                korean,
                                args.english.strip(),
                                args.example.strip(),
                                args.example_english.strip(),
                            ],
                        )
                    )
                )
            else:
                if not matches:
                    raise ValueError("Word is not in this list")
                rows = [row for row in rows if row["korean"] != korean]
            save_list(path, rows)
        print(f"Saved {path}")
    except (ValueError, OSError) as error:
        parser.exit(1, f"Error: {error}\n")


if __name__ == "__main__":
    main()
