# -*- coding: utf-8 -*-
"""Core graphics library for the NavSim educational animation (4K, Persian)."""
import math
import re
import io
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display
import matplotlib
matplotlib.use('Agg')
from matplotlib import mathtext
from matplotlib.font_manager import FontProperties

import os as _os

W, H = 3840, 2160
FPS = 24

BASE = _os.path.dirname(_os.path.abspath(__file__))
FONTS = {
    'vazir': f"{BASE}/fonts/Vazir.ttf",
    'shabnam': f"{BASE}/fonts/Shabnam.ttf",
    'tanha': f"{BASE}/fonts/Tanha.ttf",
    'dejavu': f"{BASE}/fonts/DejaVuSans.ttf",
    'dejavu_bold': f"{BASE}/fonts/DejaVuSans-Bold.ttf",
    'mono': f"{BASE}/fonts/DejaVuSansMono.ttf",
    'mono_bold': f"{BASE}/fonts/DejaVuSansMono-Bold.ttf",
}

# ------------------------------ palette ------------------------------
BG_TOP = (11, 14, 28)
BG_BOT = (26, 33, 60)
PANEL = (24, 29, 52)
PANEL_EDGE = (58, 70, 118)
INK = (236, 241, 250)
MUTED = (148, 158, 182)

C = {
    'traj':     (255, 170, 60),   # orange
    'truth':    (255, 214, 90),   # yellow
    'imu':      (255, 108, 122),  # red/pink
    'calib':    (64, 200, 190),   # teal
    'ins':      (96, 150, 255),   # blue
    'pred':     (178, 140, 255),  # purple
    'gnss':     (255, 140, 60),   # amber-orange
    'fusion':   (86, 220, 140),   # green
    'out':      (86, 205, 240),   # cyan
    'baro':     (120, 200, 255),
    'zupt':     (150, 230, 180),
    'white':    (236, 241, 250),
    'red':      (255, 108, 122),
    'green':    (86, 220, 140),
    'amber':    (255, 176, 66),
}

STAGES = ['traj', 'truth', 'imu', 'calib', 'ins', 'pred', 'gnss', 'fusion', 'out']
_STAGES = STAGES


# ------------------------------ easing ------------------------------
def clamp(x, a=0.0, b=1.0):
    return a if x < a else (b if x > b else x)


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_in(x):
    x = clamp(x)
    return x ** 3


def ease_inout(x):
    x = clamp(x)
    return 3 * x * x - 2 * x * x * x


def smoothstep(a, b, x):
    t = clamp((x - a) / (b - a) if b != a else (1.0 if x >= b else 0.0))
    return t * t * (3 - 2 * t)


def pulse(t, freq=1.0):
    return 0.5 + 0.5 * math.sin(2 * math.pi * freq * t)


# ------------------------------ compositing ------------------------------
def paste(draw, img, x=0, y=0):
    """Alpha-composite an RGBA image onto the drawing canvas."""
    draw._image.alpha_composite(img, (int(x), int(y)))


def paste_center(draw, img, x, y):
    paste(draw, img, int(x - img.width / 2), int(y - img.height / 2))


# ------------------------------ persian text ------------------------------
_CTRL = re.compile(r'[\u200e\u200f\u202a-\u202e\u2066-\u2069]')


def shape(s):
    """Reshape + bidi-reorder a Persian string into visual order."""
    s = arabic_reshaper.reshape(s)
    s = get_display(s)
    return _CTRL.sub('', s)


_text_cache = {}


