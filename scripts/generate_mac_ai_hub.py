#!/usr/bin/env python3
"""
Resumable batch image generator using local mac_ai_hub Qwen-Image 2.1 API
(http://127.0.0.1:8788/api/tools/image.generate/run).

Usage:
  uv run --with requests --with pillow python3 scripts/generate_mac_ai_hub.py \
      --manifest output/fix-plan/manifest.json \
      --grade 6 \
      --size 768x768 \
      --steps 28 \
      --qc-prefix output/fix-qc/g6-sheet
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path
import requests

BASE_URL = "http://127.0.0.1:8788"

STYLE_STILL_LIFE = (
    "Flat mid-century modern editorial vector illustration with subtle matte gouache paper-grain texture, "
    "bold opaque solid color shapes like cut-paper collage, completely lineless with zero outlines and zero sketch lines, "
    "NOT watercolor, NOT pencil drawing, clean crisp geometric silhouettes, "
    "warm muted vintage palette: warm ivory cream background, terracotta rust orange, sage olive green, dusty slate blue, deep navy, mustard ochre yellow, warm wood brown. "
    "Strictly no text, no letters, no numbers, no written signs, no borders, no watermarks. "
)

STYLE_CHARACTER = (
    "Flat mid-century modern editorial vector illustration with subtle matte gouache paper-grain texture, "
    "bold opaque solid color shapes like cut-paper collage, completely lineless with zero outlines and zero sketch lines, "
    "NOT watercolor, NOT pencil drawing, clean crisp geometric silhouettes, "
    "cute stylized rounded people with simple dot eyes and soft round terracotta blush cheeks, "
    "warm muted vintage palette: warm ivory cream background, terracotta rust orange, sage olive green, dusty slate blue, deep navy, mustard ochre yellow, warm wood brown. "
    "Strictly no text, no letters, no numbers, no written signs, no borders, no watermarks. "
)

HUMAN_KEYWORDS = (
    "child", "children", "boy", "girl", "kid", "kids", "student", "students",
    "teacher", "grandma", "grandmother", "grandpa", "grandfather", "grandparent",
    "mother", "father", "mom", "dad", "parent", "family", "person", "people",
    "friend", "friends", "neighbor", "neighbour", "worker", "doctor", "nurse",
    "officer", "driver", "farmer", "man", "woman", "baby", "player", "actor",
    "singer", "dancer", "host", "guest", "crowd", "team", "classmate", "winner",
    "scientist", "chef", "baker", "painter", "cyclist", "swimmer", "skater",
    "hiker", "elder", "smiling", "waving", "hand", "hands",
)


def pick_style_prefix(scene: str) -> str:
    low = scene.lower()
    if any(f" {kw}" in f" {low}" or f"{kw}s" in low for kw in HUMAN_KEYWORDS):
        # Still-life prompts that explicitly say "no people" should use STYLE_STILL_LIFE
        if "no people" in low or "still life" in low:
            return STYLE_STILL_LIFE
        return STYLE_CHARACTER
    return STYLE_STILL_LIFE


def deterministic_seed(key: str, offset: int = 0) -> int:
    h = int(hashlib.md5(key.encode("utf-8")).hexdigest()[:8], 16)
    return (h + offset) % 2147483647


def run_image_job(prompt: str, size: str, steps: int, seed: int, model: str = "qwen-image-2.1") -> bytes:
    r = requests.post(
        f"{BASE_URL}/api/tools/image.generate/run",
        json={
            "params": {
                "prompt": prompt,
                "size": size,
                "steps": steps,
                "seed": seed,
                "model": model,
            },
            "files": {},
        },
        timeout=30,
    )
    r.raise_for_status()
    jid = r.json()["job_id"]
    while True:
        jr = requests.get(f"{BASE_URL}/api/jobs/{jid}", timeout=30).json()
        st = jr["status"]
        if st == "succeeded":
            art_name = jr["artifacts"][0]["name"]
            img_r = requests.get(f"{BASE_URL}/api/jobs/{jid}/artifacts/{art_name}", timeout=60)
            img_r.raise_for_status()
            return img_r.content
        if st in ("failed", "cancelled"):
            raise RuntimeError(f"Job {jid} {st}: {jr.get('error')}")
        time.sleep(1.0)


def build_qc_sheet(sheet_path: Path, batch_items: list[dict], cols: int = 4) -> None:
    rows = []
    for it in batch_items:
        p = Path(it["image_path"])
        if p.exists():
            rows.append({"label": f"{it['word']} ({it['zh'][:12]})", "path": str(p)})
    if not rows:
        return
    tmp_json = sheet_path.with_suffix(".json")
    tmp_json.parent.mkdir(parents=True, exist_ok=True)
    tmp_json.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    subprocess.run(
        [sys.executable, "scripts/make_qc_sheet.py", "--out", str(sheet_path), "--cols", str(cols), "--json", str(tmp_json)],
        check=True,
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default="output/fix-plan/manifest.json")
    ap.add_argument("--grade", type=int, default=0, help="Filter to items occurring in this grade (0 = all)")
    ap.add_argument("--category", default="", help="Optional comma-separated categories: ref_phrase,ref_single,p2_polysemy")
    ap.add_argument("--only", default="", help="Optional comma-separated keys")
    ap.add_argument("--size", default="768x768")
    ap.add_argument("--steps", type=int, default=22)
    ap.add_argument("--seed-offset", type=int, default=0)
    ap.add_argument("--cooldown", type=float, default=18.0, help="Seconds to sleep after each image to keep Mac GPU cool")
    ap.add_argument("--batch-rest", type=float, default=45.0, help="Extra seconds to rest after every 16 generated images")
    ap.add_argument("--pending-only", action="store_true", help="Only select items whose target image does not exist yet")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--qc-prefix", default="", help="Write a 16-tile QC contact sheet per chunk")
    args = ap.parse_args()

    manifest_path = Path(args.manifest)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    cats = {c.strip() for c in args.category.split(",") if c.strip()}
    only = {k.strip() for k in args.only.split(",") if k.strip()}

    selected = []
    for it in manifest["items"]:
        if args.grade and not any(int(o["grade"]) == args.grade for o in it["occurrences"]):
            continue
        if cats and it["category"] not in cats:
            continue
        if only and it["key"] not in only:
            continue
        if args.pending_only:
            cur_p = Path(it.get("image_path", ""))
            gen_p = Path("output/fix-generated") / f"{it['key']}.png"
            if (cur_p.exists() and it.get("status") in ("calibrated", "generated")) or gen_p.exists():
                continue
        selected.append(it)

    # Order: ref_phrase / ref_single first, then p2_polysemy
    selected.sort(key=lambda x: (0 if x["category"].startswith("ref_") else 1, x["key"]))
    print(f"Selected {len(selected)} items (grade={args.grade or 'all'}, size={args.size}, steps={args.steps})", flush=True)

    out_dir = Path("output/fix-generated")
    out_dir.mkdir(parents=True, exist_ok=True)

    done_count = 0
    gen_count = 0
    fail_list = []

    for idx, it in enumerate(selected, 1):
        key = it["key"]
        dst = out_dir / f"{key}.png"
        # Update manifest image_path to the PNG we generate
        if it.get("status") != "calibrated" or args.force:
            it["image_path"] = str(dst)

        if dst.exists() and not args.force:
            done_count += 1
            print(f"[{idx}/{len(selected)}] SKIP (exists) {key}", flush=True)
            continue

        prompt = pick_style_prefix(it["scene_prompt"]) + it["scene_prompt"]
        seed = deterministic_seed(key, args.seed_offset)
        t0 = time.time()
        try:
            png_bytes = run_image_job(prompt, args.size, args.steps, seed)
            dst.write_bytes(png_bytes)
            it["status"] = "generated"
            gen_count += 1
            done_count += 1
            print(f"[{idx}/{len(selected)}] OK ({time.time()-t0:.1f}s) {key} -> {dst}", flush=True)
        except Exception as e:
            fail_list.append((key, str(e)))
            print(f"[{idx}/{len(selected)}] FAIL {key}: {e}", flush=True)

        # Periodically persist manifest + build QC sheet every 16 items
        if args.qc_prefix and idx % 16 == 0:
            sheet_idx = idx // 16
            build_qc_sheet(Path(f"{args.qc_prefix}-{sheet_idx}.png"), selected[idx-16:idx])
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

        # Thermal pacing: let Mac GPU cool between images / batches
        if idx < len(selected):
            if gen_count > 0 and gen_count % 16 == 0 and args.batch_rest > 0:
                print(f"  [cooling] batch rest {args.batch_rest:.0f}s...", flush=True)
                time.sleep(args.batch_rest)
            elif args.cooldown > 0:
                time.sleep(args.cooldown)

    # Build final partial QC sheet
    if args.qc_prefix and selected:
        rem = len(selected) % 16
        if rem:
            sheet_idx = (len(selected) // 16) + 1
            build_qc_sheet(Path(f"{args.qc_prefix}-{sheet_idx}.png"), selected[-rem:])

    manifest["style_prefix"] = STYLE_STILL_LIFE
    manifest["style_prefix_character"] = STYLE_CHARACTER
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Finished: done={done_count}/{len(selected)}, newly_generated={gen_count}, failed={len(fail_list)}", flush=True)
    if fail_list:
        print("Failures:", fail_list, flush=True)


if __name__ == "__main__":
    main()
