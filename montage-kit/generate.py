#!/usr/bin/env python3
"""
إعادة توليد ملفات المجلد من الكود:
  python3 generate.py            # الكل
  python3 generate.py sfx        # المؤثرات الصوتية فقط
  python3 generate.py luts       # فلاتر الألوان فقط
  python3 generate.py overlays   # الطبقات الضوئية فقط
  python3 generate.py sfx whoosh-short impact-boom   # عناصر محددة
"""
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def gen_sfx(names):
    from scipy.io import wavfile
    from kit.sfx import render, SR
    from kit.registry import SFX
    os.makedirs(os.path.join(HERE, "sfx"), exist_ok=True)
    for k in names or SFX:
        x = render(k)
        wavfile.write(os.path.join(HERE, "sfx", f"{k}.wav"), SR, (x * 32767).astype(np.int16))
        print("✓", k)


def gen_luts(names):
    from kit.luts import write_cube
    from kit.registry import LUTS
    os.makedirs(os.path.join(HERE, "luts"), exist_ok=True)
    for k in names or LUTS:
        write_cube(os.path.join(HERE, "luts", f"{k}.cube"), k)
        print("✓", k)


def gen_overlays(names):
    from kit.overlays import W, H, FPS
    from kit.registry import OVERLAYS
    os.makedirs(os.path.join(HERE, "overlays"), exist_ok=True)
    for k in names or OVERLAYS:
        out = os.path.join(HERE, "overlays", f"{k}.mp4")
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                              "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "23",
                              "-preset", "medium", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out],
                             stdin=subprocess.PIPE)
        for fr in OVERLAYS[k][0]():
            p.stdin.write(np.ascontiguousarray(fr).tobytes())
        p.stdin.close()
        p.wait()
        print("✓", k)


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    names = sys.argv[2:]
    if what in ("all", "sfx"):
        gen_sfx(names)
    if what in ("all", "luts"):
        gen_luts(names)
    if what in ("all", "overlays"):
        gen_overlays(names)
