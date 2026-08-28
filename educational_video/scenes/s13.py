"""S13 — the 9-step loop inside SimEngine."""
import gfx
from palette import (W, H, TXT, TXT_DIM, TXT_FAINT, C_INS, C_GNSS, C_CALIB,
                     C_PRED, C_FUSION, C_BARO, C_ZUPT, C_OOSM, C_TRAJ,
                     C_TRUTH, C_OK, C_WARN)
from common import Scene, seg, ease, fade_in, header, card

STEPS = [
    ('۱', 'مسیر در زمان t', C_TRAJ, 5),
    ('۲', 'Truth (WGS84 + نرخ‌های زمین)', C_TRUTH, 12),
    ('۳', 'اندازه‌گیری IMU (با همهٔ خطاها)', C_INS, 19),
    ('۴', 'به‌روزرسانی GNSS + بارومتر', C_GNSS, 26),
    ('۵', 'کالیبراسیون: کم‌کردن بایاس تخمینی', C_CALIB, 33),
    ('۶', 'به‌روزرسانی سنجش (NIS + OOSM)', C_FUSION, 40),
    ('۷', 'ZUPT + بارومتر (اگر فعال)', C_ZUPT, 48),
    ('۸', 'ثبت وضعیت در لحظهٔ دقیقِ t', C_OK, 55),
    ('۹', 'INS step + EKF predict: t → t+dt', C_PRED, 66),
]


class S13(Scene):
    name = 'S13'

    def draw(self, c, t):
        D = self.dur
        header(c, 'داخل هر گام: SimEngine.step', C_INS, t)

        for i, (num, label, col, ti) in enumerate(STEPS):
            a = ease(seg(t, ti, ti + 0.9))
            if a <= 0:
                continue
            col_i = i % 3
            row_i = i // 3
            x = 1700 - col_i * 580
            y = 180 + row_i * 235
            x0, y0, x1, y1 = x - 270, y, x + 270, y + 190
            active = (i == self._active(t))
            gfx.soft_rrect(c, (x0, y0, x1, y1), 14,
                           fill=(19, 28, 51, int(235 * a)),
                           outline=col, width=4 if active else 2)
            if active:
                gfx.glow(c, ((x0 + x1) / 2, (y0 + y1) / 2), 100, col, 60)
            d = gfx.ImageDraw.Draw(c)
            d.ellipse([x1 - 52, y0 + 16, x1 - 8, y0 + 60], fill=col + (int(255 * a),))
            gfx.text_c(c, x1 - 30, y0 + 22, num, 24, 'bold', (10, 20, 40))
            for j, ln in enumerate(gfx_lines(label, 24)):
                gfx.text_c(c, (x0 + x1) / 2, y0 + 74 + j * 40, ln, 24, 'semibold',
                           tuple(int(v * a) for v in TXT))
            if i < 8:
                if col_i < 2:
                    ar = ((x0 - 8, y0 + 95), (x0 - 34, y0 + 95))
                else:
                    ar = ((x1 - 100, y1 + 6), (x1 - 100, y1 + 32))
                d = gfx.ImageDraw.Draw(c)
                gfx.arrow(d, ar[0], ar[1], (96, 116, 160), 3, 10)
        if t > 58:
            a = ease(seg(t, 58, 60))
            x0, y0, x1, y1 = 90, 905, 1830, 1050
            gfx.soft_rrect(c, (x0, y0, x1, y1), 14, fill=(24, 35, 66, int(225 * a)),
                           outline=C_OK + (int(200 * a),), width=2)
            d = gfx.ImageDraw.Draw(c)
            d.rounded_rectangle([x1 - 10, y0 + 12, x1 - 2, y1 - 12], radius=4,
                                fill=C_OK + (int(255 * a),))
            gfx.text(c, (x1 - 36, y0 + 16),
                     'تصمیم طراحی آگاهانه: INS دقیقاً در t لاگ/تصحیح می‌شود؛ انتگرال‌گیری به t+dt در انتهای گام',
                     25, 'semibold', tuple(int(v * a) for v in TXT), 'right')
            gfx.text(c, (x1 - 36, y0 + 60),
                     'این دقیق‌سازی زمانی از کشف یک خطای یک‌گامی در تست‌ها به‌دست آمد',
                     22, 'regular', tuple(int(v * a) for v in TXT_DIM), 'right')
        if t > 74:
            a = fade_in(t, 74, 1)
            gfx.chip(c, 1560, 960, 'align → nav → done', C_INS, size=24,
                     label_color=TXT)
            gfx.text(c, (1230, 930), 'فازی‌ها:', 24, 'semibold',
                     tuple(int(v * a) for v in TXT_DIM), 'right')
        if t > 82:
            a = fade_in(t, 82, 1)
            gfx.text_c(c, 960, 1062,
                       'موتور بدون گرافیک: GUI + تست‌ها + Experimentها روی همین موتور واحد',
                       24, 'semibold', tuple(int(v * a) for v in C_WARN))

    @staticmethod
    def _active(t):
        idx = -1
        for i, (_, _, _, ti) in enumerate(STEPS):
            if t >= ti:
                idx = i
        return idx


def gfx_lines(text, size):
    import fa_text
    return fa_text.wrap_width(text, size, 'regular', 460)
