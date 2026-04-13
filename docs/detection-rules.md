# Detection rules

## Current MVP heuristics

Signals currently checked:
- ad keywords
- URLs
- phone numbers
- WeChat / VX contact hints

## Current score weights
- keyword hit: +30
- URL: +35
- phone number: +35
- WeChat / VX hint: +25

Default suspicious threshold:
- `score >= 30`

## Planned additions
- repeated message bursts
- identical message reposting
- OCR text from images
- domain allow/block list
- whitelist of trusted members
