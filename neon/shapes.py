"""
تعريف أشكال الستيكرات.

كل ستيكر = قائمة خطوط (polylines). كل خط مصفوفة نقاط (x, y)
في مساحة من -1 إلى 1، والمحور y للأسفل (مثل الشاشة).
الخطوط تُرسم بالترتيب، فترتيبها هو ترتيب ظهورها في حركة الرسم.
"""
import math
import numpy as np

TAU = 2 * math.pi


# ---------- أدوات بناء الخطوط ----------

def line(p0, p1, n=24):
    t = np.linspace(0, 1, n)[:, None]
    return (1 - t) * np.array(p0, float) + t * np.array(p1, float)


def poly(points, closed=False, n_per_seg=20):
    pts = list(points) + ([points[0]] if closed else [])
    segs = [line(pts[i], pts[i + 1], n_per_seg) for i in range(len(pts) - 1)]
    return np.vstack([s if i == 0 else s[1:] for i, s in enumerate(segs)])


def arc(cx, cy, rx, ry, a0, a1, n=90):
    a = np.linspace(math.radians(a0), math.radians(a1), n)
    return np.stack([cx + rx * np.cos(a), cy + ry * np.sin(a)], axis=1)


def circle(cx, cy, r, start=-90, n=120):
    return arc(cx, cy, r, r, start, start + 360, n)


def dot(cx, cy, r=0.05):
    return circle(cx, cy, r, n=24)


def bezier(p0, p1, p2, p3, n=60):
    t = np.linspace(0, 1, n)[:, None]
    p0, p1, p2, p3 = (np.array(p, float) for p in (p0, p1, p2, p3))
    return ((1 - t) ** 3) * p0 + 3 * ((1 - t) ** 2) * t * p1 + 3 * (1 - t) * t * t * p2 + t ** 3 * p3


def chain(*parts):
    """وصل عدة أجزاء بخط واحد متصل."""
    out = [parts[0]]
    for p in parts[1:]:
        out.append(p[1:])
    return np.vstack(out)


def transform(pts, scale=1.0, dx=0.0, dy=0.0, rot=0.0):
    r = math.radians(rot)
    c, s = math.cos(r), math.sin(r)
    x, y = pts[:, 0] * scale, pts[:, 1] * scale
    return np.stack([x * c - y * s + dx, x * s + y * c + dy], axis=1)


def rounded_rect(x0, y0, x1, y1, r):
    return chain(
        line((x0 + r, y0), (x1 - r, y0)),
        arc(x1 - r, y0 + r, r, r, -90, 0, 20),
        line((x1, y0 + r), (x1, y1 - r)),
        arc(x1 - r, y1 - r, r, r, 0, 90, 20),
        line((x1 - r, y1), (x0 + r, y1)),
        arc(x0 + r, y1 - r, r, r, 90, 180, 20),
        line((x0, y1 - r), (x0, y0 + r)),
        arc(x0 + r, y0 + r, r, r, 180, 270, 20),
    )


# ---------- الستيكرات ----------

def s_arrow():
    p0, p1, p2, p3 = (-0.75, 0.6), (-0.6, -0.25), (0.0, -0.6), (0.72, -0.42)
    shaft = bezier(p0, p1, p2, p3, 80)
    d = np.array(p3) - np.array(p2)
    ang = math.atan2(d[1], d[0])
    L = 0.32
    w1 = (p3[0] - L * math.cos(ang - 0.55), p3[1] - L * math.sin(ang - 0.55))
    w2 = (p3[0] - L * math.cos(ang + 0.55), p3[1] - L * math.sin(ang + 0.55))
    return [shaft, poly([w1, p3, w2])]


def s_arrow_straight():
    return [line((-0.8, 0), (0.75, 0), 40), poly([(0.4, -0.35), (0.78, 0), (0.4, 0.35)])]


def s_circle():
    a = np.linspace(math.radians(-110), math.radians(-110 + 395), 160)
    grow = 1 + 0.07 * (a - a[0]) / TAU
    pts = np.stack([0.9 * grow * np.cos(a), 0.7 * grow * np.sin(a)], axis=1)
    return [transform(pts, rot=-8)]


def s_underline():
    return [bezier((-0.9, 0.12), (-0.3, 0.32), (0.3, -0.08), (0.9, 0.04), 70),
            bezier((-0.6, 0.32), (-0.1, 0.42), (0.3, 0.22), (0.65, 0.26), 50)]


def s_star():
    pts = []
    for i in range(10):
        r = 0.92 if i % 2 == 0 else 0.4
        a = math.radians(-90 + i * 36)
        pts.append((r * math.cos(a), r * math.sin(a) + 0.06))
    return [poly(pts, closed=True)]


