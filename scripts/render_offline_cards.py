#!/usr/bin/env python3
"""Re-render offline picture-book JPEG cards in ../深词光绘本图片/ using headless Chrome
and the exact renderWordCard() Canvas layout from src/ui/share.ts.

Usage:
  uv run --with playwright python3 scripts/render_offline_cards.py --changed
  uv run --with playwright python3 scripts/render_offline_cards.py --all
"""
from __future__ import annotations

import argparse
import base64
import json
import pathlib
import subprocess
import sys
import time
from playwright.sync_api import sync_playwright

CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
BASE_URL = "http://localhost:5188"
OFFLINE_DIR = pathlib.Path("../深词光绘本图片")
GRADE_NAMES = {1: "一年级", 2: "二年级", 3: "三年级", 4: "四年级", 5: "五年级", 6: "六年级"}
GRADE_FROM_NAME = {v: k for k, v in GRADE_NAMES.items()}

RENDER_JS = r"""
async ({ baseUrl, grade, gradeLabel, entry }) => {
  const SERIF = '"Fraunces Variable", "Songti SC", "Noto Serif SC", Georgia, serif';
  const SANS = '-apple-system, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Noto Sans SC", sans-serif';
  const W = 1080, H = 1440, pad = 72, art = W - pad * 2;
  const SOURCE_TEXT = "源: https://github.com/linhong-cn/shenwordaltas";

  const c = document.createElement("canvas");
  c.width = W;
  c.height = H;
  const ctx = c.getContext("2d");

  await Promise.all([
    document.fonts.load(`600 120px ${SERIF}`),
    document.fonts.load(`italic 400 40px ${SERIF}`),
  ]).catch(() => null);

  function wrap(text, maxWidth) {
    const tokens = /[\u4e00-\u9fff]/.test(text) ? Array.from(text) : text.split(/(\s+)/);
    const lines = [];
    let line = "";
    for (const t of tokens) {
      const next = line + t;
      if (ctx.measureText(next).width > maxWidth && line.trim()) {
        lines.push(line.trim());
        line = t.trimStart();
      } else {
        line = next;
      }
    }
    if (line.trim()) lines.push(line.trim());
    return lines;
  }

  function roundRect(x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  }

  function loadImage(src) {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => resolve(img);
      img.onerror = reject;
      img.src = src;
    });
  }

  ctx.fillStyle = "#F3ECDF";
  ctx.fillRect(0, 0, W, H);

  ctx.save();
  roundRect(pad, pad, art, art * 0.78, 36);
  ctx.clip();
  ctx.fillStyle = "#EAE1D0";
  ctx.fillRect(pad, pad, art, art * 0.78);
  const imgSrc = `${baseUrl}/atlas/g${grade}/img/${entry.id}.webp`;
  const img = await loadImage(imgSrc);
  const crop = img.width * 0.78;
  ctx.drawImage(img, 0, (img.height - crop) / 2, img.width, crop, pad, pad, art, art * 0.78);
  ctx.restore();

  let y = pad + art * 0.78 + 120;
  ctx.fillStyle = "#1E2640";
  ctx.font = `600 ${entry.w.length > 12 ? 92 : 120}px ${SERIF}`;
  ctx.fillText(entry.w, pad, y);
  y += 62;

  ctx.font = `400 34px "Arial Unicode MS", "Lucida Grande", "Times New Roman", serif`;
  ctx.fillStyle = "#6B6F80";
  ctx.fillText(
    [entry.uk && `英 ${entry.uk}`, entry.us && entry.us !== entry.uk && `美 ${entry.us}`]
      .filter(Boolean)
      .join("    "),
    pad,
    y,
  );
  y += 72;

  const s0 = entry.senses[0] || { pos: "", zh: "" };
  ctx.fillStyle = "#C4573A";
  ctx.font = `italic 400 38px ${SERIF}`;
  ctx.fillText(s0.pos || "", pad, y);
  const posW = ctx.measureText((s0.pos || "") + "  ").width;
  ctx.fillStyle = "#1E2640";
  ctx.font = `600 40px ${SANS}`;
  ctx.fillText(entry.senses.slice(0, 2).map((s) => s.zh).join("；"), pad + posW, y);
  y += 76;

  if (entry.ex && entry.ex[0]) {
    ctx.font = `italic 400 36px ${SERIF}`;
    ctx.fillStyle = "#3C4560";
    for (const line of wrap(`“${entry.ex[0].en}”`, art).slice(0, 3)) {
      ctx.fillText(line, pad, y);
      y += 50;
    }
    ctx.font = `400 30px ${SANS}`;
    ctx.fillStyle = "#7A7C88";
    for (const line of wrap(entry.ex[0].zh, art).slice(0, 2)) {
      ctx.fillText(line, pad, y + 6);
      y += 44;
    }
  }

  ctx.fillStyle = "rgba(30,38,64,.14)";
  ctx.fillRect(pad, H - 148, art, 2);

  ctx.fillStyle = "#1E2640";
  ctx.font = `600 34px ${SERIF}`;
  ctx.fillText(`深词光 · ${gradeLabel}`, pad, H - 96);

  ctx.font = `400 26px ${SANS}`;
  ctx.fillStyle = "#7A7C88";
  const tag = "一词一画，快乐背词";
  ctx.fillText(tag, W - pad - ctx.measureText(tag).width, H - 96);

  ctx.font = `400 22px ${SANS}`;
  ctx.fillStyle = "#8A8D98";
  const sw = ctx.measureText(SOURCE_TEXT).width;
  ctx.fillText(SOURCE_TEXT, W - pad - sw, H - 50);

  return c.toDataURL("image/jpeg", 0.93).split(",", 2)[1];
}
"""


