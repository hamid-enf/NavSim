"""H09 — Fusion tab."""
from common_h import Scene, fade_in, tab_scene
from palette import (C_FUSION, C_INS, C_WARN, C_BAD, C_EST, C_ZUPT, TXT_DIM)

ITEMS = [
    (3, 'mode', 'ins | loose',
     'مهم‌ترین کلید: ins = دریفت خام؛ loose = فیوژن GNSS/INS', C_FUSION),
    (11, 'useVel', 'false', 'استفاده از سرعت GNSS در کنار موقعیت', TXT_DIM),
    (16, 'qa / qg', '0.005 / 0.02',
     'Q: اعتماد فیلتر به مدل — کوچک=آهسته‌تصحیح، بزرگ=لرزان', C_WARN),
    (24, 'qbg / qba', '0.002 / 0.005', 'random walk بایاس ژیرو/شتاب‌سنج', C_WARN),
    (30, 'p0pos / p0vel', '5 m / 0.1 m/s',
     'P صفر: باید کیفیت تراز اولیه را بازتاب کند', C_EST),
    (37, 'p0attDeg / p0gyroBiasDps', '5 ° / 0.1 °/s', 'عدم‌قطعیت وضعیت/بایاس اولیه', C_EST),
    (44, 'p0accelBias', '0.3 m/s²', 'عدم‌قطعیت بایاس شتاب‌سنج اولیه', C_EST),
    (50, 'qScale / rScale', '1 / 1',
     'ضریب تجربهٔ سریع — Q را دو برابر کنید بدون ویرایش', C_WARN),
    (56, 'robustMode', 'off | reject | adaptive',
     'گیت نویشن: رد پرت‌ها یا بادکردن R', C_BAD),
    (64, 'nisGatePos / nisGateVel', '16.27 (χ² 99.9%)',
     'آستانهٔ کای-دو، ۳ درجه آزادی — فقط پرت‌های بزرگ', C_BAD),
    (71, 'maxRInflation', '100', 'سقف بادکردن R در حالت adaptive', C_BAD),
    (77, 'useOOSM / oosmLag', 'true / 12 s',
     'سنجش دیررس روی epoch خودش اعمال شود', C_INS),
    (84, 'nisGateBaro', '10.83 (χ² 1 dof)', 'گیت جداگانهٔ بارومتر', TXT_DIM),
    (90, 'useZupt + gates', 'σ=0.05 m/s',
     'شبه‌سنجش v=0 در سکون (چراغ قرمز) + آستانه‌های سکون', C_ZUPT),
]


class H09(Scene):
    name = 'H09'

    def draw(self, c, t):
        tab_scene(c, t, 6, 'تب Fusion: مغز شبیه‌ساز', C_FUSION, ITEMS,
                  footer='پروتکل: همان تست را در mode=ins و loose اجرا کنید تا '
                         'ببینید فیلتر چه اضافه کرد', footer_t=100)
