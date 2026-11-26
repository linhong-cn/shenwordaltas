#!/usr/bin/env python3
"""
Resumable batch image generator driven by output/fix-plan/manifest.json.
Supports:
  --provider openai  (uses OPENAI_API_KEY, optional OPENAI_BASE_URL, model gpt-image-1)
  --provider gemini  (uses GEMINI_API_KEY, model imagen-3.0-generate-002 / gemini-2.5-flash-image)

Usage:
  uv run --with requests --with pillow python3 scripts/generate_from_manifest.py \
      --manifest output/fix-plan/manifest.json \
      --provider openai \
      --priority P0,P1 \
      --concurrency 3
"""
from __future__ import annotations

import argparse
import base64
import concurrent.futures
import io
import json
import os
import time
from pathlib import Path
from PIL import Image
import requests


def generate_openai(prompt: str, model: str, api_key: str, base_url: str) -> bytes:
    url = base_url.rstrip("/") + "/images/generations"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "prompt": prompt,
        "size": "1024x1024",
        "n": 1,
    }
    if model == "gpt-image-1":
        payload["quality"] = "medium"
        payload["output_format"] = "jpeg"
    else:
        payload["response_format"] = "b64_json"

    resp = requests.post(url, headers=headers, json=payload, timeout=180)
    resp.raise_for_status()
    data = resp.json()["data"][0]
    if "b64_json" in data:
        return base64.b64decode(data["b64_json"])
    if "url" in data:
        r2 = requests.get(data["url"], timeout=60)
        r2.raise_for_status()
        return r2.content
    raise RuntimeError(f"Unexpected OpenAI image response keys: {list(data.keys())}")


def generate_gemini(prompt: str, model: str, api_key: str) -> bytes:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:predict?key={api_key}"
    payload = {
        "instances": [{"prompt": prompt}],
        "parameters": {"sampleCount": 1, "aspectRatio": "1:1"},
    }
    resp = requests.post(url, json=payload, timeout=180)
    resp.raise_for_status()
    b64 = resp.json()["predictions"][0]["bytesBase64Encoded"]
    return base64.b64decode(b64)


def save_jpg(raw_bytes: bytes, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(io.BytesIO(raw_bytes)) as im:
        im = im.convert("RGB")
        im.save(out_path, format="JPEG", quality=92)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default="output/fix-plan/manifest.json")
    ap.add_argument("--provider", choices=["openai", "gemini"], required=True)
    ap.add_argument("--model", default="")
    ap.add_argument("--priority", default="P0,P1,P2")
    ap.add_argument("--only", default="")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--concurrency", type=int, default=3)
    ap.add_argument("--force", action="store_true", help="Overwrite existing images")
    args = ap.parse_args()

    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    style_prefix = manifest["style_prefix"]
    allowed_prios = {p.strip().upper() for p in args.priority.split(",") if p.strip()}
    only_set = {x.strip() for x in args.only.split(",") if x.strip()}

    if args.provider == "openai":
        api_key = os.environ.get("OPENAI_API_KEY", "")
        base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
        model = args.model or "gpt-image-1"
    else:
        api_key = os.environ.get("GEMINI_API_KEY", "")
        base_url = ""
        model = args.model or "imagen-3.0-generate-002"

    if not api_key:
        raise SystemExit(f"Missing API key env var for provider={args.provider}")

    todo = []
    for item in manifest["items"]:
        if item["priority"].upper() not in allowed_prios:
            continue
        if only_set and item["key"] not in only_set:
            continue
        out_path = Path(item["image_path"])
        if out_path.exists() and not args.force:
            continue
        if not item.get("scene_prompt"):
            continue
        todo.append(item)

    if args.limit > 0:
        todo = todo[: args.limit]

    print(f"Queued {len(todo)} images (provider={args.provider}, model={model}, concurrency={args.concurrency})")
    if not todo:
        return

    def run_one(item: dict) -> tuple[str, str]:
        full_prompt = style_prefix + item["scene_prompt"]
        out_path = Path(item["image_path"])
        for attempt in range(1, 4):
            try:
                if args.provider == "openai":
                    raw = generate_openai(full_prompt, model, api_key, base_url)
                else:
                    raw = generate_gemini(full_prompt, model, api_key)
                save_jpg(raw, out_path)
                return item["key"], f"OK -> {out_path}"
            except Exception as e:
                if attempt == 3:
                    return item["key"], f"FAIL: {e}"
                time.sleep(3 * attempt)
        return item["key"], "FAIL"

    ok = 0
    fail = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        for i, (key, status) in enumerate(ex.map(run_one, todo), 1):
            if status.startswith("OK"):
                ok += 1
            else:
                fail += 1
            print(f"[{i}/{len(todo)}] {key}: {status}", flush=True)

    print(f"Done: ok={ok}, fail={fail}")


if __name__ == "__main__":
    main()
