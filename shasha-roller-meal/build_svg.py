#!/usr/bin/env python3
"""Generate a vector (SVG) recreation of the SHASHA Roller Meal 10kg bag.

All text is converted to outlines (paths) so the file is printer-ready and
does not depend on installed fonts. Units are millimetres (viewBox 400 x 550).
Run:  python3 build_svg.py   -> writes shasha_roller_meal_10kg.svg
"""
import math
import os

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.misc.transform import Transform
from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
FD = os.path.join(HERE, "fonts")

# ---------------------------------------------------------------- palette
CYAN = "#1BA6DF"      # top band + logo oval
NAVY = "#2B2670"      # main panel, small print, barcode
RED = "#E5174B"       # SHASHA, 10kg
SKY = "#36B9EC"       # FOOD FOR CHAMPIONS
WHITE = "#FFFFFF"
BAG = "#F5F4EF"       # woven polypropylene white

W, H = 400, 550


# ---------------------------------------------------------------- fonts
class Font:
    def __init__(self, path):
        self.f = TTFont(path)
        self.gs = self.f.getGlyphSet()
        self.cmap = self.f.getBestCmap()
        self.upm = self.f["head"].unitsPerEm
        self.hmtx = self.f["hmtx"]
        os2 = self.f["OS/2"]
        self.cap = getattr(os2, "sCapHeight", 0) or self._bbox_h("H")

    def _bbox_h(self, ch):
        from fontTools.pens.boundsPen import BoundsPen
        bp = BoundsPen(self.gs)
        self.gs[self.cmap[ord(ch)]].draw(bp)
        return bp.bounds[3]

    def gname(self, ch):
        return self.cmap.get(ord(ch), ".notdef")

    def adv(self, ch):
        return self.hmtx[self.gname(ch)][0]

    def width(self, text, tracking=0):
        return sum(self.adv(c) for c in text) + tracking * self.upm * (len(text) - 1)

    def glyph(self, ch, t):
        pen = SVGPathPen(self.gs)
        self.gs[self.gname(ch)].draw(TransformPen(pen, t))
        return pen.getCommands()


ALFA = Font(os.path.join(FD, "AlfaSlabOne-Regular.ttf"))
ARVO = Font(os.path.join(FD, "Arvo-Bold.ttf"))
ARCH = Font(os.path.join(FD, "ArchivoBlack-Regular.ttf"))
ANTON = Font(os.path.join(FD, "Anton-Regular.ttf"))
MONO = Font("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")


def text_d(font, text, x, y, cap, width=None, anchor="middle", tracking=0.0):
    """Path data for `text` with baseline y and cap height `cap` (mm).
    If width is given the text is stretched/condensed horizontally to fit."""
    s = cap / font.cap
    nat = font.width(text, tracking) * s
    sx = (width / nat) if width else 1.0
    tw = nat * sx
    x0 = {"middle": x - tw / 2, "start": x, "end": x - tw}[anchor]
    d, cx = [], 0.0
    for ch in text:
        t = Transform().translate(x0 + cx * s * sx, y).scale(s * sx, -s)
        d.append(font.glyph(ch, t))
        cx += font.adv(ch) + tracking * font.upm
    return " ".join(d)


def arc_text_d(font, text, cx, cy, r, cap, top=True, tracking=0.0):
    """Text on a circle. top=True: along the top of the circle (frown);
    top=False: along the bottom (smile). Baseline radius r."""
    s = cap / font.cap
    total = font.width(text, tracking) * s
    span = total / r
    ang = -span / 2
    d = []
    for ch in text:
        a = font.adv(ch) * s
        mid = ang + (a / 2) / r
        if top:
            px, py, rot = cx + r * math.sin(mid), cy - r * math.cos(mid), mid
        else:
            px, py, rot = cx + r * math.sin(mid), cy + r * math.cos(mid), -mid
        t = Transform().translate(px, py).rotate(rot).translate(-a / 2, 0).scale(s, -s)
        d.append(font.glyph(ch, t))
        ang += (a + tracking * font.upm * s) / r
    return " ".join(d)


