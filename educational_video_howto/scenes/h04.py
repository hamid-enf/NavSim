"""H04 — Trajectory tab."""
import gfx
from palette import C_TRAJ, C_OK, C_INS, TXT, TXT_DIM
from common_h import (Scene, seg, ease, fade_in, header, gui_mock)

TRAJ = [
    ('Straight', 'خط مستقیم — پایهٔ مینیمال'),
    ('Circle', 'دوربرد هم‌راستا — پیش‌فرض'),
    ('FigureEight', 'هفت‌هشتی لِساج — پرمانور'),
    ('Acceleration', 'شتاب طولی ثابت'),
    ('Climb/Descent', 'صعود / فرود ثابت'),
    ('Turn', 'ورود نرم به دوربرد'),
    ('Combined3D', 'دایره + عمودی — کامل‌ترین'),
    ('UserDefined', 'عبارت دلخواه p(t)'),
]

ITEMS = [
    (46, 'speed', '15 m/s', 'سرعت مرجع'),
    (50, 'radius', '200 m', 'شعاع دوربرد / مقیاس'),
    (54, 'alt0', '100 m', 'ارتفاع اولیه'),
    (58, 'climbRate', '3 m/s', 'نرخ صعود/فرود'),
    (62, 'turnRate', '3 °/s', 'نرخ چرخش (Turn)'),
    (66, 'heading0', '0 °', 'جهت اولیه'),
    (70, 'accel', '1.5 m/s²', 'شتاب (Acceleration)'),
]


class H04(Scene):
    name = 'H04'

    def draw(self, c, t):
        header(c, 'تب Trajectory: حرکت مرجع', C_TRAJ, t)
        gui_mock(c, 1, (90, 150, 700, 1010), t=t)

        x0, y0, x1, y1 = 740, 150, 1830, 1010
        gfx.panel(c, (x0, y0, x1, y1))
        d = gfx.ImageDraw.Draw(c)
        d.rounded_rectangle([x1 - 10, y0 + 14, x1 - 2, y1 - 14], radius=4,
                            fill=(255, 255, 255, 255))
        gfx.text(c, (x1 - 36, y0 + 18), 'مسیر = حقیقتی که کل شبیه‌سازی روی آن سوار است',
                 26, 'bold', TXT, 'right')
        # trajectory chips 2 rows x 4
        a = ease(seg(t, 3, 4))
        for i, (nm, fa) in enumerate(TRAJ):
            ti = 4 + i * 1.4
            aa = ease(seg(t, ti, ti + 0.8))
            if aa <= 0:
                continue
            col_i = i % 4
            row_i = i // 4
            x = x1 - 60 - col_i * 252
            y = y0 + 84 + row_i * 56
            act = (nm == 'Circle')
            col = C_OK if act else (148, 163, 184)
            gfx.chip(c, x - 110, y, nm, col, size=19, pad_x=14, pad_y=8,
                     alpha_fill=60 if act else 14,
                     label_color=(15, 23, 42) if act else (242, 246, 255))
        # userExpr box
        if t > 34:
            aa = ease(seg(t, 34, 36))
            gfx.soft_rrect(c, (x0 + 20, y0 + 216, x1 - 20, y0 + 284), 10,
                           fill=(10, 16, 30, int(235 * aa)),
                           outline=(52, 211, 153, int(220 * aa)), width=2)
            gfx.text(c, (x1 - 40, y0 + 226),
                     'UserDefined:  [10*t ; 100*sin(0.05*t) ; -100]  —  سرعت و شتاب عددی مشتق می‌شوند',
                     21, 'semibold', tuple(int(v * aa) for v in (52, 211, 153)), 'right')
        # params
        yy = y0 + 316
        for (ti, en, default, fa) in ITEMS:
            a = fade_in(t, ti, 0.7)
            if a <= 0:
                yy += 46
                continue
            gfx.text(c, (x1 - 40, yy), en, 21, 'bold',
                     tuple(int(v * a) for v in C_INS), 'right')
            gfx.text(c, (x1 - 40 - 330, yy + 2), f'= {default}', 21, 'semibold',
                     tuple(int(v * a) for v in (34, 211, 238)), 'right')
            gfx.text(c, (x1 - 40, yy + 28), fa, 19, 'regular',
                     tuple(int(v * a) for v in TXT_DIM), 'right')
            yy += 46
        if t > 84:
            a = fade_in(t, 84, 1)
            gfx.soft_rrect(c, (x0 + 20, y1 - 58, x1 - 20, y1 - 12), 10,
                           fill=(24, 40, 60, int(235 * a)),
                           outline=(251, 191, 36, int(230 * a)), width=2)
            gfx.text_c(c, (x0 + x1) / 2, y1 - 48,
                       'قانون طلایی: در خط مستقیم خطای وضعیت قابل‌مشاهده نیست؛ در دایره و هفت‌هشتی هست',
                       22, 'semibold', tuple(int(v * a) for v in (251, 191, 36)))
