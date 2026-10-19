"""
حركات ومؤثرات بصرية تُطبق على الفيديو نفسه في فترة زمنية محددة.
كل مؤثر دالة: f(img, lt, p, prm, st) -> img
  img: إطار RGB uint8      lt: الوقت منذ بداية المؤثر (ثانية)
  p:  التقدم من 0 إلى 1     prm: الخيارات      st: حالة خاصة بالمؤثر
"""
import math
import numpy as np
import cv2

TAU = 2 * math.pi


# =================== أدوات ===================

def ease(x):
    x = min(1.0, max(0.0, x))
    return 0.5 - 0.5 * math.cos(math.pi * x)


def ease_out(x):
    x = min(1.0, max(0.0, x))
    return 1 - (1 - x) ** 3


def bell(p):
    return math.sin(math.pi * min(1, max(0, p)))


def edge_env(lt, d, a=0.15, b=0.15):
    """صعود في البداية ونزول في النهاية."""
    return min(1.0, lt / a if a else 1, (d - lt) / b if b else 1)


def warp(img, z=1.0, cx=0.5, cy=0.5, tx=0.0, ty=0.0, angle=0.0):
    h, w = img.shape[:2]
    if abs(z - 1) < 1e-4 and abs(tx) < 0.01 and abs(ty) < 0.01 and abs(angle) < 1e-3:
        return img
    M = cv2.getRotationMatrix2D((cx * w, cy * h), angle, z)
    M[0, 2] += tx
    M[1, 2] += ty
    return cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def noise1d(seed, k=4, fmin=5, fmax=14):
    r = np.random.default_rng(seed)
    comps = [(r.uniform(fmin, fmax), r.uniform(0, TAU), r.uniform(0.5, 1)) for _ in range(k)]
    s = sum(c[2] for c in comps)
    return lambda t: sum(a * math.sin(TAU * f * t + ph) for f, ph, a in comps) / s


def blend(a, b, alpha):
    if alpha <= 0:
        return a
    if alpha >= 1:
        return b
    return cv2.addWeighted(a, 1 - alpha, b, alpha, 0)


def screen(a, b):
    a16 = a.astype(np.uint16)
    return (255 - ((255 - a16) * (255 - b.astype(np.uint16)) >> 8)).astype(np.uint8)


def hex_rgb(c):
    named = {"white": "FFFFFF", "black": "000000", "red": "FF1744", "blue": "2979FF", "pink": "FF2D95",
             "yellow": "FFE600", "cyan": "00E5FF", "green": "39FF14", "orange": "FF7A00", "purple": "B026FF"}
    c = named.get(str(c), str(c)).lstrip("#")
    return np.array([int(c[i:i + 2], 16) for i in (0, 2, 4)], np.uint8)


