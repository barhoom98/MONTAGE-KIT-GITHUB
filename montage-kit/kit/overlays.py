"""
طبقات ضوئية على خلفية سوداء — تُستخدم بوضع الدمج Screen
(في CapCut: Blend → Screen، في Premiere: Blend Mode → Screen).
"""
import math
import numpy as np
import cv2

W, H = 1920, 1080
FPS = 30
DUR = 6.0
TAU = 2 * math.pi


def _grid(w, h):
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    return x / w, y / h


def _smooth_path(rng, n_frames, k=3, speed=0.15):
    """مسار عشوائي ناعم (مجموع موجات)."""
    t = np.arange(n_frames) / FPS
    out = np.zeros(n_frames)
    for _ in range(k):
        out += rng.uniform(0.3, 1.0) * np.sin(TAU * rng.uniform(0.3, 1.0) * speed * t + rng.uniform(0, TAU))
    return out / k


def _to8(img):
    return (np.clip(img, 0, 1) * 255).astype(np.uint8)


def _up(img):
    return cv2.resize(img, (W, H), interpolation=cv2.INTER_CUBIC)


# =================== تسريب ضوء ===================

def light_leak(palette, seed, n_blobs=6, strength=1.0):
    rng = np.random.default_rng(seed)
    w, h = 480, 270
    gx, gy = _grid(w, h)
    n = int(DUR * FPS)
    blobs = []
    for i in range(n_blobs):
        side = rng.integers(0, 4)
        cx0 = rng.choice([rng.uniform(-0.2, 0.25), rng.uniform(0.75, 1.2)]) if side < 2 else rng.uniform(0, 1)
        cy0 = rng.uniform(-0.2, 1.2)
        blobs.append(dict(
            cx=cx0 + 0.35 * _smooth_path(rng, n, 3, 0.25),
            cy=cy0 + 0.35 * _smooth_path(rng, n, 3, 0.25),
            r=rng.uniform(0.18, 0.45),
            amp=0.55 + 0.45 * _smooth_path(rng, n, 2, 0.4),
            col=np.array(palette[i % len(palette)], np.float32) / 255,
        ))
    for f in range(n):
        img = np.zeros((h, w, 3), np.float32)
        for b in blobs:
            d2 = ((gx - b["cx"][f]) * 1.6) ** 2 + (gy - b["cy"][f]) ** 2
            g = np.exp(-d2 / (2 * b["r"] ** 2)) * max(0, b["amp"][f])
            img += g[..., None] * b["col"]
        img = 1 - np.exp(-img * 1.6 * strength)  # ضغط ناعم للإضاءة
        yield _to8(_up(img))


def o_leak_warm():
    return light_leak([(255, 120, 30), (255, 60, 20), (255, 180, 80)], 1)


def o_leak_red():
    return light_leak([(255, 30, 40), (255, 80, 30), (200, 20, 60)], 2)


def o_leak_rainbow():
    return light_leak([(255, 60, 60), (255, 200, 40), (60, 220, 120), (60, 140, 255), (200, 80, 255)], 3, 7)


def o_leak_blue():
    return light_leak([(40, 120, 255), (80, 200, 255), (150, 80, 255)], 4)


def o_leak_golden():
    return light_leak([(255, 190, 70), (255, 150, 40), (255, 230, 150)], 5, 5)


# =================== عدسة ولمعات ===================

def o_lens_flare():
    n = int(DUR * FPS)
    w, h = 960, 540
    gx, gy = _grid(w, h)
    for f in range(n):
        p = f / (n - 1)
        cx, cy = -0.15 + 1.3 * p, 0.25 + 0.1 * math.sin(p * math.pi)
        img = np.zeros((h, w, 3), np.float32)
        dx, dy = (gx - cx) * 1.78, gy - cy
        core = np.exp(-(dx ** 2 + dy ** 2) / 0.002)
        halo = np.exp(-(dx ** 2 + dy ** 2) / 0.03) * 0.5
        streak = np.exp(-(dy ** 2) / 0.00015) * np.exp(-np.abs(dx) / 0.6) * 0.8
        img += (core + halo)[..., None] * np.array([1.0, 0.9, 0.75])
        img += streak[..., None] * np.array([0.5, 0.75, 1.0])
        # أشباح العدسة على الخط المار بالمركز
        for k, (s, r, col) in enumerate([(0.6, 0.04, (0.4, 1.0, 0.6)), (1.0, 0.07, (0.6, 0.5, 1.0)),
                                           (1.4, 0.03, (1.0, 0.6, 0.3)), (1.8, 0.1, (0.3, 0.6, 1.0))]):
            gxp = 0.5 + (0.5 - cx) * s * 0.9
            gyp = 0.5 + (0.5 - cy) * s * 0.9
            d2 = ((gx - gxp) * 1.78) ** 2 + (gy - gyp) ** 2
            ring = np.exp(-d2 / (2 * r * r)) * 0.25
            img += ring[..., None] * np.array(col)
        fade = min(1, p * 6, (1 - p) * 6)
        yield _to8(_up(1 - np.exp(-img * 1.5 * fade)))


