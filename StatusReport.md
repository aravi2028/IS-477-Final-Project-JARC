# IS 477 Project Status Report

## Summary

We have acquired the Spotify base dataset, profiled it, deduplicated it, and drawn a stratified sample by genre. Multiple members ran rate-limited MusicBrainz collection scripts: one is a general query for tracks after the year 2000, and the other uses the stratified sample. The stratified-sample collection is complete (6,780 tracks, 59% matched with high or medium confidence). Record linkage, integration, and analysis have not started yet.

## Progress on the timeline

| #      | Task                                     | Owner         | Target         | Status                                                                                                                |
| ------ | ---------------------------------------- | ------------- | -------------- | --------------------------------------------------------------------------------------------------------------------- |
| 1      | Project plan                             | Entire team   | Oct 22         | Done                                                                                                                  |
| 2      | Ethics and licensing review              | Ankith        | Oct 28         | _(to be completed by Ankith)_                                                                                       |
| 3      | Acquire Spotify data                     | Rohan         | Oct 28         | Done: `huggingface_spotify.csv` (114,000 rows) in the repo                                                          |
| 4      | Storage and organization                 | Rohan         | Oct 30         | Partly done: `data/raw/` and `data/interim/` exist for MusicBrainz output; other files are still in the repo root |
| 5      | Initial profiling                        | Kevin         | Nov 2          | Done (`prof_samp.ipynb`)                                                                                            |
| 6      | Sampling design                          | Kevin         | Nov 4          | Done (`prof_samp.ipynb`, `spotify_stratified_sample.csv`)                                                         |
| 7      | MusicBrainz collection                   | Kevin & Jonah | Nov 9          | Done for the stratified sample: 6,780 tracks collected and parsed (`data/interim/musicbrainz_recordings.csv`)       |
| 8      | Last.fm collection                       | Jonah         | Nov 9          | In progress: initial queries done (`lastfm.json`)                                                                  |
| 9      | Record linkage and integration           | Ankith        | Nov 14         | Not started                                                                                                           |
| 10     | Status report                            | Rohan         | Nov 17         | This document                                                                                                         |
| 11–17 | Quality assessment through final release | Team          | Nov 21–Dec 10 | Not started                                                                                                           |

## Completed work

### Initial profiling (Task 5)

Profiling of `huggingface_spotify.csv` is in `prof_samp.ipynb`.

- **Rows:** 114,000 rows, 20 columns, 114 genres with exactly 1,000 rows each.
- **Duplicate track IDs:** 89,741 unique `track_id`s.
  - 16,641 IDs appear more than once, adding 24,259 extra rows.
  - 16,299 tracks are listed under more than one genre (up to 9).
  - 450 rows are exact duplicates.
  - Duplicated IDs carry identical audio features; only `popularity` differs, and only for 720 tracks.
- **Missing values:** only 3 cells, all in one row, which has no artist, album, or track name and a duration of 0.
- **Value ranges:**
  - All audio features, popularity, key, mode, and loudness are within their documented ranges.
  - `time_signature` has 1,136 values outside the documented 3–7 range (0 or 1).
  - Also flagged: 157 tracks with tempo 0, 16,020 with popularity 0, and a longest track of 87 minutes.

### Sampling design (Task 6)

**Deduplication (114,000 → 89,740 rows, one row per track):**

1. Dropped exact duplicate rows.
2. Dropped the row with missing names.
3. Kept one row per `track_id`. For tracks in several genres, we kept the row with the highest popularity. The full genre list is kept in `all_genres`.

**Finding:** the `songwriter` genre is identical to `singer-songwriter` (all 1,000 tracks overlap). It has no rows after deduplication, which leaves 113 genres.

**Stratified sample:**

- Up to 500 tracks per genre, random seed 42, for **53,942 tracks**.
- 15 genres have fewer than 500 tracks after deduplication and are fully included. The smallest is reggaeton, with 76.
- Saved as `spotify_stratified_sample.csv`.

