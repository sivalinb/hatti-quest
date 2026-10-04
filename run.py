"""Run with python run.py. Loopback is the default for family privacy."""
import argparse
import uvicorn
import os

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Open Hatti Quest")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--live", action="store_true", help="Enable configured live AI providers")
    parser.add_argument("--nebius-key-file", help="Path to a private Nebius key file")
    parser.add_argument("--pinecone-config-file", help="Path to a private Pinecone key=value config")
    parser.add_argument("--braintrust-key-file", help="Path to a private Braintrust key file")
    args = parser.parse_args()
    if args.live:
        os.environ["HATTI_ENABLE_LIVE_AI"] = "1"
    for flag, variable in (("nebius_key_file", "HATTI_NEBIUS_KEY_FILE"),
                           ("pinecone_config_file", "HATTI_PINECONE_CONFIG_FILE"),
                           ("braintrust_key_file", "HATTI_BRAINTRUST_KEY_FILE")):
        if getattr(args, flag):
            os.environ[variable] = getattr(args, flag)
    uvicorn.run("hatti.app:app", host=args.host, port=args.port)
