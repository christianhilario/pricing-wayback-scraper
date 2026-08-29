# pricing-wayback-scraper

Technical assessment for a BU Questrom research assistant position (Digital Marketing Analytics, Prof. Tesary Lin). Goal is to collect historical subscription pricing for online news/magazine publishers using the Wayback Machine, covering Jan 2021 - Jan 2026.

See `CHALLENGES.md` for a full writeup of what I found, what I decided to do differently from the original task doc, and what's still left.

## Status
This is not a finished, full-scale run across all 299 domains, given the time I had for this assessment, I focused on building and testing each stage of the pipeline correctly across a handful of real domains (nytimes.com, edition.cnn.com, finance.naver.com, wsj.com, theguardian.com) rather than rushing partial coverage across everything. Details and reasoning are in `CHALLENGES.md`.

Note: while finishing this up, I ran into persistent rate limiting from the Wayback Machine's CDX API (see `CHALLENGES.md`) that blocked some final re-verification. The core pipeline and findings are solid, if a cell involving `get_wayback_snapshots()` fails with a 429 error when re-run, that's this known, external issue, not a bug in the code.

## What's built so far
- Domain filtering logic to flag likely aggregators/platforms (e.g. news.google.com) vs standalone publishers, using the domain/top_domain columns in the source CSV
- Automated subscription page detection (`src/subscription_checker.py`), checks common paths (/subscribe, /membership, /join, /pricing), classifies results into confidence tiers instead of a simple yes/no, tested against 5 real domains with distinct outcomes (real pricing found, a false positive caught and explained, bot-blocking encountered)
- Wayback CDX client (`src/wayback_client.py`), pulls a list of all available historical snapshots for a given URL
- Wayback snapshot fetcher (`src/wayback_snapshot_fetcher.py`), downloads archived pages and searches them for pricing data, with surrounding text captured so matches can be checked against false positives
- CSV output writer (`src/csv_writer.py`), formats results into the columns the task doc asks for (domain, pricing page URL, snapshot timestamp, pricing type, price shown, reason code)

## What's not built yet
- Running detection across the full domain list
- Parsing pricing type (monthly/annual/trial) out of matched price context — currently recorded as "unspecified"
- Retry/backoff logic for Wayback API rate limiting

## Repo structure
data/ source CSV of domains
notebooks/ exploration + testing (domain_filtering.ipynb)
src/ reusable functions imported into the notebook


## How to run
1. Activate the virtual environment:
venv\Scripts\activate

2. Install dependencies:
pip install pandas requests

3. Open `notebooks/domain_filtering.ipynb` in VS Code (or Jupyter) and run the cells from the top in order.