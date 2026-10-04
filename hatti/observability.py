"""Public learning traces, local run ledger, and bounded Prometheus labels."""
import asyncio
import json
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, generate_latest

REGISTRY = CollectorRegistry()
CALLS = Counter("hatti_ai_calls", "Provider calls by stage and outcome", ["provider", "stage", "outcome"], registry=REGISTRY)
LATENCY = Histogram("hatti_ai_stage_seconds", "AI stage latency", ["stage"], buckets=(.05,.1,.25,.5,1,2,5,10,20,40), registry=REGISTRY)
TOKENS = Counter("hatti_ai_tokens", "Reported billed tokens", ["model", "kind"], registry=REGISTRY)
RUNS = Counter("hatti_adventures", "Adventure requests by actual mode", ["mode"], registry=REGISTRY)
REJECTIONS = Counter("hatti_schema_rejections", "Model outputs rejected before display", registry=REGISTRY)
EVAL = Gauge("hatti_eval_score", "Latest measured evaluation score", ["metric", "system"], registry=REGISTRY)
CORPUS = Gauge("hatti_corpus_words", "Source-documented words in this language pack", registry=REGISTRY)

class Ledger:
    def __init__(self, directory):
        self.directory = Path(directory)

    def connect(self):
        self.directory.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.directory / "ai-runs.sqlite", timeout=5)
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, at REAL, payload TEXT)")
        connection.execute("CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, at REAL, payload TEXT)")
        return connection

    def record(self, payload):
        with self.connect() as db:
            db.execute("INSERT OR REPLACE INTO runs VALUES (?,?,?)", (payload["id"], time.time(), json.dumps(payload)))
            db.execute("DELETE FROM runs WHERE id NOT IN (SELECT id FROM runs ORDER BY at DESC LIMIT 250)")
        RUNS.labels(payload["mode"]).inc()
        for event in payload.get("stages", []):
            provider, stage = event.get("provider", "python"), event["stage"]
            CALLS.labels(provider, stage, event.get("outcome", "ok")).inc()
            LATENCY.labels(stage).observe(event.get("latency_ms", 0)/1000)
            if "model" in event:
                for kind in ("input", "output"):
                    TOKENS.labels(event["model"], kind).inc(event.get(kind + "_tokens", 0))

    def recent(self):
        with self.connect() as db:
            return [json.loads(row[0]) for row in db.execute("SELECT payload FROM runs ORDER BY at DESC LIMIT 20")]

    def cached(self, key):
        with self.connect() as db:
            row = db.execute("SELECT payload FROM cache WHERE key=? AND at>?", (key, time.time()-86400)).fetchone()
        return json.loads(row[0]) if row else None

    def cache(self, key, payload):
        with self.connect() as db:
            db.execute("INSERT OR REPLACE INTO cache VALUES (?,?,?)", (key, time.time(), json.dumps(payload)))
            db.execute("DELETE FROM cache WHERE at<?", (time.time()-86400,))

class Tracer:
    def __init__(self, settings):
        self.settings, self.logger = settings, None
        self.status = "disabled" if not settings.braintrust_key else "configured"

    async def ready(self):
        if self.logger or not self.settings.braintrust_key or self.status == "unavailable":
            return
        try:
            import braintrust
            self.logger = await asyncio.to_thread(braintrust.init_logger, project=self.settings.braintrust_project,
                                                 api_key=self.settings.braintrust_key, set_current=False)
            # Resolving the lazy ID checks authentication before we report connected.
            await asyncio.to_thread(lambda: self.logger.id)
            self.status = "connected"
        except Exception:
            self.status = "unavailable"
            self.logger = None

    @contextmanager
    def span(self, name, parent=None, **fields):
        owner = parent or self.logger
        if not owner:
            yield None
            return
        try:
            span = owner.start_span(name=name, set_current=False, **fields)
        except Exception:
            self.status = "degraded"
            yield None
            return
        try:
            yield span
        finally:
            try:
                span.end()
            except Exception:
                self.status = "degraded"

    def log(self, span, **fields):
        if span:
            try:
                span.log(**fields)
            except Exception:
                self.status = "degraded"

    def url(self, span):
        if span:
            try:
                return span.permalink()
            except Exception:
                self.status = "degraded"
        return None

    async def flush(self):
        if self.logger:
            try:
                await asyncio.to_thread(self.logger.flush)
            except Exception:
                self.status = "degraded"

def metrics():
    return generate_latest(REGISTRY)
