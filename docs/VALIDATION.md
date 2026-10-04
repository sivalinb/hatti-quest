# Release validation

The AI upgrade was verified locally on 3–4 October 2026 with Python 3.12.14, FastAPI 0.142.2, Playwright 1.62.1 and installed Google Chrome on macOS. Timestamps in the live report are UTC.

`python -m pytest -q`: **36 passed**.

The original browser workflow passed lesson completion, badges, persistence, family activities, source guidance, real MediaRecorder with a synthetic test microphone, IndexedDB audio playback after reload, lexical search, progress export/import, invalid import rejection, reset preserving audio, voice deletion and due review. It found no page errors or audio/nickname uploads and checked all four views at 375/320 px.

The new browser workflow passed Story Studio generation, exact source-form grounding, quiz feedback and saved progress, operations ledger inspection and 375/320 px layouts. A narrow-screen table overflow was fixed with a constrained grid child and scrollable table container. Screenshots are in `docs/screenshots/`.

New Python checks cover valid live generation through mocked provider transport, cache accounting with zero new tokens, rejected invented references preserving billed usage, keyless fallback, stale vector metadata rejection, wrong embedding dimensions, circuit breaker behaviour, operations authentication, credential exclusion, rejection of profile/audio fields, the global request ceiling and explicit review priority.

Real provider validation: Nebius model listing, 256-dimensional embeddings, 50 vocabulary upserts into the dedicated Pinecone namespace, query retrieval, eight live generated adventures, Braintrust trace flushing and a completed Braintrust experiment. The checked-in report records all 24 retrieval cases and six grounding guards. These tests do not validate Badaga pronunciation or cultural authority.

Monitoring validation: native Prometheus 3.14.0 successfully scraped the application; its target was up. Native Grafana 12.1.1 reported healthy database status and returned the provisioned 11-panel dashboard through its API. The video records the running dashboard.

The Starlette test client emits an httpx-adapter deprecation warning; it does not cause failure. Docker and Compose packaging are supplied but were not built locally because Docker is unavailable. A public hosted deployment has not been created. Fluent speaker review, family learning effectiveness, wider dialect coverage, and physical Safari/mobile microphone testing remain open community validation work.

The finished narrated demo is exactly 300 seconds, 1280×720, H.264 High/yuv420p at 24 fps with AAC audio. A full decode completed without errors. Sample frames were visually inspected across the introduction, writing-system context, Story Studio, monitoring dashboard and extension section. A transcription check of the synthetic English audio returned a 300-second recording with the founder, census year, family voices, Pinecone, Prometheus and extension content present. This check is not an evaluation of native Badaga pronunciation.

The 4 October 2026 presenter revision replaces first-person narration with Siva Babu's story in the third person and applies his requested Badaga/Nilgiris pronunciation cues. The regenerated narration was transcribed to check the founder, the 2011 count of 133,550, the project purpose and closing, and the absence of first-person founder claims. The final MP4 is still exactly 300 seconds; a full decode passed, audio peaked at -3.1 dBFS, and its narration/caption hashes match the render. Updated frames were inspected at the founder introduction, Story Studio, Grafana and closing. The updated founder card fits 1280×720 with no overflow. The same public Drive file ID is used for the revised video.
