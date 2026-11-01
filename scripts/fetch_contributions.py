#!/usr/bin/env python3
"""Scrape public GitHub contribution calendar (no token needed)."""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USER = "varadkokate"
URL = f"https://github.com/users/{USER}/contributions"
OUT = Path(__file__).resolve().parent.parent / "data" / "contributions.json"

LEVEL_MAP = {
    "0": 0,
    "1": 1,
    "2": 2,
    "3": 3,
    "4": 4,
}


def fetch_cells() -> list[dict]:
    resp = requests.get(URL, headers={"Accept": "text/html"})
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    cells = []
    # GitHub uses <td> elements with data-date and data-level
    for td in soup.select("td.ContributionCalendar-day"):
        date_str = td.get("data-date")
        if not date_str:
            continue
        level = td.get("data-level", "0")

        # Try to extract the actual count from the tooltip / aria text
        # GitHub uses various formats like "5 contributions on January 1"
        count = 0
        tool_tip = td.find("tool-tip") or td.find("span", class_="sr-only")
        if tool_tip:
            text = tool_tip.get_text(strip=True)
            m = re.match(r"(\d+)", text)
            if m:
                count = int(m.group(1))
        elif "No contributions" not in (td.get("aria-label", "") or ""):
            m = re.match(r"(\d+)", td.get("aria-label", ""))
            if m:
                count = int(m.group(1))

        cells.append({
            "date": date_str,
            "level": int(level),
            "count": count,
        })

    cells.sort(key=lambda c: c["date"])
    return cells


def compute_stats(cells: list[dict]) -> dict:
    today = datetime.utcnow().strftime("%Y-%m-%d")

    # Current streak
    current_streak = 0
    for c in reversed(cells):
        if c["date"] > today:
            continue
        if c["count"] > 0 or c["level"] > 0:
            current_streak += 1
        else:
            break

    # Longest streak
    longest = 0
    streak = 0
    for c in cells:
        if c["count"] > 0 or c["level"] > 0:
            streak += 1
            longest = max(longest, streak)
        else:
            streak = 0

    # Best day
    best = max(cells, key=lambda c: c["count"]) if cells else {"date": "", "count": 0}

    # Total contributions
    total = sum(c["count"] for c in cells)

    # Monthly totals
    monthly: dict[str, int] = {}
    for c in cells:
        month = c["date"][:7]  # YYYY-MM
        monthly[month] = monthly.get(month, 0) + c["count"]

    return {
        "total": total,
        "current_streak": current_streak,
        "longest_streak": longest,
        "best_day": {"date": best["date"], "count": best["count"]},
        "monthly": monthly,
    }


def main() -> None:
    print(f"[fetch_contributions] fetching {URL} ...")
    cells = fetch_cells()
    stats = compute_stats(cells)

    payload = {
        "user": USER,
        "generated": datetime.utcnow().isoformat() + "Z",
        "cells": cells,
        "stats": stats,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), "utf-8")
    print(f"[fetch_contributions] {len(cells)} days -> {OUT}")
    print(f"  total={stats['total']}  streak={stats['current_streak']}  "
          f"longest={stats['longest_streak']}  best={stats['best_day']}")


if __name__ == "__main__":
    main()
