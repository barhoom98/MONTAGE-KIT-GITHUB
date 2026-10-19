"""
حركات ومؤثرات جديدة 2026.
مؤثرات الزمن (WINDOW) تعيد ترتيب إطارات الفترة نفسها: ترجيع، بومرانغ، تسريع وتبطيء، تكرار.
"""
import math
import numpy as np
import cv2

from .effects import (ease, ease_out, bell, edge_env, warp, blend, screen, hex_rgb, rgb_shift, zoom_blur,
                      motion_blur, noise1d, TAU)

C = {"x": 0.5, "y": 0.5}


def _grid_maps(st, h, w):
    if "gx" not in st:
        y, x = np.mgrid[0:h, 0:w].astype(np.float32)
        st["gx"], st["gy"] = x, y
    return st["gx"], st["gy"]


def perspective(img, ry=0.0, rx=0.0, z=1.0, f_scale=1.4):
    """تدوير ثلاثي الأبعاد للصورة حول المحورين."""
    h, w = img.shape[:2]
    f = w * f_scale
    pts = np.array([[-w / 2, -h / 2, 0], [w / 2, -h / 2, 0], [w / 2, h / 2, 0], [-w / 2, h / 2, 0]], np.float32)
    a, b = math.radians(ry), math.radians(rx)
    Ry = np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]])
    Rx = np.array([[1, 0, 0], [0, math.cos(b), -math.sin(b)], [0, math.sin(b), math.cos(b)]])
    p = pts @ Ry.T @ Rx.T
    p[:, :2] *= z
    dst = np.stack([f * p[:, 0] / (f + p[:, 2]) + w / 2, f * p[:, 1] / (f + p[:, 2]) + h / 2], 1).astype(np.float32)
    src = np.array([[0, 0], [w, 0], [w, h], [0, h]], np.float32)
    M = cv2.getPerspectiveTransform(src, dst)
    return cv2.warpPerspective(img, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)