def outlined(d, fill, stroke=WHITE, sw=2.0, extra=""):
    """Stroke copy underneath + fill copy on top (works in every editor)."""
    return (f'<path d="{d}" fill="{stroke}" stroke="{stroke}" stroke-width="{sw}" '
            f'stroke-linejoin="round"{extra}/>\n'
            f'<path d="{d}" fill="{fill}"{extra}/>')


# ---------------------------------------------------------------- EAN-13
L = ["0001101", "0011001", "0010011", "0111101", "0100011",
     "0110001", "0101111", "0111011", "0110111", "0001011"]
G = ["0100111", "0110011", "0011011", "0100001", "0011101",
     "0111001", "0000101", "0010001", "0001001", "0010111"]
R = ["1110010", "1100110", "1101100", "1000010", "1011100",
     "1001110", "1010000", "1000100", "1001000", "1110100"]
PARITY = ["LLLLLL", "LLGLGG", "LLGGLG", "LLGGGL", "LGLLGG",
          "LGGLLG", "LGGGLL", "LGLGLG", "LGLGGL", "LGGLGL"]


def ean13(code):
    digits = [int(c) for c in code]
    chk = (10 - (sum(digits[0:12:2]) + 3 * sum(digits[1:12:2])) % 10) % 10
    assert chk == digits[12], f"bad check digit, expected {chk}"
    bits, guard = "101", [True] * 3
    for i, dgt in enumerate(digits[1:7]):
        p = PARITY[digits[0]][i]
        bits += (L if p == "L" else G)[dgt]
        guard += [False] * 7
    bits += "01010"
    guard += [True] * 5
    for dgt in digits[7:]:
        bits += R[dgt]
        guard += [False] * 7
    bits += "101"
    guard += [True] * 3
    return bits, guard


def barcode(x, y):
    code = "6514530027948"
    m = 0.66                    # module width (mm)
    bw, bh = 95 * m + 20 * m, 34
    out = [f'<g id="barcode">',
           f'<rect x="{x}" y="{y}" width="{bw:.2f}" height="{bh}" fill="{WHITE}" '
           f'stroke="{NAVY}" stroke-width="1.1"/>']
    bx, by = x + 12 * m, y + 3.2
    bits, guard = ean13(code)
    i = 0
    while i < len(bits):
        if bits[i] == "1":
            j = i
            while j < len(bits) and bits[j] == "1" and guard[j] == guard[i]:
                j += 1
            hgt = 25.5 if guard[i] else 22.5
            out.append(f'<rect x="{bx + i * m:.3f}" y="{by}" width="{(j - i) * m:.3f}" '
                       f'height="{hgt}" fill="{NAVY}"/>')
            i = j
        else:
            i += 1
    ty = by + 28.6
    dd = [text_d(MONO, code[0], bx - 4.0, ty, 4.2, anchor="middle")]
    for k, c in enumerate(code[1:7]):
        dd.append(text_d(MONO, c, bx + (3 + 7 * k + 3.5) * m, ty, 4.2))
    for k, c in enumerate(code[7:]):
        dd.append(text_d(MONO, c, bx + (50 + 7 * k + 3.5) * m, ty, 4.2))
    out.append(f'<path d="{" ".join(dd)}" fill="{NAVY}"/>')
    out.append("</g>")
    return "\n".join(out)


# ---------------------------------------------------------------- logo
# Central Premium Grain Milling Millers logo, redrawn from the close-up photo.
# Drawn in absolute bag coordinates for an oval centred at (200, 171);
# logo(cx, cy) shifts it anywhere.
DJB = Font("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")


def star(cx, cy, ro, ri, n=5, rot=-90):
    pts = []
    for k in range(n * 2):
        r = ro if k % 2 == 0 else ri
        a = math.radians(rot + k * 180 / n)
        pts.append(f"{cx + r * math.cos(a):.2f},{cy + r * math.sin(a):.2f}")
    return " ".join(pts)


