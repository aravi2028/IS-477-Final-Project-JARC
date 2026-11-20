"""
MusicBrainz collection for the stratified Spotify sample.

For each track in spotify_stratified_sample.csv, search the MusicBrainz
recording endpoint on track name + primary artist and store the raw JSON
response (one file per Spotify track_id).

Features
- Rate limiting: at most 1 request per second (MusicBrainz policy), plus
  any Retry-After the server sends.
- Caching: a track whose response is already on disk is skipped, so the
  run can be stopped and restarted at any time without re-querying.
- Retries: 429 / 5xx / timeouts / connection errors are retried with
  exponential backoff and jitter. Other 4xx errors are logged, not retried.
- Logging: human-readable log in logs/musicbrainz_collect.log and one
  JSON line per track in logs/musicbrainz_manifest.jsonl.
- Raw JSON: data/raw/musicbrainz/recordings/<track_id>.json holds the
  untouched API response plus request metadata (query, URL, time, status).

Usage (from the project folder)
    python musicbrainz_collect.py                    # 60 tracks per genre
    python musicbrainz_collect.py --per-genre 2      # quick test
    python musicbrainz_collect.py --per-genre 0      # whole sample
    MB_CONTACT=you@illinois.edu python musicbrainz_collect.py
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import random
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

API_URL = "https://musicbrainz.org/ws/2/recording"
APP = "IS477-JARC-Project/1.0"
DEFAULT_CONTACT = "sciencescholar14@gmail.com"

ROOT = Path(__file__).resolve().parent
SAMPLE_CSV = ROOT / "spotify_stratified_sample.csv"
RAW_DIR = ROOT / "data" / "raw" / "musicbrainz" / "recordings"
LOG_DIR = ROOT / "logs"
LOG_FILE = LOG_DIR / "musicbrainz_collect.log"
MANIFEST = LOG_DIR / "musicbrainz_manifest.jsonl"

RETRY_STATUS = {429, 500, 502, 503, 504}
PHRASE_SPECIAL = re.compile(r'(["\\])')  # only " and \ need escaping inside a quoted phrase

log = logging.getLogger("musicbrainz_collect")


# --------------------------------------------------------------------------- #
# Setup
# --------------------------------------------------------------------------- #
def setup_logging(verbose: bool = True) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log.setLevel(logging.INFO)
    log.handlers.clear()
    fmt = logging.Formatter("%(asctime)s %(levelname)-7s %(message)s")
    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fh.setFormatter(fmt)
    log.addHandler(fh)
    if verbose:
        sh = logging.StreamHandler()
        sh.setFormatter(fmt)
        log.addHandler(sh)


def make_session(contact: str) -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": f"{APP} ( {contact} )",
        "Accept": "application/json",
    })
    return s


# --------------------------------------------------------------------------- #
# Rate limiter
# --------------------------------------------------------------------------- #
class RateLimiter:
    """Guarantees at least `min_interval` seconds between request starts."""

    def __init__(self, min_interval: float = 1.0):
        self.min_interval = min_interval
        self._next_ok = 0.0

    def wait(self) -> None:
        now = time.monotonic()
        if now < self._next_ok:
            time.sleep(self._next_ok - now)
        self._next_ok = time.monotonic() + self.min_interval

    def penalize(self, seconds: float) -> None:
        """Push the next allowed request further out (e.g. Retry-After)."""
        self._next_ok = max(self._next_ok, time.monotonic() + seconds)


# --------------------------------------------------------------------------- #
# Query building
# --------------------------------------------------------------------------- #
def lucene_escape(text: str) -> str:
    return PHRASE_SPECIAL.sub(r"\\\1", str(text).strip())


def primary_artist(artists: str) -> str:
    # The Hugging Face data separates multiple artists with ";"
    return str(artists).split(";")[0].strip()


def build_query(track_name: str, artists: str) -> str:
    return (f'recording:"{lucene_escape(track_name)}" '
            f'AND artist:"{lucene_escape(primary_artist(artists))}"')


# --------------------------------------------------------------------------- #
# HTTP with retries
# --------------------------------------------------------------------------- #
def fetch(session, limiter, params, max_retries=5, backoff=2.0, timeout=30):
    """Return (status_code, json_or_None, attempts, error_message)."""
    last_err = None
    for attempt in range(1, max_retries + 1):
        limiter.wait()
        try:
            r = session.get(API_URL, params=params, timeout=timeout)
        except (requests.Timeout, requests.ConnectionError) as e:
            last_err = f"{type(e).__name__}: {e}"
            status = None
        else:
            status = r.status_code
            if status == 200:
                try:
                    return status, r.json(), attempt, None
                except ValueError as e:
                    return status, None, attempt, f"Invalid JSON: {e}"
            if status not in RETRY_STATUS:
                return status, None, attempt, f"HTTP {status}: {r.text[:200]}"
            last_err = f"HTTP {status}"
            retry_after = r.headers.get("Retry-After")
            if retry_after and retry_after.isdigit():
                limiter.penalize(float(retry_after))

        if attempt < max_retries:
            delay = backoff ** attempt + random.uniform(0, 1)
            log.warning("  attempt %d failed (%s); retrying in %.1fs",
                        attempt, last_err, delay)
            limiter.penalize(delay)
    return status, None, max_retries, f"Gave up after {max_retries} attempts: {last_err}"


# --------------------------------------------------------------------------- #
# Collection
# --------------------------------------------------------------------------- #
def select_tracks(per_genre: int | None, limit: int | None) -> pd.DataFrame:
    df = pd.read_csv(SAMPLE_CSV)
    if per_genre:
        # The sample is already shuffled within genre, so head() is random
        df = df.groupby("track_genre", group_keys=False).head(per_genre)
    if limit:
        df = df.head(limit)
    return df.reset_index(drop=True)


def cache_path(track_id: str) -> Path:
    return RAW_DIR / f"{track_id}.json"


def write_manifest(entry: dict) -> None:
    with open(MANIFEST, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def collect(per_genre: int | None = 60, limit: int | None = None,
            refresh: bool = False, search_limit: int = 5,
            min_interval: float = 1.0, max_retries: int = 5,
            contact: str | None = None, verbose: bool = True) -> dict:
    setup_logging(verbose)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    contact = contact or os.environ.get("MB_CONTACT", DEFAULT_CONTACT)
    session = make_session(contact)
    limiter = RateLimiter(min_interval)

    tracks = select_tracks(per_genre, limit)
    log.info("Start: %d tracks (per_genre=%s, limit=%s, refresh=%s)",
             len(tracks), per_genre, limit, refresh)

    stats = {"total": len(tracks), "cached": 0, "fetched": 0,
             "errors": 0, "with_results": 0}
    t0 = time.monotonic()
    try:
        for i, row in tracks.iterrows():
            tid = row["track_id"]
            path = cache_path(tid)
            if path.exists() and not refresh:
                stats["cached"] += 1
                continue

            query = build_query(row["track_name"], row["artists"])
            params = {"query": query, "fmt": "json", "limit": search_limit}
            started = datetime.now(timezone.utc).isoformat()
            t_req = time.monotonic()
            status, data, attempts, err = fetch(session, limiter, params,
                                                max_retries=max_retries)
            elapsed = round(time.monotonic() - t_req, 2)

            entry = {"track_id": tid, "track_genre": row["track_genre"],
                     "query": query, "status_code": status,
                     "attempts": attempts, "elapsed_s": elapsed,
                     "requested_at": started}

            if data is not None:
                record = {
                    "track_id": tid,
                    "spotify": {"track_name": row["track_name"],
                                "artists": row["artists"],
                                "album_name": row["album_name"],
                                "duration_ms": int(row["duration_ms"]),
                                "track_genre": row["track_genre"]},
                    "request": {"url": API_URL, "params": params,
                                "requested_at": started,
                                "status_code": status, "attempts": attempts},
                    "response": data,          # raw MusicBrainz JSON, untouched
                }
                tmp = path.with_suffix(".json.tmp")
                tmp.write_text(json.dumps(record, ensure_ascii=False, indent=1),
                               encoding="utf-8")
                tmp.replace(path)               # atomic: no half-written files

                recs = data.get("recordings", [])
                entry.update(result="ok", n_results=len(recs),
                             top_score=recs[0].get("score") if recs else None,
                             top_mbid=recs[0].get("id") if recs else None)
                stats["fetched"] += 1
                stats["with_results"] += bool(recs)
                log.info("[%d/%d] %s | %s - %s -> %d result(s)%s",
                         i + 1, len(tracks), row["track_genre"],
                         primary_artist(row["artists"]), row["track_name"],
                         len(recs),
                         f" (top score {recs[0].get('score')})" if recs else "")
            else:
                entry.update(result="error", error=err)
                stats["errors"] += 1
                log.error("[%d/%d] %s FAILED: %s", i + 1, len(tracks), tid, err)

            write_manifest(entry)
    except KeyboardInterrupt:
        log.warning("Interrupted by user; progress so far is cached and the "
                    "run can be resumed.")

    stats["elapsed_min"] = round((time.monotonic() - t0) / 60, 1)
    log.info("Done: %s", stats)
    return stats


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--per-genre", type=int, default=60,
                   help="tracks per genre to query (0 = entire sample)")
    p.add_argument("--limit", type=int, default=None, help="cap on total tracks")
    p.add_argument("--refresh", action="store_true",
                   help="re-query tracks that are already cached")
    p.add_argument("--search-limit", type=int, default=5,
                   help="candidate recordings returned per search")
    p.add_argument("--min-interval", type=float, default=1.0,
                   help="seconds between requests (keep >= 1.0)")
    p.add_argument("--max-retries", type=int, default=5)
    p.add_argument("--contact", default=None,
                   help="contact email for the User-Agent (or set MB_CONTACT)")
    a = p.parse_args()
    collect(per_genre=a.per_genre or None, limit=a.limit, refresh=a.refresh,
            search_limit=a.search_limit, min_interval=max(a.min_interval, 1.0),
            max_retries=a.max_retries, contact=a.contact)


if __name__ == "__main__":
    main()
