#!/usr/bin/env python3
"""Trace the Central Millers logo and the Proudly Zimbabwean badge from the
close-up reference photos.

Logo: rotate upright, fit + straighten the oval, isolate the white artwork,
remove the soft photographed lettering (it is re-set as crisp type at the exact
measured positions), fill the ribbon behind the lettering, vectorise with potrace.
Writes trace/logo_art.svg, trace/badge_art.svg and trace/layout.json.
Usage: python3 trace_logo.py LOGO_PHOTO BADGE_PHOTO
"""
import json, os, subprocess, sys
import cv2
import numpy as np

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trace")
os.makedirs(OUT, exist_ok=True)


def potrace(mask, name, turd=60):
    pbm = os.path.join(OUT, name + ".pbm")
    cv2.imwrite(pbm, cv2.bitwise_not(mask))
    subprocess.run(["potrace", pbm, "-s", "-o", os.path.join(OUT, name + ".svg"),
                    "-t", str(turd), "-a", "1.0", "-O", "0.3", "--flat"], check=True)


def bboxes_in(mask, box, min_area=40):
    x0, y0, x1, y1 = box
    sub = mask[y0:y1, x0:x1]
    n, lab, st, _ = cv2.connectedComponentsWithStats(sub)
    out = []
    for i in range(1, n):
        x, y, w, h, a = st[i]
        if a >= min_area:
            out.append([int(x + x0), int(y + y0), int(x + x0 + w), int(y + y0 + h)])
    return out


def group_words(boxes, gap):
    boxes = sorted(boxes)
    words, cur = [], [boxes[0]]
    for b in boxes[1:]:
        if b[0] - max(c[2] for c in cur) > gap:
            words.append(cur); cur = [b]
        else:
            cur.append(b)
    words.append(cur)
    return [[min(b[0] for b in w), min(b[1] for b in w), max(b[2] for b in w), max(b[3] for b in w)]
            for w in words]


