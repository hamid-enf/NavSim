"""H08 — INS & Align tab."""
from common_h import Scene, fade_in, tab_scene
from palette import C_CALIB, C_INS, C_WARN, C_BARO, C_BAD, TXT_DIM

ITEMS = [
    (3, 'refLat / refLon / refH', '50.478 / 12.365 / 430 m',
     'مرجع ژئودتیک — مبدأ فریم NED؛ همهٔ نمودارها نسبت به آن', C_CALIB),
    (11, 'earthModel', 'flat | wgs84',
     'flat: آموزشی با g ثابت؛ wgs84: local-level کامل', C_INS),
    (19, 'useEarthRate', 'true', 'جملهٔ چرخش زمین (ω_ie) — جدا روشن/خاموش', C_INS),
    (24, 'useTransportRate', 'true', 'جملهٔ نرخ ترابرد (ω_en) روی ellipsoid', C_INS),
    (29, 'useCoriolis', 'true', 'جملهٔ کوریولیس (2ω_ie+ω_en)×v', C_INS),
    (34, 'useConingSculling', 'false',
     'جبران خطای مرتبهٔ دوم ژیرو/شتاب‌سنج در مانور تند', C_WARN),
    (41, 'initPosErr / initVelErr', '[0 0 0]',
     'خطای اولیهٔ موقعیت/سرعت که خودتان تزریق می‌کنید', C_BAD),
    (47, 'Align.enabled / duration', 'true / 10 s',
     'فاز تراز قبل از ناوبری و مدت آن', C_CALIB),
    (54, 'coarseLevel', 'true',
     'در سکون: تراز رول/پیچ با شتاب‌سنج', C_CALIB),
    (60, 'magHeadingSigmaDeg', '1 °', 'دقت قطب‌نما برای یو', C_CALIB),
    (66, 'coarseMovingSigmaDeg', '3 °',
     'خطای درشت شروع با حرکت (transfer alignment)', C_WARN),
    (72, 'applyUserErr + userErrDeg', '[0 0 5] deg',
     'خطای اضافهٔ رول/پیچ/یو — مثلاً [2 2 10] برای آزمایش ۷', C_BAD),
]


class H08(Scene):
    name = 'H08'

    def draw(self, c, t):
        tab_scene(c, t, 5, 'تب INS و Align: مرجع، زمین، تراز', C_CALIB, ITEMS,
                  footer='سوئیچ‌های تک‌جمله‌ای (Earth/Transport/Coriolis) عالی‌اند '
                         'برای آزمایشِ اثر هر جمله', footer_t=84)
