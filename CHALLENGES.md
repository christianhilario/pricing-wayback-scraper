# Challenges & Notes

## Overview
This document covers what I ran into while working on this mock assignment, how I dealt with it, and where things stand. Most of the real challenges came from trying to automate paywall detection in a way that's fast but still trustworthy.

## Challenge 1: Traffic-based ranking is skewed by non-publisher domains
When I sorted the domain list by traffic, the top was dominated by domains like news.google.com, wikipedia subdomains, and yahoo portal subdomains (au.sports.yahoo.com, article.yahoo.co.jp). These had traffic in the billions, way higher than any actual news publisher in the list.

That's a problem because the task is about news and magazine publishers, and these aren't publishers, they're aggregators or platforms. Their traffic reflects the whole platform, not one publisher's subscription product, so leaving them in just wastes time checking sites that were never going to have a real subscription page.

I'm handling this by looking at the domain vs top_domain columns. Rows where domain is a subdomain of a much bigger platform (news.google.com under google.com, au.sports.yahoo.com under yahoo.com) get flagged as likely aggregators before I even check for a subscription page. Standalone publishers usually have domain equal to top_domain (nytimes.com, wsj.com). It's not a perfect rule, but it lets me skip the obvious non-publishers instead of manually checking all of them.

## Challenge 2: Status code and URL matching isn't fully reliable
My first idea for automated subscription detection was to check status codes on guessed paths (/subscribe, /membership, /join, /pricing) and treat a 200 with no redirect as a confident "yes, real page."

Testing this on finance.naver.com broke that assumption. All four guessed paths returned 200, no redirect, landing on the exact URL I requested. By my original logic that's four confident positives, but it's very unlikely a site has four separate real subscription pages sitting at exactly those paths. What's actually happening is the site returns 200 for basically any path, probably because it's a single-page app that serves the same shell regardless of URL.

So status code plus exact URL match alone isn't enough. I switched to a tiered verdict system instead of a binary yes or no:
- positive: 200, no redirect (highest confidence, still not guaranteed)
- likely positive: 200, redirected, but the final URL has a subscription-related keyword
- manual positive: 200, redirected somewhere that doesn't look subscription related
- clean negative: 404, confident no page exists
- manual negative: any other status code, unclear what it means
- error: request failed entirely (timeout, DNS error, etc.)

Only clean negative and error skip manual review. Everything else gets a confidence level instead of being trusted outright.

## Challenge 3: JavaScript-rendered pricing is invisible to plain requests
To go further than just checking URLs, I added a second check: searching the raw HTML for a price pattern using regex (dollar sign, digits, optional decimal) to see if I could confirm a real price was on the page.

I used regex instead of an exact match because every site's price is a different number I don't know ahead of time. Regex lets me describe the shape of a price once, so the same pattern matches $9.99 on one site and $14.00 on another.

I tested this on nytimes.com/subscription, a page I already knew was real. The regex did find a match, but it was "$1" sitting inside the site's JavaScript, used as a regex backreference, not a real price. There was no actual price anywhere in the raw HTML I got back.

## Challenge 4: Archived snapshots sometimes have real pricing, sometimes hit the same problem
Since live sites can hide pricing behind JavaScript, I switched to testing this against Wayback Machine snapshots. Wayback keeps an index of every capture it's ever taken of a page, called the CDX API (CDX stands for Capture Index). Querying it gets back a list of every available snapshot timestamp for a URL as data, so I didn't have to open the calendar page and read it by hand.

Pulling a sample of snapshots spread across the date range gave mixed results. A snapshot from August 2021 had real pricing sitting right in the page, a JSON blob with "productName": "Basic Digital Access $1 week for 52 weeks, then $4.25 week" plus matching HTML price tags. I checked this wasn't a false positive by pulling the text around each match, same as with the JS backreference issue, and it was clearly real pricing.

A snapshot from May 2025 hit the same false positive as the live site though, a "$1" inside JavaScript, not a real price. So older archived versions of this page seem to have had pricing embedded directly in the HTML or JSON, while newer ones moved to rendering it with JavaScript, same as the current live site. One snapshot also just timed out with nothing returned, which is its own "could not be crawled" case.

Bottom line: archived snapshots aren't a guaranteed fix for the JS problem. They happen to work for some time periods and not others depending on how the site was built at the time. Every match still needs the context check before I'd trust it.

## Challenge 5: The JS backreference issue and Wayback slowness aren't one-off
I tested the pipeline on CNN as a second real domain, not just NYT. The /subscribe page redirected to /subscription and had real pricing sitting in the raw HTML, things like "$1.99/month," "$69.99," "$29.99," right next to text like "subscription-card-grouped-products__pricing-info-price" and "automatically renews monthly." So unlike NYT's live site, CNN's page does expose pricing without needing JavaScript.

