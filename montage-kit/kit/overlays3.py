"""
طبقات ضوئية — الدفعة 3 (خلفية سوداء، دمج Screen).
"""
import math
import numpy as np
import cv2

from .overlays import W, H, FPS, DUR, TAU, _grid, _to8, _up, _smooth_path, _star


def o_hyperspace():
    """قفزة فضائية: نجوم تتمدد لخطوط نحو الكاميرا."""
    rng = np.random.default_rng(51)
    n = int(DUR * FPS)
    N = 500
    ang = rng.uniform(0, TAU, N)
    z = rng.uniform(0.05, 1, N)
    cx, cy = W / 2, H / 2
    for f in range(n):
        t = f / FPS
        speed = 0.15 + 1.2 * min(1, t / 2.5) ** 2
        img = np.zeros((H, W, 3), np.float32)
        z = z - speed / FPS
        dead = z <= 0.02
        z[dead] = 1.0
        ang[dead] = rng.uniform(0, TAU, dead.sum())
        r1 = 55 / z
        r0 = 55 / np.minimum(1, z + speed * 0.12)
        for a, ra, rb, zz in zip(ang, r0, r1, z):
            if rb > W:
                continue
            p0 = (int(cx + math.cos(a) * ra), int(cy + math.sin(a) * ra))
            p1 = (int(cx + math.cos(a) * rb), int(cy + math.sin(a) * rb))
            v = min(1.0, (1 - zz) * 1.4)
            cv2.line(img, p0, p1, (0.75 * v, 0.88 * v, v), max(1, int(3 * (1 - zz))), cv2.LINE_AA)
        yield _to8(img + cv2.GaussianBlur(img, (0, 0), 4) * 1.2)


def o_caustics():
    """انعكاسات ماء متموجة (تحت الماء / مسبح)."""
    n = int(DUR * FPS)
    w, h = 480, 270
    gx, gy = _grid(w, h)
    for f in range(n):
        t = f / FPS
        v = np.zeros((h, w), np.float32)
        for k, (fx, fy, sp) in enumerate(((7, 5, 0.8), (5, 8, -0.6), (9, 4, 0.5), (4, 6, -0.9))):
            v += np.sin(gx * fx * TAU / 2 + np.sin(gy * fy + t * sp * 2) * 1.5 + t * sp + k)
        c = np.clip(1 - np.abs(v) / 1.2, 0, 1) ** 4
        img = c[..., None] * np.array([0.55, 0.85, 1.0], np.float32) * 0.8
        yield _to8(_up(cv2.GaussianBlur(img, (0, 0), 1.2)))


def o_falling_leaves():
    rng = np.random.default_rng(52)
    n = int(DUR * FPS)
    N = 45
    xs, ys = rng.uniform(0, W, N), rng.uniform(-H, H, N)
    sp = rng.uniform(80, 170, N)
    rot = rng.uniform(0, TAU, N)
    sz = rng.uniform(22, 44, N)
    pal = [(0.95, 0.55, 0.15), (0.85, 0.3, 0.1), (0.95, 0.75, 0.2), (0.6, 0.35, 0.12)]
    for f in range(n):
        t = f / FPS
        img = np.zeros((H, W, 3), np.float32)
        for i in range(N):
            y = (ys[i] + sp[i] * t) % (H + 80) - 40
            x = (xs[i] + 60 * math.sin(rot[i] + t * 1.2) + 20 * t) % (W + 60) - 30
            a = rot[i] + t * 1.8
            flip = 0.3 + 0.7 * abs(math.sin(a * 1.1))
            L, Wd = sz[i], sz[i] * 0.45 * flip
            pts = []
            for k in range(16):
                u = k / 15 * math.pi
                pts.append((math.cos(u) * L, math.sin(u) * Wd))
            for k in range(16):
                u = math.pi + k / 15 * math.pi
                pts.append((math.cos(u) * L, math.sin(u) * Wd))
            ca, sa = math.cos(a), math.sin(a)
            P = np.array([(x + px * ca - py * sa, y + px * sa + py * ca) for px, py in pts], np.int32)
            col = pal[i % 4]
            cv2.fillPoly(img, [P], col, cv2.LINE_AA)
            cv2.line(img, tuple(P[0]), tuple(P[16]), tuple(c * 0.6 for c in col), 1, cv2.LINE_AA)
        yield _to8(img)


