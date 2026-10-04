# Release validation

Verified locally on 3 October 2026 with Python 3.12.14, FastAPI 0.142.2, Playwright 1.62.1 and installed Google Chrome on macOS.

`python -m pytest -q`: **24 passed**.

The real-browser workflow passed these checks:

- Study five words, complete all recognition questions, earn a badge, revisit and retain progress after reload.
- Complete a family activity and retain the recorded moment.
- Request source guidance and follow its published word evidence.
- Record with MediaRecorder using a synthetic test microphone, save in IndexedDB, play back and retain it after reload.
- Search Badaga source forms and teaching notes; find an attached family recording on the correct word; show an empty result for an unknown query.
- Export progress; reject an invalid import without changing state; reset progress while retaining voices; import a valid backup.
- Remove a saved voice from the test browser.
- Bring due words back for review, show recognition feedback and reschedule the words.
- Render all four views at 375 px and 320 px without horizontal overflow.
- Observe zero uncaught page errors and verify all captured POST requests are JSON to the local Python server, with no recording or speaker nickname in request bodies.

Desktop, mobile and founder-story screenshots are in `docs/screenshots/`. Any recorded microphone content in the workflow is synthetic test data and is not included in this repository.

Python checks include a mocked successful model response, malformed JSON, unknown IDs, duplicate terms, changed topics, extra generated fields and a provider outage. These establish the selection contract and fallback. No live provider, model quality, Badaga speech recognition or text-to-speech system has been tested or is claimed.

The current Starlette test client emits a deprecation warning about its httpx adapter; it does not cause a test failure. Public CI repeats Python checks on 3.12 and 3.13 and runs the browser workflow on Linux.

Docker packaging is supplied but was not built locally because Docker is unavailable on the development machine. A public hosted deployment has not been created. Fluent Badaga speaker review, learning effectiveness with children, family dialect coverage and Safari/mobile-device microphone compatibility remain to be evaluated with community participation.
