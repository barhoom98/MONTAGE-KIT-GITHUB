"""
محرك رسم النيون: يحوّل خطوط الستيكر إلى إطارات RGBA شفافة متحركة.

الحركة:
  1) رسم تدريجي للخط مع شرارة مضيئة عند رأس القلم
  2) نبض توهج مع ارتعاش نيون خفيف
  3) اختفاء ناعم في النهاية
"""
import math
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter

from .shapes import STICKERS, COLORS

SS = 2  # تنعيم الحواف بالرسم بدقة مضاعفة


def hex_rgb(c):
    c = COLORS.get(c, c).lstrip("#")
    return np.array([int(c[i:i + 2], 16) for i in (0, 2, 4)], float) / 255.0


def _lengths(pts):
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    return np.concatenate([[0], np.cumsum(seg)])


def _cut(pts, cum, L):
    """جزء الخط من بدايته حتى الطول L."""
    if L >= cum[-1]:
        return pts
    i = int(np.searchsorted(cum, L))
    if i == 0:
        return pts[:1]
    f = (L - cum[i - 1]) / max(cum[i] - cum[i - 1], 1e-9)
    return np.vstack([pts[:i], pts[i - 1] + f * (pts[i] - pts[i - 1])])


class Sticker:
    def __init__(self, name, size=512, color=None, scale=0.36, width=1.0, rotate=0.0, flip=False):
        fn, default_color, _ = STICKERS[name]
        self.name = name
        self.size = size
        self.color = hex_rgb(color or default_color)
        self.core = self.color * 0.25 + 0.75  # قلب الخط أبيض مائل للون
        self.polys = []
        r = math.radians(rotate)
        c, s = math.cos(r), math.sin(r)
        for p in fn():
            p = p.copy()
            if flip:
                p[:, 0] = -p[:, 0]
            p = np.stack([p[:, 0] * c - p[:, 1] * s, p[:, 0] * s + p[:, 1] * c], axis=1)
            self.polys.append(p * size * scale + size / 2)
        self.cums = [_lengths(p) for p in self.polys]
        self.total = sum(c[-1] for c in self.cums)
        self.w = 13 * size / 512 * width
        self.wc = 4.5 * size / 512 * width

    # ---------- رسم الأقنعة ----------

    def _mask(self, progress, width):
        S = self.size * SS
        img = Image.new("L", (S, S), 0)
        d = ImageDraw.Draw(img)
        w = max(1, int(round(width * SS)))
        budget = progress * self.total
        head = None
        for pts, cum in zip(self.polys, self.cums):
            if budget <= 0:
                break
            part = _cut(pts, cum, budget)
            budget -= cum[-1]
            q = [(float(x * SS), float(y * SS)) for x, y in part]
            if len(q) > 1:
                d.line(q, fill=255, width=w, joint="curve")
            for (x, y) in (q[0], q[-1]):
                d.ellipse([x - w / 2, y - w / 2, x + w / 2, y + w / 2], fill=255)
            head = part[-1]
        m = np.asarray(img.resize((self.size, self.size), Image.LANCZOS), np.float32) / 255.0
        return m, head

    @staticmethod
    def _blur(m, sigma):
        if sigma <= 6:
            return gaussian_filter(m, sigma)
        k = 4
        small = Image.fromarray(m).resize((m.shape[1] // k, m.shape[0] // k), Image.BILINEAR)
        b = gaussian_filter(np.asarray(small, np.float32), sigma / k)
        return np.asarray(Image.fromarray(b).resize((m.shape[1], m.shape[0]), Image.BILINEAR), np.float32)

    # ---------- إطار واحد ----------

    def frame(self, progress=1.0, intensity=1.0, opacity=1.0):
        stroke, head = self._mask(progress, self.w)
        core, _ = self._mask(progress, self.wc)
        sc = self.size / 512
        glow = (0.55 * self._blur(stroke, 4 * sc)
                + 1.1 * self._blur(stroke, 14 * sc)
                + 2.2 * self._blur(stroke, 38 * sc)) * intensity

        # شرارة عند رأس القلم أثناء الرسم
        if head is not None and progress < 1.0:
            yy, xx = np.mgrid[0:self.size, 0:self.size].astype(np.float32)
            d2 = (xx - head[0]) ** 2 + (yy - head[1]) ** 2
            spark = np.exp(-d2 / (2 * (self.w * 1.1) ** 2))
            core = np.maximum(core, spark)
            glow = glow + 1.1 * np.exp(-d2 / (2 * (self.w * 2.6) ** 2))

        a_g = np.clip(glow, 0, 1)
        stroke = stroke * min(1.0, 0.55 + 0.45 * intensity)
        # تركيب الطبقات: توهج ← خط ملون ← قلب أبيض
        A = a_g
        P = self.color[None, None, :] * a_g[..., None]
        P = self.color * stroke[..., None] + P * (1 - stroke[..., None])
        A = stroke + A * (1 - stroke)
        P = self.core * core[..., None] + P * (1 - core[..., None])
        A = core + A * (1 - core)
        A = A * opacity
        P = P * opacity
        rgb = np.where(A[..., None] > 1e-4, P / np.maximum(A[..., None], 1e-4), 0)
        out = np.dstack([np.clip(rgb, 0, 1), np.clip(A, 0, 1)])
        return (out * 255 + 0.5).astype(np.uint8)

    # ---------- التسلسل الزمني ----------

    def frames(self, duration=3.0, fps=30, draw_time=0.7, fade_out=0.3, loop_pulse=1.2, seed=None):
        n = max(1, int(round(duration * fps)))
        rng = np.random.default_rng(seed if seed is not None else abs(hash(self.name)) % 2**32)
        flick = set()
        for _ in range(max(1, int(duration / 1.5))):
            f0 = int(rng.uniform(draw_time + 0.3, max(draw_time + 0.4, duration - fade_out - 0.2)) * fps)
            flick.update({f0, f0 + 2})
        for i in range(n):
            t = i / fps
            p = 1.0 if draw_time <= 0 else min(1.0, t / draw_time)
            p = 0.5 - 0.5 * math.cos(math.pi * p)  # ease-in-out
            pulse = 0.82 + 0.18 * math.sin(TAU_ * max(0.0, t - draw_time) / loop_pulse + math.pi / 2)
            inten = pulse * (0.45 if i in flick else 1.0)
            if t < draw_time:
                inten *= 0.6 + 0.4 * p
            op = 1.0
            if fade_out > 0 and t > duration - fade_out:
                op = max(0.0, (duration - t) / fade_out)
            yield self.frame(p, inten, op)


TAU_ = 2 * math.pi
