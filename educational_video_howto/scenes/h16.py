"""H16 — runAllTests."""
import gfx
from palette import (W, H, TXT, TXT_DIM, C_OK, C_INS, C_WARN, TXT_FAINT)
from common_h import Scene, seg, ease, fade_in, header

TESTS = [
    'test_utils — تبدیل‌های دوران و LLA',
    'test_perfect_match — سنسور بی‌خطا = Truth',
    'test_ins_drift — دریفت ژیرو/شتاب‌سنج',
    'test_ekf_convergence — همگرایی فیلتر',
    'test_alignment — تراز اولیه',
    'test_variable_dt — dt متغیر',
    'test_gnss_dropout — قطعی GNSS',
    'test_time_alignment — تراز زمانی',
    'test_trajectory — هر ۹ مسیر',
    'test_runtime_updates — آپدیت حین اجرا',
    'test_high_fidelity — مدل کامل WGS84',
    'test_robust_oosm — گیت و OOSM',
    'test_aiding — بارومتر و ZUPT',
    'test_advanced_imu — اثرات پیشرفته',
]


class H16(Scene):
    name = 'H16'

    def draw(self, c, t):
        header(c, 'runAllTests: اعتبارسنجی عددی', C_OK, t)
        # terminal mock
        x0, y0, x1, y1 = 120, 150, 1800, 950
        gfx.soft_rrect(c, (x0, y0, x1, y1), 14, fill=(8, 12, 24, 255),
                       outline=(60, 78, 130, 255), width=2)
        d = gfx.ImageDraw.Draw(c)
        d.rounded_rectangle([x0, y0, x1, y0 + 40], radius=14,
                            fill=(22, 32, 60, 255))
        gfx.text_c(c, (x0 + x1) / 2, y0 + 6, 'MATLAB — Command Window', 17,
                   'semibold', TXT_DIM)
        a = fade_in(t, 2, 0.8)
        gfx.text(c, (x1 - 40, y0 + 62), '>> startup', 26, 'semibold',
                 tuple(int(v * a) for v in (34, 211, 238)), 'right')
        a = fade_in(t, 5, 0.8)
        gfx.text(c, (x1 - 40, y0 + 104), '>> runAllTests', 26, 'semibold',
                 tuple(int(v * a) for v in (34, 211, 238)), 'right')
        yy = y0 + 160
        for i, nm in enumerate(TESTS):
            ti = 8 + i * 3.2
            aa = ease(seg(t, ti, ti + 0.6))
            if aa <= 0:
                yy += 38
                continue
            gfx.text(c, (x1 - 60, yy), f'[PASS] {nm}', 21, 'regular',
                     tuple(int(v * aa) for v in C_OK), 'right')
            yy += 38
        if t > 56:
            a = fade_in(t, 56, 0.8)
            d.line([(x0 + 60, yy + 10), (x1 - 60, yy + 10)],
                   fill=(90, 108, 150, 255), width=2)
            gfx.text(c, (x1 - 60, yy + 24), 'Result: 14 passed, 0 failed', 26,
                     'black', tuple(int(v * a) for v in C_OK), 'right')
        if t > 64:
            a = fade_in(t, 64, 1)
            gfx.text_c(c, (x0 + x1) / 2, y1 + 40,
                       'فیل شود → با خطا متوقف (مناسب CI)   |   آینه پایتونی: python tools/run_mirror_tests.py',
                       22, 'regular', tuple(int(v * a) for v in TXT_DIM))
        if t > 72:
            a = fade_in(t, 72, 1)
            gfx.soft_rrect(c, (300, y1 + 66, 1620, y1 + 130), 12,
                           fill=(20, 30, 52, int(235 * a)),
                           outline=(52, 211, 153, int(230 * a)), width=2)
            gfx.text_c(c, 960, y1 + 80,
                       'GUI پنجرهٔ روی همان موتور است؛ تست‌ها همان موتور را تست می‌کنند',
                       25, 'semibold', tuple(int(v * a) for v in C_OK))
