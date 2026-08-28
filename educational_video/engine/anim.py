"""Scene framework + MP4 renderer (av/libx264)."""
import math
import os
import time

import av
import numpy as np

import gfx
from palette import W, H, FPS


def clamp(v, a=0.0, b=1.0):
    return a if v < a else b if v > b else v


def seg(t, t0, t1):
    """Normalized progress of t in [t0, t1], clamped."""
    if t1 <= t0:
        return 1.0 if t >= t1 else 0.0
    return clamp((t - t0) / (t1 - t0))


def ease(p):
    p = clamp(p)
    return p * p * (3 - 2 * p)


def ease_out(p):
    p = clamp(p)
    return 1 - (1 - p) ** 3


def ease_in(p):
    p = clamp(p)
    return p ** 3


def fade_in(t, t0, dur=0.5):
    return ease(seg(t, t0, t0 + dur))


def fade_out(t, t1, dur=0.5):
    return 1.0 - ease(seg(t, t1 - dur, t1))


def pulse(t, period=1.6, phase=0.0):
    return 0.5 + 0.5 * math.sin(2 * math.pi * (t + phase) / period)


class Scene:
    name = 'scene'
    dur = 60.0

    def draw(self, c, t):
        raise NotImplementedError


def render_scene(scene, path, fps=FPS, log=True):
    """Render scene to an H.264 mp4 (video only)."""
    n = int(round(scene.dur * fps))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    cont = av.open(path, mode='w')
    stream = cont.add_stream('libx264', rate=fps)
    stream.width = W
    stream.height = H
    stream.pix_fmt = 'yuv420p'
    stream.options = {'crf': '19', 'preset': 'fast'}
    t0 = time.time()
    for i in range(n):
        c = gfx.new_canvas()
        scene.draw(c, i / fps)
        frame = av.VideoFrame.from_ndarray(np.asarray(c.convert('RGB')),
                                           format='rgb24')
        for pkt in stream.encode(frame):
            cont.mux(pkt)
        if log and (i % (fps * 10) == 0) and i > 0:
            el = time.time() - t0
            est = el / max(i, 1) * (n - i)
            print(f'  [{scene.name}] {i}/{n} ({i / n * 100:.0f}%)  eta {est / 60:.1f} min',
                  flush=True)
    for pkt in stream.encode():
        cont.mux(pkt)
    cont.close()
    el = time.time() - t0
    print(f'  [{scene.name}] done in {el / 60:.1f} min -> {path}', flush=True)
    return path


def audio_duration(path):
    with av.open(path) as cont:
        d = cont.duration
        return float(d) / av.time_base if d else 0.0
