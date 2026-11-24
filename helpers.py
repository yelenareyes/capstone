"""helpers.py: small functions shared by the Flask app and the scraper."""
import json
from datetime import date, datetime
from pathlib import Path

BASE = Path(__file__).parent
INTERNSHIPS_FILE = BASE / "internships.json"
USERS_FILE = BASE / "users.json"


def load_json(path, default):
    """Read a JSON file. If it doesn't exist yet, return the default."""
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_internships():
    return load_json(INTERNSHIPS_FILE, [])


def deadline_status(days_left):
    """The if/else logic behind the color coding."""
    if days_left < 0:
        return "passed"      # gray
    elif days_left <= 14:
        return "urgent"      # red
    elif days_left <= 45:
        return "upcoming"    # yellow
    else:
        return "later"       # green


def add_status(item):
    """Add days_left, status, and a readable date to one internship."""
    deadline = datetime.strptime(item["deadline"], "%Y-%m-%d").date()
    item["days_left"] = (deadline - date.today()).days
    item["status"] = deadline_status(item["days_left"])
    item["deadline_pretty"] = f"{deadline:%b} {deadline.day}, {deadline.year}"
    return item


def matches(item, filters):
    """True if the internship passes every filter the user picked."""
    for field in ["source", "major", "season", "island", "company"]:
        if filters[field] and item[field] != filters[field]:
            return False
    if filters["paid"] == "yes" and not item["paid"]:
        return False
    if filters["paid"] == "no" and item["paid"]:
        return False
    if filters["hide_passed"] and item["status"] == "passed":
        return False
    return True


def filter_internships(internships, filters):
    results = []
    for item in internships:
        add_status(item)
        if matches(item, filters):
            results.append(item)
    # soonest deadline first, closed ones at the bottom
    results.sort(key=lambda i: (i["days_left"] < 0, i["deadline"]))
    return results
