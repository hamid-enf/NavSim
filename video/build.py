#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Assemble audio + render 4K frames (single process) and pipe them to ffmpeg.

The renderer runs in this Python process (core A) while libx264 runs as a
subprocess (core B), so both cores stay busy without memory-bandwidth
contention from multiprocessing.
"""
import os
import sys
import re
import subprocess
import time
import wave

import numpy as np

sys.path.insert(0, "/home/user/navsim_video")
import imageio_ffmpeg
from lib import get_bg, W, H, FPS
import lib as L
from scenes import SCENES

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
BASE = os.path.dirname(os.path.abspath(__file__))
AUDIO_DIR = os.path.join(BASE, "audio")
OUT = os.path.join(BASE, "NavSim_educational_4K.mp4")

LEAD = 0.35
TAIL = 0.85


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, **kw)


def ff_duration(path):
    p = run([FFMPEG, "-i", path], timeout=120)
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", p.stderr.decode('utf-8', 'ignore'))
    h, mi, s = int(m.group(1)), int(m.group(2)), float(m.group(3))
    return h * 3600 + mi * 60 + s


def find_clips():
    clips = []
    for i in range(len(SCENES)):
        for ext in ('.mp3', '.m4a', '.wav', '.ogg', '.aac', '.flac'):
            p = os.path.join(AUDIO_DIR, f"clip_{i:02d}{ext}")
            if os.path.exists(p):
                clips.append(p)
                break
        else:
            raise RuntimeError(f"missing clip for scene {i}")
    return clips


def decode_pcm(path, sr=44100):
    p = run([FFMPEG, "-y", "-i", path, "-f", "s16le", "-ac", "1", "-ar", str(sr), "-"])
    return np.frombuffer(p.stdout, dtype=np.int16).copy()


def assemble_audio(clips, sr=44100):
    parts = []
    for cp in clips:
        lead = np.zeros(int(LEAD * sr), dtype=np.int16)
        tail = np.zeros(int(TAIL * sr), dtype=np.int16)
        pcm = decode_pcm(cp, sr)
        parts.extend([lead, pcm, tail])
    track = np.concatenate(parts)
    wav = os.path.join(BASE, "audio_track.wav")
    with wave.open(wav, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(track.tobytes())
    return wav


def build_jobs(scene_durs):
    jobs = []
    for si, dur in enumerate(scene_durs):
        for f in range(int(round(dur * FPS))):
            jobs.append((si, f / FPS))
    return jobs


def main():
    clips = find_clips()
    durs = [ff_duration(c) for c in clips]
    scene_durs = [d + LEAD + TAIL for d in durs]
    objs = [S(d) for S, d in zip(SCENES, scene_durs)]
    print("scene durations:", [round(x, 2) for x in scene_durs])

    wav = assemble_audio(clips)
    jobs = build_jobs(scene_durs)
    out_path = OUT
    cap = int(os.environ.get("FRAME_CAP", "0"))
    if cap:
        jobs = jobs[:cap]
        out_path = os.path.join(BASE, "test_preview.mp4")
    print("total frames:", len(jobs), "=", round(len(jobs) / FPS, 1), "s")

    get_bg()

    # ---- warm caches by rendering a few sample frames per scene ----
    for si in range(len(SCENES)):
        for f in (0.15, 0.5, 0.9):
            t = scene_durs[si] * f
            img = get_bg().copy()
            d = L.ImageDraw.Draw(img)
            objs[si].draw(d, t)

    cmd = [FFMPEG, "-y",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-",
           "-i", wav,
           "-c:v", "libx264", "-preset", "ultrafast", "-crf", "19",
           "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k",
           "-movflags", "+faststart",
           "-shortest", out_path]
    print("starting ffmpeg ...")
    enc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    t0 = time.time()
    n_done = 0
    try:
        for si, t in jobs:
            img = get_bg().copy()
            d = L.ImageDraw.Draw(img)
            objs[si].draw(d, t)
            arr = np.asarray(img.convert('RGB'), dtype=np.uint8)
            dur = scene_durs[si]
            if t < 0.25:
                arr = (arr * (t / 0.25)).astype(np.uint8)
            elif t > dur - 0.35:
                f = max(0.0, (dur - t) / 0.35)
                arr = (arr * f).astype(np.uint8)
            enc.stdin.write(arr.tobytes())
            n_done += 1
            if n_done % 240 == 0:
                el = time.time() - t0
                print(f"  {n_done}/{len(jobs)} frames ({100*n_done/len(jobs):.1f}%), "
                      f"{el:.0f}s elapsed, {n_done/el:.1f} fps, "
                      f"ETA {el*(len(jobs)-n_done)/n_done/60:.1f} min", flush=True)
    finally:
        enc.stdin.close()
        enc.wait()
    print("DONE rc=", enc.returncode, "->", out_path)


if __name__ == "__main__":
    main()
