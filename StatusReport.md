# IS 477 Project Status Report

## Summary

We have acquired the Spotify base dataset, profiled it, deduplicated it, and drawn a stratified sample by genre. Multiple members ran rate-limited MusicBrainz collection scripts: one is a general query for tracks after the year 2000, and the other uses the stratified sample. The stratified-sample collection is complete (6,780 tracks, 59% matched with high or medium confidence). The record linkage and integration script has been created and tested on sample data; the full-data run and match review are pending. Analysis has not started yet.

## Progress on the timeline

| #      | Task                                     | Owner         | Target         | Status                                                                                                                |
| ------ | ---------------------------------------- | ------------- | -------------- | --------------------------------------------------------------------------------------------------------------------- |
| 1      | Project plan                             | Entire team   | Oct 22         | Done                                                                                                                  |
| 2      | Ethics and licensing review              | Ankith        | Oct 28         | Initial review complete; permission checks and release cleanup pending. See Task 2 below.                                                                                       |
| 3      | Acquire Spotify data                     | Rohan         | Oct 28         | Done: `huggingface_spotify.csv` (114,000 rows) in the repo                                                          |
| 4      | Storage and organization                 | Rohan         | Oct 30         | Partly done: `data/raw/` and `data/interim/` exist for MusicBrainz output; other files are still in the repo root |
| 5      | Initial profiling                        | Kevin         | Nov 2          | Done (`prof_samp.ipynb`)                                                                                            |
| 6      | Sampling design                          | Kevin         | Nov 4          | Done (`prof_samp.ipynb`, `spotify_stratified_sample.csv`)                                                         |
| 7      | MusicBrainz collection                   | Kevin & Jonah | Nov 9          | Done for the stratified sample: 6,780 tracks collected and parsed (`data/interim/musicbrainz_recordings.csv`)       |
| 8      | Last.fm collection                       | Jonah         | Nov 9          | In progress: initial queries done (`lastfm.json`)                                                                  |
| 9      | Record linkage and integration           | Ankith        | Nov 14         | In progress: script created and tested on sample data; full-data run and validation pending. |
| 10     | Status report                            | Rohan         | Nov 17         | This document                                                                                                         |
| 11–17 | Quality assessment through final release | Team          | Nov 21–Dec 10 | Not started                                                                                                           |

## Completed work

### Ethics and licensing review (Task 2) – Ankith

I reviewed the licenses and terms for Spotify’s Hugging Face dataset, MusicBrainz, and Last.fm. I focused on what we can use in our project and what we can share in our public GitHub repository. The review identified several items that still need confirmation; it does not mean that all permissions or repository changes are complete.

