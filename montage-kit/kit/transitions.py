"""
انتقالات مخصصة بين مقطعين (2026).
كل انتقال: f(a, b, p, st) -> إطار.  a: آخر المقطع الأول، b: أول المقطع الثاني، p من 0 إلى 1.
"""
import math
import numpy as np
import cv2

from .effects import ease, ease_out, bell, warp, blend, screen, rgb_shift, zoom_blur, motion_blur, fx_glitch
from .effects2 import perspective, paste_card, _grid_maps


def _cut(a, b, p, fa, fb):
    return fa(a, p) if p < 0.5 else fb(b, p)


def t_zoom_blur(a, b, p, st):
    if p < 0.5:
        k = ease(p * 2) ** 2
        return zoom_blur(warp(a, 1 + 1.6 * k), 0.35 * k)
    k = (1 - ease((p - 0.5) * 2)) ** 2
    return zoom_blur(warp(b, 1 + 1.6 * k), 0.35 * k)


def t_zoom_out(a, b, p, st):
    if p < 0.5:
        k = ease(p * 2) ** 2
        return zoom_blur(warp(a, 1 / (1 + 1.2 * k)), 0.25 * k)
    k = (1 - ease((p - 0.5) * 2)) ** 2
    return zoom_blur(warp(b, 1 / (1 + 1.2 * k)), 0.25 * k)


def t_spin(a, b, p, st):
    e = ease(p)
    ang = 360 * e
    src = a if p < 0.5 else b
    z = 1 + 0.6 * bell(p)
    return zoom_blur(warp(src, z, 0.5, 0.5, 0, 0, ang), 0.18 * bell(p))


def _whip(a, b, p, dx, dy):
    h, w = a.shape[:2]
    e = ease(p)
    off = e * (w if dx else h)
    blur = bell(p) ** 1.2 * w * 0.18
    ang = 0 if dx else 90
    A = warp(a, 1, 0.5, 0.5, -dx * off, -dy * off)
    B = warp(b, 1, 0.5, 0.5, dx * ((w if dx else 0) - off), dy * ((h if dy else 0) - off))
    out = A if p < 0.5 else B
    return motion_blur(out, 2 + blur, ang)


def t_whip_left(a, b, p, st):
    return _whip(a, b, p, 1, 0)


def t_whip_right(a, b, p, st):
    return _whip(a, b, p, -1, 0)


def t_whip_up(a, b, p, st):
    return _whip(a, b, p, 0, 1)


def t_whip_down(a, b, p, st):
    return _whip(a, b, p, 0, -1)


def t_glitch(a, b, p, st):
    src = a if p < 0.5 else b
    prm = {"amount": 1.6 * bell(p) + 0.2, "seed": 7, "_d": 1.0}
    out = fx_glitch(src.copy(), 0.5, p, prm, {})
    if 0.42 < p < 0.58:
        out = blend(out, a if p >= 0.5 else b, 0.35)
    return out


def t_rgb_split(a, b, p, st):
    src = a if p < 0.5 else b
    k = bell(p) ** 2
    return rgb_shift(warp(src, 1 + 0.15 * k), src.shape[1] * 0.04 * k)


def t_flash_burn(a, b, p, st):
    src = a if p < 0.5 else b
    k = bell(p) ** 1.5
    warm = np.empty_like(src)
    warm[:] = (255, 214, 150)
    out = screen(src, (warm * k).astype(np.uint8))
    return blend(out, np.full_like(src, 255), max(0, k - 0.6) * 2)


def t_light_leak(a, b, p, st):
    h, w = a.shape[:2]
    gx, gy = _grid_maps(st, h, w)
    if "leak" not in st:
        d1 = ((gx / w - 0.15) * 1.3) ** 2 + (gy / h - 0.3) ** 2
        d2 = ((gx / w - 0.85) * 1.3) ** 2 + (gy / h - 0.75) ** 2
        st["leak"] = np.clip(np.exp(-d1 / 0.08)[..., None] * [1.0, 0.45, 0.15] +
                             np.exp(-d2 / 0.12)[..., None] * [1.0, 0.75, 0.3], 0, 1).astype(np.float32)
    k = bell(p)
    base = blend(a, b, ease((p - 0.3) / 0.4))
    leak = (st["leak"] * 255 * min(1, k * 1.6)).astype(np.uint8)
    leak = np.roll(leak, int((p - 0.5) * w * 0.3), 1)
    return screen(base, leak)


