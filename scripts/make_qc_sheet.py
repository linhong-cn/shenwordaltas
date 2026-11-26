#!/usr/bin/env python3
"""
Create a labeled contact sheet (QC grid) from a list of (label, image_path) pairs
for fast visual quality inspection (style consistency, meaning accuracy, no text).

Usage:
  uv run --with pillow python3 scripts/make_qc_sheet.py --out output/fix-qc/sheet.png --cols 4 "label1=path1" "label2=path2" ...
  or
  uv run --with pillow python3 scripts/make_qc_sheet.py --out output/fix-qc/sheet.png --cols 4 --json batch.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for c in candidates:
        if Path(c).exists():
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                pass
    return ImageFont.load_default()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--cols", type=int, default=4)
    ap.add_argument("--tile", type=int, default=320)
    ap.add_argument("--json", dest="json_path", default="")
    ap.add_argument("pairs", nargs="*")
    args = ap.parse_args()

    entries: list[tuple[str, str]] = []
    if args.json_path:
        raw = json.loads(Path(args.json_path).read_text(encoding="utf-8"))
        for row in raw:
            entries.append((row["label"], row["path"]))
    for p in args.pairs:
        label, path = p.split("=", 1)
        entries.append((label, path))

    if not entries:
        raise SystemExit("No images provided")

    cols = max(1, args.cols)
    rows = (len(entries) + cols - 1) // cols
    tile = args.tile
    pad = 16
    label_h = 44
    w = pad + cols * (tile + pad)
    h = pad + rows * (tile + label_h + pad)

    canvas = Image.new("RGB", (w, h), (247, 240, 224))
    draw = ImageDraw.Draw(canvas)
    font = load_font(18)

    for idx, (label, path) in enumerate(entries):
        r, c = divmod(idx, cols)
        x = pad + c * (tile + pad)
        y = pad + r * (tile + label_h + pad)
        with Image.open(path) as im:
            im = im.convert("RGB")
            iw, ih = im.size
            if iw != ih:
                side = min(iw, ih)
                im = im.crop(((iw - side) // 2, (ih - side) // 2, (iw + side) // 2, (ih + side) // 2))
            im = im.resize((tile, tile), Image.Resampling.LANCZOS)
            canvas.paste(im, (x, y))
        draw.text((x + 4, y + tile + 10), label[:36], fill=(42, 36, 30), font=font)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_path, format="PNG")
    print(f"Saved QC sheet ({len(entries)} tiles): {out_path}")


if __name__ == "__main__":
    main()
