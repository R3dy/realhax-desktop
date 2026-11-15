#!/usr/bin/python3 -I
"""Render the realhax fastfetch logo as truecolor ANSI block art.

    tools/gen-logo.py [--preview out.png]

Deterministic authoring-time generator (no fonts, no network). It:
  1. takes LOGO_SVG from tools/install.sh.in (section 5), renders it with
     rsvg-convert and adds a soft blue glow; below it draws the "realhax.io"
     wordmark ("realhax" metallic white, ".io" red) from a built-in bold pixel
     font laid out on the terminal's quadrant grid, so its edges stay crisp;
  2. converts that picture to COLS x ROWS terminal cells. Every cell picks the
     Unicode block element (space, full, halves, quadrants, eighths) plus a
     24-bit fg/bg pair that best reproduces its 8x16 sub-pixels. Only glyphs
     from U+2580..U+259F are used, which alacritty (and most terminals) draw
     themselves, so it is pixel-exact with any font and needs no image protocol;
  3. writes assets/fastfetch-logo.ans and refreshes the base64(gzip) copy that
     is embedded in tools/install.sh.in between the REALHAX-LOGO markers
     (gzip mtime is pinned, so the output is byte-for-byte reproducible).

Needs: /usr/bin/python3 with numpy + PIL (python3-numpy, python3-pil) and
rsvg-convert. Run tools/build.sh afterwards.
"""
import argparse, base64, gzip, io, re, subprocess, sys, textwrap
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "tools" / "install.sh.in"
ANS = ROOT / "assets" / "fastfetch-logo.ans"

COLS, ROWS = 36, 18          # logo size in terminal cells
HEX_TOP, HEX_ROWS = 0.1, 13.4   # hexagon placement (rows)
WORD_TOP = 29                # wordmark top, in quadrant rows (2 per cell row)
CW, CH = 9, 20               # alacritty cell (JetBrains Mono 11.5pt @96dpi), px
K = 4                        # supersampling of the source picture
SX, SY = 8, 16               # sub-pixels per cell used for glyph fitting
BG = (0x0b, 0x0c, 0x10)      # terminal background (palette BG)
RED = (0xff, 0x23, 0x40)
GLOW = (0x6f, 0x9c, 0xff)

# Bold pixel font on the quadrant grid (1 px = half a cell each way): stems are
# 2 px wide, bars 1 px tall; rows 0-1 ascender, 2-6 x-height, baseline below.
FONT = {
    "r": ["......", "......", "XXXXX.", "XX..XX", "XX....", "XX....", "XX...."],
    "e": ["......", "......", ".XXXX.", "XX..XX", "XXXXXX", "XX....", ".XXXXX"],
    "a": ["......", "......", "XXXXX.", "....XX", ".XXXXX", "XX..XX", ".XXXXX"],
    "l": ["XX", "XX", "XX", "XX", "XX", "XX", "XX"],
    "h": ["XX....", "XX....", "XXXXX.", "XX..XX", "XX..XX", "XX..XX", "XX..XX"],
    "x": ["......", "......", "XX..XX", ".XXXX.", "..XX..", ".XXXX.", "XX..XX"],
    ".": ["..", "..", "..", "..", "..", "..", "XX"],
    "i": ["XX", "..", "XX", "XX", "XX", "XX", "XX"],
    "o": ["......", "......", ".XXXX.", "XX..XX", "XX..XX", "XX..XX", ".XXXX."],
}
GAP = 2                      # px between letters
# per cell-row colours (top -> bottom): brushed-metal white, and red for ".io"
METAL = [(0xf6, 0xf8, 0xfc), (0xe6, 0xeb, 0xf3), (0xcf, 0xd8, 0xe6), (0xb4, 0xc0, 0xd4)]
REDS = [(0xff, 0x4a, 0x63), (0xff, 0x2d, 0x4a), (0xf0, 0x1c, 0x3a), (0xd6, 0x14, 0x31)]


def render_svg(svg, size):
    png = subprocess.run(["rsvg-convert", "-w", str(size), "-h", str(size)],
                         input=svg.encode(), capture_output=True, check=True).stdout
    return Image.open(io.BytesIO(png)).convert("RGBA")


