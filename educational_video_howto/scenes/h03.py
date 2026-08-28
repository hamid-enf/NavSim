"""H03 — Simulation tab."""
import gfx
from palette import C_INS, C_WARN, TXT_DIM
from common_h import Scene, fade_in, tab_scene

ITEMS = [
    (3, 'IMU dt', '0.01 s  (100 Hz)',
     'گام پایهٔ انتگرال‌گیری؛ بزرگ‌تر = درشت‌تر + نویز نمونه بیشتر', C_INS),
    (10, 'Duration', '120 s',
     'مدت شبیه‌سازی؛ برای دیدن دریفت و فرصت یادگیری بایاس کافی باشد', C_INS),
    (18, 'RNG seed', '1',
     'بذر تصادفی — همان seed یعنی همان نویز؛ کلید تکرارپذیری مقایسه‌ها', C_WARN),
    (28, 'Run mode', 'realtime | fast',
     'realtime با ساعت واقعی؛ fast با تمام سرعت — برای تحلیل، fast', C_INS),
    (36, 'Fast chunk', '400 steps/tick',
     'در حالت fast چند گام در هر بروزرسانی GUI اجرا شود', TXT_DIM),
    (44, 'Variable dt', 'off | jitter | tworate',
     'off عادی؛ jitter = خطای زمان‌بندی تصادفی؛ tworate دو نرخ متناوب', C_WARN),
    (52, 'dtJitter', '0.5  (fraction)',
     'اندازهٔ jitter در حالت jitter — ابزار تستِ مقاومت در برابر timing error', C_WARN),
]


class H03(Scene):
    name = 'H03'

    def draw(self, c, t):
        tab_scene(c, t, 0, 'تب Simulation: ساعت شبیه‌سازی', C_INS, ITEMS,
                  footer='هر وقت دو اجرا را مقایسه می‌کنید، seed را ثابت نگه دارید',
                  footer_t=62)