def _shape_reveal(a, b, p, st, shape):
    h, w = a.shape[:2]
    e = ease_out(p) if shape != "circle" else ease(p)
    m = np.zeros((h, w), np.uint8)
    cx, cy = w / 2, h / 2
    R = math.hypot(w, h) * 0.75 * e
    if shape == "circle":
        cv2.circle(m, (int(cx), int(cy)), int(R), 255, -1, cv2.LINE_AA)
    elif shape == "heart":
        t = np.linspace(0, 2 * math.pi, 120)
        x = 16 * np.sin(t) ** 3
        y = -(13 * np.cos(t) - 5 * np.cos(2 * t) - 2 * np.cos(3 * t) - np.cos(4 * t))
        s = R / 12
        pts = np.stack([cx + x * s, cy + y * s + 2 * s], 1).astype(np.int32)
        cv2.fillPoly(m, [pts], 255, cv2.LINE_AA)
    elif shape == "star":
        pts = []
        for i in range(10):
            r = R * (1.3 if i % 2 == 0 else 0.6)
            ang = math.radians(-90 + i * 36 + p * 90)
            pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
        cv2.fillPoly(m, [np.array(pts, np.int32)], 255, cv2.LINE_AA)
    elif shape == "diamond":
        r = R * 1.2
        cv2.fillPoly(m, [np.array([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], np.int32)], 255, cv2.LINE_AA)
    mf = m.astype(np.float32)[..., None] / 255
    edge = cv2.GaussianBlur(cv2.Canny(m, 50, 150), (0, 0), 6).astype(np.float32)[..., None] / 255 * 3
    out = a * (1 - mf) + b * mf
    out = out + np.clip(edge, 0, 1) * 255 * (1 - p)
    return np.clip(out, 0, 255).astype(np.uint8)


def t_circle(a, b, p, st):
    return _shape_reveal(a, b, p, st, "circle")


def t_heart(a, b, p, st):
    return _shape_reveal(a, b, p, st, "heart")


def t_star(a, b, p, st):
    return _shape_reveal(a, b, p, st, "star")


def t_diamond(a, b, p, st):
    return _shape_reveal(a, b, p, st, "diamond")


def t_split_panels(a, b, p, st):
    h, w = a.shape[:2]
    n = 4
    out = a.copy()
    pw = w // n
    for i in range(n):
        k = ease_out(np.clip((p - i * 0.1) / 0.6, 0, 1))
        y = int(h * (1 - k)) * (1 if i % 2 == 0 else -1)
        x0, x1 = i * pw, (i + 1) * pw if i < n - 1 else w
        strip = b[:, x0:x1]
        if k <= 0:
            continue
        if y >= 0:
            out[y:, x0:x1] = strip[: h - y]
        else:
            out[: h + y, x0:x1] = strip[-y:]
    return out


def t_stretch(a, b, p, st):
    h, w = a.shape[:2]
    if p < 0.5:
        k = ease(p * 2)
        s = cv2.resize(a, (int(w * (1 + 3 * k)), h))
        x0 = (s.shape[1] - w) // 2
        out = s[:, x0:x0 + w]
        return blend(motion_blur(out, 2 + 60 * k), np.full_like(a, 255), k ** 3 * 0.6)
    k = 1 - ease((p - 0.5) * 2)
    s = cv2.resize(b, (int(w * (1 + 3 * k)), h))
    x0 = (s.shape[1] - w) // 2
    out = s[:, x0:x0 + w]
    return blend(motion_blur(out, 2 + 60 * k), np.full_like(a, 255), k ** 3 * 0.6)


