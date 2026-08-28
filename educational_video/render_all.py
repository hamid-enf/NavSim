"""Render all 16 scenes, mux with narration audio, concatenate into the final video.

Usage:
    python render_all.py              # all scenes
    python render_all.py S01 S03      # only the given scenes

Requirements:  numpy, Pillow, fonttools, uharfbuzz, av, imageio-ffmpeg
(scenes read audio/Sxx.mp3 narration clips; durations come from the audio).
"""
import json
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, 'scenes'))
sys.path.insert(0, os.path.join(BASE, 'engine'))

import av  # noqa: E402
from anim import render_scene, audio_duration  # noqa: E402
import imageio_ffmpeg  # noqa: E402

FF = imageio_ffmpeg.get_ffmpeg_exe()
SCENES = [f'S{i:02d}' for i in range(16)]


def main(only=None):
    import importlib
    for sid in SCENES:
        if only and sid not in only:
            continue
        mod = importlib.import_module(sid.lower())
        cls = getattr(mod, sid)
        apath = os.path.join(BASE, 'audio', f'{sid}.mp3')
        if not os.path.exists(apath):
            print(f'skip {sid}: no audio')
            continue
        cls.dur = audio_duration(apath) + 1.2
        print(f'== {sid}: {cls.dur:.1f}s', flush=True)
        render_scene(cls(), os.path.join(BASE, 'media', f'{sid}.mp4'))
        adur = audio_duration(apath)
        subprocess.run([FF, '-y',
                        '-i', os.path.join(BASE, 'media', f'{sid}.mp4'),
                        '-i', apath,
                        '-map', '0:v', '-map', '1:a',
                        '-c:v', 'libx264', '-crf', '19', '-preset', 'fast',
                        '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k',
                        '-t', f'{adur:.3f}', '-shortest',
                        os.path.join(BASE, 'media', f'{sid}_final.mp4')],
                       check=True, capture_output=True)
        print(f'{sid} muxed', flush=True)
    # concatenate only when all scenes are present
    missing = [s for s in SCENES
               if not os.path.exists(os.path.join(BASE, 'media', f'{s}_final.mp4'))]
    if missing:
        print('not all scenes rendered; skip concat. missing:', missing)
        return
    listfile = os.path.join(BASE, 'media', 'concat.txt')
    with open(listfile, 'w') as lf:
        for sid in SCENES:
            lf.write(f"file '{sid}_final.mp4'\n")
    final = os.path.join(BASE, 'NavSim_complete.mp4')
    subprocess.run([FF, '-y', '-f', 'concat', '-safe', '0', '-i', listfile,
                    '-c', 'copy', final], check=True, capture_output=True)
    print('FINAL:', final, flush=True)


if __name__ == '__main__':
    main(only=sys.argv[1:] if len(sys.argv) > 1 else None)
