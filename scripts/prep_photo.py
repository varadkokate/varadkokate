#!/usr/bin/env python3
"""Remove background, boost contrast, composite on white."""

import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from rembg import remove

SRC = Path(__file__).resolve().parent.parent / "source-photo.jpg"
OUT = Path(__file__).resolve().parent.parent / "source-prepped.png"


def main() -> None:
    # 1. Remove background
    raw = Image.open(SRC)
    fg = remove(raw)  # RGBA with transparent bg

    # 2. Convert to OpenCV (BGRA)
    arr = np.array(fg)
    bgra = cv2.cvtColor(arr, cv2.COLOR_RGBA2BGRA)

    # 3. Boost local contrast with CLAHE on the luminance channel
    bgr = bgra[:, :, :3]
    alpha = bgra[:, :, 3]
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
    l, a_ch, b_ch = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    lab = cv2.merge([l, a_ch, b_ch])
    bgr = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

    # 4. Composite onto pure-white background
    white = np.full_like(bgr, 255)
    alpha_f = (alpha / 255.0)[:, :, np.newaxis]
    composited = (bgr * alpha_f + white * (1 - alpha_f)).astype(np.uint8)

    # 5. Save
    cv2.imwrite(str(OUT), composited)
    print(f"[prep_photo] saved -> {OUT}")


if __name__ == "__main__":
    main()
