"""
حركات ومؤثرات — الدفعة 3.
نفس الواجهة: f(img, lt, p, prm, st) -> img
"""
import math
import numpy as np
import cv2

from .effects import ease, ease_out, bell, edge_env, warp, blend, screen, hex_rgb, rgb_shift, zoom_blur, TAU
from .effects2 import _grid_maps, fast_blur, paste_card, rounded_mask

C = {"x": 0.5, "y": 0.5}


def _gray3(img):
    return cv2.cvtColor(cv2.cvtColor(img, cv2.COLOR_RGB2GRAY), cv2.COLOR_GRAY2RGB)


# =================== زمن وأثر الحركة ===================

def fx_rgb_trail(img, lt, p, prm, st):
    """الأحمر الآن، الأخضر والأزرق متأخران: أثر ألوان خلف الحركة."""
    buf = st.setdefault("buf", [])
    buf.append(img)
    k = int(prm["lag"])
    if len(buf) > 2 * k + 1:
        buf.pop(0)
    g = buf[max(0, len(buf) - 1 - k)]
    b = buf[0]
    out = img.copy()
    out[..., 1] = g[..., 1]
    out[..., 2] = b[..., 2]
    return blend(img, out, edge_env(lt, prm["_d"], 0.1, 0.1))


def fx_light_trails(img, lt, p, prm, st):
    """تعريض طويل: الأجزاء المضيئة تترك أثراً."""
    acc = st.get("acc")
    f = img.astype(np.float32)
    acc = f if acc is None else np.maximum(f, acc * prm["decay"])
    st["acc"] = acc
    a = edge_env(lt, prm["_d"], 0.05, 0.3)
    return (f * (1 - a) + np.maximum(f, acc) * a).astype(np.uint8)


def fx_slit_scan(img, lt, p, prm, st):
    """كل سطر من لحظة زمنية مختلفة: تشويه زمني مذهل مع الحركة."""
    h, w = img.shape[:2]
    buf = st.setdefault("buf", [])
    buf.append(img)
    n = int(prm["frames"])
    if len(buf) > n:
        buf.pop(0)
    m = len(buf)
    if m < 2:
        return img
    stack = np.stack(buf, 0)
    rows = np.arange(h)
    idx = ((rows / h) * (m - 1)).astype(int)
    if prm["dir"] < 0:
        idx = (m - 1) - idx
    out = stack[idx, rows]
    return blend(img, out, edge_env(lt, prm["_d"], 0.2, 0.2))


# =================== لون ===================

def fx_color_pop(img, lt, p, prm, st):
    """إبقاء لون واحد وتحويل الباقي أبيض وأسود."""
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
    hues = {"red": 0, "orange": 15, "yellow": 30, "green": 60, "cyan": 90, "blue": 115, "purple": 140, "pink": 165}
    c = hues.get(str(prm["color"]), 0)
    d = np.abs(((hsv[..., 0].astype(np.int16) - c + 90) % 180) - 90)
    m = np.clip((prm["width"] - d) / 6.0, 0, 1) * np.clip((hsv[..., 1].astype(np.float32) - 50) / 50, 0, 1)
    m = m[..., None] * edge_env(lt, prm["_d"], 0.15, 0.15)
    g = _gray3(img)
    k = edge_env(lt, prm["_d"], 0.15, 0.15)
    gray_mix = blend(img, g, k)
    return (img * m + gray_mix * (1 - m)).astype(np.uint8)


def fx_duotone(img, lt, p, prm, st):
    g = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY).astype(np.float32)[..., None] / 255
    a = hex_rgb(prm["dark"]).astype(np.float32)
    b = hex_rgb(prm["light"]).astype(np.float32)
    out = a * (1 - g) + b * g
    return blend(img, out.astype(np.uint8), edge_env(lt, prm["_d"], 0.15, 0.15))


def fx_hue_cycle(img, lt, p, prm, st):
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
    hsv[..., 0] = ((hsv[..., 0].astype(np.int16) + int(lt * prm["speed"] * 180)) % 180).astype(np.uint8)
    out = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
    return blend(img, out, edge_env(lt, prm["_d"], 0.2, 0.2))


