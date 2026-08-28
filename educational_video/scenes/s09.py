"""S09 — Fusion: measurement update, K as trust split, NIS gating."""
import math
import numpy as np

import gfx
from palette import (W, H, TXT, TXT_DIM, TXT_FAINT, C_FUSION, C_GNSS, C_INS,
                     C_WARN, C_BAD, C_OK, C_PRED)
from common import Scene, seg, ease, fade_in, header, card

CHAIN = [
    ('نویشن (باقیمانده)', 'ν = z − p', 8),
    ('کوواریانس باقیمانده', 'S = HPHᵀ + R', 26),
    ('کسیر کالمن', 'K = PHᵀS¹', 42),
    ('تصحیح خطای حالت', 'dx ← dx + K·ν', 60),
    ('حلقهٔ فیدبک', 'تصحیح + بایاس', 76),
]


class S09(Scene):
    name = 'S09'

    def draw(self, c, t):
        D = self.dur
        header(c, 'فیوژن: قلبِ تصحیح', C_FUSION, t)

        for i, (title, eq, ti) in enumerate(CHAIN):
            aa = ease(seg(t, ti, ti + 1.2))
            if aa <= 0:
                continue
            x = 1700 - i * 330
            x0, y0, x1, y1 = x - 150, 180, x + 150, 300
            active = (i == self._active(t))
            gfx.soft_rrect(c, (x0, y0, x1, y1), 14,
                           fill=(19, 28, 51, int(235 * aa)),
                           outline=C_FUSION if active else (60, 78, 130),
                           width=4 if active else 2)
            if active:
                gfx.glow(c, ((x0 + x1) / 2, (y0 + y1) / 2), 90, C_FUSION, 70)
            gfx.text_c(c, (x0 + x1) / 2, y0 + 18, title, 22, 'bold',
                       tuple(int(v * aa) for v in (TXT if not active else C_FUSION)))
            gfx.text_c(c, (x0 + x1) / 2, y0 + 62, eq, 21, 'semibold',
                       tuple(int(v * aa) for v in (34, 211, 238)))
            if i < 4:
                d = gfx.ImageDraw.Draw(c)
                gfx.arrow(d, (x0 - 8, y0 + 60), (x0 - 30, y0 + 60),
                          (96, 116, 160), 3, 10)

        idx = self._active(t)
        if idx >= 0:
            ti = CHAIN[idx][2]
            a = ease(seg(t, ti + 0.4, ti + 1.4))
            x0, y0, x1, y1 = 90, 340, 1830, 560
            gfx.panel(c, (x0, y0, x1, y1))
            d = gfx.ImageDraw.Draw(c)
            d.rounded_rectangle([x1 - 8, y0 + 14, x1, y1 - 14], radius=4,
                                fill=C_FUSION + (int(255 * a),))
            gfx.text(c, (x1 - 36, y0 + 20), f'مرحلهٔ {["یک", "دو", "سه", "چهار", "پنج"][idx]}: {CHAIN[idx][0]}',
                     28, 'bold', tuple(int(v * a) for v in C_FUSION), 'right')
            desc = self._detail(idx)
            yy = y0 + 78
            for line, col in desc:
                aa = fade_in(t, ti + 0.7 + (yy - (y0 + 78)) / 55.0 * 0.4, 0.7)
                if aa > 0:
                    gfx.text(c, (x1 - 40, yy), line, 26, 'semibold',
                             tuple(int(v * aa) for v in col), 'right')
                yy += 55

        if t > 44:
            a = ease(seg(t, 44, 46))
            x0, y0, x1, y1 = 90, 600, 1020, 1020
            gfx.panel(c, (x0, y0, x1, y1))
            gfx.text(c, (x1 - 24, y0 + 12), 'K = تقسیمِ اعتماد: P در برابر R', 26, 'bold',
                     tuple(int(v * a) for v in TXT), 'right')
            phase = 0 if t < 56 else 1
            p_val = 0.25 if phase == 0 else 0.85
            r_val = 0.5
            p_val += 0.04 * math.sin(t * 2)
            bx = x1 - 320
            bh = 250
            for (xx, val, col, lab) in [(bx, r_val, C_GNSS, 'R (اعتماد به سنسور)'),
                                        (bx - 200, p_val, C_INS, 'P (اعتماد به INS)')]:
                d = gfx.ImageDraw.Draw(c)
                d.rounded_rectangle([xx, y0 + 60, xx + 120, y0 + 60 + bh], radius=10,
                                    fill=(30, 42, 74, 255))
                h = bh * val
                d.rounded_rectangle([xx, y0 + 60 + bh - h, xx + 120, y0 + 60 + bh],
                                    radius=10, fill=col + (255,))
                gfx.text_c(c, xx + 60, y0 + 60 + bh + 16, lab, 20, 'semibold', col)
            k_val = p_val / (p_val + r_val)
            kx0, kx1 = x0 + 120, x0 + 320
            ky = y0 + 140
            d = gfx.ImageDraw.Draw(c)
            d.rounded_rectangle([kx0, ky, kx1, ky + 46], radius=10,
                                fill=(30, 42, 74, 255))
            d.rounded_rectangle([kx0, ky, kx0 + (kx1 - kx0) * k_val, ky + 46],
                                radius=10, fill=C_FUSION + (255,))
            gfx.text_c(c, (kx0 + kx1) / 2, ky - 24, f'K = {k_val:.2f}', 26, 'black',
                       C_FUSION)
            msg = ('P کوچک ← K کوچک: تصحیح کم' if phase == 0
                   else 'P بزرگ ← K بزرگ: نزدیک شدن به GNSS')
            mc = C_OK if phase == 0 else C_WARN
            gfx.text_c(c, (x0 + x1) / 2, y1 - 40, msg, 24, 'semibold',
                       tuple(int(v * a) for v in mc))

        if t > 96:
            a = ease(seg(t, 96, 98))
            x0, y0, x1, y1 = 1060, 600, 1830, 1020
            gfx.panel(c, (x0, y0, x1, y1))
            gfx.text(c, (x1 - 24, y0 + 12), 'robustness: آزمون NIS (کای-دو)', 26, 'bold',
                     tuple(int(v * a) for v in TXT), 'right')
            ax0, ax1, ay = x0 + 70, x1 - 70, y0 + 150
            d = gfx.ImageDraw.Draw(c)
            d.line([(ax0, ay), (ax1, ay)], fill=(90, 108, 150, 255), width=3)
            gx = ax0 + (ax1 - ax0) * (16.27 / 25)
            gfx.line(d, (gx, ay - 46), (gx, ay + 46), C_WARN + (int(255 * a),), width=3, dash=8)
            gfx.text_c(c, gx, ay + 62, 'آستانه: ۱۶٫۲۷ (۹۹/۹٪، ۳ د.ا.)', 20, 'semibold',
                       tuple(int(v * a) for v in C_WARN))
            rng = np.random.default_rng(9)
            vals = [rng.uniform(1, 9) for _ in range(12)] + [21.5]
            for i, v in enumerate(vals):
                tt = 98 + i * 1.2
                aa = fade_in(t, tt, 0.6)
                if aa <= 0:
                    continue
                px = ax0 + (ax1 - ax0) * (v / 25)
                is_out = v > 16.27
                if is_out:
                    d.line([(px - 12, ay - 18), (px + 12, ay + 18)],
                           fill=C_BAD + (int(255 * aa),), width=4)
                    d.line([(px - 12, ay + 18), (px + 12, ay - 18)],
                           fill=C_BAD + (int(255 * aa),), width=4)
                    d.ellipse([px - 5, ay - 5, px + 5, ay + 5],
                              fill=C_BAD + (int(255 * aa),))
                else:
                    d.ellipse([px - 6, ay - 6, px + 6, ay + 6],
                              fill=C_OK + (int(255 * aa),))
            if t > 112:
                aa = fade_in(t, 112, 0.8)
                gfx.text(c, (x1 - 40, y0 + 250),
                         'پرت‌های ۵۰m، پیش از آلوده‌کردن فیلتر رد می‌شوند',
                         22, 'semibold', tuple(int(v * aa) for v in C_BAD), 'right')
                gfx.text(c, (x1 - 40, y0 + 296),
                         'حالت adaptive: به‌جای رد، R تا ۱۰۰ برابر باد می‌شود',
                         22, 'regular', tuple(int(v * aa) for v in TXT_DIM), 'right')

    @staticmethod
    def _active(t):
        idx = -1
        for i, (_, _, ti) in enumerate(CHAIN):
            if t >= ti:
                idx = i
        return idx

    @staticmethod
    def _detail(idx):
        if idx == 0:
            return [('ν = z_gnss − p_ins : چقدر فاصله‌ایم؟', (34, 211, 238)),
                    ('اگر فیلتر درست کار کند، ν باید کوچک و تصادفی باشد', TXT),
                    ('ν بزرگ = یا GNSS پرت است، یا INS خیلی رفته', TXT_DIM)]
        if idx == 1:
            return [('S = H·P·Hᵀ + R', (34, 211, 238)),
                    ('S: واریانسِ مورد انتظار باقیمانده', TXT),
                    ('(عدم‌قطعیت INS در همان فریم سنجش + دقت سنسور)', TXT_DIM)]
        if idx == 2:
            return [('K = P·Hᵀ·S¹ : وزن هر منبع', (34, 211, 238)),
                    ('K بین ۰ و ۱ : چند دهمِ نویشن را باور کنیم؟', TXT),
                    ('مغزِ فیوژن: اعتماد به‌تناسب عدم‌قطعیت', TXT_DIM)]
        if idx == 3:
            return [('dx ← dx + K·ν', (34, 211, 238)),
                    ('خطای حالت (۱۵ بعدی) به‌سمت صفر سوق داده می‌شود', TXT),
                    ('نه همهٔ خطا (K<1) و نه هیچ‌کس — وزن‌دهی بهینه', TXT_DIM)]
        return [('INS نامی: p ← p+dp ، v ← v+dv ، q ← ق (δφ)', (34, 211, 238)),
                ('تخمین بایاس‌ها: calBg ، calBa به‌روز می‌شوند (Data Flow)', TXT),
                ('dx ← صفر ، کوواریانس با فرم Joseph → پایداری ریاضی', TXT_DIM)]
