#!/usr/bin/env python3
"""
Carousel Generator — Conrad Palmer | Loan Market Gold Coast
============================================================
Generates Instagram carousel slides (1080×1350px) from a JSON content file.

Usage:
    python carousel_generator.py content.json

Fonts folder must sit alongside this script (auto-created on first run).
Place lm_logo.png in the same folder for the real logo, or it draws a placeholder.
"""

import json, sys, os, urllib.request, textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# ── Brand colours ──────────────────────────────────────────
BG          = (26, 26, 26)
WHITE       = (245, 247, 250)
BLUE        = (77, 163, 255)
WHITE_MUTED = (196, 198, 200)   # ~80% opacity approximation on dark bg

# ── Canvas & layout ────────────────────────────────────────
W, H        = 1080, 1350
ML, MR      = 80, 80            # left/right margin
SAFE_W      = W - ML - MR       # 920px usable width

RULE_X      = 58
RULE_W      = 5
RULE_Y1     = 195
RULE_Y2     = 1220

LOGO_RIGHT_PAD = 40
LOGO_TOP_PAD   = 35
LOGO_SIZE      = 185            # square logo width/height

COUNTER_X   = ML
COUNTER_Y   = H - 70

# ── Font paths ─────────────────────────────────────────────
SCRIPT_DIR  = Path(__file__).parent
FONTS_DIR   = SCRIPT_DIR / "fonts"

FONT_URLS = {
    "body_regular":  "https://github.com/google/fonts/raw/main/ofl/inter/static/Inter_18pt-Regular.ttf",
    "body_medium":   "https://github.com/google/fonts/raw/main/ofl/inter/static/Inter_18pt-Medium.ttf",
    "body_bold":     "https://github.com/google/fonts/raw/main/ofl/inter/static/Inter_18pt-Bold.ttf",
}

# Geomanist Bold — loaded from brand kit if present, fallback to Montserrat
GEOMANIST_PATHS = [
    FONTS_DIR / "geomanist_bold.otf",
    FONTS_DIR / "headline_bold.ttf",   # Montserrat fallback
]

def ensure_fonts():
    FONTS_DIR.mkdir(exist_ok=True)
    for name, url in FONT_URLS.items():
        dest = FONTS_DIR / f"{name}.ttf"
        if not dest.exists():
            print(f"  Downloading font: {name}...")
            urllib.request.urlretrieve(url, dest)

def font(name, size):
    if name == "headline_bold":
        for p in GEOMANIST_PATHS:
            if p.exists():
                return ImageFont.truetype(str(p), size)
        raise FileNotFoundError("No headline font found. Add geomanist_bold.otf to the fonts/ folder.")
    return ImageFont.truetype(str(FONTS_DIR / f"{name}.ttf"), size)

# ── Helpers ────────────────────────────────────────────────
def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def wrap_text(text, fnt, max_width, draw):
    """Wrap text to fit within max_width. Returns list of lines."""
    words = text.split()
    lines, current = [], []
    for word in words:
        test = " ".join(current + [word])
        w = draw.textlength(test, font=fnt)
        if w <= max_width:
            current.append(word)
        else:
            if current:
                lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines

def text_block_height(lines, fnt, line_spacing=1.25):
    """Total pixel height of a text block."""
    if not lines:
        return 0
    bbox = fnt.getbbox("Ag")
    line_h = bbox[3] - bbox[1]
    return int(line_h * line_spacing * len(lines))

def draw_text_block(draw, lines, fnt, x, y, color, line_spacing=1.25):
    """Draw a list of lines and return y after last line."""
    bbox = fnt.getbbox("Ag")
    line_h = int((bbox[3] - bbox[1]) * line_spacing)
    for line in lines:
        draw.text((x, y), line, font=fnt, fill=color)
        y += line_h
    return y

def draw_mixed_headline(draw, text, accent_word, fnt, x, y, max_width, line_spacing=1.2):
    """
    Draw a headline where one specific word/phrase is in BLUE, rest in WHITE.
    Handles multi-line wrapping. Returns y after last line.
    """
    words   = text.split()
    bbox    = fnt.getbbox("Ag")
    line_h  = int((bbox[3] - bbox[1]) * line_spacing)
    accent  = accent_word.strip().rstrip(".,!?").upper() if accent_word else None

    # Build lines with word metadata
    lines_words = []
    current     = []
    for word in words:
        test = " ".join(current + [word])
        if draw.textlength(test, font=fnt) <= max_width:
            current.append(word)
        else:
            if current:
                lines_words.append(current)
            current = [word]
    if current:
        lines_words.append(current)

    for line_words in lines_words:
        cx = x
        for i, word in enumerate(line_words):
            space = " " if i < len(line_words) - 1 else ""
            clean = word.strip(".,!?").upper()
            color = BLUE if (accent and clean == accent) else WHITE
            draw.text((cx, y), word + space, font=fnt, fill=color)
            cx += draw.textlength(word + space, font=fnt)
        y += line_h
    return y

