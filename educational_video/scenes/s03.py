"""S03 — Trajectory & Truth."""
import math

import gfx
from palette import (W, H, TXT, TXT_DIM, TXT_FAINT, C_TRAJ, C_TRUTH, C_INS,
                     C_WARN, C_OK, C_BAD)
from common import Scene, seg, ease, fade_in, header, card, vehicle

TRAJ_TYPES = ['Straight', 'Circle', 'FigureEight', 'Acceleration', 'Climb',
              'Descent', 'Turn', 'Combined3D', 'UserDefined']


class S03(Scene):
    name = 'S03'

    def draw(self, c, t):
        D = self.dur
        header(c, 'مسیر و حالت واقعی (Truth)', C_TRAJ, t)

        # ---- right: animated circle ----
        a = ease(seg(t, 0.8, 2.0))
        if a > 0:
            cx, cy, R = 1350, 500, 230
            d = gfx.ImageDraw.Draw(c)
            ax = 1000
            ay = 800
            d.line([(ax, ay), (ax, ay - 90)], fill=(148, 163, 184, 255), width=3)
            d.line([(ax, ay), (ax + 90, ay)], fill=(148, 163, 184, 255), width=3)
            d.line([(ax, ay), (ax, ay + 60)], fill=(110, 128, 165, 255), width=3)
            gfx.text_c(c, ax, ay - 110, 'N', 24, 'bold', TXT_DIM)
            gfx.text_c(c, ax + 108, ay, 'E', 24, 'bold', TXT_DIM)
            gfx.text_c(c, ax, ay + 76, 'D', 24, 'bold', TXT_DIM)
            d.ellipse([cx - R, cy - R, cx + R, cy + R],
                      outline=(148, 163, 184, int(200 * a)), width=3)
            th = 0.35 * (t - 0.8)
            px = cx + R * math.cos(th)
            py = cy - R * math.sin(th)
            gfx.line(d, (cx, cy), (px, py), (96, 116, 160, 255), width=2, dash=8)
            d.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=(96, 116, 160, 255))
            gfx.text_c(c, cx + 40, cy - R - 40, 'R = 200 m', 26, 'semibold', TXT)
            gfx.text_c(c, cx, cy + R + 44, 'V = 15 m/s   ω = V/R = 0.075 rad/s',
                       26, 'semibold', TXT)
            vehicle(c, px, py, 1.5, -th - math.pi / 2, C_INS)
        # ---- left: why circle ----
        a = ease(seg(t, 12, 14))
        if a > 0:
            x0, y0, x1, y1 = 90, 170, 870, 430
            card(c, (x0, y0, x1, y1), 'چرا دایره؟', C_WARN)
            lines = [
                ('دایره = مانور با شتاب عرضی', 14, TXT),
                ('a_lat = V²/R ≈ 1.1 m/s²', 18, C_WARN),
                ('مانور به فیلتر اجازه می‌دهد خطای', 22, TXT),
                ('وضعیت را ببیند و بایاس را تخمین بزند', 24, TXT),
                ('مسیر خطی بدون مانور: حالت‌های فیلتر', 28, TXT),
                ('قابل‌مشاهده نمی‌شوند (→ آزمایش ۷)', 30, C_BAD),
            ]
            yy = y0 + 70
            for s, ti, col in lines:
                aa = fade_in(t, ti)
                if aa <= 0:
                    yy += 40
                    continue
                gfx.text(c, (x1 - 30, yy), s, 25, 'semibold' if col != TXT else 'regular',
                         tuple(int(v * aa) for v in col), 'right')
                yy += 40
        # ---- left: NED + outputs ----
        a = ease(seg(t, 34, 36))
        if a > 0:
            x0, y0, x1, y1 = 90, 460, 870, 620
            card(c, (x0, y0, x1, y1), 'خروجی در فریم NED', C_INS)
            d = gfx.ImageDraw.Draw(c)
            for s, ti in [('N: شمال   E: شرق   D: پایین', 36),
                          ('p: موقعیت [m]   v: سرعت [m/s]   a: شتاب [m/s²]', 40)]:
                aa = fade_in(t, ti)
                if aa <= 0:
                    continue
                gfx.text(c, (x1 - 30, y0 + 70 + (0 if 'N:' in s else 46)), s,
                         25, 'regular', tuple(int(v * aa) for v in TXT), 'right')
        # 9 trajectory chips
        if t > 38:
            for i, name in enumerate(TRAJ_TYPES):
                a = ease(seg(t, 38 + i * 0.35, 38.6 + i * 0.35))
                if a <= 0:
                    continue
                x = 870 - (i % 3) * 260
                y = 688 + (i // 3) * 62
                act = (name == 'Circle')
                gfx.chip(c, x - 110, y, name, C_OK if act else C_TRAJ, size=22,
                         alpha_fill=50 if act else 14, outline_w=3 if act else 1)
            a = fade_in(t, 38, 0.8)
            gfx.text(c, (870, 648), '۹ مسیر کتابخانه + عبارت دلخواه کاربر', 24,
                     'regular', tuple(int(v * a) for v in TXT_DIM), 'right')
        # ---- bottom: attitude from velocity ----
        a = ease(seg(t, 48, 50))
        if a > 0:
            x0, y0, x1, y1 = 90, 860, 1830, 1030
            gfx.panel(c, (x0, y0, x1, y1))
            gfx.text(c, (x1 - 30, y0 + 16), 'وضعیت از خودِ سرعت ساخته می‌شود (فیزیکِ واقعی)',
                     28, 'bold', tuple(int(v * a) for v in TXT))
            d = gfx.ImageDraw.Draw(c)
            d.rounded_rectangle([x1 - 12, y0 + 12, x1 - 4, y1 - 12], radius=4,
                                fill=(251, 191, 36, int(255 * a)))
            items = [
                ('yaw = atan2(vE, vN)', 'جهت حرکت', 50),
                ('pitch = atan2(−vD, Vh)', 'زاویه مسیر پرواز', 56),
                ('roll = atan(V·ψ̇ / g)', 'چرخش هماهنگ (bank)', 62),
            ]
            xx = x1 - 60
            for eq, desc, ti in items:
                aa = fade_in(t, ti)
                if aa <= 0:
                    xx -= 560
                    continue
                d2 = gfx.ImageDraw.Draw(c)
                d2.rounded_rectangle([xx - 520, y0 + 56, xx - 20, y0 + 140],
                                     radius=12, fill=(24, 35, 66, int(220 * aa)),
                                     outline=(60, 78, 130, int(255 * aa)), width=2)
                gfx.text_c(c, xx - 270, y0 + 80, eq, 30, 'semibold',
                           tuple(int(v * aa) for v in (34, 211, 238)))
                gfx.text_c(c, xx - 270, y0 + 122, desc, 22, 'regular',
                           tuple(int(v * aa) for v in TXT_DIM))
                xx -= 560
        a = fade_in(t, 70, 1)
        if a > 0:
            gfx.text_c(c, 960, 1055, 'اگر Truth فیزیکی نباشد، ورودی IMU واقعی نیست — و کل درس اشتباه می‌شود',
                       26, 'semibold', tuple(int(v * a) for v in C_WARN))