def o_light_rays():
    n = int(DUR * FPS)
    w, h = 960, 540
    gx, gy = _grid(w, h)
    ang = np.arctan2(gy + 0.15, (gx - 0.15) * 1.78)
    dist = np.sqrt(((gx - 0.15) * 1.78) ** 2 + (gy + 0.15) ** 2)
    rng = np.random.default_rng(9)
    freqs = rng.uniform(15, 45, 6)
    phases = rng.uniform(0, TAU, 6)
    for f in range(n):
        t = f / FPS
        rays = sum(np.clip(np.sin(ang * fr + ph + 0.15 * math.sin(t * 0.7 + i)), 0, 1) ** 6
                   for i, (fr, ph) in enumerate(zip(freqs, phases))) / 2
        rays = rays * np.exp(-dist / 0.55) * (0.85 + 0.15 * math.sin(t * 1.3))
        img = rays[..., None] * np.array([1.0, 0.92, 0.75], np.float32)
        img = cv2.GaussianBlur(img, (0, 0), 3)
        yield _to8(_up(img * 0.75))


def _star(img, x, y, size, col, alpha):
    s = size
    pts = np.array([[x, y - s], [x + s * 0.18, y - s * 0.18], [x + s, y], [x + s * 0.18, y + s * 0.18],
                    [x, y + s], [x - s * 0.18, y + s * 0.18], [x - s, y], [x - s * 0.18, y - s * 0.18]], np.int32)
    cv2.fillPoly(img, [pts], tuple(float(c * alpha) for c in col), cv2.LINE_AA)


def o_sparkles():
    rng = np.random.default_rng(11)
    n = int(DUR * FPS)
    N = 90
    xs, ys = rng.uniform(0, W, N), rng.uniform(0, H, N)
    sz = rng.uniform(8, 34, N)
    ph = rng.uniform(0, TAU, N)
    sp = rng.uniform(1.0, 3.0, N)
    cols = [(1, 1, 1), (1, 0.9, 0.6), (0.7, 0.9, 1)]
    for f in range(n):
        t = f / FPS
        img = np.zeros((H, W, 3), np.float32)
        for i in range(N):
            a = max(0, math.sin(ph[i] + sp[i] * t)) ** 3
            if a > 0.02:
                _star(img, xs[i], ys[i] - 15 * t, sz[i] * (0.6 + 0.4 * a), cols[i % 3], a)
        glow = cv2.GaussianBlur(img, (0, 0), 6)
        yield _to8(img + glow * 1.5)


def o_bokeh():
    rng = np.random.default_rng(12)
    n = int(DUR * FPS)
    w, h = 960, 540
    N = 40
    xs, ys = rng.uniform(0, w, N), rng.uniform(0, h, N)
    vx, vy = rng.uniform(-12, 12, N), rng.uniform(-18, -4, N)
    rr = rng.uniform(14, 55, N)
    pal = [(1.0, 0.75, 0.4), (1.0, 0.55, 0.3), (1.0, 0.9, 0.6), (0.6, 0.8, 1.0)]
    cols = [pal[i % 4] for i in range(N)]
    ph = rng.uniform(0, TAU, N)
    for f in range(n):
        t = f / FPS
        img = np.zeros((h, w, 3), np.float32)
        for i in range(N):
            x = (xs[i] + vx[i] * t) % (w + 120) - 60
            y = (ys[i] + vy[i] * t) % (h + 120) - 60
            a = 0.25 + 0.15 * math.sin(ph[i] + t * 1.2)
            cv2.circle(img, (int(x), int(y)), int(rr[i]), tuple(c * a for c in cols[i]), -1, cv2.LINE_AA)
            cv2.circle(img, (int(x), int(y)), int(rr[i]), tuple(c * a * 0.6 for c in cols[i]), 2, cv2.LINE_AA)
        img = cv2.GaussianBlur(img, (0, 0), 2.5)
        yield _to8(_up(img))


