#!/usr/bin/env python3
"""
أداة المونتاج: حركات، انتقالات، فلاتر ألوان، طبقات ضوئية، مؤثرات صوتية، ستيكرات نيون.

  python3 edit.py list [fx|transitions|sfx|luts|overlays|stickers]

  python3 edit.py apply in.mp4 out.mp4 \
      --fx "zoom-punch,t=3.2,d=1.5" --fx "shake,t=7,d=0.6" \
      --sfx "whoosh-short,t=3" --sfx "impact-boom,t=7,vol=0.8" \
      --overlay "leak-warm,t=0,d=4,opacity=0.7" \
      --sticker "arrow,t=10,pos=top-right" \
      --lut "cinematic,strength=0.8" --grain 0.3 --vignette 0.5 \
      --music song.mp3,vol=0.25,duck=1

  python3 edit.py join a.mp4 b.mp4 c.mp4 out.mp4 --transition slideleft --td 0.5 --whoosh

صيغة كل خيار: اسم ثم خيارات key=value مفصولة بفواصل.
  t = وقت البداية بالثواني     d = المدة
"""
import argparse
import json
import os
import random
import subprocess
import sys
import tempfile

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)

from kit.registry import FX, LUTS, OVERLAYS, SFX, TRANS, NEW, NEW3, BASIC, badge  # noqa: E402
from kit.effects import parse as parse_fx, screen  # noqa: E402
from kit.effects2 import WINDOW  # noqa: E402
from kit.luts import write_cube  # noqa: E402

TRANSITIONS = [
    "fade", "fadeblack", "fadewhite", "dissolve", "wipeleft", "wiperight", "wipeup", "wipedown",
    "slideleft", "slideright", "slideup", "slidedown", "smoothleft", "smoothright", "smoothup", "smoothdown",
    "circleopen", "circleclose", "circlecrop", "rectcrop", "vertopen", "vertclose", "horzopen", "horzclose",
    "radial", "pixelize", "zoomin", "hblur", "fadegrays", "distance", "diagtl", "diagtr", "diagbl", "diagbr",
    "hlslice", "hrslice", "vuslice", "vdslice", "squeezeh", "squeezev", "wipetl", "wipetr", "wipebl", "wipebr",
    "hlwind", "hrwind", "vuwind", "vdwind", "coverleft", "coverright", "coverup", "coverdown",
    "revealleft", "revealright", "revealup", "revealdown",
]
ALIASES = {"flash": "fadewhite", "black": "fadeblack", "white": "fadewhite", "zoom": "zoomin", "blur": "hblur",
           "slide": "slideleft", "wipe": "wipeleft", "cross": "dissolve", "gray": "fadegrays", "wind": "hlwind"}


# =================== أدوات ===================

def probe(path):
    j = json.loads(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "stream=codec_type,width,height,avg_frame_rate,r_frame_rate:stream_side_data=rotation:stream_tags=rotate:format=duration",
         "-of", "json", path], capture_output=True, text=True, check=True).stdout)
    v = next(s for s in j["streams"] if s["codec_type"] == "video")
    w, h = int(v["width"]), int(v["height"])
    rot = 0
    for sd in v.get("side_data_list", []) or []:
        rot = int(float(sd.get("rotation", 0) or 0))
    rot = rot or int(float(v.get("tags", {}).get("rotate", 0) or 0))
    if abs(rot) % 180 == 90:
        w, h = h, w
    fr = v.get("avg_frame_rate", "0/0")
    if fr in ("0/0", "0/1"):
        fr = v.get("r_frame_rate", "30/1")
    n, d = fr.split("/")
    fps = float(n) / float(d) if float(d) else 30.0
    if not (5 <= fps <= 120):
        fps = 30.0
    has_audio = any(s["codec_type"] == "audio" for s in j["streams"])
    return w, h, round(fps, 3), float(j["format"]["duration"]), has_audio


