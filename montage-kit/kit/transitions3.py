"""
انتقالات — الدفعة 3.  f(a, b, p, st) -> إطار
"""
import math
import numpy as np
import cv2

from .effects import ease, ease_out, bell, warp, blend, screen, rgb_shift, zoom_blur, motion_blur
from .effects2 import _grid_maps, perspective, fast_blur
from .effects3 import _tv


def _noise(st, h, w, seed=1, scale=16, key="noise"):
    if key not in st:
        r = np.random.default_rng(seed)
        small = r.random((h // scale + 2, w // scale + 2)).astype(np.float32)
        n = cv2.resize(cv2.GaussianBlur(small, (0, 0), 1.5), (w, h), interpolation=cv2.INTER_CUBIC)
        st[key] = (n - n.min()) / (n.max() - n.min() + 1e-6)
    return st[key]


def t_ink(a, b, p, st):
    """الحبر: المقطع الثاني ينتشر كبقع حبر."""
    h, w = a.shape[:2]
    gx, gy = _grid_maps(st, h, w)
    if "ink" not in st:
        n = _noise(st, h, w, 3, 20)
        rad = np.sqrt(((gx - w / 2) / w) ** 2 + ((gy - h / 2) / w) ** 2)
        m = n * 0.55 + rad * 0.9
        st["ink"] = (m - m.min()) / (m.max() - m.min())
    thr = ease(p) * 1.15 - 0.05
    m = np.clip((thr - st["ink"]) / 0.04, 0, 1)
    edge = np.clip(1 - np.abs(thr - st["ink"]) / 0.02, 0, 1)[..., None]
    out = a * (1 - m[..., None]) + b * m[..., None]
    out = out * (1 - edge * 0.85)
    return out.astype(np.uint8)


def t_burn(a, b, p, st):
    """حرق: حافة نار تلتهم المقطع الأول."""
    h, w = a.shape[:2]
    gx, gy = _grid_maps(st, h, w)
    if "burn" not in st:
        n = _noise(st, h, w, 7, 12)
        st["burn"] = (gx / w) * 0.75 + n * 0.25 + (gy / h) * 0.1
    thr = ease(p) * 1.25 - 0.1
    d = st["burn"] - thr
    m = np.clip(-d / 0.01, 0, 1)[..., None]
    glow = np.exp(-(d / 0.03) ** 2)[..., None]
    char = np.clip(1 - np.abs(d) / 0.05, 0, 1)[..., None] * (d > 0)[..., None]
    out = a * (1 - m) + b * m
    out = out * (1 - char * 0.85)
    fire = np.array([255, 150, 40], np.float32) * glow * 1.2 + np.array([255, 240, 200], np.float32) * glow ** 6
    return np.clip(out + fire, 0, 255).astype(np.uint8)


def t_tv_switch(a, b, p, st):
    """تلفزيون: الأول ينطفئ والثاني يشتغل."""
    if p < 0.5:
        return _tv(a, ease(p * 2))
    return _tv(b, 1 - ease((p - 0.5) * 2))


def t_blinds(a, b, p, st):
    """ستائر تدور (Venetian)."""
    h, w = a.shape[:2]
    n = 10
    out = np.zeros_like(a)
    sh = h / n
    for i in range(n):
        y0, y1 = int(i * sh), int((i + 1) * sh)
        k = np.clip((p - i * 0.03) / 0.7, 0, 1)
        k = ease(k)
        src = a if k < 0.5 else b
        s = abs(math.cos(math.pi * k))
        hh = max(1, int((y1 - y0) * s))
        strip = cv2.resize(src[y0:y1], (w, hh))
        shade = 0.55 + 0.45 * s
        yc = (y0 + y1) // 2 - hh // 2
        out[yc:yc + hh] = (strip * shade).astype(np.uint8)
    return out


def t_mosaic_flip(a, b, p, st):
    """مربعات تنقلب واحداً واحداً."""
    h, w = a.shape[:2]
    n = 8
    tw, th = w // n, h // max(1, round(n * h / w))
    rows, cols = (h + th - 1) // th, (w + tw - 1) // tw
    if "order" not in st:
        r = np.random.default_rng(4)
        st["order"] = r.random((rows, cols)) * 0.5 + (np.arange(cols)[None, :] / cols) * 0.3
    out = np.zeros_like(a)
    for ry in range(rows):
        for cx in range(cols):
            y0, x0 = ry * th, cx * tw
            y1, x1 = min(h, y0 + th), min(w, x0 + tw)
            k = np.clip((p - st["order"][ry, cx]) / 0.25, 0, 1)
            src = a if k < 0.5 else b
            s = abs(math.cos(math.pi * k))
            ww = max(1, int((x1 - x0) * s))
            tile = cv2.resize(src[y0:y1, x0:x1], (ww, y1 - y0))
            xs = x0 + ((x1 - x0) - ww) // 2
            out[y0:y1, xs:xs + ww] = (tile * (0.6 + 0.4 * s)).astype(np.uint8)
    return out


def t_swirl(a, b, p, st):
    h, w = a.shape[:2]
    gx, gy = _grid_maps(st, h, w)
    if "sr" not in st:
        dx, dy = gx - w / 2, gy - h / 2
        st["sr"] = np.sqrt(dx * dx + dy * dy)
        st["sd"] = (dx, dy)
    dx, dy = st["sd"]
    R = max(w, h) * 0.7
    ang = 4.0 * bell(p) * np.clip(1 - st["sr"] / R, 0, 1) ** 2
    c, s = np.cos(ang), np.sin(ang)
    mx = (w / 2 + dx * c - dy * s).astype(np.float32)
    my = (h / 2 + dx * s + dy * c).astype(np.float32)
    A = cv2.remap(a, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    B = cv2.remap(b, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return blend(A, B, ease((p - 0.35) / 0.3))


def t_rgb_wipe(a, b, p, st):
    """مسح بثلاث قنوات لونية متأخرة."""
    h, w = a.shape[:2]
    out = np.empty_like(a)
    for c, delay in ((0, 0.0), (1, 0.12), (2, 0.24)):
        k = ease(np.clip((p - delay) / 0.76, 0, 1))
        x = int(w * k)
        out[:, :x, c] = b[:, :x, c]
        out[:, x:, c] = a[:, x:, c]
    return out


def t_slit_scan(a, b, p, st):
    """كل سطر يتحول في لحظة مختلفة مع انزلاق."""
    h, w = a.shape[:2]
    out = np.empty_like(a)
    rows = np.arange(h)
    k = np.clip((p * 1.6 - rows / h * 0.6), 0, 1)
    k = 0.5 - 0.5 * np.cos(np.pi * k)
    shift = (np.sin(np.pi * k) * w * 0.15).astype(int)
    for y in range(h):
        src = a if k[y] < 0.5 else b
        out[y] = np.roll(src[y], shift[y], axis=0)
    return out


def t_glitch_slice(a, b, p, st):
    """شرائح أفقية تنزلق بالتناوب."""
    h, w = a.shape[:2]
    n = 14
    out = np.empty_like(a)
    sh = h / n
    for i in range(n):
        y0, y1 = int(i * sh), int((i + 1) * sh)
        k = ease(np.clip((p - (i % 3) * 0.06) / 0.8, 0, 1))
        d = 1 if i % 2 == 0 else -1
        off = int(d * w * k)
        A = np.roll(a[y0:y1], off, axis=1)
        B = np.roll(b[y0:y1], off - d * w, axis=1)
        x = abs(off)
        if d > 0:
            seg = np.concatenate([B[:, :x], A[:, x:]], 1)
        else:
            seg = np.concatenate([A[:, :w - x], B[:, w - x:]], 1)
        out[y0:y1] = seg
    return rgb_shift(out, w * 0.006 * bell(p))


def t_bubbles(a, b, p, st):
    """فقاعات تكبر وتكشف المقطع الثاني."""
    h, w = a.shape[:2]
    if "bub" not in st:
        r = np.random.default_rng(9)
        st["bub"] = [(r.uniform(0, w), r.uniform(0, h), r.uniform(0, 0.45), r.uniform(0.6, 1.4)) for _ in range(26)]
    m = np.zeros((h, w), np.uint8)
    for (x, y, d, s) in st["bub"]:
        k = np.clip((p - d) / 0.55, 0, 1)
        R = int(ease_out(k) * w * 0.35 * s)
        if R > 0:
            cv2.circle(m, (int(x), int(y)), R, 255, -1, cv2.LINE_AA)
    rim = cv2.GaussianBlur(cv2.Canny(m, 50, 150), (0, 0), 3).astype(np.float32)[..., None] / 255 * 2.5
    mf = m.astype(np.float32)[..., None] / 255
    out = a * (1 - mf) + b * mf + np.clip(rim, 0, 1) * 200 * (1 - p)
    return np.clip(out, 0, 255).astype(np.uint8)


def t_doors(a, b, p, st):
    """باب ينفتح: نصفا المقطع الأول ينزلقان للجانبين."""
    h, w = a.shape[:2]
    e = ease(p)
    out = warp(b, 1.15 - 0.15 * e)
    half = w // 2
    off = int(half * e)
    L, R = a[:, :half], a[:, half:]
    if half - off > 0:
        out[:, :half - off] = (L[:, off:] * (1 - 0.3 * e)).astype(np.uint8)
        out[:, half + off:] = (R[:, :w - half - off] * (1 - 0.3 * e)).astype(np.uint8)
    return out


def t_diagonal(a, b, p, st):
    """قص قطري: المقطع الأول ينشق لمثلثين يطيران بعيداً."""
    h, w = a.shape[:2]
    e = ease(p) ** 1.3
    off = e * math.hypot(w, h) * 0.75
    ux, uy = h / math.hypot(w, h), w / math.hypot(w, h)  # عمودي على القطر
    out = warp(b, 1.12 - 0.12 * e).copy()
    tri_up = np.array([[0, 0], [w, 0], [0, h]], np.int32)
    tri_dn = np.array([[w, 0], [w, h], [0, h]], np.int32)
    for tri, sgn in ((tri_up, -1), (tri_dn, 1)):
        m = np.zeros((h, w), np.uint8)
        cv2.fillPoly(m, [tri], 255)
        M = np.float32([[1, 0, sgn * ux * off], [0, 1, sgn * uy * off]])
        moved = cv2.warpAffine(a, M, (w, h), borderMode=cv2.BORDER_CONSTANT)
        mm = cv2.warpAffine(m, M, (w, h), borderMode=cv2.BORDER_CONSTANT) > 128
        out[mm] = moved[mm]
    return out


def t_warp_tunnel(a, b, p, st):
    """نفق: الصورة تُسحب لنقطة في المركز."""
    h, w = a.shape[:2]
    gx, gy = _grid_maps(st, h, w)
    if "tr" not in st:
        dx, dy = gx - w / 2, gy - h / 2
        st["tr"] = np.sqrt(dx * dx + dy * dy) / (w / 2) + 1e-4
        st["td"] = (dx, dy)
    dx, dy = st["td"]
    k = bell(p) ** 1.3 * 3
    f = st["tr"] ** k
    src = a if p < 0.5 else b
    mx = (w / 2 + dx * (f / st["tr"])).astype(np.float32)
    my = (h / 2 + dy * (f / st["tr"])).astype(np.float32)
    out = cv2.remap(src, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return zoom_blur(out, 0.2 * bell(p))


def t_smear(a, b, p, st):
    """لطخة سرعة أفقية مع تمدد."""
    h, w = a.shape[:2]
    k = bell(p)
    src = a if p < 0.5 else b
    sx = 1 + 1.5 * k
    s = cv2.resize(src, (int(w * sx), h))
    x0 = int((s.shape[1] - w) * (0.5 + (0.5 if p < 0.5 else -0.5) * k))
    out = s[:, x0:x0 + w]
    return motion_blur(out, 2 + 90 * k, 0)


def t_kaleido(a, b, p, st):
    h, w = a.shape[:2]
    gx, gy = _grid_maps(st, h, w)
    if "kr" not in st:
        dx, dy = gx - w / 2, gy - h / 2
        st["kr"] = np.sqrt(dx * dx + dy * dy)
        st["ka"] = np.arctan2(dy, dx)
    k = bell(p)
    seg = 2 * math.pi / 6
    ang = (st["ka"] + p * 3) % seg
    ang = np.where(ang > seg / 2, seg - ang, ang)
    mx = (w / 2 + st["kr"] * np.cos(ang)).astype(np.float32)
    my = (h / 2 + st["kr"] * np.sin(ang)).astype(np.float32)
    src = blend(a, b, ease((p - 0.3) / 0.4))
    kal = cv2.remap(src, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return blend(src, kal, min(1, k * 1.6))


def t_flare_cut(a, b, p, st):
    """وهج عدسة يعبر الشاشة ويخفي القطع."""
    h, w = a.shape[:2]
    gx, gy = _grid_maps(st, h, w)
    cx = -0.2 + 1.4 * p
    dx, dy = (gx / w - cx) * 1.78, gy / h - 0.45
    core = np.exp(-(dx ** 2 + dy ** 2) / 0.02)
    streak = np.exp(-(dy ** 2) / 0.0006) * np.exp(-np.abs(dx) / 0.8)
    k = bell(p)
    fl = (core[..., None] * np.array([255, 235, 200]) + streak[..., None] * np.array([120, 180, 255])) * (0.5 + 1.2 * k)
    base = a if p < 0.5 else b
    out = screen(base, np.clip(fl, 0, 255).astype(np.uint8))
    return blend(out, np.full_like(a, 255), max(0, k - 0.75) * 3)


def t_pixel_sort(a, b, p, st):
    h, w = a.shape[:2]
    src = a if p < 0.5 else b
    k = bell(p)
    sm = cv2.resize(src, (w // 3, h // 3))
    lum = cv2.cvtColor(sm, cv2.COLOR_RGB2GRAY)
    thr = int(255 * (1 - k * 0.8))
    out = sm.copy()
    for y in range(sm.shape[0]):
        idx = np.where(lum[y] > thr)[0]
        if len(idx) > 3:
            out[y, idx] = sm[y, idx][np.argsort(lum[y, idx])]
    return cv2.resize(out, (w, h))


def t_iris(a, b, p, st):
    """قزحية: دائرة تنغلق على الأول ثم تنفتح على الثاني."""
    h, w = a.shape[:2]
    R = math.hypot(w, h) / 2
    if p < 0.5:
        r = int(R * (1 - ease(p * 2)))
        src = a
    else:
        r = int(R * ease((p - 0.5) * 2))
        src = b
    m = np.zeros((h, w), np.uint8)
    cv2.circle(m, (w // 2, h // 2), max(0, r), 255, -1, cv2.LINE_AA)
    return (src * (m[..., None].astype(np.float32) / 255)).astype(np.uint8)


TRANS3 = {
    "ink":          (t_ink,          "حبر ينتشر"),
    "burn":         (t_burn,         "حرق بحافة نار"),
    "tv-switch":    (t_tv_switch,    "تبديل تلفزيون قديم"),
    "blinds":       (t_blinds,       "ستائر تدور"),
    "mosaic-flip":  (t_mosaic_flip,  "مربعات تنقلب"),
    "swirl":        (t_swirl,        "دوامة"),
    "rgb-wipe":     (t_rgb_wipe,     "مسح بالألوان الثلاثة"),
    "slit-scan":    (t_slit_scan,    "سلِت سكان"),
    "glitch-slice": (t_glitch_slice, "شرائح غلتش"),
    "bubbles":      (t_bubbles,      "فقاعات تكشف"),
    "doors":        (t_doors,        "باب ينفتح"),
    "diagonal":     (t_diagonal,     "انشقاق قطري"),
    "warp-tunnel":  (t_warp_tunnel,  "نفق"),
    "smear":        (t_smear,        "لطخة سرعة"),
    "kaleido":      (t_kaleido,      "مشكال"),
    "flare-cut":    (t_flare_cut,    "وهج عدسة يخفي القطع"),
    "pixel-sort":   (t_pixel_sort,   "فرز بكسلات"),
    "iris":         (t_iris,         "قزحية (ستايل الأفلام القديمة)"),
}
