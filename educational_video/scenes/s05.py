"""S05 — GNSS model: noise, dropout, outlier, delay, GM."""
import math
import numpy as np

import gfx
from palette import (W, H, TXT, TXT_DIM, TXT_FAINT, C_GNSS, C_INS, C_BAD,
                     C_WARN, C_OK, C_BARO)
from common import Scene, seg, ease, ease_out, fade_in, header, card

C_EST_C = (34, 211, 238)


def _gnss_points(rng, path_fn, t0, t1, rate=1.0, sigma_h=1.5, sigma_v=3.0,
                 outlier_prob=0.02, outlier_mag=50.0, drop_windows=()):
    pts = []
    n = int((t1 - t0) * rate)
    for i in range(n + 1):
        tt = t0 + i / rate
        in_drop = any(a <= tt <= b for (a, b) in drop_windows)
        x, y = path_fn(tt)
        if in_drop:
            pts.append((tt, x, y, 'drop', 0.0))
            continue
        sH, sV = sigma_h * 0.18, sigma_v * 0.18
        dx = rng.normal(0, sH)
        dy = rng.normal(0, sV)
        is_out = rng.random() < outlier_prob
        if is_out:
            ang = rng.uniform(0, 2 * math.pi)
            m = rng.uniform(0.4, 1.0) * outlier_mag * 0.18
            dx += m * math.cos(ang)
            dy += m * math.sin(ang)
        pts.append((tt, x + dx, y + dy, 'out' if is_out else 'ok', tt))
    return pts


def _arrowhead(c, tip, direction, size, color):
    d = gfx.ImageDraw.Draw(c)
    ang = math.atan2(direction[1], direction[0])
    a1 = ang + math.pi - 0.42
    a2 = ang + math.pi + 0.42
    d.polygon([(tip[0] + size * math.cos(a1), tip[1] + size * math.sin(a1)),
               (tip[0] + size * math.cos(a2), tip[1] + size * math.sin(a2)), tip],
              fill=color)


def satellite_mini(c, pos, r, color):
    d = gfx.ImageDraw.Draw(c)
    d.rectangle([pos[0] - r, pos[1] - r * 0.4, pos[0] + r, pos[1] + r * 0.4],
                fill=(30, 50, 90, 255), outline=color + (255,), width=2)