def text_layer(text, size, color, bold=False, font='vazir'):
    key = (text, font, size, tuple(color), bold)
    if key in _text_cache:
        return _text_cache[key]
    shaped = shape(text)
    fp = FONTS[font]
    f = ImageFont.truetype(fp, size)
    stroke = max(1, size // 22) if bold else 0
    bbox = f.getbbox(shaped)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    pad = stroke + 6
    img = Image.new('RGBA', (max(w, 1) + 2 * pad, max(h, 1) + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pos = (pad - bbox[0], pad - bbox[1])
    if stroke:
        d.text(pos, shaped, font=f, fill=color, stroke_width=stroke, stroke_fill=color)
    else:
        d.text(pos, shaped, font=f, fill=color)
    res = (img, bbox[0] - pad, bbox[1] - pad)
    _text_cache[key] = res
    return res


# anchor codes: two letters, first = horizontal (l,c,r), second = vertical (t,m,b)
def text_xy(draw, xy, text, size=56, color=INK, bold=False, font='vazir',
            anchor='mm', alpha=255):
    img, ox, oy = text_layer(text, size, color, bold, font)
    if alpha < 255:
        img = img.copy()
        a = np.array(img)
        a[:, :, 3] = (a[:, :, 3] * (alpha / 255.0)).astype(np.uint8)
        img = Image.fromarray(a, 'RGBA')
    iw, ih = img.size
    x, y = xy
    if anchor[0] == 'c':
        x = x - iw // 2
    elif anchor[0] == 'r':
        x = x - iw
    if anchor[1] == 'm':
        y = y - ih // 2
    elif anchor[1] == 'b':
        y = y - ih
    paste(draw, img, x, y)
    return iw, ih


def text_w(draw, text, size=56, bold=False, font='vazir'):
    img, ox, oy = text_layer(text, size, INK, bold, font)
    return img.size[0]


# ------------------------------ drawing helpers ------------------------------
_BG_IMG = None


def make_bg():
    """Build the cached full-screen background (gradient + grid) once."""
    global _BG_IMG
    grad = np.zeros((H, W, 3), dtype=np.uint8)
    y = np.arange(H).reshape(-1, 1)
    t = y / H
    for i in range(3):
        grad[:, :, i] = (BG_TOP[i] + (BG_BOT[i] - BG_TOP[i]) * t).astype(np.uint8)
    img = Image.fromarray(grad, 'RGB').convert('RGBA')
    d = ImageDraw.Draw(img)
    step = 96
    for x in range(0, W, step):
        d.line([(x, 0), (x, H)], fill=(255, 255, 255, 6), width=1)
    for y0 in range(0, H, step):
        d.line([(0, y0), (W, y0)], fill=(255, 255, 255, 6), width=1)
    _BG_IMG = img
    return _BG_IMG


def get_bg():
    return _BG_IMG if _BG_IMG is not None else make_bg()


def bg(draw):
    paste(draw, get_bg(), 0, 0)


def rrect(draw, box, radius=28, fill=None, outline=None, width=4):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def glow_box(draw, box, color, radius=28, width=8, alpha_halo=60):
    """Draw a glowing rounded rectangle (halo + border)."""
    x0, y0, x1, y1 = box
    pad = 30
    lw, lh = (x1 - x0) + 2 * pad, (y1 - y0) + 2 * pad
    halo = Image.new('RGBA', (lw, lh), (0, 0, 0, 0))
    hd = ImageDraw.Draw(halo)
    for i in range(4, 0, -1):
        d = i * 6
        hd.rounded_rectangle([pad - d, pad - d, pad + (x1 - x0) + d, pad + (y1 - y0) + d],
                             radius=radius + d,
                             outline=tuple(color) + (alpha_halo // (i + 1),),
                             width=width + i)
    halo = halo.filter(ImageFilter.GaussianBlur(6))
    paste(draw, halo, x0 - pad, y0 - pad)
    draw.rounded_rectangle(box, radius=radius, outline=tuple(color) + (255,), width=width)


def arrow(draw, p0, p1, color, width=10, head=34):
    x0, y0 = p0
    x1, y1 = p1
    draw.line([p0, p1], fill=color, width=width)
    ang = math.atan2(y1 - y0, x1 - x0)
    for da in (150 * math.pi / 180, -150 * math.pi / 180):
        draw.line([p1, (x1 + head * math.cos(ang + da), y1 + head * math.sin(ang + da))],
                  fill=color, width=width)


def arrow_flow(draw, p0, p1, color, t, width=8, head=26):
    """Animated dashed arrow where the dashes march forward with time t."""
    x0, y0 = p0
    x1, y1 = p1
    seg = math.hypot(x1 - x0, y1 - y0)
    ang = math.atan2(y1 - y0, x1 - x0)
    n = 10
    dash = seg / (2 * n)
    for i in range(n):
        s0 = ((i / n) + (t % 1.0)) * seg % seg
        s1 = min(s0 + dash, seg)
        a = (x0 + s0 * math.cos(ang), y0 + s0 * math.sin(ang))
        b = (x0 + s1 * math.cos(ang), y0 + s1 * math.sin(ang))
        draw.line([a, b], fill=color, width=width)
    draw.line([p0, p1], fill=tuple(color) + (60,), width=width // 3)
    for da in (150 * math.pi / 180, -150 * math.pi / 180):
        draw.line([p1, (x1 + head * math.cos(ang + da), y1 + head * math.sin(ang + da))],
                  fill=color, width=width)


def dot(draw, xy, color, r=12, alpha=255):
    x, y = xy
    hw = r * 4
    halo = Image.new('RGBA', (hw, hw), (0, 0, 0, 0))
    hd = ImageDraw.Draw(halo)
    hd.ellipse([hw // 2 - r * 2, hw // 2 - r * 2, hw // 2 + r * 2, hw // 2 + r * 2],
               fill=tuple(color) + (alpha // 3,))
    halo = halo.filter(ImageFilter.GaussianBlur(8))
    paste(draw, halo, x - hw // 2, y - hw // 2)
    draw.ellipse([x - r, y - r, x + r, y + r], fill=tuple(color) + (alpha,))


_header_cache = {}


def header(draw, title, subtitle=None, tag='NavSim'):
    key = (title, subtitle, tag)
    band = _header_cache.get(key)
    if band is None:
        band = Image.new('RGBA', (W, 150), (0, 0, 0, 0))
        bd = ImageDraw.Draw(band)
        for y in range(150):
            a = int(120 * (1 - y / 150))
            bd.line([(0, y), (W, y)], fill=(10, 13, 28, a), width=1)
        bd.line([(0, 150), (W, 150)], fill=(60, 72, 120, 120), width=2)
        rrect(bd, (70, 40, 290, 110), radius=34, fill=(30, 36, 66, 255),
              outline=(90, 120, 200, 200), width=3)
        text_xy(bd, (180, 75), 'NavSim', size=44, color=C['out'], bold=True,
                font='dejavu_bold', anchor='mm')
        text_xy(bd, (W - 90, 60), title, size=76, color=INK, bold=True, anchor='rt')
        if subtitle:
            text_xy(bd, (W - 90, 118), subtitle, size=44, color=MUTED, anchor='rt')
        _header_cache[key] = band
    paste(draw, band, 0, 0)


def panel(draw, box, fill=PANEL, edge=PANEL_EDGE, radius=30):
    rrect(draw, box, radius=radius, fill=fill, outline=edge, width=3)


def stage_box(draw, box, key, label, size=44, active=False, alpha=255):
    color = C[key]
    if active:
        glow_box(draw, box, color, radius=22, width=7, alpha_halo=70)
        fill = tuple(color) + (40,)
    else:
        fill = (26, 31, 58)
    rrect(draw, box, radius=22, fill=fill,
          outline=tuple(color) + (min(255, 130 + int(alpha * 0.5)),), width=4)
    cx = (box[0] + box[2]) // 2
    cy = (box[1] + box[3]) // 2
    text_xy(draw, (cx, cy), label, size=size, color=color if not active else INK,
            bold=active, anchor='mm', alpha=alpha)


def bullets(draw, items, x_right, y_top, line_h=76, size=52, t=1.0, gap=0.18):
    """items: list of (text, color[, sub]). Right-aligned RTL list with staggered
    fade-in.  t is normalized time (0..1)."""
    n = len(items)
    for i, it in enumerate(items):
        txt = it[0]
        col = it[1] if len(it) > 1 else INK
        sub = it[2] if len(it) > 2 else None
        start = i * gap
        a = clamp((t - start) / (gap * 0.7)) if gap > 0 else 1.0
        if a <= 0:
            continue
        y = y_top + i * line_h
        dot(draw, (x_right - 18, y + size // 2), col, r=10, alpha=int(255 * ease_out(a)))
        text_xy(draw, (x_right - 46, y), txt, size=size, color=col, anchor='rt',
                alpha=int(255 * ease_out(a)))
        if sub:
            text_xy(draw, (x_right - 46, y + size + 4), sub, size=size - 12,
                    color=MUTED, anchor='rt', alpha=int(200 * ease_out(a)))


def progress(draw, t, color=(86, 205, 240)):
    draw.line([(0, H - 6), (int(W * clamp(t)), H - 6)], fill=color, width=6)


def plot_line(draw, box, x, y, color, prog=1.0, width=6, ymin=None, ymax=None,
              logy=False):
    """Draw a data series into box, animated up to fraction prog of the points."""
    bx0, by0, bx1, by1 = box
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    if len(x) < 2:
        return
    ymin = float(np.nanmin(y)) if ymin is None else ymin
    ymax = float(np.nanmax(y)) if ymax is None else ymax
    if ymax - ymin < 1e-12:
        ymax = ymin + 1.0
    n = len(x)
    # downsample long series to keep per-frame line-drawing cheap
    MAXPTS = 1400
    step = max(1, n // MAXPTS)
    nshow = max(2, int(n * clamp(prog)))
    xs = x[:nshow:step]
    ys = y[:nshow:step]
    x0, x1 = float(x[0]), float(x[-1])
    if x1 - x0 < 1e-12:
        x1 = x0 + 1.0
    pts = []
    for i in range(len(xs)):
        if not np.isfinite(xs[i]) or not np.isfinite(ys[i]):
            pts.append(None)
            continue
        px = bx0 + (xs[i] - x0) / (x1 - x0) * (bx1 - bx0)
        if logy:
            v = np.log(max(ys[i], 1e-3) + 1)
            vmin, vmax = np.log(max(ymin, 1e-3) + 1), np.log(max(ymax, 1e-3) + 1)
        else:
            v = ys[i]
            vmin, vmax = ymin, ymax
        py = by1 - (v - vmin) / (vmax - vmin) * (by1 - by0)
        pts.append((px, py))
    seg = []
    for p in pts:
        if p is None:
            if len(seg) > 1:
                draw.line(seg, fill=color, width=width)
            seg = []
        else:
            seg.append(p)
    if len(seg) > 1:
        draw.line(seg, fill=color, width=width)


def plot_axes(draw, box, ymin, ymax, n_ticks=4, label_fmt='%.0f', ylabel=None,
              title=None, title_color=INK):
    bx0, by0, bx1, by1 = box
    draw.line([(bx0, by0), (bx0, by1)], fill=(90, 100, 130), width=3)
    draw.line([(bx0, by1), (bx1, by1)], fill=(90, 100, 130), width=3)
    for i in range(n_ticks + 1):
        f = i / n_ticks
        yy = by1 - f * (by1 - by0)
        val = ymin + f * (ymax - ymin)
        draw.line([(bx0 - 8, yy), (bx0, yy)], fill=(90, 100, 130), width=3)
        text_xy(draw, (bx0 - 18, yy), label_fmt % val, size=34, color=MUTED,
                font='mono', anchor='rm')
    if ylabel:
        text_xy(draw, (bx0 - 70, (by0 + by1) // 2), ylabel, size=40, color=MUTED,
                anchor='mm')
    if title:
        text_xy(draw, ((bx0 + bx1) // 2, by0 - 30), title, size=44, color=title_color,
                bold=True, anchor='mb')


def vehicle(draw, xy, size=120, color=(200, 220, 255), heading=0.0, alpha=255):
    """A small aircraft glyph oriented by heading (radians, screen CCW)."""
    cx, cy = xy
    import math as _m
    # draw as triangle + wings, rotated
    pts = [(size, 0), (-size * 0.55, size * 0.5), (-size * 0.3, 0),
           (-size * 0.55, -size * 0.5)]
    rot = []
    for (px, py) in pts:
        rx = px * _m.cos(heading) - py * _m.sin(heading)
        ry = px * _m.sin(heading) + py * _m.cos(heading)
        rot.append((cx + rx, cy + ry))
    draw.polygon(rot, fill=tuple(color) + (alpha,))


def ned_axes(draw, origin, scale=1.0, labels=True):
    """NED triad: N=red(up), E=green(right), D=blue(down into screen)."""
    ox, oy = origin
    draw.line([origin, (ox, oy - 150 * scale)], fill=(255, 110, 110), width=8)
    draw.line([origin, (ox + 150 * scale, oy)], fill=(110, 220, 120), width=8)
    draw.line([origin, (ox - 90 * scale, oy + 90 * scale)], fill=(120, 160, 255), width=8)
    if labels:
        text_xy(draw, (ox + 20, oy - 160 * scale), 'N (شمال)', size=40,
                color=(255, 130, 130), bold=True, anchor='lb')
        text_xy(draw, (ox + 160 * scale, oy + 10), 'E (شرق)', size=40,
                color=(130, 230, 140), bold=True, anchor='lb')
        text_xy(draw, (ox - 100 * scale, oy + 100 * scale), 'D (پایین)', size=40,
                color=(130, 170, 255), bold=True, anchor='lb')


# ------------------------------ equations ------------------------------
_eq_cache = {}


def eq_img(s, color='#e8f0ff', fontsize=48, dpi=280):
    key = (s, color, fontsize, dpi)
    if key in _eq_cache:
        return _eq_cache[key]
    buf = io.BytesIO()
    prop = FontProperties(size=fontsize)
    mathtext.math_to_image(s, buf, prop=prop, dpi=dpi, format='png', color=color)
    buf.seek(0)
    img = Image.open(buf).convert('RGBA')
    a = np.array(img)
    ys, xs = np.where(a[:, :, 3] > 8)
    if len(xs) > 0:
        img = img.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
    _eq_cache[key] = img
    return img


def eq(draw, s, xy, target_h=90, color='#e8f0ff', anchor='mm', alpha=255,
       fontsize=48):
    """Draw a LaTeX equation scaled to target_h pixels height, positioned at xy."""
    img = eq_img(s, color=color, fontsize=fontsize)
    iw, ih = img.size
    scale = target_h / ih
    if abs(scale - 1) > 0.01:
        img = img.resize((max(1, int(iw * scale)), max(1, int(ih * scale))),
                         Image.LANCZOS)
        iw, ih = img.size
    if alpha < 255:
        img = img.copy()
        a = np.array(img)
        a[:, :, 3] = (a[:, :, 3] * (alpha / 255.0)).astype(np.uint8)
        img = Image.fromarray(a, 'RGBA')
    x, y = xy
    if anchor[0] == 'c':
        x = x - iw // 2
    elif anchor[0] == 'r':
        x = x - iw
    if anchor[1] == 'm':
        y = y - ih // 2
    elif anchor[1] == 'b':
        y = y - ih
    paste(draw, img, x, y)
    return iw, ih


def clear_cache():
    _text_cache.clear()
    _eq_cache.clear()
