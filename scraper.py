"""scraper.py: collect Handshake internships and add them to internships.json.

Run it on its own (not through Flask):   python scraper.py

How it works:
1. A browser window opens. YOU log in with your school account (including Duo),
   search for internships, scroll to load more, then press Enter in the terminal.
   Playwright remembers the login in the "browser_profile" folder (no passwords in code).
2. The script reads the page, finds every posting link, and pulls out the details.
3. Postings with no deadline on the list page get their own page opened to find it.
4. New postings are saved into internships.json.
"""
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

try:
    from bs4 import BeautifulSoup  # type: ignore[reportMissingImports]
except ModuleNotFoundError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "beautifulsoup4"])
    from bs4 import BeautifulSoup  # type: ignore[reportMissingImports]

try:
    from playwright.sync_api import sync_playwright  # type: ignore[reportMissingImports]
except ModuleNotFoundError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright"])
    from playwright.sync_api import sync_playwright  # type: ignore[reportMissingImports]

import helpers

HANDSHAKE_URL = "https://app.joinhandshake.com/stu/postings"  # change if your school's path differs
PROFILE_DIR = "browser_profile"
MAX_DETAIL_PAGES = 30   # how many individual posting pages to open for deadlines

# A posting link looks like /jobs/1234567 (or /stu/jobs/1234567)
JOB_LINK = re.compile(r"/jobs/(\d+)")
# Finds text like "Apply by November 30, 2026" or "Deadline: 11/30/2026"
DEADLINE_RE = re.compile(
    r"(?:apply by|deadline)[:\s]+([A-Za-z]+ \d{1,2}, \d{4}|\d{1,2}/\d{1,2}/\d{4})", re.I)


# ---------- simple if/else guessing (later: replace with an AI call) ----------

def guess_season(text):
    text = text.lower()
    if "summer" in text:
        return "Summer"
    elif "fall" in text:
        return "Fall"
    elif "spring" in text:
        return "Spring"
    return "Unknown"


def guess_island(text):
    text = text.lower()
    places = {"Oahu": ["oahu", "honolulu", "kapolei"], "Maui": ["maui"],
              "Big Island": ["big island", "hilo", "kona"], "Kauai": ["kauai"]}
    for island, words in places.items():
        for word in words:
            if word in text:
                return island
    return "Unknown"


def guess_major(text):
    text = text.lower()
    rules = {"MIS": ["information systems", "data", "analyst", "it "],
             "Marketing": ["marketing", "social media"],
             "Finance": ["finance", "financial"],
             "Accounting": ["accounting", "audit", "tax"],
             "Real Estate": ["real estate", "property"],
             "International Business": ["international", "global", "trade"]}
    for major, words in rules.items():
        for word in words:
            if word in text:
                return major
    return "Management"


def to_iso(date_text):
    """Turn 'Nov 30, 2026' (or similar) into '2026-11-30'. Returns None if it can't."""
    for fmt in ["%B %d, %Y", "%b %d, %Y", "%m/%d/%Y"]:
        try:
            return datetime.strptime(date_text.strip(), fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return None


def find_deadline(text):
    match = DEADLINE_RE.search(text)
    if match:
        return to_iso(match.group(1))
    return None


# ---------- Handshake ----------

def parse_handshake(html):
    """Find every posting link on the page and read the details around it."""
    soup = BeautifulSoup(html, "html.parser")
    found = []
    seen = set()

    for link in soup.find_all("a", href=JOB_LINK):
        job_id = JOB_LINK.search(link["href"]).group(1)
        link_lines = link.get_text("\n", strip=True).split("\n")
        title = link_lines[0] if link_lines and link_lines[0] else ""
        if job_id in seen or not title:
            continue
        seen.add(job_id)

        # climb up from the link until we reach the box that holds the whole posting
        card = link
        for _ in range(4):
            if card.parent is None:
                break
            card = card.parent
            if len(card.get_text(" ", strip=True)) > len(title) + 20:
                break

        lines = card.get_text("\n", strip=True).split("\n")
        others = [line for line in lines if line != title]
        company = others[0] if others else "See posting"
        text = card.get_text(" ")

        found.append({
            "title": title,
            "company": company,
            "island": guess_island(text),
            "major": guess_major(text),
            "season": guess_season(text),
            "paid": "unpaid" not in text.lower(),
            "deadline": find_deadline(text),   # may be None; filled in later
            "source": "Handshake",
            "url": urljoin("https://app.joinhandshake.com", link["href"]),
        })
    return found


def scrape_handshake():
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(PROFILE_DIR, headless=False)
        page = context.new_page()
        page.goto(HANDSHAKE_URL)
        input("Log in if asked, search for internships, scroll to load more, then press Enter here... ")

        html = page.content()
        # saved so you can open it and see what the script saw
        Path("handshake_page.html").write_text(html, encoding="utf-8")
        found = parse_handshake(html)
        print(f"Found {len(found)} postings on the list page.")

        # open individual postings that had no deadline on the list page
        missing = [item for item in found if item["deadline"] is None][:MAX_DETAIL_PAGES]
        for item in missing:
            page.goto(item["url"])
            page.wait_for_timeout(1500)   # wait a moment, and don't hammer the site
            item["deadline"] = find_deadline(page.inner_text("body"))
        context.close()

    with_deadline = [item for item in found if item["deadline"]]
    print(f"{len(with_deadline)} have a deadline we could read.")
    if not with_deadline:
        print("Nothing usable. Open handshake_page.html and check that postings are in it.")
    return with_deadline


# ---------- LinkedIn and Indeed ----------
# Both sites forbid automated scraping and actively block it, so these stay empty.
# Use the "Search on" links in the app, or add listings to internships.json by hand
# with "source": "LinkedIn" / "Indeed". They show up in the app like any other.

def scrape_linkedin():
    return []


def scrape_indeed():
    return []


# ---------- save ----------

def save_scraped(new_items):
    existing = helpers.load_internships()
    known_urls = {i["url"] for i in existing}
    next_id = max([i["id"] for i in existing], default=0) + 1
    added = 0
    for item in new_items:
        if item["url"] in known_urls:
            continue
        item["id"] = next_id
        next_id += 1
        existing.append(item)
        added += 1
    helpers.save_json(helpers.INTERNSHIPS_FILE, existing)
    print(f"Added {added} new internships.")


if __name__ == "__main__":
    everything = scrape_handshake() + scrape_linkedin() + scrape_indeed()
    save_scraped(everything)