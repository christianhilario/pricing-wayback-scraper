import requests
import re

price_pattern = r"\$\d+(\.\d{2})?"

def fetch_snapshot_price(snapshot, context_chars=60):
    """
    Fetches one archived Wayback snapshot and searches its HTML for a
    price pattern. Also captures surrounding text for each match so we
    can eyeball whether it's a real price or noise (like the JS
    backreference false positive found on the live NYT site).
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
            "timestamp": timestamp,
            "wayback_url": wayback_url,
            "status": response.status_code,
            "prices_found": matches_with_context,
            "num_prices": len(matches_with_context)
        }

    except requests.exceptions.RequestException as e:
        return {
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
    fetching all of them. E.g. n=8 across 1769 snapshots gives you
    roughly one every ~7 months over a 5 year range - enough to see
    price changes over time without fetching everything.
    """
    if len(snapshots) <= n:
        return snapshots
    step = len(snapshots) // n
    return snapshots[::step][:n]