def fx_pop_art(img, lt, p, prm, st):
    """بوب آرت: ألوان مسطحة صارخة وحواف سوداء."""
    h, w = img.shape[:2]
    small = cv2.resize(img, (w // 2, h // 2))
    g = cv2.cvtColor(small, cv2.COLOR_RGB2GRAY)
    pal = np.array([[20, 20, 40], [230, 40, 120], [40, 200, 230], [255, 225, 40]], np.uint8)
    lv = np.clip((g.astype(np.int16) * 4) // 256, 0, 3)
    out = pal[lv]
    e = cv2.Canny(cv2.GaussianBlur(g, (5, 5), 0), 60, 140)
    out[e > 0] = 0
    return blend(img, cv2.resize(out, (w, h), interpolation=cv2.INTER_NEAREST), edge_env(lt, prm["_d"], 0.12, 0.12))


def fx_pixel_sort(img, lt, p, prm, st):
    """فرز البكسلات حسب الإضاءة في الأسطر (ترند غلتش فني)."""
    h, w = img.shape[:2]
    sm = cv2.resize(img, (w // 2, h // 2))
    hh, ww = sm.shape[:2]
    lum = cv2.cvtColor(sm, cv2.COLOR_RGB2GRAY)
    thr = int(255 * prm["threshold"])
    out = sm.copy()
    k = edge_env(lt, prm["_d"], 0.1, 0.1)
    cut = int(ww * (0.2 + 0.8 * k))
    for y in range(hh):
        row = lum[y, :cut]
        mask = row > thr
        if mask.sum() < 4:
            continue
        idx = np.where(mask)[0]
        seg = sm[y, idx]
        order = np.argsort(row[idx])
        out[y, idx] = seg[order]
    return cv2.resize(out, (w, h))


def fx_ascii(img, lt, p, prm, st):
    """تحويل الصورة لحروف ASCII خضراء على أسود."""
    h, w = img.shape[:2]
    cell = max(6, int(w * prm["size"] / 100))
    chars = " .:-=+*#%@"
    key = ("atlas", cell)
    if key not in st:
        atlas = []
        for ch in chars:
            t = np.zeros((cell, cell), np.uint8)
            cv2.putText(t, ch, (0, int(cell * 0.85)), cv2.FONT_HERSHEY_PLAIN, cell / 12, 255, 1, cv2.LINE_AA)
            atlas.append(t)
        st[key] = np.stack(atlas)
    g = cv2.resize(cv2.cvtColor(img, cv2.COLOR_RGB2GRAY), (w // cell, h // cell), interpolation=cv2.INTER_AREA)
    lv = (g.astype(np.int32) * (len(chars) - 1) // 255)
    tiles = st[key][lv]
    gh, gw = lv.shape
    mono = tiles.transpose(0, 2, 1, 3).reshape(gh * cell, gw * cell)
    canvas = np.zeros((h, w), np.uint8)
    canvas[:mono.shape[0], :mono.shape[1]] = mono
    col = hex_rgb(prm["color"]).astype(np.float32) / 255
    out = (canvas[..., None].astype(np.float32) * col).astype(np.uint8)
    return blend(img, out, edge_env(lt, prm["_d"], 0.1, 0.1))


def fx_sketch(img, lt, p, prm, st):
    g = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    inv = 255 - g
    bl = cv2.GaussianBlur(inv, (0, 0), img.shape[1] / 180)
    sk = cv2.divide(g, 255 - bl, scale=256)
    out = cv2.cvtColor(sk, cv2.COLOR_GRAY2RGB)
    if prm["color"]:
        out = cv2.multiply(out, img, scale=1 / 255)
    return blend(img, out, edge_env(lt, prm["_d"], 0.15, 0.15))


def fx_watercolor(img, lt, p, prm, st):
    h, w = img.shape[:2]
    small = cv2.resize(img, (w // 3, h // 3))
    sty = cv2.stylization(small, sigma_s=40, sigma_r=0.35)
    out = cv2.resize(sty, (w, h), interpolation=cv2.INTER_LINEAR)
    return blend(img, out, edge_env(lt, prm["_d"], 0.2, 0.2))


def fx_emboss(img, lt, p, prm, st):
    k = np.array([[-2, -1, 0], [-1, 1, 1], [0, 1, 2]], np.float32)
    g = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    e = cv2.filter2D(g.astype(np.float32), -1, k)
    out = cv2.cvtColor(cv2.normalize(e, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8), cv2.COLOR_GRAY2RGB)
    return blend(img, out, edge_env(lt, prm["_d"], 0.15, 0.15))


# =================== تشويه وعدسات ===================

def fx_fisheye(img, lt, p, prm, st):
    h, w = img.shape[:2]
    gx, gy = _grid_maps(st, h, w)
    if "fr" not in st:
        nx, ny = (gx - w / 2) / (w / 2), (gy - h / 2) / (w / 2)
        st["fr"] = np.sqrt(nx * nx + ny * ny)
        st["fn"] = (nx, ny)
    k = prm["amount"] * 0.45 * edge_env(lt, prm["_d"], 0.25, 0.25)
    r = st["fr"]
    f = 1 + k * r * r
    nx, ny = st["fn"]
    mx = (nx / f) * (w / 2) + w / 2
    my = (ny / f) * (w / 2) + h / 2
    s = 1 / (1 + k * 0.25)
    mx = (mx - w / 2) * s + w / 2
    my = (my - h / 2) * s + h / 2
    return cv2.remap(img, mx.astype(np.float32), my.astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def fx_magnify(img, lt, p, prm, st):
    """عدسة مكبرة دائرية على نقطة."""
    h, w = img.shape[:2]
    e = ease_out(min(lt / 0.3, (prm["_d"] - lt) / 0.3, 1))
    if e <= 0.01:
        return img
    R = int(w * prm["r"] * e)
    cx, cy = int(prm["x"] * w), int(prm["y"] * h)
    z = prm["zoom"]
    big = warp(img, z, prm["x"], prm["y"])
    m = np.zeros((h, w), np.uint8)
    cv2.circle(m, (cx, cy), R, 255, -1, cv2.LINE_AA)
    mf = m.astype(np.float32)[..., None] / 255
    out = img * (1 - mf) + big * mf
    out = out.astype(np.uint8)
    cv2.circle(out, (cx, cy), R, (255, 255, 255), max(2, w // 300), cv2.LINE_AA)
    sh = np.zeros((h, w), np.uint8)
    cv2.circle(sh, (cx, cy), R + w // 120, 255, w // 150, cv2.LINE_AA)
    sh = cv2.GaussianBlur(sh, (0, 0), w / 200).astype(np.float32)[..., None] / 255
    return (out * (1 - 0.4 * sh)).astype(np.uint8)


def fx_vertigo(img, lt, p, prm, st):
    """دولي زوم (Vertigo): المركز ثابت والأطراف تمتد."""
    h, w = img.shape[:2]
    gx, gy = _grid_maps(st, h, w)
    if "vr" not in st:
        dx, dy = gx - w / 2, gy - h / 2
        st["vr"] = np.sqrt(dx * dx + dy * dy) / (w / 2)
        st["vd"] = (dx, dy)
    k = prm["amount"] * 0.35 * math.sin(math.pi * p)
    dx, dy = st["vd"]
    f = 1 / (1 + k * np.clip(st["vr"], 0, 2) ** 1.5)
    mx = w / 2 + dx * f
    my = h / 2 + dy * f
    return cv2.remap(img, mx.astype(np.float32), my.astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def fx_dizzy(img, lt, p, prm, st):
    """دوخة: تمايل ورؤية مزدوجة."""
    e = edge_env(lt, prm["_d"], 0.3, 0.3) * prm["amount"]
    a = math.sin(lt * 2.2) * 4 * e
    dx = math.sin(lt * 1.7) * img.shape[1] * 0.012 * e
    A = warp(img, 1.06, 0.5, 0.5, dx, 0, a)
    B = warp(img, 1.06, 0.5, 0.5, -dx * 2, img.shape[0] * 0.006 * e, -a * 0.6)
    out = blend(A, B, 0.4 * e)
    return fast_blur(out, 1 + 3 * e) if e > 0.3 else out


def fx_droste(img, lt, p, prm, st):
    """إطار داخل إطار لانهائي (Droste)."""
    h, w = img.shape[:2]
    s = prm["scale"]
    e = edge_env(lt, prm["_d"], 0.25, 0.25)
    out = img.copy()
    cur = img
    for i in range(int(prm["depth"])):
        cur = cv2.resize(cur, (max(2, int(cur.shape[1] * s)), max(2, int(cur.shape[0] * s))), interpolation=cv2.INTER_AREA)
        ch, cw = cur.shape[:2]
        y0, x0 = (h - ch) // 2, (w - cw) // 2
        ang = lt * prm["spin"] * (i + 1) * 15
        M = cv2.getRotationMatrix2D((w / 2, h / 2), ang, 1)
        layer = np.zeros_like(img)
        layer[y0:y0 + ch, x0:x0 + cw] = cur
        mask = np.zeros((h, w), np.uint8)
        mask[y0:y0 + ch, x0:x0 + cw] = 255
        layer = cv2.warpAffine(layer, M, (w, h))
        mask = cv2.warpAffine(mask, M, (w, h)) > 128
        out[mask] = layer[mask]
        if ang == 0:
            cv2.rectangle(out, (x0, y0), (x0 + cw, y0 + ch), (255, 255, 255), max(1, w // 400))
    return blend(img, out, e)


# =================== شاشات وتلفزيون ===================

def _tv(img, k):
    """k=0 صورة كاملة، k=1 مطفأة."""
    h, w = img.shape[:2]
    out = np.zeros_like(img)
    if k < 0.6:
        s = 1 - k / 0.6
        nh = max(2, int(h * s))
        sq = cv2.resize(img, (w, nh))
        sq = np.clip(sq.astype(np.int16) + int(120 * (1 - s)), 0, 255).astype(np.uint8)
        y0 = (h - nh) // 2
        out[y0:y0 + nh] = sq
    elif k < 0.9:
        s = 1 - (k - 0.6) / 0.3
        lw = max(4, int(w * s))
        x0 = (w - lw) // 2
        out[h // 2 - 2:h // 2 + 2, x0:x0 + lw] = 255
    else:
        r = int(6 * (1 - (k - 0.9) / 0.1)) + 1
        cv2.circle(out, (w // 2, h // 2), r, (255, 255, 255), -1, cv2.LINE_AA)
    glow = cv2.GaussianBlur(out, (0, 0), 6)
    return cv2.add(out, glow)


def fx_tv_off(img, lt, p, prm, st):
    return _tv(img, ease(p))


def fx_tv_on(img, lt, p, prm, st):
    return _tv(img, 1 - ease(p))


def fx_blink(img, lt, p, prm, st):
    """رمشة عين: جفنان يغلقان ويفتحان."""
    h, w = img.shape[:2]
    k = bell(p) ** 0.7
    lid = int(h / 2 * k)
    out = img.copy()
    if lid > 0:
        out[:lid] = 0
        out[h - lid:] = 0
        edge = max(2, h // 60)
        out[max(0, lid - edge):lid] = (out[max(0, lid - edge):lid] * 0.3).astype(np.uint8)
    return fast_blur(out, 1 + 6 * k) if k > 0.2 else out


def fx_film_strip(img, lt, p, prm, st):
    """الفيديو داخل شريط فيلم يتحرك."""
    h, w = img.shape[:2]
    e = ease(min(lt / 0.35, (prm["_d"] - lt) / 0.35, 1))
    if e < 0.01:
        return img
    s = 1 - 0.42 * e
    fw, fh = int(w * s), int(h * s)
    frame = cv2.resize(img, (fw, fh))
    strip_h = int(fh * 1.3)
    strip = np.full((strip_h, w * 2, 3), 18, np.uint8)
    pitch = fw + w // 20
    off = int((lt * w * 0.25) % pitch)
    x = -off
    y0 = (strip_h - fh) // 2
    while x < w * 2:
        a, b = max(0, x), min(w * 2, x + fw)
        if b > a:
            strip[y0:y0 + fh, a:b] = frame[:, a - x:b - x]
        x += pitch
    hole_w, hole_h = w // 45, strip_h // 16
    for xx in range(-off % (hole_w * 3), w * 2, hole_w * 3):
        cv2.rectangle(strip, (xx, hole_h // 2), (xx + hole_w, hole_h // 2 + hole_h), (235, 235, 230), -1)
        cv2.rectangle(strip, (xx, strip_h - hole_h // 2 - hole_h), (xx + hole_w, strip_h - hole_h // 2), (235, 235, 230), -1)
    bg = (fast_blur(img, w / 30) * 0.4).astype(np.uint8)
    y0 = (h - strip_h) // 2
    out = bg.copy()
    sy0, sy1 = max(0, y0), min(h, y0 + strip_h)
    out[sy0:sy1] = strip[sy0 - y0:sy1 - y0, :w]
    M = cv2.getRotationMatrix2D((w / 2, h / 2), prm["angle"] * e, 1)
    rot = cv2.warpAffine(out, M, (w, h), borderMode=cv2.BORDER_REFLECT)
    return blend(img, rot, e)


def fx_phone_frame(img, lt, p, prm, st):
    """الفيديو داخل إطار جوال فوق خلفية ضبابية."""
    h, w = img.shape[:2]
    e = ease_out(min(lt / 0.4, (prm["_d"] - lt) / 0.4, 1))
    if e < 0.01:
        return img
    ph = int(h * (1 - 0.18 * e))
    pw = int(ph * 9 / 19.5) if w > h else int(w * (1 - 0.18 * e))
    if w <= h:
        ph = int(pw * 19.5 / 9)
        if ph > h * 0.95:
            ph = int(h * 0.95)
            pw = int(ph * 9 / 19.5)
    screen_img = cv2.resize(img[:, max(0, (w - int(h * 9 / 19.5)) // 2):][:, :max(2, int(h * 9 / 19.5))] if w > h else img,
                            (pw, ph))
    bezel = max(4, pw // 22)
    phone = np.full((ph + 2 * bezel, pw + 2 * bezel, 3), 15, np.uint8)
    phone[bezel:bezel + ph, bezel:bezel + pw] = screen_img
    notch_w = pw // 3
    cv2.rectangle(phone, ((pw + 2 * bezel - notch_w) // 2, bezel), ((pw + 2 * bezel + notch_w) // 2, bezel + bezel), (15, 15, 15), -1)
    bg = (fast_blur(img, w / 25) * 0.55).astype(np.uint8)
    return paste_card(bg, phone, w / 2, h / 2, prm["angle"] * e, 1.0, radius=pw * 0.12, shadow=True)


def fx_beat_flash(img, lt, p, prm, st):
    """ومضة مع كل ضربة إيقاع."""
    beat = 60.0 / prm["bpm"]
    ph = (lt % beat) / beat
    k = math.exp(-ph * 10) * prm["amount"]
    col = np.empty_like(img)
    col[:] = hex_rgb(prm["color"])
    return blend(img, col, k)


def fx_ink_reveal(img, lt, p, prm, st):
    """ظهور الصورة كأنها حبر ينتشر من السواد."""
    h, w = img.shape[:2]
    if "n" not in st:
        r = np.random.default_rng(int(prm["seed"]))
        small = r.random((h // 16 + 2, w // 16 + 2)).astype(np.float32)
        n = cv2.resize(cv2.GaussianBlur(small, (0, 0), 2), (w, h), interpolation=cv2.INTER_CUBIC)
        gx, gy = _grid_maps(st, h, w)
        rad = np.sqrt(((gx - w / 2) / w) ** 2 + ((gy - h / 2) / w) ** 2)
        n = (n - n.min()) / (n.max() - n.min() + 1e-6) * 0.5 + rad
        st["n"] = (n - n.min()) / (n.max() - n.min() + 1e-6)
    thr = ease(p) * 1.15
    m = np.clip((thr - st["n"]) / 0.06, 0, 1)[..., None]
    bg = np.full_like(img, 0) if prm["color"] == "black" else np.full_like(img, 255)
    return (img * m + bg * (1 - m)).astype(np.uint8)


def fx_glow_pulse(img, lt, p, prm, st):
    """توهج ينبض مع الإيقاع (بلوم)."""
    h, w = img.shape[:2]
    beat = 60.0 / prm["bpm"]
    k = math.exp(-((lt % beat) / beat) * 6) * prm["amount"]
    f = img.astype(np.float32) / 255
    bl = fast_blur(np.clip(f - 0.45, 0, 1), w / 50) * 2.0 * k
    return (np.clip(1 - (1 - f) * (1 - bl), 0, 1) * 255).astype(np.uint8)


def fx_shake_rgb(img, lt, p, prm, st):
    """اهتزاز مع انفصال ألوان (ستايل الكليبات)."""
    r = np.random.default_rng(int(lt * 60) + 3)
    e = edge_env(lt, prm["_d"], 0.05, 0.15) * prm["amount"]
    h, w = img.shape[:2]
    out = warp(img, 1 + 0.06 * e, 0.5, 0.5, r.normal(0, w * 0.012 * e), r.normal(0, h * 0.012 * e))
    return rgb_shift(out, w * 0.008 * e * r.choice([-1, 1]))


FX3 = {
    "rgb-trail":     (fx_rgb_trail,     dict(lag=4, d=2.0), "زمن", "أثر ألوان خلف الحركة"),
    "light-trails":  (fx_light_trails,  dict(decay=0.92, d=2.0), "زمن", "تعريض طويل (أثر الأضواء)"),
    "slit-scan":     (fx_slit_scan,     dict(frames=20, dir=1, d=2.0), "زمن", "سلِت سكان: كل سطر من لحظة مختلفة"),
    "color-pop":     (fx_color_pop,     dict(color="red", width=12, d=3.0), "لون", "إبقاء لون واحد والباقي أبيض وأسود"),
    "duotone":       (fx_duotone,       dict(dark="#1a0b3d", light="#ff8a3d", d=2.0), "لون", "لونان فقط (ستايل بوسترات)"),
    "hue-cycle":     (fx_hue_cycle,     dict(speed=0.5, d=2.0), "لون", "دوران ألوان قوس قزح"),
    "pop-art":       (fx_pop_art,       dict(d=1.5), "ستايل", "بوب آرت"),
    "pixel-sort":    (fx_pixel_sort,    dict(threshold=0.45, d=1.0), "ستايل", "فرز بكسلات (غلتش فني)"),
    "ascii":         (fx_ascii,         dict(size=1.2, color="green", d=1.5), "ستايل", "حروف ASCII"),
    "sketch":        (fx_sketch,        dict(color=0, d=2.0), "ستايل", "رسم بالرصاص"),
    "watercolor":    (fx_watercolor,    dict(d=2.0), "ستايل", "ألوان مائية"),
    "emboss":        (fx_emboss,        dict(d=1.0), "ستايل", "نقش بارز"),
    "fisheye":       (fx_fisheye,       dict(amount=1.0, d=2.0), "عدسة", "عين السمكة"),
    "magnify":       (fx_magnify,       dict(C, r=0.14, zoom=2.0, d=2.0), "عدسة", "عدسة مكبرة على نقطة"),
    "vertigo":       (fx_vertigo,       dict(amount=1.0, d=1.5), "عدسة", "دولي زوم (Vertigo)"),
    "dizzy":         (fx_dizzy,         dict(amount=1.0, d=2.0), "عدسة", "دوخة ورؤية مزدوجة"),
    "droste":        (fx_droste,        dict(scale=0.72, depth=5, spin=0.0, d=2.0), "عدسة", "إطار داخل إطار لانهائي"),
    "tv-off":        (fx_tv_off,        dict(d=0.6), "شاشة", "إطفاء تلفزيون قديم"),
    "tv-on":         (fx_tv_on,         dict(d=0.6), "شاشة", "تشغيل تلفزيون قديم"),
    "blink":         (fx_blink,         dict(d=0.5), "شاشة", "رمشة عين"),
    "film-strip":    (fx_film_strip,    dict(angle=-6.0, d=3.0), "شاشة", "الفيديو داخل شريط فيلم"),
    "phone-frame":   (fx_phone_frame,   dict(angle=0.0, d=3.0), "شاشة", "الفيديو داخل إطار جوال"),
    "ink-reveal":    (fx_ink_reveal,    dict(seed=1, color="black", d=1.2), "شاشة", "ظهور كالحبر"),
    "beat-flash":    (fx_beat_flash,    dict(bpm=120, color="white", amount=0.5, d=4.0), "إيقاع", "ومضة مع كل ضربة"),
    "glow-pulse":    (fx_glow_pulse,    dict(bpm=120, amount=1.0, d=4.0), "إيقاع", "توهج ينبض مع الإيقاع"),
    "shake-rgb":     (fx_shake_rgb,     dict(amount=1.0, d=0.6), "إيقاع", "اهتزاز مع انفصال ألوان"),
}
