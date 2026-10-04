"""Explicit maintenance operations; they are not exposed as billable web endpoints."""
import argparse
import asyncio
import json
import os
from .rag import RagService

async def main():
    parser = argparse.ArgumentParser(description="Hatti Quest AI maintenance")
    parser.add_argument("operation", choices=("ingest", "eval", "status"))
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--nebius-key-file")
    parser.add_argument("--pinecone-config-file")
    parser.add_argument("--braintrust-key-file")
    args = parser.parse_args()
    if args.live:
        os.environ["HATTI_ENABLE_LIVE_AI"] = "1"
    for flag, env in (("nebius_key_file", "HATTI_NEBIUS_KEY_FILE"), ("pinecone_config_file", "HATTI_PINECONE_CONFIG_FILE"),
                      ("braintrust_key_file", "HATTI_BRAINTRUST_KEY_FILE")):
        if getattr(args, flag):
            os.environ[env] = getattr(args, flag)
    service = RagService()
    if args.operation == "ingest":
        result = await service.ingest()
    elif args.operation == "eval":
        from .evaluation import evaluate
        report = await evaluate(service)
        result = {"metrics": report["metrics"], "braintrust_url": report["braintrust_url"], "report": "evals/reports/latest.json"}
    else:
        result = service.status()
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