But the same page also had the same kind of false positive as NYT, bare "$1" matches sitting inside the site's JavaScript, used as a regex replacement placeholder (for example e.replace(h,'<a href="$1">$1</a>')). Quick explanation for anyone reading this cold: in regex, when part of a search pattern is wrapped in parentheses, you can "capture" that part and reuse it later, and the capture is written as $1, $2, and so on depending on which group it was. So that code isn't saying "one dollar" at all, it's saying "take whatever the first group captured and reuse it twice." It just happens to look exactly like a price when my regex, which is looking for something totally different, scans over that text.

Since I've now seen this on two unrelated sites, I don't think it's specific to NYT. It's a predictable side effect of any site shipping JavaScript that uses regex capture groups, which is extremely common. My price regex is basically always going to pick up a few of these, so checking the context around each match stays necessary no matter which domain I'm looking at.

I also hit repeated timeouts from Wayback while testing more domains, even after raising my timeout from 15 to 60 seconds. This happened regardless of which domain or query I ran, so I don't think a longer timeout alone fixes it. Wayback's servers just seem inconsistently slow. A full version of this project would need real retry logic (try again a few times with increasing wait times) instead of one request per snapshot.

## Challenge 6: Wayback rate limiting and an outright outage
Later in testing I started getting 429 errors (too many requests) from the CDX API, which lasted for hours, well past what I'd expect from a normal short rate limit window. On the morning I finished this up, a fresh attempt failed with a connection timeout instead. I checked whether this was specific to my code by loading web.archive.org directly in a browser, and the site itself failed to load. That confirmed it wasn't something wrong on my end, Wayback was down or badly degraded at that point for everyone, not just for my requests.

This is a real constraint worth naming on its own: relying on a single external archive service means the pipeline is only as reliable as that service's uptime, and a production version of this would need to handle extended outages gracefully, not just brief slowdowns.

## Deviations from Protocol
- The task doc suggests checking for subscription pages manually or through a site's search bar. I automated this first pass instead with status code and URL checks, only sending the ambiguous cases to manual review. I did this to make checking a large domain list realistic in the time I had, but it means the automated "clean negative" and "positive" verdicts haven't actually been checked by hand the way the doc describes.
- The task doc asks for every daily snapshot from Jan 2021 to Jan 2026 for each domain. For nytimes.com/subscription alone that's 1,769 snapshots, and each one takes roughly 15 seconds to fetch and check, so doing this fully for one domain would take hours, let alone 299 domains. Instead I sampled a small number of snapshots spread evenly across the range, enough to see how pricing changed over time without fetching everything. This is a deliberate tradeoff given the time I had for this assessment, not necessarily what I'd do for a real production version.

## Assumptions
- My price regex only matches USD-style formatting ($X or $X.XX). I haven't handled other currencies (euros, pounds, etc.) yet, even though the domain list is international. This is a narrower first pass, not a final version.
- I'm assuming the four guessed paths (/subscribe, /membership, /join, /pricing) cover most common subscription URLs, but I know this won't catch every site's actual structure (some might use /subscription or /premium instead).
- For the domain vs top_domain filtering, I'm assuming a subdomain relationship is a reasonable signal that a domain is an aggregator rather than a standalone publisher. This is a heuristic, not a guarantee. There could be legitimate publishers with similar subdomain patterns I'd need to double check by hand.

## Status and what's left
I've built and tested: the domain filtering logic, the automated subscription detection function (URL and status code check plus content-based price check), a Wayback CDX client that pulls historical snapshot lists for a given URL, a snapshot fetcher that downloads archived pages and checks them for real pricing with context verification, and a CSV writer that outputs the structure the task doc asks for.

I tested the full pipeline on five real domains: nytimes.com, edition.cnn.com, finance.naver.com, wsj.com, and theguardian.com. Each one surfaced a different, real finding rather than just repeating the same result: Naver's false-positive SPA behavior, NYT's JavaScript rendering limitation, CNN's genuine embedded pricing alongside the same JS noise pattern, WSJ returning 403 (likely blocking automated requests), and the Guardian showing clean promotional pricing with no noise at all.

I haven't run this across the full 299-domain list, since I focused my time on getting each stage of the pipeline right and documenting real findings rather than rushing partial coverage everywhere. What's left is scaling up: running detection on the full domain list, and parsing pricing type (monthly, annual, trial) out of the matched price context instead of leaving it as "unspecified."

## Note on a Python caching issue
While updating my snapshot fetcher function, I ran into a case where editing and saving the file in src/ didn't actually change what ran in my notebook, even after a normal kernel restart. Checking the function's source with inspect.getsource() showed the new code, but calling it still ran the old version with the old parameters. I fixed this by deleting the __pycache__ folder inside src/ (a folder Python creates automatically to store compiled versions of code, which can occasionally serve a stale version instead of the latest edit) and doing a full restart, closing the notebook tab entirely, not just restarting the kernel.