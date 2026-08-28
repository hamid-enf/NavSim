"""Shared helpers for the how-to video: mock MATLAB GUI, param panels."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'engine'))

import gfx
from palette import (W, H, TXT, TXT_DIM, TXT_FAINT, C_INS, C_TRAJ, C_IMU,
                     C_GNSS, C_BARO, C_CALIB, C_FUSION, C_BAD, C_WARN,
                     C_EST, C_OK, C_TRUTH, C_PRED)
from anim import Scene, seg, ease, fade_in

TAB_NAMES = ['Simulation', 'Trajectory', 'IMU', 'GNSS', 'Baro',
             'INS & Align', 'Fusion', 'Errors', 'Experiments', 'Logs']
TAB_COLORS = [C_INS, C_TRAJ, C_IMU, C_GNSS, C_BARO, C_CALIB, C_FUSION,
              C_BAD, C_WARN, C_EST]
PLOT_TABS = ['Position', 'Velocity', 'Attitude', 'Errors', 'Sensors',
             '3D View', 'Data Flow']


def header(c, title, accent, t=0.0):
    a = fade_in(t, 0.15, 0.6)
    if a <= 0:
        return
    ac = tuple(int(v * a) for v in accent)
    d = gfx.ImageDraw.Draw(c)
    d.rounded_rectangle([W - 14, 26, W - 8, 90], radius=3, fill=ac + (255,))
    gfx.text(c, (W - 40, 30), title, 42, 'bold',
             tuple(int(v * a) for v in TXT), 'right')
    d.line([(0, 118), (W, 118)], fill=(34, 46, 82, 255), width=1)


def gui_mock(c, active_tab, box, t=0.0, highlight_plots=False, note=None):
    """Draw a compact mock of the NavSim MATLAB window.
    active_tab: index into TAB_NAMES or -1.
    """
    x0, y0, x1, y1 = [int(v) for v in box]
    a = ease(seg(t, 0.3, 1.3))
    if a <= 0:
        return
    d = gfx.ImageDraw.Draw(c)
    # window frame
    gfx.soft_rrect(c, (x0, y0, x1, y1), 12, fill=(12, 18, 36, 255),
                   outline=(60, 78, 130, 255), width=2)
    # title bar
    d.rounded_rectangle([x0, y0, x1, y0 + 34], radius=12, fill=(22, 32, 60, 255))
    gfx.text_c(c, (x0 + x1) / 2, y0 + 4, 'Navigation Simulator — GNSS/INS Educational Lab',
               15, 'semibold', TXT_DIM)
    # left column (tabs)
    lx0, lx1 = x0 + 8, x0 + (x1 - x0) * 0.36
    ty = y0 + 44
    tab_h = 26
    for i, nm in enumerate(TAB_NAMES):
        act = (i == active_tab)
        col = TAB_COLORS[i]
        alpha = 150 if act else 0
        d.rounded_rectangle([lx0 + 4, ty, lx1 - 4, ty + tab_h], radius=8,
                            fill=col + (alpha,),
                            outline=col + ((255 if act else 110),), width=2 if act else 1)
        gfx.text_c(c, (lx0 + lx1) / 2, ty + 3, nm, 14, 'bold' if act else 'regular',
                   TXT if act else TXT_DIM)
        ty += tab_h + 5
    # transport
    ty += 6
    d.rounded_rectangle([lx0 + 4, ty, lx1 - 4, ty + 92], radius=8,
                        fill=(18, 26, 48, 255), outline=(48, 64, 108, 255), width=1)
    btns = ['Start', 'Pause', 'Stop', 'Reset', 'Step']
    bw = (lx1 - lx0 - 24) / 5
    for j, b in enumerate(btns):
        bx = lx0 + 8 + j * bw
        col = C_OK if b == 'Start' else (C_WARN if b in ('Stop', 'Reset') else C_INS)
        d.rounded_rectangle([bx + 2, ty + 8, bx + bw - 2, ty + 34], radius=6,
                            fill=col + (90,), outline=col + (220,), width=1)
        gfx.text_c(c, bx + bw / 2, ty + 11, b, 12, 'semibold', TXT)
    # slider
    d.line([(lx0 + 16, ty + 56), (lx1 - 16, ty + 56)], fill=(90, 108, 150, 255), width=3)
    d.ellipse([lx0 + 40 - 5, ty + 56 - 5, lx0 + 40 + 5, ty + 56 + 5],
              fill=(240, 250, 255, 255))
    gfx.text_c(c, (lx0 + lx1) / 2, ty + 66, 'speed 0.1×–20×', 12, 'regular', TXT_FAINT)
    gfx.text_c(c, (lx0 + lx1) / 2, ty + 82, 't = 0.00 / 120 s', 12, 'semibold', TXT_DIM)
    # status bar
    d.rounded_rectangle([x0 + 8, y1 - 30, x1 - 8, y1 - 8], radius=6,
                        fill=(18, 26, 48, 255), outline=(48, 64, 108, 255), width=1)
    gfx.text_c(c, (x0 + x1) / 2, y1 - 26,
               'phase: idle   |   GNSS: -   |   |pos err| fused: -',
               13, 'regular', TXT_FAINT)
    # right column (plot tabs)
    rx0 = lx1 + 8
    ty = y0 + 44
    for i, nm in enumerate(PLOT_TABS):
        act = False
        col = C_FUSION if nm == 'Data Flow' else (C_PRED if nm == '3D View' else C_EST)
        fill_a = 70 if highlight_plots else 0
        d.rounded_rectangle([rx0 + 4, ty, x1 - 4, ty + tab_h], radius=8,
                            fill=col + (fill_a,),
                            outline=col + (170 if highlight_plots else 110,),
                            width=1)
        gfx.text_c(c, (rx0 + x1) / 2, ty + 3, nm, 14, 'regular', TXT_DIM)
        ty += tab_h + 5
    # plot area hint
    d.rounded_rectangle([rx0 + 4, ty + 8, x1 - 4, y1 - 40], radius=8,
                        fill=(14, 22, 44, 255), outline=(40, 55, 95, 255), width=1)
    if highlight_plots:
        # little legend lines
        ly = ty + 40
        for nm, col in [('Truth', (230, 240, 250)), ('INS', (70, 140, 230)),
                        ('GNSS', (250, 140, 40)), ('Fused', (60, 200, 90))]:
            d.line([(x1 - 220, ly), (x1 - 180, ly)], fill=col + (255,), width=3)
            gfx.text(c, (x1 - 170, ly - 12), nm, 14, 'semibold', col, 'right')
            ly += 26
    if note:
        gfx.text_c(c, (x0 + x1) / 2, y1 - 46, note, 14, 'regular', TXT_FAINT)


def param_row(c, x_right, y, en, default, fa, color=TXT, t=0.0, en_size=22,
              fa_size=20):
    """One parameter: english name (bold, colored) + default + Persian meaning."""
    a = fade_in(t, 0.2, 0.6)
    if a <= 0:
        return
    gfx.text(c, (x_right, y), en, en_size, 'bold', tuple(int(v * a) for v in color),
             'right')
    gfx.text(c, (x_right - 320, y + 2), f'= {default}', en_size, 'semibold',
             tuple(int(v * a) for v in (34, 211, 238)), 'right')
    gfx.text(c, (x_right, y + 34), fa, fa_size, 'regular',
             tuple(int(v * a) for v in TXT_DIM), 'right')


def detail_panel(c, box, title, color, t=0.0):
    x0, y0, x1, y1 = [int(v) for v in box]
    a = ease(seg(t, 0.5, 1.3))
    if a <= 0:
        return
    gfx.panel(c, (x0, y0, x1, y1))
    d = gfx.ImageDraw.Draw(c)
    d.rounded_rectangle([x1 - 10, y0 + 14, x1 - 2, y1 - 14], radius=4,
                        fill=color + (int(255 * a),))
    gfx.text(c, (x1 - 36, y0 + 20), title, 30, 'bold',
             tuple(int(v * a) for v in TXT), 'right')


def tab_scene(c, t, tab_idx, title, accent, items, footer=None, footer_t=999.0):
    """Standard layout for tab-explainer scenes.
    items: list of (t_start, en, default, fa, color)
    """
    D = getattr(tab_scene, '_dur', 999)
    header(c, title, accent, t)
    gui_mock(c, tab_idx, (90, 150, 700, 1010), t=t)
    x0, y0, x1, y1 = 740, 150, 1830, 1010
    gfx.panel(c, (x0, y0, x1, y1))
    d = gfx.ImageDraw.Draw(c)
    d.rounded_rectangle([x1 - 10, y0 + 14, x1 - 2, y1 - 14], radius=4, fill=accent + (255,))
    yy = y0 + 42
    for (ti, en, default, fa, col) in items:
        a = fade_in(t, ti, 0.7)
        if a <= 0:
            yy += 58
            continue
        gfx.text(c, (x1 - 40, yy), en, 21, 'bold', tuple(int(v * a) for v in col),
                 'right')
        gfx.text(c, (x1 - 40 - 450, yy + 2), f'= {default}', 21, 'semibold',
                 tuple(int(v * a) for v in (34, 211, 238)), 'right')
        gfx.text(c, (x1 - 40, yy + 28), fa, 19, 'regular',
                 tuple(int(v * a) for v in TXT_DIM), 'right')
        yy += 58
    if t >= footer_t and footer:
        a = fade_in(t, footer_t, 1)
        gfx.soft_rrect(c, (x0 + 20, y1 - 66, x1 - 20, y1 - 14), 10,
                       fill=(24, 40, 60, int(235 * a)),
                       outline=(251, 191, 36, int(230 * a)), width=2)
        gfx.text_c(c, (x0 + x1) / 2, y1 - 54, footer, 23, 'semibold',
                   tuple(int(v * a) for v in (251, 191, 36)))


def vehicle(c, cx, cy, s, heading, color=(120, 200, 255)):
    """Small quad/vehicle icon (copied from video-1 common)."""
    import math
    d = gfx.ImageDraw.Draw(c)
    L = 34 * s
    ca, sa = math.cos(heading), math.sin(heading)

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
