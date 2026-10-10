"""Conservative, reusable word-type annotations for imported Korean vocabulary."""

import json
from pathlib import Path

LEXICON = json.loads(Path(__file__).with_suffix(".json").read_text())
FIELDS = ("parts_of_speech", "lemma", "pos_source", "pos_needs_review", "pos_note")


def annotate_word(row):
    # Only normalize surrounding sentence punctuation, never internal OCR damage.
    korean = row["korean_text"].strip().strip(".。!?")
    entry = LEXICON["entries"].get(korean)
    tags = entry["parts_of_speech"] if entry else ["unknown"]
    return {
        **row,
        "parts_of_speech": list(tags),
        "lemma": entry["lemma"] if entry else None,
        "pos_source": f"starter-lexicon-v{LEXICON['version']}" if entry else "unclassified",
        "pos_needs_review": not entry or len(tags) > 1,
        "pos_note": entry.get("note", "") if entry else "Word type needs checking.",
    }
