"""S10 — Aiding: Baro, ZUPT, OOSM."""
import math

import gfx
from palette import (W, H, TXT, TXT_DIM, TXT_FAINT, C_BARO, C_ZUPT, C_OOSM,
                     C_GNSS, C_INS, C_OK, C_BAD)
from common import Scene, seg, ease, fade_in, header, card


class S10(Scene):
    name = 'S10'

    def draw(self, c, t):
        D = self.dur
        header(c, 'کمک‌های جانبی: Baro ، ZUPT ، OOSM', C_BARO, t)

        a = ease(seg(t, 4, 6))
        if a > 0:
            x0, y0, x1, y1 = 90, 170, 1830, 400
            card(c, (x0, y0, x1, y1), '۱ — ارتفاع‌سنج بارومتریک', C_BARO)
            d = gfx.ImageDraw.Draw(c)
            ax0, ax1, ay0, ay1 = x0 + 60, x0 + 560, y0 + 70, y1 - 24
            d.line([(ax0, (ay0 + ay1) / 2 + 30), (ax1, (ay0 + ay1) / 2 + 30)],
                   fill=(90, 108, 150, 255), width=2)
            n = 60
            import numpy as np
            ts = np.linspace(0, 1, n)
            drift = 40 * ts ** 2
            pts = [(ax0 + (ax1 - ax0) * x, (ay0 + ay1) / 2 + 30 + drift[i] * 0.5)
                   for i, x in enumerate(ts)]
            d.line(pts, fill=C_BAD + (200,), width=3)
            pts2 = [(ax0 + (ax1 - ax0) * x, (ay0 + ay1) / 2 + 30 + 8 * math.sin(i / 4))
                    for i, x in enumerate(ts)]
            d.line(pts2, fill=C_OK + (255,), width=3)
            gfx.text(c, (x1 - 40, y0 + 70), 'سنجش اسکالر ارتفاع: σ = ۱ m ، نرخ ۱۰ Hz',
                     25, 'semibold', tuple(int(v * a) for v in TXT), 'right')
            gfx.text(c, (x1 - 40, y0 + 112),
                     'در تونل / اتاق پرواز (GNSS قطع): کانال عمودی کران‌دار می‌ماند',
                     23, 'regular', tuple(int(v * a) for v in TXT_DIM), 'right')
            gfx.text(c, (x1 - 40, y0 + 158), 'آپدیت اسکالر با H = [0 0 −1 0 …] و گیت NIS جداگانه',
                     22, 'semibold', tuple(int(v * a) for v in (34, 211, 238)), 'right')
            gfx.text_c(c, ax0 + 60, ay1 + 8, 'بدون بارومتر', 19, 'regular', C_BAD, 'right')
            gfx.text_c(c, ax1 - 40, ay1 + 8, 'با بارومتر', 19, 'regular', C_OK, 'right')

        if t > 26:
            a = ease(seg(t, 26, 28))
            x0, y0, x1, y1 = 1060, 440, 1830, 1030
            card(c, (x0, y0, x1, y1), '۲ — ZUPT: به‌روزرسانی سرعت صفر', C_ZUPT)
            if t > 30:
                aa = fade_in(t, 30, 0.8)
                d = gfx.ImageDraw.Draw(c)
                tx, ty = x0 + 160, y0 + 120
                d.rounded_rectangle([tx - 14, ty - 70, tx + 14, ty + 50], radius=8,
                                    fill=(30, 42, 74, 255),
                                    outline=(90, 108, 150, 255), width=2)
                for j, col in enumerate([(80, 90, 110), (90, 90, 60), (220, 70, 60)]):
                    d.ellipse([tx - 9, ty - 62 + j * 40, tx + 9, ty - 44 + j * 40],
                              fill=col + (int(255 * aa),))
                carx, cary = x0 + 160, y0 + 220
                d.rounded_rectangle([carx - 60, cary - 18, carx + 60, cary + 18],
                                    radius=12, fill=(60, 80, 130, int(255 * aa)),
                                    outline=C_ZUPT + (int(255 * aa),), width=3)
                d.ellipse([carx - 38, cary + 10, carx - 14, cary + 34],
                          fill=(30, 42, 74, 255), outline=C_ZUPT + (int(255 * aa),), width=3)
                d.ellipse([carx + 14, cary + 10, carx + 38, cary + 34],
                          fill=(30, 42, 74, 255), outline=C_ZUPT + (int(255 * aa),), width=3)
                gfx.text_c(c, carx, cary + 56, 'خودرو پشت چراغ قرمز', 20, 'regular',
                           tuple(int(v * aa) for v in TXT_DIM))
            rows = [
                ('شرط سکون:', TXT, 38),
                ('|‖f‖ − g| < 0.05g و ‖ω < 3°/s', (34, 211, 238), 42),
                ('حداقل ۱ ثانیه (zuptHoldS)', TXT, 47),
                ('→ شبه‌سنجش: v = 0 با σ = 0.05 m/s', C_ZUPT, 52),
                ('دریفت INS عملاً صفر می‌ماند', C_OK, 58),
            ]
            yy = y0 + 74
            for s, col, ti in rows:
                aa = fade_in(t, ti, 0.7)
                if aa <= 0:
                    yy += 48
                    continue
                gfx.text(c, (x1 - 40, yy), s, 24, 'semibold',
                         tuple(int(v * aa) for v in col), 'right')
                yy += 48

        if t > 60:
            a = ease(seg(t, 60, 62))
            x0, y0, x1, y1 = 90, 440, 1020, 1030
            card(c, (x0, y0, x1, y1), '۳ — OOSM: اندازه‌گیری خارج از ترتیب', C_OOSM)
            ax0, ax1, ay = x0 + 70, x1 - 70, y0 + 120
            d = gfx.ImageDraw.Draw(c)
            d.line([(ax0, ay), (ax1, ay)], fill=(90, 108, 150, 255), width=3)
            gfx.text_c(c, ax1 + 24, ay, 't', 22, 'regular', TXT_FAINT, 'left')
            wx0, wx1 = ax0 + (ax1 - ax0) * 0.12, ax0 + (ax1 - ax0) * 0.85
            d.rounded_rectangle([wx0, ay - 34, wx1, ay + 34], radius=10,
                                fill=(251, 191, 36, int(40 * a)),
                                outline=C_OOSM + (int(180 * a),), width=2)
            gfx.text_c(c, (wx0 + wx1) / 2, ay - 58, 'پنجرهٔ fixed-lag = ۱۲ s',
                       21, 'semibold', tuple(int(v * a) for v in C_OOSM))
            tm = ax0 + (ax1 - ax0) * 0.30
            te = ax0 + (ax1 - ax0) * 0.92
            if t > 64:
                aa = fade_in(t, 64, 0.8)
                d.line([(tm, ay - 20), (tm, ay + 20)], fill=C_GNSS + (int(255 * aa),), width=3)
                gfx.text_c(c, tm, ay + 40, 'tMeas (در گذشته)', 20, 'semibold',
                           tuple(int(v * aa) for v in C_GNSS))
            if t > 70:
                aa = fade_in(t, 70, 0.8)
                d.line([(te, ay - 20), (te, ay + 20)], fill=C_INS + (int(255 * aa),), width=3)
                gfx.text_c(c, te, ay + 40, 'اکنون (تحویل دیرهنگام)', 20, 'semibold',
                           tuple(int(v * aa) for v in C_INS))
                gfx.arrow(d, (te - 10, ay - 44), (tm + 10, ay - 44),
                          (251, 191, 36, int(255 * aa)), 3, 12)
            if t > 78:
                rows = [
                    ('برگشت به epoch درست ← اعمال سنجش', 78),
                    ('بازگسترش قطعیِ همهٔ وضعیت‌های بعدی', 84),
                    ('ثبت در تاریخچه ← replay قطعی (مثل GNSS)', 90),
                ]
                yy = y0 + 210
                for s, ti in rows:
                    aaa = fade_in(t, ti, 0.7)
                    if aaa <= 0:
                        yy += 46
                        continue
                    gfx.text(c, (x1 - 40, yy), s, 24, 'semibold',
                             tuple(int(v * aaa) for v in TXT), 'right')
                    yy += 46
        if t > 100:
            a = fade_in(t, 100, 1)
            gfx.chip(c, 960, 1050, 'سه ابزار برای سه شکاف: عمودی / سکون / تأخیر',
                     C_BARO, size=26)
