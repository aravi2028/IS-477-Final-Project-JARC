# IS 477 Course Plan Project:

## Overview

For our project, we want to look at how different features of songs on Spotify relate to their popularity. We are interested in seeing if things like danceability, energy, tempo, and loudness have an impact on how popular a song becomes. Our main goal is to find patterns in these features and see if we can use them to predict how popular a song might be. We also want to see if these patterns are different depending on the type of music.To do this, we will be using data from Spotify, MusicBrainz, and Last.fm. These datasets will give us information about songs, artists, and how popular they are. We will start by collecting the data and cleaning it up so that everything is consistent and easier to work with. We will also have to match songs and artists across the three datasets to combine the information. After that, we plan to use Python to look for relationships between the different audio features and song popularity. We will create graphs and use regression models to help us understand the results. By the end of the project, we hope to get a better idea of which features are connected to a song's popularity and how useful they are for making predictions.

## Team

| Team Member | Responsibility |
| --- | --- |
| Ankith Ravikumar | Licensing review, data integration and analysis |
| Rohan Kare | Data acquisition, storage, linkage, and analysis |
| Kevin Chen | Data cleaning, quality assessment, and workflow automation |
| Jonah Miller | Data cleaning, extraction, and documentation |

## Research Question

How do Spotify audio features predict track popularity?

We want to test the correlation between different track features and its popularity so that we can predict a track’s popularity even before it is released to the public. Beyond simple linear correlation, our analysis aims to evaluate how feature interactions such as the relationship between energy and valence (musical positiveness) or acousticness and loudness influence audience engagement across different musical genres.
Nowadays, streaming platforms like Spotify, Apple Music, Youtube Music, etc, generate vast amounts of listener behavior data. However, predicting which songs audiences will like before release is quite difficult. This analysis will benefit artists when creating music and record labelers when marketing tracks. By identifying features with high correlation with popularity, we can better understand the patterns that drive success in the music industry. This would benefit all stakeholders.

## Datasets

We will use three datasets that each add a different kind of information about the same tracks and artists. 
1. Spotify Tracks Dataset (Hugging Face)
Source: https://huggingface.co/datasets/maharshipandya/spotify-tracks-dataset
Format and access: CSV, downloaded directly from Hugging Face
Description: About 114,000 Spotify tracks across 125 genres, collected and cleaned with Spotify's Web API and Python. Each row is one track with:
Identifiers: “track_id”,” artists”, “album_name”, “track_name”
Outcome: “popularity” (0–100, based on total and recent plays)
Audio features: “danceability”, “energy”, “key”, “loudness”, “mode”, “speechiness”, “acousticness”, “instrumentalness”, “liveness”, “valence”, “tempo, time_signature”
Other fields: “explicit”, “duration_ms”, “track_genre”
Role in project: The base table. It provides the outcome variable (popularity) and the audio-feature predictors.
2. 2. MusicBrainz (API / database)
Source: https://musicbrainz.org/doc/MusicBrainz_API
Format and access: JSON from the public web service (no key required; 1 request per second with an identifying User-Agent). Full database dumps are available if API volume becomes a problem.
Description: An open, community-maintained music encyclopedia covering artists, recordings, releases, and the relationships between them. Fields we plan to collect include the artist MBID, artist type, country or area, begin and end dates, gender (for solo artists, only for aggregate reporting), recording MBID, ISRCs, and first release date. MusicBrainz also stores links to external services, including Spotify URLs, which can be used to confirm matches.
License: Core data is CC0 (public domain). Some supplementary data is CC BY-NC-SA.
Role in project: Adds artist-level context and release dates, and supplies the MBID that serves as a shared identifier across all three sources.
3. Last.fm (API)
Source: https://www.last.fm/api (methods track.getInfo, artist.getInfo, track.getTopTags)
Format and access: JSON via the Last.fm API (free API key required)
Description: Listening data scrobbled by Last.fm users. For each track and artist we will collect the listener count, total play count, top user tags, and the MBID that Last.fm returns when one is available.
License/terms: Last.fm API Terms of Service (non-commercial use with attribution).
Role in project: Gives an independent measure of popularity from a second platform, plus crowd-sourced genre and mood tags.

### How the datasets link

| Link | Shared attribute(s) | Method |
| --- | --- | --- |
| Spotify →MusicBrainz | Artist name + track name; Spotify track URL | Search the MusicBrainz API on normalized artist and track name; confirm with the Spotify URL relationship or duration when available |
| Spotify → Last.fm | Artist name + track name | “track.getInfo” lookup on normalized names (Last.fm also auto-corrects spellings) |
| Last.fm ↔ MusicBrainz | MBID | Last.fm returns MBIDs that join directly to MusicBrainz records |

