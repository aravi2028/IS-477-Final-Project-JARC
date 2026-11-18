"""
Combine the raw MusicBrainz JSON files into one table.

Reads  data/raw/musicbrainz/recordings/<track_id>.json  (written by musicbrainz_collect.py)
Writes data/interim/musicbrainz_recordings.csv          (one row per Spotify track)

For each track the best candidate is chosen from the search results:
highest score first, then the recording whose length is closest to the
Spotify duration. A match_confidence flag is added:
  high   - score 100 and length within 5 s of Spotify (or length unknown)
  medium - score >= 90 and length within 15 s (or length unknown)
  low    - any other candidate
  none   - MusicBrainz returned no candidates

Usage:  python musicbrainz_parse.py
Safe to run while the collector is still running (it reads finished files only).
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
RAW_DIR = ROOT / "data" / "raw" / "musicbrainz" / "recordings"
OUT_DIR = ROOT / "data" / "interim"
OUT_CSV = OUT_DIR / "musicbrainz_recordings.csv"


def length_diff_s(rec: dict, spotify_ms: int) -> float | None:
    if rec.get("length") is None or not spotify_ms:
        return None
    return abs(rec["length"] - spotify_ms) / 1000


def pick_best(recs: list[dict], spotify_ms: int) -> dict | None:
    if not recs:
        return None
    def key(r):
        d = length_diff_s(r, spotify_ms)
        return (-(r.get("score") or 0), d if d is not None else 1e9)
    return sorted(recs, key=key)[0]


def confidence(rec: dict | None, diff: float | None) -> str:
    if rec is None:
        return "none"
    score = rec.get("score") or 0
    if score == 100 and (diff is None or diff <= 5):
        return "high"
    if score >= 90 and (diff is None or diff <= 15):
        return "medium"
    return "low"


def earliest_release(rec: dict) -> dict:
    rels = [r for r in rec.get("releases", []) if r.get("date")]
    return min(rels, key=lambda r: r["date"]) if rels else {}


def parse_file(path: Path) -> dict:
    d = json.loads(path.read_text(encoding="utf-8"))
    sp = d["spotify"]
    recs = d["response"].get("recordings", [])
    best = pick_best(recs, sp["duration_ms"])
    diff = length_diff_s(best, sp["duration_ms"]) if best else None

    row = {
        "track_id": d["track_id"],
        "track_name": sp["track_name"],
        "artists": sp["artists"],
        "album_name": sp["album_name"],
        "track_genre": sp["track_genre"],
        "spotify_duration_ms": sp["duration_ms"],
        "mb_n_candidates": len(recs),
        "match_confidence": confidence(best, diff),
        "requested_at": d["request"]["requested_at"],
    }
    if best:
        credits = best.get("artist-credit", [])
        rel = earliest_release(best)
        row.update({
            "recording_mbid": best.get("id"),
            "mb_title": best.get("title"),
            "mb_score": best.get("score"),
            "mb_length_ms": best.get("length"),
            "length_diff_s": diff,
            "mb_artist_credit": "".join(c.get("name", "") + c.get("joinphrase", "")
                                        for c in credits),
            "artist_mbid": credits[0]["artist"]["id"] if credits else None,
            "all_artist_mbids": "|".join(c["artist"]["id"] for c in credits),
            "first_release_date": best.get("first-release-date"),
            "isrcs": "|".join(best.get("isrcs", [])) or None,
            "n_releases": len(best.get("releases", [])),
            "earliest_release_title": rel.get("title"),
            "earliest_release_country": rel.get("country"),
            "release_group_type": (rel.get("release-group") or {}).get("primary-type"),
        })
    return row


def main() -> pd.DataFrame:
    files = sorted(RAW_DIR.glob("*.json"))
    rows, bad = [], []
    for f in files:
        try:
            rows.append(parse_file(f))
        except (json.JSONDecodeError, KeyError) as e:
            bad.append((f.name, repr(e)))

    df = pd.DataFrame(rows)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_CSV, index=False)

    print(f"Read {len(files):,} raw files -> {len(df):,} rows")
    print(f"Saved {OUT_CSV.relative_to(ROOT)}")
    if bad:
        print(f"Skipped {len(bad)} unreadable file(s):", bad[:5])
    if len(df):
        print("\nMatch confidence:")
        print(df["match_confidence"].value_counts().to_string())
        print("\nShare matched (high or medium) by genre, lowest 10:")
        matched = df["match_confidence"].isin(["high", "medium"])
        print(matched.groupby(df["track_genre"]).mean().sort_values()
              .head(10).round(2).to_string())
    return df


if __name__ == "__main__":
    main()
