# Challenges & Notes

## Overview
This is my overall Challenges and Notes document showcasing what obstacles I faced when completing this mock assignment.
It reflects the challenges of trying to automate the paywall detection method for optimizing for time.

## Challenge 1: Traffic-based ranking is skewed by non-publisher domains
When I first sorted the domain list by traffic, the top of the list was dominated by domains like news.google.com, wikipedia subdomains, and yahoo portal subdomains (au.sports.yahoo.com, article.yahoo.co.jp). These had traffic numbers in the billions, way higher than any actual news publisher in the sample.

This matters because the task is about "online news and magazine publishers," and these domains aren't publishers, they're aggregators or platforms. Their traffic reflects the whole platform, not a single publisher's subscription product, so including them just adds noise to the ranking and wastes time checking domains that were never going to have a real subscription page.

I'm resolving this by looking at the domain vs top_domain relationship in the CSV. Rows where domain is a subdomain of a much bigger platform (news.google.com under google.com, au.sports.yahoo.com under yahoo.com) get flagged as likely aggregators before I even check for a subscription page. Standalone publishers generally have domain == top_domain (nytimes.com, wsj.com). This isn't a perfect rule, but it lets me deprioritize the obvious non-publishers instead of manually checking every single one.

## Challenge 2: Status code / URL matching isn't fully reliable
My first approach for automated subscription detection was to check status codes (the number a website's server sends back saying whether a page was found, like 200 for success or 404 for not found) on guessed paths (/subscribe, /membership, /join, /pricing) and treat an exact URL match with no redirect as a confident "yes, this is a real page."

Testing this on finance.naver.com broke that assumption. All four guessed paths returned status 200, with no redirect, landing on the exact URL I requested each time. By my original logic that should mean four confident positives, but it's extremely unlikely a site has four separate real subscription pages sitting at exactly the paths I guessed. What's actually happening is the site returns 200 for basically any path, likely because it's built as a single-page app that serves the same app shell regardless of the URL.

This means status code + exact URL match alone isn't enough to confidently say a page is real. I adjusted my detection to a tiered verdict system instead of a binary yes/no:
- positive - 200, no redirect (still not 100% guaranteed real, but highest confidence)
- likely positive - 200, redirected, but the final URL contains a subscription-related keyword
- manual positive - 200, redirected somewhere that doesn't look subscription related
- clean negative - 404, confident no page exists
- manual negative - any other status code, unclear what it means
- error - request failed entirely (timeout, DNS error, etc.)

Only clean negative and error skip manual review. Everything else gets flagged at different confidence levels rather than trusted outright.

## Challenge 3: JavaScript-rendered pricing is invisible to plain HTTP requests
To go a step further than just checking URLs, I tried a second-layer check: searching the raw HTML of a page for a price pattern (regex for $ followed by digits, e.g. $9.99) to see if I could confirm a real price was present.

I used regex here instead of just searching for an exact price string, because every site's price is a different number, and I don't know what it is ahead of time. Regex lets me describe the general shape of a price (a dollar sign, followed by digits, optionally followed by a decimal and two more digits) instead of one exact value, so the same pattern can match $9.99 on one site and $14.00 on another.

I tested this against nytimes.com/subscription, a page I already knew was a real subscribe page. The regex did find a match, but it was "$1" sitting inside the site's bundled JavaScript code, used as a regex backreference, not an actual price at all. There was no real price anywhere in the raw HTML I fetched.

## Challenge 4: Archived snapshots sometimes have real pricing data, sometimes hit the same JS problem
Since live sites can hide pricing behind JavaScript, I moved to testing this against actual Wayback Machine snapshots instead. Wayback Machine (archive.org) keeps an index of every snapshot it has ever captured of a webpage, called the CDX API (CDX stands for Capture Index). Querying it lets me get back a list of every available snapshot timestamp for a given URL directly as data, instead of having to open Wayback's calendar page in a browser and read it manually.

Fetching a sample of snapshots spread across that range gave me a mixed result. A snapshot from August 2021 had real, confirmable pricing data sitting directly in the page - a JSON blob with `"productName": "Basic Digital Access $1 week for 52 weeks, then $4.25 week"` and matching HTML price tags. I checked this wasn't a false positive by pulling the text around each match, same way I caught the JS backreference issue earlier, and it clearly was real subscription pricing.

But a snapshot from May 2025 hit the exact same false positive as the live site — a "$1" inside JavaScript code, not an actual price. So it looks like older archived versions of this page had pricing data embedded directly in the HTML/JSON, while newer ones moved to rendering it client-side with JavaScript, same as the current live site. One snapshot also just timed out and returned nothing at all, which is its own "could not be crawled" case.

Takeaway: archived snapshots aren't a guaranteed fix for the JS-rendering problem, they just happen to work for some time periods and not others depending on how the site was built at that point. Every match still needs the same context check before I'd trust it.

## Deviations from Protocol
- The task doc suggests checking for subscription pages manually or via a site's search bar. Instead, I automated this first pass with status code and URL checks, and only route the ambiguous cases to manual review. I did this to make checking a large domain list realistic in the time I had, but it means the automated "clean negative" and "positive" verdicts haven't been manually double checked the way the doc originally describes.
- The task doc asks for every daily snapshot between Jan 2021 and Jan 2026 for each domain. For nytimes.com/subscription alone, that's 1,769 snapshots, and each one takes roughly 15 seconds to fetch and check, so doing this for one domain fully would take hours, let alone 299 domains. Instead I sampled a small number of snapshots spread evenly across the date range, which is enough to see how pricing changed over time without needing to fetch everything. I'm noting this as a deliberate tradeoff given the time I had for this assessment, not something I'd necessarily do for a real production version of this project.

## Assumptions
- My price regex only matches USD-style formatting ($X or $X.XX). I haven't tested or accounted for other currencies (€, £, etc.) yet, even though the domain list is international — this is a narrower first pass, not a final version.
- I'm assuming the four guessed paths (/subscribe, /membership, /join, /pricing) cover most common subscription page URLs, but I know this won't catch every site's actual URL structure (e.g. some might use /subscription or /premium instead).
- For the domain vs top_domain filtering, I'm assuming a subdomain relationship (like news.google.com under google.com) is a reasonable signal that a domain is an aggregator rather than a standalone publisher. This is a heuristic, not a guarantee — there could be legitimate publishers with similar subdomain patterns that I'd need to double check by hand.

## Status / What's left
So far I've built and tested: the domain filtering logic, the automated subscription detection function (URL/status-code check + content-based price check), a Wayback CDX client that pulls historical snapshot lists for a given URL, and a snapshot fetcher that downloads archived pages and checks them for real pricing data with context verification.

I have not yet run any of this across the full 299-domain list, since I focused my time on getting each stage of the pipeline working correctly and documenting real findings on one domain (nytimes.com) rather than rushing partial coverage across all domains. What's left is scaling this up: running the detection logic on the full domain list, and building out the final CSV output with the required columns (domain, pricing page URL, snapshot timestamp, pricing type, price shown, reason code).

## Note: Python module caching issue
While testing an update to my snapshot fetcher function, I ran into a case where editing and saving the .py file in src/ didn't actually change what ran in my notebook, even after restarting the kernel through the normal restart button. Checking the function's source with `inspect.getsource()` showed the new code, but calling the function still ran the old version with the old parameters. I resolved this by deleting the __pycache__ folder inside src/ (a folder Python automatically creates to store a compiled version of code, so it doesn't have to recompile the same file every time — but it can occasionally serve a stale cached version instead of the latest edit) and doing a full restart, closing the notebook tab completely, not just restarting the kernel — which forced Python to reload the actual updated file instead of a stale cached version.