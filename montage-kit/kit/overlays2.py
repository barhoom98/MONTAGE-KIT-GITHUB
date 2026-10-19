"""
طبقات ضوئية جديدة 2026 — خلفية سوداء، تُدمج بوضع Screen.
"""
import math
import numpy as np
import cv2

from .overlays import W, H, FPS, DUR, TAU, _grid, _to8, _up, _smooth_path, _star


def o_speed_lines():
    """خطوط سرعة (أنمي) تتجه للمركز."""
    rng = np.random.default_rng(31)
    n = int(DUR * FPS)
    cx, cy = W / 2, H / 2
    for f in range(n):
        img = np.zeros((H, W, 3), np.float32)
        r2 = np.random.default_rng(f // 2 + 100)
        for _ in range(70):
            a = r2.uniform(0, TAU)
            r_out = 0.62 * W
            r_in = r2.uniform(0.2, 0.42) * W
            wdt = r2.uniform(0.004, 0.02)
            p0 = (cx + math.cos(a - wdt) * r_out, cy + math.sin(a - wdt) * r_out)
            p1 = (cx + math.cos(a + wdt) * r_out, cy + math.sin(a + wdt) * r_out)
            tip = (cx + math.cos(a) * r_in, cy + math.sin(a) * r_in)
            pts = np.array([p0, p1, tip], np.int32)
            v = r2.uniform(0.5, 1.0)
            cv2.fillPoly(img, [pts], (v, v, v), cv2.LINE_AA)
        yield _to8(img)


def o_neon_grid():
    """أرضية شبكة نيون (Retrowave) تتحرك للأمام."""
    n = int(DUR * FPS)
    horizon = int(H * 0.55)
    for f in range(n):
        t = f / FPS
        img = np.zeros((H, W, 3), np.float32)
        col = (1.0, 0.2, 0.85)
        for i in range(-30, 31):
            x0 = W / 2 + i * 40
            x1 = W / 2 + i * 260
            cv2.line(img, (int(x0), horizon), (int(x1), H), col, 2, cv2.LINE_AA)
        for k in range(20):
            z = ((k + (t * 1.5) % 1) / 20)
            y = horizon + (H - horizon) * z ** 2.2
            cv2.line(img, (0, int(y)), (W, int(y)), col, 2, cv2.LINE_AA)
        fade = np.clip((np.arange(H) - horizon) / (H - horizon), 0, 1)[:, None, None] ** 0.6
        img *= fade
        sun = np.zeros_like(img)
        sc, sr = horizon - 40, 240
        cv2.circle(sun, (W // 2, sc), sr, (1.0, 1.0, 1.0), -1, cv2.LINE_AA)
        g = np.clip((np.arange(H, dtype=np.float32) - (sc - sr)) / (2 * sr), 0, 1)[:, None]
        sun *= np.stack([np.ones_like(g), 0.9 - 0.65 * g, 0.25 + 0.45 * g], -1)
        for k in range(7):
            yy = sc - 30 + k * 26 - int((t * 20) % 26)
            cv2.rectangle(sun, (0, yy), (W, yy + 3 + k * 2), (0, 0, 0), -1)
        sun[horizon:] = 0
        img = img + sun * 0.8
        yield _to8(img + cv2.GaussianBlur(img, (0, 0), 8) * 1.5)


def o_fireworks():
    rng = np.random.default_rng(32)
    n = int(DUR * FPS)
    shows = []
    for i in range(7):
        t0 = rng.uniform(0, DUR - 1.8)
        cx, cy = rng.uniform(0.15, 0.85) * W, rng.uniform(0.15, 0.5) * H
        col = [(1, 0.3, 0.4), (1, 0.85, 0.3), (0.4, 0.8, 1), (0.6, 1, 0.5), (1, 0.5, 1)][i % 5]
        ang = rng.uniform(0, TAU, 90)
        sp = rng.uniform(260, 620, 90)
        shows.append((t0, cx, cy, col, ang, sp))
    for f in range(n):
        t = f / FPS
        img = np.zeros((H, W, 3), np.float32)
        for (t0, cx, cy, col, ang, sp) in shows:
            k = t - t0
            if 0 <= k < 1.8:
                fade = (1 - k / 1.8) ** 0.8 * 1.6
                for a, s in zip(ang, sp):
                    for tr in (0, 0.04, 0.08):
                        kk = max(0, k - tr)
                        x = cx + math.cos(a) * s * kk
                        y = cy + math.sin(a) * s * kk + 120 * kk * kk
                        v = fade * (1 - tr * 8)
                        cv2.circle(img, (int(x), int(y)), 3, tuple(c * v for c in col), -1, cv2.LINE_AA)
        yield _to8(img + cv2.GaussianBlur(img, (0, 0), 10) * 5)


def o_aurora():
    n = int(DUR * FPS)
    w, h = 480, 270
    gx, gy = _grid(w, h)
    for f in range(n):
        t = f / FPS
        img = np.zeros((h, w, 3), np.float32)
        for k, col in enumerate(((0.2, 1.0, 0.6), (0.3, 0.6, 1.0), (0.8, 0.3, 1.0))):
            yc = 0.3 + 0.08 * k + 0.08 * np.sin(gx * 6 + t * 0.6 + k) + 0.04 * np.sin(gx * 15 - t * 0.9)
            band = np.exp(-((gy - yc) / (0.05 + 0.03 * np.sin(gx * 4 + t))) ** 2)
            curtain = band * (0.6 + 0.4 * np.sin(gx * 60 + t * 2 + k)) * np.clip(1 - gy * 1.3, 0, 1)
            img += curtain[..., None] * np.array(col)
        img = cv2.GaussianBlur(img, (0, 0), 2)
        yield _to8(_up(img * 0.9))


def o_bubbles():
    rng = np.random.default_rng(33)
    n = int(DUR * FPS)
    N = 45
    xs, ys = rng.uniform(0, W, N), rng.uniform(0, H, N)
    sp = rng.uniform(60, 180, N)
    rr = rng.uniform(12, 50, N)
    ph = rng.uniform(0, TAU, N)
    for f in range(n):
        t = f / FPS
        img = np.zeros((H, W, 3), np.float32)
        for i in range(N):
            y = (ys[i] - sp[i] * t) % (H + 120) - 60
            x = xs[i] + 25 * math.sin(ph[i] + t * 1.8)
            r = int(rr[i])
            cv2.circle(img, (int(x), int(y)), r, (0.55, 0.75, 0.9), 2, cv2.LINE_AA)
            cv2.circle(img, (int(x - r * 0.35), int(y - r * 0.35)), max(2, r // 5), (0.9, 0.95, 1.0), -1, cv2.LINE_AA)
            cv2.ellipse(img, (int(x), int(y)), (r - 3, r - 3), 0, 200, 260, (0.9, 0.7, 1.0), 2, cv2.LINE_AA)
        yield _to8(img + cv2.GaussianBlur(img, (0, 0), 4))


def o_petals():
    rng = np.random.default_rng(34)
    n = int(DUR * FPS)
    N = 70
    xs, ys = rng.uniform(-200, W, N), rng.uniform(-H, H, N)
    sp = rng.uniform(70, 160, N)
    rot = rng.uniform(0, TAU, N)
    sz = rng.uniform(10, 22, N)
    for f in range(n):
        t = f / FPS
        img = np.zeros((H, W, 3), np.float32)
        for i in range(N):
            y = (ys[i] + sp[i] * t) % (H + 80) - 40
            x = (xs[i] + sp[i] * 0.6 * t + 40 * math.sin(rot[i] + t * 1.5)) % (W + 100) - 50
            a = rot[i] + t * 2
            flip = 0.35 + 0.65 * abs(math.sin(a * 1.3))
            cv2.ellipse(img, (int(x), int(y)), (int(sz[i]), int(sz[i] * 0.55 * flip)), math.degrees(a), 0, 360,
                        (1.0, 0.62, 0.78), -1, cv2.LINE_AA)
        yield _to8(img * 0.95)


def o_fireflies():
    rng = np.random.default_rng(35)
    n = int(DUR * FPS)
    N = 60
    bx, by = rng.uniform(0, W, N), rng.uniform(0.3 * H, H, N)
    ph = rng.uniform(0, TAU, N)
    for f in range(n):
        t = f / FPS
        img = np.zeros((H, W, 3), np.float32)
        for i in range(N):
            x = bx[i] + 60 * math.sin(ph[i] + t * 0.7) + 30 * math.sin(ph[i] * 2 + t * 1.9)
            y = by[i] + 40 * math.cos(ph[i] + t * 0.6)
            a = max(0, math.sin(ph[i] * 3 + t * 2.2)) ** 2
            cv2.circle(img, (int(x), int(y)), 4, (0.85 * a, 1.0 * a, 0.35 * a), -1, cv2.LINE_AA)
        yield _to8(img * 1.5 + cv2.GaussianBlur(img, (0, 0), 9) * 14)


def o_dust_motes():
    """ذرات غبار تطفو في شعاع ضوء."""
    rng = np.random.default_rng(36)
    n = int(DUR * FPS)
    N = 260
    xs, ys = rng.uniform(0, W, N), rng.uniform(0, H, N)
    depth = rng.uniform(0.2, 1, N)
    ph = rng.uniform(0, TAU, N)
    gx, gy = _grid(W // 4, H // 4)
    beam = np.clip(1 - np.abs((gx - 0.25) - (gy * 0.55)) / 0.22, 0, 1) ** 2 * 0.25
    beam = _up(np.repeat(beam[..., None], 3, -1).astype(np.float32) * np.array([1.0, 0.9, 0.7], np.float32))
    for f in range(n):
        t = f / FPS
        img = beam.copy()
        for i in range(N):
            x = (xs[i] + 20 * depth[i] * t + 15 * math.sin(ph[i] + t * 0.5)) % W
            y = (ys[i] + 10 * math.cos(ph[i] + t * 0.4) - 8 * t) % H
            v = 0.3 + 0.7 * depth[i] * (0.6 + 0.4 * math.sin(ph[i] + t * 3))
            cv2.circle(img, (int(x), int(y)), max(1, int(3 * depth[i])), (v, v * 0.95, v * 0.8), -1, cv2.LINE_AA)
        yield _to8(cv2.GaussianBlur(img, (0, 0), 1.0))


def o_anamorphic():
    """خطوط ضوء أفقية زرقاء (أنامورفيك)."""
    rng = np.random.default_rng(37)
    n = int(DUR * FPS)
    w, h = 960, 540
    srcs = [(rng.uniform(0.1, 0.9), rng.uniform(0.2, 0.8), rng.uniform(0.4, 1.0), rng.uniform(0, TAU)) for _ in range(5)]
    gx, gy = _grid(w, h)
    for f in range(n):
        t = f / FPS
        img = np.zeros((h, w, 3), np.float32)
        for (x0, y0, a, ph) in srcs:
            x = x0 + 0.08 * math.sin(t * 0.5 + ph)
            inten = a * (0.6 + 0.4 * math.sin(t * 1.3 + ph))
            streak = np.exp(-((gy - y0) / 0.004) ** 2) * np.exp(-np.abs(gx - x) / 0.35) * inten
            core = np.exp(-(((gx - x) * 1.78) ** 2 + (gy - y0) ** 2) / 0.0008) * inten
            img += streak[..., None] * np.array([0.3, 0.6, 1.0]) + core[..., None] * np.array([0.8, 0.9, 1.0])
        yield _to8(_up(img + cv2.GaussianBlur(img, (0, 0), 3)))


def o_shooting_stars():
    rng = np.random.default_rng(38)
    n = int(DUR * FPS)
    shots = [(rng.uniform(0, DUR - 0.8), rng.uniform(0.2, 1.0) * W, rng.uniform(0, 0.4) * H) for _ in range(8)]
    for f in range(n):
        t = f / FPS
        img = np.zeros((H, W, 3), np.float32)
        for (t0, x0, y0) in shots:
            k = t - t0
            if 0 <= k < 0.8:
                x, y = x0 - 1400 * k, y0 + 600 * k
                for j in range(14):
                    xx, yy = x + j * 18, y - j * 7.7
                    v = (1 - j / 14) * (1 - k / 0.8)
                    cv2.circle(img, (int(xx), int(yy)), max(1, 3 - j // 5), (v, v, v * 0.9 + 0.1), -1, cv2.LINE_AA)
        yield _to8(img + cv2.GaussianBlur(img, (0, 0), 5) * 2)


def o_glitter():
    rng = np.random.default_rng(39)
    n = int(DUR * FPS)
    N = 600
    xs, ys = rng.uniform(0, W, N), rng.uniform(0, H, N)
    ph = rng.uniform(0, TAU, N)
    sp = rng.uniform(2, 6, N)
    pal = np.array([(1, 0.85, 0.5), (1, 1, 1), (1, 0.6, 0.8), (0.7, 0.85, 1)])
    for f in range(n):
        t = f / FPS
        img = np.zeros((H, W, 3), np.float32)
        a = np.clip(np.sin(ph + sp * t), 0, 1) ** 8
        for i in np.where(a > 0.05)[0]:
            c = tuple(pal[i % 4] * a[i])
            if a[i] > 0.7:
                _star(img, xs[i], ys[i] + 20 * t, 9 * a[i], pal[i % 4], a[i])
            else:
                cv2.circle(img, (int(xs[i]), int(ys[i] + 20 * t) % H), 2, c, -1, cv2.LINE_AA)
        yield _to8(img + cv2.GaussianBlur(img, (0, 0), 4) * 1.5)


def o_crt():
    """خطوط شاشة قديمة CRT مع وميض."""
    n = int(DUR * FPS)
    rng = np.random.default_rng(40)
    base = np.zeros((H, W, 3), np.float32)
    base[::4] = 0.12
    base[1::4] = 0.06
    gx, gy = _grid(W, H)
    vig = (1 - np.clip(((gx - 0.5) * 2) ** 2 + ((gy - 0.5) * 2) ** 2, 0, 1)) * 0.0
    for f in range(n):
        t = f / FPS
        img = base * (0.8 + 0.2 * math.sin(t * 40)) + vig[..., None]
        y0 = int((t * 0.25 % 1) * H)
        img[max(0, y0 - 40):y0] += 0.08
        yield _to8(img)


def o_hologram():
    n = int(DUR * FPS)
    rng = np.random.default_rng(41)
    for f in range(n):
        t = f / FPS
        img = np.zeros((H, W, 3), np.float32)
        img[::3] = (0.0, 0.25, 0.3)
        for _ in range(3):
            y = int((rng.random() + t * 0.3) % 1 * H)
            img[y:y + rng.integers(2, 10)] += (0.0, 0.5, 0.6)
        if rng.random() < 0.1:
            img += (0.0, 0.15, 0.18)
        yield _to8(img)


def o_light_flicker():
    """وميض ضوء كأنه من شمعة/لمبة."""
    n = int(DUR * FPS)
    rng = np.random.default_rng(42)
    w, h = 480, 270
    gx, gy = _grid(w, h)
    glow = np.exp(-(((gx - 0.5) * 1.78) ** 2 + (gy - 0.15) ** 2) / 0.25)
    v = 0.6
    for f in range(n):
        v = 0.85 * v + 0.15 * rng.uniform(0.3, 1.0)
        if rng.random() < 0.03:
            v = 0.1
        img = glow[..., None] * np.array([1.0, 0.75, 0.45]) * v * 0.7
        yield _to8(_up(img.astype(np.float32)))


def o_rain_glass():
    """قطرات على زجاج."""
    rng = np.random.default_rng(43)
    n = int(DUR * FPS)
    N = 160
    xs, ys = rng.uniform(0, W, N), rng.uniform(0, H, N)
    rr = rng.uniform(4, 14, N)
    fall = rng.random(N) < 0.2
    sp = rng.uniform(80, 300, N)
    for f in range(n):
        t = f / FPS
        img = np.zeros((H, W, 3), np.float32)
        for i in range(N):
            y = (ys[i] + (sp[i] * t if fall[i] else 0)) % H
            r = int(rr[i])
            cv2.ellipse(img, (int(xs[i]), int(y)), (r, int(r * 1.2)), 0, 180, 360, (0.25, 0.28, 0.32), 2, cv2.LINE_AA)
            cv2.circle(img, (int(xs[i] - r * 0.3), int(y - r * 0.4)), max(1, r // 4), (0.7, 0.75, 0.8), -1, cv2.LINE_AA)
            if fall[i]:
                cv2.line(img, (int(xs[i]), int(y - r)), (int(xs[i]), int(y - r - 80)), (0.12, 0.13, 0.15), max(1, r // 3), cv2.LINE_AA)
        yield _to8(cv2.GaussianBlur(img, (0, 0), 1.0))


def o_prism():
    """انكسار قوس قزح يتحرك."""
    n = int(DUR * FPS)
    w, h = 480, 270
    gx, gy = _grid(w, h)
    for f in range(n):
        t = f / FPS
        pos = 0.2 + 0.6 * (0.5 + 0.5 * math.sin(t * 0.6))
        u = (gx + gy * 0.5 - pos) / 0.18
        band = np.exp(-u ** 2)
        hue = np.clip(u * 0.5 + 0.5, 0, 1)
        r = np.clip(1.5 - np.abs(hue * 4 - 0.5) , 0, 1)
        g = np.clip(1.5 - np.abs(hue * 4 - 2.0), 0, 1)
        b = np.clip(1.5 - np.abs(hue * 4 - 3.5), 0, 1)
        img = np.stack([r, g, b], -1) * band[..., None] * 0.6
        yield _to8(_up(img.astype(np.float32)))


def o_smoke():
    n = int(DUR * FPS)
    w, h = 480, 270
    rng = np.random.default_rng(44)
    big = np.zeros((h * 3, w), np.float32)
    for s, a in ((25, 1.0), (10, 0.5), (4, 0.2)):
        big += cv2.GaussianBlur(rng.random(big.shape).astype(np.float32), (0, 0), s) * a
    big = (big - big.min()) / (big.max() - big.min())
    gx, gy = _grid(w, h)
    for f in range(n):
        t = f / n
        y1 = int((1 - t) * h * 1.6)
        a = big[y1:y1 + h]
        warp = cv2.remap(a, (gx * w + 15 * np.sin(gy * 8 + t * 6)).astype(np.float32), (gy * h).astype(np.float32),
                         cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        sm = np.clip(warp - 0.5, 0, 1) * 2.2 * (gy ** 1.2)
        yield _to8(_up(np.repeat(sm[..., None], 3, -1) * np.array([0.8, 0.82, 0.88], np.float32)))


def o_halation():
    """توهج أحمر ناعم حول الأطراف (طابع فيلم)."""
    n = int(DUR * FPS)
    w, h = 480, 270
    gx, gy = _grid(w, h)
    r = np.sqrt(((gx - 0.5) * 1.6) ** 2 + (gy - 0.5) ** 2)
    for f in range(n):
        t = f / FPS
        ring = np.clip((r - 0.45) / 0.4, 0, 1) ** 1.5 * (0.75 + 0.25 * math.sin(t * 1.5))
        img = ring[..., None] * np.array([0.9, 0.25, 0.12])
        yield _to8(_up(img.astype(np.float32)))


def o_y2k_stars():
    rng = np.random.default_rng(45)
    n = int(DUR * FPS)
    N = 26
    xs, ys = rng.uniform(0, W, N), rng.uniform(0, H, N)
    sz = rng.uniform(20, 60, N)
    ph = rng.uniform(0, TAU, N)
    for f in range(n):
        t = f / FPS
        img = np.zeros((H, W, 3), np.float32)
        for i in range(N):
            a = 0.5 + 0.5 * math.sin(ph[i] + t * 2.5)
            s = sz[i] * (0.7 + 0.3 * a)
            x, y = xs[i], ys[i] - 12 * t
            col = (0.85, 0.9, 1.0) if i % 2 else (1.0, 0.75, 0.95)
            _star(img, x, y, s, col, a)
            _star(img, x, y, s * 0.45, (1, 1, 1), a)
        yield _to8(img + cv2.GaussianBlur(img, (0, 0), 7) * 1.8)


OVERLAYS2 = {
    "speed-lines":    (o_speed_lines,    "خطوط سرعة أنمي"),
    "neon-grid":      (o_neon_grid,      "شبكة نيون ريترو مع شمس"),
    "fireworks":      (o_fireworks,      "ألعاب نارية"),
    "aurora":         (o_aurora,         "شفق قطبي"),
    "bubbles":        (o_bubbles,        "فقاعات صابون"),
    "petals":         (o_petals,         "بتلات ورد متطايرة"),
    "fireflies":      (o_fireflies,      "يراعات مضيئة"),
    "dust-motes":     (o_dust_motes,     "ذرات غبار في شعاع ضوء"),
    "anamorphic":     (o_anamorphic,     "خطوط ضوء أنامورفيك زرقاء"),
    "shooting-stars": (o_shooting_stars, "شهب"),
    "glitter":        (o_glitter,        "جليتر لامع"),
    "crt":            (o_crt,            "خطوط شاشة CRT"),
    "hologram":       (o_hologram,       "هولوغرام"),
    "light-flicker":  (o_light_flicker,  "وميض لمبة/شمعة"),
    "rain-glass":     (o_rain_glass,     "قطرات على زجاج"),
    "prism":          (o_prism,          "انكسار قوس قزح"),
    "smoke":          (o_smoke,          "دخان صاعد"),
    "halation":       (o_halation,       "هالة فيلم حمراء"),
    "y2k-stars":      (o_y2k_stars,      "نجوم Y2K لامعة"),
}