def t_ripple(a, b, p, st):
    h, w = a.shape[:2]
    gx, gy = _grid_maps(st, h, w)
    if "rr" not in st:
        dx, dy = gx - w / 2, gy - h / 2
        st["rr"] = np.sqrt(dx * dx + dy * dy) + 1e-3
        st["ux"], st["uy"] = dx / st["rr"], dy / st["rr"]
    amp = bell(p) * w * 0.02
    wave = np.sin(st["rr"] / (w * 0.025) - p * 25) * amp
    mx = (gx + st["ux"] * wave).astype(np.float32)
    my = (gy + st["uy"] * wave).astype(np.float32)
    A = cv2.remap(a, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    B = cv2.remap(b, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return blend(A, B, ease(p))


def t_cube(a, b, p, st):
    """مكعب ثلاثي الأبعاد يدور: الوجه الأول يذهب يساراً والثاني يأتي من اليمين."""
    h, w = a.shape[:2]
    th = math.radians(90 * ease(p))
    f = w * 1.6
    dz = w * 0.35 * bell(p)
    hw, hh = w / 2, h / 2

    def proj(pts):
        out = []
        for x, y, z in pts:
            xr = x * math.cos(th) + z * math.sin(th)
            zr = -x * math.sin(th) + z * math.cos(th)
            depth = zr + hw + dz
            out.append((f * xr / (f + depth) + hw, f * y / (f + depth) + hh, depth))
        return out

    faces = [
        (a, [(-hw, -hh, -hw), (hw, -hh, -hw), (hw, hh, -hw), (-hw, hh, -hw)]),
        (b, [(hw, -hh, -hw), (hw, -hh, hw), (hw, hh, hw), (hw, hh, -hw)]),
    ]
    out = np.full_like(a, 12).astype(np.float32)
    src = np.array([[0, 0], [w, 0], [w, h], [0, h]], np.float32)
    drawn = []
    for img, pts in faces:
        pr = proj(pts)
        (x0, y0, _), (x1, y1, _), (x2, y2, _) = pr[0], pr[1], pr[2]
        if (x1 - x0) * (y2 - y1) - (y1 - y0) * (x2 - x1) <= 1:  # الوجه لا يقابل الكاميرا
            continue
        drawn.append((sum(q[2] for q in pr), img, pr))
    for _, img, pr in sorted(drawn, key=lambda d: -d[0]):
        dst = np.array([(q[0], q[1]) for q in pr], np.float32)
        M = cv2.getPerspectiveTransform(src, dst)
        fr = cv2.warpPerspective(img, M, (w, h)).astype(np.float32)
        m = cv2.warpPerspective(np.full((h, w), 255, np.uint8), M, (w, h)).astype(np.float32)[..., None] / 255
        width = abs(dst[1, 0] - dst[0, 0]) / w
        shade = 0.45 + 0.55 * min(1, width)
        out = out * (1 - m) + fr * shade * m
    return out.astype(np.uint8)


def t_flip(a, b, p, st):
    h, w = a.shape[:2]
    full = np.full((h, w), 255, np.uint8)
    if p < 0.5:
        ang, img = 90 * ease(p * 2), a
    else:
        ang, img = -90 * (1 - ease((p - 0.5) * 2)), b
    if abs(ang) > 89:
        return np.zeros_like(a)
    fr = perspective(img, ang, 0, 1 - 0.15 * bell(p))
    m = perspective(full, ang, 0, 1 - 0.15 * bell(p)).astype(np.float32)[..., None] / 255
    return (fr * m).astype(np.uint8)


def t_push(a, b, p, st):
    h, w = a.shape[:2]
    e = ease(p)
    A = warp(a, 1, 0.5, 0.5, -w * e * 0.35, 0)
    A = (A * (1 - 0.5 * e)).astype(np.uint8)
    x = int(w * (1 - e))
    out = A.copy()
    if x < w:
        out[:, x:] = b[:, : w - x]
        sh = max(1, int(w * 0.03))
        x0 = max(0, x - sh)
        grad = np.linspace(1, 0.55, x - x0)[None, :, None] if x > x0 else None
        if grad is not None:
            out[:, x0:x] = (out[:, x0:x] * grad).astype(np.uint8)
    return out


def t_pixel(a, b, p, st):
    h, w = a.shape[:2]
    src = a if p < 0.5 else b
    k = bell(p)
    bs = max(1, int(1 + k * w / 18))
    if bs <= 1:
        return src
    small = cv2.resize(src, (max(1, w // bs), max(1, h // bs)), interpolation=cv2.INTER_AREA)
    return cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)


def t_shake_cut(a, b, p, st):
    src = a if p < 0.5 else b
    r = np.random.default_rng(int(p * 1000))
    k = bell(p)
    h, w = src.shape[:2]
    out = warp(src, 1 + 0.08 * k, 0.5, 0.5, r.normal(0, w * 0.02 * k), r.normal(0, h * 0.02 * k), r.normal(0, 2 * k))
    return blend(out, np.full_like(src, 255), max(0, k - 0.75) * 3)


def t_blur_dissolve(a, b, p, st):
    k = bell(p)
    s = k * a.shape[1] / 60
    out = blend(a, b, ease(p))
    return cv2.GaussianBlur(out, (0, 0), s) if s > 0.3 else out


def t_luma(a, b, p, st):
    g = cv2.cvtColor(b, cv2.COLOR_RGB2GRAY).astype(np.float32) / 255
    thr = p * 1.2 - 0.1
    m = np.clip((thr - g) / 0.1 + 0.5, 0, 1)[..., None]
    return (a * (1 - m) + b * m).astype(np.uint8)


def t_shatter(a, b, p, st):
    h, w = a.shape[:2]
    if "tiles" not in st:
        r = np.random.default_rng(5)
        n = 8
        tiles = []
        tw, th = w // n, h // (n * h // w + 1 if w > h else n)
        th = max(1, th)
        for y in range(0, h, th):
            for x in range(0, w, tw):
                cxv, cyv = x + tw / 2 - w / 2, y + th / 2 - h / 2
                tiles.append(dict(x=x, y=y, tw=min(tw, w - x), th=min(th, h - y),
                                  vx=cxv * r.uniform(0.5, 1.5) / w * 2, vy=r.uniform(-0.5, 0.3),
                                  rot=r.uniform(-360, 360), delay=r.uniform(0, 0.35) * (1 - math.hypot(cxv, cyv) / w)))
        st["tiles"] = tiles
    out = b.copy()
    for t in st["tiles"]:
        k = max(0.0, (p - t["delay"]) / (1 - t["delay"]))
        tile = a[t["y"]:t["y"] + t["th"], t["x"]:t["x"] + t["tw"]]
        if k <= 0:
            out[t["y"]:t["y"] + t["th"], t["x"]:t["x"] + t["tw"]] = tile
            continue
        kk = ease(k)
        cx = t["x"] + t["tw"] / 2 + t["vx"] * w * 0.5 * kk
        cy = t["y"] + t["th"] / 2 + (t["vy"] * kk + 1.8 * kk * kk) * h
        sc = 1 - 0.5 * kk
        if cy - t["th"] > h or sc <= 0.05:
            continue
        M = cv2.getRotationMatrix2D((t["tw"] / 2, t["th"] / 2), t["rot"] * kk, sc)
        M[0, 2] += cx - t["tw"] / 2
        M[1, 2] += cy - t["th"] / 2
        tw_ = cv2.warpAffine(tile, M, (w, h))
        tm = cv2.warpAffine(np.full(tile.shape[:2], 255, np.uint8), M, (w, h))
        out[tm > 128] = tw_[tm > 128]
    return out


def t_card_swap(a, b, p, st):
    """المقطع الأول يصغر لبطاقة ويطير، والثاني يكبر من بطاقة."""
    h, w = a.shape[:2]
    bg = np.full_like(a, 18)
    if p < 0.5:
        e = ease(p * 2)
        return paste_card(bg, a, w / 2 - w * 0.6 * max(0, e - 0.5) * 2, h / 2, -8 * e, 1 - 0.3 * e, radius=w * 0.03 * e)
    e = 1 - ease((p - 0.5) * 2)
    return paste_card(bg, b, w / 2 + w * 0.6 * max(0, e - 0.5) * 2, h / 2, 8 * e, 1 - 0.3 * e, radius=w * 0.03 * e)


def t_bounce_slide(a, b, p, st):
    h, w = a.shape[:2]
    # ease-out-back مع تجاوز بسيط
    c1 = 1.7
    e = 1 + (c1 + 1) * (p - 1) ** 3 + c1 * (p - 1) ** 2
    x = int(w * (1 - e))
    out = (a * (1 - 0.4 * min(1, p * 1.5))).astype(np.uint8)
    if x < w:
        if x >= 0:
            out[:, x:] = b[:, : w - x]
        else:
            out[:, :] = np.concatenate([b[:, -x:], b[:, :(-x)][:, ::-1]], 1)[:, :w]
    return out


# ---- أساسيات (حتى تُخلط مع المخصصة) ----

def t_fade(a, b, p, st):
    return blend(a, b, ease(p))


def t_fadeblack(a, b, p, st):
    z = np.zeros_like(a)
    return blend(a, z, ease(p * 2)) if p < 0.5 else blend(z, b, ease((p - 0.5) * 2))


def t_fadewhite(a, b, p, st):
    z = np.full_like(a, 255)
    return blend(a, z, ease(p * 2)) if p < 0.5 else blend(z, b, ease((p - 0.5) * 2))


def _slide(a, b, p, dx, dy):
    h, w = a.shape[:2]
    e = ease(p)
    A = warp(a, 1, 0.5, 0.5, -dx * w * e, -dy * h * e)
    B = warp(b, 1, 0.5, 0.5, dx * w * (1 - e), dy * h * (1 - e))
    if dx:
        x = int(w * (1 - e)) if dx > 0 else int(w * e)
        return np.concatenate([A[:, :x], B[:, x:]], 1) if dx > 0 else np.concatenate([B[:, :x], A[:, x:]], 1)
    y = int(h * (1 - e)) if dy > 0 else int(h * e)
    return np.concatenate([A[:y], B[y:]], 0) if dy > 0 else np.concatenate([B[:y], A[y:]], 0)


TRANS = {
    "zoom-blur":    (t_zoom_blur,    "زوم عبور مع تمويه (الأشهر)"),
    "zoom-out":     (t_zoom_out,     "زوم للخارج"),
    "spin":         (t_spin,         "لفّة مع تمويه"),
    "whip-left":    (t_whip_left,    "سحبة سريعة لليسار"),
    "whip-right":   (t_whip_right,   "سحبة سريعة لليمين"),
    "whip-up":      (t_whip_up,      "سحبة سريعة للأعلى"),
    "whip-down":    (t_whip_down,    "سحبة سريعة للأسفل"),
    "glitch":       (t_glitch,       "غلتش"),
    "rgb-split":    (t_rgb_split,    "انفصال ألوان"),
    "flash-burn":   (t_flash_burn,   "فلاش دافئ"),
    "light-leak":   (t_light_leak,   "تسريب ضوء"),
    "circle":       (t_circle,       "دائرة تكشف"),
    "heart":        (t_heart,        "قلب يكشف"),
    "star":         (t_star,         "نجمة تكشف"),
    "diamond":      (t_diamond,      "معيّن يكشف"),
    "split-panels": (t_split_panels, "شرائح تدخل متتابعة"),
    "stretch":      (t_stretch,      "مطّ"),
    "ripple":       (t_ripple,       "تموّج ماء"),
    "cube":         (t_cube,         "مكعب 3D"),
    "flip":         (t_flip,         "قلب بطاقة 3D"),
    "push":         (t_push,         "دفع مع ظل"),
    "pixel":        (t_pixel,        "بكسلة"),
    "shake-cut":    (t_shake_cut,    "اهتزاز وقطع"),
    "blur-dissolve": (t_blur_dissolve, "ذوبان مع تمويه"),
    "luma":         (t_luma,         "ظهور حسب الإضاءة"),
    "shatter":      (t_shatter,      "تحطّم زجاج"),
    "card-swap":    (t_card_swap,    "تبديل بطاقات"),
    "bounce-slide": (t_bounce_slide, "انزلاق مع ارتداد"),
    # أساسيات
    "fade":         (t_fade,         "تلاشي"),
    "fadeblack":    (t_fadeblack,    "تلاشي للأسود"),
    "fadewhite":    (t_fadewhite,    "تلاشي للأبيض"),
    "slideleft":    (lambda a, b, p, st: _slide(a, b, p, 1, 0), "انزلاق لليسار"),
    "slideright":   (lambda a, b, p, st: _slide(a, b, p, -1, 0), "انزلاق لليمين"),
    "slideup":      (lambda a, b, p, st: _slide(a, b, p, 0, 1), "انزلاق للأعلى"),
    "slidedown":    (lambda a, b, p, st: _slide(a, b, p, 0, -1), "انزلاق للأسفل"),
}
BASIC = {"fade", "fadeblack", "fadewhite", "slideleft", "slideright", "slideup", "slidedown"}