def o_stars():
    rng = np.random.default_rng(13)
    n = int(DUR * FPS)
    N = 400
    xs, ys = rng.uniform(0, W, N), rng.uniform(0, H, N)
    b = rng.uniform(0.2, 1.0, N) ** 2
    ph = rng.uniform(0, TAU, N)
    sp = rng.uniform(1, 4, N)
    for f in range(n):
        t = f / FPS
        img = np.zeros((H, W, 3), np.float32)
        for i in range(N):
            a = b[i] * (0.6 + 0.4 * math.sin(ph[i] + sp[i] * t))
            cv2.circle(img, (int(xs[i]), int(ys[i])), 1 + int(b[i] * 2), (a, a, a * 0.95 + 0.05), -1, cv2.LINE_AA)
        yield _to8(img + cv2.GaussianBlur(img, (0, 0), 4) * 2)


# =================== جزيئات ===================

def o_snow():
    rng = np.random.default_rng(14)
    n = int(DUR * FPS)
    N = 350
    depth = rng.uniform(0.2, 1.0, N)
    xs, ys = rng.uniform(0, W, N), rng.uniform(0, H, N)
    ph = rng.uniform(0, TAU, N)
    for f in range(n):
        t = f / FPS
        img = np.zeros((H, W, 3), np.float32)
        for i in range(N):
            d = depth[i]
            y = (ys[i] + 140 * d * t) % (H + 20) - 10
            x = (xs[i] + 30 * math.sin(ph[i] + t * 1.2 * d) + 20 * t) % W
            v = 0.4 + 0.6 * d
            cv2.circle(img, (int(x), int(y)), max(1, int(5 * d)), (v, v, v), -1, cv2.LINE_AA)
        yield _to8(cv2.GaussianBlur(img, (0, 0), 1.2) * 1.2)


def o_rain():
    rng = np.random.default_rng(15)
    n = int(DUR * FPS)
    N = 500
    depth = rng.uniform(0.3, 1.0, N)
    xs, ys = rng.uniform(0, W + 300, N), rng.uniform(0, H, N)
    for f in range(n):
        t = f / FPS
        img = np.zeros((H, W, 3), np.float32)
        for i in range(N):
            d = depth[i]
            sp = 1400 * d
            y = (ys[i] + sp * t) % (H + 100) - 50
            x = (xs[i] - 0.18 * sp * t) % (W + 300) - 150
            L = 40 * d
            v = 0.25 + 0.45 * d
            cv2.line(img, (int(x), int(y)), (int(x - 0.18 * L), int(y + L)), (v, v, v * 1.05), 1 + int(d > 0.8), cv2.LINE_AA)
        yield _to8(cv2.GaussianBlur(img, (0, 0), 0.8))


def o_embers():
    rng = np.random.default_rng(16)
    n = int(DUR * FPS)
    N = 160
    xs, ys = rng.uniform(0, W, N), rng.uniform(0, H, N)
    sp = rng.uniform(60, 220, N)
    sz = rng.uniform(1.5, 5, N)
    ph = rng.uniform(0, TAU, N)
    for f in range(n):
        t = f / FPS
        img = np.zeros((H, W, 3), np.float32)
        for i in range(N):
            y = (ys[i] - sp[i] * t) % (H + 40) - 20
            x = xs[i] + 40 * math.sin(ph[i] + t * 1.5) + 0.2 * sp[i] * t
            a = (0.5 + 0.5 * math.sin(ph[i] * 3 + t * 6)) * (max(y, 0) / H) ** 0.5
            cv2.circle(img, (int(x) % W, int(y)), int(sz[i]), (1.0 * a, 0.45 * a, 0.08 * a), -1, cv2.LINE_AA)
        yield _to8(img + cv2.GaussianBlur(img, (0, 0), 7) * 3)


