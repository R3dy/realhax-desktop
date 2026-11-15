#!/usr/bin/env python3
"""Generate the RealHax wallpaper SVG (deterministic: fixed seed, static output).
Run once at authoring time; the output is embedded verbatim in install.sh."""
import random, math, sys

R = random.Random(1337)
W, H = 1920, 1080
HZ = 742          # horizon / waterline
CX, CY, RR = 1217, 566, 236   # neon ring

def ridge(pts, rough, iters):
    """midpoint displacement between control points"""
    for _ in range(iters):
        out = []
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            out.append((x1, y1))
            d = math.hypot(x2 - x1, y2 - y1)
            out.append(((x1 + x2) / 2 + R.uniform(-.15, .15) * d * .3,
                        (y1 + y2) / 2 + R.uniform(-1, 1) * d * rough))
        out.append(pts[-1])
        pts = out
    return pts

def path(pts, close_to=None):
    s = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    if close_to is not None:
        s += f" L{pts[-1][0]:.1f},{close_to} L{pts[0][0]:.1f},{close_to} Z"
    return s

# far range (behind ring, faint)
far = ridge([(-20, 700), (300, 640), (620, 690), (900, 655), (1300, 690),
             (1650, 650), (1940, 690)], .12, 5)
# main massif in front of ring (peak left of ring centre, like reference)
main = ridge([(520, HZ), (660, 690), (790, 620), (900, 540), (990, 482),
              (1062, 452), (1120, 500), (1175, 528), (1262, 560), (1335, 602),
              (1420, 640), (1560, 690), (1700, HZ)], .09, 5)
# left cliff
left = ridge([(-20, 420), (60, 470), (150, 540), (260, 640), (380, HZ)], .08, 4)
# right low ridge
right = ridge([(1450, HZ), (1600, 700), (1760, 660), (1940, 690)], .10, 4)

def cracks(n, x0, x1, ymin_fn, spread):
    out = []
    for _ in range(n):
        x = R.uniform(x0, x1)
        y = ymin_fn(x) + R.uniform(8, spread)
        pts = [(x, y)]
        for _ in range(R.randint(2, 5)):
            x += R.uniform(-14, 22); y += R.uniform(2, 14)
            pts.append((x, min(y, HZ - 2)))
        out.append(path(pts))
    return out

def top_y(pts, x):
    best = min(pts, key=lambda p: abs(p[0] - x))
    return best[1]

lava = cracks(75, 860, 1600, lambda x: top_y(main, x), 120)
lava_left = cracks(12, 20, 330, lambda x: top_y(left, x), 90)

facets = []
for _ in range(220):
    x = R.uniform(560, 1680); ty = top_y(main, x)
    if ty >= HZ - 5: continue
    y = R.uniform(ty, HZ); s_ = R.uniform(14, 48)
    pts = [(x, y), (x + R.uniform(-s_, s_), y + R.uniform(0, s_)), (x + R.uniform(-s_, s_), y + R.uniform(-s_*.3, s_*.6))]
    lit = 1 - min(1, abs(x - CX) / 700)
    c = int(14 + 26 * R.random() * (0.4 + lit))
    rr = min(255, c + int(30 * lit * R.random()))
    facets.append(f'<path d="{path(pts)} Z" fill="rgb({rr},{c},{c+2})" fill-opacity="{R.uniform(.25,.6):.2f}"/>')

# right-facing ridge segments that catch the ring light
rim = []
for (x1, y1), (x2, y2) in zip(main, main[1:]):
    if 760 < x1 < 1640:
        dist = abs((x1 + x2) / 2 - CX)
        op = max(0.15, 1 - dist / 520)
        rim.append(f'<path d="M{x1:.1f},{y1:.1f} L{x2:.1f},{y2:.1f}" stroke-opacity="{op:.2f}"/>')

# foreground rocky shore: scattered dark facets
rocks = []
for _ in range(260):
    x = R.uniform(-40, W + 40); y = R.uniform(HZ + 60, H + 20)
    s = (y - HZ) / 340 * R.uniform(10, 46)
    pts = [(x + R.uniform(-s, s), y + R.uniform(-s * .4, s * .4)) for _ in range(4)]
    shade = R.randint(10, 26)
    rocks.append(f'<path d="{path(pts)} Z" fill="rgb({shade},{shade},{shade+3})" fill-opacity="0.8"/>')
# red reflections on wet rocks
glints = []
for _ in range(90):
    x = R.gauss(CX, 160); y = R.uniform(HZ + 10, H)
    w = R.uniform(10, 60) * (1.2 - abs(x - CX) / 600)
    if w <= 2: continue
    glints.append(f'<rect x="{x - w/2:.1f}" y="{y:.1f}" width="{w:.1f}" height="{R.uniform(1,3):.1f}" '
                  f'fill="#ff2340" fill-opacity="{R.uniform(.2,.7):.2f}"/>')