# ------------------------------------------------------------------ logo
img = cv2.rotate(cv2.imread(sys.argv[1]), cv2.ROTATE_90_COUNTERCLOCKWISE)
h, w = img.shape[:2]
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
cyan = cv2.inRange(hsv, (85, 90, 90), (110, 255, 255))
cyan = cv2.morphologyEx(cyan, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
cnts, _ = cv2.findContours(cyan, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
inner = [c for c in cnts if cv2.pointPolygonTest(c, (w // 2, h // 2), False) >= 0] or [max(cnts, key=cv2.contourArea)]
(ex, ey), (ma, mi), ang = cv2.fitEllipse(cv2.convexHull(max(inner, key=cv2.contourArea)))
major = ang if ma >= mi else ang + 90
ma, mi = max(ma, mi), min(ma, mi)
tilt = ((major + 90) % 180) - 90
rot = cv2.warpAffine(img, cv2.getRotationMatrix2D((ex, ey), tilt, 1.0), (w, h),
                     flags=cv2.INTER_CUBIC, borderValue=(0, 0, 0))
a, b = ma / 2, mi / 2
x0, y0 = int(max(0, ex - a - 40)), int(max(0, ey - b - 40))
crop = rot[y0:int(ey + b + 40), x0:int(ex + a + 40)]
S = 4
crop = cv2.resize(crop, None, fx=S, fy=S, interpolation=cv2.INTER_CUBIC)
cx, cy, A, B = (ex - x0) * S, (ey - y0) * S, a * S, b * S
hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
sat = cv2.GaussianBlur(hsv[..., 1].astype(np.float32), (0, 0), 2.0)
val = cv2.GaussianBlur(hsv[..., 2].astype(np.float32), (0, 0), 2.0)
strict = ((sat < 105) & (val > 140)).astype(np.uint8) * 255
# adaptive: white where saturation is well below the local (cyan) level - copes with glare
local = cv2.GaussianBlur(sat, (0, 0), 40.0 * S)
loose = ((sat < local * 0.62) & (sat < 135) & (val > 120)).astype(np.uint8) * 255
# very strict white (true ink only, rejects glare on the cyan) for the lettering surrounds
vstrict = ((sat < 72) & (val > 165)).astype(np.uint8) * 255
for m in (strict, loose, vstrict):
    m[:] = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
oval = np.zeros_like(strict)
cv2.ellipse(oval, (int(cx), int(cy)), (int(A - 7 * S), int(B - 7 * S)), 0, 0, 360, 255, -1)
art = cv2.bitwise_and(loose, oval)

# text zones, as fractions of the inner ellipse (measured from the photo)
def zone(fx0, fy0, fx1, fy1):
    return [int(cx + fx0 * A), int(cy + fy0 * B), int(cx + fx1 * A), int(cy + fy1 * B)]

Z_CENTRAL = zone(-0.30, -0.45, 0.30, -0.25)
Z_RIBBON = zone(-0.42, -0.17, 0.42, 0.10)
Z_MILLERS = zone(-0.32, 0.16, 0.32, 0.43)

layout = {"ellipse": {"cx": float(cx), "cy": float(cy), "a": float(A), "b": float(B)}, "size": [crop.shape[1], crop.shape[0]]}
# white lettering: measure word boxes, then erase
for key, z in (("CENTRAL", Z_CENTRAL), ("MILLERS", Z_MILLERS)):
    bb = bboxes_in(strict, z, 30 * S * S)
    layout[key] = group_words(bb, 60 * S)
    bb = [q for q in bb if (q[3] - q[1]) < 0.25 * B and (q[2] - q[0]) < 0.2 * A]   # letters only
    layout[key] = group_words(bb, 60 * S)
    zm = np.zeros_like(strict)
    for (bx0, by0, bx1, by1) in bb:
        zm[by0:by1, bx0:bx1] = strict[by0:by1, bx0:bx1]
    zm = cv2.dilate(zm, np.ones((3 * S, 3 * S), np.uint8))
    # inside the word box use the strict mask (no glare halo), minus the letters
    for (wx0, wy0, wx1, wy1) in layout[key]:
        p = 8 * S
        sl = np.s_[wy0 - p:wy1 + p, wx0 - p:wx1 + p]
        # letters = everything white inside the tight word box; keep the frame around it
        lm = np.zeros_like(strict)
        lm[wy0:wy1, wx0:wx1] = strict[wy0:wy1, wx0:wx1]
        lm = cv2.dilate(lm, np.ones((16 * S, 9 * S), np.uint8))
        sl = np.s_[wy0 - 14 * S:wy1 + 14 * S, wx0 - 14 * S:wx1 + 14 * S]
        art[sl] = cv2.bitwise_and(vstrict[sl], cv2.bitwise_not(lm[sl]))

# ribbon lettering = holes in the white ribbon: measure, then fill
rib = cv2.bitwise_and(strict, oval)
cnts, hier = cv2.findContours(rib, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
holes = []
for i, c in enumerate(cnts):
    if hier[0][i][3] >= 0:  # a hole
        x, y, ww, hh = cv2.boundingRect(c)
        mx, my = x + ww / 2, y + hh / 2
        if Z_RIBBON[0] < mx < Z_RIBBON[2] and Z_RIBBON[1] < my < Z_RIBBON[3] and ww * hh > 25 * S * S:
            holes.append([int(x), int(y), int(x + ww), int(y + hh)])
            cv2.drawContours(art, [c], -1, 255, -1)
            cv2.drawContours(art, [c], -1, 255, 6)
layout["RIBBON"] = group_words(holes, 14 * S)
# solid ribbon body behind the lettering: fill each word box (the letters sit inside the ribbon)
for (wx0, wy0, wx1, wy1) in layout["RIBBON"]:
    art[wy0 - 3 * S:wy1 + 3 * S, wx0 - 3 * S:wx1 + 3 * S] = 255
ws = sorted(layout["RIBBON"])
for (a0, b0) in zip(ws, ws[1:]):          # gap between words
    art[max(a0[1], b0[1]) - 3 * S:min(a0[3], b0[3]) + 3 * S, a0[2]:b0[0]] = 255
# small ornaments are too degraded in the photo to trace: erase, redrawn as vectors
for (fx0, fy0, fx1, fy1) in ((-0.17, -0.64, 0.17, -0.455), (-0.13, -0.245, 0.13, -0.19)):
    z = zone(fx0, fy0, fx1, fy1)
    art[z[1]:z[3], z[0]:z[2]] = 0
layout["CREST"] = [cx, (zone(0, -0.64, 0, -0.455)[1] + zone(0, -0.64, 0, -0.455)[3]) / 2]
layout["SCROLL"] = [cx, (zone(0, -0.245, 0, -0.19)[1] + zone(0, -0.245, 0, -0.19)[3]) / 2]
cv2.imwrite(os.path.join(OUT, "logo_art.png"), art)
potrace(art, "logo_art", turd=40 * S)
json.dump(layout, open(os.path.join(OUT, "layout.json"), "w"), indent=1)
print("ribbon words", len(layout["RIBBON"]), "central", len(layout["CENTRAL"]), "millers", len(layout["MILLERS"]))

# ------------------------------------------------------------------ badge
img = cv2.rotate(cv2.imread(sys.argv[2]), cv2.ROTATE_90_COUNTERCLOCKWISE)
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
wt = ((hsv[..., 1] < 90) & (hsv[..., 2] > 150)).astype(np.uint8) * 255
wt = cv2.morphologyEx(wt, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
cnts, _ = cv2.findContours(wt, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
disk = max(cnts, key=cv2.contourArea)
(bx, by), (bma, bmi), bang = cv2.fitEllipse(disk)
R = max(bma, bmi) / 2
x0, y0 = int(bx - R - 20), int(by - R - 20)
# ellipse axes are close to the image axes: stretch the short one to make a circle
horiz, vert = (bmi, bma) if 45 < bang < 135 else (bma, bmi)
sx, sy = max(bma, bmi) / horiz, max(bma, bmi) / vert
img = cv2.resize(img, None, fx=sx, fy=sy, interpolation=cv2.INTER_CUBIC)
bx, by = bx * sx, by * sy
sub = img[int(by - R - 20):int(by + R + 20), int(bx - R - 20):int(bx + R + 20)]
x0, y0 = int(bx - R - 20), int(by - R - 20)
sub = cv2.resize(sub, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
hsv = cv2.cvtColor(sub, cv2.COLOR_BGR2HSV)
sat = cv2.GaussianBlur(hsv[..., 1].astype(np.float32), (0, 0), 2.0)
val = cv2.GaussianBlur(hsv[..., 2].astype(np.float32), (0, 0), 2.0)
bm = ((sat < 95) & (val > 145)).astype(np.uint8) * 255
bm = cv2.morphologyEx(bm, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
keep = np.zeros_like(bm)
cv2.circle(keep, (int((bx - x0) * 4), int((by - y0) * 4)), int(R * 4 - 10), 255, -1)
bm = cv2.bitwise_and(bm, keep)
cv2.imwrite(os.path.join(OUT, "badge_art.png"), bm)
potrace(bm, "badge_art", turd=200)
json.dump({"cx": (bx - x0) * 4, "cy": (by - y0) * 4, "r": R * 4, "rx": bma * 2, "ry": bmi * 2},
          open(os.path.join(OUT, "badge.json"), "w"))
print("badge r", R, bma / bmi)
