"""H14 — Experiments tab."""
import gfx
from palette import (W, H, TXT, TXT_DIM, C_WARN, C_OK, C_INS, C_BAD, C_EST)
from common_h import Scene, seg, ease, fade_in, header, gui_mock

C_GNSS_C = (251, 146, 60)

EXPS = [
    ('1. Perfect IMU', 'Fused روی نویز GNSS — چک سلامت', C_OK, 14),
    ('2. Gyro Bias', 'در ins رشد t²؛ در loose: calBg → [0.51 -0.31 0.13]', C_INS, 22),
    ('3. Accel Bias', 'در ins: ½·b·t² — Fusion کران‌دار', C_INS, 30),
    ('4. IMU Noise', 'random walk — با Fusion محدود می‌شود', C_INS, 37),
    ('5. GNSS Noise', 'IMU کامل + σ=10m — Fused با R محدود', C_GNSS_C, 44),
    ('6. GNSS Dropout', 'در قطعی: ۳۰m در برابر ۱۰۲۲m؛ بعد: ۱٫۹m', C_BAD, 52),
    ('7. Align Error', '[2 2 10]° — فیلتر در مانور می‌آموزد', C_WARN, 60),
    ('8. INS vs Loose', 'مقایسهٔ خودکار + جدول آماری', C_OK, 67),
    ('9. Variable dt', 'jitter 50٪ — مقاومت به timing error', C_WARN, 74),
    ('10. Combined', 'همهٔ خطاها — سناریوی دنیای واقعی', C_BAD, 81),
]


class H14(Scene):
    name = 'H14'

    def draw(self, c, t):
        header(c, 'تب Experiments: مسیر یادگیری آماده', C_WARN, t)
        gui_mock(c, 8, (90, 150, 700, 1010), t=t)
        x0, y0, x1, y1 = 740, 150, 1830, 1010
        gfx.panel(c, (x0, y0, x1, y1))
        d = gfx.ImageDraw.Draw(c)
        d.rounded_rectangle([x1 - 10, y0 + 14, x1 - 2, y1 - 14], radius=4,
                            fill=C_WARN + (255,))
        a = fade_in(t, 2, 0.8)
        gfx.text(c, (x1 - 36, y0 + 18), 'ده آزمایش با نتیجهٔ مورد انتظارِ مشخص', 27,
                 'bold', tuple(int(v * a) for v in TXT), 'right')
        # two action buttons
        if t > 5:
            aa = ease(seg(t, 5, 6.5))
            gfx.soft_rrect(c, (x0 + 30, y0 + 66, x1 - 30, y0 + 110), 10,
                           fill=(16, 24, 46, int(235 * aa)),
                           outline=(52, 211, 153, int(230 * aa)), width=2)
            gfx.text_c(c, (x0 + 30 + x1 - 30) / 2, y0 + 72,
                       'Apply to Config  →  کانفیگ به UI، بعد Start: زنده تماشا',
                       21, 'semibold', tuple(int(v * aa) for v in (52, 211, 153)))
            gfx.soft_rrect(c, (x0 + 30, y0 + 122, x1 - 30, y0 + 166), 10,
                           fill=(16, 24, 46, int(235 * aa)),
                           outline=(56, 189, 248, int(230 * aa)), width=2)
            gfx.text_c(c, (x0 + 30 + x1 - 30) / 2, y0 + 128,
                       'Run Headless & Compare  →  فوراً، بدون GUI: نمودار + جدول rms/max/fin',
                       21, 'semibold', tuple(int(v * aa) for v in (56, 189, 248)))
        # experiment rows (2 cols x 5)
        for i, (nm, fa, col, ti) in enumerate(EXPS):
            aa = ease(seg(t, ti, ti + 1))
            if aa <= 0:
                continue
            col_i = i % 2
            row_i = i // 2
            x = x1 - 40 - col_i * 530
            y = y0 + 180 + row_i * 134
            gfx.soft_rrect(c, (x - 500, y, x, y + 116), 12,
                           fill=(16, 24, 46, int(235 * aa)),
                           outline=col + (int(200 * aa),), width=2)
            gfx.text(c, (x - 24, y + 12), nm, 22, 'bold',
                     tuple(int(v * aa) for v in col), 'right')
            lines = []
            cur = ''
            for wd in fa.split(' '):
                trial = (cur + ' ' + wd).strip()
                if len(trial) > 24:
                    lines.append(cur)
                    cur = wd
                else:
                    cur = trial
            if cur:
                lines.append(cur)
            lyy = y + 48
            for ln in lines:
                gfx.text(c, (x - 24, lyy), ln, 19, 'regular',
                         tuple(int(v * aa) for v in TXT_DIM), 'right')
                lyy += 28