**Spotify dataset.** The [Hugging Face dataset page](https://huggingface.co/datasets/maharshipandya/spotify-tracks-dataset) lists 114,000 rows and labels the license as “bsd.” However, that label alone does not establish the uploader’s rights to license all Spotify-derived content or identify all conditions that apply. [Spotify’s Developer Terms](https://developer.spotify.com/terms) and [Developer Policy](https://developer.spotify.com/policy) restrict storage, transfer, analysis, and machine-learning uses of Spotify Content obtained through its platform. Our source is a third-party download, so we still need to clarify its collection history and the rights that apply to our intended use. I recommend asking the instructor about this before treating the data as cleared for analysis or redistribution. Until this is resolved, we should avoid publishing additional raw or row-level copies and review the Spotify files already in the repository. Attribution by itself does not resolve the permission question.

**MusicBrainz.** MusicBrainz separates [core data from supplementary data](https://musicbrainz.org/doc/MusicBrainz_Database). Core data is released under CC0. Its published list includes recording MBIDs, titles, artist credits, duration, ISRCs, artist metadata, and release dates. Supplementary data, such as annotations, tags, ratings, and search indexes, uses CC BY-NC-SA 3.0, which requires credit, noncommercial use, and sharing adaptations under the same license. We should record which fields we keep and avoid treating an entire search response as CC0. The parsed table should also distinguish MusicBrainz metadata from our own matching flags. Keeping raw responses out of GitHub is a useful precaution, but any older JSON files and notebook outputs also need review. See the [MusicBrainz licensing page](https://musicbrainz.org/doc/About/Data_License).

**Last.fm.** The [Last.fm API terms](https://www.last.fm/api/tos) ask researchers and students to contact Last.fm before academic use. They allow certain noncommercial copying and sharing subject to conditions, including attribution, license notices, privacy requirements, and restrictions on sublicensing. They also set a 100 MB usage/storage cap unless written consent is obtained, require caching according to response headers, and prohibit bypassing rate limits. We should confirm our academic use and planned public outputs with Last.fm. Until then, I recommend keeping Last.fm responses and extracts out of the public release, including reviewing `lastfm.json` and `lastfm_orig.json`. Our GitHub code license would not give others new rights to Last.fm data.

**Ethical issues and next steps.** Our results should distinguish Spotify popularity scores from Last.fm listener and play counts because they measure different things. The status report also shows that MusicBrainz matches vary by genre. Analyzing only matched tracks could therefore give a misleading picture of the full sample. We should report missingness and match rates, hand-check uncertain matches, and avoid claiming that a high match score proves two recordings are identical.

Before the final release, we should:

- Document each source, collection date, retained fields, and applicable license or terms.
- Keep API keys and credentials out of scripts, logs, and notebook outputs. If a real key was exposed, revoke or rotate it.
- Review raw data, extracts, and notebook outputs already tracked in Git. Adding a path to `.gitignore` does not remove existing tracked files or history.
- Respect API limits and avoid collecting individual listening histories or other unnecessary personal data.
- Publish our scripts, methods, and only those data fields and results cleared for sharing. Summary results also need review; aggregation is not automatic permission.

**Status:** The initial review is complete. Spotify provenance/permissions, Last.fm academic-use confirmation, field-level release decisions, and repository cleanup remain open. These are recommendations and pending checks, not actions already completed.

###Storage and organization

I set up the storage plan for our project so that the folder a file sits in shows its processing stage. Source data goes in data/raw/ exactly as it was downloaded or returned by an API, and those files are never edited. Tables that our scripts make from the raw data, such as parsed, deduplicated or sampled tables, go in data/interim/. The integrated, analysis-ready table from record linkage (Task 9) will go in data/processed/. Any change to a raw file produces a new file in a later stage instead of overwriting the original, so every step can be traced back to its source.

Part of this structure is already in use. The MusicBrainz collection saves one raw JSON response per track in data/raw/musicbrainz/recordings/ (6,780 files, about 130 MB). That folder is excluded from git with .gitignore. The parsed table is committed at data/interim/musicbrainz_recordings.csv, and the collection log and per-request manifest are in logs/. Several files are still in the repository root: huggingface_spotify.csv, spotify_stratified_sample.csv, musicbrainz.json, musicbrainz_orig.json, lastfm.json, lastfm_orig.json, three notebooks, and two scripts. data/processed/ has not been created yet because integration has not started.

The next step is to move the remaining files into this structure. The Spotify CSV goes in data/raw/spotify/ and the stratified sample in data/interim/. Last.fm responses go in data/raw/lastfm/. The older MusicBrainz and Last.fm JSON files go in data/raw/legacy/. Scripts move to scripts/ and notebooks to notebooks/. Files will use lowercase snake_case names that start with the source (spotify_, musicbrainz_, lastfm_), and suffixes like _orig will be dropped because the folder already shows the stage. Raw API caches will keep one file per track, named by Spotify track_id, so collection can resume after an interruption.

The .gitignore will exclude large raw API caches, Last.fm responses, the legacy JSON files, API keys and .env files, and notebook checkpoints. As Task 2 notes, adding a path to .gitignore does not remove files that are already tracked, so the Last.fm and legacy files also need to be untracked with git rm --cached. Whether the Spotify CSVs stay tracked depends on the open permission question from Task 2. After the files move, I will update the file paths in the scripts and notebooks and add a short data/README.md describing each folder.


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

### Task 9: Record Linkage and Integration – Ankith

I worked on the record linkage and integration portion of our project using our Spotify, MusicBrainz, and Last.fm data sources.

For the integration process, I created a Python script that standardizes track and artist names by making capitalization and punctuation consistent and handling featured artists and remastered song titles. This should help reduce mismatches when comparing records across different sources.

For MusicBrainz, I used the existing matching results that include Spotify track IDs, recording MBIDs, artist MBIDs, and confidence scores. Our current MusicBrainz dataset contains 6,780 tracks, with 4,006 having high- or medium-confidence matches. I also included additional name comparisons to identify matches that may need manual review.

For Last.fm, I added matching logic that checks recording MBIDs when available and otherwise compares normalized track and artist names. The script assigns confidence flags so we can distinguish reliable matches from those needing further verification.

The script is designed to combine the information into one integrated dataset containing Spotify audio features and popularity, MusicBrainz metadata, and available Last.fm listener and play counts. It saves the results in CSV and SQLite formats for easier analysis.

**Current status:** The integration script has been created and tested on sample data. We still need to run it on the full project data, verify the Last.fm JSON format, and review uncertain matches. Once those steps are finished, we can use the integrated dataset for our quality assessment and regression analysis.

## Changes to the plan

- **Sample size:** the stratified sample file contains up to 500 tracks per genre. API enrichment uses the first 60 per genre, to stay within the plan's 50–80 and the MusicBrainz rate limit. The larger sample is kept in case we want to enrich more tracks later.
- **Genre count:** after deduplication we have 113 genres, not 114, because `songwriter` duplicates `singer-songwriter`.
- **MusicBrainz approach:** earlier queries searched the release endpoint by artist and appended results to a single `musicbrainz.json`. That file is not valid JSON and cannot be loaded as one file. Collection now uses the recording search per track, with one raw JSON file per track.

## Next steps

| Task | Owner  | Next action                                                                |
| ---- | ------ | -------------------------------------------------------------------------- |
| 8    | Jonah  | Finish Last.fm collection on the same stratified sample                    |
| 9    | Ankith | Run integration on full project data; verify Last.fm JSON format; review uncertain matches |
| 11   | Kevin  | Match rates by genre; hand-check a sample of matches                       |

## Challenges or Problems Faced

| Problem                                                                                   |
| ----------------------------------------------------------------------------------------- |
| Musicbrainz limits queries to 1 second per query, so it took hours to query 6780 tracks   |
| Musicbrainz limits queries per user, so different individuals have to perform the queries |
|                                                                                           |

## Team Contributions

| Team member      | Contributions so far                                                                                                                           |
| ---------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| Ankith Ravikumar | Reviewed source licenses and API terms; documented sharing restrictions, ethical risks, and pending release checks. Created and sample-tested the record linkage and integration script; full-data execution and match validation pending.                                                                                                                |
| Rohan Kare       | _(to be completed by Rohan)_                                                                                                                 |
| Kevin Chen       | Uploaded the Spotify dataset; initial profiling; deduplication and stratified sampling; MusicBrainz collection and parsing scripts             |
| Jonah Miller     | Initial MusicBrainz and Last.fm API queries (`IS477FinalProject.ipynb`, `musicbrainz.json`, `lastfm.json`) _(more details from Jonah)_ |