def motion_blur(img, length, angle=0.0):
    L = int(length)
    if L < 2:
        return img
    k = np.zeros((L, L), np.float32)
    k[L // 2, :] = 1
    M = cv2.getRotationMatrix2D((L / 2 - 0.5, L / 2 - 0.5), angle, 1)
    k = cv2.warpAffine(k, M, (L, L))
    k /= k.sum() + 1e-9
    return cv2.filter2D(img, -1, k, borderType=cv2.BORDER_REFLECT)


def zoom_blur(img, strength, cx=0.5, cy=0.5, n=7):
    if strength < 0.005:
        return img
    acc = img.astype(np.float32)
    for i in range(1, n):
        acc += warp(img, 1 + strength * i / (n - 1), cx, cy).astype(np.float32)
    return (acc / n).astype(np.uint8)


def rgb_shift(img, dx, dy=0):
    if abs(dx) < 0.5 and abs(dy) < 0.5:
        return img
    h, w = img.shape[:2]
    out = img.copy()
    M1 = np.float32([[1, 0, dx], [0, 1, dy]])
    M2 = np.float32([[1, 0, -dx], [0, 1, -dy]])
    out[..., 0] = cv2.warpAffine(img[..., 0], M1, (w, h), borderMode=cv2.BORDER_REFLECT)
    out[..., 2] = cv2.warpAffine(img[..., 2], M2, (w, h), borderMode=cv2.BORDER_REFLECT)
    return out


# =================== حركات الكاميرا ===================

def fx_zoom_punch(img, lt, p, prm, st):
    d = prm["_d"]
    rise = min(prm["speed"], d / 3)
    k = ease_out(lt / rise)
    if prm["back"] and lt > d - rise:
        k = ease((d - lt) / rise)
    return warp(img, 1 + (prm["amount"] - 1) * k, prm["x"], prm["y"])


def fx_zoom_in(img, lt, p, prm, st):
    return warp(img, 1 + (prm["amount"] - 1) * ease(p), prm["x"], prm["y"])


def fx_zoom_out(img, lt, p, prm, st):
    return warp(img, 1 + (prm["amount"] - 1) * (1 - ease(p)), prm["x"], prm["y"])


def fx_ken_burns(img, lt, p, prm, st):
    e = ease(p)
    h, w = img.shape[:2]
    z = 1 + (prm["amount"] - 1) * e
    tx = (prm["pan"] * w * 0.08) * (e - 0.5) * 2
    return warp(img, z, 0.5, 0.5, tx, 0)


def _shake(img, lt, p, prm, st, base_freq=(6, 14)):
    if "nx" not in st:
        s = int(prm["seed"])
        st["nx"], st["ny"], st["nr"] = noise1d(s, 4, *base_freq), noise1d(s + 1, 4, *base_freq), noise1d(s + 2, 3, 2, 6)
    h, w = img.shape[:2]
    e = edge_env(lt, prm["_d"], 0.08, 0.2) * prm["amount"]
    dx, dy = st["nx"](lt) * w * 0.02 * e, st["ny"](lt) * h * 0.025 * e
    ang = st["nr"](lt) * 1.2 * e * prm["rotate"]
    return warp(img, 1 + 0.05 * e, 0.5, 0.5, dx, dy, ang)


def fx_shake(img, lt, p, prm, st):
    return _shake(img, lt, p, prm, st, (6, 14))


def fx_earthquake(img, lt, p, prm, st):
    prm = dict(prm, amount=prm["amount"] * 2.2)
    out = _shake(img, lt, p, prm, st, (12, 25))
    return motion_blur(out, 6 * prm["amount"] * edge_env(lt, prm["_d"]), 90)


def fx_handheld(img, lt, p, prm, st):
    prm = dict(prm, amount=prm["amount"] * 0.35)
    return _shake(img, lt, p, prm, st, (0.3, 1.2))


def fx_pulse(img, lt, p, prm, st):
    beat = 60.0 / prm["bpm"]
    ph = (lt % beat) / beat
    z = 1 + (prm["amount"] - 1) * math.exp(-ph * 7)
    return warp(img, z, prm["x"], prm["y"])


def fx_tilt(img, lt, p, prm, st):
    d = prm["_d"]
    k = ease(min(lt / 0.4, (d - lt) / 0.4, 1)) if prm["back"] else ease(lt / 0.4)
    ang = prm["angle"] * k
    z = 1 + abs(math.sin(math.radians(ang))) * 0.9
    return warp(img, z, 0.5, 0.5, 0, 0, ang)


def fx_spin(img, lt, p, prm, st):
    e = ease(p)
    ang = 360 * prm["turns"] * e * (1 if prm["dir"] >= 0 else -1)
    z = 1 + 0.5 * bell(p)
    out = warp(img, z, 0.5, 0.5, 0, 0, ang)
    return zoom_blur(out, 0.12 * bell(p))


def fx_whip(img, lt, p, prm, st):
    h, w = img.shape[:2]
    b = bell(p) ** 1.5
    sgn = 1 if prm["dir"] >= 0 else -1
    vertical = prm.get("vertical", 0)
    shift = (ease(p) - 0.5) * 2 * w * 0.25 * sgn
    out = warp(img, 1.05, 0.5, 0.5, 0 if vertical else -shift, -shift if vertical else 0)
    return motion_blur(out, 4 + b * w * 0.12 * prm["amount"], 90 if vertical else 0)


def fx_zoom_transition(img, lt, p, prm, st):
    """زوم داخل حتى منتصف المؤثر ثم خروج من زوم — يخفي القطع بين لقطتين."""
    a = prm["amount"]
    if p < 0.5:
        z = 1 + (a - 1) * ease(p * 2) ** 2
    else:
        z = 1 + (a - 1) * (1 - ease((p - 0.5) * 2)) ** 2
    out = warp(img, z, prm["x"], prm["y"])
    return zoom_blur(out, 0.25 * bell(p) ** 2, prm["x"], prm["y"])


def fx_bounce(img, lt, p, prm, st):
    z = 1 + (prm["amount"] - 1) * math.exp(-lt * 6) * math.cos(lt * 28) ** 2 * (1 if lt < 1.5 else 0)
    return warp(img, z, prm["x"], prm["y"])


def fx_slide(img, lt, p, prm, st):
    """دخول الصورة من جانب."""
    h, w = img.shape[:2]
    e = ease_out(lt / max(0.05, prm["speed"]))
    dirs = {"left": (-1, 0), "right": (1, 0), "up": (0, -1), "down": (0, 1)}
    dx, dy = dirs.get(str(prm["from"]), (-1, 0))
    out = warp(img, 1, 0.5, 0.5, dx * w * (1 - e), dy * h * (1 - e))
    return motion_blur(out, (1 - e) * 60, 0 if dx else 90)


# =================== مؤثرات ضوئية ولونية ===================

def fx_flash(img, lt, p, prm, st):
    d = prm["_d"]
    rise = min(0.06, d * 0.2)
    a = (lt / rise) if lt < rise else (1 - (lt - rise) / max(1e-3, d - rise)) ** 2
    col = np.empty_like(img)
    col[:] = hex_rgb(prm["color"])
    return blend(img, col, a * prm["amount"])


def fx_dip(img, lt, p, prm, st):
    col = np.empty_like(img)
    col[:] = hex_rgb(prm["color"])
    return blend(img, col, bell(p) ** 0.7)


def fx_fade_in(img, lt, p, prm, st):
    col = np.empty_like(img)
    col[:] = hex_rgb(prm["color"])
    return blend(img, col, 1 - ease(p))


def fx_fade_out(img, lt, p, prm, st):
    col = np.empty_like(img)
    col[:] = hex_rgb(prm["color"])
    return blend(img, col, ease(p))


def fx_strobe(img, lt, p, prm, st):
    on = int(lt * prm["rate"] * 2) % 2 == 0
    if on:
        return img
    col = np.empty_like(img)
    col[:] = hex_rgb(prm["color"])
    return blend(img, col, prm["amount"])


def fx_bw(img, lt, p, prm, st):
    g = cv2.cvtColor(cv2.cvtColor(img, cv2.COLOR_RGB2GRAY), cv2.COLOR_GRAY2RGB)
    return blend(img, g, edge_env(lt, prm["_d"], 0.12, 0.12))


def fx_invert(img, lt, p, prm, st):
    return 255 - img


def fx_tint(img, lt, p, prm, st):
    g = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY).astype(np.float32)[..., None] / 255
    col = hex_rgb(prm["color"]).astype(np.float32)
    duo = (g * col).astype(np.uint8)
    return blend(img, duo, prm["amount"] * edge_env(lt, prm["_d"], 0.12, 0.12))


