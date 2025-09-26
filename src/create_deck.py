import csv
import os
import random

from genanki import Deck, Model, Note, Package


def main():
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

    # Read from CSV file
    csv_file_path = "korean_english_pairs.csv"

    if not os.path.exists(csv_file_path):
        print(f"Error: CSV file '{csv_file_path}' not found!")
        return

    try:
        with open(csv_file_path, "r", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            note_count = 0

            for row in reader:
                korean_text = row["korean_text"].strip()
                english_text = row["english_text"].strip()

                # Skip empty rows
                if not korean_text or not english_text:
                    continue

                # Create note and add to deck
                print(f"Creating note: {korean_text} -> {english_text}")
                note = Note(model=my_model, fields=[korean_text, english_text])
                my_deck.add_note(note)
                note_count += 1

            print(f"Successfully created {note_count} flashcards from CSV file")

    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return

    # Write the deck to file
    try:
        Package(my_deck).write_to_file(f"{package_name}.apkg")
        print(f"Anki deck saved as '{package_name}.apkg'")
    except Exception as e:
        print(f"Error saving Anki deck: {e}")


if __name__ == "__main__":
    main()