def o_sun_glare():
    """وهج شمس في الزاوية مع حلقات (للطبيعة والسفر)."""
    n = int(DUR * FPS)
    w, h = 960, 540
    gx, gy = _grid(w, h)
    for f in range(n):
        t = f / FPS
        sx, sy = 0.82 + 0.02 * math.sin(t * 0.4), 0.12
        dx, dy = (gx - sx) * 1.78, gy - sy
        r2 = dx * dx + dy * dy
        flick = 0.9 + 0.1 * math.sin(t * 3.1) * math.sin(t * 1.7)
        img = np.exp(-r2 / 0.004)[..., None] * np.array([1.0, 0.97, 0.9])
        img += np.exp(-r2 / 0.08)[..., None] * np.array([1.0, 0.75, 0.4]) * 0.55
        ang = np.arctan2(dy, dx)
        rays = (np.clip(np.sin(ang * 14 + t * 0.3), 0, 1) ** 8) * np.exp(-np.sqrt(r2) / 0.5) * 0.35
        img += rays[..., None] * np.array([1.0, 0.85, 0.6])
        for s, rr, col in ((0.5, 0.05, (0.5, 1.0, 0.6)), (0.95, 0.08, (0.9, 0.6, 1.0)), (1.35, 0.03, (1.0, 0.7, 0.3))):
            gpx, gpy = sx + (0.5 - sx) * 2 * s, sy + (0.5 - sy) * 2 * s
            d2 = ((gx - gpx) * 1.78) ** 2 + (gy - gpy) ** 2
            ring = np.exp(-((np.sqrt(d2) - rr) / 0.006) ** 2) * 0.25 + np.exp(-d2 / (rr * rr)) * 0.08
            img += ring[..., None] * np.array(col)
        yield _to8(_up((img * flick).astype(np.float32)))


def o_god_rays():
    """أشعة ضوء نازلة من الأعلى بين الأشجار."""
    n = int(DUR * FPS)
    w, h = 480, 270
    gx, gy = _grid(w, h)
    rng = np.random.default_rng(53)
    beams = [(rng.uniform(0.1, 0.9), rng.uniform(0.02, 0.06), rng.uniform(0, TAU), rng.uniform(0.4, 1.0)) for _ in range(7)]
    for f in range(n):
        t = f / FPS
        img = np.zeros((h, w), np.float32)
        for (x0, wd, ph, a) in beams:
            xc = x0 + (gy * 0.35) + 0.02 * math.sin(t * 0.5 + ph)
            img += np.exp(-((gx - xc) / (wd * (1 + gy))) ** 2) * a * (0.7 + 0.3 * math.sin(t * 0.8 + ph))
        img *= np.clip(1.2 - gy, 0, 1)
        col = img[..., None] * np.array([1.0, 0.92, 0.72], np.float32) * 0.45
        yield _to8(_up(cv2.GaussianBlur(col, (0, 0), 2)))


def o_concert_beams():
    """أضواء مسرح تتحرك (حفلات)."""
    n = int(DUR * FPS)
    w, h = 480, 270
    gx, gy = _grid(w, h)
    cols = [(1.0, 0.2, 0.6), (0.2, 0.6, 1.0), (0.6, 0.2, 1.0), (1.0, 0.6, 0.1), (0.2, 1.0, 0.7)]
    for f in range(n):
        t = f / FPS
        img = np.zeros((h, w, 3), np.float32)
        for i, col in enumerate(cols):
            ox = (i + 0.5) / len(cols)
            ang = 0.45 * math.sin(t * (0.8 + i * 0.17) + i * 1.3)
            dx, dy = gx - ox, gy - 1.05
            a = np.arctan2(dx, -dy)
            beam = np.exp(-((a - ang) / 0.06) ** 2) * np.clip(1.1 + dy, 0, 1)
            img += beam[..., None] * np.array(col) * 0.6
        haze = cv2.GaussianBlur(img, (0, 0), 6)
        yield _to8(_up(img + haze * 0.6))


def o_laser_show():
    n = int(DUR * FPS)
    for f in range(n):
        t = f / FPS
        img = np.zeros((H, W, 3), np.float32)
        ox, oy = W / 2, H * 0.08
        for i in range(14):
            a = math.pi / 2 + 0.9 * math.sin(t * 1.3 + i * 0.45) * (1 if i % 2 else -1)
            ex, ey = ox + math.cos(a) * W, oy + math.sin(a) * W
            col = (0.2, 1.0, 0.3) if i % 3 == 0 else ((1.0, 0.1, 0.3) if i % 3 == 1 else (0.2, 0.5, 1.0))
            cv2.line(img, (int(ox), int(oy)), (int(ex), int(ey)), col, 2, cv2.LINE_AA)
        yield _to8(img * 0.9 + cv2.GaussianBlur(img, (0, 0), 6) * 2.5)


