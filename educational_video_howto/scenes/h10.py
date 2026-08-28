"""H10 — Errors tab."""
import gfx
from palette import C_BAD, TXT, TXT_DIM, C_OK
from common_h import Scene, seg, ease, fade_in, header, gui_mock

SWITCHES = [
    'Gyro bias', 'Accel bias', 'Gyro noise', 'Accel noise',
    'Gyro scale factor', 'Accel scale factor', 'Gyro misalignment',
    'Accel misalignment', 'GNSS noise', 'GNSS outlier', 'GNSS dropout',
    'Initial alignment error', 'Timing error (variable dt)',
]


class H10(Scene):
    name = 'H10'

    def draw(self, c, t):
        header(c, 'تب Errors: همهٔ کلیدها در یک صفحه', C_BAD, t)
        gui_mock(c, 7, (90, 150, 700, 1010), t=t)
        x0, y0, x1, y1 = 740, 150, 1830, 1010
        gfx.panel(c, (x0, y0, x1, y1))
        d = gfx.ImageDraw.Draw(c)
        d.rounded_rectangle([x1 - 10, y0 + 14, x1 - 2, y1 - 14], radius=4,
                            fill=C_BAD + (255,))
        a = fade_in(t, 2, 0.8)
        gfx.text(c, (x1 - 36, y0 + 20), 'پارامتر جدیدی ندارد — کلیدهای تب‌های دیگر',
                 26, 'bold', tuple(int(v * a) for v in TXT), 'right')
        # switch grid
        for i, nm in enumerate(SWITCHES):
            ti = 4 + i * 1.1
            aa = ease(seg(t, ti, ti + 0.7))
            if aa <= 0:
                continue
            col_i = i % 2
            row_i = i // 2
            x = x1 - 70 - col_i * 520
            y = y0 + 90 + row_i * 52
            gfx.soft_rrect(c, (x - 440, y - 20, x, y + 24), 10,
                           fill=(16, 24, 46, int(230 * aa)),
                           outline=(248, 113, 113, int(140 * aa)), width=1)
            # toggle knob
            d2 = gfx.ImageDraw.Draw(c)
            d2.rounded_rectangle([x - 42, y - 12, x - 4, y + 14], radius=12,
                                 fill=(52, 211, 153, int(255 * aa)))
            d2.ellipse([x - 46, y - 10, x - 26, y + 10], fill=(240, 250, 255, 255))
            gfx.text(c, (x - 62, y - 12), nm, 20, 'semibold',
                     tuple(int(v * aa) for v in TXT), 'right')
        if t > 21:
            a = fade_in(t, 21, 1)
            gfx.soft_rrect(c, (x0 + 20, y1 - 150, x1 - 20, y1 - 84), 10,
                           fill=(10, 16, 30, int(235 * a)),
                           outline=(60, 78, 130, 255), width=2)
            gfx.text(c, (x1 - 40, y1 - 138),
                     'Gyro bias اینجای = دقیقاً همان IMU.useGyroBias تب IMU',
                     22, 'semibold', tuple(int(v * a) for v in (34, 211, 238)),
                     'right')
            gfx.text(c, (x1 - 40, y1 - 104),
                     'همان مسیرِ همان کانفیگ — دو دریچه روی یک چاه', 21,
                     'regular', tuple(int(v * a) for v in TXT_DIM), 'right')
        if t > 28:
            a = fade_in(t, 28, 1)
            gfx.soft_rrect(c, (x0 + 20, y1 - 70, x1 - 20, y1 - 14), 10,
                           fill=(24, 40, 60, int(235 * a)),
                           outline=(52, 211, 153, int(230 * a)), width=2)
            gfx.text_c(c, (x0 + x1) / 2, y1 - 58,
                       'پروتکل: همه خاموش → یک منبع روشن → اثرش را دنبال کنید',
                       24, 'semibold', tuple(int(v * a) for v in C_OK))