def make_base(slide_num, total):
    """Create base canvas with background, rule, and counter."""
    img  = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    # Vertical rule
    draw.rectangle([RULE_X, RULE_Y1, RULE_X + RULE_W, RULE_Y2], fill=BLUE)
    # Slide counter
    f = font("body_regular", 28)
    draw.text((COUNTER_X, COUNTER_Y), f"{slide_num} / {total}", font=f, fill=WHITE_MUTED)
    return img, draw

def draw_logo(img, draw):
    """Draw LM logo top-right. Uses lm_logo.png if present, otherwise draws placeholder."""
    logo_path = SCRIPT_DIR / "lm_logo.png"
    lx = W - LOGO_SIZE - LOGO_RIGHT_PAD
    ly = LOGO_TOP_PAD

    if logo_path.exists():
        logo = Image.open(logo_path).convert("RGBA")
        logo = logo.resize((LOGO_SIZE, LOGO_SIZE), Image.LANCZOS)
        img.paste(logo, (lx, ly), logo)
    else:
        # Draw placeholder blue square with "Loan Market" text
        draw.rectangle([lx, ly, lx + LOGO_SIZE, ly + LOGO_SIZE], fill=(0, 171, 230))
        lf1 = font("body_bold", 34)
        lf2 = font("body_bold", 30)
        draw.text((lx + 18, ly + 45), "Loan", font=lf1, fill=WHITE)
        draw.text((lx + 12, ly + 88), "Market", font=lf2, fill=WHITE)
        draw.text((lx + LOGO_SIZE - 20, ly + LOGO_SIZE - 28), "™", font=font("body_regular", 18), fill=WHITE)

