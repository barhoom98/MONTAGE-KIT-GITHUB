#!/usr/bin/env python3
"""
يصدّر كل الستيكرات إلى مجلد assets:
  assets/webm/<name>.webm  فيديو متحرك بخلفية شفافة (3 ثواني)
  assets/png/<name>.png    صورة ثابتة شفافة
  assets/preview.gif       معاينة لكل المجموعة على خلفية داكنة

الاستخدام:
  python3 export_all.py              # كل الستيكرات
  python3 export_all.py arrow heart  # ستيكرات محددة
"""
import os
import sys

from PIL import Image

from neon import Sticker, STICKERS
from neon.export import write_video

ROOT = os.path.dirname(os.path.abspath(__file__))
SIZE, FPS, DUR = 512, 30, 3.0


def export_one(name):
    st = Sticker(name, size=SIZE)
    write_video(st.frames(DUR, FPS), os.path.join(ROOT, "assets/webm", f"{name}.webm"), SIZE, FPS)
    Image.fromarray(st.frame(1.0, 1.0)).save(os.path.join(ROOT, "assets/png", f"{name}.png"), optimize=True)
    print("✓", name)


def preview(names, cell=120, cols=7):
    rows = (len(names) + cols - 1) // cols
    gens = [Sticker(n, size=cell).frames(DUR, 12) for n in names]
    out = []
    for frames in zip(*gens):
        sheet = Image.new("RGBA", (cols * cell, rows * cell), (12, 12, 20, 255))
        for i, f in enumerate(frames):
            sheet.alpha_composite(Image.fromarray(f), ((i % cols) * cell, (i // cols) * cell))
        out.append(sheet.convert("RGB").quantize(colors=255, method=Image.Quantize.MEDIANCUT))
    out[0].save(os.path.join(ROOT, "assets/preview.gif"), save_all=True, append_images=out[1:],
                duration=int(1000 / 12), loop=0, optimize=True)
    print("✓ preview.gif")


if __name__ == "__main__":
    os.makedirs(os.path.join(ROOT, "assets/webm"), exist_ok=True)
    os.makedirs(os.path.join(ROOT, "assets/png"), exist_ok=True)
    names = sys.argv[1:] or list(STICKERS)
    for n in names:
        export_one(n)
    if not sys.argv[1:]:
        preview(names)
