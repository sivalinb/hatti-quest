# Running the AI system

Start in authored mode with `python run.py`. Enable live mode only after configuring Nebius and Pinecone and running ingestion. Braintrust is optional: its unavailability should not prevent a family adventure. The chosen models were successfully called during this release's live validation; future availability depends on the provider account.

The defaults use a 256-dimensional dense Pinecone index and a dedicated `hatti-quest-v1` namespace. An existing matching index may be reused. The shared credential file's namespace is deliberately ignored, so another project's namespace cannot be overwritten accidentally. Vocabulary updates change the fingerprint; re-ingest before querying the new version.

## Configuration and maintenance

See `.env.example`. Python reads process variables. CLI file flags can read private credential files without copying their values into the repository. Keep key files outside Git. No key or private index host is returned by the evidence API.

`python -m hatti.cli ingest` upserts the corpus. `python -m hatti.cli eval` records a fresh evaluation. `python -m hatti.cli status` reads local evidence. These are explicit administrative commands; there is no billable ingestion or evaluation web endpoint.

The server caches successful stories for 24 hours. Cache keys include the prompt version, corpus fingerprint, request parameters, model and live mode. Fallbacks are not cached, so recovery can produce a new live story. The ledger retains 250 runs and the dashboard shows the latest 20. Both are stored in ignored `data/private/`. Family progress and audio remain in browser storage, separate from the server ledger.

Provider calls have connection and overall timeouts, no automatic billable retry, and a 60-second circuit breaker after three request failures. Invalid response references fall back to authored content. A failed generation's reported tokens are retained in the run ledger. No dollar price is inferred from tokens.

The process-wide web ceiling is six story requests per minute. Multiple worker processes each have their own ceiling. An internet deployment needs shared quotas and authentication appropriate to its spending policy. The default server binds to loopback.

## Inspect the evidence

- `/lab`: status, recent runs, candidate word forms, lexical/vector ranks, RRF scores, prompt version, trace links and eval results.
- `/api/ai/status`: private operations evidence. Loopback clients are allowed when no operations token is set. When `HATTI_OPS_TOKEN` is set, every client needs the bearer token. The lab accepts the token in a form and holds it only in page memory.
- `/metrics`: aggregate Prometheus exposition. No prompts, family names, word IDs, credentials or recordings appear in labels.
- `/health`: application liveness, independent of provider readiness. The lab distinguishes configured, connected, disabled and degraded providers; a configured key alone is not evidence of a successful request.

Braintrust receives fixed public learning themes and queries, source IDs, English fictional output and stage metrics. Logs do not include audio or a learner profile. Production observability should review retention and access controls for the intended audience.

## Monitoring stack

`docker compose up --build -d` packages the Python app, Prometheus and Grafana. Set a private `GRAFANA_ADMIN_PASSWORD` first. Ports 8765, 9097 and 3017 bind to localhost. Use `admin` and your configured password for Grafana. Grafana's datasource and 11-panel dashboard are provisioned from `ops/grafana/`. Named volumes persist app evidence and metrics.

The Docker container runs as a non-root user. With Docker port forwarding, the app may see a bridge-network client rather than loopback; set `HATTI_OPS_TOKEN` and use the lab's token form. The app, Prometheus and Grafana do not share family browser storage.

The panels cover application reachability, corpus size, reported tokens, requests, calls per minute, p95 stage latency, model/token breakdown, actual story modes, retrieval recall, grounding guard scores and rejected output. Sparse traffic can leave rate-based latency panels empty until enough observations exist; cumulative counters still show recorded activity.

Prometheus alert rules cover target unavailability, measured provider-stage failure rate and a failed grounding guard. The supplied rules do not configure external notifications. The denominator counts instrumented stage events, rather than promising a provider-specific uptime SLA.

Docker is unavailable on the development host, so Compose was supplied and inspected but not built there. Equivalent native Prometheus 3.14.0 and Grafana 12.1.1 instances were run against the app: Grafana's database health was OK, the provisioned dashboard had 11 panels, and the Prometheus target was up. The local demo uses ports 9097/3017 and private runtime data outside the repository.

For public hosting, configure HTTPS, trusted proxy handling, administrative authentication, secrets management, shared quotas, backups and an explicit data policy. A public hosted instance is not part of this release. Do not expose local builder services with a tunnel as a substitute for deployment review.

Primary integration references: [Nebius API](https://api.studio.nebius.com/docs), [Pinecone query API](https://docs.pinecone.io/reference/api/2025-10/data-plane/query), [Braintrust evals](https://www.braintrust.dev/docs/evaluate), [Grafana provisioning](https://grafana.com/docs/grafana/latest/administration/provisioning/).
