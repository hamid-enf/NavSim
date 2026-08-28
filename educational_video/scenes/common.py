"""Shared helpers for scenes."""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'engine'))

import gfx
from palette import (W, H, TXT, TXT_DIM, TXT_FAINT, PANEL, PANEL_EDGE,
                     STAGES, STAGE_COLORS, C_OK, C_WARN, C_BAD)
from anim import Scene, seg, ease, ease_out, fade_in, pulse


def header(c, title, accent, t=0.0, dur=0.6, subtitle=None):
    a = fade_in(t, 0.15, dur)
    if a <= 0:
        return
    ac = tuple(int(v * a) for v in accent)
    d = gfx.ImageDraw.Draw(c)
    bar_h = 64
    d.rounded_rectangle([W - 14, 26, W - 8, 26 + bar_h], radius=3, fill=ac + (255,))
    gfx.text(c, (W - 40, 30), title, 44, 'bold',
             tuple(int(v * a) for v in TXT), 'right')
    if subtitle:
        gfx.text(c, (W - 40, 86), subtitle, 26, 'regular',
                 tuple(int(v * a) for v in TXT_DIM), 'right')
    d.line([(0, 118), (W, 118)], fill=(34, 46, 82, 255), width=1)


def stage_color(name):
    return STAGE_COLORS.get(name, TXT_DIM)


def pipeline_strip(c, t, active, y=160, scale=1.0, highlight_all_after=False):
    """Row of stage chips with arrows; `active` index highlights current stage."""
    n = len(STAGES)
    x0 = 90
    x1 = W - 90
    total_w = x1 - x0
    gap = total_w / n
    d = gfx.ImageDraw.Draw(c)
    for i, st in enumerate(STAGES):
        col = stage_color(st)
        cx = x0 + gap * (i + 0.5)
        ap = fade_in(t, 0.3 + i * 0.12)
        if ap <= 0:
            continue
        is_act = (i == active)
        is_done = (i < active) if active >= 0 else highlight_all_after
        alpha_fill = 60 if is_act else (28 if is_done else 18)
        ow = 4 if is_act else 2
        glowp = (0.5 + 0.5 * pulse(t, 2.2, i * 0.2)) if is_act else 0
        if is_act:
            gfx.glow(c, (cx, y), 90, col, intensity=int(50 + 40 * glowp))
        gfx.chip(c, cx, y, st, col, size=int(24 * scale), pad_x=int(22 * scale),
                 pad_y=int(10 * scale), alpha_fill=alpha_fill, outline_w=ow)
        if i < n - 1:
            d2 = gfx.ImageDraw.Draw(c)
            gfx.arrow(d2, (cx + gap * 0.42, y), (x0 + gap * (i + 1.5) - gap * 0.42, y),
                      (96, 116, 160), 3, 12, progress=ease(seg(t, 0.5 + i * 0.12, 0.9 + i * 0.12)))


def vehicle(c, cx, cy, s, heading, color=(120, 200, 255), rot=True):
    """Small quad/vehicle icon."""
    d = gfx.ImageDraw.Draw(c)
    L = 34 * s
    ang = heading if rot else 0
    ca, sa = math.cos(ang), math.sin(ang)

    def T(x, y):
        return (cx + x * ca - y * sa, cy + x * sa + y * ca)

    d.polygon([T(-L * 0.4, -L * 0.4), T(L * 0.5, 0), T(-L * 0.4, L * 0.4), T(-L * 0.75, 0)],
              fill=color + (255,))
    for sx, sy in [(-L * 0.45, -L * 0.45), (-L * 0.45, L * 0.45),
                   (L * 0.45, -L * 0.45), (L * 0.45, L * 0.45)]:
        px, py = T(sx, sy)
        d.ellipse([px - 7 * s, py - 7 * s, px + 7 * s, py + 7 * s],
                  fill=(20, 30, 56, 255), outline=color + (255,), width=2)
    nx, ny = T(L * 0.5, 0)
    d.ellipse([nx - 4 * s, ny - 4 * s, nx + 4 * s, ny + 4 * s],
              fill=(240, 250, 255, 255))