def kv(spec, defaults):
    parts = [s.strip() for s in spec.split(",") if s.strip()]
    o = dict(defaults)
    o["name"] = parts[0]
    for p in parts[1:]:
        k, _, v = p.partition("=")
        if v == "":
            o[k] = 1
        else:
            try:
                o[k] = float(v)
            except ValueError:
                o[k] = v
    return o


def sfx_path(name):
    if os.path.exists(name):
        return name
    p = os.path.join(HERE, "sfx", f"{name}.wav")
    if not os.path.exists(p):
        raise SystemExit(f"مؤثر صوتي غير موجود: {name}  (شغّل: edit.py list sfx)")
    return p


def overlay_path(name):
    if os.path.exists(name):
        return name
    p = os.path.join(HERE, "overlays", f"{name}.mp4")
    if not os.path.exists(p):
        raise SystemExit(f"طبقة غير موجودة: {name}  (شغّل: edit.py list overlays)")
    return p


def lut_file(spec, tmp):
    o = kv(spec, {"strength": 1.0})
    name = o["name"]
    if os.path.exists(name):
        return name
    if name not in LUTS:
        raise SystemExit(f"فلتر غير موجود: {name}  (شغّل: edit.py list luts)")
    if o["strength"] == 1.0:
        return os.path.join(HERE, "luts", f"{name}.cube")
    p = os.path.join(tmp, f"{name}.cube")
    write_cube(p, name, float(o["strength"]))
    return p


def esc(p):
    return p.replace("\\", "/").replace(":", "\\:").replace("'", "\\'")


# =================== مصادر الطبقات ===================

