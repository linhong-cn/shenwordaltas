#!/usr/bin/env python3
"""Regenerate the mini program's baked word list (utils/atlas-data.js) from the
PWA's public/atlas/g*/entries/*.json, so text, phonetics and examples never drift.

Keeps the compact schema the pages already use:
  i id | w word | z zh | p phonetic | c cefr index | t topic index | m memory
  s short zh | e example EN | x example ZH | b book | u unit
"""
import json
import glob
import sys
from pathlib import Path

PWA_ROOT = Path("/Users/hong/WorkBuddy/shenwordaltas")
TARGET = Path("/Users/hong/WorkBuddy/shenwordaltas-mp-v2/utils/atlas-data.js")
ORDER = ["i", "w", "z", "p", "c", "t", "m", "s", "e", "x", "b", "u"]
OPTIONAL = {"e", "x", "p"}


def main() -> int:
    raw = TARGET.read_text(encoding="utf-8")
    meta = json.loads(raw.split("=", 1)[1].strip().rstrip(";"))

    pwa = {}
    for f in sorted(glob.glob(str(PWA_ROOT / "public/atlas/g*/entries/*.json"))):
        for e in json.loads(Path(f).read_text(encoding="utf-8")):
            pwa[e["id"]] = e

    stats = {"phonetic": 0, "example": 0, "zh": 0, "word": 0, "missing": 0}
    for grade, block in meta.items():
        rebuilt = []
        for w in block["words"]:
            e = pwa.get(w["i"])
            if e is None:
                stats["missing"] += 1
                rebuilt.append(w)
                continue

            zh = ((e.get("senses") or [{}])[0].get("zh") or "").strip() or w["z"]
            phonetic = (e.get("uk") or e.get("us") or "").strip()
            examples = e.get("ex") or []
            en = examples[0].get("en", "") if examples else ""
            zx = examples[0].get("zh", "") if examples else ""

            if phonetic and not w["p"]:
                stats["phonetic"] += 1
            if en and not w.get("e"):
                stats["example"] += 1
            if zh != w["z"]:
                stats["zh"] += 1
            if e.get("w") and e["w"] != w["w"]:
                stats["word"] += 1

            row = {
                "i": w["i"],
                "w": e.get("w") or w["w"],
                "z": zh,
                "p": phonetic or w["p"],
                "c": w["c"],
                "t": w["t"],
                "m": w["m"],
                "s": zh,
                "e": en,
                "x": zx,
                "b": w["b"],
                "u": w["u"],
            }
            rebuilt.append({k: row[k] for k in ORDER})
        block["words"] = rebuilt

    out = "module.exports = " + json.dumps(meta, ensure_ascii=False, separators=(",", ":")) + ";\n"
    TARGET.write_text(out, encoding="utf-8")
    print("补齐音标 %(phonetic)d / 补齐例句 %(example)d / 修正释义 %(zh)d / 修正词形 %(word)d / 缺词 %(missing)d" % stats)
    return 0


if __name__ == "__main__":
    sys.exit(main())
