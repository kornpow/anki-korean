---
name: find-my-korean-words
description: Find Korean words or English meanings in the user's Duolingo word list, including checking whether a word is in their list during Korean practice.
---

Read `wordlist/duolingo-korean-words-2026-10-22.csv` from the repository root
using Python's `csv.DictReader` with `encoding="utf-8-sig"`.
Columns are `korean` and `english`. If missing, find the current export in `wordlist/`.

Search both columns. Match English case-insensitively using whole words.
For Korean, check exact spelling first, then stems or likely typos if helpful.
Distinguish exact matches from related words and corrections.

Reply briefly with matching entries and their listed translations, or say the
word is absent. Keep dictionary meanings and conjugation explanations separate
from the CSV translation. Do not change the word list unless asked.