def o_money_rain():
    rng = np.random.default_rng(54)
    n = int(DUR * FPS)
    N = 40
    xs, ys = rng.uniform(0, W, N), rng.uniform(-H, H, N)
    sp = rng.uniform(140, 260, N)
    rot = rng.uniform(0, TAU, N)
    for f in range(n):
        t = f / FPS
        img = np.zeros((H, W, 3), np.float32)
        for i in range(N):
            y = (ys[i] + sp[i] * t) % (H + 120) - 60
            x = xs[i] + 50 * math.sin(rot[i] + t * 1.5)
            a = rot[i] + t * 2.2
            flip = 0.25 + 0.75 * abs(math.cos(a * 1.4))
            w2, h2 = 46, 20 * flip
            ca, sa = math.cos(a * 0.5), math.sin(a * 0.5)
            pts = np.array([[x + ca * dx - sa * dy, y + sa * dx + ca * dy] for dx, dy in
                            ((-w2, -h2), (w2, -h2), (w2, h2), (-w2, h2))], np.int32)
            cv2.fillPoly(img, [pts], (0.45 * flip + 0.2, 0.75 * flip + 0.2, 0.4 * flip + 0.15), cv2.LINE_AA)
            cv2.polylines(img, [pts], True, (0.2, 0.45, 0.2), 2, cv2.LINE_AA)
            c = pts.mean(0).astype(int)
            cv2.circle(img, tuple(c), int(h2 * 0.6) + 1, (0.25, 0.5, 0.25), 2, cv2.LINE_AA)
        yield _to8(img)


def o_magic_dust():
    """غبار سحري يدور حلزونياً."""
    rng = np.random.default_rng(55)
    n = int(DUR * FPS)
    N = 300
    ph = rng.uniform(0, TAU, N)
    rad = rng.uniform(0.05, 0.45, N)
    sp = rng.uniform(0.4, 1.2, N)
    life = rng.uniform(0, 1, N)
    for f in range(n):
        t = f / FPS
        img = np.zeros((H, W, 3), np.float32)
        for i in range(N):
            a = ph[i] + t * sp[i]
            r = rad[i] * (0.8 + 0.2 * math.sin(t + i))
            x = W / 2 + math.cos(a) * r * W
            y = H / 2 + math.sin(a) * r * W * 0.35 - (t * 40 + life[i] * H) % H + H / 2
            v = 0.5 + 0.5 * math.sin(t * 4 + i)
            cv2.circle(img, (int(x), int(y) % H), 3, (1.0 * v, 0.85 * v, 0.45 * v), -1, cv2.LINE_AA)
        yield _to8(img * 1.4 + cv2.GaussianBlur(img, (0, 0), 7) * 6)


def o_light_orbs():
    """كرات ضوء ملونة تطفو ببطء."""
    rng = np.random.default_rng(56)
    n = int(DUR * FPS)
    w, h = 480, 270
    N = 14
    pal = [(1.0, 0.5, 0.7), (0.5, 0.7, 1.0), (1.0, 0.8, 0.4), (0.6, 1.0, 0.8)]
    paths = [(rng.uniform(0, 1), rng.uniform(0, 1), _smooth_path(rng, n, 3, 0.15), _smooth_path(rng, n, 3, 0.15),
              rng.uniform(0.04, 0.12), pal[i % 4]) for i in range(N)]
    gx, gy = _grid(w, h)
    for f in range(n):
        img = np.zeros((h, w, 3), np.float32)
        for (x0, y0, px, py, r, col) in paths:
            x, y = x0 + 0.15 * px[f], y0 + 0.15 * py[f]
            d2 = ((gx - x) * 1.78) ** 2 + (gy - y) ** 2
            img += np.exp(-d2 / (r * r))[..., None] * np.array(col) * 0.5
        yield _to8(_up(img))


