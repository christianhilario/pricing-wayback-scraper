import csv

def write_pricing_csv(all_results, output_path="data/pricing_results.csv"):
    """
    Takes a list of result dicts (from fetch_snapshot_price, one per
    domain/snapshot) and writes them into the CSV structure the task
    doc asks for: domain, pricing page url, snapshot timestamp,
    pricing type, price shown, reason code.

    NOTE: "pricing type" (monthly/annual/trial/etc.) is not actually
    parsed out of the page content yet - that would need more specific
    text parsing around each match, which I haven't built. For now this
    just records the raw matched price string and leaves pricing type
    blank/unspecified, which is a real gap noted in CHALLENGES.md.
    """
    rows = []

    for result in all_results:
        domain = result.get("domain", "")
        url = result.get("wayback_url", result.get("final_url", ""))
        timestamp = result.get("timestamp", "")

        prices = result.get("prices_found") or result.get("price_matches")

        if result.get("error"):
            # could not be crawled - task doc wants this reason code separate
            # from "no subscription found"
            rows.append({
                "domain": domain,
                "pricing_page_url": url,
                "snapshot_timestamp": timestamp,
                "pricing_type": "",
                "price_shown": "",
                "reason_code": "could_not_crawl"
            })
        elif not prices:
            # page loaded fine but no price pattern matched
            rows.append({
                "domain": domain,
                "pricing_page_url": url,
                "snapshot_timestamp": timestamp,
                "pricing_type": "",
                "price_shown": "",
                "reason_code": "no_price_found"
            })
        else:
            # one row per price match found on this page
            for p in prices:
                rows.append({
                    "domain": domain,
                    "pricing_page_url": url,
                    "snapshot_timestamp": timestamp,
                    "pricing_type": "unspecified",  # not parsed yet, see note above
                    "price_shown": p["match"],
                    "reason_code": ""
                })

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "domain", "pricing_page_url", "snapshot_timestamp",
            "pricing_type", "price_shown", "reason_code"
        ])
        writer.writeheader()
        writer.writerows(rows)

    return rows