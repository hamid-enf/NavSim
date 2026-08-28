"""S08 — 15-state error-state EKF: prediction."""
import math
import numpy as np

import gfx
from palette import (W, H, TXT, TXT_DIM, TXT_FAINT, C_PRED, C_INS, C_WARN,
                     C_OK, C_EST, C_CALIB, C_BAD)
from common import Scene, seg, ease, fade_in, header, card

BLOCKS = [
    ('خطای موقعیت', 'δp', C_EST, 10),
    ('خطای سرعت', 'δv', C_INS, 13),
    ('خطای وضعیت', 'δφ', C_PRED, 16),
    ('بایاس ژیرو', 'δbg', C_WARN, 19),
    ('بایاس شتاب‌سنج', 'δba', C_CALIB, 22),
]


class S08(Scene):
    name = 'S08'

    def draw(self, c, t):
        D = self.dur
        header(c, 'فیلتر EKF: پانزده حالت خطا', C_PRED, t)
        a = fade_in(t, 3, 1)
        if a > 0:
            gfx.chip(c, 1620, 165, 'قرارداد: خطا = واقعی − تخمین', C_PRED, size=24)

        for i, (name, sym, col, ti) in enumerate(BLOCKS):
            aa = ease(seg(t, ti, ti + 1))
            if aa <= 0:
                continue
            x = 1740 - i * 330
            x0, y0, x1, y1 = x - 150, 200, x + 150, 380
            gfx.soft_rrect(c, (x0, y0, x1, y1), 14,
                           fill=(19, 28, 51, int(230 * aa)),
                           outline=col + (int(200 * aa),), width=3)
            gfx.text_c(c, (x0 + x1) / 2, y0 + 22, name, 24, 'bold',
                       tuple(int(v * aa) for v in TXT))
            for j in range(3):
                d = gfx.ImageDraw.Draw(c)
                d.rounded_rectangle([x0 + 20 + j * 80, y0 + 66, x0 + 88 + j * 80,
                                     y0 + 108], radius=8,
                                    fill=col + (int(90 * aa),))
                gfx.text_c(c, x0 + 60 + j * 80, y0 + 72, f'{sym}_{[0, 1, 2][j]}',
                           18, 'semibold', tuple(int(v * aa) for v in col))
            gfx.text_c(c, (x0 + x1) / 2, y0 + 128, '۳ × N/E/D', 20, 'regular',
                       tuple(int(v * aa) for v in TXT_FAINT))
            if i < 4:
                d = gfx.ImageDraw.Draw(c)
                gfx.arrow(d, (x0 - 8, y0 + 90), (x0 - 30, y0 + 90),
                          (96, 116, 160), 3, 10)
        if t > 26:
            aa = fade_in(t, 26, 0.8)
            gfx.text_c(c, 960, 405, 'مجموع: ۱۵ حالت  ←  EKF خطای‌حالتی', 26, 'semibold',
                       tuple(int(v * aa) for v in TXT))

        # ---------- error dynamics (left) ----------
        if t > 30:
            a = ease(seg(t, 30, 32))
            x0, y0, x1, y1 = 90, 450, 1020, 760
            card(c, (x0, y0, x1, y1), 'پیش‌بینی ۱: گسترش خطا', C_PRED)
            rows = [
                ('δv̇ = [f]×δφ − C·δba', 33),
                ('δφ̇ = −[ω_in]×δφ + C·δbg', 40),
                ('δḃg = n_g ، δḃa = n_a   (random walk)', 47),
            ]
            yy = y0 + 74
            for s, ti in rows:
                aa = fade_in(t, ti, 0.8)
                if aa > 0:
                    gfx.text(c, (x1 - 40, yy), s, 27, 'semibold',
                             tuple(int(v * aa) for v in (34, 211, 238)), 'right')
                yy += 52
            aa = fade_in(t, 52, 0.8)
            if aa > 0:
                gfx.text(c, (x1 - 40, yy + 10),
                         'خطای وضعیت، نیروی ویژه را می‌چرخاند → به سرعت می‌رسد',
                         21, 'regular', tuple(int(v * aa) for v in TXT_DIM), 'right')

        # ---------- P propagation (right) ----------
        if t > 55:
            a = ease(seg(t, 55, 57))
            x0, y0, x1, y1 = 1060, 450, 1830, 760
            card(c, (x0, y0, x1, y1), 'پیش‌بینی ۲: گسترش کوواریانس', C_WARN)
            aa = fade_in(t, 58, 0.8)
            if aa > 0:
                gfx.text_c(c, (x0 + x1) / 2, y0 + 70, 'P ← F·P·Fᵀ + Q', 40, 'black',
                           tuple(int(v * aa) for v in (251, 191, 36)))
            rows = [
                ('Q: نویز پروس — «اعتماد به مدل»', 62),
                ('qa = 0.005 m/s²/√Hz (شتاب‌سنج)', 66),
                ('qg = 0.02 °/s/√Hz (ژیرو)', 70),
            ]
            yy = y0 + 120
            for s, ti in rows:
                aa = fade_in(t, ti, 0.8)
                if aa > 0:
                    gfx.text(c, (x1 - 40, yy), s, 24, 'semibold',
                             tuple(int(v * aa) for v in TXT), 'right')
                yy += 46

        # ---------- P0 (bottom left) ----------
        if t > 72:
            a = ease(seg(t, 72, 74))
            x0, y0, x1, y1 = 90, 800, 1020, 1030
            card(c, (x0, y0, x1, y1), 'P صفر: باید کیفیت تراز اولیه را بازتاب کند', C_EST)
            items = [
                ('موقعیت: ۵ m', 75), ('سرعت: ۰٫۱ m/s', 78),
                ('وضعیت: ۵°', 81), ('بایاس ژیرو: ۰٫۱ °/s', 84),
                ('بایاس شتاب‌سنج: ۰٫۳ m/s²', 87),
            ]
            for i, (s, ti) in enumerate(items):
                aa = fade_in(t, ti, 0.6)
                if aa <= 0:
                    continue
                x = x1 - 40 - (i % 3) * 300
                y = y0 + 80 + (i // 3) * 60
                gfx.chip(c, x - 130, y, s, C_EST, size=21, pad_x=16, pad_y=8)

        # ---------- P growth without GNSS (bottom right) ----------
        if t > 95:
            a = ease(seg(t, 95, 97))
            x0, y0, x1, y1 = 1060, 800, 1830, 1030
            gfx.panel(c, (x0, y0, x1, y1))
            gfx.text(c, (x1 - 24, y0 + 12), 'بدون GNSS: P بی‌رحمانه رشد می‌کند', 24, 'bold',
                     tuple(int(v * a) for v in C_BAD), 'right')
            p = gfx.Plot((x0 + 10, y0 + 34, x1 - 10, y1 - 14), 0, 120, 0, 1,
                         pad=(30, 6, 20, 26))
            p.axes(c, tlabels=[0, 60, 120])
            ts = np.linspace(0, 120, 300)
            sig = 0.06 + 0.9 * (ts / 120) ** 1.6
            pr = ease(seg(t, 96, 106))
            p.trace(c, ts, sig, C_BAD, progress=pr, lw=4, fill_to=0, fill_alpha=50)
            gfx.text_c(c, (x0 + x1) / 2, y1 + 14, 'σ فیلتر در Data Flow زنده دیده می‌شود',
                       19, 'regular', TXT_DIM)
