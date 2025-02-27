from genanki import Note, Model, Deck, Package


def main():
    print("Hello from anki-korean!")


my_model = Model(
    1607392319,
    "Simple Model",
    fields=[
        {"name": "Question"},
        {"name": "Answer"},
    ],
    templates=[
        {
            "name": "Card 1",
            "qfmt": "{{Question}}",
            "afmt": '{{FrontSide}}<hr id="answer">{{Answer}}',
        },
    ],
)

my_note1 = Note(model=my_model, fields=["Hello", "안녕하세요"])

my_note2 = Note(model=my_model, fields=["Dog", "개"])

deck_name = "Korean Lesson"
package_name = deck_name.lower().replace(" ", "_")
my_deck = Deck(2059400110, "Korean Lesson")

my_deck.add_note(my_note1)
my_deck.add_note(my_note2)

Package(my_deck).write_to_file(f"{package_name}.apkg")

# if __name__ == "__main__":
#     main()