def fast_blur(img, sigma):
    """تمويه قوي سريع: تصغير ثم تمويه ثم تكبير."""
    h, w = img.shape[:2]
    k = 4 if sigma > 8 else 1
    if k == 1:
        return cv2.GaussianBlur(img, (0, 0), sigma)
    small = cv2.resize(img, (w // k, h // k), interpolation=cv2.INTER_AREA)
    return cv2.resize(cv2.GaussianBlur(small, (0, 0), sigma / k), (w, h), interpolation=cv2.INTER_LINEAR)


def rounded_mask(h, w, r):
    m = np.zeros((h, w), np.uint8)
    cv2.rectangle(m, (r, 0), (w - r, h), 255, -1)
    cv2.rectangle(m, (0, r), (w, h - r), 255, -1)
    for cx, cy in ((r, r), (w - r, r), (r, h - r), (w - r, h - r)):
        cv2.circle(m, (cx, cy), r, 255, -1, cv2.LINE_AA)
    return m


def paste_card(bg, card, cx, cy, angle=0.0, scale=1.0, radius=0.0, shadow=True, border=0, border_col=(255, 255, 255)):
    """لصق صورة كبطاقة (زوايا دائرية، إطار، ظل، دوران) فوق خلفية."""
    H, W = bg.shape[:2]
    ch, cw = card.shape[:2]
    if border:
        card = cv2.copyMakeBorder(card, border, int(border * 3.2), border, border, cv2.BORDER_CONSTANT, value=border_col)
        ch, cw = card.shape[:2]
    mask = rounded_mask(ch, cw, int(radius)) if radius else np.full((ch, cw), 255, np.uint8)
    M = cv2.getRotationMatrix2D((cw / 2, ch / 2), angle, scale)
    M[0, 2] += cx - cw / 2
    M[1, 2] += cy - ch / 2
    wc = cv2.warpAffine(card, M, (W, H), flags=cv2.INTER_LINEAR)
    wm = cv2.warpAffine(mask, M, (W, H), flags=cv2.INTER_LINEAR).astype(np.float32)[..., None] / 255
    out = bg.astype(np.float32)
    if shadow:
        sm = fast_blur(wm, W / 60)
        sm = np.roll(sm, (int(H * 0.015), int(W * 0.01)), (0, 1))
        if sm.ndim == 2:
            sm = sm[..., None]
        out = out * (1 - 0.55 * sm)
    out = out * (1 - wm) + wc.astype(np.float32) * wm
    return out.astype(np.uint8)


# =================== حركات ثلاثية الأبعاد ===================

def fx_perspective_tilt(img, lt, p, prm, st):
    e = edge_env(lt, prm["_d"], 0.3, 0.3)
    ry = prm["angle"] * math.sin(lt * prm["speed"]) * e
    rx = prm["angle"] * 0.5 * math.cos(lt * prm["speed"] * 0.8) * e
    bg = fast_blur(img, img.shape[1] / 60)
    fr = perspective(img, ry, rx, 1 - 0.12 * e)
    m = perspective(np.full(img.shape[:2], 255, np.uint8), ry, rx, 1 - 0.12 * e).astype(np.float32)[..., None] / 255
    return (bg * (1 - m) + fr * m).astype(np.uint8)


def fx_flip_3d(img, lt, p, prm, st):
    ang = 360 * ease(p) * (1 if prm["dir"] >= 0 else -1)
    src = img if (abs(ang) % 360) < 90 or (abs(ang) % 360) > 270 else img[:, ::-1]
    z = 1 - 0.25 * bell(p)
    fr = perspective(src, ang if not prm["vertical"] else 0, ang if prm["vertical"] else 0, z)
    bg = (fast_blur(img, img.shape[1] / 40) * 0.5).astype(np.uint8)
    m = perspective(np.full(img.shape[:2], 255, np.uint8), ang if not prm["vertical"] else 0,
                    ang if prm["vertical"] else 0, z).astype(np.float32)[..., None] / 255
    return (bg * (1 - m) + fr * m).astype(np.uint8)


def fx_frame_in(img, lt, p, prm, st):
    """الفيديو يصغر لبطاقة بزوايا دائرية فوق خلفية ضبابية."""
    h, w = img.shape[:2]
    e = ease(min(lt / 0.4, (prm["_d"] - lt) / 0.4, 1))
    s = 1 - (1 - prm["scale"]) * e
    if e < 0.01:
        return img
    bg = fast_blur(img, w / 35)
    bg = (bg * (1 - 0.35 * e)).astype(np.uint8)
    return paste_card(bg, img, w / 2, h / 2, prm["angle"] * e, s, radius=w * 0.03 * e, shadow=True)


def fx_photo_snap(img, lt, p, prm, st):
    """لقطة كاميرا: تجميد + فلاش + صورة بولارويد مائلة."""
    h, w = img.shape[:2]
    if "f" not in st:
        st["f"] = img.copy()
        st["bg"] = (fast_blur(img, w / 30) * 0.55).astype(np.uint8)
    e = ease_out(lt / 0.35)
    s = 1 - (1 - prm["scale"]) * e
    bw = int(w * 0.018 * e)
    out = paste_card(st["bg"], st["f"], w / 2, h / 2, prm["angle"] * e, s * (1 - 0.06 * e), shadow=e > 0.05,
                     border=bw)
    if lt < 0.18:
        out = blend(out, np.full_like(out, 255), 1 - lt / 0.18)
    return out


# =================== شاشات مقسومة ===================

def fx_grid(img, lt, p, prm, st):
    h, w = img.shape[:2]
    n = int(prm["n"])
    small = cv2.resize(img, (w // n, h // n), interpolation=cv2.INTER_AREA)
    out = np.tile(small, (n, n, 1))
    return cv2.resize(out, (w, h)) if out.shape[:2] != (h, w) else out


def fx_split_3(img, lt, p, prm, st):
    h, w = img.shape[:2]
    if w >= h:
        sw = w // 3
        c = img[:, w // 2 - sw // 2: w // 2 - sw // 2 + sw]
        out = np.concatenate([c, c, c], 1)
    else:
        sh = h // 3
        c = img[h // 2 - sh // 2: h // 2 - sh // 2 + sh]
        out = np.concatenate([c, c, c], 0)
    return cv2.resize(out, (w, h))


def fx_mirror_quad(img, lt, p, prm, st):
    h, w = img.shape[:2]
    q = cv2.resize(img, (w // 2, h // 2))
    top = np.concatenate([q, q[:, ::-1]], 1)
    out = np.concatenate([top, top[::-1]], 0)
    return cv2.resize(out, (w, h))


def fx_kaleidoscope(img, lt, p, prm, st):
    h, w = img.shape[:2]
    gx, gy = _grid_maps(st, h, w)
    if "r" not in st:
        dx, dy = gx - w / 2, gy - h / 2
        st["r"] = np.sqrt(dx * dx + dy * dy)
        st["a"] = np.arctan2(dy, dx)
    seg = TAU / int(prm["segments"])
    a = (st["a"] + lt * prm["spin"]) % seg
    a = np.where(a > seg / 2, seg - a, a)
    mx = (w / 2 + st["r"] * np.cos(a)).astype(np.float32)
    my = (h / 2 + st["r"] * np.sin(a)).astype(np.float32)
    k = cv2.remap(img, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return blend(img, k, edge_env(lt, prm["_d"], 0.25, 0.25))


# =================== تشويه وحركة ===================

def fx_chroma_zoom(img, lt, p, prm, st):
    beat = 60.0 / prm["bpm"]
    ph = (lt % beat) / beat
    k = math.exp(-ph * 8)
    out = warp(img, 1 + (prm["amount"] - 1) * k)
    return rgb_shift(out, img.shape[1] * 0.012 * k)


def fx_jello(img, lt, p, prm, st):
    h, w = img.shape[:2]
    gx, gy = _grid_maps(st, h, w)
    a = prm["amount"] * edge_env(lt, prm["_d"], 0.15, 0.15) * w * 0.02
    off = a * np.sin(gy / h * TAU * 1.5 + lt * 18) * np.sin(lt * 7)
    return cv2.remap(img, (gx + off).astype(np.float32), gy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def fx_ripple(img, lt, p, prm, st):
    h, w = img.shape[:2]
    gx, gy = _grid_maps(st, h, w)
    cx, cy = prm["x"] * w, prm["y"] * h
    dx, dy = gx - cx, gy - cy
    r = np.sqrt(dx * dx + dy * dy) + 1e-3
    front = lt * w * 0.9
    wave = np.sin((r - front) / (w * 0.02)) * np.exp(-((r - front) / (w * 0.12)) ** 2)
    amp = prm["amount"] * w * 0.012 * (1 - p)
    mx = gx + dx / r * wave * amp
    my = gy + dy / r * wave * amp
    return cv2.remap(img, mx.astype(np.float32), my.astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def fx_swirl(img, lt, p, prm, st):
    h, w = img.shape[:2]
    gx, gy = _grid_maps(st, h, w)
    cx, cy = prm["x"] * w, prm["y"] * h
    dx, dy = gx - cx, gy - cy
    r = np.sqrt(dx * dx + dy * dy)
    R = max(w, h) * 0.6
    ang = prm["amount"] * 3.0 * bell(p) * np.clip(1 - r / R, 0, 1) ** 2
    c, s = np.cos(ang), np.sin(ang)
    mx = cx + dx * c - dy * s
    my = cy + dx * s + dy * c
    return cv2.remap(img, mx.astype(np.float32), my.astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def fx_datamosh(img, lt, p, prm, st):
    """تلطيخ الحركة (داتاموش): الإطار السابق يُسحب مع حركة المشهد."""
    h, w = img.shape[:2]
    if "prev_out" not in st:
        st["prev_out"] = img.copy()
        st["prev_in"] = cv2.resize(cv2.cvtColor(img, cv2.COLOR_RGB2GRAY), (w // 8, h // 8))
        return img
    g = cv2.resize(cv2.cvtColor(img, cv2.COLOR_RGB2GRAY), (w // 8, h // 8))
    flow = cv2.calcOpticalFlowFarneback(st["prev_in"], g, None, 0.5, 2, 9, 2, 5, 1.1, 0)
    flow = cv2.resize(flow, (w, h)) * 8 * prm["amount"] * 1.5
    gx, gy = _grid_maps(st, h, w)
    moved = cv2.remap(st["prev_out"], (gx - flow[..., 0]).astype(np.float32), (gy - flow[..., 1]).astype(np.float32),
                      cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    env = edge_env(lt, prm["_d"], 0.05, 0.25)
    out = blend(img, moved, 0.92 * env)
    st["prev_out"], st["prev_in"] = out, g
    return out


def fx_stutter(img, lt, p, prm, st):
    """تقطيع الحركة (فريمات أقل) بطابع الأنمي."""
    k = int(prm["hold"])
    st["i"] = st.get("i", -1) + 1
    if st["i"] % k == 0:
        st["held"] = img
    return st["held"]


# =================== ستايلات ===================

def fx_neon_edges(img, lt, p, prm, st):
    h, w = img.shape[:2]
    small = cv2.resize(img, (w // 2, h // 2))
    g = cv2.GaussianBlur(cv2.cvtColor(small, cv2.COLOR_RGB2GRAY), (5, 5), 0)
    e = cv2.Canny(g, 60, 140)
    e = cv2.dilate(e, np.ones((2, 2), np.uint8))
    e = cv2.resize(e, (w, h)).astype(np.float32) / 255
    if prm["color"] == "rainbow":
        gx, gy = _grid_maps(st, h, w)
        hue = ((gx / w + gy / h * 0.5 + lt * 0.3) % 1 * 180).astype(np.uint8)
        hsv = np.stack([hue, np.full_like(hue, 255), np.full_like(hue, 255)], -1)
        col = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB).astype(np.float32) / 255
    else:
        col = hex_rgb(prm["color"]).astype(np.float32)[None, None, :] / 255
    glow = cv2.GaussianBlur(e, (0, 0), w / 250)[..., None]
    lines = (e[..., None] + glow * 1.5) * col
    base = img.astype(np.float32) / 255 * (1 - prm["dark"])
    out = 1 - (1 - base) * (1 - np.clip(lines, 0, 1))
    a = edge_env(lt, prm["_d"], 0.2, 0.2)
    return blend(img, (out * 255).astype(np.uint8), a)


def fx_halftone(img, lt, p, prm, st):
    h, w = img.shape[:2]
    cell = max(4, int(w * prm["size"] / 100))
    gx, gy = _grid_maps(st, h, w)
    key = ("ht", cell)
    if key not in st:
        cx = (gx % cell) - cell / 2
        cy = (gy % cell) - cell / 2
        st[key] = np.sqrt(cx * cx + cy * cy) / (cell / 2)
    g = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    small = cv2.resize(g, (w // cell + 1, h // cell + 1), interpolation=cv2.INTER_AREA)
    big = cv2.resize(small, (small.shape[1] * cell, small.shape[0] * cell), interpolation=cv2.INTER_NEAREST)[:h, :w]
    rad = (1 - big.astype(np.float32) / 255) * 1.25
    dots = np.clip((rad - st[key]) * cell * 0.5, 0, 1)
    paper = np.array([245, 238, 225], np.float32)
    ink = (img.astype(np.float32) * 0.6) if prm["color"] else np.zeros_like(img, np.float32)
    out = paper * (1 - dots[..., None]) + ink * dots[..., None]
    return blend(img, out.astype(np.uint8), edge_env(lt, prm["_d"], 0.15, 0.15))


def fx_cartoon(img, lt, p, prm, st):
    h, w = img.shape[:2]
    small = cv2.resize(img, (w // 2, h // 2))
    for _ in range(2):
        small = cv2.bilateralFilter(small, 7, 60, 7)
    q = 256 // int(prm["levels"])
    small = (small // q) * q + q // 2
    g = cv2.medianBlur(cv2.cvtColor(small, cv2.COLOR_RGB2GRAY), 5)
    edges = cv2.adaptiveThreshold(g, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 4)
    out = cv2.bitwise_and(small, small, mask=edges)
    return blend(img, cv2.resize(out, (w, h)), edge_env(lt, prm["_d"], 0.15, 0.15))


def fx_thermal(img, lt, p, prm, st):
    g = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    g = cv2.equalizeHist(cv2.GaussianBlur(g, (0, 0), 2))
    out = cv2.cvtColor(cv2.applyColorMap(g, cv2.COLORMAP_INFERNO if prm["style"] == 1 else cv2.COLORMAP_JET), cv2.COLOR_BGR2RGB)
    return blend(img, out, edge_env(lt, prm["_d"], 0.1, 0.1))


def fx_night_vision(img, lt, p, prm, st):
    h, w = img.shape[:2]
    r = np.random.default_rng(int(lt * 1000))
    g = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY).astype(np.float32)
    g = np.clip(g * 1.6 + 20 + r.normal(0, 14, g.shape), 0, 255)
    gx, gy = _grid_maps(st, h, w)
    if "vig" not in st:
        rr = np.sqrt(((gx / w - 0.5) * 1.4) ** 2 + (gy / h - 0.5) ** 2)
        st["vig"] = np.clip(1.25 - rr * 1.8, 0, 1)
    g = g * st["vig"]
    g[::3] *= 0.85
    out = np.stack([g * 0.25, g, g * 0.35], -1)
    return blend(img, np.clip(out, 0, 255).astype(np.uint8), edge_env(lt, prm["_d"], 0.08, 0.08))


def fx_xray(img, lt, p, prm, st):
    g = 255 - cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    g = cv2.equalizeHist(g).astype(np.float32)
    out = np.stack([g * 0.7, g * 0.9, np.clip(g * 1.1 + 20, 0, 255)], -1)
    return blend(img, out.astype(np.uint8), edge_env(lt, prm["_d"], 0.08, 0.08))


def fx_anaglyph(img, lt, p, prm, st):
    h, w = img.shape[:2]
    s = int(w * 0.008 * prm["amount"] * edge_env(lt, prm["_d"], 0.15, 0.15))
    if s < 1:
        return img
    out = img.copy()
    out[..., 0] = np.roll(img[..., 0], -s, 1)
    out[..., 1] = np.roll(img[..., 1], s, 1)
    out[..., 2] = np.roll(img[..., 2], s, 1)
    return out


def fx_dreamy(img, lt, p, prm, st):
    h, w = img.shape[:2]
    f = img.astype(np.float32) / 255
    soft = fast_blur(f, w / 90)
    bloom = fast_blur(np.clip(f - 0.55, 0, 1), w / 40) * 1.6
    out = 1 - (1 - (f * 0.55 + soft * 0.45)) * (1 - bloom)
    out = out * 0.92 + 0.06
    a = prm["amount"] * edge_env(lt, prm["_d"], 0.3, 0.3)
    return blend(img, (np.clip(out, 0, 1) * 255).astype(np.uint8), a)


def fx_spotlight(img, lt, p, prm, st):
    """تعتيم كل شيء ما عدا دائرة على العنصر المهم."""
    h, w = img.shape[:2]
    gx, gy = _grid_maps(st, h, w)
    key = ("sp", prm["x"], prm["y"], prm["r"])
    if key not in st:
        d = np.sqrt(((gx - prm["x"] * w) / w) ** 2 + ((gy - prm["y"] * h) / w) ** 2)
        st[key] = np.clip((d - prm["r"]) / (prm["r"] * 0.35), 0, 1)[..., None]
    a = prm["amount"] * ease(min(lt / 0.3, (prm["_d"] - lt) / 0.3, 1))
    dark = 1 - a * st[key]
    return (img * dark).astype(np.uint8)


def fx_tilt_shift(img, lt, p, prm, st):
    """تأثير المجسمات الصغيرة (Miniature)."""
    h, w = img.shape[:2]
    gx, gy = _grid_maps(st, h, w)
    if "ts" not in st:
        st["ts"] = np.clip(np.abs(gy / h - prm["y"]) / 0.25 - 0.3, 0, 1)[..., None]
    b = fast_blur(img, w / 160)
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
    hsv[..., 1] = np.clip(hsv[..., 1].astype(np.int16) * 1.35, 0, 255).astype(np.uint8)
    sat = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
    m = st["ts"] * edge_env(lt, prm["_d"], 0.3, 0.3)
    return (sat * (1 - m) + b * m).astype(np.uint8)


def fx_focus_pull(img, lt, p, prm, st):
    """سحب التركيز: من ضبابي لواضح ثم يرجع (أو العكس)."""
    s = bell(p) if prm["mode"] == 0 else 1 - bell(p)
    sigma = s * img.shape[1] / 110 * prm["amount"]
    out = fast_blur(img, sigma) if sigma > 0.3 else img
    return warp(out, 1 + 0.02 * s)


# =================== مؤثرات الزمن ===================
# دالة تأخذ p (0..1) وترجع موضع الإطار المصدر (0..1) داخل الفترة

def tm_velocity(p, prm):
    """بطيء - سريع - بطيء (Velocity Edit). amount يزيد قوة التباين بالسرعة."""
    g = p
    for _ in range(max(1, int(round(prm["amount"])))):
        g = ease(g)
    return g


def tm_speed_ramp(p, prm):
    """سريع ثم يبطّئ تدريجياً (للحظة المهمة)."""
    return 1 - (1 - p) ** (1 + prm["amount"])


def tm_slow_in(p, prm):
    """بطيء ثم يسرع."""
    return p ** (1 + prm["amount"])


def tm_rewind(p, prm):
    return 1 - p


def tm_boomerang(p, prm):
    return p * 2 if p < 0.5 else 2 - p * 2


def tm_repeat(p, prm):
    n = int(prm["times"])
    seg = 1.0 / n
    return (p % seg)


WINDOW = {
    "velocity": tm_velocity, "speed-ramp": tm_speed_ramp, "slow-in": tm_slow_in,
    "rewind": tm_rewind, "boomerang": tm_boomerang, "repeat": tm_repeat,
}


def _window_fx(img, lt, p, prm, st):
    # لمسة بصرية خفيفة للترجيع
    if prm.get("_name") == "rewind" and prm.get("look", 1):
        r = np.random.default_rng(int(lt * 1000))
        out = rgb_shift(img, 3)
        y0 = int((lt * 2.5 % 1) * img.shape[0])
        out[y0:y0 + 6] = np.clip(out[y0:y0 + 6].astype(np.int16) + r.integers(0, 120, out[y0:y0 + 6].shape), 0, 255)
        return out
    return img


FX2 = {
    "velocity":     (_window_fx, dict(amount=1.0, d=1.5), "زمن", "بطيء-سريع-بطيء (Velocity) ترند تيك توك"),
    "speed-ramp":   (_window_fx, dict(amount=1.5, d=1.5), "زمن", "سريع ثم بطيء للحظة المهمة"),
    "slow-in":      (_window_fx, dict(amount=1.5, d=1.5), "زمن", "بطيء ثم يسرع"),
    "rewind":       (_window_fx, dict(look=1, d=1.5), "زمن", "ترجيع للخلف"),
    "boomerang":    (_window_fx, dict(d=1.5), "زمن", "بومرانغ (ذهاب وعودة)"),
    "repeat":       (_window_fx, dict(times=3, d=1.2), "زمن", "تكرار سريع (Stutter Edit)"),
    "stutter":      (fx_stutter, dict(hold=3, d=2.0), "زمن", "فريمات متقطعة بطابع الأنمي"),
    "perspective-tilt": (fx_perspective_tilt, dict(angle=14.0, speed=2.0, d=3.0), "3D", "ميلان ثلاثي الأبعاد"),
    "flip-3d":      (fx_flip_3d, dict(dir=1, vertical=0, d=0.8), "3D", "قلب البطاقة 3D"),
    "frame-in":     (fx_frame_in, dict(scale=0.78, angle=0.0, d=3.0), "3D", "الفيديو داخل بطاقة فوق خلفية ضبابية"),
    "photo-snap":   (fx_photo_snap, dict(scale=0.72, angle=-5.0, d=1.5), "3D", "لقطة كاميرا بولارويد"),
    "grid":         (fx_grid, dict(n=3, d=0.6), "تقسيم", "شبكة مكررة"),
    "split-3":      (fx_split_3, dict(d=1.5), "تقسيم", "ثلاث نسخ جنب بعض"),
    "mirror-quad":  (fx_mirror_quad, dict(d=1.5), "تقسيم", "مرآة رباعية"),
    "kaleidoscope": (fx_kaleidoscope, dict(segments=6, spin=0.6, d=2.0), "تقسيم", "مشكال (كاليدوسكوب)"),
    "chroma-zoom":  (fx_chroma_zoom, dict(amount=1.08, bpm=120, d=4.0), "إيقاع", "زوم وانفصال ألوان مع الإيقاع"),
    "jello":        (fx_jello, dict(amount=1.0, d=1.0), "تشويه", "اهتزاز جيلي"),
    "ripple":       (fx_ripple, dict(C, amount=1.0, d=1.2), "تشويه", "موجة ماء من نقطة"),
    "swirl":        (fx_swirl, dict(C, amount=1.0, d=0.8), "تشويه", "دوامة"),
    "datamosh":     (fx_datamosh, dict(amount=1.0, d=1.5), "تشويه", "داتاموش (تلطيخ الحركة)"),
    "neon-edges":   (fx_neon_edges, dict(color="rainbow", dark=0.7, d=2.0), "ستايل", "حواف نيون متوهجة"),
    "halftone":     (fx_halftone, dict(size=1.0, color=0, d=2.0), "ستايل", "نقاط كوميكس"),
    "cartoon":      (fx_cartoon, dict(levels=6, d=2.0), "ستايل", "رسوم كرتونية"),
    "thermal":      (fx_thermal, dict(style=1, d=2.0), "ستايل", "كاميرا حرارية"),
    "night-vision": (fx_night_vision, dict(d=2.0), "ستايل", "رؤية ليلية"),
    "x-ray":        (fx_xray, dict(d=1.0), "ستايل", "أشعة X"),
    "anaglyph":     (fx_anaglyph, dict(amount=1.0, d=2.0), "ستايل", "ثلاثي أبعاد أحمر/أزرق"),
    "dreamy":       (fx_dreamy, dict(amount=0.9, d=3.0), "ستايل", "حالم متوهج"),
    "spotlight":    (fx_spotlight, dict(C, r=0.18, amount=0.75, d=2.0), "تركيز", "إضاءة على عنصر وتعتيم الباقي"),
    "tilt-shift":   (fx_tilt_shift, dict(y=0.55, d=3.0), "تركيز", "مجسمات صغيرة (Miniature)"),
    "focus-pull":   (fx_focus_pull, dict(mode=1, amount=1.0, d=1.2), "تركيز", "سحب التركيز"),
}