def _spear(x, y, ang_deg):
    """Spear/arrow head on a stack of beads, attached to a frame corner."""
    a = math.radians(ang_deg)
    ux, uy = math.cos(a), math.sin(a)
    px, py = -uy, ux
    out = []
    for d, r in ((1.6, 1.45), (4.1, 1.25), (6.2, 0.95)):
        out.append(f'<circle cx="{x + ux * d:.2f}" cy="{y + uy * d:.2f}" r="{r}" fill="{WHITE}"/>')
    b0, b1, wmax = 7.2, 17.5, 1.9
    bx, by = x + ux * b0, y + uy * b0
    tx, ty = x + ux * b1, y + uy * b1
    m = b0 + (b1 - b0) * 0.42
    mx, my = x + ux * m, y + uy * m
    out.append(
        f'<path d="M{bx:.2f},{by:.2f} '
        f'Q{mx + px * wmax * 2:.2f},{my + py * wmax * 2:.2f} {tx:.2f},{ty:.2f} '
        f'Q{mx - px * wmax * 2:.2f},{my - py * wmax * 2:.2f} {bx:.2f},{by:.2f} Z" fill="{WHITE}"/>')
    # thin rib down the blade (cyan)
    out.append(f'<line x1="{bx + ux * 1.5:.2f}" y1="{by + uy * 1.5:.2f}" x2="{tx - ux * 2:.2f}" '
               f'y2="{ty - uy * 2:.2f}" stroke="{CYAN}" stroke-width="0.35"/>')
    return "".join(out)


def _wheat_ear(bx, by, tx, ty, n=6):
    ang = math.degrees(math.atan2(tx - bx, -(ty - by)))  # rotation from "up"
    L = math.hypot(tx - bx, ty - by)
    g = [f'<g transform="translate({bx} {by}) rotate({ang:.2f})" fill="{WHITE}">']
    for k in range(n):
        yy = -1.2 - k * (L - 2.4) / n
        s = 1.0 - k * 0.06
        for side in (-1, 1):
            g.append(f'<ellipse cx="{side * 1.15 * s:.2f}" cy="{yy:.2f}" rx="{0.85 * s:.2f}" '
                     f'ry="{1.55 * s:.2f}" transform="rotate({side * 30} {side * 1.15 * s:.2f} {yy:.2f})"/>')
    g.append(f'<ellipse cx="0" cy="{-L + 0.6:.2f}" rx="0.7" ry="1.5"/>')
    g.append(f'<line x1="0" y1="0" x2="0" y2="{-L + 1:.2f}" stroke="{WHITE}" stroke-width="0.45"/>')
    g.append('</g>')
    return "".join(g)


def _maize():
    # local coords: base at origin, tip at (0,-26); rotated to lean up-left
    g = [f'<g transform="translate(258 188) rotate(-37) scale(0.82)">']
    # outer husk streaks (left)
    g.append(f'<path d="M-1.2,1 C-10,-4 -13.5,-17 -12.5,-30 C-11,-18 -7.8,-8 0,-0.5 Z" fill="{WHITE}"/>')
    g.append(f'<path d="M-0.6,0.4 C-6.6,-5 -8.6,-15 -7.4,-27 C-5.8,-17 -4.4,-9 0.8,-1.6 Z" fill="{WHITE}"/>')
    # right husk with the notch at the base
    g.append(f'<path d="M0.8,0.6 C7.5,-0.8 9.6,-6 8.4,-12.5 C7.2,-8.5 5.4,-6.6 3.2,-6.2 '
             f'C5.2,-4.6 4.4,-2.4 0.8,-2.2 Z" fill="{WHITE}"/>')
    # stalk stub
    g.append(f'<path d="M-0.9,0 L0.9,0 L1.4,4.5 L-0.6,4.8 Z" fill="{WHITE}"/>')
    # kernels
    for row in range(12):
        yy = -3.2 - row * 1.95
        half = 4.1 * math.sqrt(max(0.0, 1 - ((yy + 13.5) / 13.2) ** 2))
        n = 4 if half > 3.4 else (3 if half > 2.2 else 2)
        for c in range(n):
            xx = -half + 1.0 + c * (2 * half - 2.0) / max(1, n - 1)
            g.append(f'<ellipse cx="{xx:.2f}" cy="{yy:.2f}" rx="0.72" ry="0.82" fill="{WHITE}"/>')
    g.append('</g>')
    return "".join(g)


