"""S07 — INS mechanization & drift."""
import math
import numpy as np

import gfx
from palette import (W, H, TXT, TXT_DIM, TXT_FAINT, C_INS, C_TRAJ, C_TRUTH,
                     C_PRED, C_WARN, C_BAD, C_OK)
from common import Scene, seg, ease, fade_in, header, card

STEPS = [
    ('۱', 'کواترنیون', 'q ← q⊗δq(ω·dt)', 8),
    ('۲', 'تبدیل به NED', 'f_n = C·f_b', 15),
    ('۳', 'انتگرال سرعت', 'v ← v+(f_n+g)·dt', 22),
    ('۴', 'انتگرال موقعیت', 'p ← p+½(v+vv)·dt', 29),
]


class S07(Scene):
    name = 'S07'

    def draw(self, c, t):
        D = self.dur
        header(c, 'مکانیزاسیون INS و دریفت', C_INS, t)

        # ---------- 4 step cards ----------
        for i, (num, title, eq, ti) in enumerate(STEPS):
            a = ease(seg(t, ti, ti + 1.2))
            if a <= 0:
                continue
            x = 1020 - i * 240
            x0, y0, x1, y1 = x - 110, 160, x + 110, 330
            gfx.soft_rrect(c, (x0, y0, x1, y1), 14,
                           fill=(19, 28, 51, int(230 * a)),
                           outline=(56, 189, 248, int(160 * a)), width=2)
            d = gfx.ImageDraw.Draw(c)
            d.ellipse([x1 - 44, y0 + 14, x1 - 10, y0 + 48], fill=C_INS + (int(255 * a),))
            gfx.text_c(c, x1 - 27, y0 + 22, num, 22, 'bold', (10, 20, 40))
            gfx.text_c(c, (x0 + x1) / 2, y0 + 66, title, 21, 'bold',
                       tuple(int(v * a) for v in TXT))
            gfx.text_c(c, (x0 + x1) / 2, y0 + 122, eq, 20, 'semibold',
                       tuple(int(v * a) for v in (34, 211, 238)))
            if i < 3:
                gfx.arrow(d, (x0 - 6, y0 + 95), (x0 - 24, y0 + 95),
                          (96, 116, 160), 3, 10)

        # ---------- earth models ----------
        a = ease(seg(t, 34, 36))
        if a > 0:
            gfx.text(c, (1020, 360), 'دو مدل زمین:', 26, 'bold',
                     tuple(int(v * a) for v in TXT), 'right')
            gfx.soft_rrect(c, (560, 396, 1020, 500), 12, fill=(24, 35, 66, int(210 * a)),
                           outline=(148, 163, 184, int(200 * a)), width=2)
            gfx.text_c(c, 790, 416, 'flat: آموزشی، g ثابت', 24, 'semibold',
                       tuple(int(v * a) for v in TXT_DIM))
            gfx.soft_rrect(c, (90, 396, 540, 500), 12, fill=(24, 35, 66, int(210 * a)),
                           outline=(167, 139, 250, int(220 * a)), width=2)
            gfx.text_c(c, 315, 412, 'WGS84: چرخش زمین + ترابرد', 22, 'semibold',
                       tuple(int(v * a) for v in TXT))
            gfx.text_c(c, 315, 448, '+ کوریولیس + گرانش محلی', 22, 'semibold',
                       tuple(int(v * a) for v in (167, 139, 250)))
            gfx.text_c(c, 790, 452, 'برای دقت و مسافت بلند', 20, 'regular',
                       tuple(int(v * a) for v in TXT_FAINT))

        # ---------- why INS drifts: error growth plot ----------
        if t > 45:
            a = ease(seg(t, 45, 47))
            x0, y0, x1, y1 = 90, 540, 1020, 1020
            gfx.panel(c, (x0, y0, x1, y1))
            gfx.text(c, (x1 - 24, y0 + 12),
                     'چرا INS تنها کافی نیست؟ (dead-reckoning)', 26, 'bold',
                     tuple(int(v * a) for v in C_WARN), 'right')
            p = gfx.Plot((x0 + 20, y0 + 40, x1 - 20, y1 - 20), 0, 120, 0, 1.0,
                         pad=(40, 8, 30, 44))
            p.axes(c, tlabels=[0, 30, 60, 90, 120], ylabels=[0, 0.25, 0.5, 0.75, 1.0],
                   xlabel='زمان [ثانیه]')
            ts = np.linspace(0, 120, 400)
            att = ts / 120 * 0.30
            vel = ts / 120 * 0.55
            pos = (ts / 120) ** 2
            pr = ease(seg(t, 46, 70))
            p.trace(c, ts, att, (148, 163, 184), progress=pr, lw=4)
            p.trace(c, ts, vel, C_INS, progress=pr, lw=4)
            p.trace(c, ts, pos, C_BAD, progress=pr, lw=4, fill_to=0, fill_alpha=40)
            for xx, lab, col, dy in [(700, 'خطای وضعیت: ∝ t', (148, 163, 184), 118),
                                     (700, 'خطای سرعت: ∝ t', C_INS, 78),
                                     (700, 'خطای موقعیت: ∝ t²', C_BAD, 44)]:
                gfx.text(c, (x1 - 60, y0 + dy), lab, 21, 'semibold',
                         tuple(int(v * a) for v in col), 'right')
        # ---------- drift map ----------
        if t > 66:
            a = ease(seg(t, 66, 68))
            x0, y0, x1, y1 = 1060, 540, 1830, 1020
            gfx.panel(c, (x0, y0, x1, y1))
            gfx.text(c, (x1 - 24, y0 + 12), 'INS خالص از مسیر واقعی جدا می‌شود', 25,
                     'bold', tuple(int(v * a) for v in TXT), 'right')
            cx, cy, R = 1445, 810, 160
            d = gfx.ImageDraw.Draw(c)
            d.ellipse([cx - R, cy - R, cx + R, cy + R],
                      outline=(148, 163, 184, int(180 * a)), width=2)
            pr = ease(seg(t, 67, 95))
            tt = 11 * pr
            nseg = int(110 * pr)
            for i in range(nseg):
                t1_ = i * 0.1
                t2_ = (i + 1) * 0.1
                a1 = -0.9 - 0.17 * t1_
                a2 = -0.9 - 0.17 * t2_
                rt = R * (1 + 0.45 * (t1_ / 11) ** 2)
                rd = R * (1 + 0.45 * (t2_ / 11) ** 2)
                d.line([(cx + rt * math.cos(a1), cy + rt * math.sin(a1)),
                        (cx + rd * math.cos(a2), cy + rd * math.sin(a2))],
                       fill=C_INS + (255,), width=3)
            ta = -0.9 - 0.17 * tt
            r_ins = R * (1 + 0.45 * (tt / 11) ** 2)
            tp = (cx + R * math.cos(ta), cy + R * math.sin(ta))
            ip = (cx + r_ins * math.cos(ta), cy + r_ins * math.sin(ta))
            gfx.dot(c, tp, 7, (148, 163, 184))
            gfx.dot(c, ip, 8, C_INS)
            if t > 84:
                aa = fade_in(t, 84, 1)
                gfx.line(d, tp, ip, C_BAD + (int(255 * aa),), width=3, dash=6)
            gfx.text_c(c, x1 - 90, y0 + 100, 'دریفت: فاصلهٔ INS از Truth',
                       22, 'bold', tuple(int(v * a) for v in C_INS), 'right')
            if t > 100:
                aa = fade_in(t, 100, 1)
                gfx.text_c(c, (x0 + x1) / 2, y1 - 22,
                           'با خطاهای پیش‌فرض بعد از ۱۲۰s: مرتبهٔ هزار متر (در آزمایش dropout: ۱۰۱۲ m)',
                           21, 'semibold', tuple(int(v * aa) for v in C_WARN))
        # closing
        if t > 104:
            a = fade_in(t, 104, 1)
            gfx.chip(c, 555, 990, 'INS خالص همیشه موازی اجرا می‌شود ← مقایسهٔ زنده',
                     C_INS, size=24)
