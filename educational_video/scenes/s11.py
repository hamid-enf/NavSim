"""S11 — Error analysis: INS vs Fused, dropout numbers, bias learning."""
import math

import numpy as np

import gfx
from palette import (W, H, TXT, TXT_DIM, TXT_FAINT, C_INS, C_OK, C_BAD,
                     C_GNSS, C_WARN, C_EST)
from common import Scene, seg, ease, fade_in, header, card


def _fused_err(ts):
    base = 6 + 3 * np.sin(ts / 4) + 10 * np.exp(-ts / 6)
    out = np.empty_like(ts)
    for i, t_ in enumerate(ts):
        if t_ < 30:
            out[i] = base[i]
        elif t_ < 60:
            out[i] = base[i] + 24 * np.sin((t_ - 30) / 30 * math.pi / 2) ** 2 * 0.9
        else:
            tau = t_ - 60
            out[i] = 2 + (30 - 2) * np.exp(-tau / 3) + 2 * np.sin(ts[i] / 4)
    return out


class S11(Scene):
    name = 'S11'

    def draw(self, c, t):
        D = self.dur
        header(c, 'تحلیل خطا: INS در برابر Fused', C_OK, t)

        a = ease(seg(t, 1, 2.5))
        if a > 0:
            x0, y0, x1, y1 = 90, 160, 1240, 700
            gfx.panel(c, (x0, y0, x1, y1))
            gfx.text(c, (x1 - 24, y0 + 14),
                     'نرمِ خطای موقعیت (متر) — دو خط، کل داستان', 27, 'bold',
                     tuple(int(v * a) for v in TXT), 'right')
            p = gfx.Plot((x0 + 30, y0 + 50, x1 - 20, y1 - 40), 0, 120, 0, 1100,
                         pad=(60, 16, 40, 52))
            p.axes(c, tlabels=[0, 20, 40, 60, 80, 100, 120],
                   ylabels=[0, 250, 500, 750, 1000], xlabel='زمان [ثانیه]')
            d = gfx.ImageDraw.Draw(c)
            dx0, dx1 = p.X(30), p.X(60)
            d.rectangle([dx0, p.ax[1], dx1, p.ax[3]], fill=(251, 146, 60, 26))
            gfx.text_c(c, (dx0 + dx1) / 2, p.ax[1] + 12, 'قطعی GNSS ۳۰–۶۰s', 20,
                       'semibold', C_GNSS)
            ts = np.linspace(0, 120, 900)
            ins = 1012 * (ts / 120) ** 1.9
            fus = _fused_err(ts)
            pr = ease(seg(t, 2, 30))
            p.trace(c, ts, fus, C_OK, progress=pr, lw=5, fill_to=0, fill_alpha=45)
            p.trace(c, ts, ins, C_BAD, progress=pr, lw=5)
            gfx.dot(c, (x1 - 240, y0 + 34), 7, C_OK)
            gfx.text(c, (x1 - 224, y0 + 24), 'Fused', 22, 'semibold', C_OK, 'left')
            gfx.dot(c, (x1 - 120, y0 + 34), 7, C_BAD)
            gfx.text(c, (x1 - 104, y0 + 24), 'INS خالص', 22, 'semibold', C_BAD, 'left')
        if t > 34:
            a = ease(seg(t, 34, 36))
            x0, y0, x1, y1 = 1280, 160, 1830, 700
            card(c, (x0, y0, x1, y1), 'اعداد مرجع ریپوزیتری', C_WARN)
            stats = [
                ('در دل قطعی:', TXT, 38),
                ('Fused: ≈ ۳۰ m', C_WARN, 42),
                ('INS: ≈ ۱۰۱۲ m', C_BAD, 46),
                ('پس از بازگشت:', TXT, 54),
                ('Fused: ≈ ۱٫۹ m', C_OK, 58),
                ('در چند ثانیه!', C_OK, 62),
            ]
            yy = y0 + 80
            for s, col, ti in stats:
                aa = fade_in(t, ti, 0.7)
                if aa <= 0:
                    yy += 54
                    continue
                gfx.text(c, (x1 - 36, yy), s, 26, 'bold' if col != TXT else 'regular',
                         tuple(int(v * aa) for v in col), 'right')
                yy += 54
        if t > 64:
            a = ease(seg(t, 64, 66))
            x0, y0, x1, y1 = 90, 740, 1830, 1040
            gfx.panel(c, (x0, y0, x1, y1))
            gfx.text(c, (x1 - 24, y0 + 12),
                     'آزمایش ۲: فیلتر بایاس ژیرو را می‌آموزد', 26, 'bold',
                     tuple(int(v * a) for v in TXT), 'right')
            ax0, ax1, ay = x0 + 80, x1 - 80, y0 + 120
            d = gfx.ImageDraw.Draw(c)
            d.line([(ax0, ay), (ax1, ay)], fill=(90, 108, 150, 255), width=3)
            truth = ax0 + (ax1 - ax0) * 0.42
            est = ax0 + (ax1 - ax0) * (0.42 + 0.30 * math.exp(-(t - 66) / 14)) if t > 66 else ax0 + (ax1 - ax0) * 0.72
            d.line([(truth, ay - 40), (truth, ay + 40)], fill=C_OK + (int(255 * a),), width=3)
            gfx.text_c(c, truth, ay + 56, 'بایاس واقعی', 20, 'semibold',
                       tuple(int(v * a) for v in C_OK))
            d.ellipse([est - 9, ay - 9, est + 9, ay + 9], fill=C_INS + (int(255 * a),))
            gfx.text_c(c, est, ay - 26, 'calBg (تخمین)', 20, 'semibold',
                       tuple(int(v * a) for v in C_INS))
            gfx.text_c(c, (ax0 + ax1) / 2, y1 - 30,
                       'بعد از ۱۲۰s مانور: تخمین ≈ [۰٫۵۱ ، −۰٫۳۱ ، ۰٫۱۳] در برابر واقعی [۱ ، −۰٫۷ ، ۰٫۵] °/s',
                       23, 'semibold', tuple(int(v * a) for v in TXT_DIM))
        if t > 80:
            a = fade_in(t, 80, 1)
            gfx.chip(c, 960, 1055, 'فیلتر فقط تصحیح نمی‌کند؛ یاد می‌گیرد',
                     C_OK, size=28)
