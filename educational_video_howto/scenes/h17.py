"""H17 — Recommended learning scenarios."""
import gfx
from palette import (W, H, TXT, TXT_DIM, C_OK, C_INS, C_WARN, C_BAD, C_EST)
from common_h import Scene, seg, ease, fade_in, header

SCEN = [
    ('سناریوی ۱ — چک سلامت', 'آزمایش ۱: Perfect IMU',
     'Fused روی نویز GNSS بنشیند؛ σ پایدار؛ نشسته؟ یعنی سیستم سالم است', C_OK, 6),
    ('سناریوی ۲ — دیدن بایاس', 'آزمایش ۲: فقط بایاس ژیرو',
     'اول mode=ins و رشد t² را ببینید؛ بعد loose و همگرایی calBg را', C_INS, 18),
    ('سناریوی ۳ — صداقت فیلتر', 'آزمایش ۶: dropout',
     'σ در دل قطعی رشد می‌کند؛ بعد از بازگشت، سقوط می‌کند', C_WARN, 30),
    ('سناریوی ۴ — تراز', 'v=0 + alignment با مدت بلند',
     'در Attitude خط magenta را ببینید؛ بعد مدت را کم کنید و هزینه را', C_EST, 42),
    ('سناریوی ۵ — مقاومت', 'آزمایش ۹: dt متغیر',
     'INS باید در هر دو حالت سازگار بماند', C_BAD, 54),
]


class H17(Scene):
    name = 'H17'

    def draw(self, c, t):
        header(c, 'پنج سناریوی یادگیری', C_OK, t)
        x0, y0, x1, y1 = 90, 150, 1830, 900
        yy = y0
        for (title, en, fa, col, ti) in SCEN:
            a = ease(seg(t, ti, ti + 1.4))
            if a <= 0:
                yy += 148
                continue
            gfx.soft_rrect(c, (x0, yy, x1, yy + 128), 14,
                           fill=(16, 24, 46, int(235 * a)),
                           outline=col + (int(220 * a),), width=2)
            d = gfx.ImageDraw.Draw(c)
            d.rounded_rectangle([x1 - 10, yy + 14, x1 - 2, yy + 114], radius=4,
                                fill=col + (int(255 * a),))
            gfx.text(c, (x1 - 36, yy + 20), title, 27, 'bold',
                     tuple(int(v * a) for v in col), 'right')
            gfx.text(c, (x1 - 36, yy + 62), en, 24, 'semibold',
                     tuple(int(v * a) for v in (34, 211, 238)), 'right')
            gfx.text(c, (x1 - 36, yy + 98), fa, 21, 'regular',
                     tuple(int(v * a) for v in TXT_DIM), 'right')
            yy += 148
        if t > 66:
            a = fade_in(t, 66, 1.2)
            gfx.soft_rrect(c, (150, 940, 1770, 1050), 16,
                           fill=(24, 40, 60, int(235 * a)),
                           outline=(52, 211, 153, int(235 * a)), width=3)
            gfx.text_c(c, 960, 962, 'قانون طلایی:', 28, 'bold',
                       tuple(int(v * a) for v in (251, 191, 36)))
            gfx.text_c(c, 960, 1006,
                       'یک متغیر در هر بار  +  seed ثابت  +  پیش از اجرا، نتیجه را پیش‌بینی کنید',
                       26, 'semibold', tuple(int(v * a) for v in TXT))
