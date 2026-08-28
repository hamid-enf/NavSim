"""H06 — GNSS tab."""
from common_h import Scene, fade_in, tab_scene
from palette import C_GNSS, C_INS, C_WARN, C_BAD, C_BARO, TXT_DIM

ITEMS = [
    (3, 'rate', '1 Hz', 'نرخ رسیور — واقع‌بینانه برای کم‌هزینه', C_GNSS),
    (8, 'posSigmaH / posSigmaV', '1.5 / 3.0 m',
     'نویز افقی/عمودی — عمودی بدتر است (هندسهٔ ماهواره‌ها/DOP)', C_GNSS),
    (15, 'enableVel + velSigma', '0.05 m/s',
     'سنجش سرعت در فیوژن (اختیاری)', TXT_DIM),
    (20, 'biasNed', '[0 0 0] m', 'بایاس ثابت شمال/شرق/پایین — مثل آنتن بد', C_WARN),
    (26, 'useDropout + dropoutText', '"30 60; 90 100"',
     'پنجره‌های قطعی به ثانیه: «شروع پایان؛ شروع پایان» — مثل تونل', C_BAD),
    (35, 'randDropProb', '0 (off)', 'احتمال قطعی تصادفی در هر epoch', C_BAD),
    (41, 'useOutlier + outlierProb', '0.02',
     'احتمال پرت در هر epoch — تداخل/multipath', C_BAD),
    (48, 'outlierMag', '50 m', 'اندازهٔ جهشِ پرت', C_BAD),
    (53, 'outlierVelSigma', '0 (off)',
     'بزرگ‌تر از صفر → آن epoch سرعت هم خراب می‌شود', C_BAD),
    (59, 'delay', '0 s', 'تأخیر تحویل — جایی که OOSM وارد می‌شود', C_WARN),
    (66, 'useGmNoise + gmSigma/gmTau', '2 m / 30 s',
     'نویز همبستهٔ گاوس-مارکوف شبیه multipath', C_BARO),
]


class H06(Scene):
    name = 'H06'

    def draw(self, c, t):
        tab_scene(c, t, 3, 'تب GNSS: رسیور ماهواره', C_GNSS, ITEMS,
                  footer='نکتهٔ درس: خطای GM در R نیست؛ با robustMode خاموش، '
                         'فیلتر بیش از حد مطمئن می‌شود', footer_t=76)
