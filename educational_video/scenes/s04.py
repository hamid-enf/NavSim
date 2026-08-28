"""S04 — IMU error model."""
import math
import numpy as np

import gfx
from palette import (W, H, TXT, TXT_DIM, TXT_FAINT, C_IMU, C_INS, C_WARN,
                     C_OK, C_BAD, C_CALIB)
from common import Scene, seg, ease, fade_in, header, card


class S04(Scene):
    name = 'S04'

    def draw(self, c, t):
        D = self.dur
        header(c, 'مدل IMU: ژیرو + شتاب‌سنج', C_IMU, t)

        a = ease(seg(t, 1, 2.5))
        if a > 0:
            gfx.panel(c, (460, 150, 1460, 260))
            gfx.text_c(c, 960, 180, 'meas = M · true + bias + noise', 44, 'black',
                       tuple(int(v * a) for v in (251, 191, 36)))
            gfx.text_c(c, 960, 236, 'اندازه‌گیری = ماتریس خطا × واقعی + بایاس + نویز', 24,
                       'regular', tuple(int(v * a) for v in TXT_DIM))
        a = ease(seg(t, 9, 11))
        if a > 0:
            x0, y0, x1, y1 = 90, 300, 880, 590
            card(c, (x0, y0, x1, y1), 'M: دو اثرِ سیستماتیک', C_IMU)
            cx, cy = 300, 470
            d = gfx.ImageDraw.Draw(c)
            d.line([(cx - 70, cy), (cx + 70, cy)], fill=(148, 163, 184, 255), width=3)
            ang = math.radians(3)
            d.line([(cx, cy), (cx + 120 * math.cos(ang), cy - 120 * math.sin(ang))],
                   fill=C_IMU + (255,), width=3)
            gfx.text_c(c, cx + 40, cy - 30, 'δ', 26, 'bold', C_IMU)
            gfx.text(c, (x1 - 30, 380), 'کج‌بودن محورها', 26, 'bold', TXT, 'right')
            gfx.text(c, (x1 - 30, 420), 'محورهای سنسور دقیقاً عمود نیستند', 22, 'regular',
                     TXT_DIM, 'right')
            gfx.text(c, (x1 - 30, 470), 'misalignment [deg]', 24, 'semibold', C_IMU,
                     'right')
            gfx.text(c, (x1 - 30, 530), 'ضریب مقیاس: ژیرو ۵۰ppm', 26, 'bold', TXT, 'right')
            gfx.text(c, (x1 - 30, 566), 'یعنی ۰٫۰۰۵٪ بیشتر می‌سنجد [ppm]', 22, 'regular',
                     TXT_DIM, 'right')
        a = ease(seg(t, 20, 22))
        if a > 0:
            x0, y0, x1, y1 = 90, 620, 880, 860
            card(c, (x0, y0, x1, y1), 'بایاس ثابت ژیرو', C_WARN)
            d = gfx.ImageDraw.Draw(c)
            gfx.text(c, (x1 - 30, y0 + 66), 'bias = 0.02 °/s  ←  کوچک به نظر می‌رسد',
                     25, 'semibold', TXT, 'right')
            p = ease(seg(t, 24, 34))
            ang = math.radians(1.2 * p)
            bx, by = 250, 800
            d.line([(bx - 90, by), (bx + 90, by)], fill=(148, 163, 184, 255), width=3)
            d.line([(bx, by), (bx + 130 * math.cos(ang), by - 130 * math.sin(ang))],
                   fill=C_WARN + (255,), width=4)
            d.arc([bx - 40, by - 40, bx + 40, by], start=math.degrees(-ang), end=0,
                  fill=C_WARN + (255,), width=3)
            val = 1.2 * p
            gfx.text_c(c, bx + 160, by - 60, f'{val:.2f}°', 34, 'black', C_WARN)
            gfx.text(c, (x1 - 30, 800), 'پس از ۱ دقیقه: ۱٫۲° خطای وضعیت', 25, 'semibold',
                     C_WARN, 'right')
        a = ease(seg(t, 30, 32))
        if a > 0:
            x0, y0, x1, y1 = 970, 290, 1830, 700
            card(c, (x0, y0, x1, y1), 'نویز به‌صورت چگالی (PSD)', C_INS)
            rng = np.random.default_rng(3)
            n = 200
            ts = np.linspace(0, 1, n)
            arw = np.cumsum(rng.normal(0, 1, n)) * 0.02
            arw -= arw.mean()
            gx0, gy0, gx1, gy1 = x0 + 40, y0 + 80, x0 + 420, y0 + 210
            d = gfx.ImageDraw.Draw(c)
            true = np.zeros(n)
            meas = true + arw / arw.max() * 0.45
            pts = [(gx0 + (gx1 - gx0) * x, gy1 - (gy1 - gy0) * (y + 0.5))
                   for x, y in zip(ts, meas)]
            d.line([(gx0, (gy0 + gy1) / 2), (gx1, (gy0 + gy1) / 2)],
                   fill=(90, 108, 150, 255), width=2)
            d.line(pts, fill=C_IMU + (255,), width=2)
            gfx.text_c(c, (gx0 + gx1) / 2, gy0 - 14, 'ژیرو: ARW = 0.01 °/s/√Hz', 22,
                       'semibold', C_IMU)
            ax0, ay0, ax1, ay1 = x0 + 470, y0 + 80, x0 + 850, y0 + 210
            vrw = np.cumsum(rng.normal(0, 1, n)) * 0.02
            vrw -= vrw.mean()
            meas2 = vrw / vrw.max() * 0.45
            pts2 = [(ax0 + (ax1 - ax0) * x, ay1 - (ay1 - ay0) * (y + 0.5))
                    for x, y in zip(ts, meas2)]
            d.line([(ax0, (ay0 + ay1) / 2), (ax1, (ay0 + ay1) / 2)],
                   fill=(90, 108, 150, 255), width=2)
            d.line(pts2, fill=C_INS + (255,), width=2)
            gfx.text_c(c, (ax0 + ax1) / 2, ay0 - 14, 'شتاب‌سنج: VRW = 0.02 m/s/√Hz', 22,
                       'semibold', C_INS)
            a2 = fade_in(t, 38, 1)
            if a2 > 0:
                gfx.text(c, (1790, y0 + 255), 'σ_نمونه = چگالی / √dt', 32, 'black',
                         tuple(int(v * a2) for v in (251, 191, 36)), 'right')
                gfx.text(c, (1790, y0 + 305),
                         'توان نویز در هر ثانیه ثابت است — dt ریزتر، نویز هر نمونه کمتر',
                         23, 'regular', tuple(int(v * a2) for v in TXT_DIM), 'right')
        a = ease(seg(t, 48, 50))
        if a > 0:
            x0, y0, x1, y1 = 970, 740, 1830, 1060
            card(c, (x0, y0, x1, y1), 'بایاس: فقط ثابت نیست', C_CALIB)
            rng = np.random.default_rng(11)
            d = gfx.ImageDraw.Draw(c)
            n = 120
            ts = np.linspace(0, 1, n)
            rw = np.cumsum(rng.normal(0, 1, n)) * 0.01
            gm = np.zeros(n)
            x = 0
            for i in range(n):
                x = math.exp(-1 / 60) * x + 0.004 * rng.normal()
                gm[i] = x
            gx0, gy0 = x0 + 40, y0 + 90
            gw, gh = 400, 130
            pts = [(gx0 + gw * t_, gy0 + gh - (rw[i] - rw.min()) / (np.ptp(rw) + 1e-9) * gh)
                   for i, t_ in enumerate(ts)]
            d.line(pts, fill=C_IMU + (255,), width=2)
            gfx.text_c(c, gx0 + gw / 2, y0 + 60, 'random walk', 22, 'semibold', C_IMU)
            ax0 = x0 + 480
            pts2 = [(ax0 + gw * t_, gy0 + gh - (gm[i] - gm.min()) / (np.ptp(gm) + 1e-9) * gh)
                    for i, t_ in enumerate(ts)]
            d.line(pts2, fill=C_CALIB + (255,), width=2)
            gfx.text_c(c, ax0 + gw / 2, y0 + 60, 'Gauss–Markov (τ = 1 s)', 22,
                       'semibold', C_CALIB)
        if t > 62:
            items = [
                ('g-sensitivity', 'ژیرو به شتاب هم واکنش دارد', C_WARN, 62),
                ('saturation', 'سقف: ۴۰۰°/s ژیرو، ۲۰g شتاب‌سنج', C_BAD, 67),
                ('quantization', 'کوانتیزاسیون دیجیتال خروجی', C_INS, 72),
            ]
            for i, (en, fa, col, ti) in enumerate(items):
                a = ease(seg(t, ti, ti + 0.8))
                if a <= 0:
                    continue
                x = 480 + i * 460
                d = gfx.ImageDraw.Draw(c)
                gfx.soft_rrect(c, (x - 215, 995, x + 215, 1068), 14,
                               fill=(24, 35, 66, int(220 * a)),
                               outline=col + (int(220 * a),), width=2)
                gfx.text_c(c, x, 1012, en, 22, 'semibold',
                           tuple(int(v * a) for v in col))
                gfx.text_c(c, x, 1042, fa, 20, 'regular',
                           tuple(int(v * a) for v in TXT))
        a = fade_in(t, 78, 1)
        if a > 0:
            gfx.glow(c, (490, 930), 70, C_IMU, int(60 * a))
            gfx.chip(c, 490, 930, 'dt = 0.01 s  →  100 Hz', C_IMU, size=28)
            gfx.text_c(c, 490, 990, 'نرخ واقعی IMUهای تاکتیکی', 22, 'regular',
                       tuple(int(v * a) for v in TXT_DIM))