class S05(Scene):
    name = 'S05'

    def draw(self, c, t):
        D = self.dur
        header(c, 'مدل GNSS: دقیق، اما...', C_GNSS, t)
        gfx.chip(c, 1750, 165, 'نرخ: ۱ Hz', C_GNSS, size=24)

        # ---------- map panel ----------
        a = ease(seg(t, 1, 2.5))
        if a > 0:
            x0, y0, x1, y1 = 90, 150, 1020, 720
            gfx.panel(c, (x0, y0, x1, y1))
            gfx.text(c, (x1 - 24, y0 + 16), 'مسیر واقعی و نقاط GNSS', 26, 'bold',
                     tuple(int(v * a) for v in TXT), 'right')
            cx, cy, R = 555, 445, 230
            d = gfx.ImageDraw.Draw(c)
            d.ellipse([cx - R, cy - R, cx + R, cy + R],
                      outline=(148, 163, 184, int(180 * a)), width=2)
            dur = 120.0
            rng = np.random.default_rng(5)
            path = lambda tt: (cx + R * math.cos(0.075 * tt), cy - R * math.sin(0.075 * tt))
            pts = _gnss_points(rng, path, 0, dur)
            tshow = min(2 + (t - 2) * 1.4, dur)
            for (tt, px, py, kind, _) in pts:
                if tt > tshow:
                    break
                if kind == 'drop':
                    if t > 24:
                        d.ellipse([px - 3, py - 3, px + 3, py + 3],
                                  fill=(110, 128, 165, int(160 * a)))
                    continue
                if kind == 'out' and t > 36:
                    d.line([(cx, cy), (px, py)], fill=C_BAD + (90,), width=2)
                    gfx.dot(c, (px, py), 6, C_BAD)
                elif t > 4:
                    gfx.dot(c, (px, py), 5, C_GNSS)
            vtt = tshow
            vx, vy = path(vtt)
            gfx.dot(c, (vx, vy), 9, C_INS)
            if t > 24:
                aa = fade_in(t, 24, 0.8)
                d = gfx.ImageDraw.Draw(c)
                gfx.soft_rrect(c, (x0 + 20, y1 - 70, x1 - 20, y1 - 18), 12,
                               fill=(40, 48, 70, int(220 * aa)),
                               outline=(110, 128, 165, int(255 * aa)), width=2)
                gfx.text_c(c, (x0 + x1) / 2, y1 - 60,
                           'قطعی (dropout): مثلاً ۳۰ تا ۶۰ ثانیه — مثل یک تونل، یا تصادفی epoch به epoch',
                           22, 'semibold', tuple(int(v * aa) for v in TXT_DIM))
        # ---------- sigma card ----------
        a = ease(seg(t, 8, 10))
        if a > 0:
            x0, y0, x1, y1 = 1060, 150, 1830, 420
            card(c, (x0, y0, x1, y1), 'نویز موقعیت', C_GNSS)
            gfx.text(c, (x1 - 30, y0 + 70), 'σH = 1.5 m   (افقی)', 27, 'bold',
                     tuple(int(v * a) for v in TXT), 'right')
            gfx.text(c, (x1 - 30, y0 + 112), 'σV = 3.0 m   (عمودی)', 27, 'bold',
                     tuple(int(v * a) for v in C_WARN), 'right')
            if t > 14:
                aa = fade_in(t, 14, 0.8)
                sx, sy = x0 + 190, y0 + 150
                d = gfx.ImageDraw.Draw(c)
                d.arc([sx - 120, sy - 120, sx + 120, sy + 120], start=200, end=340,
                      fill=(90, 108, 150, int(255 * aa)), width=3)
                for ang in (215, 250, 285, 320):
                    px = sx + 105 * math.cos(math.radians(ang))
                    py = sy + 105 * math.sin(math.radians(ang))
                    satellite_mini(c, (px, py), int(12 * aa), C_GNSS)
                d.ellipse([sx - 8, sy - 8, sx + 8, sy + 8], fill=C_INS + (int(255 * aa),))
                gfx.text_c(c, sx, sy + 70, 'ماهواره‌ها تقریباً بالای سر', 20, 'regular',
                           tuple(int(v * aa) for v in TXT_DIM))
                gfx.text(c, (x1 - 30, y0 + 160), 'هندسهٔ عمودی ضعیف‌تر', 24, 'semibold',
                         tuple(int(v * a) for v in C_WARN), 'right')
                gfx.text(c, (x1 - 30, y0 + 196), '(DOP) → σV بزرگ‌تر از σH', 22, 'regular',
                         tuple(int(v * a) for v in TXT_DIM), 'right')
                gfx.text(c, (x1 - 30, y0 + 238), 'بایاس ثابت N/E/D هم قابل تعریف است', 21,
                         'regular', tuple(int(v * a) for v in TXT_DIM), 'right')
        # ---------- timeline (delay) ----------
        if t > 48:
            a = ease(seg(t, 48, 50))
            x0, y0, x1, y1 = 90, 760, 1020, 1010
            gfx.panel(c, (x0, y0, x1, y1))
            gfx.text(c, (x1 - 24, y0 + 14), 'تأخیر: دو زمان برای هر سنجش', 26, 'bold',
                     tuple(int(v * a) for v in TXT), 'right')
            ax0, ax1, ay = x0 + 60, x1 - 60, y0 + 130
            d = gfx.ImageDraw.Draw(c)
            d.line([(ax0, ay), (ax1, ay)], fill=(90, 108, 150, 255), width=3)
            _arrowhead(c, (ax1, ay), (1, 0), 14, (90, 108, 150, 255))
            gfx.text_c(c, ax1 + 20, ay, 't', 22, 'regular', TXT_FAINT, 'left')
            m = 0.30
            e = 0.52
            tx, ex = ax0 + (ax1 - ax0) * m, ax0 + (ax1 - ax0) * e
            for xx, lab, col, tt in [(tx, 'tMeas (فیزیکی)', C_GNSS, 50),
                                     (ex, 'tEmit (تحویل)', C_EST_C, 54)]:
                aa = fade_in(t, tt, 0.8)
                if aa <= 0:
                    continue
                d.line([(xx, ay - 26), (xx, ay + 26)], fill=col + (int(255 * aa),), width=3)
                gfx.text_c(c, xx, ay + 44, lab, 22, 'semibold',
                           tuple(int(v * aa) for v in col))
            if t > 57:
                aa = fade_in(t, 57, 0.8)
                gfx.arrow(d, (tx + 8, ay - 46), (ex - 8, ay - 46),
                          (251, 191, 36, int(255 * aa)), 3, 12)
                gfx.text_c(c, (tx + ex) / 2, ay - 72, 'delay', 20, 'semibold',
                           tuple(int(v * aa) for v in (251, 191, 36)))
                gfx.text_c(c, (ax0 + ax1) / 2, y1 - 24,
                           'سنجش در tMeas گرفته می‌شود، ولی tEmit تحویل می‌دهد',
                           21, 'regular', tuple(int(v * aa) for v in TXT_DIM))
        # ---------- GM card ----------
        if t > 64:
            a = ease(seg(t, 64, 66))
            x0, y0, x1, y1 = 1060, 460, 1830, 740
            card(c, (x0, y0, x1, y1), 'نویز همبسته (شبیه multipath)', C_BARO)
            rng = np.random.default_rng(21)
            n = 160
            ts = np.linspace(0, 1, n)
            x = 0
            gm = np.zeros(n)
            for i in range(n):
                x = math.exp(-1 / 40) * x + 0.25 * rng.normal()
                gm[i] = x
            d = gfx.ImageDraw.Draw(c)
            gx0, gy0, gx1, gy1 = x0 + 30, y0 + 70, x0 + 400, y0 + 210
            pts = [(gx0 + (gx1 - gx0) * t_, gy0 + (gy1 - gy0) / 2 - gm[i] * (gy1 - gy0) * 0.28)
                   for i, t_ in enumerate(ts)]
            d.line(pts, fill=C_BARO + (255,), width=3)
            gfx.text(c, (x1 - 30, y0 + 80), 'Gauss–Markov: σ=۲m، τ=۳۰s', 24, 'semibold',
                     tuple(int(v * a) for v in TXT), 'right')
            gfx.text(c, (x1 - 30, y0 + 122), 'خطای همبسته در طول زمان', 22, 'regular',
                     tuple(int(v * a) for v in TXT_DIM), 'right')
            if t > 72:
                aa = fade_in(t, 72, 0.8)
                d = gfx.ImageDraw.Draw(c)
                gfx.soft_rrect(c, (x0 + 30, y0 + 170, x1 - 30, y0 + 250), 12,
                               fill=(60, 30, 30, int(200 * aa)),
                               outline=C_BAD + (int(255 * aa),), width=2)
                gfx.text(c, (x1 - 44, y0 + 182),
                         'نکتهٔ درس: این خطا عمداً در R نیست؛ بدون robust mode، فیلتر بیش از حد مطمئن می‌شود',
                         21, 'semibold', tuple(int(v * aa) for v in C_BAD), 'right')
        # ---------- summary ----------
        if t > 82:
            a = fade_in(t, 82, 1)
            gfx.chip(c, 960, 905, 'هر سناریوی واقعی: نویز + قطعی + پرت + تأخیر + همبستگی',
                     C_GNSS, size=26)
