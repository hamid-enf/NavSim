"""H02 — Anatomy of the window."""
import gfx
from palette import (W, H, TXT, TXT_DIM, C_INS, C_FUSION, C_EST, C_WARN,
                     C_CALIB, C_BAD)
from common_h import Scene, seg, ease, fade_in, header, gui_mock, TAB_NAMES, PLOT_TABS


class H02(Scene):
    name = 'H02'

    def draw(self, c, t):
        D = self.dur
        header(c, 'آناتومی پنجره', C_INS, t)
        # big mock in center
        gui_mock(c, -1, (330, 150, 1590, 980), t=t, highlight_plots=True)
        # callouts
        cal = [
            (322, 300, 'تب‌های پارامتر: ۸ تب + Experiments + Logs', C_INS, 5,
             (120, 240)),
            (322, 800, 'Transport: Start/Pause/Stop/Reset/Step + سرعت', C_WARN, 12,
             (120, 860)),
            (322, 935, 'نوار وضعیت: t ، فاز ، رویداد GNSS ، خطای لحظه‌ای', C_EST, 18,
             (120, 930)),
            (1598, 300, '۵ تب نمودار + 3D View + Data Flow', C_FUSION, 25,
             (1580, 240)),
        ]
        for x, y, txt, col, ti, _ in cal:
            a = ease(seg(t, ti, ti + 1))
            if a <= 0:
                continue
            lines = []
            cur = ''
            for wd in txt.split(' '):
                trial = (cur + ' ' + wd).strip()
                if len(trial) > 22:
                    lines.append(cur)
                    cur = wd
                else:
                    cur = trial
            if cur:
                lines.append(cur)
            yy = y - 12 * len(lines)
            for ln in lines:
                gfx.text_c(c, x, yy, ln, 22, 'semibold',
                           tuple(int(v * a) for v in col))
                yy += 34
        if t > 33:
            a = fade_in(t, 33, 1)
            gfx.soft_rrect(c, (330, 1010, 1590, 1070), 12,
                           fill=(20, 30, 52, int(235 * a)),
                           outline=(52, 211, 153, int(230 * a)), width=2)
            gfx.text_c(c, 960, 1022,
                       'چپ: تصمیم می‌گیرید چه اتفاقی بیفتد  →  Start  →  راست: نتیجه',
                       26, 'semibold', tuple(int(v * a) for v in TXT))
        if t > 43:
            a = fade_in(t, 43, 1)
            gfx.text_c(c, 960, 1075, 'هر کنترلِ چپ روی یک کانفیگ مشترک نوشته می‌شود؛ '
                                     'تغییرات ساختاری در Start بعدی اعمال می‌شوند',
                       23, 'regular', tuple(int(v * a) for v in TXT_DIM))
