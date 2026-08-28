"""S14 — GUI, experiments, logging."""
import math

import gfx
from palette import (W, H, TXT, TXT_DIM, TXT_FAINT, C_INS, C_GNSS, C_FUSION,
                     C_OK, C_WARN, C_BAD, C_EST, C_CALIB, C_TRAJ)
from common import Scene, seg, ease, fade_in, header, card

TABS = ['Simulation', 'Trajectory', 'IMU', 'GNSS', 'Baro', 'INS & Align',
        'Fusion', 'Errors']
EXPS = [
    ('۱', 'IMU بی‌خطا', 'اعتبارسنجی سیستم', 72),
    ('۲', 'فقط بایاس ژیرو', 'تخمین بایاس را ببینید', 77),
    ('۶', 'قطعی GNSS', 'رشد σ + بازگشت', 82),
    ('۷', 'خطای تراز', 'درسِ قابل‌مشاهده‌شدن', 87),
    ('۸', 'INS در برابر GNSS/INS', 'مقایسهٔ خودکار + جدول آماری', 92),
]


class S14(Scene):
    name = 'S14'

    def draw(self, c, t):
        D = self.dur
        header(c, 'در عمل: GUI ، آزمایش‌ها، لاگینگ', C_INS, t)

        a = ease(seg(t, 1, 2.5))
        if a > 0:
            x0, y0, x1, y1 = 90, 160, 1830, 850
            gfx.panel(c, (x0, y0, x1, y1))
            d = gfx.ImageDraw.Draw(c)
            d.rounded_rectangle([x0, y0, x1, y0 + 46], radius=18,
                                fill=(30, 42, 74, 255))
            d.ellipse([x1 - 34, y0 + 14, x1 - 14, y0 + 34], fill=C_BAD + (255,))
            d.ellipse([x1 - 62, y0 + 14, x1 - 42, y0 + 34], fill=C_WARN + (255,))
            d.ellipse([x1 - 90, y0 + 14, x1 - 70, y0 + 34], fill=C_OK + (255,))
            gfx.text(c, (x1 - 110, y0 + 10), 'NavSim — uifigure', 22, 'semibold',
                     TXT_DIM, 'right')
            lx0 = x0 + 20
            gfx.text_c(c, lx0 + 180, y0 + 78, 'تب‌های پارامتر (Runtime-safe)', 24,
                       'bold', tuple(int(v * a) for v in TXT))
            for i, tab in enumerate(TABS):
                ti = 4 + i * 2.2
                aa = fade_in(t, ti, 0.7)
                if aa <= 0:
                    continue
                col = C_BAD if tab == 'Errors' else (C_EST if tab in ('IMU', 'GNSS') else C_INS)
                y = y0 + 120 + i * 72
                gfx.chip(c, lx0 + 180, y, tab, col, size=22, pad_x=20, pad_y=10,
                         label_color=TXT)
                if tab == 'Errors' and t > 26:
                    aaa = fade_in(t, 26, 0.8)
                    gfx.text(c, (lx0 + 360, y - 34),
                             'همهٔ سوئیچ‌های خطا در یک صفحه', 19, 'regular',
                             tuple(int(v * aaa) for v in C_BAD), 'right')
            if t > 35:
                aa = fade_in(t, 35, 0.8)
                btns = ['Start', 'Pause', 'Stop', 'Reset', 'Step']
                for j, b in enumerate(btns):
                    xx = 1000 - j * 130
                    yy = y0 + 120
                    col = C_OK if b == 'Start' else (C_WARN if b in ('Stop', 'Reset') else C_INS)
                    gfx.chip(c, xx, yy, b, col, size=21, pad_x=18, pad_y=9,
                             label_color=TXT)
                gfx.text(c, (1055, y0 + 170), 'Step: تدریس گام‌به‌گام', 20,
                         'semibold', tuple(int(v * aa) for v in C_WARN), 'right')
                gfx.text(c, (1055, y0 + 204), 'سرعت ۰٫۱× تا ۲۰×  —  real-time / fast',
                         20, 'regular', tuple(int(v * aa) for v in TXT_DIM), 'right')
            rx0 = 620
            gfx.text_c(c, (rx0 + 1105 + 30) / 2, y0 + 78, 'نمایش‌ها', 24, 'bold',
                       tuple(int(v * a) for v in TXT))
            px0, py0, px1, py1 = rx0 + 30, y0 + 110, rx0 + 560, y0 + 430
            d.rounded_rectangle([px0, py0, px1, py1], radius=12,
                                fill=(20, 30, 56, 255), outline=(60, 78, 130, 255), width=2)
            import numpy as np
            ts = np.linspace(0, 1, 120)
            fus = 6 + 4 * np.sin(ts * 9) + 8 * np.exp(-ts * 12)
            ins = 120 * ts ** 2
            pts1 = [(px0 + 10 + (px1 - px0 - 20) * x, py1 - 12 - (py1 - py0 - 24) * (y / 130))
                    for x, y in zip(ts, ins)]
            pts2 = [(px0 + 10 + (px1 - px0 - 20) * x, py1 - 12 - (py1 - py0 - 24) * (y / 130))
                    for x, y in zip(ts, fus)]
            d.line(pts1, fill=C_BAD + (255,), width=3)
            d.line(pts2, fill=C_OK + (255,), width=3)
            gfx.text_c(c, (px0 + px1) / 2, py0 + 16, 'Position / Velocity / Attitude / Errors / Sensors',
                       17, 'semibold', TXT_DIM)
            qx0, qy0, qx1, qy1 = rx0 + 590, y0 + 110, rx0 + 850, y0 + 430
            d.rounded_rectangle([qx0, qy0, qx1, qy1], radius=12,
                                fill=(20, 30, 56, 255), outline=(60, 78, 130, 255), width=2)
            cx, cy = (qx0 + qx1) / 2, (qy0 + qy1) / 2
            d.ellipse([cx - 120, cy - 100, cx + 120, cy + 100],
                      outline=(148, 163, 184, 120), width=2)
            ang = (t * 0.6) % (2 * math.pi)
            vx, vy = cx + 120 * math.cos(ang), cy - 100 * math.sin(ang)
            d.ellipse([vx - 8, vy - 8, vx + 8, vy + 8], fill=C_INS + (255,))
            gfx.text_c(c, (qx0 + qx1) / 2, qy0 + 16, '3D View', 17, 'semibold', TXT_DIM)
            fx0, fy0 = rx0 + 880, y0 + 110
            for i, st in enumerate(['TRUTH', 'IMU', 'INS', 'GNSS', 'FUSED']):
                y = fy0 + i * 62
                col = C_TRAJ if st == 'TRUTH' else C_INS if st == 'INS' else C_GNSS if st == 'GNSS' else C_OK
                gfx.soft_rrect(c, (fx0, y, fx0 + 250, y + 48), 10,
                               fill=(20, 30, 56, 255), outline=col + (160,), width=2)
                gfx.text_c(c, fx0 + 125, y + 6, st, 17, 'semibold', col)
                val = f'{3 + i * 7.3 + 0.1 * math.sin(t * 2 + i):.2f}'
                gfx.text_c(c, fx0 + 125, y + 26, val, 17, 'regular', TXT_DIM)
            gfx.text_c(c, (rx0 + 30 + 1105) / 2, y0 + 470, 'Data Flow: مقادیر زندهٔ هر مرحله',
                       20, 'semibold', C_EST)
            if t > 50:
                aa = fade_in(t, 50, 0.8)
                d.rounded_rectangle([rx0 + 30, y0 + 500, rx0 + 1105, y0 + 720],
                                    radius=12, fill=(24, 35, 66, int(220 * aa)),
                                    outline=C_EST + (int(200 * aa),), width=2)
                gfx.text_c(c, (rx0 + 30 + 1105) / 2, y0 + 528,
                           'روی هر مرحله کلیک کنید ← پنل آموزشی: چیست؟ ورودی/خروجی؟ معادله؟ خطاها؟',
                           23, 'semibold', tuple(int(v * aa) for v in C_EST))
        if t > 70:
            a = fade_in(t, 70, 0.8)
            gfx.text(c, (1830, 880), '۱۰ آزمایش آماده = یک مسیر یادگیری', 27, 'bold',
                     tuple(int(v * a) for v in TXT), 'right')
            for i, (num, name, why, ti) in enumerate(EXPS):
                aa = ease(seg(t, ti, ti + 0.9))
                if aa <= 0:
                    continue
                x = 1740 - i * 330
                x0, y0, x1, y1 = x - 150, 920, x + 150, 1030
                gfx.soft_rrect(c, (x0, y0, x1, y1), 12, fill=(19, 28, 51, int(230 * aa)),
                               outline=C_WARN + (int(180 * aa),), width=2)
                gfx.text_c(c, (x0 + x1) / 2, y0 + 14, f'Exp {num}', 21, 'bold',
                           tuple(int(v * aa) for v in C_WARN))
                gfx.text_c(c, (x0 + x1) / 2, y0 + 52, name, 21, 'semibold',
                           tuple(int(v * aa) for v in TXT))
                gfx.text_c(c, (x0 + x1) / 2, y0 + 86, why, 18, 'regular',
                           tuple(int(v * aa) for v in TXT_DIM))
        if t > 96:
            a = fade_in(t, 96, 1)
            gfx.chip(c, 1330, 1058, 'لاگینگ: MAT / CSV + بازپخش انیمیشنی', C_EST,
                     size=23, label_color=TXT)
            gfx.chip(c, 640, 1058, 'runAllTests: ۱۴ تست اعتبارسنجی', C_OK, size=23,
                     label_color=TXT)