def _scroll(cx, cy, w, h):
    """Symmetric flourish: centre bead with curling scrolls either side."""
    out = [f'<g fill="none" stroke="{WHITE}" stroke-width="0.5" stroke-linecap="round">']
    for s in (-1, 1):
        out.append(f'<path d="M{cx + s * 1.6:.2f},{cy:.2f} '
                   f'C{cx + s * w * 0.25:.2f},{cy - h * 0.9:.2f} {cx + s * w * 0.4:.2f},{cy + h * 0.9:.2f} '
                   f'{cx + s * w * 0.5:.2f},{cy:.2f}"/>')
        out.append(f'<circle cx="{cx + s * w * 0.5 - s * 0.7:.2f}" cy="{cy - 0.5:.2f}" r="0.6"/>')
    out.append('</g>')
    out.append(f'<ellipse cx="{cx}" cy="{cy}" rx="1.3" ry="1.0" fill="none" stroke="{WHITE}" stroke-width="0.5"/>'
               f'<circle cx="{cx}" cy="{cy}" r="0.45" fill="{WHITE}"/>')
    return "".join(out)


def _crest(cx, cy):
    """Ornament sitting on the frame's top edge: o-(O)-o with end curls."""
    out = [f'<g stroke="{WHITE}" fill="none" stroke-width="0.55" stroke-linecap="round">',
           f'<line x1="{cx - 11}" y1="{cy}" x2="{cx + 11}" y2="{cy}"/>',
           f'<ellipse cx="{cx}" cy="{cy}" rx="1.6" ry="2.1" fill="{CYAN}"/>',
           f'<circle cx="{cx - 4.3}" cy="{cy}" r="1.0" fill="{CYAN}"/>',
           f'<circle cx="{cx + 4.3}" cy="{cy}" r="1.0" fill="{CYAN}"/>',
           f'<path d="M{cx - 11},{cy} q-1.2,-1.6 0.3,-1.9"/>',
           f'<path d="M{cx + 11},{cy} q1.2,-1.6 -0.3,-1.9"/>',
           '</g>',
           f'<circle cx="{cx}" cy="{cy}" r="0.5" fill="{WHITE}"/>']
    return "".join(out)