def o_confetti():
    rng = np.random.default_rng(17)
    n = int(DUR * FPS)
    N = 220
    xs = rng.uniform(0, W, N)
    y0 = rng.uniform(-H, 0, N)
    sp = rng.uniform(180, 380, N)
    rot = rng.uniform(0, TAU, N)
    rs = rng.uniform(2, 8, N)
    pal = [(1, 0.2, 0.3), (1, 0.8, 0.1), (0.2, 0.8, 1), (0.4, 1, 0.4), (0.9, 0.3, 1), (1, 1, 1)]
    for f in range(n):
        t = f / FPS
        img = np.zeros((H, W, 3), np.float32)
        for i in range(N):
            y = y0[i] + sp[i] * t
            if y < -20 or y > H + 20:
                continue
            x = xs[i] + 50 * math.sin(rot[i] + t * 2)
            a = rot[i] + rs[i] * t
            flip = abs(math.cos(a * 1.3))
            w2, h2 = 9, 5 * flip + 1
            c, s = math.cos(a), math.sin(a)
            pts = np.array([[x + c * dx - s * dy, y + s * dx + c * dy] for dx, dy in
                            ((-w2, -h2), (w2, -h2), (w2, h2), (-w2, h2))], np.int32)
            col = pal[i % len(pal)]
            cv2.fillPoly(img, [pts], tuple(v * (0.6 + 0.4 * flip) for v in col), cv2.LINE_AA)
        yield _to8(img)


def o_hearts():
    rng = np.random.default_rng(18)
    n = int(DUR * FPS)
    N = 40
    xs, ys = rng.uniform(0, W, N), rng.uniform(0, H, N)
    sp = rng.uniform(70, 170, N)
    sz = rng.uniform(14, 45, N)
    ph = rng.uniform(0, TAU, N)
    tt = np.linspace(0, TAU, 40)
    hx = 16 * np.sin(tt) ** 3 / 16
    hy = -(13 * np.cos(tt) - 5 * np.cos(2 * tt) - 2 * np.cos(3 * tt) - np.cos(4 * tt)) / 16
    for f in range(n):
        t = f / FPS
        img = np.zeros((H, W, 3), np.float32)
        for i in range(N):
            y = (ys[i] - sp[i] * t) % (H + 100) - 50
            x = xs[i] + 30 * math.sin(ph[i] + t * 1.3)
            a = 0.5 + 0.5 * math.sin(ph[i] + t)
            pts = np.stack([x + hx * sz[i], y + hy * sz[i]], 1).astype(np.int32)
            cv2.fillPoly(img, [pts], (1.0 * a, 0.25 * a, 0.5 * a), cv2.LINE_AA)
        yield _to8(img + cv2.GaussianBlur(img, (0, 0), 8) * 1.5)


# =================== فيلم و VHS ===================

def o_dust():
    rng = np.random.default_rng(19)
    n = int(DUR * FPS)
    scratches = [(rng.uniform(0, W), rng.integers(0, n), rng.integers(8, 40)) for _ in range(10)]
    for f in range(n):
        img = np.zeros((H, W, 3), np.float32)
        for _ in range(rng.integers(5, 25)):
            x, y = rng.uniform(0, W), rng.uniform(0, H)
            if rng.random() < 0.7:
                cv2.circle(img, (int(x), int(y)), int(rng.uniform(1, 4)), (0.8,) * 3, -1, cv2.LINE_AA)
            else:
                pts = np.cumsum(rng.normal(0, 4, (8, 2)), 0) + [x, y]
                cv2.polylines(img, [pts.astype(np.int32)], False, (0.7,) * 3, 1, cv2.LINE_AA)
        for (x, f0, L) in scratches:
            if f0 <= f < f0 + L:
                xx = int(x + 3 * math.sin(f * 0.5))
                cv2.line(img, (xx, 0), (xx + rng.integers(-5, 5), H), (0.5,) * 3, 1, cv2.LINE_AA)
        img += rng.uniform(0, 0.04)  # وميض خفيف
        yield _to8(cv2.GaussianBlur(img, (0, 0), 0.7))


def o_vhs():
    rng = np.random.default_rng(20)
    n = int(DUR * FPS)
    h = 540
    scan = (np.arange(h) % 3 == 0).astype(np.float32)[:, None] * 0.06
    for f in range(n):
        img = np.zeros((h, 960), np.float32) + scan
        # خط التتبع المتحرك
        y0 = int((f * 7) % (h + 80)) - 40
        band = np.exp(-((np.arange(h) - y0) / 10.0) ** 2)[:, None]
        img += band * rng.random((h, 960)).astype(np.float32) * 0.6
        # ضوضاء أفقية متقطعة
        for _ in range(rng.integers(1, 5)):
            y = rng.integers(0, h)
            img[y:y + rng.integers(1, 3), :] += rng.random(960).astype(np.float32) * 0.35
        img += rng.random((h, 960)).astype(np.float32) * 0.05
        col = np.stack([img * 0.9, img * 1.0, img * 1.1], -1)
        yield _to8(_up(col))