After matching, each integrated row will carry “track_id” (Spotify), “recording_mbid” / “artist_mbid” (MusicBrainz), and the Last.fm metrics, along with a match-confidence flag.

Because both APIs are rate limited, we will enrich a stratified sample (planned at roughly 50–80 tracks per genre, about 6,000–10,000 tracks in total) instead of all 114,000 rows. Sampling by genre keeps every genre represented.

## Timeline

| # | Task | Description | Course topic(s) | Target date | Owner |
| --- | --- | --- | --- | --- | --- |
| 1 | Project plan | Write ProjectPlan.md, set up the repository and folder structure, create the project-plan release | Data lifecycle | Oct 22 | Entire Team |
| 2 | Ethics and licensing review | Record the license and terms of use for each source; confirm what we can redistribute in the repo (raw API responses may need to be excluded) | Ethical data handling | Oct 28 | Ankith |
| 3 | Acquire Spotify data | Script the download from Hugging Face; save the raw CSV unchanged | Data collection and acquisition | Oct 28 | Rohan |
| 4 | Storage and organization | Set up data/raw, data/interim, data/processed; naming conventions; .gitignore for large or restricted files | Storage and organization | Oct 30 | Rohan |
| 5 | Initial profiling | Check row counts, duplicate “track_ids” (tracks listed under more than one genre), missing values, value ranges | Data quality | Nov 2 | Kevin |
| 6 | Sampling design | Build the stratified sample by genre after deduplication | Data quality, integration | Nov 4 | Kevin |
| 7 | MusicBrainz collection | Rate-limited collection script with caching, retries, and logging; store raw JSON | Extraction and enrichment | Nov 9 | Jonah |
| 8 | Last.fm collection | Same approach as Last.fm; API key kept out of the repo | Extraction and enrichment | Nov 9 | Jonah |
| 9 | Record linkage and integration | Normalize names (case, punctuation, "feat." credits, remaster suffixes); match across sources; assign confidence flags; join on MBID; store the integrated table (e.g., in SQLite) | Data integration | Nov 14 | Ankith |
| 10 | Status report | Update the plan based on feedback; write StatusReport.md; create the status-report release | - | Nov 17 | Rohan |
| 11 | Quality assessment of integrated data | Measure match rates by genre, check false matches on a hand-checked sample, assess missingness in the enriched fields | Data quality | Nov 21 | Kevin |
| 12 | Cleaning | Resolve duplicates, standardize data types and units, handle missing values, harmonize Last.fm tags | Data cleaning | Nov 24 | Jonah |
| 13 | Analysis | Correlations and plots (Q1), regression with and without artist features (Q2), Spotify vs. Last.fm comparison (Q3), genre–tag agreement (Q4) | Analysis and visualization | Dec 3 | Both (Q1–Q2 Ankith Q3–Q4 Rohan) |
| 14 | Workflow automation and provenance | Run the whole pipeline with one command (e.g., Snakemake or a run_all script); capture provenance | Workflow automation and provenance | Dec 5 | Kevin |
| 15 | Reproducibility package | Pin package versions in requirements.txt; write step-by-step instructions to reproduce; archive outputs (e.g., Box or Zenodo) | Reproducibility and transparency | Dec 8 | Jonah |
| 16 | Metadata and documentation | Data dictionary, descriptive metadata (e.g., DataCite or schema.org), README, citations and licenses | Metadata and documentation | Dec 9 | Jonah |
| 17 | Final report and release | Final README/report; create the final-project release | - | Dec 10 | Entire Team |

## Constraints

Before starting our projects, some preliminary constraints and restrictions that we can foresee are:
Data compatibility: All of the different sources we have collected return data in different formats (e.g. csv, JSON, xml, etc…). This will pose potential problems with converting all of the data into formats that are able to be joined together.
Licensing: The only API that has restrictive licensing is Last.fm. The biggest stipulation is that it requires us crediting last.fm in any “derivative works” created with data acquired from their API as stated on their terms of service
Overlap: We have some concerns that there might not be enough artist/album overlap between the three data sources, and we would thus be limited in our subsequent analysis with only the artists that are contained within all three
Timespan: Building off of the coverage constraint, there might be gaps in years in some datasets that are present in others, or the time ranges within each dataset could have significant offset that would also constrain our subsequent analysis

## Gaps

Our current concerns for gaps in knowledge include our ability to properly and effectively clean and process the raw data that we receive after collecting it from the various API sources. We have covered some basic data cleaning (e.g. stripping blank space, standardizing letter cases, correcting/comparing string similarities), but we are unaware of any more advanced techniques that would be required to clean more complicated datasets for heavy use. Additionally, we aren’t yet aware of the requirements as to demonstrate the reproducibility of our methodology and data.