def s_heart():
    t = np.linspace(0, TAU, 160)
    x = 16 * np.sin(t) ** 3
    y = 13 * np.cos(t) - 5 * np.cos(2 * t) - 2 * np.cos(3 * t) - np.cos(4 * t)
    pts = np.stack([x / 17.5, -(y / 17.5) + 0.08], axis=1)
    return [pts]


def s_lightning():
    return [poly([(0.18, -0.92), (-0.45, 0.1), (-0.02, 0.1), (-0.22, 0.92),
                  (0.5, -0.16), (0.06, -0.16)], closed=True)]


def s_check():
    return [poly([(-0.72, 0.02), (-0.22, 0.52), (0.76, -0.56)], n_per_seg=30)]


def s_cross():
    return [line((-0.62, -0.62), (0.62, 0.62)), line((0.62, -0.62), (-0.62, 0.62))]


def s_question():
    top = arc(0, -0.38, 0.4, 0.4, -200, 35, 80)
    end = top[-1]
    tail = bezier(tuple(end), (0.15, -0.05), (0.0, 0.0), (0.0, 0.32), 30)
    return [chain(top, tail), dot(0, 0.72, 0.06)]


def s_exclamation():
    return [line((0, -0.85), (0, 0.38)), dot(0, 0.72, 0.06)]


def s_bell():
    body = chain(
        line((-0.75, 0.48), (-0.55, 0.3), 8),
        bezier((-0.55, 0.3), (-0.5, 0.1), (-0.6, -0.65), (0, -0.66), 50),
        bezier((0, -0.66), (0.6, -0.65), (0.5, 0.1), (0.55, 0.3), 50),
        line((0.55, 0.3), (0.75, 0.48), 8),
        line((0.75, 0.48), (-0.75, 0.48), 30),
    )
    knob = arc(0, -0.72, 0.08, 0.08, 180, 360, 20)
    clapper = arc(0, 0.56, 0.16, 0.16, 0, 180, 30)
    return [body, knob, clapper]


def s_play():
    return [circle(0, 0, 0.88), poly([(-0.26, -0.42), (0.48, 0), (-0.26, 0.42)], closed=True)]


def s_crown():
    return [poly([(-0.8, 0.45), (-0.88, -0.38), (-0.42, 0.02), (0, -0.62),
                  (0.42, 0.02), (0.88, -0.38), (0.8, 0.45)], closed=True),
            line((-0.8, 0.7), (0.8, 0.7))]


def _sparkle(scale=1.0, dx=0.0, dy=0.0):
    pts = [(0, -0.85), (0.85, 0), (0, 0.85), (-0.85, 0), (0, -0.85)]
    parts = []
    for a, b in zip(pts, pts[1:]):
        # منحنى ينحني نحو المركز
        c1 = (a[0] * 0.15, a[1] * 0.15)
        c2 = (b[0] * 0.15, b[1] * 0.15)
        parts.append(bezier(a, c1, c2, b, 30))
    return transform(chain(*parts), scale, dx, dy)


def s_sparkle():
    return [_sparkle(0.85, -0.12, 0.1), _sparkle(0.3, 0.62, -0.6), _sparkle(0.18, -0.68, -0.66)]


def s_bubble():
    x0, y0, x1, y1, r = -0.85, -0.68, 0.85, 0.32, 0.25
    outline = chain(
        line((x0 + r, y0), (x1 - r, y0)),
        arc(x1 - r, y0 + r, r, r, -90, 0, 20),
        line((x1, y0 + r), (x1, y1 - r)),
        arc(x1 - r, y1 - r, r, r, 0, 90, 20),
        line((x1 - r, y1), (-0.25, y1)),
        line((-0.25, y1), (-0.58, 0.78), 14),
        line((-0.58, 0.78), (-0.5, y1), 14),
        line((-0.5, y1), (x0 + r, y1)),
        arc(x0 + r, y1 - r, r, r, 90, 180, 20),
        line((x0, y1 - r), (x0, y0 + r)),
        arc(x0 + r, y0 + r, r, r, 180, 270, 20),
    )
    return [outline, dot(-0.4, -0.18, 0.06), dot(0, -0.18, 0.06), dot(0.4, -0.18, 0.06)]