def logo(cx=200, cy=171, standalone=False):
    out = [f'<g id="central-millers-logo" transform="translate({cx - 200} {cy - 171})">']
    # oval
    out.append(f'<ellipse cx="200" cy="171" rx="80" ry="42" fill="{CYAN}" '
               f'stroke="{WHITE}" stroke-width="2.6"/>')
    # star points emerging left and right of the cartouche
    out.append(f'<path d="M163.5,155.5 L149,169.4 L163.5,171 Z M236.5,155.5 L251,169.4 L236.5,171 Z" fill="{WHITE}"/>')
    # wheat (lower left): two ears, stems crossed
    out.append(f'<g stroke="{WHITE}" stroke-width="0.55" stroke-linecap="round">'
               f'<line x1="141" y1="185.5" x2="157" y2="195.5"/>'
               f'<line x1="154" y1="183.5" x2="150.5" y2="196"/></g>')
    out.append(_wheat_ear(141, 185.5, 132, 171.5, 6))
    out.append(_wheat_ear(154, 183.5, 147.5, 168.5, 6))
    # maize cob (lower right)
    out.append(_maize())
    # spears at the four frame corners
    for (x, y, a) in ((172, 148, -125), (228, 148, -55), (172, 190, 125), (228, 190, 55)):
        out.append(_spear(x, y, a))
    # cartouche frame (barrel sides, notched corners)
    r = 3.5
    frame = (f"M{172 + r},148 L{228 - r},148 A{r},{r} 0 0 0 228,{148 + r} "
             f"C239,156 239,182 228,{190 - r} A{r},{r} 0 0 0 {228 - r},190 "
             f"Q200,197 {172 + r},190 A{r},{r} 0 0 0 172,{190 - r} "
             f"C161,182 161,156 172,{148 + r} A{r},{r} 0 0 0 {172 + r},148 Z")
    out.append(f'<path d="{frame}" fill="{CYAN}" stroke="{WHITE}" stroke-width="1.9" stroke-linejoin="round"/>')
    out.append(_crest(200, 146.6))
    # CENTRAL + flourish
    out.append(f'<path d="{text_d(DJB, "CENTRAL", 200, 155.7, 5.8, width=37, tracking=0.14)}" fill="{WHITE}"/>')
    out.append(_scroll(200, 159.0, 22, 2.2))
    # ribbon: tails, folds, body
    for s in (-1, 1):
        x0 = 200 + s * 34          # inner end of tail (behind body)
        x1 = 200 + s * 40.5          # outer tip of tail
        out.append(f'<path d="M{x0},{165.5} L{x1},{166} L{x1 - s * 2.4},{171.3} L{x1},{177} L{x0},{177} Z" '
                   f'fill="{WHITE}"/>')
        out.append(f'<path d="M{200 + s * 37},{174.3} L{x0},{177} L{x0},{174.3} Z" fill="#BFE6F6"/>')
    out.append(f'<path d="M163,162.8 Q200,159.6 237,162.8 L237,174.6 Q200,171.6 163,174.6 Z" '
               f'fill="{CYAN}" stroke="{WHITE}" stroke-width="1.3" stroke-linejoin="round"/>')
    out.append(f'<path d="{text_d(ARVO, "PREMIUM GRAIN MILLING", 200, 171.4, 7.6, width=66, tracking=0.02)}" '
               f'fill="{WHITE}"/>')
    # MILLERS
    out.append(f'<path d="{text_d(DJB, "MILLERS", 200, 189.0, 10.2, width=43, tracking=0.06)}" fill="{WHITE}"/>')
    out.append('</g>')
    return "\n".join(out)


def standalone_logo():
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="170mm" height="92mm" viewBox="115 125 170 92">'
            '<title>Central Premium Grain Milling Millers - logo (vector)</title>\n'
            + logo() + '\n</svg>')



# ---------------------------------------------------------------- badges & icons
def proudly_zimbabwean(cx, cy, r=13):
    out = ['<g id="proudly-zimbabwean">',
           f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{WHITE}"/>',
           f'<circle cx="{cx}" cy="{cy}" r="{r - 0.9}" fill="none" stroke="{NAVY}" stroke-width="0.5"/>',
           f'<path d="{arc_text_d(ANTON, "ZIMBABWEAN", cx, cy, r - 3.6, 2.4, top=True, tracking=0.12)}" '
           f'fill="{NAVY}" transform="rotate(-62 {cx} {cy})"/>',
           f'<path d="{arc_text_d(ANTON, "PROUDLY", cx, cy, r - 3.6, 2.4, top=True, tracking=0.12)}" '
           f'fill="{NAVY}" transform="rotate(68 {cx} {cy})"/>',
           f'<circle cx="{cx}" cy="{cy - r + 2.2}" r="0.5" fill="{NAVY}"/>',
           f'<circle cx="{cx}" cy="{cy + r - 2.2}" r="0.5" fill="{NAVY}"/>',
           f'<polygon points="{star(cx + 0.5, cy - 0.5, 6.6, 2.8)}" fill="{WHITE}" '
           f'stroke="{NAVY}" stroke-width="0.7" stroke-linejoin="round"/>',
           # stylised bird over the star
           f'<path d="M{cx - 3.6},{cy + 4.2} C{cx - 4.5},{cy + 0.5} {cx - 2.6},{cy - 2.5} {cx - 0.3},{cy - 3.4} '
           f'L{cx + 1.8},{cy - 5.2} L{cx + 1.6},{cy - 3.0} C{cx + 3.4},{cy - 1.5} {cx + 2.6},{cy + 1.8} '
           f'{cx + 0.6},{cy + 3.0} L{cx + 2.4},{cy + 5.4} L{cx - 3.6},{cy + 5.4} Z" fill="{NAVY}"/>',
           '</g>']
    return "\n".join(out)


