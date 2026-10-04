# Extending the approach to another language

The current product supports the Badaga starter only. A reusable language-pack interface is a next implementation step, rather than a claim that other languages already work.

The separation already established is useful: vocabulary and source records live in `hatti/content.py`; retrieval and generation live in `hatti/rag.py`; review and quizzes live in `hatti/engine.py`; family audio stays with the browser. English fictional scenes and deterministic word cards can be reused without asking a model to invent a low-resource language.

For another community, establish its choices with speakers first. A pack should include a language identifier, stable word IDs, source forms, English glosses, writing/romanisation choices, optional variants, respectful-usage notes, attribution, permission information and actual review status. Existing family audio must continue to match its original word ID and language.

Each pack needs its own lessons, original family activities and community review. It also needs a retrieval dataset reflecting its meanings and ambiguous forms. Evaluate the pack independently; the Badaga results do not transfer to it.

Replace the hardcoded pack name, fingerprint and namespace with pack-specific settings. Partition vectors and browser progress by language and version. Add a schema-backed loader, source validation and migration tests. Preserve the rule that the model selects known word references while Python supplies the language forms.

Recording can support languages whose sounds are poorly represented in writing, but permission, device storage and playback need to remain clear. A future shared archive would require explicit consent, rights, contributor controls and community governance. It is a separate feature from today's private family recordings.

Speech recognition or synthetic pronunciation should be added only after evidence that a model supports that language, followed by speaker evaluation. The system should be useful with source material and human voices even when no speech model exists.

The goal is a platform whose engineering can be reused while the language content, learning choices and authority stay with each community.
