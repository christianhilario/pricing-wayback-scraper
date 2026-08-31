import requests
import re

price_pattern = r"\$\d+(\.\d{2})?"


def fetch_snapshot_price(snapshot, domain, context_chars=60):
    """
    Fetches one archived Wayback snapshot and searches its HTML for a
    price pattern. Also grabs the text around each match so I can check
    whether it's a real price or just noise (like the JS backreference
    issue I found on the live NYT site and again in CNN and later NYT
    snapshots).

    domain is passed in separately since a snapshot on its own only
    has a timestamp and URL, not which domain it came from - without
    this, the domain column in my final CSV output was coming out blank.
    """
    timestamp = snapshot["timestamp"]
    original_url = snapshot["original"]

    wayback_url = f"https://web.archive.org/web/{timestamp}/{original_url}"

    try:
        response = requests.get(wayback_url, timeout=30)
        response.raise_for_status()

        matches_with_context = []
        for m in re.finditer(price_pattern, response.text):
            start = max(0, m.start() - context_chars)
            end = min(len(response.text), m.end() + context_chars)
            matches_with_context.append({
                "match": m.group(),
                "context": response.text[start:end]
            })

        return {
            "domain": domain,
            "timestamp": timestamp,
            "wayback_url": wayback_url,
            "status": response.status_code,
            "prices_found": matches_with_context,
            "num_prices": len(matches_with_context)
        }

    except requests.exceptions.RequestException as e:
        return {
            "domain": domain,
            "timestamp": timestamp,
            "wayback_url": wayback_url,
            "status": None,
            "prices_found": None,
            "num_prices": 0,
            "error": str(e)
        }


def sample_snapshots_across_range(snapshots, n=8):
    """
    Picks n snapshots evenly spread across the full list, instead of
    fetching all of them. For nytimes.com/subscription there were 1,769
    snapshots over 5 years - fetching every one would take hours, so
    this spreads out a smaller sample (e.g. one every ~7 months) to
    still show how pricing changed over time without needing everything.
    """
    if len(snapshots) <= n:
        return snapshots
    step = len(snapshots) // n
    return snapshots[::step][:n]