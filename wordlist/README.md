# Duolingo word export

The Korean word list was exported from the logged-in Duolingo page at
https://www.duolingo.com/practice-hub/words.

## Saved word list

`duolingo-korean-words-2026-10-22.csv` contains 993 Korean and English
word pairs. Verification confirmed the columns are `korean,english`, with
no empty fields. The filename date comes from the browser's UTC date.

The CSV uses UTF-8 with a byte order mark, quotes fields, and preserves
commas inside translations. It contains the translations shown by Duolingo.

## Export again

1. Open the words page in the browser where you are logged into Duolingo.
2. Open the JavaScript Console with Option + Command + J on Mac.
3. Paste the contents of `../src/export_duolingo_words.js` into the console.
4. Press Enter and keep the tab open while the script loads the full list.
5. Save the downloaded CSV in this `wordlist` directory.

Brave may initially block pasting with a security warning. Review the script
before deciding whether to manually type `allow pasting` into the console
and press Enter. Then paste and run the script again.

## How the script works

The script uses the existing browser session without reading passwords or
tokens. It clicks **Load more** until the list is expanded, reads each Korean
word and English translation, and checks the number of rows against the
page's total before creating a local CSV download. It does not upload the list.

Duolingo implements **Load more** as a list item with `role="button"`, so
the script checks both native buttons and elements with that role. The first
attempt detected only 50 of 993 words and stopped without exporting. After
fixing that selector, both exports contained all 993 pairs.

The script expects the English interface and Korean course. If the layout
changes, it may need updating. The older `src/duolingo_parse.py` extracts
words from video using OCR and is separate from this browser exporter.

## Korean keyboard on this Mac

Added **2-Set Korean** under System Settings → Keyboard → Text Input → Edit.
The input sources now include **U.S.** and **2-Set Korean**. The input menu
is visible in the menu bar, and the Globe key is set to **Change Input Source**.

Press the Globe key to switch keyboards, or select **2-Set Korean** from the
menu bar input menu. Korean letters combine into syllables as you type.
For example, the keys `g k s r n r` produce `한국` on the 2-Set layout.
Switch back to **U.S.** to type English.
