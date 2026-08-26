# Challenges & Notes

## Overview
This is my overall Challenges and Notes document showcasing what obstacles I faced when completing this mock assignment.
It reflects the challenges of trying to automate the paywall detection method for optimizing for time.

## Challenge 1: Traffic-based ranking is skewed by non-publisher domains
When I first sorted the domain list by traffic, the top of the list was dominated by domains like news.google.com, wikipedia subdomains, and yahoo portal subdomains (au.sports.yahoo.com, article.yahoo.co.jp). These had traffic numbers in the billions, way higher than any actual news publisher in the sample.

This matters because the task is about "online news and magazine publishers," and these domains aren't publishers, they're aggregators or platforms. Their traffic reflects the whole platform, not a single publisher's subscription product, so including them just adds noise to the ranking and wastes time checking domains that were never going to have a real subscription page.

I'm resolving this by looking at the domain vs top_domain relationship in the CSV. Rows where domain is a subdomain of a much bigger platform (news.google.com under google.com, au.sports.yahoo.com under yahoo.com) get flagged as likely aggregators before I even check for a subscription page. Standalone publishers generally have domain == top_domain (nytimes.com, wsj.com). This isn't a perfect rule, but it lets me deprioritize the obvious non-publishers instead of manually checking every single one.

## Challenge 2: Status code / URL matching isn't fully reliable
My first approach for automated subscription detection was to check status codes on guessed paths (/subscribe, /membership, /join, /pricing) and treat an exact URL match with no redirect as a confident "yes, this is a real page."

Testing this on finance.naver.com broke that assumption. All four guessed paths returned status 200, with no redirect, landing on the exact URL I requested each time. By my original logic that should mean four confident positives, but it's extremely unlikely a site has four separate real subscription pages sitting at exactly the paths I guessed. What's actually happening is the site returns 200 for basically any path, likely because it's built as a single-page app that serves the same app shell regardless of the URL.

This means status code + exact URL match alone isn't enough to confidently say a page is real. I adjusted my detection to a tiered verdict system instead of a binary yes/no:
- positive — 200, no redirect (still not 100% guaranteed real, but highest confidence)
- likely positive — 200, redirected, but the final URL contains a subscription-related keyword
- manual positive — 200, redirected somewhere that doesn't look subscription related
- clean negative — 404, confident no page exists
- manual negative — any other status code, unclear what it means
- error — request failed entirely (timeout, DNS error, etc.)

Only clean negative and error skip manual review. Everything else gets flagged at different confidence levels rather than trusted outright.

## Challenge 3: JavaScript-rendered pricing is invisible to plain HTTP requests
To go a step further than just checking URLs, I tried a second-layer check: searching the raw HTML of a page for a price pattern (regex for $ followed by digits, e.g. $9.99) to see if I could confirm a real price was present.

I tested this against nytimes.com/subscription, a page I already knew was a real subscribe page. The regex did find a match — but it was "$1" sitting inside the site's bundled JavaScript code, used as a regex backreference, not an actual price at all. There was no real price anywhere in the raw HTML I fetched.

This tells me the actual subscription prices on this page are rendered client-side by JavaScript after the page loads in a browser. requests.get() only pulls the raw HTML/JS source, it doesn't run any JavaScript, so it can't see anything the page renders dynamically. This is a hard limitation, not something I can fix by improving the regex.

I'm handling this by treating the content-check as a best-effort signal, not proof either way. If it finds a price, that's a strong positive signal. If it doesn't find one, that does not mean there's no subscription — it just means this method couldn't detect it, and it should still get routed to manual review instead of being marked as a negative. For the actual price extraction stage (using Wayback Machine snapshots instead of live requests), this issue should matter less, since archive.org's crawler generally captures pages as rendered, which sidesteps this specific problem.

## Assumptions
- My price regex only matches USD-style formatting ($X or $X.XX). I haven't tested or accounted for other currencies (€, £, etc.) yet, even though the domain list is international — this is a narrower first pass, not a final version.
- I'm assuming the four guessed paths (/subscribe, /membership, /join, /pricing) cover most common subscription page URLs, but I know this won't catch every site's actual URL structure (e.g. some might use /subscription or /premium instead).
- For the domain vs top_domain filtering, I'm assuming a subdomain relationship (like news.google.com under google.com) is a reasonable signal that a domain is an aggregator rather than a standalone publisher. This is a heuristic, not a guarantee — there could be legitimate publishers with similar subdomain patterns that I'd need to double check by hand.

## Status / What's left
So far I've built and tested the domain filtering logic and the automated subscription detection function (URL/status-code check + content-based price check), and confirmed both work correctly against known examples (nytimes.com as a positive case, finance.naver.com as a false-positive case I caught and adjusted for).

I have not yet built the Wayback Machine scraper (pulling snapshot lists via the CDX API, selecting the earliest snapshot per day, downloading and parsing prices from archived pages) or run the detection logic across the full domain list. Given the time constraints on this mock assignment, I prioritized getting the detection logic right and documented over rushing through the remaining pipeline steps.

## Note: Python module caching issue
While testing an update to my snapshot fetcher function, I ran into a case where editing and saving the .py file in src/ didn't actually change what ran in my notebook, even after restarting the kernel through the normal restart button. Checking the function's source with `inspect.getsource()` showed the new code, but calling the function still ran the old version with the old parameters. I resolved this by deleting the __pycache__ folder inside src/ (Python's compiled bytecode cache) and doing a full restart - closing the notebook tab completely, not just restarting the kernel - which forced Python to reload the actual updated file instead of a stale cached version.