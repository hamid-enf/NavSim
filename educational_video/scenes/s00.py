"""S00 — Intro / title + four questions."""
import gfx
from palette import (W, H, TXT, TXT_DIM, C_INS, C_GNSS, C_FUSION, C_EST)
from common import Scene, seg, ease, ease_out, fade_in, header, pipeline_strip

C_OOSM_C = (251, 191, 36)


class S00(Scene):
    name = 'S00'

    def draw(self, c, t):
        D = self.dur
        a = ease(seg(t, 0.3, 1.6))
        if a > 0:
            gfx.text_c(c, W / 2, 150, 'شبیه‌ساز ناوبری NavSim', 64, 'black',
                       tuple(int(v * a) for v in TXT))
            gfx.text_c(c, W / 2, 235, 'از سنسور تا پاسخ ناوبری — به‌زبانِ ساده و گرافیکی',
                       30, 'regular', tuple(int(v * a) for v in TXT_DIM))
            d = gfx.ImageDraw.Draw(c)
            lw = int(420 * a)
            d.line([(W / 2 - lw, 285), (W / 2 + lw, 285)],
                   fill=(56, 189, 248, 255), width=3)
        qs = [
            ('داده از کجا می‌آید؟', C_GNSS, 7.0),
            ('داده به کجا می‌رود؟', C_INS, 11.0),
            ('چرا؟', C_FUSION, 15.0),
            ('پارامترها باید چه مقدار باشند؟', C_OOSM_C, 19.0),
        ]
        for i, (q, col, t0) in enumerate(qs):
            x0 = 260 + (i % 2) * 660
            y0 = 360 + (i // 2) * 210
            a = ease(seg(t, t0, t0 + 1.0))
            if a <= 0:
                continue
            x = x0 + int((1 - a) * 60)
            x1, y1 = x + 600, y0 + 150
            d = gfx.ImageDraw.Draw(c)
            gfx.soft_rrect(c, (x, y0, x1, y1), 18, fill=(19, 28, 51, int(235 * a)),
                           outline=(40, 55, 95, int(255 * a)), width=2)
            d.rounded_rectangle([x1 - 10, y0 + 16, x1 - 2, y1 - 16], radius=4,
                                fill=col + (int(255 * a),))
            gfx.text_c(c, (x + x1) / 2, (y0 + y1) / 2, q, 32, 'bold',
                       tuple(int(v * a) for v in TXT))
        if t > 4:
            pipeline_strip(c, t - 4, active=-1, y=830, scale=0.9, highlight_all_after=True)
            p = (t - 4) / max(D - 4, 1)
            p = p - int(p)
            x = 120 + p * (W - 240)
            gfx.glow(c, (x, 830), 30, C_EST, 120)
            gfx.dot(c, (x, 830), 8, (240, 250, 255))
        a = fade_in(t, 26, 1.2)
        if a > 0:
            gfx.text_c(c, W / 2, 950, 'هر مرحله: ورودی ← فرایند ← خروجی ← دلیل', 30,
                       'semibold', tuple(int(v * a) for v in (251, 191, 36)))
        a = fade_in(t, 31, 1.2)
        if a > 0:
            gfx.text_c(c, W / 2, 1010, 'با مقادیر واقعی٬ از ریپوزیتوری٬ بدون ساده‌سازیِ بیش‌ازحد',
                       24, 'regular', tuple(int(v * a) for v in TXT_DIM))