def o_hud():
    """واجهة مستقبلية (HUD): دوائر ومؤشرات تدور."""
    n = int(DUR * FPS)
    cx, cy = W // 2, H // 2
    col = (0.25, 0.9, 1.0)
    for f in range(n):
        t = f / FPS
        img = np.zeros((H, W, 3), np.float32)
        for k, (r, w, sp, a0, a1) in enumerate(((320, 2, 0.5, 0, 300), (360, 6, -0.3, 20, 90), (360, 6, -0.3, 200, 270),
                                                  (250, 1, 1.0, 0, 360), (420, 2, 0.15, 0, 40), (420, 2, 0.15, 180, 220))):
            rot = math.degrees(t * sp)
            cv2.ellipse(img, (cx, cy), (r, r), rot, a0, a1, col, w, cv2.LINE_AA)
        for i in range(36):
            a = math.radians(i * 10 + t * 20)
            r0, r1 = 280, 290 if i % 3 else 300
            cv2.line(img, (int(cx + math.cos(a) * r0), int(cy + math.sin(a) * r0)),
                     (int(cx + math.cos(a) * r1), int(cy + math.sin(a) * r1)), col, 1, cv2.LINE_AA)
        L = 30
        for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            x0, y0 = cx + sx * 140, cy + sy * 140
            cv2.line(img, (x0, y0), (x0 - sx * L, y0), col, 3, cv2.LINE_AA)
            cv2.line(img, (x0, y0), (x0, y0 - sy * L), col, 3, cv2.LINE_AA)
        y = int(cy - 300 + (t * 120) % 600)
        cv2.line(img, (cx - 300, y), (cx + 300, y), (0.15, 0.5, 0.6), 1, cv2.LINE_AA)
        for i in range(8):
            bh = int(20 + 60 * abs(math.sin(t * 2 + i)))
            cv2.rectangle(img, (80 + i * 18, H - 80 - bh), (92 + i * 18, H - 80), col, -1)
        yield _to8(img * 0.85 + cv2.GaussianBlur(img, (0, 0), 5) * 1.2)


def o_confetti_burst():
    """انفجار قصاصات من الأسفل (لحظة احتفال)."""
    rng = np.random.default_rng(57)
    n = int(DUR * FPS)
    N = 260
    side = rng.integers(0, 2, N)
    x0 = np.where(side == 0, W * 0.12, W * 0.88)
    ang = np.radians(np.where(side == 0, -62, -118) + rng.normal(0, 16, N))
    spd = rng.uniform(700, 2100, N)
    vx = np.cos(ang) * spd
    vy = np.sin(ang) * spd
    delay = rng.uniform(0, 0.25, N)
    rot = rng.uniform(0, TAU, N)
    pal = [(1, 0.2, 0.35), (1, 0.85, 0.1), (0.2, 0.75, 1), (0.4, 1, 0.45), (0.9, 0.35, 1), (1, 1, 1)]
    for f in range(n):
        t = f / FPS
        img = np.zeros((H, W, 3), np.float32)
        for i in range(N):
            k = t - delay[i]
            if k < 0:
                continue
            drag = (1 - math.exp(-k * 2.2)) / 2.2
            x = x0[i] + vx[i] * drag + 40 * math.sin(rot[i] + k * 3) * min(1, k)
            y = H + 10 + vy[i] * drag + 140 * k * k
            if y > H + 20 or y < -40:
                continue
            a = rot[i] + k * 7
            flip = abs(math.cos(a))
            w2, h2 = 8, 4 * flip + 1
            c, s = math.cos(a * 0.6), math.sin(a * 0.6)
            pts = np.array([[x + c * dx - s * dy, y + s * dx + c * dy] for dx, dy in
                            ((-w2, -h2), (w2, -h2), (w2, h2), (-w2, h2))], np.int32)
            cv2.fillPoly(img, [pts], tuple(v * (0.55 + 0.45 * flip) for v in pal[i % 6]), cv2.LINE_AA)
        yield _to8(img)


