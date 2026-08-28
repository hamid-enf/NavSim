"""S06 — Initial alignment: levelling (static) & transfer alignment (moving)."""
import math
import numpy as np

import gfx
from palette import (W, H, TXT, TXT_DIM, TXT_FAINT, C_CALIB, C_INS, C_WARN,
                     C_OK, C_BAD, C_EST)
from common import Scene, seg, ease, fade_in, header, card, vehicle


class S06(Scene):
    name = 'S06'

    def draw(self, c, t):
        D = self.dur
        header(c, 'تراز اولیه: وضعیت را پیدا کن', C_CALIB, t)

        # ---------------- right: levelling animation ----------------
        a = ease(seg(t, 1, 2.5))
        if a > 0:
            cx, cy = 1445, 400
            d = gfx.ImageDraw.Draw(c)
            ang0 = math.radians(14)
            p = ease(seg(t, 8, 30))
            ang = ang0 * (1 - p)
            ca, sa = math.cos(ang), math.sin(ang)
            L = 250
            ex1 = (cx - L * ca, cy + L * sa)
            ex2 = (cx + L * ca, cy - L * sa)
            d.line([ex1, ex2], fill=(148, 163, 184, int(220 * a)), width=5)
            d.line([(cx, cy - 190), (cx, cy - 40)], fill=C_WARN + (int(255 * a),), width=4)
            _ah(c, (cx, cy - 40), (0, 1), 16, C_WARN + (int(255 * a),))
            gfx.text_c(c, cx, cy - 214, 'g (همیشه به پایین)', 22, 'semibold',
                       tuple(int(v * a) for v in C_WARN))
            veh_ang = -ang - math.pi / 2
            vehicle(c, cx, cy - 34, 1.6, veh_ang, C_INS)
            if t > 30:
                aa = fade_in(t, 30, 0.8)
                gfx.chip(c, cx, cy + 170, 'تراز شده: سطح با g هم‌راستا شد', C_OK,
                         size=24, label_color=TXT)
        # ---------------- left: static card ----------------
        a = ease(seg(t, 8, 10))
        if a > 0:
            x0, y0, x1, y1 = 90, 160, 1020, 560
            card(c, (x0, y0, x1, y1), 'حالت اول: سکون (Levelling)', C_CALIB)
            d = gfx.ImageDraw.Draw(c)
            d.rounded_rectangle([x1 - 8, y0 + 14, x1, y1 - 14], radius=4,
                                fill=C_CALIB + (int(255 * a),))
            rows = [
                ('آستانهٔ سکون:', TXT, 10),
                ('v ≤ 1 m/s ، a ≤ 0.1 m/s² ، ω ≤ 0.1°/s', C_INS, 12),
                ('در سکون شتاب‌سنج فقط گرانش را می‌بیند:', TXT, 16),
                ('roll = atan2(−fy, −fz)', (34, 211, 238), 20),
                ('pitch = atan2(fx, √(fy²+fz²))', (34, 211, 238), 23),
                ('yaw: از قطب‌نما — دقت پیش‌فرض ۱°', TXT, 27),
            ]
            yy = y0 + 76
            for s, col, ti in rows:
                aa = fade_in(t, ti)
                if aa <= 0:
                    yy += 46
                    continue
                gfx.text(c, (x1 - 40, yy), s, 25,
                         'bold' if s.endswith(':') else 'semibold',
                         tuple(int(v * aa) for v in col), 'right')
                yy += 46
        # ---------------- convergence plot ----------------
        if t > 34:
            a = ease(seg(t, 34, 36))
            x0, y0, x1, y1 = 90, 600, 1020, 1010
            gfx.panel(c, (x0, y0, x1, y1))
            gfx.text(c, (x1 - 24, y0 + 12), 'همگرایی با میانگین‌گیری: 1/√n', 26, 'bold',
                     tuple(int(v * a) for v in TXT), 'right')
            p = gfx.Plot((x0 + 20, y0 + 30, x1 - 20, y1 - 30), 0, 50, 0, 1.1,
                         pad=(40, 10, 30, 40))
            p.axes(c, tlabels=[0, 10, 20, 30, 40, 50], ylabels=[0, 0.25, 0.5, 0.75, 1.0],
                   xlabel='تعداد نمونه')
            n = 200
            ns = np.arange(1, n + 1, dtype=float)
            ideal = 1 / np.sqrt(ns)
            rng = np.random.default_rng(3)
            noisy = ideal * (1 + 0.25 * rng.standard_normal(n))
            noisy = np.clip(noisy, 0, 1.05)
            ns = ns / n * 50
            pr = ease(seg(t, 35, 52))
            p.trace(c, ns, ideal, (148, 163, 184), progress=pr, lw=3)
            p.trace(c, ns, noisy, C_CALIB, progress=pr, lw=3)
            gfx.text_c(c, x1 - 150, y0 + 46, 'میانگین ← 1/√n', 20, 'regular', TXT_DIM, 'right')
        # ---------------- moving card ----------------
        if t > 50:
            a = ease(seg(t, 50, 52))
            x0, y0, x1, y1 = 1060, 620, 1830, 1010
            card(c, (x0, y0, x1, y1), 'حالت دوم: حرکت (Transfer Alignment)', C_WARN)
            rows = [
                ('در حرکت، levelling معتبر نیست', TXT, 52),
                ('(شتاب‌سنج گرانش + شتاب را می‌بیند)', TXT_DIM, 55),
                ('منبع دیگر وضعیت را با خطای درشت', TXT, 59),
                ('تحویل می‌دهد: σ = ۳°', C_WARN, 62),
                ('اصلاح دقیق: با Fusion در حین مانور', C_OK, 66),
            ]
            yy = y0 + 72
            for s, col, ti in rows:
                aa = fade_in(t, ti)
                if aa <= 0:
                    yy += 46
                    continue
                gfx.text(c, (x1 - 40, yy), s, 24, 'semibold',
                         tuple(int(v * aa) for v in col), 'right')
                yy += 46
            d = gfx.ImageDraw.Draw(c)
            if t > 70:
                aa = fade_in(t, 70, 0.8)
                gfx.soft_rrect(c, (x0 + 20, y1 - 52, x1 - 20, y1 - 8), 10,
                               fill=(60, 30, 30, int(180 * aa)),
                               outline=C_BAD + (int(255 * aa),), width=2)
                gfx.text_c(c, (x0 + x1) / 2, y1 - 44,
                           'خطای اولیهٔ دلخواه کاربر ← تزریق از تب Errors',
                           21, 'semibold', tuple(int(v * aa) for v in C_BAD))


def _ah(c, tip, direction, size, color):
    d = gfx.ImageDraw.Draw(c)
    ang = math.atan2(direction[1], direction[0])
    a1 = ang + math.pi - 0.42
    a2 = ang + math.pi + 0.42
    d.polygon([(tip[0] + size * math.cos(a1), tip[1] + size * math.sin(a1)),
               (tip[0] + size * math.cos(a2), tip[1] + size * math.sin(a2)), tip],
              fill=color)
