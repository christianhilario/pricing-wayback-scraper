# pricing-wayback-scraper

Technical assessment for a BU Questrom research assistant position (Digital Marketing Analytics, Prof. Tesary Lin). The goal is to collect historical subscription pricing for online news and magazine publishers using the Wayback Machine, covering Jan 2021 to Jan 2026.

See `CHALLENGES.md` for a full writeup of what I found, what I did differently from the original task doc, and what's still left.

## Status
This is not a finished, full-scale run across all 299 domains. Given the time I had for this assessment, I focused on building and testing each stage of the pipeline correctly across a handful of real domains (nytimes.com, edition.cnn.com, finance.naver.com, wsj.com, theguardian.com) instead of rushing partial coverage across everything. Full reasoning is in `CHALLENGES.md`.

Note: while finishing this up, I ran into repeated problems reaching the Wayback Machine's CDX API, first rate limiting (429 errors), and later a full connection timeout that lasted for hours. I checked whether this was specific to my code by loading web.archive.org directly in a browser, and the site itself failed to load, which confirmed it was a broader outage, not something wrong with my requests. See `CHALLENGES.md` for details. If a cell involving `get_wayback_snapshots()` shows an error when you run it, that's this known issue, not a bug.

## What's built so far
- Domain filtering logic that flags likely aggregators or platforms (e.g. news.google.com) versus standalone publishers, using the domain and top_domain columns in the source CSV
- Automated subscription page detection (`src/subscription_checker.py`), which checks common paths (/subscribe, /membership, /join, /pricing) and classifies results into confidence tiers instead of a simple yes or no. Tested against 5 real domains with distinct outcomes: real pricing found, a false positive caught and explained, and a site that appears to block automated requests
- Wayback CDX client (`src/wayback_client.py`), pulls a list of all available historical snapshots for a given URL
- Wayback snapshot fetcher (`src/wayback_snapshot_fetcher.py`), downloads archived pages and searches them for pricing data, capturing the surrounding text so each match can be checked for false positives
- CSV output writer (`src/csv_writer.py`), formats results into the columns the task doc asks for (domain, pricing page URL, snapshot timestamp, pricing type, price shown, reason code)

## What's not built yet
- Running detection across the full domain list
- Parsing pricing type (monthly, annual, trial) out of the matched price context, currently recorded as "unspecified"
- Retry and backoff logic for handling Wayback API rate limiting and outages

## Repo structure
- `data/` — source CSV of domains
- `notebooks/` — exploration and testing (`domain_filtering.ipynb`)
- `src/` — reusable functions imported into the notebook

## How to run

1. Activate the virtual environment:
venv\Scripts\activate

2. Install dependencies:
pip install pandas requests

3. Open `notebooks/domain_filtering.ipynb` in VS Code (or Jupyter) and run the cells from the top in order.