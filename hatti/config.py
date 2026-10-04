"""Explicit, opt-in provider configuration. Credentials never enter a response."""
import os
import shlex
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent

def read_assignments(path):
    values = {}
    if path:
        for line in Path(path).expanduser().read_text().splitlines():
            line = line.strip().removeprefix("export ")
            if line and not line.startswith("#") and "=" in line:
                name, value = line.split("=", 1)
                parts = shlex.split(value, comments=True)
                values[name.strip()] = parts[0] if parts else ""
    return values

def secret(name, file_name):
    if os.getenv(name):
        return os.environ[name].strip()
    path = os.getenv(file_name)
    return Path(path).expanduser().read_text().strip() if path else ""

@dataclass(frozen=True)
class Settings:
    live: bool = False
    nebius_key: str = field(default="", repr=False)
    pinecone_key: str = field(default="", repr=False)
    braintrust_key: str = field(default="", repr=False)
    nebius_base: str = "https://api.studio.nebius.com/v1"
    chat_model: str = "Qwen/Qwen3-30B-A3B-Instruct-2507"
    embedding_model: str = "Qwen/Qwen3-Embedding-8B"
    dimensions: int = 256
    pinecone_host: str = ""
    namespace: str = "hatti-quest-v1"
    braintrust_project: str = "Hatti Quest"
    data_dir: Path = ROOT / "data" / "private"
    grafana_url: str = "http://127.0.0.1:3017/d/hatti-quest/hatti-quest"
    prometheus_url: str = "http://127.0.0.1:9097"
    ops_token: str = field(default="", repr=False)
    rate_per_minute: int = 6

    @classmethod
    def from_env(cls):
        pc = read_assignments(os.getenv("HATTI_PINECONE_CONFIG_FILE", ""))
        def value(name, default=""):
            return os.getenv(name, pc.get(name, default))
        host = value("PINECONE_INDEX_HOST").strip().rstrip("/")
        if host and not host.startswith("https://"):
            host = "https://" + host
        settings = cls(
            live=os.getenv("HATTI_ENABLE_LIVE_AI") == "1",
            nebius_key=secret("NEBIUS_API_KEY", "HATTI_NEBIUS_KEY_FILE"),
            pinecone_key=value("PINECONE_API_KEY"),
            braintrust_key=secret("BRAINTRUST_API_KEY", "HATTI_BRAINTRUST_KEY_FILE"),
            nebius_base=os.getenv("HATTI_NEBIUS_BASE_URL", cls.nebius_base).rstrip("/"),
            chat_model=os.getenv("HATTI_CHAT_MODEL", cls.chat_model),
            embedding_model=os.getenv("HATTI_EMBEDDING_MODEL", cls.embedding_model),
            dimensions=int(os.getenv("HATTI_EMBEDDING_DIMENSIONS", "256")),
            pinecone_host=host,
            # Deliberately do not adopt an unrelated namespace from a shared credential file.
            namespace=os.getenv("HATTI_PINECONE_NAMESPACE", "hatti-quest-v1"),
            braintrust_project=os.getenv("HATTI_BRAINTRUST_PROJECT", "Hatti Quest"),
            data_dir=Path(os.getenv("HATTI_DATA_DIR", ROOT / "data" / "private")),
            grafana_url=os.getenv("HATTI_GRAFANA_URL", cls.grafana_url),
            prometheus_url=os.getenv("HATTI_PROMETHEUS_URL", cls.prometheus_url),
            ops_token=os.getenv("HATTI_OPS_TOKEN", ""),
        )
        if urlparse(settings.nebius_base).scheme != "https":
            raise ValueError("Nebius requires HTTPS")
        if host and urlparse(host).scheme != "https":
            raise ValueError("Pinecone requires HTTPS")
        if not settings.namespace.startswith("hatti-quest-"):
            raise ValueError("Use a dedicated hatti-quest- namespace")
        return settings

    @property
    def generation_ready(self):
        return self.live and bool(self.nebius_key)

    @property
    def retrieval_ready(self):
        return self.generation_ready and bool(self.pinecone_key and self.pinecone_host)
