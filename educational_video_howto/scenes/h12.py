"""H12 — Reading the plots."""
import gfx
from palette import (W, H, TXT, TXT_DIM, C_FUSION, C_OK, C_WARN, C_INS, C_BAD)
from common_h import Scene, seg, ease, fade_in, header, gui_mock

TRACES = [('Truth', (230, 240, 250)), ('INS', (70, 140, 230)),
          ('GNSS', (250, 140, 40)), ('Fused', (60, 200, 90))]

PANELS = [
    ('Position', 'N/E/D + نقشهٔ دید از بالا', 4),
    ('Velocity', 'vN / vE / vD', 12),
    ('Attitude', 'رول/پیچ/یو + خط magenta تخمین تراز در فاز align', 20),
    ('Errors', 'نرم خطا + مؤلفه‌ها — همین‌جا حکم تست را می‌دهید', 28),
    ('Sensors', 'واقعی (خاکستری) در برابر اندازه‌شده (قرمز) — بایاس=آفست ثابت', 36),
    ('3D View', 'وسيلة + محورهای بدنه + NED + مسیرها + نقاط GNSS', 44),
]


class H12(Scene):
    name = 'H12'

    def draw(self, c, t):
        header(c, 'ستون راست: خواندن نمودارها', C_FUSION, t)
        gui_mock(c, -1, (90, 150, 700, 1010), t=t, highlight_plots=True)
        x0, y0, x1, y1 = 740, 150, 1830, 1010
        gfx.panel(c, (x0, y0, x1, y1))
        d = gfx.ImageDraw.Draw(c)
        d.rounded_rectangle([x1 - 10, y0 + 14, x1 - 2, y1 - 14], radius=4,
                            fill=C_FUSION + (255,))
        a = fade_in(t, 2, 0.8)
        gfx.text(c, (x1 - 36, y0 + 18), 'شش تب نمایش — یک کد رنگ برای همه', 28,
                 'bold', tuple(int(v * a) for v in TXT), 'right')
        # color legend
        for i, (nm, col) in enumerate(TRACES):
            aa = ease(seg(t, 3 + i * 0.8, 3.8 + i * 0.8))
            if aa <= 0:
                continue
            x = x1 - 60 - i * 300
            y = y0 + 84
            d2 = gfx.ImageDraw.Draw(c)
            d2.line([(x - 120, y), (x - 60, y)], fill=col + (255,), width=4)
            gfx.text(c, (x - 44, y - 16), nm, 22, 'bold',
                     tuple(int(v * aa) for v in col), 'right')
        yy = y0 + 140
        for (nm, fa, ti) in PANELS:
            aa = ease(seg(t, ti, ti + 1))
            if aa <= 0:
                yy += 86
                continue
            col = C_OK if nm == 'Errors' else C_FUSION
            gfx.soft_rrect(c, (x0 + 30, yy, x1 - 30, yy + 68), 10,
                           fill=(16, 24, 46, int(235 * aa)),
                           outline=col + (int(180 * aa),), width=2)
            gfx.text(c, (x1 - 60, yy + 10), nm, 23, 'bold',
                     tuple(int(v * aa) for v in col), 'right')
            gfx.text(c, (x1 - 250, yy + 14), fa, 21, 'regular',
                     tuple(int(v * aa) for v in TXT_DIM), 'right')
            yy += 86
        if t > 52:
            a = fade_in(t, 52, 1)
            gfx.soft_rrect(c, (x0 + 30, y1 - 150, x1 - 30, y1 - 16), 12,
                           fill=(24, 40, 60, int(235 * a)),
                           outline=(52, 211, 153, int(230 * a)), width=2)
            gfx.text_c(c, (x0 + x1) / 2, y1 - 128,
                       'سؤال‌ها: INS در حال رشد است؟  Fused کران‌دار مانده؟',
                       24, 'semibold', tuple(int(v * a) for v in TXT))
            gfx.text_c(c, (x0 + x1) / 2, y1 - 84,
                       'در پنجرهٔ قطعی فک زده؟  بعد از بازگشت سریع برگشته؟',
                       24, 'semibold', tuple(int(v * a) for v in C_OK))
            gfx.text_c(c, (x0 + x1) / 2, y1 - 44,
                       'در Sensors: بایاس به‌صورت آفست ثابت، نویز به‌صورت ضخیم‌شدن خط',
                       21, 'regular', tuple(int(v * a) for v in TXT_DIM))