def s_fire():
    outer = chain(
        bezier((0, 0.85), (-0.75, 0.85), (-0.75, 0.1), (-0.35, -0.25), 40),
        bezier((-0.35, -0.25), (-0.3, -0.05), (-0.15, 0.0), (-0.1, -0.05), 20),
        bezier((-0.1, -0.05), (-0.25, -0.45), (0.05, -0.75), (0.1, -0.92), 30),
        bezier((0.1, -0.92), (0.6, -0.55), (0.8, 0.1), (0.55, 0.55), 40),
        bezier((0.55, 0.55), (0.4, 0.85), (0.15, 0.85), (0, 0.85), 20),
    )
    inner = chain(
        bezier((0, 0.68), (-0.35, 0.68), (-0.35, 0.3), (-0.1, 0.1), 30),
        bezier((-0.1, 0.1), (0.0, 0.25), (0.1, 0.0), (0.08, -0.15), 20),
        bezier((0.08, -0.15), (0.45, 0.15), (0.35, 0.68), (0, 0.68), 30),
    )
    return [outer, inner]


def s_focus():
    k, L = 0.85, 0.38
    return [poly([(-k, -k + L), (-k, -k), (-k + L, -k)]),
            poly([(k - L, -k), (k, -k), (k, -k + L)]),
            poly([(k, k - L), (k, k), (k - L, k)]),
            poly([(-k + L, k), (-k, k), (-k, k - L)])]


def s_magnifier():
    c = (-0.15, -0.15)
    r = 0.55
    a = math.radians(45)
    return [circle(*c, r, start=45), line((c[0] + r * math.cos(a), c[1] + r * math.sin(a)), (0.82, 0.82))]


def s_burst():
    lines = []
    for i in range(8):
        a = math.radians(-90 + i * 45)
        r0, r1 = (0.42, 0.88) if i % 2 == 0 else (0.5, 0.75)
        lines.append(line((r0 * math.cos(a), r0 * math.sin(a)), (r1 * math.cos(a), r1 * math.sin(a)), 16))
    return lines


def s_like():
    # إبهام مرفوع مبسط
    thumb = chain(
        line((-0.3, -0.05), (-0.05, -0.45), 14),
        bezier((-0.05, -0.45), (0.0, -0.6), (0.05, -0.85), (0.12, -0.85), 14),
        bezier((0.12, -0.85), (0.3, -0.85), (0.32, -0.55), (0.22, -0.2), 20),
        line((0.22, -0.2), (0.62, -0.2), 14),
        bezier((0.62, -0.2), (0.85, -0.2), (0.82, 0.05), (0.7, 0.12), 14),
        bezier((0.7, 0.12), (0.82, 0.25), (0.72, 0.42), (0.62, 0.42), 14),
        bezier((0.62, 0.42), (0.7, 0.55), (0.6, 0.72), (0.45, 0.72), 14),
        line((0.45, 0.72), (-0.3, 0.72), 20),
        line((-0.3, 0.72), (-0.3, -0.05), 20),
    )
    cuff = rounded_rect(-0.72, -0.08, -0.38, 0.78, 0.06)
    return [cuff, thumb]


STICKERS = {
    "arrow":          (s_arrow,          "#00E5FF", "سهم منحني"),
    "arrow-straight": (s_arrow_straight, "#00E5FF", "سهم مستقيم"),
    "circle":         (s_circle,         "#FF2D95", "دائرة تأشير"),
    "underline":      (s_underline,      "#FFE600", "خط تحت"),
    "star":           (s_star,           "#FFE600", "نجمة"),
    "heart":          (s_heart,          "#FF2D95", "قلب"),
    "lightning":      (s_lightning,      "#FFE600", "برق"),
    "check":          (s_check,          "#39FF14", "صح"),
    "cross":          (s_cross,          "#FF1744", "خطأ"),
    "question":       (s_question,       "#B026FF", "علامة سؤال"),
    "exclamation":    (s_exclamation,    "#FF7A00", "علامة تعجب"),
    "bell":           (s_bell,           "#FFE600", "جرس التنبيهات"),
    "play":           (s_play,           "#FF1744", "زر تشغيل"),
    "crown":          (s_crown,          "#FFC400", "تاج"),
    "sparkle":        (s_sparkle,        "#7DF9FF", "لمعة"),
    "bubble":         (s_bubble,         "#00E5FF", "فقاعة كلام"),
    "fire":           (s_fire,           "#FF7A00", "نار"),
    "focus":          (s_focus,          "#39FF14", "إطار تركيز"),
    "magnifier":      (s_magnifier,      "#00E5FF", "عدسة تكبير"),
    "burst":          (s_burst,          "#FFE600", "انفجار ضوئي"),
    "like":           (s_like,           "#2979FF", "لايك"),
}

COLORS = {
    "cyan": "#00E5FF", "pink": "#FF2D95", "yellow": "#FFE600", "green": "#39FF14",
    "purple": "#B026FF", "orange": "#FF7A00", "red": "#FF1744", "blue": "#2979FF",
    "gold": "#FFC400", "white": "#E8F4FF",
}
