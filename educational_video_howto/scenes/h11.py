"""H11 — Transport & standard test protocol."""
import gfx
from palette import (W, H, TXT, TXT_DIM, C_WARN, C_OK, C_INS, C_BAD)
from common_h import Scene, seg, ease, fade_in, header, gui_mock

STEPS = [
    ('۱', 'کانفیگ پیش‌فرض را اجرا کنید؛ baseline را به خاطر بسپارید', C_INS, 30),
    ('۲', 'دقیقاً یک خطا را روشن کنید و اجرا کنید', C_WARN, 40),
    ('۳', 'تب Errors: INS در برابر Fused — چه چیزی عوض شد؟', C_INS, 50),
    ('۴', 'Data Flow: سیگما و NIS را بخوانید', C_OK, 60),
    ('۵', 'mode=ins بگذارید و دوباره — فیلتر چه اضافه کرد؟', C_BAD, 70),
]


class H11(Scene):
    name = 'H11'

    def draw(self, c, t):
        header(c, 'Transport و پروتکل تست استاندارد', C_WARN, t)
        gui_mock(c, -1, (90, 150, 700, 1010), t=t)
        # highlight transport zone with pulse
        if t > 2:
            p = 0.5 + 0.5 * (t % 2)
            d = gfx.ImageDraw.Draw(c)
            gfx.soft_rrect(c, (98, 700, 692, 812), 10,
                           fill=(251, 191, 36, int(18 + 20 * p)),
                           outline=(251, 191, 36, 255), width=3)
            gfx.text_c(c, 395, 706, 'Start / Pause / Stop / Reset / Step + speed',
                       17, 'semibold', (251, 191, 36))
        x0, y0, x1, y1 = 740, 150, 1830, 1010
        gfx.panel(c, (x0, y0, x1, y1))
        d = gfx.ImageDraw.Draw(c)
        d.rounded_rectangle([x1 - 10, y0 + 14, x1 - 2, y1 - 14], radius=4,
                            fill=C_WARN + (255,))
        a = fade_in(t, 2, 0.8)
        gfx.text(c, (x1 - 36, y0 + 20), 'پروتکل تست استاندارد: پنج مرحله', 28,
                 'bold', tuple(int(v * a) for v in TXT), 'right')
        yy = y0 + 90
        for (num, s, col, ti) in STEPS:
            aa = ease(seg(t, ti, ti + 1.2))
            if aa <= 0:
                yy += 118
                continue
            gfx.soft_rrect(c, (x0 + 30, yy, x1 - 30, yy + 96), 12,
                           fill=(16, 24, 46, int(235 * aa)),
                           outline=col + (int(200 * aa),), width=2)
            d2 = gfx.ImageDraw.Draw(c)
            d2.ellipse([x1 - 84, yy + 24, x1 - 40, yy + 68],
                       fill=col + (int(255 * aa),))
            gfx.text_c(c, x1 - 62, yy + 30, num, 24, 'bold', (10, 20, 40))
            lines = []
            cur = ''
            for wd in s.split(' '):
                trial = (cur + ' ' + wd).strip()
                if len(trial) > 26:
                    lines.append(cur)
                    cur = wd
                else:
                    cur = trial
            if cur:
                lines.append(cur)
            lyy = yy + 16 if len(lines) > 1 else yy + 30
            for ln in lines:
                gfx.text(c, (x1 - 100, lyy), ln, 24, 'semibold',
                         tuple(int(v * aa) for v in TXT), 'right')
                lyy += 36
            yy += 118
        if t > 84:
            a = fade_in(t, 84, 1)
            gfx.text_c(c, (x0 + x1) / 2, y1 - 40,
                       'نوار وضعیت: t ، فاز ، رویداد GNSS (MEAS/DROPOUT/REJECTED) ، خطای لحظه‌ای',
                       22, 'regular', tuple(int(v * a) for v in TXT_DIM))
