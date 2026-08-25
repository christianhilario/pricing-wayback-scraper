import requests
import re

# common paths to check for subscription pages
paths_to_check = ["subscribe", "membership", "join", "pricing"]

# keywords that suggest the redirected page is still subscription related
sub_keywords = ["subscri", "member", "plan"]

# basic price pattern - $ followed by digits, optional cents
# starting simple with USD format, can expand later if needed
price_pattern = r"\$\d+(\.\d{2})?"


def check_domain_paths(domain, paths=paths_to_check):
    # stage 1 - just checking status codes and urls, no page content yet
    results = []
    for path in paths:
        url = f"https://{domain}/{path}"
        try:
            response = requests.get(url, timeout=5)

            if response.status_code == 200:
                if response.url.endswith(f"https://{domain}/{path}"):
                    # exact match, no redirect - probably good but not 100% sure
                    # (found out some sites like Naver return 200 for everything
                    # because of how their site is built, so this isnt guaranteed)
                    verdict = "positive"
                elif any(word in response.url for word in sub_keywords):
                    verdict = "likely positive"
                else:
                    # redirected somewhere that doesnt look subscription related
                    # probably just bounced to homepage
                    verdict = "manual positive"

            elif response.status_code == 404:
                verdict = "clean negative"

            else:
                # some other status code, not sure what it means, flag it
                verdict = "manual negative"

            results.append({
                "domain": domain,
                "path": path,
                "status": response.status_code,
                "final_url": response.url,
                "html": response.text,  # only keeping this for the content check, remove later
                "verdict": verdict
            })

        except requests.exceptions.RequestException as e:
            # request failed completely - this is the "could not be crawled" case
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


def has_price_in_content(html):
    # stage 2 check - looks for a price pattern in the actual page html
    # NOTE: this only sees raw html, not stuff rendered by javascript.
    # tested on nytimes.com/subscription and it did NOT find a real price -
    # the only match was inside some javascript code ($1 used as a regex
    # backreference, not an actual price). so a lot of sites render their
    # prices with js and this check just wont catch that.
    # false = "couldnt find it this way", not "there is no price"
    if not html:
        return False
    return bool(re.search(price_pattern, html))


def check_domain_full(domain, paths=paths_to_check):
    # runs both stages together
    results = check_domain_paths(domain, paths)

    for r in results:
        if r["status"] == 200:
            r["price_found_in_html"] = has_price_in_content(r["html"])
        else:
            r["price_found_in_html"] = None  # nothing to check

        del r["html"]  # dont need to keep the full page html around

    return results