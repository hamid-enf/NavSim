"""S12 — Why these parameter values?"""
import math

import gfx
from palette import (W, H, TXT, TXT_DIM, TXT_FAINT, C_INS, C_GNSS, C_WARN,
                     C_OK, C_BAD, C_EST, C_BARO)
from common import Scene, seg, ease, fade_in, header, card

CARDS = [
    ('dt = 0.01 s  (100 Hz)', 'نرخ واقعی IMU؛ گام ریزتر = انتگرال دقیق‌تر + نویز نمونه کمتر', C_INS, 3, 4),
    ('مدت = 120 s', 'هم دریفت دیده شود، هم مانور کافی برای قابل‌مشاهده‌شدن بایاس', C_INS, 15, 16),
    ('GNSS: 1 Hz', 'رسیور واقع‌بینانهٔ کم‌نرخ؛ فیوژن loosely-coupled است', C_GNSS, 24, 25),
    ('σ = 1.5 / 3 m', 'دقت واقع‌بینانهٔ رسیور مصرفی (عمودی ضعیف‌تر: DOP)', C_GNSS, 33, 34),
]


class S12(Scene):
    name = 'S12'

    def draw(self, c, t):
        D = self.dur
        header(c, 'چرا این پارامترها؟', C_WARN, t)

        for i, (title, why, col, t0, t1) in enumerate(CARDS):
            a = ease(seg(t, t0, t0 + 1.2))
            if a <= 0:
                continue
            x = 1760 - (i % 2) * 860
            y = 180 + (i // 2) * 210
            x0, y0, x1, y1 = x - 410, y, x + 50, y + 170
            gfx.soft_rrect(c, (x0, y0, x1, y1), 14, fill=(19, 28, 51, int(230 * a)),
                           outline=col + (int(200 * a),), width=2)
            d = gfx.ImageDraw.Draw(c)
            d.rounded_rectangle([x1 - 8, y0 + 14, x1, y1 - 14], radius=4,
                                fill=col + (int(255 * a),))
            gfx.text(c, (x1 - 30, y0 + 18), title, 26, 'bold',
                     tuple(int(v * a) for v in col), 'right')
            gfx.text(c, (x1 - 30, y0 + 62), why, 22, 'regular',
                     tuple(int(v * a) for v in TXT), 'right')

        if t > 44:
            a = ease(seg(t, 44, 46))
            x0, y0, x1, y1 = 90, 620, 1020, 1040
            gfx.panel(c, (x0, y0, x1, y1))
            gfx.text(c, (x1 - 24, y0 + 12), 'Q: چگالی نویز پروس = اعتماد فیلتر به مدل',
                     26, 'bold', tuple(int(v * a) for v in TXT), 'right')
            cx, cy = 555, 830
            phase = 0 if t < 62 else 1
            ang = math.radians(-12 if phase == 0 else 12)
            L = 330
            ca, sa = math.cos(ang), math.sin(ang)
            d = gfx.ImageDraw.Draw(c)
            d.line([(cx - L * ca, cy - L * sa), (cx + L * ca, cy + L * sa)],
                   fill=(148, 163, 184, 255), width=8)
            d.ellipse([cx - 12, cy - 12, cx + 12, cy + 12], fill=(240, 250, 255, 255))
            lx, ly = cx + L * ca, cy + L * sa
            rx, ry = cx - L * ca, cy - L * sa
            gfx.chip(c, lx, ly - 60, 'Q خیلی کوچک', C_BAD if phase == 0 else C_INS, size=23)
            gfx.chip(c, rx, ry - 60, 'Q خیلی بزرگ', C_BAD if phase == 1 else C_INS, size=23)
            if phase == 0:
                msg = (('اعتماد بیش از حد به مدل:', C_BAD), ('تصحیح آهسته + کورشدگی در برابر خطای مدل', TXT_DIM))
            else:
                msg = (('بی‌اعتمادی به مدل:', C_BAD), ('دنبال‌کردن هر نویز سنسور → خروجی لرزان', TXT_DIM))
            m1, c1 = msg[0]
            m2, c2 = msg[1]
            yy = y1 - 130
            gfx.text_c(c, (x0 + x1) / 2, yy, m1, 25, 'bold',
                       tuple(int(v * a) for v in c1))
            gfx.text_c(c, (x0 + x1) / 2, yy + 42, m2, 23, 'regular',
                       tuple(int(v * a) for v in c2))
        if t > 78:
            a = ease(seg(t, 78, 80))
            x0, y0, x1, y1 = 1060, 620, 1830, 1040
            card(c, (x0, y0, x1, y1), 'P صفر: بازتابِ کیفیت تراز اولیه', C_EST)
            rows = [
                ('باید واقع‌بینانه باشد:', TXT, 81),
                ('کوچک‌تر از واقعیت ←', C_BAD, 86),
                ('فیلتر تصحیح‌ها را نمی‌پذیرد (بیش‌اطمینانی)', C_BAD, 89),
                ('بزرگ‌تر از واقعیت ←', C_WARN, 94),
                ('شروع با لرزش + دیر همگرایی', C_WARN, 97),
            ]
            yy = y0 + 76
            for s, col, ti in rows:
                aa = fade_in(t, ti, 0.7)
                if aa <= 0:
                    yy += 50
                    continue
                gfx.text(c, (x1 - 40, yy), s, 24, 'semibold',
                         tuple(int(v * aa) for v in col), 'right')
                yy += 50
        if t > 104:
            items = [
                ('NIS gate = 16.27', 'کای-دو ۹۹/۹٪ (۳ د.ا.) — فقط پرت‌های واقعی رد می‌شوند', C_WARN, 104),
                ('OOSM window = 12 s', 'تأخیر رسیور + بافر امن', C_BARO, 112),
                ('Align = 10 s', 'کافی برای همگرایی 1/√n', C_INS, 118),
            ]
            for i, (en, fa, col, ti) in enumerate(items):
                aa = ease(seg(t, ti, ti + 0.9))
                if aa <= 0:
                    continue
                x = 1690 - i * 570
                gfx.soft_rrect(c, (x - 270, 430, x + 270, 590), 12,
                               fill=(19, 28, 51, int(225 * aa)),
                               outline=col + (int(200 * aa),), width=2)
                gfx.text_c(c, (x - 270 + x + 270) / 2, 452, en, 24, 'semibold',
                           tuple(int(v * aa) for v in col))
                gfx.text_c(c, (x - 270 + x + 270) / 2, 505, fa, 21, 'regular',
                           tuple(int(v * aa) for v in TXT))
        if t > 124:
            a = fade_in(t, 124, 1)
            gfx.chip(c, 960, 1058, 'بیشتر این پارامترها در حین اجرا قابل تغییرند — بدون Reset',
                     C_OK, size=27)
