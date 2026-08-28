"""H18 — Wrap up: expert checklist."""
import math

import gfx
from palette import (W, H, TXT, TXT_DIM, C_OK, C_INS, C_WARN, C_FUSION)
from common_h import Scene, seg, ease, fade_in, header, vehicle

BEFORE = [
    'مسیرم چیست و در آن چه چیزی قابل‌مشاهده است؟',
    'کدام یک خطا را روشن کردم و اثرش باید کجا باشد — وضعیت، سرعت، موقعیت؟',
    'انتظار دقیقاً چه نتیجه‌ای است در کدام نمودار؟',
]
AFTER = [
    'INS را با Fused مقایسه کنید',
    'σ و NIS را در Data Flow بخوانید',
    'لاگ را با نام معنادار ذخیره کنید',
]
EXTEND = [
    ('مسیر جدید', 'یک case در TrajectoryLibrary', C_INS),
    ('سنسور جدید', 'کلاسی مثل BaroModel + یک آپدیت در حلقه', C_WARN),
    ('فیلتر جدید', 'جایگزینی LooselyCoupledEKF با همان رابط', C_OK),
]


class H18(Scene):
    name = 'H18'

    def draw(self, c, t):
        header(c, 'چک‌لیست متخصص', C_OK, t)
        # before panel (right)
        x0, y0, x1, y1 = 1000, 150, 1830, 560
        gfx.panel(c, (x0, y0, x1, y1))
        d = gfx.ImageDraw.Draw(c)
        d.rounded_rectangle([x1 - 10, y0 + 14, x1 - 2, y1 - 14], radius=4,
                            fill=C_INS + (255,))
        a = fade_in(t, 2, 0.8)
        gfx.text(c, (x1 - 36, y0 + 20), 'پیش از هر تست، سه سؤال:', 27, 'bold',
                 tuple(int(v * a) for v in TXT), 'right')
        yy = y0 + 84
        for i, s in enumerate(BEFORE):
            aa = ease(seg(t, 5 + i * 4, 5.8 + i * 4))
            if aa <= 0:
                yy += 130
                continue
            gfx.soft_rrect(c, (x0 + 24, yy, x1 - 24, yy + 110), 10,
                           fill=(16, 24, 46, int(235 * aa)),
                           outline=(56, 189, 248, int(180 * aa)), width=2)
            d2 = gfx.ImageDraw.Draw(c)
            d2.ellipse([x1 - 76, yy + 30, x1 - 44, yy + 62],
                       fill=(56, 189, 248, int(255 * aa)))
            gfx.text_c(c, x1 - 60, yy + 34, str(i + 1), 22, 'bold', (10, 20, 40))
            lines = []
            cur = ''
            for wd in s.split(' '):
                trial = (cur + ' ' + wd).strip()
                if len(trial) > 22:
                    lines.append(cur)
                    cur = wd
                else:
                    cur = trial
            if cur:
                lines.append(cur)
            lyy = yy + 14 if len(lines) > 1 else yy + 34
            for ln in lines:
                gfx.text(c, (x1 - 92, lyy), ln, 21, 'regular',
                         tuple(int(v * aa) for v in TXT), 'right')
                lyy += 32
            yy += 130
        # after panel (left)
        x0, y0, x1, y1 = 90, 150, 950, 560
        gfx.panel(c, (x0, y0, x1, y1))
        d = gfx.ImageDraw.Draw(c)
        d.rounded_rectangle([x1 - 10, y0 + 14, x1 - 2, y1 - 14], radius=4,
                            fill=C_OK + (255,))
        a = fade_in(t, 2, 0.8)
        gfx.text(c, (x1 - 36, y0 + 20), 'بعد از هر تست:', 27, 'bold',
                 tuple(int(v * a) for v in TXT), 'right')
        yy = y0 + 90
        for i, s in enumerate(AFTER):
            aa = ease(seg(t, 10 + i * 5, 10.8 + i * 5))
            if aa <= 0:
                yy += 120
                continue
            d2 = gfx.ImageDraw.Draw(c)
            d2.ellipse([x1 - 70, yy + 10, x1 - 44, yy + 36],
                       fill=(52, 211, 153, int(255 * aa)))
            gfx.text(c, (x1 - 84, yy + 8), s, 24, 'semibold',
                     tuple(int(v * aa) for v in TXT), 'right')
            yy += 120
        # extend panel (bottom)
        x0, y0, x1, y1 = 90, 600, 1830, 880
        gfx.panel(c, (x0, y0, x1, y1))
        d = gfx.ImageDraw.Draw(c)
        d.rounded_rectangle([x1 - 10, y0 + 14, x1 - 2, y1 - 14], radius=4,
                            fill=C_WARN + (255,))
        a = fade_in(t, 28, 0.8)
        gfx.text(c, (x1 - 36, y0 + 20), 'معماری باز — برای گسترش:', 27, 'bold',
                 tuple(int(v * a) for v in TXT), 'right')
        for i, (nm, fa, col) in enumerate(EXTEND):
            aa = ease(seg(t, 32 + i * 4, 32.8 + i * 4))
            if aa <= 0:
                continue
            x = x1 - 60 - i * 570
            gfx.soft_rrect(c, (x - 530, y0 + 84, x, y0 + 236), 12,
                           fill=(16, 24, 46, int(235 * aa)),
                           outline=col + (int(200 * aa),), width=2)
            gfx.text_c(c, (x - 530 + x) / 2, y0 + 104, nm, 25, 'bold',
                       tuple(int(v * aa) for v in col))
            lines = []
            cur = ''
            for wd in fa.split(' '):
                trial = (cur + ' ' + wd).strip()
                if len(trial) > 18:
                    lines.append(cur)
                    cur = wd
                else:
                    cur = trial
            if cur:
                lines.append(cur)
            lyy = y0 + 156
            for ln in lines:
                gfx.text_c(c, (x - 530 + x) / 2, lyy, ln, 21, 'regular',
                           tuple(int(v * aa) for v in TXT_DIM))
                lyy += 32
        # closing
        if t > 46:
            a = fade_in(t, 46, 1.5)
            gfx.text_c(c, 960, 930, 'شما دیگر کاربرِ شبیه‌ساز نیستید؛ اپراتورش هستید',
                       34, 'black', tuple(int(v * a) for v in C_OK))
            gfx.text_c(c, 960, 985, 'main را بزنید و با آزمایش ۱ شروع کنید',
                       28, 'semibold', tuple(int(v * a) for v in TXT))
            vehicle(c, 1720, 960, 1.6, (t * 1.2) % (2 * math.pi), C_INS)