class OverlaySrc:
    def __init__(self, spec, W, H, fps):
        o = kv(spec, {"t": 0.0, "d": 6.0, "opacity": 1.0})
        self.path = overlay_path(o["name"])
        self.t0, self.d, self.op = float(o["t"]), float(o["d"]), float(o["opacity"])
        self.W, self.H, self.fps = W, H, fps
        self.proc = None
        self.done = False

    def active(self, t):
        return not self.done and self.t0 <= t < self.t0 + self.d

    def frame(self, t):
        if self.proc is None:
            self.proc = subprocess.Popen(
                ["ffmpeg", "-v", "error", "-stream_loop", "-1", "-i", self.path, "-t", str(self.d),
                 "-vf", f"scale={self.W}:{self.H}:force_original_aspect_ratio=increase,crop={self.W}:{self.H},fps={self.fps}",
                 "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
        buf = self.proc.stdout.read(self.W * self.H * 3)
        if len(buf) < self.W * self.H * 3:
            self.done = True
            return None
        f = np.frombuffer(buf, np.uint8).reshape(self.H, self.W, 3)
        lt = t - self.t0
        env = min(1.0, lt / 0.3, (self.d - lt) / 0.3)  # دخول وخروج ناعم
        a = self.op * max(0.0, env)
        if a < 0.999:
            f = (f.astype(np.float32) * a).astype(np.uint8)
        return f


class StickerSrc:
    def __init__(self, spec, W, H, fps):
        import overlay as stk  # من مجلد Glowing-Icons الرئيسي
        from neon import Sticker
        o = stk.parse_spec(spec)
        self.S = stk.resolve_size(o["size"], W, H)
        self.x, self.y = stk.resolve_pos(o["pos"], W, H, self.S)
        self.t0, self.d = o["t"], o["d"]
        st = Sticker(o["name"], size=self.S, color=o["color"], rotate=o["rot"], flip=o["flip"], width=o["width"])
        self.gen = st.frames(o["d"], fps, draw_time=min(o["draw"], o["d"] * 0.5), fade_out=min(0.3, o["d"] * 0.2))
        self.done = False

    def active(self, t):
        return not self.done and self.t0 <= t < self.t0 + self.d

    def apply(self, img):
        try:
            fr = next(self.gen)
        except StopIteration:
            self.done = True
            return img
        H, W = img.shape[:2]
        x0, y0 = max(0, self.x), max(0, self.y)
        x1, y1 = min(W, self.x + self.S), min(H, self.y + self.S)
        if x1 <= x0 or y1 <= y0:
            return img
        s = fr[y0 - self.y:y1 - self.y, x0 - self.x:x1 - self.x].astype(np.float32)
        a = s[..., 3:4] / 255
        reg = img[y0:y1, x0:x1].astype(np.float32)
        img[y0:y1, x0:x1] = (s[..., :3] * a + reg * (1 - a)).astype(np.uint8)
        return img


# =================== apply ===================

def cmd_apply(a):
    W, H, fps, dur, has_audio = probe(a.input)
    tmp = tempfile.mkdtemp(prefix="montage_")
    fx_list = []
    windows = []
    for s in a.fx:
        name, prm = parse_fx(s)
        prm["_name"] = name
        fx_list.append((name, prm, {}))
        if name in WINDOW:
            windows.append((name, prm))
    overlays = [OverlaySrc(s, W, H, fps) for s in a.overlay]
    stickers = [StickerSrc(s, W, H, fps) for s in a.sticker]
    need_frames = bool(fx_list or overlays or stickers)

    # ---- فلاتر ffmpeg للصورة ----
    vf = []
    if a.lut:
        vf.append(f"lut3d='{esc(lut_file(a.lut, tmp))}'")
    if a.vignette:
        vf.append(f"vignette=a={0.35 + 0.5 * a.vignette:.3f}")
    if a.sharpen:
        vf.append(f"unsharp=5:5:{0.6 * a.sharpen:.2f}")
    if a.grain:
        vf.append(f"noise=alls={int(6 + 22 * a.grain)}:allf=t")
    vf.append("format=yuv420p")

    # ---- المدخلات ----
    inputs = []
    if need_frames:
        inputs += ["-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps), "-i", "-"]
        inputs += ["-i", a.input]
        src_a = "1:a"
        n_in = 2
    else:
        inputs += ["-i", a.input]
        src_a = "0:a"
        n_in = 1
    fc = [f"[0:v]{','.join(vf)}[vout]"]
    mix = []
    if has_audio:
        fc.append(f"[{src_a}]aresample=48000,aformat=channel_layouts=stereo,volume={a.voice}[a0]")
    else:
        inputs += ["-f", "lavfi", "-t", str(dur), "-i", "anullsrc=r=48000:cl=stereo"]
        fc.append(f"[{n_in}:a]anull[a0]")
        n_in += 1
    base = "[a0]"

    if a.music:
        o = kv(a.music, {"vol": 0.25, "duck": 1.0, "start": 0.0})
        inputs += ["-stream_loop", "-1", "-ss", str(o["start"]), "-i", o["name"]]
        fc.append(f"[{n_in}:a]aresample=48000,aformat=channel_layouts=stereo,volume={o['vol']},"
                  f"afade=t=in:d=1,afade=t=out:st={max(0, dur - 2)}:d=2[mus]")
        n_in += 1
        if o["duck"] and has_audio:
            fc.append("[a0]asplit[a0x][sc]")
            fc.append("[mus][sc]sidechaincompress=threshold=0.02:ratio=8:attack=30:release=500[musd]")
            base = "[a0x]"
            mix.append("[musd]")
        else:
            mix.append("[mus]")

    for i, s in enumerate(a.sfx):
        o = kv(s, {"t": 0.0, "vol": 0.8})
        inputs += ["-i", sfx_path(o["name"])]
        ms = int(float(o["t"]) * 1000)
        fc.append(f"[{n_in}:a]aresample=48000,aformat=channel_layouts=stereo,adelay={ms}:all=1,volume={o['vol']}[s{i}]")
        mix.append(f"[s{i}]")
        n_in += 1

    if mix:
        fc.append(f"{base}{''.join(mix)}amix=inputs={1 + len(mix)}:duration=first:normalize=0,alimiter=limit=0.95[aout]")
    else:
        fc.append(f"{base}anull[aout]")

    out_cmd = ["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", ";".join(fc),
               "-map", "[vout]", "-map", "[aout]", "-c:v", "libx264", "-crf", str(a.crf), "-preset", a.preset,
               "-c:a", "aac", "-b:a", "192k", "-t", str(dur), "-movflags", "+faststart", a.output]

    if not need_frames:
        subprocess.run(out_cmd, check=True)
        print("✓ تم:", a.output)
        return

    reader = subprocess.Popen(["ffmpeg", "-v", "error", "-i", a.input, "-vf", f"fps={fps}",
                               "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    writer = subprocess.Popen(out_cmd, stdin=subprocess.PIPE)
    fsize = W * H * 3
    total = int(dur * fps)

    def read():
        buf = reader.stdout.read(fsize)
        if len(buf) < fsize:
            return None
        return np.frombuffer(bytearray(buf), np.uint8).reshape(H, W, 3)

    starts = {int(round(prm["t"] * fps)): (name, prm) for name, prm in windows}

    def source():
        """الإطارات بالترتيب، مع إعادة ترتيب فترات مؤثرات الزمن."""
        j = 0
        while True:
            f = read()
            if f is None:
                return
            if j in starts:
                name, prm = starts[j]
                n = max(2, int(round(prm["_d"] * fps)))
                block = [f]
                while len(block) < n:
                    g = read()
                    if g is None:
                        break
                    block.append(g)
                m = len(block)
                for k in range(m):
                    q = WINDOW[name](k / max(1, m - 1), prm)
                    yield block[min(m - 1, max(0, int(round(q * (m - 1)))))]
                j += m
                continue
            yield f
            j += 1

    i = 0
    for img in source():
        t = i / fps
        for name, prm, st in fx_list:
            t0, d = prm["t"], prm["_d"]
            if t0 <= t < t0 + d:
                lt = t - t0
                img = FX[name][0](img, lt, lt / d, prm, st)
        for o in overlays:
            if o.active(t):
                f = o.frame(t)
                if f is not None:
                    img = screen(img, f)
        for s in stickers:
            if s.active(t):
                img = s.apply(np.ascontiguousarray(img))
        writer.stdin.write(np.ascontiguousarray(img, np.uint8).tobytes())
        i += 1
        if i % int(fps * 5) == 0:
            print(f"  {i}/{total} إطار", flush=True)
    writer.stdin.close()
    reader.wait()
    for o in overlays:
        if o.proc:
            o.proc.kill()
    if writer.wait() != 0:
        raise SystemExit("فشل الترميز")
    print("✓ تم:", a.output)


# =================== join ===================

def cmd_join(a):
    clips = a.clips[:-1]
    out = a.clips[-1]
    if len(clips) < 2:
        raise SystemExit("يلزم مقطعين على الأقل ثم اسم ملف الخرج")
    infos = [probe(c) for c in clips]
    if a.size:
        W, H = (int(v) for v in a.size.lower().split("x"))
    else:
        W, H = infos[0][0], infos[0][1]
    W, H = W // 2 * 2, H // 2 * 2
    fps = a.fps or infos[0][2]
    td = a.td
    trans = []
    names = a.transition or ["fade"]
    custom_pool = [k for k in TRANS if k not in BASIC]
    for k in range(len(clips) - 1):
        n = names[k % len(names)]
        if n == "random":
            n = random.choice(custom_pool)
        if n not in TRANS:
            n = ALIASES.get(n, n)
        if n not in TRANS and n not in TRANSITIONS:
            raise SystemExit(f"انتقال غير موجود: {n}  (شغّل: edit.py list transitions)")
        trans.append(n)
    use_py = any(n in TRANS and n not in TRANSITIONS for n in trans)
    if use_py:
        bad = [n for n in trans if n not in TRANS]
        if bad:
            raise SystemExit(f"لا يمكن خلط هذه الانتقالات مع الانتقالات الجديدة في نفس الأمر: {', '.join(bad)}")

    inputs, fc = [], []
    base_in = 1 if use_py else 0
    if use_py:
        inputs += ["-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps), "-i", "-"]
    for c in clips:
        inputs += ["-i", c]
    n_in = base_in + len(clips)
    for i, (c, info) in enumerate(zip(clips, infos)):
        if not use_py:
            fc.append(f"[{i}:v]scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:black,"
                      f"setsar=1,fps={fps},format=yuv420p,settb=AVTB[v{i}]")
        if info[4]:
            fc.append(f"[{base_in + i}:a]aresample=48000,aformat=channel_layouts=stereo,apad,atrim=0:{info[3]}[a{i}]")
        else:
            inputs += ["-f", "lavfi", "-t", str(info[3]), "-i", "anullsrc=r=48000:cl=stereo"]
            fc.append(f"[{n_in}:a]anull[a{i}]")
            n_in += 1
    cur_v, cur_a = ("[0:v]" if use_py else "[v0]"), "[a0]"
    length = infos[0][3]
    offsets = []
    for k in range(1, len(clips)):
        off = max(0.0, length - td)
        offsets.append(off)
        if not use_py:
            fc.append(f"{cur_v}[v{k}]xfade=transition={trans[k - 1]}:duration={td}:offset={off:.3f}[vx{k}]")
            cur_v = f"[vx{k}]"
        fc.append(f"{cur_a}[a{k}]acrossfade=d={td}[ax{k}]")
        cur_a = f"[ax{k}]"
        length = length + infos[k][3] - td

    mix = []
    if a.whoosh:
        sp = sfx_path(a.whoosh_sfx)
        for k, off in enumerate(offsets):
            inputs += ["-i", sp]
            ms = int(max(0, off - 0.1) * 1000)
            fc.append(f"[{n_in}:a]aresample=48000,aformat=channel_layouts=stereo,adelay={ms}:all=1,volume={a.whoosh_vol}[w{k}]")
            mix.append(f"[w{k}]")
            n_in += 1
    if mix:
        fc.append(f"{cur_a}{''.join(mix)}amix=inputs={1 + len(mix)}:duration=first:normalize=0,alimiter=limit=0.95[aout]")
        cur_a = "[aout]"
    if use_py:
        fc.append(f"{cur_v}format=yuv420p[vout]")
        cur_v = "[vout]"
    cmd = ["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", ";".join(fc), "-map", cur_v, "-map", cur_a,
           "-c:v", "libx264", "-crf", str(a.crf), "-preset", "medium", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out]
    if not use_py:
        subprocess.run(cmd, check=True)
    else:
        _join_frames(clips, trans, W, H, fps, td, cmd)
    print(f"✓ تم: {out}  ({length:.1f}s)  الانتقالات: {', '.join(trans)}")


def _join_frames(clips, trans, W, H, fps, td, cmd):
    """يدمج المقاطع إطاراً إطاراً مع انتقالات بايثون."""
    from collections import deque
    fsize = W * H * 3
    nt = max(2, int(round(td * fps)))
    writer = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    def frames(path):
        p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", path, "-vf",
                              f"scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:black,"
                              f"setsar=1,fps={fps}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
        while True:
            buf = p.stdout.read(fsize)
            if len(buf) < fsize:
                break
            yield np.frombuffer(bytearray(buf), np.uint8).reshape(H, W, 3)
        p.wait()

    def put(f):
        writer.stdin.write(np.ascontiguousarray(f, np.uint8).tobytes())

    tail = deque()
    for ci, path in enumerate(clips):
        gen = frames(path)
        if ci > 0:
            head = []
            for f in gen:
                head.append(f)
                if len(head) >= nt:
                    break
            m = min(len(tail), len(head))
            tl = list(tail)[-m:] if m else []
            for x in list(tail)[: len(tail) - m]:
                put(x)
            fn = TRANS[trans[ci - 1]][0]
            st = {}
            for k in range(m):
                put(fn(tl[k], head[k], (k + 0.5) / m, st))
            tail = deque()
            for f in head[m:]:
                tail.append(f)
        last = ci == len(clips) - 1
        for f in gen:
            tail.append(f)
            if not last and len(tail) > nt:
                put(tail.popleft())
            elif last:
                put(tail.popleft())
    for f in tail:
        put(f)
    writer.stdin.close()
    if writer.wait() != 0:
        raise SystemExit("فشل الترميز")


# =================== list ===================

def cmd_list(a):
    what = a.what or "all"
    star = badge  # 🔥 الدفعة 3، ⭐ الدفعة 2

    def head(t):
        print(f"\n=== {t} ===")

    if what in ("all", "fx"):
        head("حركات ومؤثرات --fx")
        for k, (_, d, cat, ar) in FX.items():
            opts = ", ".join(f"{kk}={vv}" for kk, vv in d.items())
            print(f"  {k:16} [{cat}] {ar}{star('fx', k)}   ({opts})")
    if what in ("all", "transitions"):
        head("انتقالات join --transition")
        print("  جديدة (مخصصة):")
        for k, (_, ar) in TRANS.items():
            print(f"    {k:16} {ar}{star('transitions', k)}")
        print("  كلاسيكية:")
        print("    " + " ".join(TRANSITIONS))
        print("  اختصارات: " + ", ".join(f"{k}={v}" for k, v in ALIASES.items()) + ", random")
    if what in ("all", "sfx"):
        head("مؤثرات صوتية --sfx")
        for k, (_, cat, ar) in SFX.items():
            print(f"  {k:16} [{cat}] {ar}{star('sfx', k)}")
    if what in ("all", "luts"):
        head("فلاتر ألوان --lut")
        for k, (_, ar) in LUTS.items():
            print(f"  {k:16} {ar}{star('luts', k)}")
    if what in ("all", "overlays"):
        head("طبقات ضوئية --overlay")
        for k, (_, ar) in OVERLAYS.items():
            print(f"  {k:16} {ar}{star('overlays', k)}")
    if what in ("all", "stickers"):
        from neon import STICKERS
        head("ستيكرات نيون --sticker")
        for k, (_, c, ar) in STICKERS.items():
            print(f"  {k:16} {ar}")


def main():
    ap = argparse.ArgumentParser(description="أداة المونتاج", formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("apply", help="تطبيق مؤثرات على فيديو")
    p.add_argument("input")
    p.add_argument("output")
    p.add_argument("--fx", action="append", default=[])
    p.add_argument("--sfx", action="append", default=[])
    p.add_argument("--overlay", action="append", default=[])
    p.add_argument("--sticker", action="append", default=[])
    p.add_argument("--lut")
    p.add_argument("--grain", type=float, default=0)
    p.add_argument("--vignette", type=float, default=0)
    p.add_argument("--sharpen", type=float, default=0)
    p.add_argument("--music")
    p.add_argument("--voice", type=float, default=1.0, help="مستوى صوت الفيديو الأصلي")
    p.add_argument("--crf", default="18")
    p.add_argument("--preset", default="medium")
    p.set_defaults(fn=cmd_apply)

    p = sub.add_parser("join", help="دمج مقاطع مع انتقالات")
    p.add_argument("clips", nargs="+")
    p.add_argument("--transition", action="append")
    p.add_argument("--td", type=float, default=0.5, help="مدة الانتقال")
    p.add_argument("--size", help="مثل 1080x1920")
    p.add_argument("--fps", type=float)
    p.add_argument("--whoosh", action="store_true", help="إضافة صوت ووش مع كل انتقال")
    p.add_argument("--whoosh-sfx", default="whoosh-short")
    p.add_argument("--whoosh-vol", type=float, default=0.7)
    p.add_argument("--crf", default="18")
    p.set_defaults(fn=cmd_join)

    p = sub.add_parser("list", help="عرض كل ما هو متوفر")
    p.add_argument("what", nargs="?")
    p.set_defaults(fn=cmd_list)

    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
