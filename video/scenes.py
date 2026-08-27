# -*- coding: utf-8 -*-
"""Scene definitions for the NavSim educational animation (Persian, 4K)."""
import math
import os
import numpy as np
from lib import *


# ------------------------------ shared layout ------------------------------
PIPE_LABELS = [('traj', 'مسیر'), ('truth', 'حقیقت'), ('imu', 'IMU'),
               ('calib', 'کالیبراسیون'), ('ins', 'INS'), ('pred', 'پیش‌بینی'),
               ('fusion', 'تلفیق'), ('out', 'تخمین'), ('out', 'تحلیل خطا')]


def pipe_boxes(y=760, h=170, bw=330, gap=62):
    x0 = (W - (9 * bw + 8 * gap)) // 2
    boxes = []
    for i, (k, lb) in enumerate(PIPE_LABELS):
        x = x0 + i * (bw + gap)
        boxes.append((k, lb, (x, y, x + bw, y + h)))
    return boxes, x0


def flow_along(d, pts, color, t, r=16, trail=8):
    """Glowing particle moving along a polyline; t in [0,1)."""
    n = len(pts) - 1
    segs = [math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1])
            for i in range(n)]
    total = sum(segs)
    if total == 0:
        return
    s = (t % 1.0) * total
    acc = 0.0
    for i in range(n):
        if s <= acc + segs[i]:
            f = (s - acc) / segs[i] if segs[i] > 0 else 0
            x = pts[i][0] + f * (pts[i + 1][0] - pts[i][0])
            y = pts[i][1] + f * (pts[i + 1][1] - pts[i][1])
            # trail
            for kk in range(1, trail + 1):
                ff = f - kk * (segs[i] / total) * (r / 20.0)
                if ff >= 0:
                    tx = pts[i][0] + ff * (pts[i + 1][0] - pts[i][0])
                    ty = pts[i][1] + ff * (pts[i + 1][1] - pts[i][1])
                    dot(d, (tx, ty), color, r=max(3, int(r * (1 - kk / (trail + 1)))),
                        alpha=int(180 * (1 - kk / (trail + 1))))
            dot(d, (x, y), color, r=r)
            return
        acc += segs[i]


