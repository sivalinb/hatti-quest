# Contributing to Hatti Quest

Help children keep Badaga present in everyday family life. Contributions from speakers, families, educators and developers are welcome.

For a word correction, include the existing word ID, proposed source form and English gloss, an evidence link, and any relevant village, household or respectful-usage context. Say whether a fluent speaker has reviewed it. Keep a variant labelled as a variant rather than silently replacing another family's form.

Vocabulary lives in `hatti/content.py`. Keep stable IDs so saved progress and recordings continue to match. Source records must have a title, URL and checked date. Add original teaching notes. A word's `review_status` must reflect the actual review, not an expectation that review will happen.

For recordings, images or stories, obtain the contributor’s agreement and establish redistribution rights before including them in the public repository. Do not commit private family audio, children’s photos or identifying family information. The app lets families keep their own recordings in their browser instead.

Run `python -m pytest -q`. For interface changes, also run the optional real-browser workflow in the README. Test at 320 px and with keyboard navigation. Keep the Python application usable without an AI service or API key. Generated Badaga, automatic accent grades and unreviewed translations are outside the current design.