def fx_glow(img, lt, p, prm, st):
    f = img.astype(np.float32) / 255
    bright = np.clip((f - prm["threshold"]) / (1 - prm["threshold"]), 0, 1)
    h, w = img.shape[:2]
    b = cv2.GaussianBlur(bright, (0, 0), w / 80)
    a = prm["amount"] * edge_env(lt, prm["_d"], 0.15, 0.15)
    return (np.clip(1 - (1 - f) * (1 - b * a), 0, 1) * 255).astype(np.uint8)


def fx_light_sweep(img, lt, p, prm, st):
    h, w = img.shape[:2]
    if "g" not in st:
        y, x = np.mgrid[0:h, 0:w].astype(np.float32)
        st["g"] = (x / w + y / h * 0.6)
    pos = -0.3 + 1.9 * ease(p)
    band = np.exp(-((st["g"] - pos) / 0.06) ** 2) * prm["amount"]
    col = hex_rgb(prm["color"]).astype(np.float32)
    add = (band[..., None] * col).astype(np.uint8)
    return screen(img, add)


def fx_vignette(img, lt, p, prm, st):
    h, w = img.shape[:2]
    if "v" not in st:
        y, x = np.mgrid[0:h, 0:w].astype(np.float32)
        r = np.sqrt(((x / w - 0.5) * 1.3) ** 2 + (y / h - 0.5) ** 2)
        st["v"] = np.clip(1 - (r / 0.75) ** 2.5, 0, 1)[..., None]
    a = prm["amount"] * edge_env(lt, prm["_d"], 0.2, 0.2)
    v = 1 - a * (1 - st["v"])
    return (img * v).astype(np.uint8)