def o_sparks():
    """شرر لحام يتطاير."""
    rng = np.random.default_rng(58)
    n = int(DUR * FPS)
    parts = []
    for f in range(n):
        t = f / FPS
        for _ in range(18):
            a = rng.uniform(-math.pi * 0.95, -math.pi * 0.05)
            sp = rng.uniform(300, 900)
            parts.append([W * 0.5 + rng.normal(0, 8), H * 0.62, math.cos(a) * sp, math.sin(a) * sp, rng.uniform(0.4, 1.2)])
        img = np.zeros((H, W, 3), np.float32)
        alive = []
        for p in parts:
            x, y, vx, vy, life = p
            nx, ny = x + vx / FPS, y + vy / FPS
            p[0], p[1], p[3], p[4] = nx, ny, vy + 900 / FPS, life - 1 / FPS
            if p[4] > 0 and 0 < nx < W and ny < H:
                v = min(1, p[4])
                cv2.line(img, (int(x), int(y)), (int(nx), int(ny)), (1.0 * v, 0.7 * v, 0.25 * v), 2, cv2.LINE_AA)
                alive.append(p)
        parts = alive
        cv2.circle(img, (W // 2, int(H * 0.62)), 10, (1, 0.95, 0.8), -1, cv2.LINE_AA)
        yield _to8(img + cv2.GaussianBlur(img, (0, 0), 6) * 2)


def o_snow_heavy():
    rng = np.random.default_rng(59)
    n = int(DUR * FPS)
    N = 900
    depth = rng.uniform(0.15, 1.0, N)
    xs, ys = rng.uniform(0, W, N), rng.uniform(0, H, N)
    ph = rng.uniform(0, TAU, N)
    for f in range(n):
        t = f / FPS
        img = np.zeros((H, W, 3), np.float32)
        for i in range(N):
            d = depth[i]
            y = (ys[i] + 220 * d * t) % (H + 20) - 10
            x = (xs[i] + 140 * t * d + 25 * math.sin(ph[i] + t * 1.5 * d)) % W
            v = 0.35 + 0.65 * d
            cv2.circle(img, (int(x), int(y)), max(1, int(6 * d)), (v, v, v), -1, cv2.LINE_AA)
        yield _to8(cv2.GaussianBlur(img, (0, 0), 1.4) * 1.1)


def o_lens_dirt():
    """أوساخ عدسة وبقع ضوء تظهر مع الوهج (تُستخدم مع light leak)."""
    rng = np.random.default_rng(60)
    n = int(DUR * FPS)
    w, h = 960, 540
    base = np.zeros((h, w), np.float32)
    for _ in range(140):
        x, y, r = rng.uniform(0, w), rng.uniform(0, h), rng.uniform(4, 40)
        cv2.circle(base, (int(x), int(y)), int(r), float(rng.uniform(0.15, 0.6)), -1, cv2.LINE_AA)
    for _ in range(25):
        pts = np.cumsum(rng.normal(0, 12, (12, 2)), 0) + rng.uniform(0, [w, h])
        cv2.polylines(base, [pts.astype(np.int32)], False, 0.3, 2, cv2.LINE_AA)
    base = cv2.GaussianBlur(base, (0, 0), 3)
    gx, gy = _grid(w, h)
    for f in range(n):
        t = f / FPS
        lx, ly = 0.2 + 0.6 * (0.5 + 0.5 * math.sin(t * 0.5)), 0.3
        light = np.exp(-(((gx - lx) * 1.78) ** 2 + (gy - ly) ** 2) / 0.12)
        img = (base * light)[..., None] * np.array([1.0, 0.9, 0.75], np.float32) * 1.2
        yield _to8(_up(img))


OVERLAYS3 = {
    "hyperspace":     (o_hyperspace,     "قفزة فضائية (نجوم تتمدد)"),
    "caustics":       (o_caustics,       "انعكاسات ماء (تحت الماء)"),
    "falling-leaves": (o_falling_leaves, "أوراق خريف تتساقط"),
    "sun-glare":      (o_sun_glare,      "وهج شمس بحلقات عدسة"),
    "god-rays":       (o_god_rays,       "أشعة نازلة بين الأشجار"),
    "concert-beams":  (o_concert_beams,  "أضواء مسرح متحركة"),
    "laser-show":     (o_laser_show,     "عرض ليزر"),
    "money-rain":     (o_money_rain,     "مطر فلوس"),
    "magic-dust":     (o_magic_dust,     "غبار سحري حلزوني"),
    "light-orbs":     (o_light_orbs,     "كرات ضوء ملونة"),
    "hud":            (o_hud,            "واجهة مستقبلية HUD"),
    "confetti-burst": (o_confetti_burst, "انفجار قصاصات احتفال"),
    "sparks":         (o_sparks,         "شرر لحام"),
    "snow-heavy":     (o_snow_heavy,     "ثلج كثيف مع ريح"),
    "lens-dirt":      (o_lens_dirt,      "أوساخ عدسة مع ضوء"),
}
