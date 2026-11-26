#!/usr/bin/env python3
"""
Generate missing and corrected English pronunciation & example MP3s via local
mac_ai_hub Qwen3-TTS 1.7B CustomVoice (http://127.0.0.1:8788/api/tools/tts.speak/run),
encode WAV -> 64kbps mono MP3 via lameenc, write to public/atlas/g{1..6}/audio/{uk,us,ex,ex2}/,
and sync media bitmasks (m) in index.json and entries/*.json.

Uses content-addressed caching under output/fix-tts-cache/ so identical words/sentences
are synthesized only once and runs are 100% resumable.

Usage:
  uv run --with requests --with lameenc python3 scripts/generate_tts_mac_ai_hub.py \
      --grade 6 --cooldown 2.5 --batch-rest 20
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import io
import json
import os
import time
import wave
from pathlib import Path
import lameenc
import requests

BASE_URL = "http://127.0.0.1:8788"
ROOT = Path(__file__).resolve().parent.parent
PUBLIC_ATLAS = ROOT / "public" / "atlas"
CACHE_DIR = ROOT / "output" / "fix-tts-cache"

MEDIA_IMG = 1
MEDIA_UK = 2
MEDIA_US = 4
MEDIA_EX = 8
MEDIA_EX2 = 16


def cache_key(voice: str, accent: str, text: str) -> str:
    raw = f"{voice}|{accent}|{text.strip()}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def wav_to_mp3(wav_bytes: bytes, bitrate: int = 64) -> bytes:
    with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
        ch = wf.getnchannels()
        sr = wf.getframerate()
        pcm = wf.readframes(wf.getnframes())
    enc = lameenc.Encoder()
    enc.set_bit_rate(bitrate)
    enc.set_in_sample_rate(sr)
    enc.set_channels(ch)
    enc.set_quality(2)
    return bytes(enc.encode(pcm) + enc.flush())


def synth_mp3(text: str, voice: str, accent: str, is_sentence: bool) -> bytes:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    ck = cache_key(voice, accent, text)
    cp = CACHE_DIR / f"{ck}.mp3"
    if cp.exists() and cp.stat().st_size > 500:
        return cp.read_bytes()

    instruct = (
        f"Clear, natural, warm {accent} reading of an example sentence for elementary school students, friendly moderate pace."
        if is_sentence
        else f"Clear, crisp, natural {accent} pronunciation of a single vocabulary word or phrase for elementary school students."
    )
    r = requests.post(
        f"{BASE_URL}/api/tools/tts.speak/run",
        json={
            "params": {
                "text": text,
                "voice": voice,
                "language": "english",
                "instruct": instruct,
                "model": "Qwen3-TTS-1.7B-CustomVoice",
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
            wav_bytes = requests.get(f"{BASE_URL}/api/jobs/{jid}/artifacts/{art_name}", timeout=60).content
            mp3_bytes = wav_to_mp3(wav_bytes)
            cp.write_bytes(mp3_bytes)
            return mp3_bytes
        if st in ("failed", "cancelled"):
            raise RuntimeError(f"TTS job {jid} {st}: {jr.get('error')}")
        time.sleep(0.4)


def clean_speak_word(word: str, wid: str) -> str:
    if wid == "g4_b2_u2_174_it":
        return "I. T."
    if word == "like doing sth.":
        return "like doing something"
    if word == "show ... around ...":
        return "show around"
    if word == "PS":
        return "P. S."
    if word == "PE":
        return "P. E."
    return word


def sync_media_bitmasks(grades: list[int]) -> None:
    for g in grades:
        idx_path = PUBLIC_ATLAS / f"g{g}" / "index.json"
        idx = json.loads(idx_path.read_text(encoding="utf-8"))
        m_by_id: dict[str, int] = {}
        voiced = 0
        illustrated = 0
        for row in idx["words"]:
            wid = row[0]
            m = 0
            if (PUBLIC_ATLAS / f"g{g}" / "img" / f"{wid}.webp").exists():
                m |= MEDIA_IMG
                illustrated += 1
            if (PUBLIC_ATLAS / f"g{g}" / "audio" / "uk" / f"{wid}.mp3").exists():
                m |= MEDIA_UK
            if (PUBLIC_ATLAS / f"g{g}" / "audio" / "us" / f"{wid}.mp3").exists():
                m |= MEDIA_US
            if (PUBLIC_ATLAS / f"g{g}" / "audio" / "ex" / f"{wid}.mp3").exists():
                m |= MEDIA_EX
            if (PUBLIC_ATLAS / f"g{g}" / "audio" / "ex2" / f"{wid}.mp3").exists():
                m |= MEDIA_EX2
            if m & (MEDIA_UK | MEDIA_US):
                voiced += 1
            row[6] = m
            m_by_id[wid] = m

        idx["illustrated"] = illustrated
        if "voiced" in idx:
            idx["voiced"] = voiced
        idx_path.write_text(json.dumps(idx, ensure_ascii=False), encoding="utf-8")

        for ep in sorted(glob.glob(str(PUBLIC_ATLAS / f"g{g}" / "entries" / "*.json"))):
            ep_path = Path(ep)
            chunk = json.loads(ep_path.read_text(encoding="utf-8"))
            changed = False
            for entry in chunk:
                nm = m_by_id.get(entry["id"])
                if nm is not None and entry.get("m") != nm:
                    entry["m"] = nm
                    changed = True
            if changed:
                ep_path.write_text(json.dumps(chunk, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--grade", type=int, default=0, help="Target grade 1..6 (0 = all)")
    ap.add_argument("--cooldown", type=float, default=2.0, help="Seconds to rest between newly synthesized clips")
    ap.add_argument("--batch-rest", type=float, default=15.0, help="Extra seconds to rest every 40 newly synthesized clips")
    ap.add_argument("--skip-ex2", action="store_true", help="Skip generating ex2 audio")
    args = ap.parse_args()

    targets = json.loads((ROOT / "output" / "fix-text" / "text_targets.json").read_text(encoding="utf-8"))
    # Set of (grade, id) whose word uk/us audio must be replaced/generated
    word_audio_ids = {
        (int(o["grade"]), o["id"])
        for grp in targets["audio_word_targets"]
        for o in grp["occurrences"]
    }
    # Set of (grade, id) whose ex/ex2 text was rewritten or missing
    ex_audio_ids = {
        (int(o["grade"]), o["id"])
        for grp in targets["groups"]
        for o in grp["occurrences"]
    }

    grades = [args.grade] if args.grade else [1, 2, 3, 4, 5, 6]

    # Collect jobs: list of (grade, wid, kind, text, voice, accent, is_sentence)
    jobs: list[tuple[int, str, str, str, str, str, bool]] = []
    for g in grades:
        entries = {}
        for ep in sorted(glob.glob(str(PUBLIC_ATLAS / f"g{g}" / "entries" / "*.json"))):
            for e in json.loads(Path(ep).read_text(encoding="utf-8")):
                entries[e["id"]] = e

        for wid, e in sorted(entries.items()):
            w = e.get("w", "")
            exs = e.get("ex") or []
            if (g, wid) in word_audio_ids:
                sw = clean_speak_word(w, wid)
                jobs.append((g, wid, "uk", sw, "serena", "British English", False))
                jobs.append((g, wid, "us", sw, "vivian", "American English", False))
            if (g, wid) in ex_audio_ids:
                if len(exs) >= 1 and exs[0].get("en"):
                    jobs.append((g, wid, "ex", exs[0]["en"], "serena", "British English", True))
                if (not args.skip_ex2) and len(exs) >= 2 and exs[1].get("en"):
                    jobs.append((g, wid, "ex2", exs[1]["en"], "vivian", "American English", True))

    # Count unique texts to synthesize (not yet cached)
    unique_uncached = set()
    for _, _, _, text, voice, accent, _ in jobs:
        ck = cache_key(voice, accent, text)
        if not (CACHE_DIR / f"{ck}.mp3").exists():
            unique_uncached.add(ck)

    print(f"TTS plan (grades={grades}): total_files={len(jobs)}, unique_uncached_to_synth={len(unique_uncached)}", flush=True)

    synth_count = 0
    written = 0
    failed = []
    for i, (g, wid, kind, text, voice, accent, is_sent) in enumerate(jobs, 1):
        ck = cache_key(voice, accent, text)
        was_cached = (CACHE_DIR / f"{ck}.mp3").exists()
        dst = PUBLIC_ATLAS / f"g{g}" / "audio" / kind / f"{wid}.mp3"
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            t0 = time.time()
            mp3_bytes = synth_mp3(text, voice, accent, is_sent)
            dst.write_bytes(mp3_bytes)
            written += 1
            if not was_cached:
                synth_count += 1
                if synth_count % 20 == 0 or synth_count <= 5:
                    print(f"  [synth {synth_count}/{len(unique_uncached)} | file {i}/{len(jobs)}] OK ({time.time()-t0:.1f}s) g{g} {kind}/{wid}", flush=True)
                if synth_count % 40 == 0 and args.batch_rest > 0:
                    print(f"  [cooling] TTS batch rest {args.batch_rest:.0f}s...", flush=True)
                    time.sleep(args.batch_rest)
                elif args.cooldown > 0:
                    time.sleep(args.cooldown)
        except Exception as exc:
            failed.append((g, wid, kind, str(exc)))
            print(f"  [FAIL] g{g} {kind}/{wid}: {exc}", flush=True)

    sync_media_bitmasks(grades)
    print(f"TTS finished: written={written}/{len(jobs)}, newly_synthesized={synth_count}, failed={len(failed)}", flush=True)
    if failed:
        print("Failures (first 20):", failed[:20], flush=True)


if __name__ == "__main__":
    main()