# =================== غلتش ورقمي ===================

def fx_glitch(img, lt, p, prm, st):
    r = np.random.default_rng(int(lt * 1000) + int(prm["seed"]))
    h, w = img.shape[:2]
    a = prm["amount"] * edge_env(lt, prm["_d"], 0.03, 0.05)
    if r.random() > 0.85 * min(1, a + 0.3):
        return rgb_shift(img, 3 * a)
    out = rgb_shift(img, r.uniform(4, 22) * a * (1 if r.random() < 0.5 else -1), r.uniform(-3, 3) * a)
    for _ in range(int(r.integers(2, 9) * a) + 1):
        y0 = int(r.uniform(0, h))
        hh = int(r.uniform(4, h * 0.08))
        sh = int(r.uniform(-w * 0.08, w * 0.08) * a)
        out[y0:y0 + hh] = np.roll(out[y0:y0 + hh], sh, axis=1)
    if r.random() < 0.35 * a:
        y0, x0 = int(r.uniform(0, h * 0.9)), int(r.uniform(0, w * 0.9))
        bh, bw = int(r.uniform(10, h * 0.12)), int(r.uniform(30, w * 0.3))
        out[y0:y0 + bh, x0:x0 + bw] = out[y0:y0 + bh, x0:x0 + bw][..., ::-1]
    if r.random() < 0.15 * a:
        out = 255 - out
    return out


def fx_rgb_split(img, lt, p, prm, st):
    h, w = img.shape[:2]
    return rgb_shift(img, w * 0.006 * prm["amount"] * edge_env(lt, prm["_d"], 0.1, 0.1))


