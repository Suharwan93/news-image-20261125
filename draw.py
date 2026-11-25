#!/usr/bin/env python3
"""Render the entry image for the make.fun news-image-20261125 bounty.

Draws a 1024x1024 newspaper front page summarising world news for
Wednesday, 25 November 2026, from the frozen, sourced content in
news.json. This is the build-time tool that produces entry.png; the
entrypoint the grader runs is main.py (standard library only), which
copies entry.png to /output/entry.png.

Deterministic: the same input always produces the exact same PNG.
News content is frozen in news.json (no live fetching, no randomness,
no timestamps in the output), so re-running the program reproduces
the image byte-for-byte.

Usage:
    python3 draw.py [--output entry.png]

Requires: Python 3.13+ and Pillow.
    pip install -r requirements.txt
"""

import argparse
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 1024, 1024
MARGIN = 36

PAPER = (251, 250, 247)      # warm off-white
INK = (17, 17, 17)           # near-black
NAVY = (16, 36, 62)          # masthead / rules
RED = (185, 28, 28)          # section tags
MUTED = (90, 90, 90)         # secondary text
RULE = (180, 180, 175)       # hairlines

TAG_COLORS = {
    "MIDDLE EAST": (185, 28, 28),
    "GAZA": (140, 20, 20),
    "UKRAINE": (30, 64, 175),
    "MARKETS": (21, 101, 52),
    "TECH": (107, 33, 168),
    "PACIFIC": (13, 116, 128),
}

# Candidate font files, in preference order. DejaVu ships with most
# Linux images; Liberation is the fallback.
FONT_CANDIDATES = {
    "serif_bold": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
    ],
    "sans_bold": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ],
    "sans": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ],
}


def load_font(kind, size):
    for path in FONT_CANDIDATES[kind]:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size=size)


def wrap_text(draw, text, font, max_width):
    """Greedy word wrap; returns a list of lines that fit max_width."""
    words = text.split()
    lines, current = [], ""
    for word in words:
        trial = f"{current} {word}".strip()
        if draw.textlength(trial, font=font) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_lines(draw, x, y, lines, font, fill, spacing=1.18):
    """Draw lines top-down; returns the y position below the block."""
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        y += int(font.size * spacing)
    return y


def render(data):
    img = Image.new("RGB", (WIDTH, HEIGHT), PAPER)
    d = ImageDraw.Draw(img)

    masthead_font = load_font("serif_bold", 62)
    date_font = load_font("sans_bold", 21)
    lead_tag_font = load_font("sans_bold", 22)
    lead_head_font = load_font("sans_bold", 44)
    lead_body_font = load_font("sans", 24)
    tag_font = load_font("sans_bold", 18)
    head_font = load_font("sans_bold", 26)
    body_font = load_font("sans", 21)
    ticker_font = load_font("sans_bold", 19)
    source_font = load_font("sans", 15)

    content_w = WIDTH - 2 * MARGIN
    x = MARGIN
    y = 28

    # --- Masthead -----------------------------------------------------
    title = data["title"]
    tw = d.textlength(title, font=masthead_font)
    d.text(((WIDTH - tw) / 2, y), title, font=masthead_font, fill=NAVY)
    y += 78

    dateline = f"{data['date'].upper()}  •  {data['subtitle']}"
    tw = d.textlength(dateline, font=date_font)
    d.text(((WIDTH - tw) / 2, y), dateline, font=date_font, fill=MUTED)
    y += 34

    d.rectangle([x, y, x + content_w, y + 4], fill=NAVY)
    y += 10
    d.rectangle([x, y, x + content_w, y + 1], fill=RULE)
    y += 22

    # --- Lead story ---------------------------------------------------
    lead = data["lead"]
    d.text((x, y), lead["tag"], font=lead_tag_font, fill=RED)
    y += 32
    lines = wrap_text(d, lead["headline"], lead_head_font, content_w)
    y = draw_lines(d, x, y, lines, lead_head_font, INK, spacing=1.08)
    y += 8
    lines = wrap_text(d, lead["summary"], lead_body_font, content_w)
    y = draw_lines(d, x, y, lines, lead_body_font, INK, spacing=1.25)
    y += 18
    d.rectangle([x, y, x + content_w, y + 1], fill=RULE)
    y += 20

    # --- Story grid: 2 columns x 3 rows -------------------------------
    gap = 28
    col_w = (content_w - gap) // 2
    row_h = 170
    for i, story in enumerate(data["stories"]):
        col, row = i % 2, i // 2
        cx = x + col * (col_w + gap)
        cy = y + row * row_h
        color = TAG_COLORS.get(story["tag"], RED)
        d.text((cx, cy), story["tag"], font=tag_font, fill=color)
        cy += 26
        lines = wrap_text(d, story["headline"], head_font, col_w)
        cy = draw_lines(d, cx, cy, lines[:2], head_font, INK, spacing=1.08)
        cy += 4
        lines = wrap_text(d, story["summary"], body_font, col_w)
        draw_lines(d, cx, cy, lines[:3], body_font, (60, 60, 60), spacing=1.22)
        # vertical divider between columns
        if col == 0:
            d.rectangle(
                [x + col_w + gap // 2, y + 4, x + col_w + gap // 2 + 1,
                 y + 3 * row_h - 12],
                fill=RULE,
            )
    y += 3 * row_h + 8

    # --- Ticker strip ---------------------------------------------------
    strip_h = 52
    d.rectangle([0, y, WIDTH, y + strip_h], fill=NAVY)
    ticker = data["ticker"]
    tw = d.textlength(ticker, font=ticker_font)
    if tw > WIDTH - 2 * MARGIN:
        # shrink to fit rather than overflow
        ticker_font = load_font("sans_bold", 17)
        tw = d.textlength(ticker, font=ticker_font)
    d.text(((WIDTH - tw) / 2, y + (strip_h - ticker_font.size) // 2 - 2),
           ticker, font=ticker_font, fill=(255, 255, 255))
    y += strip_h + 14

    # --- Sources footer ---------------------------------------------------
    sources = data["sources"]
    tw = d.textlength(sources, font=source_font)
    d.text(((WIDTH - tw) / 2, y), sources, font=source_font, fill=MUTED)

    return img


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="entry.png")
    parser.add_argument("--news", default="news.json")
    args = parser.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, args.news), encoding="utf-8") as f:
        data = json.load(f)

    img = render(data)

    out_path = args.output
    if not os.path.isabs(out_path):
        out_path = os.path.join(here, out_path)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    img.save(out_path, format="PNG", optimize=True)
    size = os.path.getsize(out_path)
    print(f"Wrote {out_path} ({img.size[0]}x{img.size[1]}, {size} bytes)")
    assert img.size == (WIDTH, HEIGHT), "output must be 1024x1024"
    assert size <= 1024 * 1024, "output must be <= 1 MiB"
    return 0


if __name__ == "__main__":
    sys.exit(main())
