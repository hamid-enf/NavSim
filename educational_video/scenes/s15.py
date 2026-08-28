"""S15 — Wrap up."""
import math

import gfx
from palette import (W, H, TXT, TXT_DIM, TXT_FAINT, C_INS, C_GNSS, C_FUSION,
                     C_OK, C_WARN, C_EST, STAGES, STAGE_COLORS)
from common import Scene, seg, ease, fade_in, header, card, stage_color, vehicle


class S15(Scene):
    name = 'S15'

    def draw(self, c, t):
        D = self.dur
        header(c, 'جمع‌بندی', C_FUSION, t)

        a = ease(seg(t, 1, 2.5))
        if a > 0:
            nodes = [
                (1350, 320, 'پیش‌بینی سریع و ارزان', 'INS — هر ۱۰ms', C_INS),
                (960, 560, 'اصلاح آهسته و دقیق', 'GNSS — هر ثانیه (و کمک‌ها)', C_GNSS),
                (570, 320, 'فیلتری که عدم‌قطعیتش را می‌داند', 'EKF: K = PHᵀS⁻¹', C_FUSION),
            ]
            for (cx, cy, t1, t2, col) in nodes:
                gfx.glow(c, (cx, cy), 110, col, int(60 * a))
                gfx.soft_rrect(c, (cx - 240, cy - 70, cx + 240, cy + 70), 18,
                               fill=(19, 28, 51, int(235 * a)),
                               outline=col + (int(230 * a),), width=3)
                gfx.text_c(c, cx, cy - 34, t1, 27, 'bold',
                           tuple(int(v * a) for v in TXT))
                gfx.text_c(c, cx, cy + 18, t2, 23, 'semibold',
                           tuple(int(v * a) for v in col))
            d = gfx.ImageDraw.Draw(c)
            p = ease(seg(t, 3, 8))
            gfx.arrow(d, (1350 - 250, 300), (1000, 470), C_INS, 4, 16, progress=p)
            gfx.arrow(d, (940, 545), (800, 400), C_GNSS, 4, 16, progress=ease(seg(t, 4.5, 9)))
            gfx.arrow(d, (585, 330), (1100, 290), C_FUSION, 4, 16,
                      progress=ease(seg(t, 6, 11)))
        if t > 16:
            gfx.text(c, (1830, 700), 'آنچه در NavSim دیدیم:', 27, 'bold',
                     tuple(int(v * ease(seg(t, 16, 17))) for v in TXT), 'right')
            pass_items = [
                ('مسیر ← Truth: مرجعِ بدون خطا', 18),
                ('سنسورها با همهٔ خطاهای واقعی (بایاس، نویز، قطعی، پرت، تأخیر)', 23),
                ('تراز اولیه: levelling یا transfer alignment', 28),
                ('INS دریفت می‌کند (∝ t²)', 33),
                ('EKF دریفت را کران‌دار می‌کند — و بایاس‌ها را می‌آموزد', 38),
                ('Baro / ZUPT / OOSM شکاف‌ها را می‌پوشانند', 44),
                ('تحلیل خطا: Fused حول دقت GNSS، INS در هزارمترها', 50),
            ]
            yy = 745
            for s, ti in pass_items:
                aa = fade_in(t, ti, 0.7)
                if aa <= 0:
                    yy += 44
                    continue
                d = gfx.ImageDraw.Draw(c)
                d.ellipse([1780, yy + 10, 1800, yy + 30], fill=C_OK + (int(255 * aa),))
                gfx.text(c, (1766, yy), s, 24, 'regular',
                         tuple(int(v * aa) for v in TXT), 'right')
                yy += 44
        if t > 56:
            a = fade_in(t, 56, 1.2)
            gfx.soft_rrect(c, (430, 920, 1490, 1010), 18,
                           fill=(24, 40, 60, int(235 * a)),
                           outline=C_OK + (int(230 * a),), width=3)
            gfx.text_c(c, 960, 942, 'main را اجرا کنید — یک پارامتر را در حین اجرا عوض کنید',
                       28, 'bold', tuple(int(v * a) for v in TXT))
            gfx.text_c(c, 960, 984, 'و اثرش را با چشمِ خودتان ببینید',
                       24, 'semibold', tuple(int(v * a) for v in C_OK))
        if t > 62:
            a = fade_in(t, 62, 1.2)
            gfx.text_c(c, 960, 1052,
                       'این‌جوری است که از کاربرِ شبیه‌ساز، به فهمِ سیستم تبدیل می‌شوید',
                       26, 'semibold', tuple(int(v * a) for v in (251, 191, 36)))
            vehicle(c, 1750, 1000, 1.4, (t * 1.2) % (2 * math.pi), C_INS)