def fx_vhs(img, lt, p, prm, st):
    r = np.random.default_rng(int(lt * 1000))
    h, w = img.shape[:2]
    a = prm["amount"] * edge_env(lt, prm["_d"], 0.1, 0.1)
    ycc = cv2.cvtColor(img, cv2.COLOR_RGB2YCrCb)
    ycc[..., 1] = cv2.blur(ycc[..., 1], (int(1 + 12 * a), 1))
    ycc[..., 2] = cv2.blur(ycc[..., 2], (int(1 + 12 * a), 1))
    out = cv2.cvtColor(ycc, cv2.COLOR_YCrCb2RGB)
    out = rgb_shift(out, 3 * a)
    jit = (r.normal(0, 1.5 * a, h)).astype(np.float32)
    mapx = (np.arange(w, dtype=np.float32)[None, :] + jit[:, None])
    mapy = np.repeat(np.arange(h, dtype=np.float32)[:, None], w, 1)
    out = cv2.remap(out, mapx, mapy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    out[::3] = (out[::3] * (1 - 0.18 * a)).astype(np.uint8)
    y0 = int((lt * 0.4 % 1.2) * h)
    band = slice(max(0, y0 - 8), min(h, y0 + 8))
    out[band] = np.clip(out[band].astype(np.int16) + r.integers(0, 90, out[band].shape), 0, 255).astype(np.uint8)
    return out


def fx_pixelate(img, lt, p, prm, st):
    h, w = img.shape[:2]
    x0, y0 = int(prm["x"] * w), int(prm["y"] * h)
    x1, y1 = int(min(w, x0 + prm["w"] * w)), int(min(h, y0 + prm["h"] * h))
    reg = img[y0:y1, x0:x1]
    if reg.size == 0:
        return img
    bs = max(2, int(prm["block"] * w / 100))
    small = cv2.resize(reg, (max(1, reg.shape[1] // bs), max(1, reg.shape[0] // bs)), interpolation=cv2.INTER_AREA)
    out = img.copy()
    out[y0:y1, x0:x1] = cv2.resize(small, (reg.shape[1], reg.shape[0]), interpolation=cv2.INTER_NEAREST)
    return out


def fx_blur_region(img, lt, p, prm, st):
    h, w = img.shape[:2]
    x0, y0 = int(prm["x"] * w), int(prm["y"] * h)
    x1, y1 = int(min(w, x0 + prm["w"] * w)), int(min(h, y0 + prm["h"] * h))
    out = img.copy()
    if x1 > x0 and y1 > y0:
        out[y0:y1, x0:x1] = cv2.GaussianBlur(img[y0:y1, x0:x1], (0, 0), max(2, w * 0.015 * prm["amount"]))
    return out


def fx_blur(img, lt, p, prm, st):
    s = prm["amount"] * edge_env(lt, prm["_d"], 0.2, 0.2) * img.shape[1] / 120
    return cv2.GaussianBlur(img, (0, 0), s) if s > 0.3 else img


def fx_blur_in(img, lt, p, prm, st):
    s = prm["amount"] * (1 - ease(p)) * img.shape[1] / 100
    return cv2.GaussianBlur(img, (0, 0), s) if s > 0.3 else img


def fx_blur_out(img, lt, p, prm, st):
    s = prm["amount"] * ease(p) * img.shape[1] / 100
    return cv2.GaussianBlur(img, (0, 0), s) if s > 0.3 else img


def fx_zoom_blur(img, lt, p, prm, st):
    return zoom_blur(img, 0.3 * prm["amount"] * bell(p), prm["x"], prm["y"])


def fx_mirror(img, lt, p, prm, st):
    out = img.copy()
    w = img.shape[1]
    out[:, w // 2:] = img[:, : w - w // 2][:, ::-1]
    return out


def fx_wave(img, lt, p, prm, st):
    h, w = img.shape[:2]
    if "mx" not in st:
        st["mx"] = np.repeat(np.arange(w, dtype=np.float32)[None, :], h, 0)
        st["my"] = np.repeat(np.arange(h, dtype=np.float32)[:, None], w, 1)
    a = prm["amount"] * edge_env(lt, prm["_d"], 0.2, 0.2) * w * 0.012
    mapx = st["mx"] + a * np.sin(st["my"] / h * TAU * 3 + lt * 6)
    mapy = st["my"] + a * 0.6 * np.sin(st["mx"] / w * TAU * 2 + lt * 4)
    return cv2.remap(img, mapx, mapy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def fx_bulge(img, lt, p, prm, st):
    h, w = img.shape[:2]
    if "r" not in st:
        y, x = np.mgrid[0:h, 0:w].astype(np.float32)
        st["dx"], st["dy"] = x / w - prm["x"], (y / h - prm["y"]) * h / w
        st["r"] = np.sqrt(st["dx"] ** 2 + st["dy"] ** 2)
    k = prm["amount"] * 0.5 * edge_env(lt, prm["_d"], 0.15, 0.15)
    R = 0.35
    f = np.where(st["r"] < R, (st["r"] / R) ** k, 1.0)
    mapx = (prm["x"] + st["dx"] * f) * w
    mapy = (prm["y"] + st["dy"] * f * w / h) * h
    return cv2.remap(img, mapx.astype(np.float32), mapy.astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def fx_film(img, lt, p, prm, st):
    r = np.random.default_rng(int(lt * 1000))
    a = prm["amount"]
    out = img.astype(np.float32) * (1 + r.uniform(-0.08, 0.08) * a)
    out = warp(np.clip(out, 0, 255).astype(np.uint8), 1.01, 0.5, 0.5, 0, r.normal(0, 1.5 * a))
    g = cv2.cvtColor(out, cv2.COLOR_RGB2GRAY)
    sep = np.stack([g * 1.07, g * 0.95, g * 0.75], -1)
    return blend(out, np.clip(sep, 0, 255).astype(np.uint8), 0.6 * a)


def fx_letterbox(img, lt, p, prm, st):
    h, w = img.shape[:2]
    target_h = w / prm["ratio"]
    bar = max(0, (h - target_h) / 2)
    k = ease_out(lt / 0.6)
    if prm["back"] and lt > prm["_d"] - 0.6:
        k = ease((prm["_d"] - lt) / 0.6)
    b = int(bar * k)
    if b <= 0:
        return img
    out = img.copy()
    out[:b] = 0
    out[h - b:] = 0
    return out


def fx_echo(img, lt, p, prm, st):
    buf = st.setdefault("buf", [])
    buf.append(img)
    if len(buf) > int(prm["frames"]):
        buf.pop(0)
    acc = img.astype(np.float32)
    wsum = 1.0
    for i, f in enumerate(reversed(buf[:-1])):
        wt = prm["amount"] ** (i + 1)
        acc += f.astype(np.float32) * wt
        wsum += wt
    return (acc / wsum).astype(np.uint8)


def fx_impact(img, lt, p, prm, st):
    """زوم + اهتزاز + فلاش: ضربة قوية للحظات المهمة."""
    out = fx_zoom_punch(img, lt, p, dict(prm, speed=0.06, back=0), st)
    out = _shake(out, lt, p, dict(prm, amount=prm["amount"] * 1.2), st, (10, 20))
    if lt < 0.2:
        white = np.full_like(out, 255)
        out = blend(out, white, (1 - lt / 0.2) * 0.7)
    return rgb_shift(out, 8 * max(0, 1 - lt / 0.3))


# =================== تجميد ===================

def fx_freeze(img, lt, p, prm, st):
    if "f" not in st:
        st["f"] = img.copy()
    out = st["f"]
    if prm["bw"]:
        out = cv2.cvtColor(cv2.cvtColor(out, cv2.COLOR_RGB2GRAY), cv2.COLOR_GRAY2RGB)
    if prm["zoom"] > 1:
        out = warp(out, 1 + (prm["zoom"] - 1) * ease_out(lt / 0.25), 0.5, 0.5)
    return out


# =================== السجل ===================
# الاسم: (الدالة، القيم الافتراضية، التصنيف، الوصف)

C = {"x": 0.5, "y": 0.5}
FX = {
    "zoom-punch":   (fx_zoom_punch,   dict(C, amount=1.25, speed=0.12, back=1, d=1.0), "حركة", "زوم سريع على لحظة مهمة"),
    "zoom-in":      (fx_zoom_in,      dict(C, amount=1.3, d=3.0), "حركة", "زوم داخل بطيء"),
    "zoom-out":     (fx_zoom_out,     dict(C, amount=1.3, d=3.0), "حركة", "زوم خارج بطيء"),
    "ken-burns":    (fx_ken_burns,    dict(amount=1.2, pan=1.0, d=5.0), "حركة", "زوم مع تحريك (للصور)"),
    "shake":        (fx_shake,        dict(amount=1.0, rotate=1.0, seed=1, d=0.8), "حركة", "اهتزاز الكاميرا"),
    "earthquake":   (fx_earthquake,   dict(amount=1.0, rotate=1.0, seed=2, d=1.0), "حركة", "اهتزاز قوي (زلزال)"),
    "handheld":     (fx_handheld,     dict(amount=1.0, rotate=1.0, seed=3, d=5.0), "حركة", "كاميرا محمولة باليد"),
    "pulse":        (fx_pulse,        dict(C, amount=1.06, bpm=120, d=4.0), "حركة", "نبض مع الإيقاع"),
    "bounce":       (fx_bounce,       dict(C, amount=1.12, d=1.0), "حركة", "ارتداد"),
    "tilt":         (fx_tilt,         dict(angle=8.0, back=1, d=2.0), "حركة", "ميلان الكاميرا"),
    "slide-in":     (fx_slide,        dict(speed=0.35, **{"from": "left"}, d=0.5), "حركة", "دخول من جانب"),
    "spin":         (fx_spin,         dict(turns=1.0, dir=1, d=0.6), "انتقال", "لفّة كاملة (تخفي القطع)"),
    "whip":         (fx_whip,         dict(amount=1.0, dir=1, vertical=0, d=0.35), "انتقال", "سحبة سريعة (Whip Pan)"),
    "zoom-transition": (fx_zoom_transition, dict(C, amount=2.5, d=0.5), "انتقال", "زوم عبور بين لقطتين"),
    "flash":        (fx_flash,        dict(color="white", amount=1.0, d=0.4), "انتقال", "فلاش"),
    "dip":          (fx_dip,          dict(color="black", d=0.6), "انتقال", "غمق ورجوع"),
    "fade-in":      (fx_fade_in,      dict(color="black", d=1.0), "انتقال", "ظهور تدريجي"),
    "fade-out":     (fx_fade_out,     dict(color="black", d=1.0), "انتقال", "اختفاء تدريجي"),
    "impact":       (fx_impact,       dict(C, amount=1.3, rotate=1.0, seed=5, d=0.5), "ضربة", "زوم+اهتزاز+فلاش للحظة قوية"),
    "glitch":       (fx_glitch,       dict(amount=1.0, seed=0, d=0.5), "رقمي", "غلتش"),
    "rgb-split":    (fx_rgb_split,    dict(amount=1.0, d=1.0), "رقمي", "انفصال ألوان"),
    "vhs":          (fx_vhs,          dict(amount=1.0, d=3.0), "رقمي", "شريط VHS قديم"),
    "strobe":       (fx_strobe,       dict(rate=8.0, color="black", amount=0.8, d=1.0), "ضوء", "ستروب"),
    "light-sweep":  (fx_light_sweep,  dict(color="white", amount=0.5, d=0.8), "ضوء", "لمعة تعبر الشاشة"),
    "glow":         (fx_glow,         dict(amount=0.8, threshold=0.6, d=2.0), "ضوء", "توهج للمناطق المضيئة"),
    "vignette":     (fx_vignette,     dict(amount=0.6, d=3.0), "ضوء", "تعتيم الأطراف"),
    "bw":           (fx_bw,           dict(d=2.0), "لون", "أبيض وأسود مؤقت"),
    "invert":       (fx_invert,       dict(d=0.1), "لون", "عكس الألوان"),
    "tint":         (fx_tint,         dict(color="cyan", amount=0.6, d=2.0), "لون", "صبغة لونية"),
    "film":         (fx_film,         dict(amount=1.0, d=3.0), "لون", "فيلم قديم (اهتزاز وارتعاش)"),
    "blur":         (fx_blur,         dict(amount=1.0, d=2.0), "تمويه", "تمويه"),
    "blur-in":      (fx_blur_in,      dict(amount=1.0, d=0.8), "تمويه", "من ضبابي لواضح"),
    "blur-out":     (fx_blur_out,     dict(amount=1.0, d=0.8), "تمويه", "من واضح لضبابي"),
    "zoom-blur":    (fx_zoom_blur,    dict(C, amount=1.0, d=0.5), "تمويه", "تمويه زوم"),
    "pixelate":     (fx_pixelate,     dict(x=0.0, y=0.0, w=1.0, h=1.0, block=3.0, d=2.0), "تمويه", "تقطيع بكسل (إخفاء)"),
    "blur-region":  (fx_blur_region,  dict(x=0.35, y=0.3, w=0.3, h=0.4, amount=1.0, d=2.0), "تمويه", "تمويه منطقة (إخفاء وجه/رقم)"),
    "mirror":       (fx_mirror,       dict(d=2.0), "تشويه", "مرآة"),
    "wave":         (fx_wave,         dict(amount=1.0, d=2.0), "تشويه", "تموج (حلم/دوخة)"),
    "bulge":        (fx_bulge,        dict(C, amount=1.0, d=1.5), "تشويه", "انتفاخ عدسة"),
    "echo":         (fx_echo,         dict(amount=0.7, frames=8, d=2.0), "تشويه", "صدى حركة (أثر)"),
    "letterbox":    (fx_letterbox,    dict(ratio=2.35, back=1, d=4.0), "سينمائي", "أشرطة سينمائية متحركة"),
    "freeze":       (fx_freeze,       dict(bw=0, zoom=1.0, d=1.5), "سينمائي", "تجميد اللقطة"),
}


def parse(spec):
    parts = [s.strip() for s in spec.split(",") if s.strip()]
    name = parts[0]
    if name not in FX:
        raise SystemExit(f"مؤثر غير موجود: {name}")
    prm = dict(FX[name][1])
    prm["t"] = 0.0
    for p in parts[1:]:
        k, _, v = p.partition("=")
        if v == "":
            prm[k] = 1
            continue
        try:
            prm[k] = float(v)
        except ValueError:
            prm[k] = v
    prm["_d"] = prm.pop("d")
    return name, prm