def source_image():
    W, H = COLS * CW * K, ROWS * CH * K
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    svg = re.search(r"^LOGO_SVG='(.*)'$", SRC.read_text(encoding="utf-8"), re.M).group(1)

    # hex badge. The hexagon spans 224/256 of the SVG viewBox height.
    hex_h = HEX_ROWS * CH * K
    size = int(round(hex_h * 256 / 224))
    badge = render_svg(svg, size)
    bx, by = (W - size) // 2, int(HEX_TOP * CH * K) - (size - int(hex_h)) // 2
    # glow: blurred, tinted copy of the bright strokes behind the badge
    a = np.asarray(badge, dtype=np.float32)
    lum = a[..., :3].mean(axis=2) / 255.0 * (a[..., 3] / 255.0)
    glow = Image.new("RGBA", badge.size, GLOW + (0,))
    glow.putalpha(Image.fromarray((np.clip(lum * 1.4, 0, 1) * 255).astype(np.uint8)))
    glow = glow.filter(ImageFilter.GaussianBlur(radius=CH * K * 0.35))
    ga = np.asarray(glow).copy(); ga[..., 3] = (ga[..., 3] * 0.55).astype(np.uint8)
    img.alpha_composite(Image.fromarray(ga), (bx, by))
    img.alpha_composite(badge, (bx, by))

    # wordmark, centred on the quadrant grid
    text = "realhax.io"
    width = sum(len(FONT[c][0]) for c in text) + GAP * (len(text) - 1)
    px = np.asarray(img).copy()
    qw, qh = CW * K // 2, CH * K // 2           # one quadrant pixel, in source px
    x = (COLS * 2 - width) // 2
    for i, ch in enumerate(text):
        colours = REDS if i >= text.index(".") else METAL
        for r, line in enumerate(FONT[ch]):
            qy = WORD_TOP + r
            col = colours[min(len(colours) - 1, qy // 2 - WORD_TOP // 2)]
            for c, bit in enumerate(line):
                if bit == "X":
                    px[qy * qh:(qy + 1) * qh, (x + c) * qw:(x + c + 1) * qw] = col + (255,)
        x += len(FONT[ch][0]) + GAP
    return Image.fromarray(px)


# --- glyph fitting ----------------------------------------------------------
def masks():
    """(char, SYxSX bool mask of the 'ink' (fg) part) for every candidate."""
    out = []
    def m(fn):
        g = np.zeros((SY, SX), bool)
        for y in range(SY):
            for x in range(SX):
                g[y, x] = fn(x, y)
        return g
    out.append((" ", m(lambda x, y: False)))
    out.append(("█", m(lambda x, y: True)))
    for i in range(1, 8):  # lower i/8: ▁▂▃▄▅▆▇
        out.append((chr(0x2580 + i), m(lambda x, y, i=i: y >= SY - SY * i // 8)))
    for i in range(1, 8):  # left (8-i)/8: ▉▊▋▌▍▎▏
        out.append((chr(0x2588 + i), m(lambda x, y, i=i: x < SX * (8 - i) // 8)))
    out.append(("▀", m(lambda x, y: y < SY // 2)))
    out.append(("▐", m(lambda x, y: x >= SX // 2)))
    out.append(("▔", m(lambda x, y: y < SY // 8)))
    out.append(("▕", m(lambda x, y: x >= SX - SX // 8)))
    # quadrants: bits UL UR LL LR
    quad = {0b0010: "▖", 0b0001: "▗", 0b1000: "▘", 0b1011: "▙", 0b1001: "▚",
            0b1110: "▛", 0b1101: "▜", 0b0100: "▝", 0b0110: "▞", 0b0111: "▟"}
    for bits, ch in quad.items():
        def f(x, y, bits=bits):
            q = (0 if y < SY // 2 else 2) + (0 if x < SX // 2 else 1)
            return bool(bits & (0b1000 >> q))
        out.append((ch, m(f)))
    return out


def to_cells(img):
    big = Image.new("RGBA", img.size, BG + (255,))
    big.alpha_composite(img)
    small = big.convert("RGB").resize((COLS * SX, ROWS * SY), Image.BOX)
    px = np.asarray(small, dtype=np.float64)
    cand = masks()
    M = np.stack([c[1].ravel() for c in cand]).astype(np.float64)   # (K,128)
    n1 = M.sum(1); n0 = SX * SY - n1
    cells = []
    for r in range(ROWS):
        row = []
        for c in range(COLS):
            P = px[r * SY:(r + 1) * SY, c * SX:(c + 1) * SX].reshape(-1, 3)
            S = P.sum(0); Q = (P ** 2).sum()
            S1 = M @ P; S0 = S - S1
            with np.errstate(divide="ignore", invalid="ignore"):
                e = Q - np.where(n1 > 0, (S1 ** 2).sum(1) / n1, 0) - np.where(n0 > 0, (S0 ** 2).sum(1) / n0, 0)
            # tiny bias toward simpler glyphs so flat areas stay clean
            e = e + np.arange(len(cand)) * 1e-6
            k = int(np.argmin(e))
            fg = tuple(int(round(v)) for v in (S1[k] / n1[k] if n1[k] else BG))
            bg = tuple(int(round(v)) for v in (S0[k] / n0[k] if n0[k] else BG))
            row.append((cand[k][0], fg, bg))
        cells.append(row)
    return cells


INVERSE = {"▀": "▄", "▄": "▀", "▌": "▐", "▐": "▌", "▖": "▜", "▜": "▖", "▗": "▛", "▛": "▗",
           "▘": "▟", "▟": "▘", "▝": "▙", "▙": "▝", "▚": "▞", "▞": "▚", "█": " ", " ": "█"}


def near_bg(c, tol=10):
    return max(abs(a - b) for a, b in zip(c, BG)) <= tol


def to_ansi(cells):
    lines = []
    for row in cells:
        out, cur_fg, cur_bg = [], None, None
        for ch, fg, bg in row:
            if ch == " ":
                fg = None
            elif ch == "█":
                ch, bg, fg = " ", fg, None
            if bg is not None and near_bg(bg):
                bg = None
            if fg is not None and near_bg(fg):
                if ch in INVERSE and bg is not None:
                    ch, fg, bg = INVERSE[ch], bg, None
                else:
                    ch, fg = " ", None
            seq = []
            if ch != " " and fg != cur_fg:
                seq.append("38;2;%d;%d;%d" % fg); cur_fg = fg
            if bg != cur_bg:
                seq.append("49" if bg is None else "48;2;%d;%d;%d" % bg); cur_bg = bg
            if seq:
                out.append("\x1b[" + ";".join(seq) + "m")
            out.append(ch)
        out.append("\x1b[0m")
        lines.append("".join(out).rstrip())
    return "\n".join(lines) + "\n"


def preview(ansi_cells, path):
    """Paint the fitted cells back to pixels (what the terminal will show)."""
    img = Image.new("RGB", (COLS * CW * 2, ROWS * CH * 2), BG)
    cand = dict(masks())
    for r, row in enumerate(ansi_cells):
        for c, (ch, fg, bg) in enumerate(row):
            m = Image.fromarray((cand[ch] * 255).astype(np.uint8)).resize((CW * 2, CH * 2), Image.NEAREST)
            tile = Image.new("RGB", (CW * 2, CH * 2), bg)
            tile.paste(Image.new("RGB", tile.size, fg), (0, 0), m)
            img.paste(tile, (c * CW * 2, r * CH * 2))
    img.save(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    a = ap.parse_args()
    img = source_image()
    cells = to_cells(img)
    if a.preview:
        preview(cells, a.preview)
        img.save(a.preview.replace(".png", "-src.png"))
    ansi = to_ansi(cells)
    ANS.parent.mkdir(exist_ok=True)
    ANS.write_text(ansi, encoding="utf-8")
    blob = base64.b64encode(gzip.compress(ansi.encode(), compresslevel=9, mtime=0)).decode()
    block = "\n".join(textwrap.wrap(blob, 100))
    s = SRC.read_text(encoding="utf-8")
    s, n = re.subn(r"(\nLOGO_ANS_B64='\n)(?:.*?\n)?('\n# <<< REALHAX-LOGO)",
                   lambda m: m.group(1) + block + "\n" + m.group(2), s, flags=re.S)
    if n != 1:
        sys.exit("REALHAX-LOGO markers not found in install.sh.in")
    SRC.write_text(s, encoding="utf-8")
    print(f"{ANS.relative_to(ROOT)}: {COLS}x{ROWS} cells, {len(ansi)} bytes, embedded {len(blob)} b64 chars")


if __name__ == "__main__":
    main()
