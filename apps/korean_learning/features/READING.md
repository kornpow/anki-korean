# Real World Reading

[Plan index](../PLAN.md)

Include visual examples of Korean as encountered in menus, signs, labels, receipts, notices, posters, messages, and media captions. Everyday physical surroundings and digital content are both core sources for learning.

Offer curated scenes organized by theme as well as the ability to bring in a photo, screenshot, or pasted text. Learners should be able to practice without supplying their own material.

Proposed scene controls:

- Zoom in to read independently.
- Select an individual word within a phrase for help limited to that selection.
- Tap a word or line to hear it spoken.
- Reveal a clear Hangul transcript for stylized or difficult lettering.
- Request a hint, then optionally reveal the selected word's meaning; reveal a phrase translation only through a separate action.
- Listen to the whole scene while following highlighted text.
- Save unfamiliar vocabulary to a themed collection or flashcard review.

Keep translations hidden initially, with help available on demand. Confirm whether the requested reading option means independent reading, read-aloud audio, or both.

### Help for a selected word

Selecting a word opens a small help panel while keeping the surrounding Korean visible. Selection alone should not reveal a definition or translate the phrase.

Working interpretation of “without revealing the whole word”: provide progressive hints before showing the selected word's full meaning, and keep the rest of the phrase untranslated. This supports getting a small amount of help while continuing to work out the text independently.

Proposed help options:

- Hear the selected word on request.
- Request a small clue, such as its grammatical role or a broad meaning category.
- Request a breakdown of a base word and attached particle, or a verb stem and ending, where applicable.
- Explicitly reveal the selected word's meaning in context.
- Save the word or verb form for review without revealing the phrase translation.

For example, selecting 먹었어요 in 빵을 먹었어요 could first offer “past tense, polite form.” A further requested hint could show the dictionary form 먹다. The meaning of the selected word and the full sentence translation remain separate reveals.

The same interaction should work in lesson text and reading scenes. Designed scenes need selectable text or aligned word regions; photographed text needs checked transcriptions aligned to the visible words. Help should account for attached particles and verb endings rather than relying only on spaces.

Use carefully typeset Korean in designed scenes and, where appropriate, real photographs with checked transcriptions. Verify that visible Korean, transcripts, translations, and audio agree.

Example café activity: find a drink, identify its price, read its description, then write your order.


## Content sources and examples

Use the same targeted reading help across [menus and other everyday examples](../examples/EVERYDAY_READING.md) and the [shared reel example](../examples/SHARED_REEL.md). Imported photos and screenshots need editable extracted text, orientation and crop controls, and checks for uncertain readings. A source may lead to quick reading help, optional saved vocabulary, verb practice, or typed writing.

Video-specific playback and caption timing are extensions of this shared reading experience.

## Media selection and crop requirements

Select reusable language: instructions, warnings, requests, descriptions, food choices, and purchase conditions. Exclude images whose main content is a location, street, station, or other proper name.

Favor legible Korean in recognizable everyday situations. Menus, products, notices, and instructions remain core examples.

Preserve the real-world object and enough context to understand the situation. Trim distracting outer margins, not individual text lines. Keep sign borders and pictograms, doorway context, menu layout, food displays, and product packaging. If the image could be replaced by plain text without losing anything, the crop is too tight.

For the approved examples, retain #1's whole notice and pharmacy doorway, #4's standing sign, no-smoking symbol and entrance, and #5's full warning panel with scooter illustration. Printed English can remain in the review photo; handling answer-revealing English in future learning mode must not destroy the scene's context.

The media review page shows English descriptions and selected translations beside each photo. Learning-mode translations remain available on request. All ten sample images now show a single contextual view; this supersedes the earlier Korean-only text-region cropping requirement. Preserve originals, attribution and recorded viewport coordinates.

## Review feedback workflow

User requirement: never require Export feedback. Choices and notes save automatically to the server with visible Saving/Saved/retry status. Existing reviews at the current browser origin migrate automatically. The agent reads saved feedback directly when asked. No file upload is part of the review workflow. Implemented in the Python review server.