### MusicBrainz collection (Task 7)

`musicbrainz_collect.py` queries the MusicBrainz recording search for each sampled track, using track name and primary artist.

- **Rate limiting:** at most 1 request per second, plus any `Retry-After` the server sends.
- **Caching:** one raw JSON file per track in `data/raw/musicbrainz/recordings/`. The run is resumable.
- **Retries:** exponential backoff on 429, 5xx, timeouts, and connection errors.
- **Logging:** `logs/musicbrainz_collect.log` and a per-request manifest, `logs/musicbrainz_manifest.jsonl`.

`musicbrainz_parse.py` combines the raw files into `data/interim/musicbrainz_recordings.csv`. That table has the best candidate per track (recording and artist MBIDs, first release date, ISRCs) and a `match_confidence` flag: high, medium, low, or none.

**Collection size:** 6,780 tracks (60 per genre across 113 genres, consistent with the plan's 50–80). The full run took about 2 h 45 min on November 18, 2026.

**Reliability:** every track has a raw JSON file, and all files are valid.

- MusicBrainz returned temporary errors (mostly 503 "busy") on 603 requests, and the retries recovered them.
- 6 tracks still failed after 5 attempts. Re-running the script fetched only those 6 (already-collected tracks are skipped), so no tracks are missing.

**Results** (`data/interim/musicbrainz_recordings.csv`, one row per track):

| Match confidence                         | Tracks | Share |
| ---------------------------------------- | ------ | ----- |
| High (score 100, length within 5 s)      | 3,851  | 56.8% |
| Medium (score ≥ 90, length within 15 s) | 155    | 2.3%  |
| Low                                      | 232    | 3.4%  |
| None (no candidates)                     | 2,542  | 37.5% |

- **Overall:** 4,006 tracks (59.1%) matched with high or medium confidence, and 62.5% returned at least one candidate.
- **Fields:** among matched tracks, 97% have a first release date and 53% have at least one ISRC.
- **By genre:** match rates vary widely.
  - Lowest: sleep (3%), romance (10%), malay (12%), classical (12%), forro (18%).
  - Highest: industrial (95%), garage (93%), death-metal (93%).
  - Low-match genres need a closer look in the quality assessment (Task 11).

**Repository:** the raw responses (`data/raw/`, about 130 MB) are excluded from git with `.gitignore`. The parsed table, the scripts, and the logs are committed.

## Changes to the plan

- **Sample size:** the stratified sample file contains up to 500 tracks per genre. API enrichment uses the first 60 per genre, to stay within the plan's 50–80 and the MusicBrainz rate limit. The larger sample is kept in case we want to enrich more tracks later.
- **Genre count:** after deduplication we have 113 genres, not 114, because `songwriter` duplicates `singer-songwriter`.
- **MusicBrainz approach:** earlier queries searched the release endpoint by artist and appended results to a single `musicbrainz.json`. That file is not valid JSON and cannot be loaded as one file. Collection now uses the recording search per track, with one raw JSON file per track.

## Next steps

| Task | Owner | Next action |
| --- | --- | --- |
| 8 | Jonah | Finish Last.fm collection on the same stratified sample |
| 9 | Ankith | Normalize names and join on MBID; assign confidence flags; store in SQLite |
| 11 | Kevin | Match rates by genre; hand-check a sample of matches |

## Team contributions

| Team member      | Contributions so far                                                                                                                           |
| ---------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| Ankith Ravikumar | _(to be completed by Ankith)_                                                                                                                |
| Rohan Kare       | _(to be completed by Rohan)_                                                                                                                 |
| Kevin Chen       | Uploaded the Spotify dataset; initial profiling; deduplication and stratified sampling; MusicBrainz collection and parsing scripts             |
| Jonah Miller     | Initial MusicBrainz and Last.fm API queries (`IS477FinalProject.ipynb`, `musicbrainz.json`, `lastfm.json`) _(more details from Jonah)_ |
