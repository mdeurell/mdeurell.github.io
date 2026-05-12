"""Local development server for the Critical Earth website.

Serves the `website/` directory at http://localhost:5000, mirroring
the GitHub Pages deployment so visualizations and navigation work identically.

Usage:
    python main.py              # default port 5000
    python main.py --port 8080  # custom port
"""

from __future__ import annotations

import argparse
from pathlib import Path

from flask import Flask, send_from_directory

WEBSITE_DIR = Path(__file__).parent / "website"

app = Flask(__name__, static_folder=str(WEBSITE_DIR), static_url_path="")


@app.route("/")
def index():
    return send_from_directory(WEBSITE_DIR, "index.html")


@app.route("/<path:path>")
def serve(path: str):
    return send_from_directory(WEBSITE_DIR, path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Critical Earth local dev server")
    parser.add_argument("--port", type=int, default=5000, help="Port to listen on (default: 5000)")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to (default: 127.0.0.1)")
    args = parser.parse_args()

    print(f"Critical Earth dev server -> http://{args.host}:{args.port}")
    print("Serving:  website/")
    print("Stop:     Ctrl+C\n")
    app.run(host=args.host, port=args.port, debug=True)


if __name__ == "__main__":
    main()

