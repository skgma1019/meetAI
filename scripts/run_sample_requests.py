from __future__ import annotations

import json
import urllib.request
from pathlib import Path


BASE_URL = "http://127.0.0.1:8000"
ROOT = Path(__file__).resolve().parents[1]


def request_json(method: str, url: str, payload_path: Path | None = None) -> dict:
    data = None
    headers = {}
    if payload_path is not None:
        data = payload_path.read_bytes()
        headers["Content-Type"] = "application/json; charset=utf-8"
    req = urllib.request.Request(url=url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def print_block(title: str, payload: dict) -> None:
    print()
    print(f"== {title} ==")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def main() -> None:
    print_block("health", request_json("GET", f"{BASE_URL}/health"))
    print_block(
        "analyze/language",
        request_json("POST", f"{BASE_URL}/analyze/language", ROOT / "data" / "samples" / "language_request.json"),
    )
    print_block(
        "analyze/nonverbal",
        request_json("POST", f"{BASE_URL}/analyze/nonverbal", ROOT / "data" / "samples" / "nonverbal_request.json"),
    )
    print_block(
        "analyze/full",
        request_json("POST", f"{BASE_URL}/analyze/full", ROOT / "data" / "samples" / "full_request.json"),
    )


if __name__ == "__main__":
    main()
