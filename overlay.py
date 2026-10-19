#!/usr/bin/env python3
"""
تركيب ستيكرات نيون متحركة على فيديو.

أمثلة:
  python3 overlay.py video.mp4 out.mp4 --add "arrow,t=5,d=3,pos=top-right"
  python3 overlay.py video.mp4 out.mp4 \
      --add "circle,t=2,d=2.5,pos=50%:40%,size=35%,color=pink" \
      --add "like,t=8,pos=bottom-right,size=200" \
      --add "arrow,t=10,rot=90,flip"
  python3 overlay.py --list

خيارات كل ستيكر (مفصولة بفواصل، أولها اسم الستيكر):
  t=      وقت الظهور بالثواني (افتراضي 0)
  d=      المدة بالثواني (افتراضي 3)
  pos=    center | top | bottom | left | right | top-left | top-right |
          bottom-left | bottom-right | X:Y بالبكسل | X%:Y% نسبة من الفيديو
          (الإحداثيات تحدد مركز الستيكر)
  size=   الحجم بالبكسل أو نسبة من ارتفاع الفيديو مثل 30% (افتراضي 35%)
  color=  اسم لون أو كود #RRGGBB
  rot=    دوران بالدرجات
  flip    عكس أفقي
  width=  سماكة الخط (1 = عادي)
  draw=   مدة حركة الرسم بالثواني (0 = يظهر مباشرة)
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from neon import Sticker, STICKERS, COLORS  # noqa: E402
from neon.export import write_video  # noqa: E402


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height,r_frame_rate:format=duration", "-of", "json", path],
                         capture_output=True, text=True, check=True).stdout
    j = json.loads(out)
    s = j["streams"][0]
    num, den = s["r_frame_rate"].split("/")
    has_audio = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries",
                                "stream=index", "-of", "csv=p=0", path],
                               capture_output=True, text=True).stdout.strip() != ""
    return int(s["width"]), int(s["height"]), float(num) / float(den), float(j["format"]["duration"]), has_audio


def parse_spec(spec):
    parts = [p.strip() for p in spec.split(",") if p.strip()]
    o = {"name": parts[0], "t": 0.0, "d": 3.0, "pos": "center", "size": "35%",
         "color": None, "rot": 0.0, "flip": False, "width": 1.0, "draw": 0.7}
    for p in parts[1:]:
        if p == "flip":
            o["flip"] = True
            continue
        k, _, v = p.partition("=")
        if k not in o:
            raise SystemExit(f"خيار غير معروف: {k}")
        o[k] = float(v) if k in ("t", "d", "rot", "width", "draw") else v
    if o["name"] not in STICKERS:
        raise SystemExit(f"ستيكر غير موجود: {o['name']}  (شغّل --list)")
    return o


def resolve_size(size, W, H):
    s = str(size)
    px = H * float(s[:-1]) / 100 if s.endswith("%") else float(s)
    return max(32, int(px) // 2 * 2)


def resolve_pos(pos, W, H, S):
    named = {
        "center": (0.5, 0.5), "top": (0.5, 0), "bottom": (0.5, 1), "left": (0, 0.5), "right": (1, 0.5),
        "top-left": (0, 0), "top-right": (1, 0), "bottom-left": (0, 1), "bottom-right": (1, 1),
    }
    if pos in named:
        fx, fy = named[pos]
        # الستيكر فيه هامش للتوهج، فنسمح له يقترب من الحافة
        m = -0.08 * S
        x = m + fx * (W - S - 2 * m)
        y = m + fy * (H - S - 2 * m)
        return int(x), int(y)
    xs, ys = pos.split(":")
    cx = W * float(xs[:-1]) / 100 if xs.endswith("%") else float(xs)
    cy = H * float(ys[:-1]) / 100 if ys.endswith("%") else float(ys)
    return int(cx - S / 2), int(cy - S / 2)


def main():
    ap = argparse.ArgumentParser(description="تركيب ستيكرات نيون على فيديو",
                                 formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    ap.add_argument("input", nargs="?")
    ap.add_argument("output", nargs="?")
    ap.add_argument("--add", action="append", default=[], help="ستيكر واحد (كرّرها لأكثر من ستيكر)")
    ap.add_argument("--list", action="store_true", help="عرض الستيكرات والألوان")
    ap.add_argument("--crf", default="18", help="جودة الفيديو الناتج (أقل = أعلى جودة)")
    a = ap.parse_args()

    if a.list:
        print("الستيكرات:")
        for k, (_, c, ar) in STICKERS.items():
            print(f"  {k:16} {ar}  ({c})")
        print("الألوان:", ", ".join(COLORS))
        return
    if not (a.input and a.output and a.add):
        ap.error("يلزم: ملف الدخل، ملف الخرج، و --add واحد على الأقل")

    W, H, fps, dur, has_audio = probe(a.input)
    specs = [parse_spec(s) for s in a.add]
    tmp = tempfile.mkdtemp(prefix="neon_")
    inputs, filters, last = [], [], "[0:v]"

    for i, o in enumerate(specs):
        S = resolve_size(o["size"], W, H)
        x, y = resolve_pos(o["pos"], W, H, S)
        st = Sticker(o["name"], size=S, color=o["color"], rotate=o["rot"], flip=o["flip"], width=o["width"])
        path = os.path.join(tmp, f"s{i}.mov")
        frames = st.frames(o["d"], fps, draw_time=min(o["draw"], o["d"] * 0.5),
                           fade_out=min(0.3, o["d"] * 0.2))
        write_video(frames, path, S, fps)
        print(f"✓ {o['name']} عند {o['t']}s لمدة {o['d']}s")
        inputs += ["-i", path]
        t0, t1 = o["t"], o["t"] + o["d"]
        filters.append(f"[{i + 1}:v]setpts=PTS-STARTPTS+{t0}/TB[s{i}]")
        out = f"[v{i}]"
        filters.append(f"{last}[s{i}]overlay={x}:{y}:eof_action=pass:"
                       f"enable='between(t,{t0},{t1})'{out}")
        last = out

    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", a.input, *inputs,
           "-filter_complex", ";".join(filters), "-map", last]
    if has_audio:
        cmd += ["-map", "0:a?", "-c:a", "copy"]
    cmd += ["-c:v", "libx264", "-crf", a.crf, "-preset", "medium", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart", a.output]
    subprocess.run(cmd, check=True)
    print("✓ تم:", a.output)


if __name__ == "__main__":
    main()