HEX = "M0,-100 L86.6,-50 L86.6,50 L0,100 L-86.6,50 L-86.6,-50 Z"

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" preserveAspectRatio="xMidYMid slice">
<defs>
  <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#040507"/><stop offset=".55" stop-color="#0d0e13"/>
    <stop offset=".69" stop-color="#1a1416"/><stop offset="1" stop-color="#050506"/>
  </linearGradient>
  <radialGradient id="haze" cx="{CX}" cy="{CY+60}" r="620" gradientUnits="userSpaceOnUse">
    <stop offset="0" stop-color="#ff1638" stop-opacity=".28"/>
    <stop offset=".45" stop-color="#b0102a" stop-opacity=".10"/>
    <stop offset="1" stop-color="#000" stop-opacity="0"/>
  </radialGradient>
  <linearGradient id="rock" x1="0" y1="0" x2="1" y2=".3">
    <stop offset="0" stop-color="#08090c"/><stop offset=".6" stop-color="#141519"/><stop offset="1" stop-color="#1d1215"/>
  </linearGradient>
  <linearGradient id="water" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#120d10"/><stop offset=".3" stop-color="#09090b"/><stop offset="1" stop-color="#030304"/>
  </linearGradient>
  <linearGradient id="metal" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#ffffff"/><stop offset=".5" stop-color="#b9c7de"/><stop offset="1" stop-color="#6d7d99"/>
  </linearGradient>
  <filter id="g1" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="6"/></filter>
  <filter id="g2" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="22"/></filter>
  <filter id="g3" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="2.2"/></filter>
  <filter id="soft" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur stdDeviation="5"/></filter>
  <clipPath id="mclip"><path d="{path(main, HZ)}"/></clipPath>
  <clipPath id="above"><rect width="{W}" height="{HZ}"/></clipPath>
  <g id="logo">
    <path d="{HEX}" fill="#0c1018" fill-opacity=".85"/>
    <path d="{HEX}" fill="none" stroke="url(#metal)" stroke-width="16" stroke-dasharray="88 12" stroke-dashoffset="44"/>
    <path d="{HEX}" transform="scale(.74)" fill="none" stroke="url(#metal)" stroke-width="7"/>
    <path d="M-38,-26 L-6,2 L-38,30" fill="none" stroke="#fff" stroke-width="13" stroke-linecap="square"/>
    <path d="M6,32 L44,32" stroke="#fff" stroke-width="13"/>
  </g>
  <g id="scene">
    <path d="{path(far, HZ)}" fill="#0b0b0f" fill-opacity=".9"/>
    <circle cx="{CX}" cy="{CY}" r="{RR}" fill="none" stroke="#ff1e40" stroke-width="26" stroke-opacity=".55" filter="url(#g2)"/>
    <circle cx="{CX}" cy="{CY}" r="{RR}" fill="none" stroke="#ff2b4a" stroke-width="10" filter="url(#g1)"/>
    <circle cx="{CX}" cy="{CY}" r="{RR}" fill="none" stroke="#ffd6dc" stroke-width="2.6"/>
    <path d="{path(left, HZ)}" fill="url(#rock)"/>
    <path d="{path(right, HZ)}" fill="url(#rock)"/>
    <path d="{path(main, HZ)}" fill="url(#rock)"/>
    <g clip-path="url(#mclip)">{"".join(facets)}</g>
    <g fill="none" stroke="#ff2a48" stroke-width="2.2" stroke-linecap="round">{"".join(rim)}</g>
    <g fill="none" stroke="#ff2a48" stroke-width="5" stroke-linecap="round" filter="url(#g1)" opacity=".6">{"".join(rim)}</g>
    <g fill="none" stroke="#ff1d3d" stroke-width="1.1" stroke-linecap="round" stroke-opacity=".55">{"".join(f'<path d="{d}"/>' for d in lava + lava_left)}</g>
  </g>
</defs>
<rect width="{W}" height="{H}" fill="url(#sky)"/>
<rect width="{W}" height="{H}" fill="url(#haze)"/>
<use href="#scene" clip-path="url(#above)"/>
<rect y="{HZ}" width="{W}" height="{H-HZ}" fill="url(#water)"/>
<g opacity=".38" filter="url(#soft)"><use href="#scene" transform="translate(0,{2*HZ}) scale(1,-1)"/></g>
<rect x="{CX-260}" y="{HZ+2}" width="520" height="3" fill="#ff3352" filter="url(#g3)" opacity=".8"/>
<g>{"".join(glints)}</g>
<g>{"".join(rocks)}</g>
<g transform="translate({CX},{CY+6}) scale(.8)">
  <use href="#logo" filter="url(#g2)" opacity=".75" style="color:#9fb8ff"/>
  <path d="{HEX}" fill="none" stroke="#a9c1ff" stroke-width="34" opacity=".55" filter="url(#g2)"/>
  <use href="#logo"/>
</g>
<g font-family="JetBrains Mono, JetBrainsMono Nerd Font, DejaVu Sans Mono, monospace" fill="#c9ccd3" font-size="12" letter-spacing="4.2">
  <text x="186" y="156">OFFENSIVE SECURITY TRAINING</text>
  <rect x="186" y="172" width="46" height="1.2" fill="#555a63"/>
  <rect x="1436" y="142" width="1.2" height="90" fill="#3a3d44"/>
  <text x="1460" y="153" font-size="11.5" fill="#a6aab3">LABS</text>
  <text x="1460" y="178" font-size="11.5" fill="#a6aab3">SKILLS</text>
  <text x="1460" y="203" font-size="11.5" fill="#a6aab3">PRACTICE</text>
  <text x="1460" y="228" font-size="11.5" fill="#a6aab3">PROGRESS</text>
  <rect x="1672" y="895" width="20" height="2" fill="#ff2340"/>
  <text x="1672" y="920" font-size="12.5" fill="#e4e6ea">REAL SKILLS.</text>
  <text x="1672" y="941" font-size="12.5" fill="#e4e6ea">REAL ENVIRONMENTS.</text>
  <text x="1672" y="962" font-size="12.5" fill="#e4e6ea">REAL OUTCOMES.</text>
</g>
</svg>
'''
sys.stdout.write(svg)
