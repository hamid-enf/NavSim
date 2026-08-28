"""S02 — The big picture: full data flow."""
import gfx
from palette import (W, H, TXT, TXT_DIM, C_EST, STAGES,
                     STAGE_COLORS, C_OK, C_BAD, C_INS, C_GNSS, C_IMU)
from common import Scene, seg, ease, fade_in, header, pipeline_strip, stage_color

C_FUSION_C = (52, 211, 153)

DETAILS = {
    'Trajectory': ('ورودی: ۹ نوع مسیر (خطی، دایره، هفت‌هشتی، …)',
                   'خروجی: p، v، a در فریم NED',
                   'مسیر مرجعِ حرکت — همه‌چیز از اینجا شروع می‌شود'),
    'Truth': ('ورودی: مسیر',
              'خروجی: موقعیت، سرعت، وضعیت بدون خطا',
              'مرجعِ مقایسه برای همهٔ بخش‌ها'),
    'IMU': ('ورودی: ω و f واقعی',
            'خروجی: اندازه‌گیری + بایاس + نویز',
            'سنسور سریع (۱۰Hz) اما با دریفت'),
    'Calibration': ('ورودی: خروجی IMU + بایاس تخمینی',
                    'خروجی: ω، f بدون بایاس',
                    'بایاسی که فیلتر تخمین زده، کم می‌شود'),
    'INS': ('ورودی: IMU کالیبره‌شده',
            'خروجی: p، v، وضعیت تخمینی',
            'انتگرال‌گیری = پیش‌بینی سریع ولی دریفت‌دار'),
    'Prediction': ('ورودی: خطای حالت + dt',
                   'خروجی: P گسترش‌یافته',
                    'رشد عدم‌قطعیت بین دو سنجش'),
    'GNSS': ('ورودی: موقعیت واقعی + خطاها',
             'خروجی: سنجش موقعیت (۱Hz)',
             'دقیق ولی آهسته — و گاهی قطع/پرت'),
    'Fusion': ('ورودی: سنجش GNSS + خطای حالت',
               'خروجی: خطای تصحیح‌شده + بایاس جدید',
               'قلبِ اصلاح: K = PHᵀS⁻¹'),
    'Estimate': ('ورودی: INS تصحیح‌شده',
                 'خروجی: p، v، وضعیت ترکیبی',
                 'پاسخ نهاییِ ناوبری'),
    'Error': ('ورودی: تخمین در برابر Truth',
              'خروجی: خطای موقعیت/سرعت/وضعیت',
              'سنجشِ کیفیت — INS در برابر Fused'),
}

NARR_ORDER = ['Trajectory', 'Truth', 'IMU', 'GNSS', 'Calibration',
              'INS', 'Prediction', 'Fusion', 'Estimate', 'Error']
TIMES = [(4, 14), (14, 22), (22, 34), (34, 44), (44, 52),
         (52, 60), (60, 68), (68, 78), (78, 86), (86, 89.5)]


class S02(Scene):
    name = 'S02'

    def draw(self, c, t):
        D = self.dur
        header(c, 'تصویر بزرگ: جریان داده', C_FUSION_C, t)

        n = len(STAGES)
        d = gfx.ImageDraw.Draw(c)
        positions = {}
        for i in range(6):
            st = STAGES[i]
            x = 140 + i * 270
            y = 220
            positions[st] = (x, y)
        for i in range(4):
            st = STAGES[6 + i]
            x = 1490 - i * 270
            y = 330
            positions[st] = (x, y)
        for i in range(5):
            x = 140 + i * 270
            gfx.arrow(d, (x + 120, 220), (x + 270 - 120, 220), (96, 116, 160), 3, 12,
                      progress=ease(seg(t, 0.5 + i * 0.15, 0.9 + i * 0.15)))
        gfx.arrow(d, (positions['Prediction'][0], 252),
                  (positions['GNSS'][0], 298), (96, 116, 160), 3, 12,
                  progress=ease(seg(t, 0.8, 1.2)))
        for i in range(3):
            st = STAGES[6 + i]
            st2 = STAGES[7 + i]
            x1 = positions[st][0]
            x2 = positions[st2][0]
            gfx.arrow(d, (x1 - 120, 330), (x2 + 120, 330), (96, 116, 160), 3, 12,
                      progress=ease(seg(t, 1.0 + i * 0.15, 1.4 + i * 0.15)))

        active = -1
        for idx, st in enumerate(NARR_ORDER):
            t0, t1 = TIMES[idx]
            if t >= t0:
                active = idx

        for i, st in enumerate(STAGES):
            col = stage_color(st)
            x, y = positions[st]
            narr_idx = NARR_ORDER.index(st)
            t0, t1 = TIMES[narr_idx]
            a = ease(seg(t, t0, t0 + 0.8))
            if a <= 0:
                continue
            is_act = (narr_idx == active)
            is_done = (narr_idx < active)
            if is_act:
                gfx.glow(c, (x, y), 80, col, 90)
            gfx.chip(c, x, y, st, col, size=26, alpha_fill=55 if is_act else (30 if is_done else 15),
                     outline_w=4 if is_act else 2)

        if active >= 0:
            st = NARR_ORDER[active]
            t0, t1 = TIMES[active]
            a = ease(seg(t, t0 + 0.5, t0 + 1.4))
            if a > 0:
                inp, out, why = DETAILS[st]
                col = stage_color(st)
                x0, y0, x1, y1 = 120, 430, 1800, 860
                gfx.panel(c, (x0, y0, x1, y1))
                d = gfx.ImageDraw.Draw(c)
                d.rounded_rectangle([x1 - 10, y0 + 18, x1 - 2, y1 - 18], radius=4,
                                    fill=col + (int(255 * a),))
                gfx.text(c, (x1 - 40, y0 + 26), st, 40, 'bold',
                         tuple(int(v * a) for v in col))
                yy = y0 + 110
                for label, val, vv in [('ورودی', inp, TXT), ('خروجی', out, (34, 211, 238)),
                                       ('چرا؟', why, (251, 191, 36))]:
                    aa = fade_in(t, t0 + 0.8 + (yy - (y0 + 110)) / 90.0 * 0.5, 0.6)
                    if aa <= 0:
                        yy += 95
                        continue
                    gfx.text(c, (x1 - 50, yy), label, 24, 'bold',
                             tuple(int(v * aa) for v in TXT_DIM), 'right')
                    gfx.text(c, (x1 - 50 - 120, yy + 6), val, 30, 'semibold',
                             tuple(int(v * aa) for v in vv), 'right')
                    yy += 95
        a = fade_in(t, 80, 1)
        if a > 0:
            y = 940
            d = gfx.ImageDraw.Draw(c)
            gfx.soft_rrect(c, (300, y, 1620, y + 90), 14,
                           fill=(20, 30, 56, int(230 * a)),
                           outline=(56, 189, 248, int(255 * a)), width=2)
            gfx.text_c(c, 960, y + 14,
                       'کل این زنجیره هر ۱۰ میلی‌ثانیه (هر گام) داخل SimEngine اجرا می‌شود — موتورِ بدون گرافیک؛ GUI فقط پنجرهٔ مشاهده',
                       26, 'semibold', tuple(int(v * a) for v in TXT))
