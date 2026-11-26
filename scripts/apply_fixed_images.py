#!/usr/bin/env python3
"""
Convert generated illustration PNG/JPG/WebP files to 512x512 WebP and apply them
to public/atlas/g{1..6}/{img,thumb}/{id}.webp according to a manifest JSON.
Also updates entries/*.json `note` fields to remove outdated image-reuse notices.

Usage:
  uv run --with pillow python3 scripts/apply_fixed_images.py --manifest output/fix-plan/manifest.json [--dry-run] [--only key1,key2]
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
PUBLIC_ATLAS = ROOT / "public" / "atlas"


def clean_note_for_redrawn_image(note: str) -> str:
    """Remove the '插画、' or '配图与' reference from entry.note when image is redrawn."""
    if not note:
        return note
    # Case 1: "插画、发音与详解参考词库词条 XXX。" -> "发音与详解参考词库词条 XXX。"
    updated = note.replace("插画、发音与详解参考词库词条", "发音与详解参考词库词条")
    # Case 2: "配图与详解参考词库词条 XXX。" -> "详解参考词库词条 XXX。"
    updated = updated.replace("配图与详解参考词库词条", "详解参考词库词条")
    # Case 3: "插画与详解参考词库词条 XXX。" -> "详解参考词库词条 XXX。"
    updated = updated.replace("插画与详解参考词库词条", "详解参考词库词条")
    # Case 4: "配图、发音与详解参考词库词条 XXX。" -> "发音与详解参考词库词条 XXX。"
    updated = updated.replace("配图、发音与详解参考词库词条", "发音与详解参考词库词条")
    # Case 5: "仅插画参考..." or "插画参考..." -> ""
    if re.fullmatch(r"(仅)?(插画|配图)参考词库词条\s*.+。?", updated.strip()):
        updated = ""
    # Case 6: "本词暂未匹配到词库插画与音频。" -> "本词暂未匹配到词库音频。"
    updated = updated.replace("本词暂未匹配到词库插画与音频。", "本词暂未匹配到词库音频。")
    return updated


def convert_to_512_webp(src: Path, dst: Path, quality: int = 86) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as im:
        im = im.convert("RGB")
        w, h = im.size
        # Center-crop to square if slightly non-square
        if w != h:
            side = min(w, h)
            left = (w - side) // 2
            top = (h - side) // 2
            im = im.crop((left, top, left + side, top + side))
        if im.size != (512, 512):
            im = im.resize((512, 512), Image.Resampling.LANCZOS)
        im.save(dst, format="WEBP", quality=quality, method=6)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True, help="Path to manifest JSON")
    ap.add_argument("--dry-run", action="store_true", help="Do not write files")
    ap.add_argument("--only", default="", help="Comma-separated manifest item keys to apply")
    ap.add_argument("--quality", type=int, default=86, help="WebP quality (default 86)")
    args = ap.parse_args()

    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    items = manifest["items"] if isinstance(manifest, dict) and "items" in manifest else manifest
    only_set = {x.strip() for x in args.only.split(",") if x.strip()}

    # Track which (grade, entry_id) had their images updated so we can clean notes
    updated_ids_by_grade: dict[int, set[str]] = {g: set() for g in range(1, 7)}
    applied_items = 0
    applied_files = 0
    missing_sources = []

    for item in items:
        key = item["key"]
        if only_set and key not in only_set:
            continue
        src_path = Path(item.get("image_path", ""))
        if not item.get("image_path") or not src_path.exists():
            missing_sources.append(key)
            continue

        applied_items += 1
        for occ in item["occurrences"]:
            g = int(occ["grade"])
            eid = occ["id"]
            img_dst = PUBLIC_ATLAS / f"g{g}" / "img" / f"{eid}.webp"
            thumb_dst = PUBLIC_ATLAS / f"g{g}" / "thumb" / f"{eid}.webp"
            if not args.dry_run:
                convert_to_512_webp(src_path, img_dst, quality=args.quality)
                convert_to_512_webp(src_path, thumb_dst, quality=args.quality)
            updated_ids_by_grade[g].add(eid)
            applied_files += 2

    # Update entries/*.json notes for updated IDs
    notes_updated = 0
    for g in range(1, 7):
        target_ids = updated_ids_by_grade[g]
        if not target_ids:
            continue
        for ep in sorted(glob.glob(str(PUBLIC_ATLAS / f"g{g}" / "entries" / "*.json"))):
            ep_path = Path(ep)
            data = json.loads(ep_path.read_text(encoding="utf-8"))
            changed = False
            for entry in data:
                if entry.get("id") in target_ids:
                    old_note = entry.get("note", "") or ""
                    new_note = clean_note_for_redrawn_image(old_note)
                    if new_note != old_note:
                        entry["note"] = new_note
                        changed = True
                        notes_updated += 1
            if changed and not args.dry_run:
                ep_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    print(
        f"{'[DRY-RUN] ' if args.dry_run else ''}"
        f"Applied {applied_items} unique images -> {applied_files} webp files "
        f"(img+thumb), updated {notes_updated} entry notes, "
        f"missing sources: {len(missing_sources)}"
    )
    if missing_sources:
        print("Missing source keys (first 20):", missing_sources[:20])


if __name__ == "__main__":
    main()
