import requests

def get_wayback_snapshots(url, from_date="20210101", to_date="20260101"):
    cdx_url = "https://web.archive.org/cdx/search/cdx"  # https, not http
    params = {
        "url": url,
        "from": from_date,
        "to": to_date,
        "output": "json",
        "filter": "statuscode:200",  # only snapshots that actually loaded successfully
        "collapse": "timestamp:8",   # collapse to one snapshot per day (first digit-8 = YYYYMMDD)
    }

    response = requests.get(cdx_url, params=params, timeout=60)
    response.raise_for_status()

    data = response.json()
    if not data:
        return []

    headers = data[0]
    rows = data[1:]
    return [dict(zip(headers, row)) for row in rows]