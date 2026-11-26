#!/usr/bin/env python3
"""
Apply generated entry text metadata (senses, ex, col, tip, ipa, cleaned note) and
the 7 source typo fixes to public/atlas/g{1..6}/index.json and entries/*.json.

Usage:
  python3 scripts/apply_fixed_text.py
"""
from __future__ import annotations

import glob
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLIC_ATLAS = ROOT / "public" / "atlas"
TARGETS_PATH = ROOT / "output" / "fix-text" / "text_targets.json"
GEN_PATH = ROOT / "output" / "fix-text" / "generated_text.json"


def main() -> None:
    targets = json.loads(TARGETS_PATH.read_text(encoding="utf-8"))
    gen_map = json.loads(GEN_PATH.read_text(encoding="utf-8"))
    typo_fixes = targets["typo_fixes"]

    # Map (grade, id) -> group data + generated payload
    by_occ: dict[tuple[int, str], tuple[dict, dict]] = {}
    missing_gen = []
    for grp in targets["groups"]:
        gkey = grp["gkey"]
        payload = gen_map.get(gkey)
        if not payload:
            missing_gen.append(gkey)
            continue
        for o in grp["occurrences"]:
            by_occ[(int(o["grade"]), o["id"])] = (grp, payload)

    if missing_gen:
        print(f"WARNING: {len(missing_gen)} missing generated groups: {missing_gen[:10]}")

    updated_entries = 0
    updated_index_rows = 0

    for g in range(1, 7):
        idx_path = PUBLIC_ATLAS / f"g{g}" / "index.json"
        idx = json.loads(idx_path.read_text(encoding="utf-8"))

        # Update index.json rows (typos + missing IPA)
        for row in idx["words"]:
            wid = row[0]
            tfix = typo_fixes.get(f"{g}:{wid}", {})
            changed_row = False
            if "w" in tfix and row[1] != tfix["w"]:
                row[1] = tfix["w"]
                changed_row = True
            if "zh" in tfix and row[2] != tfix["zh"]:
                row[2] = tfix["zh"]
                changed_row = True
            if "ipa" in tfix and row[3] != tfix["ipa"]:
                row[3] = tfix["ipa"]
                changed_row = True
            if (g, wid) in by_occ:
                grp, payload = by_occ[(g, wid)]
                if not row[3] and payload.get("uk"):
                    row[3] = payload["uk"]
                    changed_row = True
            if changed_row:
                updated_index_rows += 1

        # Update entries/*.json
        total_examples = 0
        for ep in sorted(glob.glob(str(PUBLIC_ATLAS / f"g{g}" / "entries" / "*.json"))):
            ep_path = Path(ep)
            chunk = json.loads(ep_path.read_text(encoding="utf-8"))
            chunk_changed = False
            for entry in chunk:
                wid = entry["id"]
                tfix = typo_fixes.get(f"{g}:{wid}", {})
                if "w" in tfix and entry.get("w") != tfix["w"]:
                    entry["w"] = tfix["w"]
                    chunk_changed = True
                if "zh" in tfix and entry.get("senses"):
                    entry["senses"][0]["zh"] = tfix["zh"]
                    chunk_changed = True
                if "ipa" in tfix:
                    entry["uk"] = tfix["ipa"]
                    entry["us"] = tfix["ipa"]
                    chunk_changed = True

                if (g, wid) in by_occ:
                    grp, payload = by_occ[(g, wid)]
                    entry["w"] = grp["word"]
                    if payload.get("uk") and not entry.get("uk"):
                        entry["uk"] = payload["uk"]
                    if payload.get("us") and not entry.get("us"):
                        entry["us"] = payload["us"]
                    # Keep textbook zh strictly intact in senses[0]
                    senses = payload.get("senses") or []
                    if senses:
                        senses = [dict(s) for s in senses]
                        senses[0]["zh"] = grp["zh"]
                        entry["senses"] = senses
                    if payload.get("ex"):
                        entry["ex"] = payload["ex"][:2]
                    entry["col"] = payload.get("col") or []
                    entry["fam"] = payload.get("fam") or []
                    entry["syn"] = payload.get("syn") or []
                    entry["ant"] = payload.get("ant") or []
                    entry["tip"] = payload.get("tip") or ""
                    # Clear outdated borrowed-root or missing-asset note
                    old_note = entry.get("note", "") or ""
                    if "参考词库词条" in old_note or "暂未匹配到词库" in old_note:
                        entry["note"] = ""
                    chunk_changed = True
                    updated_entries += 1

                total_examples += len(entry.get("ex") or [])

            if chunk_changed:
                ep_path.write_text(json.dumps(chunk, ensure_ascii=False), encoding="utf-8")

        idx["examples"] = total_examples
        idx_path.write_text(json.dumps(idx, ensure_ascii=False), encoding="utf-8")

    print(f"Applied fixed text: updated_entries={updated_entries}, updated_index_rows={updated_index_rows}, missing_gen={len(missing_gen)}")


if __name__ == "__main__":
    main()
