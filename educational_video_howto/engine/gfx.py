"""Drawing primitives (PIL) for the explainer video."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import fa_text
from palette import (W, H, BG_TOP, BG_BOT, GRID, PANEL, PANEL_EDGE,
                     TXT, TXT_DIM, TXT_FAINT, STAGE_COLORS)

# ---------------------------------------------------------------- bg --------

_BG = None


def _build_bg():
    global _BG
    t = np.linspace(0, 1, H)[:, None]
    col = np.array(BG_TOP, dtype=float) + (np.array(BG_BOT, dtype=float) -
                                           np.array(BG_TOP, dtype=float)) * t
    hgrad = np.repeat(col[:, None, :], W, axis=1).astype(np.uint8)
    img = Image.fromarray(hgrad, 'RGB').convert('RGBA')
    d = ImageDraw.Draw(img)
    step = 80
    for x in range(step, W, step):
        for y in range(step, H, step):
            d.ellipse([x - 1, y - 1, x + 1, y + 1], fill=(44, 59, 100, 255))
    vig = Image.new('L', (W, H), 0)
    vd = ImageDraw.Draw(vig)
    vd.rectangle([0, 0, W, H], fill=255)
    for i in range(140):
        a = int(75 * (i / 140) ** 2)
        vd.rectangle([i, i, W - i, H - i], outline=255 - a)
    vig = vig.filter(ImageFilter.GaussianBlur(60))
    black = Image.new('RGBA', (W, H), (0, 0, 0, 255))
    img.paste(black, (0, 0), vig)
    _BG = img


def bg_copy():
    if _BG is None:
        _build_bg()
    return _BG.copy()


def new_canvas():
    return bg_copy()


def rect_box(x, y, w, h):
    return (x, y, x + w, y + h)


# ---------------------------------------------------------------- shapes ----

def rrect(d, box, r, fill=None, outline=None, width=1):
    d.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)


def soft_rrect(c, box, r, fill=None, outline=None, width=1):
    """Rounded rect with proper alpha blending for semi-transparent fills."""
    if fill is not None and fill[3] < 255:
        x0, y0, x1, y1 = [int(v) for v in box]
        w, h = max(1, x1 - x0), max(1, y1 - y0)
        layer = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        ld.rounded_rectangle((0, 0, w, h), radius=min(r, w // 2, h // 2), fill=fill)
        c.alpha_composite(layer, (x0, y0))
    d = ImageDraw.Draw(c)
    if outline is not None:
        d.rounded_rectangle(box, radius=r, outline=outline, width=width)
    elif fill is not None and fill[3] >= 255:
        d.rounded_rectangle(box, radius=r, fill=fill)


def chip(c, cx, cy, label, color, size=26, weight='semibold', pad_x=26, pad_y=14,
         alpha_fill=34, outline=True, label_color=None, outline_w=3):
    """Rounded chip centered at (cx, cy). Returns box (x0,y0,x1,y1)."""
    w, h, bl, asc, desc = fa_text.text_size(label, size, weight)
    box = rect_box(cx - w / 2 - pad_x, cy - (asc + desc) / 2 - pad_y,
                   w + 2 * pad_x, (asc + desc) + 2 * pad_y)
    if label_color is None:
        a = alpha_fill / 255.0
        bg = (13, 21, 42)
        eff = [color[i] * a + bg[i] * (1 - a) for i in range(3)]
        lum = 0.299 * eff[0] + 0.587 * eff[1] + 0.114 * eff[2]
        label_color = TXT if lum < 140 else (15, 23, 42)
    soft_rrect(c, box, 16, fill=tuple(color) + (alpha_fill,),
               outline=tuple(color) + (255,) if outline else None, width=outline_w)
    fa_text.paste_text(c, (cx + w / 2, box[1] + pad_y), label, size, weight,
                       label_color, 'right')
    return box


def line(d, p1, p2, color, width=3, dash=0, offset=0):
    if not dash:
        d.line([p1, p2], fill=color, width=width)
        return
    x1, y1 = p1
    x2, y2 = p2
    L = math.hypot(x2 - x1, y2 - y1)
    if L < 1e-6:
        return
    ux, uy = (x2 - x1) / L, (y2 - y1) / L
    n = int(L / (dash * 2)) + 1
    for i in range(n + 1):
        s0 = i * 2 * dash - offset
        s1 = s0 + dash
        s0 = max(s0, 0.0)
        if s1 <= 0 or s0 >= L:
            continue
        s1 = min(s1, L)
        d.line([(x1 + ux * s0, y1 + uy * s0), (x1 + ux * s1, y1 + uy * s1)],
               fill=color, width=width)


def _arrowhead(d, tip, direction, size, color):
    ang = math.atan2(direction[1], direction[0])
    a1 = ang + math.pi - 0.42
    a2 = ang + math.pi + 0.42
    p1 = (tip[0] + size * math.cos(a1), tip[1] + size * math.sin(a1))
    p2 = (tip[0] + size * math.cos(a2), tip[1] + size * math.sin(a2))
    d.polygon([tip, p1, p2], fill=color)


def arrow(d, p1, p2, color, width=4, head=16, dash=0, offset=0, progress=1.0):
    if progress <= 0:
        return
    x1, y1 = p1
    x2, y2 = p2
    ex = x1 + (x2 - x1) * progress
    ey = y1 + (y2 - y1) * progress
    line(d, (x1, y1), (ex, ey), color, width, dash, offset)
    if progress >= 0.999:
        _arrowhead(d, (x2, y2), (x2 - x1, y2 - y1), head, color)


def circle(d, c, r, color, width=3, fill=None):
    d.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r],
              outline=color if fill is None else None, width=width, fill=fill)


def dot(c, center, r, color):
    d = ImageDraw.Draw(c)
    d.ellipse([center[0] - r, center[1] - r, center[0] + r, center[1] + r],
              fill=color)


def ring(c, center, r, color, width=4):
    d = ImageDraw.Draw(c)
    d.ellipse([center[0] - r, center[1] - r, center[0] + r, center[1] + r],
              outline=color, width=width)


_GLOW_CACHE = {}


def glow(c, center, r, color, intensity=110):
    key = (int(r * 2), color, intensity)
    sprite = _GLOW_CACHE.get(key)
    if sprite is None:
        d0 = max(2, int(r * 2))
        a = np.zeros((d0 * 2, d0 * 2), dtype=np.float32)
        yy, xx = np.mgrid[0:d0 * 2, 0:d0 * 2]
        dist = np.sqrt((xx - d0) ** 2 + (yy - d0) ** 2) / d0
        a = np.clip(1 - dist, 0, 1) ** 2 * intensity
        sprite = np.zeros((d0 * 2, d0 * 2, 4), dtype=np.uint8)
        sprite[..., 0] = color[0]
        sprite[..., 1] = color[1]
        sprite[..., 2] = color[2]
        sprite[..., 3] = a.astype(np.uint8)
        sprite = Image.fromarray(sprite, 'RGBA')
        _GLOW_CACHE[key] = sprite
    c.alpha_composite(sprite, (int(center[0] - r), int(center[1] - r)))


def panel(c, box, r=18, fill=PANEL + (235,), edge=PANEL_EDGE + (255,), width=2):
    soft_rrect(c, box, r, fill=fill, outline=edge, width=width)


def text(c, xy, s, size, weight='regular', color=TXT, align='right'):
    return fa_text.paste_text(c, xy, s, size, weight, color, align)


def text_c(c, cx, cy, s, size, weight='regular', color=TXT, align='center'):
    """Vertical-center text at (cx, cy)."""
    w, h, bl, asc, desc = fa_text.text_size(s, size, weight)
    if align == 'center':
        x = cx - w / 2
        a = 'center'
    elif align == 'right':
        x = cx
        a = 'right'
    else:
        x = cx
        a = 'left'
    fa_text.paste_text(c, (x, cy - (asc + desc) / 2), s, size, weight, color, a)
    return (w, h)


def hbar(c, box, p, color, track=(38, 52, 90), r=None):
    x0, y0, x1, y1 = box
    r = r if r is not None else (y1 - y0) / 2
    soft_rrect(c, box, r, fill=track + (255,))
    if p > 0.01:
        w = (x1 - x0) * max(0.02, min(1, p))
        soft_rrect(c, (x0, y0, x0 + w, y1), min(r, w / 2), fill=color + (255,))


def polygon(c, pts, fill, outline=None, width=2):
    d = ImageDraw.Draw(c)
    d.polygon(pts, fill=fill, outline=outline, width=width if outline else 1)


def dashed_rect(d, box, r, outline, width=2, dash=10):
    x0, y0, x1, y1 = box
    for (a, b) in [((x0 + r, y0), (x1 - r, y0)),
                   ((x1, y0 + r), (x1, y1 - r)),
                   ((x1 - r, y1), (x0 + r, y1)),
                   ((x0, y1 - r), (x0, y0 + r))]:
        line(d, a, b, outline, width, dash)


# ----------------------------------------------------------------- plots ---

class Plot:
    """Simple axes plot inside a box; maps data coords to pixels."""

    def __init__(self, box, xmin, xmax, ymin, ymax, pad=(50, 30, 70, 46)):
        self.box = box
        self.xmin, self.xmax = xmin, xmax
        self.ymin, self.ymax = ymin, ymax
        pl, pt, pr, pb = pad
        x0, y0, x1, y1 = box
        self.ax = (x0 + pl, y0 + pt, x1 - pr, y1 - pb)

    def X(self, x):
        a0, _, a1, _ = self.ax
        return a0 + (x - self.xmin) / (self.xmax - self.xmin) * (a1 - a0)

    def Y(self, y):
        _, a0, _, a1 = self.ax
        return a1 - (y - self.ymin) / (self.ymax - self.ymin) * (a1 - a0)

    def axes(self, c, tlabels=(), ylabels=(), xlabel='', ylabel='',
             grid=(34, 46, 80), axis=(90, 108, 150)):
        d = ImageDraw.Draw(c)
        a0x, a0y, a1x, a1y = self.ax
        for gx in tlabels:
            x = self.X(gx)
            d.line([(x, a0y), (x, a1y)], fill=grid + (255,), width=1)
        for gy in ylabels:
            y = self.Y(gy)
            d.line([(a0x, y), (a1x, y)], fill=grid + (255,), width=1)
        d.line([(a0x, a1y), (a1x, a1y)], fill=axis + (255,), width=2)
        d.line([(a0x, a1y), (a0x, a0y)], fill=axis + (255,), width=2)
        for gx in tlabels:
            text_c(c, self.X(gx), a1y + 24, str(gx), 22, 'regular', TXT_FAINT)
        for gy in ylabels:
            fa_text.paste_text(c, (a0x - 12, self.Y(gy) - 12), str(gy), 22,
                               'regular', TXT_FAINT, 'right')
        if xlabel:
            text_c(c, (a0x + a1x) / 2, a1y + 52, xlabel, 24, 'regular', TXT_DIM)
        if ylabel:
            text_c(c, a0x - 90, (a0y + a1y) / 2, ylabel, 24, 'regular', TXT_DIM)

    def trace(self, c, ts, vs, color, progress=1.0, lw=4, fill_to=None,
              fill_alpha=60):
        if len(ts) < 2:
            return
        n = max(2, int(len(ts) * progress))
        ax0, ay0, ax1, ay1 = self.ax
        pw, ph = max(1, int(ax1 - ax0)), max(1, int(ay1 - ay0))
        layer = Image.new('RGBA', (pw, ph), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        pts = [((self.X(ts[i]) - ax0), (self.Y(vs[i]) - ay0)) for i in range(n)]
        d.line(pts, fill=color + (255,), width=lw, joint='curve')
        if fill_to is not None and n >= 2:
            base = self.Y(fill_to) - ay0
            poly = pts + [(self.X(ts[n - 1]) - ax0, base),
                          (self.X(ts[0]) - ax0, base)]
            d.polygon(poly, fill=color + (fill_alpha,))
        c.alpha_composite(layer, (int(ax0), int(ay0)))
        if 0 < progress < 1 and pts:
            dot(c, (ax0 + pts[-1][0], ay0 + pts[-1][1]), lw + 3, color)

    def vline(self, c, x, color, width=3, dash=8):
        a0x, a0y, a1x, a1y = self.ax
        line(ImageDraw.Draw(c), (self.X(x), a0y), (self.X(x), a1y),
             color + (255,), width, dash)

    def point(self, c, x, y, color, r=7):
        dot(c, (self.X(x), self.Y(y)), r, color)
