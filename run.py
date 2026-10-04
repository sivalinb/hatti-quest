"""Run with python run.py. Loopback is the default for family privacy."""
import argparse
import uvicorn

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Open Hatti Quest")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    uvicorn.run("hatti.app:app", host=args.host, port=args.port)
