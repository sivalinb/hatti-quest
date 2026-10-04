# Evaluation methodology

The checked-in report is a real live run of Nebius embeddings, Pinecone retrieval, Nebius story generation and Braintrust experiment logging. Its timestamp is UTC. It contains public learning examples, model names, reported usage, retrieval ranks and trace links, without API credentials or family recordings.

`evals/retrieval-v1.jsonl` contains 24 curated English queries with expected stable word IDs. Both systems use the same 50-word corpus. BM25 is the original lexical search. Hybrid uses a 256-dimensional Qwen embedding, Pinecone candidates and reciprocal rank fusion with k=60.

- Recall@5 is the proportion of expected IDs found in the first five results, averaged across cases. Most cases expect one word; the counting case expects three.
- Mean reciprocal rank measures the rank of the first expected ID within the first five results. Missing words score zero. It is not a claim that the first result is always correct.
- The eight story cases span all five learning topics and all four fictional themes. The reported grounding score checks three unique IDs from the local source collection. A separate live-generation score prevents authored fallback from being counted as a successful model generation.
- Six deterministic guards reject invented IDs, duplicate references, an instruction supplied as an ID, extra translation fields, markup and an empty model response. These test the contract, rather than resistance to every possible prompt injection.

Recorded results: BM25 recall@5 0.5417 and MRR 0.4111; hybrid recall@5 1.0 and MRR 0.6660. Eight of eight stories used valid IDs and were live generations. Six of six guards passed.

The dataset is small, hand-curated and includes synonyms intended to exercise semantic retrieval. It is not a held-out community benchmark. Recall@5 can succeed while another result ranks first. No score measures pronunciation, natural Badaga sentences, dialect correctness, cultural authority, child engagement or learning retention. Speaker review and family trials remain necessary.

Run `python -m hatti.cli eval --live` with the provider environment configured. This replaces `latest.json` with the actual new results, including degraded backend modes when a service is unavailable. The evaluation bypasses the web request ceiling because it is an explicit maintenance command. It makes 24 query-embedding/search pairs and eight story requests, plus Braintrust logging. It never accepts child audio.

The public repository report is reproducible in method, but later model outputs and ranking may differ. Braintrust links refer to the creator's authenticated project; access depends on that project's permissions. The JSON report itself is public and can be inspected without a Braintrust account.
