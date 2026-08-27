import requests
import re

# common paths to check for subscription pages
paths_to_check = ["subscribe", "membership", "join", "pricing"]

# keywords that suggest the redirected page is still subscription related
sub_keywords = ["subscri", "member", "plan"]

# basic price pattern - $ followed by digits, optional cents
price_pattern = r"\$\d+(\.\d{2})?"


def check_domain_paths(domain, paths=paths_to_check):
    results = []
    for path in paths:
        url = f"https://{domain}/{path}"
        try:
            response = requests.get(url, timeout=5)

            if response.status_code == 200:
                if response.url.endswith(f"https://{domain}/{path}"):
                    verdict = "positive"
                elif any(word in response.url for word in sub_keywords):
                    verdict = "likely positive"
                else:
                    verdict = "manual positive"
            elif response.status_code == 404:
                verdict = "clean negative"
            else:
                verdict = "manual negative"

            results.append({
                "domain": domain,
                "path": path,
                "status": response.status_code,
                "final_url": response.url,
                "html": response.text,
                "verdict": verdict
            })

        except requests.exceptions.RequestException as e:
            results.append({
                "domain": domain,
                "path": path,
                "status": None,
                "final_url": None,
                "html": None,
                "verdict": "error",
                "error": str(e)
            })

    return results


def has_price_in_content(html, context_chars=60):
    # now returns the actual matches + surrounding text instead of just True/False,
    # so a hit on a bare homepage (like CNN's /join redirect) can be checked
    # for whether it's a real price or just noise from unrelated page content
    if not html:
        return []

    matches_with_context = []
    for m in re.finditer(price_pattern, html):
        start = max(0, m.start() - context_chars)
        end = min(len(html), m.end() + context_chars)
        matches_with_context.append({
            "match": m.group(),
            "context": html[start:end]
        })
    return matches_with_context


def check_domain_full(domain, paths=paths_to_check):
    results = check_domain_paths(domain, paths)

    for r in results:
        if r["status"] == 200:
            r["price_matches"] = has_price_in_content(r["html"])
        else:
            r["price_matches"] = None
        del r["html"]

    return results