def recycle_icon(cx, cy, label):
    r = 7.5
    out = [f'<g id="icon-{label.lower().replace(" ", "-")}">',
           f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{NAVY}"/>',
           f'<circle cx="{cx}" cy="{cy}" r="{r - 1}" fill="none" stroke="{WHITE}" stroke-width="0.4"/>']
    if "RECYCLE" in label:
        # two chasing arrows
        out.append(f'<path d="M{cx - 4},{cy + 0.5} A4.2,4.2 0 0 1 {cx + 2.4},{cy - 3.5}" '
                   f'fill="none" stroke="{WHITE}" stroke-width="1.6"/>'
                   f'<polygon points="{cx + 1.6},{cy - 5.6} {cx + 4.6},{cy - 3.2} {cx + 1.2},{cy - 1.4}" fill="{WHITE}"/>'
                   f'<path d="M{cx + 4},{cy - 0.5} A4.2,4.2 0 0 1 {cx - 2.4},{cy + 3.5}" '
                   f'fill="none" stroke="{WHITE}" stroke-width="1.6"/>'
                   f'<polygon points="{cx - 1.6},{cy + 5.6} {cx - 4.6},{cy + 3.2} {cx - 1.2},{cy + 1.4}" fill="{WHITE}"/>')
    else:
        # person dropping litter into a bin
        out.append(f'<circle cx="{cx - 2.2}" cy="{cy - 4}" r="1.2" fill="{WHITE}"/>'
                   f'<path d="M{cx - 2.2},{cy - 2.6} L{cx - 2.6},{cy + 1.6} M{cx - 2.6},{cy + 1.6} L{cx - 4},{cy + 5} '
                   f'M{cx - 2.6},{cy + 1.6} L{cx - 1.2},{cy + 5} M{cx - 2.3},{cy - 1.6} L{cx + 0.8},{cy - 0.6}" '
                   f'stroke="{WHITE}" stroke-width="1.1" stroke-linecap="round" fill="none"/>'
                   f'<path d="M{cx + 0.8},{cy + 0.4} L{cx + 4.4},{cy + 0.4} L{cx + 3.8},{cy + 5} L{cx + 1.4},{cy + 5} Z" '
                   f'fill="{WHITE}"/>'
                   f'<rect x="{cx + 1.9}" y="{cy - 1.6}" width="0.9" height="0.9" fill="{WHITE}"/>')
    out.append(f'<path d="{text_d(ARCH, label, cx, cy + r + 5.2, 2.9)}" fill="{NAVY}"/>')
    out.append("</g>")
    return "\n".join(out)