def draw_pipeline(d, t, highlight=None, speed=1.0, show_gnss=True):
    """The full data-flow pipeline with animated particles."""
    boxes, x0 = pipe_boxes(y=640, h=180)
    # connecting arrows between main-chain boxes
    for i in range(len(boxes) - 1):
        k0, lb0, b0 = boxes[i]
        k1, lb1, b1 = boxes[i + 1]
        xa = b0[2]
        xb = b1[0]
        ymid = (b0[1] + b0[3]) // 2
        arrow_flow(d, (xa + 6, ymid), (xb - 6, ymid), C[k1], t * speed, width=8)
    # draw boxes
    for i, (k, lb, b) in enumerate(boxes):
        active = (highlight == i)
        stage_box(d, b, k, lb, size=42, active=active)
    # GNSS branch
    if show_gnss:
        tb = boxes[1][2]      # truth box
        fb = boxes[6][2]      # fusion box
        gx = (tb[2] + fb[0]) // 2
        gb = (gx - 170, 1000, gx + 170, 1160)
        arrow(d, ((tb[0] + tb[2]) // 2, tb[3]), (gb[0] + 70, gb[1]),
              C['gnss'], width=8, head=26)
        arrow_flow(d, (gb[2] - 70, gb[3]), ((fb[0] + fb[2]) // 2, fb[1]),
                   C['gnss'], t * speed, width=8, head=26)
        stage_box(d, gb, 'gnss', 'GNSS', size=42,
                  active=(highlight == 'gnss'))
        # particles
        pts_main = [(b[0] + 30, (b[1] + b[3]) // 2) for _, _, b in boxes]
        flow_along(d, pts_main, C['out'], t, r=15)
        flow_along(d, [((tb[0] + tb[2]) // 2, tb[3]), (gb[0] + 70, gb[1] + 60),
                       ((gb[0] + gb[2]) // 2, (gb[1] + gb[3]) // 2),
                       ((fb[0] + fb[2]) // 2, fb[1])],
                   C['gnss'], t, r=13)


# ------------------------------ chart data ------------------------------
def _data():
    D = {}
    for name in ('dropout', 'gyrobias', 'accelbias', 'align', 'sigma'):
        p = os.path.join(BASE, "data", f"{name}.npz")
        if os.path.exists(p):
            with np.load(p) as npz:
                D[name] = {k: npz[k].copy() for k in npz.files}
    return D


DATA = _data()


# ------------------------------ base scene ------------------------------
class Scene:
    title = ''
    subtitle = ''

    def __init__(self, dur):
        self.dur = max(dur, 0.5)

    def draw(self, d, t):
        pass

    def u(self, t):
        return clamp(t / self.dur)


# ------------------------------ Scene 0: intro ------------------------------
class SceneIntro(Scene):
    title = 'شبیه‌ساز ناوبری NavSim'
    subtitle = 'آموزش کامل و گرافیکی جریان داده — از سنسور تا جواب ناوبری'

    def draw(self, d, t):
        u = self.u(t)
        bg(d)
        # ---- title phase (0 .. 0.38) ----
        if u < 0.42:
            a = ease_out(clamp(u / 0.16))
            text_xy(d, (W // 2, 660), 'NavSim', size=220, color=C['out'],
                    bold=True, font='dejavu_bold', anchor='mm', alpha=int(255 * a))
            text_xy(d, (W // 2, 900), 'شبیه‌ساز آموزشی ناوبری GNSS / INS',
                    size=110, color=INK, bold=True, anchor='mm',
                    alpha=int(255 * ease_out(clamp((u - 0.06) / 0.16))))
            text_xy(d, (W // 2, 1050), 'از سنسور تا جواب ناوبری — قدم‌به‌قدم، شفاف و گرافیکی',
                    size=62, color=MUTED, anchor='mm',
                    alpha=int(255 * ease_out(clamp((u - 0.12) / 0.16))))
            text_xy(d, (W // 2, 1220), 'زبان: فارسی  •  کیفیت: 4K',
                    size=48, color=MUTED, anchor='mm',
                    alpha=int(255 * ease_out(clamp((u - 0.18) / 0.16))))
        # ---- pipeline phase (0.38 .. 1) ----
        else:
            v = clamp((u - 0.38) / 0.1)
            header(d, 'نمای کلی: جریان داده از سنسور تا جواب',
                   'هر داده از کجا می‌آید، به کجا می‌رود و چرا؟')
            # fade the whole diagram in
            if v < 1:
                pass
            draw_pipeline(d, t - 0.38 * self.dur, speed=0.35)
            bullets(d, [
                ('۱. داده از کجا می‌آید؟', C['truth']),
                ('۲. چرا به این‌جا می‌رود؟', C['ins']),
                ('۳. خروجی چرا همین است؟', C['out']),
                ('۴. پارامترها باید چه باشند؟', C['gnss']),
            ], x_right=W - 120, y_top=1300, line_h=90, size=56,
              t=clamp((u - 0.46) / 0.5), gap=0.12)
            progress(d, clamp((u - 0.42) / 0.5))


# ------------------------------ Scene 1: trajectory & truth ------------------------------
class SceneTraj(Scene):
    title = 'مرحله‌ی ۱ و ۲ — مسیر و حالت واقعی'
    subtitle = 'Trajectory → Truth: تولید موقعیت، سرعت و وضعیت بدون خطا'

    def draw(self, d, t):
        u = self.u(t)
        bg(d)
        header(d, self.title, self.subtitle)
        # left panel: 9 trajectories
        panel(d, (120, 240, 1280, 2030))
        text_xy(d, (700, 300), '۹ مسیر آماده', size=56, color=C['traj'],
                bold=True, anchor='mm')
        items = [
            'پرواز مستقیم (Straight)',
            'دایره (Circle)',
            'هشت لاتین (FigureEight)',
            'شتاب‌گیری (Acceleration)',
            'صعود (Climb)',
            'فرود (Descent)',
            'گردش (Turn)',
            'ترکیب سه‌بعدی (Combined3D)',
            'مسیر دلخواه کاربر (UserDefined)',
        ]
        for i, it in enumerate(items):
            a = ease_out(clamp((u - 0.03 - i * 0.04) / 0.05))
            if a > 0:
                col = C['traj'] if i < 8 else C['out']
                dot(d, (150, 380 + i * 62), col, r=9, alpha=int(255 * a))
                text_xy(d, (180, 380 + i * 62), it, size=40, color=INK,
                        anchor='lm', alpha=int(255 * a))
        # right: NED + circle animation
        cx, cy = 2470, 700
        panel(d, (1400, 240, 3720, 1400))
        text_xy(d, (2560, 300), 'دستگاه مختصات محلی NED', size=52, color=C['truth'],
                bold=True, anchor='mm')
        ned_axes(d, (cx, cy), scale=1.3)
        # circle drawing (top view N-E): animate the dot around
        R = 560
        theta = 2 * math.pi * (u * 1.2)
        px = cx + R * math.cos(theta)
        py = cy - R * math.sin(theta) * 0.55   # ellipse foreshorten
        # draw full ellipse path faint
        d.ellipse([cx - R, cy - R * 0.55, cx + R, cy + R * 0.55],
                  outline=(90, 100, 130), width=4)
        vx, vy = -math.sin(theta), math.cos(theta) * 0.55
        vl = math.hypot(vx, vy)
        arrow(d, (px, py), (px + vx / vl * 150, py + vy / vl * 150), C['traj'], width=10)
        vehicle(d, (px, py), size=46, color=C['traj'],
                heading=math.atan2(vy, vx))
        text_xy(d, (2560, 1340), 'مسیر دایره: سرعت ۱۵ m/s، شعاع ۲۰۰ m',
                size=44, color=MUTED, anchor='mm')
        # bottom panel: truth outputs
        panel(d, (1400, 1480, 3720, 2030))
        text_xy(d, (2560, 1540), 'خروجی حالت واقعی → ورودی شبیه‌ساز IMU',
                size=50, color=C['truth'], bold=True, anchor='mm')
        eq(d, r"$\omega_{ib}^{b} = T(eul)\,\dot{eul}$", (2050, 1660), target_h=84,
           color='#ffd65a')
        eq(d, r"$f^{b} = C_{n}^{b}\left(a^{n} - g^{n}\right)$", (2050, 1800),
           target_h=84, color='#ffd65a')
        text_xy(d, (2960, 1660), 'نرخ زاویه‌ای واقعی بدنه', size=42, color=MUTED,
                anchor='lm', alpha=int(255 * ease_out(clamp((u - 0.25) / 0.1))))
        text_xy(d, (2960, 1800), 'نیروی ویژه‌ی واقعی بدنه', size=42, color=MUTED,
                anchor='lm', alpha=int(255 * ease_out(clamp((u - 0.35) / 0.1))))
        progress(d, u)


# ------------------------------ Scene 2: IMU ------------------------------
class SceneIMU(Scene):
    title = 'مرحله‌ی ۳ — مدل سنسور IMU'
    subtitle = 'ژیرو + شتاب‌سنج: بایاس، نویز، مقیاس، ناهم‌راستایی و ...'

    def draw(self, d, t):
        u = self.u(t)
        bg(d)
        header(d, self.title, self.subtitle)
        # top equation
        panel(d, (140, 220, 3700, 700))
        eq(d, r"$\tilde{y} = (I + [m]_\times)\,\mathrm{diag}(1+SF)\, y + b + n$",
           (1920, 380), target_h=110, color='#ff8a9a')
        text_xy(d, (1920, 560), 'خروجی سنسور = (ناهم‌راستایی × مقیاس) × مقدار واقعی + بایاس + نویز',
                size=48, color=INK, anchor='mm',
                alpha=int(255 * ease_out(clamp((u - 0.1) / 0.1))))
        # flow: true -> IMU -> measured
        ax = 150
        text_xy(d, (ax + 240, 900), 'ورودی واقعی', size=50, color=C['truth'],
                bold=True, anchor='mm')
        text_xy(d, (ax + 240, 980), 'ω_true , f_true', size=42, color=MUTED,
                font='mono', anchor='mm')
        glow_box(d, (ax + 520, 820, ax + 1050, 1040), C['imu'], radius=28, width=7)
        text_xy(d, (ax + 785, 900), 'مدل خطای IMU', size=52, color=C['imu'],
                bold=True, anchor='mm')
        text_xy(d, (ax + 785, 980), 'بایاس + نویز + SF + Mis', size=40, color=MUTED,
                anchor='mm')
        text_xy(d, (ax + 1320, 900), 'خروجی خام', size=50, color=C['imu'],
                bold=True, anchor='mm')
        text_xy(d, (ax + 1320, 980), 'ω_meas , f_meas', size=42, color=MUTED,
                font='mono', anchor='mm')
        arrow_flow(d, (ax + 360, 930), (ax + 510, 930), C['truth'], t, width=9)
        arrow_flow(d, (ax + 1060, 930), (ax + 1210, 930), C['imu'], t, width=9)
        # error source cards (right side grid 3x3)
        cards = [
            ('بایاس ثابت', 'gyro ≈ 0.02 °/s\naccel ≈ 2 mg', C['red']),
            ('نویز سفید', 'σ = ρ / √dt\nARW / VRW', C['amber']),
            ('خطای مقیاس', 'SF ≈ 50 ppm', C['ins']),
            ('ناهم‌راستایی', 'Mis ≈ 0.02°', C['pred']),
            ('حساسیت به g', 'g-sensitivity', C['calib']),
            ('اشباع + کوانتیزاسیون', 'سقف برد + LSB', C['gnss']),
        ]
        cw, ch, gx, gy = 800, 300, 190, 1160
        for i, (ttl, sub, col) in enumerate(cards):
            r, c = divmod(i, 3)
            bx = gx + c * (cw + 30)
            by = gy + r * (ch + 30)
            a = ease_out(clamp((u - 0.12 - i * 0.06) / 0.08))
            if a <= 0:
                continue
            panel(d, (bx, by, bx + cw, by + ch), fill=(26, 31, 58),
                  edge=tuple(col) + (120,))
            text_xy(d, (bx + cw // 2, by + 70), ttl, size=48, color=col, bold=True,
                    anchor='mm', alpha=int(255 * a))
            for j, ln in enumerate(sub.split('\n')):
                text_xy(d, (bx + cw // 2, by + 150 + j * 54), ln, size=40,
                        color=MUTED, anchor='mm', font='mono',
                        alpha=int(230 * a))
        progress(d, u)


# ------------------------------ Scene 3: calibration + INS ------------------------------
class SceneINS(Scene):
    title = 'مرحله‌ی ۴ و ۵ — کالیبراسیون و مکانیزاسیون INS'
    subtitle = 'تصحیح بایاس، سپس انتگرال‌گیری برای موقعیت، سرعت و وضعیت'

    def draw(self, d, t):
        u = self.u(t)
        bg(d)
        header(d, self.title, self.subtitle)
        # calibration panel
        panel(d, (140, 220, 1870, 760))
        text_xy(d, (1000, 290), 'کالیبراسیون', size=52, color=C['calib'],
                bold=True, anchor='mm')
        eq(d, r"$w_c = w_m - \hat{b}_g$", (1000, 420), target_h=80, color='#40c8be')
        eq(d, r"$f_c = f_m - \hat{b}_a$", (1000, 580), target_h=80, color='#40c8be')
        text_xy(d, (1000, 700), 'بایاسِ تخمینی فیلتر از اندازه‌گیری کم می‌شود',
                size=40, color=MUTED, anchor='mm',
                alpha=int(255 * ease_out(clamp((u - 0.2) / 0.12))))
        # INS mechanization chain (4 steps)
        steps = [
            ('وضعیت', r"$q \leftarrow q \otimes \delta q$", C['ins']),
            ('تبدیل فریم', r"$f^{n} = C_{b}^{n}\, f^{b}$", C['pred']),
            ('سرعت', r"$v \leftarrow v + (f^{n}+g^{n})\,dt$", C['calib']),
            ('موقعیت', r"$p \leftarrow p + v\,dt$", C['out']),
        ]
        x = 2000
        for i, (name, f, col) in enumerate(steps):
            a = ease_out(clamp((u - 0.1 - i * 0.09) / 0.1))
            if a <= 0:
                continue
            by = 240 + i * 210
            panel(d, (x, by, x + 1700, by + 170), fill=(26, 31, 58),
                  edge=tuple(col) + (140,))
            text_xy(d, (x + 40, by + 85), name, size=50, color=col, bold=True,
                    anchor='lm', alpha=int(255 * a))
            eq(d, f, (x + 320, by + 85), target_h=72, color='#e8f0ff', anchor='lm',
               alpha=int(255 * a))
            if i < 3:
                arrow_flow(d, (x + 850, by + 170), (x + 850, by + 240), col,
                           t + i * 0.2, width=7)
        # drift equation + mini chart
        panel(d, (140, 1040, 1870, 2030))
        text_xy(d, (1000, 1100), 'چرا INS به‌تنهایی دریفت می‌کند؟', size=50,
                color=C['red'], bold=True, anchor='mm')
        eq(d, r"$\delta p(t) = \frac{1}{2}\, b_{a}\, t^{2}$", (1000, 1220),
           target_h=90, color='#ff8a9a')
        text_xy(d, (1000, 1330), 'خطای بایاس شتاب‌سنج → رشد درجه‌دوم موقعیت',
                size=40, color=MUTED, anchor='mm',
                alpha=int(255 * ease_out(clamp((u - 0.35) / 0.1))))
        box = (320, 1400, 1690, 1960)
        plot_axes(d, box, 0, 706, n_ticks=4, label_fmt='%.0f', ylabel='خطا [m]',
                  title='خطای موقعیت: فقط بایاس شتاب‌سنج ۱۰ mg', title_color=C['red'])
        if 'accelbias' in DATA:
            dd = DATA['accelbias']
            plot_line(d, box, dd['t'], dd['theory'], C['amber'], prog=u * 1.0,
                      width=8)
            plot_line(d, box, dd['t'], dd['errIns'], C['red'], prog=u * 1.0, width=6)
        # WGS84 note
        text_xy(d, (2400, 1300), 'دو مدل زمین:', size=50, color=C['out'], bold=True,
                anchor='lm')
        text_xy(d, (2400, 1380), 'flat  = آموزشی و ساده', size=44, color=INK,
                anchor='lm')
        text_xy(d, (2400, 1450), 'WGS84 = چرخش زمین + کوریولیس + نرخ انتقال',
                size=44, color=INK, anchor='lm')
        text_xy(d, (2400, 1560), 'coning / sculling و گام زمانی متغیر هم پشتیبانی می‌شوند',
                size=42, color=MUTED, anchor='lm',
                alpha=int(255 * ease_out(clamp((u - 0.5) / 0.1))))
        progress(d, u)


# ------------------------------ Scene 4: GNSS ------------------------------
class SceneGNSS(Scene):
    title = 'مرحله‌ی ۶ — مدل گیرنده‌ی GNSS'
    subtitle = 'موقعیت مطلق با نرخ پایین: نویز H/V، قطعی، پرت و تأخیر'

    def draw(self, d, t):
        u = self.u(t)
        bg(d)
        header(d, self.title, self.subtitle)
        # equation
        panel(d, (140, 220, 1900, 640))
        eq(d, r"$z = p_{\mathrm{true}} + b + n$", (1090, 380), target_h=100,
           color='#ff8c3c')
        text_xy(d, (1090, 540), 'σ_H = 1.5 m (افقی)  ،  σ_V = 3.0 m (عمودی)',
                size=46, color=INK, anchor='mm',
                alpha=int(255 * ease_out(clamp((u - 0.1) / 0.1))))
        text_xy(d, (1090, 620), 'نرخ پیش‌فرض: ۱ Hz (هر ۱ ثانیه یک سنجش)',
                size=42, color=MUTED, anchor='mm',
                alpha=int(255 * ease_out(clamp((u - 0.2) / 0.1))))
        # rate comparison timeline (IMU vs GNSS)
        panel(d, (2120, 220, 3700, 640))
        text_xy(d, (2910, 290), 'IMU: 100 Hz  در برابر  GNSS: 1 Hz', size=50,
                color=C['ins'], bold=True, anchor='mm')
        yim = 440
        for i in range(20):
            xx = 2260 + i * 68
            d.line([(xx, yim), (xx, yim - 26)], fill=C['ins'], width=5)
        text_xy(d, (2260, 470), 'IMU 100Hz', size=36, color=C['ins'], anchor='lm')
        yg = 560
        for i in range(3):
            xx = 2260 + i * 680
            d.line([(xx, yg), (xx, yg - 40)], fill=C['gnss'], width=10)
        text_xy(d, (2260, 590), 'GNSS 1Hz', size=36, color=C['gnss'], anchor='lm')
        # dropout illustration
        panel(d, (140, 940, 1900, 2030))
        text_xy(d, (1090, 1000), 'قطعی (Dropout): تونل یا سایه‌ی ماهواره', size=50,
                color=C['red'], bold=True, anchor='mm')
        # timeline with shaded dropout window
        y = 1120
        d.line([(300, y), (1740, y)], fill=(90, 100, 130), width=5)
        for s in (0, 40, 70, 120):
            xx = 300 + s / 120 * 1440
            d.line([(xx, y - 14), (xx, y + 14)], fill=(90, 100, 130), width=4)
            text_xy(d, (xx, y + 40), str(s) + 's', size=34, color=MUTED,
                    font='mono', anchor='mm')
        # shaded region 40..70
        xa = 300 + 40 / 120 * 1440
        xb = 300 + 70 / 120 * 1440
        rrect(d, (xa, y - 60, xb, y + 60), radius=16, fill=(255, 108, 122, 40),
              outline=C['red'], width=3)
        text_xy(d, (1090, 1290), 'مثال: قطعی از ثانیه‌ی ۴۰ تا ۷۰', size=44, color=INK,
                anchor='mm')
        text_xy(d, (1090, 1420), 'درون قطعی: سیگما رشد می‌کند و INS ادامه می‌دهد',
                size=42, color=MUTED, anchor='mm')
        # outlier + delay
        panel(d, (2120, 940, 3700, 2030))
        text_xy(d, (2910, 1000), 'پرت (Outlier) و تأخیر (Delay)', size=50,
                color=C['amber'], bold=True, anchor='mm')
        # outlier: true point + far outlier point
        cx, cy = 2910, 1220
        dot(d, (cx - 260, cy), C['green'], r=16)
        text_xy(d, (cx - 220, cy - 60), 'سنجش سالم', size=38, color=C['green'],
                anchor='lm')
        dot(d, (cx + 300, cy - 40), C['red'], r=16)
        text_xy(d, (cx + 340, cy - 60), 'پرت: ده‌ها متر خطا', size=38, color=C['red'],
                anchor='lm')
        d.line([(cx - 260, cy), (cx + 300, cy - 40)], fill=(90, 100, 130), width=3)
        # delay
        text_xy(d, (2910, 1450), 'تأخیر: tMeas ≠ tEmit', size=46, color=C['calib'],
                bold=True, anchor='mm', font='mono')
        text_xy(d, (2910, 1540), 'epoch فیزیکی سنجش، از epoch تحویل جداست',
                size=42, color=MUTED, anchor='mm')
        text_xy(d, (2910, 1630), '→ پایه‌ی پردازش اندازه‌گیری خارج از ترتیب (OOSM)',
                size=42, color=INK, anchor='mm',
                alpha=int(255 * ease_out(clamp((u - 0.5) / 0.1))))
        text_xy(d, (2910, 1750), 'خطای همبسته‌ی گاوس-مارکوف (چندمسیری) نیز مدل شده',
                size=42, color=MUTED, anchor='mm',
                alpha=int(255 * ease_out(clamp((u - 0.6) / 0.1))))
        progress(d, u)


# ------------------------------ Scene 5: EKF part 1 ------------------------------
class SceneEKFPredict(Scene):
    title = 'مرحله‌ی ۷ — فیلتر تلفیق (۱): مدل خطا و پیش‌بینی'
    subtitle = 'ESKF پانزده‌حالته: بردار خطا، دینامیک و انتشار کوواریانس'

    def draw(self, d, t):
        u = self.u(t)
        bg(d)
        header(d, self.title, self.subtitle)
        # state vector (stacked blocks)
        panel(d, (140, 220, 1350, 2030))
        text_xy(d, (815, 290), 'بردار حالت خطا (۱۵)', size=52, color=C['pred'],
                bold=True, anchor='mm')
        blocks = [
            ('δp', 'خطای موقعیت', 3, C['out']),
            ('δv', 'خطای سرعت', 3, C['ins']),
            ('δφ', 'خطای وضعیت', 3, C['pred']),
            ('δb_g', 'بایاس ژیرو', 3, C['gnss']),
            ('δb_a', 'بایاس شتاب‌سنج', 3, C['calib']),
        ]
        y = 360
        for i, (sym, name, n, col) in enumerate(blocks):
            a = ease_out(clamp((u - 0.05 - i * 0.05) / 0.06))
            if a <= 0:
                continue
            panel(d, (200, y, 1290, y + 270), fill=(26, 31, 58),
                  edge=tuple(col) + (140,))
            text_xy(d, (240, y + 135), sym, size=66, color=col, bold=True,
                    font='dejavu_bold', anchor='lm', alpha=int(255 * a))
            text_xy(d, (560, y + 100), name, size=44, color=INK, anchor='lm',
                    alpha=int(255 * a))
            text_xy(d, (560, y + 170), f'{n} مؤلفه', size=38, color=MUTED,
                    anchor='lm', alpha=int(220 * a))
            y += 320
        # error dynamics equations
        panel(d, (1560, 220, 3700, 900))
        text_xy(d, (2630, 290), 'دینامیک خطا (خطا = واقعی − تخمین)', size=52,
                color=C['pred'], bold=True, anchor='mm')
        eq(d, r"$\delta\dot{v} = [f^{n}]_{\times}\,\delta\phi - C_{b}^{n}\,\delta b_{a} - [2\omega_{ie}^{n}+\omega_{en}^{n}]_{\times}\delta v$",
           (2630, 450), target_h=110, color='#b28cff')
        eq(d, r"$\delta\dot{\phi} = -[\omega_{in}^{n}]_{\times}\,\delta\phi + C_{b}^{n}\,\delta b_{g}$",
           (2630, 640), target_h=100, color='#b28cff')
        eq(d, r"$\delta\dot{b} = -\delta b / \tau + n_b$", (2630, 800), target_h=80,
           color='#b28cff')
        # prediction / covariance
        panel(d, (1560, 1180, 3700, 2030))
        text_xy(d, (2630, 1250), 'پیش‌بینی: انتشار کوواریانس', size=52, color=C['ins'],
                bold=True, anchor='mm')
        eq(d, r"$P \leftarrow \Phi\, P\, \Phi^{T} + Q_d$", (2630, 1390), target_h=100,
           color='#6096ff')
        # noise densities
        text_xy(d, (2630, 1560), 'نویز فرایند (Q): چهار چگالی کلیدی', size=46,
                color=INK, bold=True, anchor='mm',
                alpha=int(255 * ease_out(clamp((u - 0.4) / 0.1))))
        dens = [
            ('qa', 'نویز شتاب‌سنج', '0.05 m/s²/√Hz'),
            ('qg', 'نویز ژیرو', '0.02 °/s/√Hz'),
            ('qbg', 'RW بایاس ژیرو', '0.002 °/s/√s'),
            ('qba', 'RW بایاس شتاب‌سنج', '0.005 m/s²/√s'),
        ]
        x0 = 1660
        for i, (sym, name, val) in enumerate(dens):
            a = ease_out(clamp((u - 0.45 - i * 0.07) / 0.07))
            if a <= 0:
                continue
            bx = x0 + i * 500
            panel(d, (bx, 1660, bx + 460, 1960), fill=(26, 31, 58),
                  edge=(110, 130, 180))
            text_xy(d, (bx + 230, 1720), sym, size=60, color=C['ins'], bold=True,
                    font='dejavu_bold', anchor='mm', alpha=int(255 * a))
            text_xy(d, (bx + 230, 1800), name, size=36, color=INK, anchor='mm',
                    alpha=int(255 * a))
            text_xy(d, (bx + 230, 1860), val, size=34, color=MUTED, font='mono',
                    anchor='mm', alpha=int(220 * a))
        progress(d, u)


# ------------------------------ Scene 6: EKF part 2 ------------------------------
class SceneEKFUpdate(Scene):
    title = 'مرحله‌ی ۷ — فیلتر تلفیق (۲): به‌روزرسانی، گیتینگ و فیدبک'
    subtitle = 'نوآوری → بهره‌ی کالمن → تصحیح → NIS → فیدبک حلقه‌بسته'

    def draw(self, d, t):
        u = self.u(t)
        bg(d)
        header(d, self.title, self.subtitle)
        # update chain
        panel(d, (140, 220, 3700, 820))
        eq(d, r"$\nu = z - \hat{p}\qquad S = H P H^{T} + R\qquad K = P H^{T} S^{-1}\qquad \delta x = K\nu$",
           (1920, 460), target_h=120, color='#56dc8c')
        # gating ellipse illustration
        panel(d, (140, 1100, 1900, 2030))
        text_xy(d, (1090, 1160), 'گیتینگ NIS: تشخیص پرت', size=52, color=C['gnss'],
                bold=True, anchor='mm')
        # draw gate ellipse + accepted/rejected points
        cx, cy = 1090, 1560
        d.ellipse([cx - 420, cy - 220, cx + 420, cy + 220],
                  outline=(110, 200, 160), width=6)
        text_xy(d, (cx, cy + 250), 'گیت (آستانه‌ی χ²)', size=40, color=C['green'],
                anchor='mm')
        # accepted points inside
        import random
        random.seed(3)
        for _ in range(9):
            ang = random.uniform(0, 2 * math.pi)
            rr = random.uniform(0, 0.75)
            dot(d, (cx + 420 * rr * math.cos(ang), cy + 220 * rr * math.sin(ang)),
                C['green'], r=10)
        for i in range(2):
            dot(d, (cx + (620 + i * 180) * math.cos(0.9), cy + 300 * math.sin(0.9)),
                C['red'], r=12)
        text_xy(d, (cx, 1920), 'سنجش بیرون گیت → رد یا تطبیق نویز (robust)',
                size=42, color=MUTED, anchor='mm')
        eq(d, r"$\mathrm{NIS} = \nu^{T} S^{-1} \nu \;\leq\; \chi_{3}^{2}(99.9\%) = 16.27$",
           (cx, 1300), target_h=80, color='#ff8c3c')
        # feedback loop
        panel(d, (2120, 1100, 3700, 2030))
        text_xy(d, (2910, 1160), 'فیدبک حلقه‌بسته', size=52, color=C['fusion'],
                bold=True, anchor='mm')
        steps = [
            'خطای تخمینی از حالت INS کم می‌شود',
            'بایاس‌های IMU اصلاح می‌شوند (calBg, calBa)',
            'بردار خطا دوباره صفر می‌شود',
            'کوواریانس با ژاکوبین ریست منتقل می‌شود',
        ]
        for i, s in enumerate(steps):
            a = ease_out(clamp((u - 0.2 - i * 0.09) / 0.1))
            if a <= 0:
                continue
            dot(d, (2180, 1340 + i * 120), C['fusion'], r=11, alpha=int(255 * a))
            text_xy(d, (2230, 1340 + i * 120), s, size=44, color=INK, anchor='lm',
                    alpha=int(255 * a))
        text_xy(d, (2910, 1900), '← بایاس ژیرو با مانور، به‌تدریج شناسایی می‌شود (observability)',
                size=40, color=C['amber'], anchor='mm',
                alpha=int(255 * ease_out(clamp((u - 0.55) / 0.12))))
        progress(d, u)


# ------------------------------ Scene 7: aiding + output ------------------------------
class SceneOutput(Scene):
    title = 'مرحله‌ی ۸ و ۹ — ایدینگ کمکی، خروجی و تحلیل خطا'
    subtitle = 'Baro و ZUPT، مقایسه‌ی INS در برابر Fused، و اعداد واقعی'

    def draw(self, d, t):
        u = self.u(t)
        bg(d)
        header(d, self.title, self.subtitle)
        # baro + zupt cards
        panel(d, (140, 220, 1300, 700))
        text_xy(d, (790, 300), 'ارتفاع‌سنج بارومتریک', size=50, color=C['baro'],
                bold=True, anchor='mm')
        text_xy(d, (790, 380), 'H = [0 0 −1 0 ... 0]', size=40, color=MUTED,
                font='mono', anchor='mm')
        text_xy(d, (790, 450), 'آپدیت اسکالر ارتفاع', size=40, color=INK, anchor='mm')
        text_xy(d, (790, 520), 'گیت χ²(1) = 10.83', size=38, color=MUTED, font='mono',
                anchor='mm')
        text_xy(d, (790, 590), 'برای تونل: کانال عمودی مقید می‌ماند', size=36,
                color=MUTED, anchor='mm')
        panel(d, (1520, 220, 2680, 700))
        text_xy(d, (2100, 300), 'ZUPT (سرعت صفر)', size=50, color=C['zupt'],
                bold=True, anchor='mm')
        text_xy(d, (2100, 380), 'تشخیص سکون: |‖f‖−g| < 0.05g و ‖ω‖ < 3°/s',
                size=36, color=MUTED, anchor='mm')
        text_xy(d, (2100, 450), 'پس از ۱ ثانیه سکون → شبه‌سنجش v=0', size=40,
                color=INK, anchor='mm')
        text_xy(d, (2100, 520), 'دریفت را در توقف (مثل پشت چراغ) صفر نگه می‌دارد',
                size=36, color=MUTED, anchor='mm')
        # main chart: dropout error
        panel(d, (140, 1000, 2200, 2030))
        text_xy(d, (1170, 1050), 'قطع ۳۰ ثانیه‌ای GNSS — خطای موقعیت',
                size=50, color=C['out'], bold=True, anchor='mm')
        box = (360, 1140, 2020, 1900)
        plot_axes(d, box, 0, 1400, n_ticks=4, label_fmt='%.0f', ylabel='خطا [m]',
                  title='')
        if 'dropout' in DATA:
            dd = DATA['dropout']
            # shaded dropout region 40..70
            xa = 360 + 40 / 120 * (2020 - 360)
            xb = 360 + 70 / 120 * (2020 - 360)
            rrect(d, (xa, 1140, xb, 1900), radius=10, fill=(255, 108, 122, 30),
                  outline=(255, 108, 122, 120), width=3)
            plot_line(d, box, dd['t'], dd['errInsOnly'], C['red'], prog=u, width=7)
            plot_line(d, box, dd['t'], dd['errFus'], C['green'], prog=u, width=9)
        text_xy(d, (560, 1210), 'INS (بدون GNSS)', size=40, color=C['red'],
                bold=True, anchor='lm')
        text_xy(d, (900, 1210), '≈ ۱۲۳۵ m در قطعی', size=38, color=C['red'],
                anchor='lm', font='mono')
        text_xy(d, (560, 1270), 'Fused (تلفیق)', size=40, color=C['green'],
                bold=True, anchor='lm')
        text_xy(d, (900, 1270), '≈ ۳۱ m → بازگشت ≈ ۱٫۹ m', size=38, color=C['green'],
                anchor='lm', font='mono')
        # gyro bias estimation chart
        panel(d, (2340, 1000, 3700, 2030))
        text_xy(d, (3020, 1050), 'تخمین بایاس ژیرو (Fusion)', size=50, color=C['gnss'],
                bold=True, anchor='mm')
        box2 = (2560, 1140, 3480, 1900)
        plot_axes(d, box2, -0.4, 0.6, n_ticks=5, label_fmt='%.1f', ylabel='°/s',
                  title='')
        if 'gyrobias' in DATA:
            gd = DATA['gyrobias']
            for i, col, lab in [(0, C['red'], 'bgx'), (1, C['green'], 'bgy'),
                                (2, C['ins'], 'bgz')]:
                plot_line(d, box2, gd['t'], gd['calBg'][i], col, prog=u, width=7)
            for val, col in [(0.5, C['red']), (-0.3, C['green']), (0.2, C['ins'])]:
                yy = 1900 - (val + 0.4) / 1.0 * 760
                d.line([(2560, yy), (3480, yy)], fill=tuple(col) + (120,), width=3)
        text_xy(d, (3020, 1960), 'خط‌چین = مقدار واقعی  →  تخمین همگرا می‌شود',
                size=38, color=MUTED, anchor='mm')
        progress(d, u)


# ------------------------------ Scene 8: parameters + recap ------------------------------
class SceneParams(Scene):
    title = 'پارامترهای کلیدی و جمع‌بندی'
    subtitle = 'هر پارامتر چیست، چرا این مقدار است و باید چه باشد'

    def draw(self, d, t):
        u = self.u(t)
        bg(d)
        header(d, self.title, self.subtitle)
        # parameter table
        rows = [
            ('dt = 0.01 s', 'گام شبیه‌سازی (100 Hz)', 'برای انتگرال‌گیری دقیق INS'),
            ('GNSS rate = 1 Hz', 'نرخ سنجش ماهواره', 'کمتر از نرخ polling باشد'),
            ('p0pos = 5 m , p0att = 5°', 'عدم‌قطعیت اولیه', 'اعتماد اولیه‌ی فیلتر'),
            ('qa, qg, qbg, qba', 'نویز فرایند Q', 'اعتماد به مدل (تیونینگ)'),
            ('NIS gate = 16.27', 'χ²(3) در 99.9%', 'آستانه‌ی رد پرت'),
            ('oosmLag = 12 s', 'پنجره‌ی OOSM', 'بازپخش اندازه‌گیری تأخیری'),
            ('qScale = rScale = 1', 'ضریب‌های مقیاس', 'مبنا برای تیونینگ'),
        ]
        y = 240
        for i, (val, what, why) in enumerate(rows):
            a = ease_out(clamp((u - 0.02 - i * 0.04) / 0.06))
            if a <= 0:
                continue
            panel(d, (140, y, 1900, y + 230), fill=(26, 31, 58),
                  edge=(110, 130, 180))
            text_xy(d, (180, y + 70), val, size=46, color=C['out'], bold=True,
                    font='mono', anchor='lm', alpha=int(255 * a))
            text_xy(d, (180, y + 140), what, size=42, color=INK, anchor='lm',
                    alpha=int(255 * a))
            text_xy(d, (1480, y + 140), why, size=40, color=MUTED, anchor='rm',
                    alpha=int(220 * a))
            y += 250
        # recap pipeline (right)
        text_xy(d, (3060, 300), 'خلاصه‌ی جریان داده', size=56, color=C['fusion'],
                bold=True, anchor='mm')
        draw_pipeline(d, t, speed=0.5)
        bullets(d, [
            ('مسیر → حقیقت → سنسورها', C['traj']),
            ('IMU → کالیبراسیون → INS', C['ins']),
            ('GNSS / Baro / ZUPT → تلفیق', C['gnss']),
            ('تلفیق → تصحیح INS → خروجی', C['fusion']),
            ('خروجی ← مقایسه با حقیقت', C['out']),
        ], x_right=W - 140, y_top=1300, line_h=88, size=50,
          t=clamp((u - 0.35) / 0.5), gap=0.1)
        progress(d, u)


# ------------------------------ registry ------------------------------
SCENES = [SceneIntro, SceneTraj, SceneIMU, SceneINS, SceneGNSS,
          SceneEKFPredict, SceneEKFUpdate, SceneOutput, SceneParams]
