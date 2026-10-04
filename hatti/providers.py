"""Small REST clients: explicit timeouts, sanitized errors, measurable usage."""
import json
import math
import time
import httpx

class ProviderError(Exception):
    def __init__(self, provider, reason, status=None):
        self.provider, self.reason, self.status = provider, reason, status
        super().__init__(f"{provider}: {reason}")

class Providers:
    def __init__(self, settings, transport=None):
        self.settings = settings
        self.transport = transport
        self.health = {}
        self.failures = {}

    async def request(self, provider, endpoint, payload):
        count, until = self.failures.get(provider, (0, 0))
        if until > time.monotonic():
            raise ProviderError(provider, "circuit-open")
        cfg = self.settings
        if provider == "nebius":
            url = cfg.nebius_base + endpoint
            headers = {"Authorization": f"Bearer {cfg.nebius_key}"}
        else:
            url = cfg.pinecone_host + endpoint
            headers = {"Api-Key": cfg.pinecone_key, "X-Pinecone-Api-Version": "2025-10"}
        started = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(40, connect=8), transport=self.transport,
                                         follow_redirects=False) as client:
                response = await client.post(url, headers=headers, json=payload)
                if not response.is_success:
                    raise ProviderError(provider, "http-error", response.status_code)
                result = response.json()
                if not isinstance(result, dict):
                    raise ValueError("Expected object")
        except (httpx.HTTPError, ValueError, ProviderError) as exc:
            count += 1
            self.failures[provider] = (count, time.monotonic() + 60 if count >= 3 else 0)
            self.health[provider] = {"status": "degraded", "reason": exc.reason if isinstance(exc, ProviderError) else "request-failed"}
            if isinstance(exc, ProviderError):
                raise
            raise ProviderError(provider, "request-failed") from None
        self.failures[provider] = (0, 0)
        self.health[provider] = {"status": "connected", "checked_at": time.time()}
        return result, round((time.perf_counter() - started) * 1000, 2)

    async def embed(self, texts):
        cfg = self.settings
        result, latency = await self.request("nebius", "/embeddings", {
            "model": cfg.embedding_model, "input": texts, "dimensions": cfg.dimensions})
        try:
            rows = sorted(result["data"], key=lambda row: row["index"])
            vectors = [row["embedding"] for row in rows]
            if len(vectors) != len(texts) or any(len(v) != cfg.dimensions or
                    any(not isinstance(x, (int, float)) or not math.isfinite(x) for x in v) for v in vectors):
                raise ValueError("Invalid vectors")
        except (KeyError, TypeError, ValueError):
            raise ProviderError("nebius", "embedding-shape") from None
        return vectors, {"stage": "embedding", "provider": "nebius", "model": cfg.embedding_model,
                         "latency_ms": latency, "input_tokens": result.get("usage", {}).get("prompt_tokens", 0),
                         "output_tokens": 0, "dimensions": cfg.dimensions}

    async def query(self, vector, category="", top_k=8):
        cfg = self.settings
        filters = {"pack": {"$eq": "bfq-v1"}}
        if category:
            filters["category"] = {"$eq": category}
        result, latency = await self.request("pinecone", "/query", {
            "namespace": cfg.namespace, "vector": vector, "topK": top_k,
            "includeMetadata": True, "includeValues": False, "filter": filters})
        return result.get("matches", []), {"stage": "vector-search", "provider": "pinecone",
                                          "model": "dense-index", "latency_ms": latency,
                                          "read_units": result.get("usage", {}).get("read_units", 0)}

    async def generate(self, messages):
        cfg = self.settings
        result, latency = await self.request("nebius", "/chat/completions", {
            "model": cfg.chat_model, "temperature": 0.55, "max_tokens": 900,
            "response_format": {"type": "json_object"}, "messages": messages})
        usage = result.get("usage", {})
        event = {"stage": "generation", "provider": "nebius", "model": cfg.chat_model,
                 "latency_ms": latency, "input_tokens": usage.get("prompt_tokens", 0),
                 "output_tokens": usage.get("completion_tokens", 0)}
        try:
            return json.loads(result["choices"][0]["message"]["content"]), event
        except (KeyError, IndexError, TypeError, ValueError):
            # Preserve billed usage even when the returned JSON is unusable.
            return None, event
