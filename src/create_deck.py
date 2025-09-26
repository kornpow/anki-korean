import csv
import os
import random
from typing import List, Tuple

from genanki import Deck, Model, Note, Package


def remove_duplicates_from_csv(csv_file_path: str) -> List[Tuple[str, str]]:
    """
    Read CSV file and remove duplicate Korean-English pairs.
    Returns a list of unique (korean_text, english_text) tuples.
    """
    if not os.path.exists(csv_file_path):
        print(f"Error: CSV file '{csv_file_path}' not found!")
        return []

    unique_pairs = {}  # Use dict to maintain order and remove duplicates
    duplicate_count = 0

    try:
        with open(csv_file_path, "r", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)

            for row in reader:
                korean_text = row["korean_text"].strip()
                english_text = row["english_text"].strip()

                # Skip empty rows
                if not korean_text or not english_text:
                    continue

                # Use korean_text as key to identify duplicates
                if korean_text in unique_pairs:
                    duplicate_count += 1
                    print(f"Duplicate found and removed: {korean_text} -> {english_text}")
                else:
                    unique_pairs[korean_text] = english_text

    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return []

    print(f"Removed {duplicate_count} duplicate entries")
    print(f"Total unique Korean-English pairs: {len(unique_pairs)}")

    return [(korean, english) for korean, english in unique_pairs.items()]


def main() -> None:
    # Define the model for the flashcards
    my_model = Model(
        random.randrange(1 << 30, 1 << 31),
        "Korean-English Model",
        fields=[
            {"name": "Korean"},
            {"name": "English"},
        ],
        templates=[
            {
                "name": "Korean to English",
                "qfmt": "{{Korean}}",
                "afmt": '{{FrontSide}}<hr id="answer">{{English}}',
            },
        ],
    )

    # Create the deck
    deck_name = "Korean Vocabulary"
    package_name = deck_name.lower().replace(" ", "_")
    my_deck = Deck(random.randrange(1 << 30, 1 << 31), deck_name)

    # Process CSV file and remove duplicates
    csv_file_path = "korean_english_pairs.csv"
    unique_pairs = remove_duplicates_from_csv(csv_file_path)

    if not unique_pairs:
        print("No valid Korean-English pairs found. Exiting.")
        return

    # Create flashcards from unique pairs
    note_count = 0
    for korean_text, english_text in unique_pairs:
        # Create note and add to deck
        print(f"Creating note: {korean_text} -> {english_text}")
        note = Note(model=my_model, fields=[korean_text, english_text])
        my_deck.add_note(note)
        note_count += 1

    print(f"Successfully created {note_count} flashcards from unique pairs")

    # Write the deck to file
    try:
        Package(my_deck).write_to_file(f"{package_name}.apkg")
        print(f"Anki deck saved as '{package_name}.apkg'")
    except Exception as e:
        print(f"Error saving Anki deck: {e}")


if __name__ == "__main__":
    main()
