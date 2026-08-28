"""H07 — Baro tab."""
import gfx
from palette import (W, H, TXT, TXT_DIM, C_BARO, C_BAD, C_OK, C_WARN)
from common_h import Scene, seg, ease, fade_in, header, gui_mock, tab_scene

ITEMS = [
    (4, 'enabled', 'false', 'اگر روشن، سنجش ارتفاع وارد فیلتر شود', C_BARO),
    (9, 'rate', '10 Hz', 'نرخ اندازه‌گیری — سریع‌تر از GNSS', C_BARO),
    (14, 'sigma', '1 m', 'نویز سفید سنجش', C_BARO),
    (19, 'bias', '0 m', 'بایاس ثابت به متر', C_WARN),
    (24, 'gmSigma / gmTau', '0 / 60 s',
     'اندازه و زمان همبستگی درافت فشار', C_BARO),
]


class H07(Scene):
    name = 'H07'

    def draw(self, c, t):
        tab_scene(c, t, 4, 'تب Baro: کمکِ کانال عمودی', C_BARO, ITEMS,
                  footer='وقتی GNSS خاموش است (تونل)، ارتفاع با بارومتر کران‌دار می‌ماند؛ '
                         'آپدیت اسکالار با گیت NIS جداگانه', footer_t=34)
        # altitude mini plot on the mock side
        if t > 30:
            a = ease(seg(t, 30, 32))
            x0, y0, x1, y1 = 90, 150 + 0, 700, 1010
            # draw below transport? use a strip at bottom of mock
            gfx.soft_rrect(c, (110, 930, 680, 995), 10,
                           fill=(16, 24, 46, int(235 * a)),
                           outline=(40, 55, 95, 255), width=1)
            import math
            d = gfx.ImageDraw.Draw(c)
            ax0, ax1, ay = 140, 650, 962
            d.line([(ax0, ay), (ax1, ay)], fill=(90, 108, 150, 255), width=2)
            n = 60
            pts = []
            for i in range(n + 1):
                x = ax0 + (ax1 - ax0) * i / n
                y = ay - 18 * math.sin(i / 7) - (i / n) * 8
                pts.append((x, y))
            d.line(pts, fill=(52, 211, 153, 255), width=3)
            gfx.text_c(c, 400, 938, 'ارتفاع: نوسان مسیر + درافت (GM)', 16, 'regular',
                       TXT_DIM)