def satellite(c, cx, cy, s, color=(251, 146, 60), t=0.0):
    d = gfx.ImageDraw.Draw(c)
    L = 30 * s
    d.rounded_rectangle([cx - L * 0.3, cy - L * 0.4, cx + L * 0.3, cy + L * 0.4],
                        radius=4 * s, fill=color + (255,))
    for sgn in (-1, 1):
        x = cx + sgn * (L * 0.4)
        x2 = x + sgn * L * 0.5
        lo, hi = min(x, x2), max(x, x2)
        d.rectangle([lo, cy - L * 0.28, hi, cy + L * 0.28],
                    fill=(30, 50, 90, 255), outline=color + (255,), width=2)
    d.ellipse([cx - 6 * s, cy - 14 * s, cx + 6 * s, cy - 2 * s],
              outline=(240, 250, 255, 255), width=2)


def ground_station(c, cx, cy, s, color=(148, 163, 184)):
    d = gfx.ImageDraw.Draw(c)
    L = 26 * s
    d.polygon([(cx, cy - L), (cx + L * 0.8, cy + L * 0.7), (cx - L * 0.8, cy + L * 0.7)],
              fill=(24, 34, 62, 255), outline=color + (255,), width=3)
    d.ellipse([cx - 5 * s, cy - L - 8 * s, cx + 5 * s, cy - L + 8 * s],
              fill=color + (255,))


def card(c, box, title, color, t=None, dur=0.5, title_size=30):
    a = 1.0 if t is None else fade_in(t, 0.2, dur)
    if a <= 0:
        return box
    x0, y0, x1, y1 = box
    gfx.soft_rrect(c, (x0, y0, x1, y1), 16,
                   fill=PANEL + (int(225 * a),), outline=PANEL_EDGE + (int(255 * a),), width=2)
    d = gfx.ImageDraw.Draw(c)
    d.rounded_rectangle([x1 - 8, y0 + 14, x1, y1 - 14], radius=4, fill=color + (int(255 * a),))
    gfx.text(c, (x1 - 24, y0 + 18), title, title_size, 'bold',
             tuple(int(v * a) for v in TXT), 'right')
    return box


def bullets(c, x_right, y, items, size=26, gap=44, color=TXT, mark_color=(52, 211, 153),
            t=0.0, stagger=0.25, weight='regular', max_w=1100):
    yy = y
    for i, it in enumerate(items):
        a = fade_in(t, 0.2 + i * stagger, 0.5)
        if a <= 0:
            yy += gap
            continue
        lines = fa_wrap(it, size, max_w)
        d = gfx.ImageDraw.Draw(c)
        for j, ln in enumerate(lines):
            col = tuple(int(v * a) for v in color)
            gfx.text(c, (x_right - 34, yy), ln, size, weight, col, 'right')
            yy += int(size * 1.45)
        d.ellipse([x_right - 6, yy - gap + int(size * 0.55), x_right + 10, yy - gap + int(size * 0.55) + 16],
                  fill=mark_color + (int(255 * a),))
        yy += gap - int(size * 1.45) * len(lines) + int(gap * 0.15)
    return yy


def fa_wrap(text, size, max_w):
    import fa_text
    return fa_text.wrap_width(text, size, 'regular', max_w)


def value_box(c, x_right, y, label, value, color=(34, 211, 238), t=0.0,
              label_size=22, value_size=34):
    a = fade_in(t, 0.2, 0.5)
    if a <= 0:
        return
    d = gfx.ImageDraw.Draw(c)
    gfx.text(c, (x_right, y), label, label_size, 'regular',
             tuple(int(v * a) for v in TXT_DIM), 'right')
    gfx.text(c, (x_right, y + label_size + 8), value, value_size, 'bold',
             tuple(int(v * a) for v in color), 'right')


def fmt(v, nd=1):
    if abs(v) >= 100:
        return f'{v:,.0f}'
    if abs(v) >= 10:
        return f'{v:.1f}'
    return f'{v:.{nd}f}'
