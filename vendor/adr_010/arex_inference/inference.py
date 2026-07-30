#!/usr/bin/env python3
"""Run one AREX BrowseComp generation through an OpenAI-compatible endpoint."""

from __future__ import annotations

import argparse
import os

from prompts import build_messages


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--question", required=True)
    parser.add_argument(
        "--base-url",
        default=os.environ.get("AREX_BASE_URL", "http://127.0.0.1:8000/v1"),
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("AREX_API_KEY", "EMPTY"),
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("AREX_MODEL", "AREX-Turbo"),
    )
    parser.add_argument("--max-tokens", type=int, default=8192)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise SystemExit("Install the client first: pip install -U openai") from exc

    client = OpenAI(
        base_url=args.base_url.rstrip("/") + "/",
        api_key=args.api_key,
        timeout=600.0,
    )
    response = client.chat.completions.create(
        model=args.model,
        messages=build_messages(args.question),
        max_tokens=args.max_tokens,
        temperature=1.0,
        top_p=0.95,
        presence_penalty=1.5,
        extra_body={"top_k": 20},
    )
    print(response.choices[0].message.content or "")


if __name__ == "__main__":
    main()
