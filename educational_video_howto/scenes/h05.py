"""H05 — IMU tab."""
from common_h import Scene, fade_in, tab_scene
from palette import C_IMU, C_INS, C_WARN, C_BAD, C_CALIB, TXT_DIM

ITEMS = [
    (3, 'useGyroBias + gyroBiasDps', '0.02 °/s',
     'بایاس ثابت ژیرو — در یک دقیقه ≈ ۱٫۲° خطای وضعیت', C_IMU),
    (10, 'accelBiasMg', '[2 -1.5 1] mg',
     'بایاس شتاب‌سنج به میلی‌جی؛ ۱mg ≈ ۱۰⁻ m/s²', C_IMU),
    (18, 'gyroARWDpsHz', '0.01 °/s/√Hz',
     'چگالی random walk زاویه ۳ژیرو — نویز نمونه = چگالی/√dt', C_INS),
    (25, 'accelVRW', '0.02 m/s/√Hz',
     'random walk سرعت شتاب‌سنج', C_INS),
    (32, 'useGyroSF + ppm', '[50 -30 20] ppm',
     'ضریب مقیاس: ۵۰ppm = ۰٫۰۰۵٪ بیشتر اندازه‌گیری', C_WARN),
    (39, 'gyroMisDeg', '[0.02 0.01 -0.015]',
     'کج‌بودن محورها (نه دقیقاً عمود بر هم) به درجه', C_WARN),
    (46, 'biasModel', 'randomwalk | gaussmarkov',
     'بایاس خالص‌دریفت‌دار یا حافظه‌دار (به صفر برمی‌گردد)', C_CALIB),
    (53, 'gyroBiasTau', '3600 s',
     'زمان همبستگی در حالت gaussmarkov — پیش‌فرض یک ساعت', C_CALIB),
    (60, 'gyroBiasRW / accelBiasRW', '0 (off)',
     'نویز راه‌انداز بایاس — وقتی بزرگ‌تر از صفر فعال می‌شود', C_CALIB),
    (67, 'gyroSaturationDps', '400 °/s', 'سقف خروجی ژیرو (تشبیط)', C_BAD),
    (73, 'accelSaturationG', '20 g', 'سقف خروجی شتاب‌سنج', C_BAD),
    (79, 'quantization', '0 (off)', 'LSB خروجی دیجیتال', C_BAD),
    (85, 'gyroGSensitivity', '[0 0 0] °/s/g',
     'واکنش ژیرو به شتاب — اثر واقع‌گرایی', C_BAD),
]


class H05(Scene):
    name = 'H05'

    def draw(self, c, t):
        tab_scene(c, t, 2, 'تب IMU: منبع هر دریفت', C_IMU, ITEMS,
                  footer='قانون طلایی: یک منبع را روشن کنید؛ اثرش کجا است — '
                         'وضعیت، سرعت، یا موقعیت؟', footer_t=95)
