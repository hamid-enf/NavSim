"""H01 — Intro & goal."""
import gfx
from palette import (W, H, TXT, TXT_DIM, C_INS, C_OK, C_WARN)
from common_h import Scene, seg, ease, fade_in, header


class H01(Scene):
    name = 'H01'

    def draw(self, c, t):
        D = self.dur
        header(c, 'ویدیوی دوم: راهنمای عملی NavSim', C_INS, t)
        a = ease(seg(t, 0.5, 1.8))
        if a > 0:
            gfx.text_c(c, W / 2, 170, 'از کاربرِ کلیک‌زن تا اپراتورِ مسلط', 40,
                       'black', tuple(int(v * a) for v in TXT))
            gfx.text_c(c, W / 2, 235,
                       'ویدیوی اول: فرایند بود (داده از کجا، به کجا، چرا) — این ویدیو: خودِ ابزار',
                       26, 'regular', tuple(int(v * a) for v in TXT_DIM))
        # 5 questions
        qs = [
            ('این برنامه دقیقاً چه چیزی است؟', 4),
            ('با آن چه چیزی را تست می‌کنیم؟', 8),
            ('چطور تست کنیم؟', 12),
            ('چه پارامترهایی می‌دهیم / چه چیزی برمی‌گردد؟', 16),
            ('هر تب و هر گزینه چه کاری انجام می‌دهد؟', 20),
        ]
        for i, (q, ti) in enumerate(qs):
            aa = ease(seg(t, ti, ti + 1))
            if aa <= 0:
                continue
            x = 1680 - i * 300
            d = gfx.ImageDraw.Draw(c)
            gfx.soft_rrect(c, (x - 140, 300, x + 140, 520), 14,
                           fill=(19, 28, 51, int(230 * aa)),
                           outline=(56, 189, 248, int(160 * aa)), width=2)
            d.ellipse([x + 90, 316, x + 124, 350], fill=(56, 189, 248, int(255 * aa),)
                      )
            gfx.text_c(c, x + 107, 322, f'؟{i + 1}' if False else str(i + 1), 20, 'bold',
                       (10, 20, 40))
            lines = []
            cur = ''
            for wd in q.split(' '):
                trial = (cur + ' ' + wd).strip()
                if len(trial) > 14:
                    lines.append(cur)
                    cur = wd
                else:
                    cur = trial
            if cur:
                lines.append(cur)
            yy = 372
            for ln in lines:
                gfx.text_c(c, (x - 140 + x + 140) / 2, yy, ln, 22, 'semibold',
                           tuple(int(v * aa) for v in TXT))
                yy += 34
        # run commands
        if t > 25:
            a = fade_in(t, 25, 1)
            gfx.text_c(c, 960, 590, 'باز کردن برنامه:', 28, 'bold',
                       tuple(int(v * a) for v in TXT))
            gfx.soft_rrect(c, (560, 640, 1360, 720), 12, fill=(10, 16, 30, 255),
                           outline=(60, 78, 130, 255), width=2)
            gfx.text(c, (1330, 660), '>> main', 34, 'semibold',
                     tuple(int(v * a) for v in (34, 211, 238)), 'right')
            gfx.text_c(c, 960, 745, '>> cd NavSim   و بعد   main   — همین', 24, 'regular',
                       tuple(int(v * a) for v in TXT_DIM))
            gfx.soft_rrect(c, (560, 790, 1360, 870), 12, fill=(10, 16, 30, 255),
                           outline=(60, 78, 130, 255), width=2)
            gfx.text(c, (1330, 810), '>> runAllTests', 34, 'semibold',
                     tuple(int(v * a) for v in (52, 211, 153)), 'right')
            gfx.text_c(c, 960, 895, 'اعتبارسنجی عددی — آخر ویدیو می‌رسیم بهش', 24,
                       'regular', tuple(int(v * a) for v in TXT_DIM))
        if t > 33:
            a = fade_in(t, 33, 1)
            gfx.chip(c, 960, 990, 'هدف: خودتان تست طراحی کنید، نتیجه را پیش‌بینی کنید، درست بخوانید',
                     C_OK, size=27)