def o_film_burn():
    n = int(3.0 * FPS)
    w, h = 480, 270
    rng = np.random.default_rng(21)
    base = cv2.GaussianBlur(rng.random((h, w)).astype(np.float32), (0, 0), 18)
    base = (base - base.min()) / (base.max() - base.min())
    gx, gy = _grid(w, h)
    for f in range(n):
        p = f / (n - 1)
        a = math.sin(p * math.pi) ** 1.5
        field = base * 0.6 + (1 - gx) * 0.4
        heat = np.clip((a * 1.15 - (1 - field)) * 2.5, 0, 1.25)
        img = np.stack([np.clip(heat * 1.4, 0, 1), np.clip(heat * 0.72, 0, 1) ** 1.4, np.clip(heat - 0.85, 0, 1) ** 2], -1)
        yield _to8(_up(img))


def o_fog():
    n = int(DUR * FPS)
    w, h = 480, 270
    rng = np.random.default_rng(22)
    big = np.zeros((h * 2, w * 3), np.float32)
    for s, a in ((40, 1.0), (18, 0.5), (8, 0.25)):
        big += cv2.GaussianBlur(rng.random(big.shape).astype(np.float32), (0, 0), s) * a
    big = (big - big.min()) / (big.max() - big.min())
    for f in range(n):
        t = f / n
        x1, x2 = int(t * w * 0.8), int(t * w * 1.6)
        a = big[0:h, x1:x1 + w]
        b = big[h // 3:h // 3 + h, x2:x2 + w]
        fog = np.clip((a * 0.6 + b * 0.6) - 0.45, 0, 1) * 1.6
        fog = fog * (0.4 + 0.6 * _grid(w, h)[1])
        yield _to8(_up(np.repeat(fog[..., None], 3, -1) * np.array([0.85, 0.88, 0.92], np.float32)))


def o_lightning():
    n = int(DUR * FPS)
    rng = np.random.default_rng(23)
    strikes = sorted(rng.choice(np.arange(10, n - 20), 3, replace=False))
    for f in range(n):
        img = np.zeros((H, W, 3), np.float32)
        for s in strikes:
            k = f - s
            if 0 <= k < 8:
                inten = [1.0, 0.3, 0.9, 0.5, 0.3, 0.15, 0.08, 0.03][k]
                img += inten * 0.35
                r2 = np.random.default_rng(int(s))
                x, y = r2.uniform(W * 0.2, W * 0.8), 0
                pts = [(x, y)]
                while y < H * 0.85:
                    x += r2.normal(0, 30)
                    y += r2.uniform(20, 60)
                    pts.append((x, y))
                cv2.polylines(img, [np.array(pts, np.int32)], False, (inten,) * 3, 3, cv2.LINE_AA)
        glow = cv2.GaussianBlur(img, (0, 0), 12)
        yield _to8((img + glow * 2) * np.array([0.85, 0.9, 1.0], np.float32))


OVERLAYS = {
    "leak-warm":    (o_leak_warm,    "تسريب ضوء دافئ"),
    "leak-golden":  (o_leak_golden,  "تسريب ضوء ذهبي"),
    "leak-red":     (o_leak_red,     "تسريب ضوء أحمر"),
    "leak-blue":    (o_leak_blue,    "تسريب ضوء أزرق"),
    "leak-rainbow": (o_leak_rainbow, "تسريب ضوء ملون"),
    "lens-flare":   (o_lens_flare,   "وهج عدسة يعبر الشاشة"),
    "light-rays":   (o_light_rays,   "أشعة ضوء"),
    "sparkles":     (o_sparkles,     "لمعات"),
    "bokeh":        (o_bokeh,        "بوكيه (دوائر ضوء ضبابية)"),
    "stars":        (o_stars,        "نجوم تتلألأ"),
    "snow":         (o_snow,         "ثلج"),
    "rain":         (o_rain,         "مطر"),
    "embers":       (o_embers,       "جمر متطاير"),
    "confetti":     (o_confetti,     "قصاصات احتفال"),
    "hearts":       (o_hearts,       "قلوب طائرة"),
    "dust":         (o_dust,         "غبار وخدوش فيلم قديم"),
    "vhs":          (o_vhs,          "VHS شريط فيديو قديم"),
    "film-burn":    (o_film_burn,    "حرق فيلم (انتقال)"),
    "fog":          (o_fog,          "ضباب"),
    "lightning":    (o_lightning,    "برق وعاصفة"),
}
