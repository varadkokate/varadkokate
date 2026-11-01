#!/usr/bin/env python3
"""Render contribution heatmap SVG from scraped JSON."""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "contributions.json"
OUT = ROOT / "contrib-heatmap.svg"

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
BG = "#0d1117"
BORDER = "#30363d"
TEXT_COL = "#8b949e"
TITLE_COL = "#c9d1d9"

CELL = 12       # cell size px
GAP = 3         # gap between cells
RADIUS = 2      # rounded corners
PAD_X = 50      # left padding for day labels
PAD_Y = 40      # top padding for month labels
PAD_BOTTOM = 60 # bottom padding for legend + stats
PAD_RIGHT = 20

WEEKS = 53
DAYS = 7

DAY_LABELS = ["Mon", "", "Wed", "", "Fri", "", ""]
MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def load_data() -> dict:
    with open(DATA, "r", encoding="utf-8") as f:
        return json.load(f)


def build_grid(cells: list[dict]) -> list[list[int]]:
    """Organize cells into a 53×7 grid of levels."""
    date_to_level = {c["date"]: c["level"] for c in cells}

    # Find the Sunday that starts the grid (53 weeks back from today)
    today = datetime.utcnow().date()
    # Go to the most recent Saturday, then back 52 weeks to get start Sunday
    days_since_sunday = (today.weekday() + 1) % 7
    end_sunday = today - timedelta(days=days_since_sunday)
    start_sunday = end_sunday - timedelta(weeks=WEEKS - 1)

    grid = []
    for week in range(WEEKS):
        col = []
        for day in range(DAYS):
            d = start_sunday + timedelta(weeks=week, days=day)
            date_str = d.strftime("%Y-%m-%d")
            level = date_to_level.get(date_str, 0)
            col.append(min(level, len(PALETTE) - 1))
        grid.append(col)

    return grid


def get_month_labels(grid_weeks: int) -> list[tuple[int, str]]:
    """Return (week_index, month_name) for month boundaries."""
    today = datetime.utcnow().date()
    days_since_sunday = (today.weekday() + 1) % 7
    end_sunday = today - timedelta(days=days_since_sunday)
    start_sunday = end_sunday - timedelta(weeks=grid_weeks - 1)

    labels = []
    last_month = -1
    for week in range(grid_weeks):
        d = start_sunday + timedelta(weeks=week)
        if d.month != last_month:
            labels.append((week, MONTH_NAMES[d.month - 1]))
            last_month = d.month
    return labels


def render_svg(grid: list[list[int]], stats: dict) -> str:
    w = PAD_X + WEEKS * (CELL + GAP) + PAD_RIGHT
    h = PAD_Y + DAYS * (CELL + GAP) + PAD_BOTTOM

    parts = []
    parts.append(f'<?xml version="1.0" encoding="utf-8"?>')
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">')

    # Embedded CSS for animation
    parts.append('<style>')
    parts.append(f'  .cell {{ opacity: 0; animation: reveal 0.4s ease forwards; }}')
    # Stagger using individual class delays
    for week in range(WEEKS):
        for day in range(DAYS):
            idx = week * DAYS + day
            delay = (week + day) * 0.012  # diagonal
            parts.append(f'  .c{idx} {{ animation-delay: {delay:.3f}s; }}')
    parts.append('  @keyframes reveal {')
    parts.append('    from { opacity: 0; transform: translateY(-4px); }')
    parts.append('    to   { opacity: 1; transform: translateY(0); }')
    parts.append('  }')
    parts.append("  .label { font-family: 'Courier New', monospace; font-size: 10px; fill: " + TEXT_COL + "; }")
    parts.append("  .title { font-family: 'Courier New', monospace; font-size: 12px; fill: " + TITLE_COL + "; font-weight: bold; }")
    parts.append("  .stat  { font-family: 'Courier New', monospace; font-size: 11px; fill: " + TEXT_COL + "; }")
    parts.append('</style>')

    # Background
    parts.append(f'<rect width="100%" height="100%" rx="8" fill="{BG}" stroke="{BORDER}" stroke-width="1" />')

    # Month labels
    month_labels = get_month_labels(WEEKS)
    for week_idx, name in month_labels:
        x = PAD_X + week_idx * (CELL + GAP)
        parts.append(f'<text x="{x}" y="{PAD_Y - 8}" class="label">{name}</text>')

    # Day labels
    for day_idx, label in enumerate(DAY_LABELS):
        if label:
            y = PAD_Y + day_idx * (CELL + GAP) + CELL - 1
            parts.append(f'<text x="{PAD_X - 30}" y="{y}" class="label">{label}</text>')

    # Cells
    for week in range(WEEKS):
        for day in range(DAYS):
            x = PAD_X + week * (CELL + GAP)
            y = PAD_Y + day * (CELL + GAP)
            level = grid[week][day]
            color = PALETTE[level]
            idx = week * DAYS + day
            parts.append(
                f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
                f'rx="{RADIUS}" fill="{color}" class="cell c{idx}" />'
            )

    # Legend
    legend_y = PAD_Y + DAYS * (CELL + GAP) + 16
    legend_x = PAD_X
    parts.append(f'<text x="{legend_x}" y="{legend_y + 10}" class="label">Less</text>')
    for i, color in enumerate(PALETTE):
        bx = legend_x + 35 + i * (CELL + 3)
        parts.append(
            f'<rect x="{bx}" y="{legend_y}" width="{CELL}" height="{CELL}" '
            f'rx="{RADIUS}" fill="{color}" />'
        )
    parts.append(f'<text x="{legend_x + 35 + len(PALETTE) * (CELL + 3) + 5}" y="{legend_y + 10}" class="label">More</text>')

    # Stats footer
    stat_y = legend_y + 28
    total = stats.get("total", 0)
    current = stats.get("current_streak", 0)
    longest = stats.get("longest_streak", 0)
    best = stats.get("best_day", {})
    best_str = f"{best.get('date', '?')} ({best.get('count', 0)})"

    stats_text = (
        f"Total: {total}  │  "
        f"Current Streak: {current}d  │  "
        f"Longest: {longest}d  │  "
        f"Best: {best_str}"
    )
    parts.append(f'<text x="{PAD_X}" y="{stat_y}" class="stat">{stats_text}</text>')

    parts.append('</svg>')
    return '\n'.join(parts)


def main() -> None:
    data = load_data()
    grid = build_grid(data["cells"])
    svg = render_svg(grid, data["stats"])
    OUT.write_text(svg, "utf-8")
    print(f"[render_heatmap_svg] saved -> {OUT}")


if __name__ == "__main__":
    main()