# ---------------------------------------------------------------- build
def build():
    px0, px1 = 48, 352           # printed panel
    band_top, band_bot, panel_bot = 90, 164, 440
    s = []
    s.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" '
             f'viewBox="0 0 {W} {H}">')
    s.append('<title>SHASHA Roller Meal 10kg - bag artwork (vector)</title>')
    s.append('<defs>'
             '<pattern id="weave" width="2.4" height="2.4" patternUnits="userSpaceOnUse">'
             f'<rect width="2.4" height="2.4" fill="{BAG}"/>'
             '<rect x="0" y="0" width="2.4" height="0.25" fill="#E6E4DC"/>'
             '<rect x="0" y="0" width="0.25" height="2.4" fill="#ECEAE3"/>'
             '</pattern></defs>')

    # bag substrate (woven texture on its own layer - hide for print plates)
    s.append('<g id="bag-substrate">')
    s.append(f'<rect width="{W}" height="{H}" fill="{BAG}"/>')
    s.append(f'<rect width="{W}" height="{H}" fill="url(#weave)" id="woven-texture"/>')
    s.append(f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" fill="none" '
             f'stroke="#D8D5CB" stroke-width="1"/>')
    s.append('</g>')

    # die-cut handle
    s.append(f'<g id="die-cut-handle"><rect x="168" y="38" width="64" height="15" rx="7.5" '
             f'fill="#CFCBBF" stroke="#A9A496" stroke-width="0.6"/></g>')

    # panel
    s.append('<g id="front-panel">')
    s.append(f'<rect x="{px0}" y="{band_top}" width="{px1 - px0}" height="{band_bot - band_top}" fill="{CYAN}"/>')
    s.append(f'<rect x="{px0}" y="{band_bot}" width="{px1 - px0}" height="{panel_bot - band_bot}" fill="{NAVY}"/>')
    s.append(f'<rect x="{px0}" y="{band_bot - 1.4}" width="{px1 - px0}" height="2.8" fill="{WHITE}"/>')
    s.append(f'<rect x="{px0}" y="{band_top}" width="{px1 - px0}" height="{panel_bot - band_top}" '
             f'fill="none" stroke="{NAVY}" stroke-width="0.6"/>')
    s.append('</g>')

    s.append(logo(200, 171))

    # main typography
    s.append('<g id="typography">')
    s.append(outlined(text_d(ALFA, "SHASHA", 200, 268, 44, width=166, tracking=0.02), RED, WHITE, 3.0))
    s.append(f'<path d="{text_d(ARVO, "ROLLER", 200, 315, 27, width=112, tracking=0.04)}" fill="{WHITE}"/>')
    s.append(f'<path d="{text_d(ARVO, "MEAL", 200, 350, 27, width=82, tracking=0.04)}" fill="{WHITE}"/>')
    s.append(outlined(text_d(ARCH, "FOOD FOR CHAMPIONS", 200, 372, 9.0, width=146, tracking=0.02),
                      SKY, WHITE, 1.6))
    s.append(outlined(text_d(ALFA, "10kg", 200, 422, 30, width=56), RED, WHITE, 2.4))
    s.append('</g>')

    s.append(proudly_zimbabwean(300, 416))

    # back-of-pack info under panel
    s.append(barcode(84, 452))
    s.append('<g id="manufacturer">')
    lines = ["PRODUCT OF:", "CENTRAL MILLERS (PVT) LTD", "4 SMITH STREET, KADOMA",
             "STAND 506, VAINONA TOWNSHIP, HARARE"]
    for k, ln in enumerate(lines):
        s.append(f'<path d="{text_d(ANTON, ln, 350, 458 + k * 5.6, 3.6, anchor="end", tracking=0.03)}" '
                 f'fill="{NAVY}"/>')
    s.append('</g>')

    s.append(recycle_icon(170, 512, "PLEASE RECYCLE"))
    s.append(recycle_icon(238, 512, "PLEASE DISPOSE"))

    # chain-stitched bottom seam
    st = ['<g id="bottom-seam">',
          f'<line x1="0" y1="516" x2="{W}" y2="516" stroke="#C9C5B9" stroke-width="0.4"/>']
    x = 2.0
    while x < W:
        st.append(f'<ellipse cx="{x:.1f}" cy="516" rx="1.6" ry="0.9" fill="{WHITE}" '
                  f'stroke="#B8B3A6" stroke-width="0.35"/>')
        x += 3.0
    st.append(f'<rect x="0" y="536" width="{W}" height="14" fill="#EDEBE4"/>')
    st.append('</g>')
    s.append("\n".join(st))

    s.append("</svg>")
    return "\n".join(s)


if __name__ == "__main__":
    out = os.path.join(HERE, "shasha_roller_meal_10kg.svg")
    with open(out, "w") as fh:
        fh.write(build())
    with open(os.path.join(HERE, "central_millers_logo.svg"), "w") as fh:
        fh.write(standalone_logo())
    print("wrote", out, os.path.getsize(out), "bytes")
