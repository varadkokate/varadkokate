#!/usr/bin/env python3
"""Convert prepped portrait to a self-typing ASCII SVG."""
from __future__ import annotations

from pathlib import Path
import xml.etree.ElementTree as ET

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "source-prepped.png"
OUT = ROOT / "avi-ascii.svg"

COLS, ROWS = 100, 53
RAMP = ' .`:-=+*cs#%@'
FILL = "#c9d1d9"
BG = "#0d1117"
FONT_W = 7.2   # px per character
FONT_H = 13    # px per line
PAD = 10


def brightness_char(gray_val: int) -> str:
    idx = int(gray_val / 255 * (len(RAMP) - 1))
    return RAMP[idx]


def image_to_grid(path: Path) -> list[str]:
    img = Image.open(path).convert("L")
    img = img.resize((COLS, ROWS), Image.LANCZOS)
    pixels = img.load()
    rows = []
    for y in range(ROWS):
        row = ""
        for x in range(COLS):
            # Invert so dark pixels map to dense characters
            row += brightness_char(255 - pixels[x, y])
        rows.append(row)
    return rows


def build_svg(grid: list[str]) -> str:
    w = COLS * FONT_W + PAD * 2
    h = ROWS * FONT_H + PAD * 2

    svg = ET.Element("svg", {
        "xmlns": "http://www.w3.org/2000/svg",
        "viewBox": f"0 0 {w} {h}",
        "width": str(int(w)),
        "height": str(int(h)),
    })

    # Background
    ET.SubElement(svg, "rect", {
        "width": "100%", "height": "100%", "fill": BG,
    })

    defs = ET.SubElement(svg, "defs")

    total_dur = 2.5  # seconds for entire animation
    row_dur = total_dur / len(grid)

    for i, row_text in enumerate(grid):
        row_w = COLS * FONT_W
        y = PAD + i * FONT_H + FONT_H * 0.8  # baseline

        # Clip-path for wipe effect
        clip_id = f"clip-r{i}"
        cp = ET.SubElement(defs, "clipPath", {"id": clip_id})
        rect = ET.SubElement(cp, "rect", {
            "x": str(PAD), "y": str(PAD + i * FONT_H),
            "width": "0", "height": str(FONT_H),
        })
        # SMIL animate: wipe width from 0 → row_w
        ET.SubElement(rect, "animate", {
            "attributeName": "width",
            "from": "0",
            "to": str(row_w),
            "begin": f"{i * row_dur:.3f}s",
            "dur": f"{row_dur:.3f}s",
            "fill": "freeze",
        })

        # Text element
        txt = ET.SubElement(svg, "text", {
            "x": str(PAD),
            "y": f"{y:.1f}",
            "font-family": "'Courier New', monospace",
            "font-size": "12",
            "fill": FILL,
            "clip-path": f"url(#{clip_id})",
            "xml:space": "preserve",
        })
        txt.text = row_text


    tree = ET.ElementTree(svg)
    with open(OUT, "wb") as f:
        tree.write(f, xml_declaration=True, encoding="utf-8")

    # Fix xml:space namespace issue
    content = OUT.read_text("utf-8")
    content = content.replace("ns0:", "").replace(":ns0", "")
    content = content.replace('xmlns:ns0="http://www.w3.org/XML/1998/namespace" ', '')
    OUT.write_text(content, "utf-8")
    print(f"[make_ascii_svg] saved -> {OUT}")


def main() -> None:
    if not SRC.exists():
        print(f"[make_ascii_svg] {SRC} not found – run prep_photo.py first")
        return
    grid = image_to_grid(SRC)
    build_svg(grid)


if __name__ == "__main__":
    main()
