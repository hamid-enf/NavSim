"""S01 — Why navigation? two sensor families + the combination idea."""
import math
import numpy as np

import gfx
from palette import (W, H, TXT, TXT_DIM, TXT_FAINT, C_IMU, C_GNSS, C_FUSION,
                     C_EST, C_INS, PANEL, PANEL_EDGE, C_OK, C_BAD)
from common import Scene, seg, ease, ease_out, fade_in, header, card, vehicle, satellite


class S01(Scene):
    name = 'S01'

    def draw(self, c, t):
        D = self.dur
        header(c, 'چرا ناوبری؟', C_INS, t)

        # 1) vehicle + the three questions
        va = ease(seg(t, 0.8, 2.2))
        if va > 0:
            cx = W / 2
            cy = 330
            ang = -math.pi / 2 + 0.5 * math.sin((t - 0.8) * 0.7)
            gfx.glow(c, (cx, cy), 70, C_INS, 60)
            vehicle(c, cx, cy, 2.2 * va, ang + math.pi / 2)
            qs = [('ما کجا هستیم؟', 1780), ('کجا می‌رویم؟', 1390),
                  ('با چه جهتی؟', 1000)]
            # RTL: first question rightmost
            for i, (q, x) in enumerate(qs):
                a = fade_in(t, 1.2 + i * 0.5)
                if a > 0:
                    gfx.text(c, (x, 165), q, 30, 'semibold',
                             tuple(int(v * a) for v in TXT), 'right')
        # 2) two sensor cards
        # IMU card (right)
        a = ease(seg(t, 6, 7.5))
        if a > 0:
            x0, y0, x1, y1 = 1000, 200, 1830, 640
            card(c, (x0, y0, x1, y1), 'IMU — واحد اینرسی', C_IMU)
            gfx.text(c, (x1 - 28, y0 + 66), 'ژیرو + شتاب‌سنج', 28, 'semibold',
                     tuple(int(v * a) for v in C_IMU))
            items = [
                ('نرخ: ۱۰۰ هرتز (هر ۱۰ms)', 11),
                ('سریع، مستقل از محیط', 16),
                ('خطا با زمان جمع می‌شود (دریفت)', 21),
            ]
            yy = y0 + 120
            for s, ti in items:
                aa = fade_in(t, ti)
                if aa <= 0:
                    yy += 52
                    continue
                d = gfx.ImageDraw.Draw(c)
                col = tuple(int(v * aa) for v in TXT)
                gfx.text(c, (x1 - 28, yy), s, 25, 'regular', col, 'right')
                d.ellipse([x1 - 14, yy + 10, x1 + 2, yy + 26],
                          fill=C_IMU + (int(255 * aa),))
                yy += 52
            # drift sparkline
            sx0, sy0, sx1, sy1 = x0 + 30, y0 + 200, x1 - 60, y0 + 330
            d = gfx.ImageDraw.Draw(c)
            ts = np.linspace(0, 1, 120)
            drift = 2 * ts ** 2
            pts = [(sx0 + (sx1 - sx0) * x, sy1 - (sy1 - sy0) * y / 2.2)
                   for x, y in zip(ts, drift)]
            d.line(pts, fill=C_IMU + (255,), width=3)
            pts2 = [(sx0 + (sx1 - sx0) * x, sy1 - (sy1 - sy0) * 0.05) for x in ts]
            d.line(pts2, fill=C_OK + (180,), width=2)
            gfx.text(c, (sx1 - 4, sy0 - 14), 'دریفت با زمان', 20, 'regular',
                     TXT_FAINT, 'right')
        # GNSS card (left)
        a = ease(seg(t, 29, 30.5))
        if a > 0:
            x0, y0, x1, y1 = 90, 200, 920, 640
            card(c, (x0, y0, x1, y1), 'GNSS — ماهواره (GPS)', C_GNSS)
            satellite(c, x1 - 90, y0 + 130, 1.6 * a, C_GNSS)
            items = [
                ('نرخ: ۱ هرتز (هر ثانیه)', 32),
                ('موقعیت با دقت چند متر', 37),
                ('در تونل/شهر ممکن است قطع شود', 42),
            ]
            yy = y0 + 120
            for s, ti in items:
                aa = fade_in(t, ti)
                if aa <= 0:
                    yy += 52
                    continue
                d = gfx.ImageDraw.Draw(c)
                col = tuple(int(v * aa) for v in TXT)
                gfx.text(c, (x1 - 28, yy), s, 25, 'regular', col, 'right')
                d.ellipse([x1 - 14, yy + 10, x1 + 2, yy + 26],
                          fill=C_GNSS + (int(255 * aa),))
                yy += 52
            # scatter sparkline
            sx0, sy0, sx1, sy1 = x0 + 30, y0 + 200, x1 - 60, y0 + 330
            rng = np.random.default_rng(7)
            d = gfx.ImageDraw.Draw(c)
            base = [(sx0 + (sx1 - sx0) * x, sy1 - (sy1 - sy0) * 0.5)
                    for x in np.linspace(0, 1, 60)]
            d.line(base, fill=(90, 108, 150, 255), width=2)
            for i in range(14):
                x = (i / 14)
                px = sx0 + (sx1 - sx0) * x
                py = sy1 - (sy1 - sy0) * 0.5 + rng.normal(0, (sy1 - sy0) * 0.16)
                gfx.dot(c, (px, py), 5, C_GNSS)
            gfx.text(c, (sx1 - 4, sy0 - 14), 'نقاط GNSS دور مسیر', 20, 'regular',
                     TXT_FAINT, 'right')
        # 3) combination
        a = ease(seg(t, 49, 51))
        if a > 0:
            d = gfx.ImageDraw.Draw(c)
            gfx.arrow(d, (1415, 660), (W / 2 + 220, 770), C_IMU, 4, 16,
                      progress=ease(seg(t, 49, 50.5)))
            gfx.arrow(d, (505, 660), (W / 2 - 220, 770), C_GNSS, 4, 16,
                      progress=ease(seg(t, 49.5, 51)))
        a = ease(seg(t, 52, 54))
        if a > 0:
            gfx.chip(c, W / 2, 800, 'فیلتر ترکیب‌کننده (EKF)', C_FUSION, size=30)
            gfx.text(c, (690, 795), 'اینرسی پیش‌بینی می‌کند، ماهواره اصلاح می‌کند', 26,
                     'regular', tuple(int(v * a) for v in TXT_DIM), 'right')
        a = ease(seg(t, 57, 59))
        if a > 0:
            d = gfx.ImageDraw.Draw(c)
            gfx.arrow(d, (W / 2, 845), (W / 2, 915), C_EST, 5, 18,
                      progress=ease(seg(t, 57, 58.5)))
            gfx.glow(c, (W / 2, 975), 60, C_EST, int(80 * a))
            gfx.chip(c, W / 2, 975, 'پاسخ پایدار: موقعیت + سرعت + وضعیت',
                     C_EST, size=30)
        # closing
        a = fade_in(t, 64, 1)
        if a > 0:
            gfx.text_c(c, W / 2, 1040,
                       'NavSim: همین فرایند، با تمام خطاهای واقعی — تا فهمِ جواب را داشته باشید',
                       28, 'semibold', tuple(int(v * a) for v in (251, 191, 36)))
