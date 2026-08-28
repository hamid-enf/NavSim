"""H13 — Data Flow & education panel."""
import gfx
from palette import (W, H, TXT, TXT_DIM, C_EST, C_OK, C_INS, C_GNSS, C_FUSION)
from common_h import Scene, seg, ease, fade_in, header, gui_mock

BLOCKS = [
    ('TRUTH', 'Pos/Vel/Att + Lat/Lon/Alt', C_EST, 6),
    ('IMU MEASUREMENT', 'Gyro/Accel + بایاس تخمینیِ استفاده‌شده', C_INS, 12),
    ('INS OUTPUT', 'Pos/Vel/Att تخمینی', C_INS, 18),
    ('GNSS', 'رویداد + موقعیت + epoch + OOSM؟', C_GNSS, 24),
    ('FILTER (PREDICTION)', 'σ موقعیت/وضعیت + NIS در برابر گیت + پذیرفته؟', C_FUSION, 30),
    ('FUSED OUTPUT', 'Lat/Lon/Alt نهایی', C_OK, 36),
    ('ERROR ANALYSIS', '|pos err| INS و Fused + vel/att', C_OK, 42),
]


class H13(Scene):
    name = 'H13'

    def draw(self, c, t):
        header(c, 'Data Flow: پنجرهٔ داخل موتور', C_EST, t)
        gui_mock(c, -1, (90, 150, 700, 1010), t=t)
        x0, y0, x1, y1 = 740, 150, 1830, 1010
        gfx.panel(c, (x0, y0, x1, y1))
        d = gfx.ImageDraw.Draw(c)
        d.rounded_rectangle([x1 - 10, y0 + 14, x1 - 2, y1 - 14], radius=4,
                            fill=C_EST + (255,))
        a = fade_in(t, 2, 0.8)
        gfx.text(c, (x1 - 36, y0 + 18), 'در هر گام، مقادیر زندهٔ هر مرحله', 28,
                 'bold', tuple(int(v * a) for v in TXT), 'right')
        # left column: stage buttons
        stages = ['Trajectory', 'Truth', 'IMU', 'Calibration', 'INS',
                  'Prediction', 'GNSS', 'Fusion', 'Estimate']
        ty = y0 + 70
        for i, st in enumerate(stages):
            aa = ease(seg(t, 3 + i * 0.35, 3.8 + i * 0.35))
            if aa <= 0:
                continue
            d2 = gfx.ImageDraw.Draw(c)
            d2.rounded_rectangle([x0 + 24, ty, x0 + 260, ty + 34], radius=8,
                                 fill=(16, 24, 46, int(235 * aa)),
                                 outline=(40, 55, 95, 255), width=1)
            gfx.text_c(c, (x0 + 24 + x0 + 260) / 2, ty + 4, st, 17, 'semibold',
                       tuple(int(v * aa) for v in TXT_DIM))
            ty += 42
        # right: live blocks
        yy = y0 + 70
        for (nm, fa, col, ti) in BLOCKS:
            aa = ease(seg(t, ti, ti + 1))
            if aa <= 0:
                yy += 96
                continue
            gfx.soft_rrect(c, (x0 + 290, yy, x1 - 24, yy + 80), 10,
                           fill=(16, 24, 46, int(235 * aa)),
                           outline=col + (int(180 * aa),), width=2)
            gfx.text(c, (x1 - 44, yy + 10), nm, 21, 'bold',
                     tuple(int(v * aa) for v in col), 'right')
            gfx.text(c, (x1 - 44, yy + 44), fa, 19, 'regular',
                     tuple(int(v * aa) for v in TXT_DIM), 'right')
            yy += 96
        if t > 50:
            a = fade_in(t, 50, 1)
            gfx.soft_rrect(c, (x0 + 20, y1 - 130, x1 - 20, y1 - 16), 12,
                           fill=(24, 40, 60, int(235 * a)),
                           outline=(52, 211, 153, int(230 * a)), width=2)
            gfx.text_c(c, (x0 + x1) / 2, y1 - 104,
                       'روی هر مرحله کلیک کنید ← پنل آموزشی: چیست؟ ورودی/خروجی؟ معادله؟ خطاها؟',
                       23, 'semibold', tuple(int(v * a) for v in C_OK))
            gfx.text_c(c, (x0 + x1) / 2, y1 - 62,
                       'هر وقت عددی عجیب به نظر رسید، حدس نزنید؛ اینجا بخوانید',
                       21, 'regular', tuple(int(v * a) for v in TXT_DIM))