def find_changed_ids() -> set[tuple[int, str]]:
    out = subprocess.check_output(["git", "diff", "--name-only", "public/atlas/"], text=True).splitlines()
    changed: set[tuple[int, str]] = set()
    for p in out:
        parts = p.split("/")
        if len(parts) == 5 and parts[3] == "img" and parts[4].endswith(".webp"):
            changed.add((int(parts[2][1:]), parts[4][:-5]))
    for g in range(1, 7):
        for ef in sorted(pathlib.Path(f"public/atlas/g{g}/entries").glob("*.json")):
            cur = {e["id"]: e for e in json.loads(ef.read_text())}
            old_raw = subprocess.check_output(["git", "show", f"HEAD:{ef.as_posix()}"], text=True)
            old = {e["id"]: e for e in json.loads(old_raw)}
            for eid, ce in cur.items():
                oe = old.get(eid)
                if not oe:
                    changed.add((g, eid))
                    continue
                k = lambda e: (e.get("w"), e.get("uk"), e.get("us"), e.get("senses"), (e.get("ex") or [None])[0])
                if k(ce) != k(oe):
                    changed.add((g, eid))
    return changed


def load_all_entries() -> dict[tuple[int, str], dict]:
    entries: dict[tuple[int, str], dict] = {}
    for g in range(1, 7):
        for ef in sorted(pathlib.Path(f"public/atlas/g{g}/entries").glob("*.json")):
            for item in json.loads(ef.read_text()):
                entries[(g, item["id"])] = item
    return entries


def map_offline_cards() -> dict[tuple[int, str], pathlib.Path]:
    cards: dict[tuple[int, str], pathlib.Path] = {}
    for jpg in sorted(OFFLINE_DIR.rglob("*.jpg")):
        g = GRADE_FROM_NAME[jpg.parts[2]]
        eid = jpg.stem.split("_", 1)[1]
        cards[(g, eid)] = jpg
    return cards


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="Re-render all 1,880 cards")
    ap.add_argument("--base-url", default=BASE_URL)
    args = ap.parse_args()

    entries = load_all_entries()
    cards = map_offline_cards()
    targets = sorted(entries.keys()) if args.all else sorted(find_changed_ids())

    missing = [k for k in targets if k not in cards]
    if missing:
        print(f"ERROR: {len(missing)} target IDs not found in {OFFLINE_DIR}: {missing[:5]}", file=sys.stderr)
        sys.exit(1)

    t0 = time.time()
    print(f"Rendering {len(targets)} offline picture-book cards via headless Chrome ({args.base_url})...")
    per_grade = {g: 0 for g in range(1, 7)}

    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROME_PATH, headless=True)
        page = browser.new_page(viewport={"width": 1200, "height": 900})
        page.goto(args.base_url, wait_until="networkidle")
        # Ensure Fraunces Variable is loaded
        page.evaluate("() => document.fonts.ready")

        for i, key in enumerate(targets, 1):
            g, eid = key
            entry = entries[key]
            b64 = page.evaluate(
                RENDER_JS,
                {"baseUrl": args.base_url, "grade": g, "gradeLabel": GRADE_NAMES[g], "entry": entry},
            )
            dst = cards[key]
            tmp = dst.with_suffix(".jpg.tmp")
            tmp.write_bytes(base64.b64decode(b64))
            tmp.replace(dst)
            per_grade[g] += 1
            if i % 100 == 0 or i == len(targets):
                elapsed = time.time() - t0
                print(f"  [{i}/{len(targets)}] {elapsed:.1f}s ({i / max(elapsed, 0.1):.1f} cards/s)")

        browser.close()

    print("Done! Per-grade re-rendered:", json.dumps(per_grade))


if __name__ == "__main__":
    main()