def draw_warning_triangle(draw, x, y, size=36):
    """Draw a solid warning triangle (⚠ symbol) programmatically."""
    # Equilateral triangle pointing up
    h = int(size * 0.866)  # height = side * sqrt(3)/2
    pts = [
        (x + size // 2, y),           # apex
        (x, y + h),                   # bottom-left
        (x + size, y + h),            # bottom-right
    ]
    draw.polygon(pts, fill=BLUE)
    # "!" inside — tiny white exclamation
    f_ex = font("headline_bold", 18)
    draw.text((x + size // 2 - 4, y + h // 4), "!", font=f_ex, fill=(20, 20, 20))

def draw_date_badge(draw, text, y=330, warn=True):
    """Draw a blue rounded-rect badge. Optionally prepend a drawn warning triangle."""
    f    = font("headline_bold", 34)
    tw   = int(draw.textlength(text, font=f))

    tri_w   = 44 if warn else 0  # space reserved for triangle
    pad     = 20
    bw      = tw + pad * 2 + tri_w
    bh      = 52
    bx      = ML
    by      = y

    draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=26, fill=BLUE)

    if warn:
        draw_warning_triangle(draw, bx + pad - 2, by + 8, size=34)

    draw.text((bx + pad + tri_w, by + 8), text, font=f, fill=(20, 20, 20))

# ── Slide builders ─────────────────────────────────────────

def build_hook(slide, num, total):
    img, draw = make_base(num, total)
    draw_logo(img, draw)

    date_tag = slide.get("date_tag", "")
    if date_tag:
        draw_date_badge(draw, date_tag, y=330, warn=True)

    f_head = font("headline_bold", 82)
    y = 430
    headline = slide.get("headline", "")
    lines = wrap_text(headline, f_head, SAFE_W, draw)
    draw_text_block(draw, lines, f_head, ML, y, WHITE, line_spacing=1.15)
    return img

def build_content(slide, num, total):
    img, draw = make_base(num, total)
    draw_logo(img, draw)

    f_head   = font("headline_bold", 88)
    f_accent = font("headline_bold", 160)
    f_body   = font("body_regular", 52)

    headline     = slide.get("headline", "")
    accent_word  = slide.get("accent_word", "")
    body         = slide.get("body", "")

    # If there's an accent word, strip it from the headline and put it on its own line after
    if accent_word:
        # Remove accent word from headline text for display above
        import re
        head_clean = re.sub(re.escape(accent_word) + r'\.?', '', headline, flags=re.IGNORECASE).strip().rstrip(".,")
        y = 360
        head_lines = wrap_text(head_clean, f_head, SAFE_W, draw)
        y = draw_text_block(draw, head_lines, f_head, ML, y, WHITE, line_spacing=1.15)
        y += 10
        draw.text((ML, y), accent_word.upper() + ".", font=f_accent, fill=BLUE)
        bbox = f_accent.getbbox(accent_word.upper() + ".")
        y += (bbox[3] - bbox[1]) + 45
    else:
        y = 400
        head_lines = wrap_text(headline, f_head, SAFE_W, draw)
        y = draw_text_block(draw, head_lines, f_head, ML, y, WHITE, line_spacing=1.15)
        y += 45

    body_lines = wrap_text(body, f_body, SAFE_W, draw)
    draw_text_block(draw, body_lines, f_body, ML, y, WHITE_MUTED, line_spacing=1.5)
    return img

def build_data_stat(slide, num, total):
    img, draw = make_base(num, total)
    draw_logo(img, draw)

    f_label   = font("body_regular", 44)
    f_number  = font("headline_bold", 180)
    f_support = font("body_medium", 52)

    label   = slide.get("label", "")
    number  = slide.get("big_number", "")
    support = slide.get("supporting_text", "")

    y = 430
    if label:
        draw.text((ML, y), label, font=f_label, fill=WHITE_MUTED)
        y += 65

    draw.text((ML, y), number, font=f_number, fill=BLUE)
    bbox = f_number.getbbox(number)
    y += (bbox[3] - bbox[1]) + 45

    support_lines = wrap_text(support, f_support, SAFE_W, draw)
    draw_text_block(draw, support_lines, f_support, ML, y, WHITE, line_spacing=1.5)
    return img

def build_comparison(slide, num, total):
    img, draw = make_base(num, total)
    draw_logo(img, draw)

    f_label  = font("body_regular", 44)
    f_strike = font("headline_bold", 120)
    f_number = font("headline_bold", 160)
    f_sup    = font("body_regular", 46)

    label     = slide.get("label", "")
    strikethrough_num = slide.get("strikethrough_number", "")
    corrected = slide.get("corrected_number", "")
    support   = slide.get("supporting_text", "")

    y = 420
    if label:
        draw.text((ML, y), label, font=f_label, fill=WHITE_MUTED)
        y += 65

    # Strikethrough number (muted)
    draw.text((ML, y), strikethrough_num, font=f_strike, fill=WHITE_MUTED)
    bbox = f_strike.getbbox(strikethrough_num)
    num_w = int(draw.textlength(strikethrough_num, font=f_strike))
    num_h = bbox[3] - bbox[1]
    mid_y = y + num_h // 2
    draw.line([(ML, mid_y), (ML + num_w, mid_y)], fill=WHITE_MUTED, width=7)
    y += num_h + 15

    # Corrected number (blue, larger)
    draw.text((ML, y), corrected, font=f_number, fill=BLUE)
    bbox2 = f_number.getbbox(corrected)
    y += (bbox2[3] - bbox2[1]) + 50

    sup_lines = wrap_text(support, f_sup, SAFE_W, draw)
    draw_text_block(draw, sup_lines, f_sup, ML, y, WHITE_MUTED, line_spacing=1.5)
    return img

def build_cta(slide, num, total):
    img, draw = make_base(num, total)
    draw_logo(img, draw)

    f_prompt  = font("headline_bold", 46)
    f_keyword = font("headline_bold", 76)
    f_support = font("body_regular", 30)
    f_name    = font("body_bold", 34)
    f_title   = font("body_medium", 26)
    f_stars   = font("body_medium", 24)

    cta_prompt = slide.get("cta_prompt", "Message me")
    keyword    = slide.get("keyword", "")
    support    = slide.get("supporting_text", "")
    name       = slide.get("name", "Conrad Palmer")
    title      = slide.get("title", "Loan Market")
    social     = slide.get("social_proof", "★★★★★  150+ Google Reviews")

    y = 300
    draw.text((ML, y), cta_prompt, font=f_prompt, fill=WHITE)
    y += 65

    draw.text((ML, y), f'"{keyword}"', font=f_keyword, fill=BLUE)
    bbox = f_keyword.getbbox(f'"{keyword}"')
    y += (bbox[3] - bbox[1]) + 30

    sup_lines = wrap_text(support, f_support, SAFE_W, draw)
    y = draw_text_block(draw, sup_lines, f_support, ML, y, WHITE_MUTED, line_spacing=1.5)

    y += 55
    draw.line([(ML, y), (W - MR, y)], fill=(60, 70, 80), width=2)
    y += 35

    draw.text((ML, y), name, font=f_name, fill=WHITE)
    y += 46
    draw.text((ML, y), title, font=f_title, fill=WHITE_MUTED)
    y += 38
    draw.text((ML, y), social, font=f_stars, fill=BLUE)
    return img

# ── Slide type dispatcher ──────────────────────────────────
BUILDERS = {
    "hook":        build_hook,
    "content":     build_content,
    "data_stat":   build_data_stat,
    "comparison":  build_comparison,
    "cta":         build_cta,
}

def generate(config_path):
    config_path = Path(config_path)
    with open(config_path) as f:
        cfg = json.load(f)

    slides      = cfg["slides"]
    total       = len(slides)
    output_dir  = config_path.parent / cfg.get("output_folder", "output_slides")
    output_dir.mkdir(exist_ok=True)

    print(f"\nGenerating {total} slides → {output_dir}\n")
    ensure_fonts()

    for i, slide in enumerate(slides, 1):
        stype   = slide.get("type", "content").lower()
        builder = BUILDERS.get(stype, build_content)
        img     = builder(slide, i, total)
        out     = output_dir / f"slide_{i:02d}.png"
        img.save(out, "PNG")
        print(f"  ✓ Slide {i}: {stype} → {out.name}")

    print(f"\nDone. {total} slides saved to: {output_dir}\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python carousel_generator.py content.json")
        sys.exit(1)
    generate(sys.argv[1])
