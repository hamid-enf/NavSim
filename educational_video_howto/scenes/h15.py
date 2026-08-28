"""H15 — Logging."""
import gfx
from palette import (W, H, TXT, TXT_DIM, C_EST, C_OK, C_INS, C_WARN)
from common_h import Scene, seg, ease, fade_in, header, gui_mock

FIELDS = [
    ('t , dt', 'زمان و گام هر IMU step', 6),
    ('truthP/V/E', 'موقعیت/سرعت/وضعیت واقعی', 10),
    ('gyroT/M ، accT/M', 'واقعی در برابر اندازه‌شده + بایاس واقعی', 15),
    ('insP/V/E ، fusP/V/E', 'خروجی INS خالص و Fused', 20),
    ('calBg ، calBa', 'تخمین بایاس‌ها در طول زمان', 25),
    ('gnssP + gnssFlag', '۱=سنجش ۲=پرت تزریق‌شده ۳=رد NIS ۴=ندارد', 30),
    ('gnssTMeas / OOSM', 'epoch فیزیکی + خارج از ترتیب؟', 36),
    ('baroH + baroFlag ، zupt', 'بارومتر و وضعیت ZUPT', 41),
    ('sigP/V/A ، NIS ، alignEst', 'سیگماها ، نویشن ، تخمین تراز', 46),
]


class H15(Scene):
    name = 'H15'

    def draw(self, c, t):
        header(c, 'تب Logs: ذخیره و بازبینی', C_EST, t)
        gui_mock(c, 9, (90, 150, 700, 1010), t=t)
        x0, y0, x1, y1 = 740, 150, 1830, 1010
        gfx.panel(c, (x0, y0, x1, y1))
        d = gfx.ImageDraw.Draw(c)
        d.rounded_rectangle([x1 - 10, y0 + 14, x1 - 2, y1 - 14], radius=4,
                            fill=C_EST + (255,))
        a = fade_in(t, 2, 0.8)
        gfx.text(c, (x1 - 36, y0 + 18), 'داخل لاگ برای هر گام IMU:', 28, 'bold',
                 tuple(int(v * a) for v in TXT), 'right')
        yy = y0 + 80
        for (en, fa, ti) in FIELDS:
            aa = ease(seg(t, ti, ti + 0.9))
            if aa <= 0:
                yy += 72
                continue
            gfx.soft_rrect(c, (x0 + 30, yy, x1 - 30, yy + 58), 10,
                           fill=(16, 24, 46, int(235 * aa)),
                           outline=(56, 189, 248, int(150 * aa),), width=1)
            gfx.text(c, (x1 - 44, yy + 8), en, 21, 'semibold',
                     tuple(int(v * aa) for v in (34, 211, 238)), 'right')
            gfx.text(c, (x1 - 560, yy + 12), fa, 20, 'regular',
                     tuple(int(v * aa) for v in TXT_DIM), 'right')
            yy += 72
        if t > 54:
            a = fade_in(t, 54, 1)
            gfx.soft_rrect(c, (x0 + 30, y1 - 150, x1 - 30, y1 - 16), 12,
                           fill=(24, 40, 60, int(235 * a)),
                           outline=(52, 211, 153, int(230 * a)), width=2)
            gfx.text_c(c, (x0 + x1) / 2, y1 - 124,
                       'Save MAT / CSV  +  Load MAT & view (بدون اجرا)  +  Replay animation در 3D View',
                       23, 'semibold', tuple(int(v * a) for v in C_OK))
            gfx.text_c(c, (x0 + x1) / 2, y1 - 76,
                       'پروتکل: هر تست معنادار را با نامی که توصیفش می‌کند ذخیره کنید',
                       21, 'regular', tuple(int(v * a) for v in TXT_DIM))
