#!/usr/bin/env python3
"""Hand-author a neofetch-style SVG info card."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "info-card.svg"

LINES = [
    ("Now",        "CS Student · Open-Source Developer"),
    ("Prev",       "Web Dev Intern · Hackathon Winner"),
    ("Stack",      "Python · JavaScript · React · Node.js"),
    ("Tools",      "Git · Docker · VS Code · Linux"),
    ("Highlights", "Full-Stack Projects · ML Enthusiast"),
    ("Learning",   "Cloud · DevOps · System Design"),
    ("Hobbies",    "Coding · Gaming · Open Source"),
]

BG = "#0d1117"
BORDER = "#30363d"
TEXT = "#c9d1d9"
KEY_COL = "#58a6ff"
SEP = "#8b949e"
GREEN = "#3fb950"

W, H = 490, 310
PAD_X, PAD_Y = 20, 20
LINE_H = 26
TITLE_H = 40


def main() -> None:
    lines_svg = []

    # Title bar dots
    dots = ""
    for i, color in enumerate(["#ff5f57", "#febc2e", "#28c840"]):
        cx = PAD_X + 10 + i * 18
        dots += f'<circle cx="{cx}" cy="{PAD_Y + 12}" r="5" fill="{color}" />\n'

    # Username line
    user_y = PAD_Y + TITLE_H + 8
    user_line = (
        f'<text x="{PAD_X}" y="{user_y}" '
        f'font-family="\'Courier New\', monospace" font-size="14" '
        f'fill="{GREEN}" font-weight="bold">'
        f'varadkokate@github</text>'
    )
    sep_y = user_y + 6
    sep_line = (
        f'<text x="{PAD_X}" y="{sep_y + 14}" '
        f'font-family="\'Courier New\', monospace" font-size="14" '
        f'fill="{SEP}">'
        f'{"─" * 30}</text>'
    )

    # Info rows with staggered animation
    base_y = sep_y + 38
    for idx, (key, val) in enumerate(LINES):
        y = base_y + idx * LINE_H
        delay = 0.3 + idx * 0.15
        row = (
            f'<g opacity="0" transform="translate(-20, 0)">\n'
            f'  <text x="{PAD_X}" y="{y}" '
            f'font-family="\'Courier New\', monospace" font-size="13" '
            f'fill="{KEY_COL}">{key}</text>\n'
            f'  <text x="{PAD_X + 100}" y="{y}" '
            f'font-family="\'Courier New\', monospace" font-size="13" '
            f'fill="{TEXT}">{val}</text>\n'
            f'  <animateTransform attributeName="transform" '
            f'type="translate" from="-20 0" to="0 0" '
            f'begin="{delay:.2f}s" dur="0.4s" fill="freeze" />\n'
            f'  <animate attributeName="opacity" '
            f'from="0" to="1" '
            f'begin="{delay:.2f}s" dur="0.4s" fill="freeze" />\n'
            f'</g>'
        )
        lines_svg.append(row)

    svg = f"""<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
  <rect width="100%" height="100%" rx="8" fill="{BG}" stroke="{BORDER}" stroke-width="1" />
  {dots}
  {user_line}
  {sep_line}
  {chr(10).join('  ' + line for line in lines_svg)}
</svg>
"""

    OUT.write_text(svg.strip(), "utf-8")
    print(f"[make_info_card] saved -> {OUT}")


if __name__ == "__main__":
    main()
