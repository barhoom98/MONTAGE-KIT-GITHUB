"""
فلاتر ألوان (Color Grading) كملفات LUT بصيغة .cube
تعمل في CapCut و Premiere و DaVinci و Final Cut و ffmpeg.
"""
import numpy as np

SIZE = 33


# =================== عمليات لونية ===================

def luma(c):
    return c[..., 0] * 0.2126 + c[..., 1] * 0.7152 + c[..., 2] * 0.0722


def saturation(c, s):
    y = luma(c)[..., None]
    return y + (c - y) * s


def contrast(c, amount, pivot=0.5):
    """منحنى S ناعم. amount>0 يزيد التباين."""
    x = np.clip(c, 0, 1)
    s = x * x * (3 - 2 * x)  # smoothstep
    out = x + (s - x) * amount * 2
    return pivot + (out - pivot) * (1 + amount * 0.3)


def lift_gamma_gain(c, lift=(0, 0, 0), gamma=(1, 1, 1), gain=(1, 1, 1)):
    lift, gamma, gain = (np.array(v, float) for v in (lift, gamma, gain))
    x = np.clip(c, 0, 1)
    x = x * (gain - lift) + lift
    return np.clip(x, 0, 1) ** (1 / gamma)


def split_tone(c, shadow, highlight, amount=0.15, balance=0.5):
    y = luma(c)[..., None]
    w_h = np.clip((y - balance) * 2 + 0.5, 0, 1)
    w_s = 1 - w_h
    sh = np.array(shadow, float)
    hi = np.array(highlight, float)
    return c + amount * (w_s * (sh - 0.5) + w_h * (hi - 0.5)) * 2 * (1 - np.abs(y - 0.5))


def fade_blacks(c, lift=0.08, crush_white=0.0):
    return c * (1 - lift - crush_white) + lift


def mono(c, weights=(0.3, 0.59, 0.11)):
    y = c[..., 0] * weights[0] + c[..., 1] * weights[1] + c[..., 2] * weights[2]
    return np.repeat(y[..., None], 3, axis=-1)


def tint(c, color, amount):
    return c * (1 - amount) + c * np.array(color, float) * amount


def hue_rgb(c):
    """hue بين 0 و 1 لكل لون."""
    r, g, b = c[..., 0], c[..., 1], c[..., 2]
    mx = np.max(c, axis=-1)
    mn = np.min(c, axis=-1)
    d = mx - mn + 1e-9
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) / 6
    return h, (mx - mn) / (mx + 1e-9)


def hue_mask(c, center, width=0.08):
    h, s = hue_rgb(c)
    d = np.abs(((h - center + 0.5) % 1) - 0.5)
    return (np.clip(1 - d / width, 0, 1) * np.clip(s * 3, 0, 1))[..., None]


def selective_sat(c, center, width, amount):
    m = hue_mask(c, center, width)
    return c * (1 - m) + saturation(c, amount) * m


def teal_orange(c, amount=0.6):
    orange = np.array([1.0, 0.6, 0.3])
    # تحويل الألوان الدافئة للبرتقالي والباردة للتركوازي
    warm = hue_mask(c, 0.07, 0.12)
    out = c * (1 - amount * 0.25 * warm) + amount * 0.25 * warm * c * orange * 1.3
    out = split_tone(out, (0.2, 0.55, 0.62), (0.75, 0.55, 0.35), 0.18 * amount, 0.45)
    return out


def channel_curve(c, r=1.0, g=1.0, b=1.0):
    """gamma لكل قناة."""
    return np.clip(c, 0, 1) ** np.array([1 / r, 1 / g, 1 / b])


# =================== الوصفات ===================

def g_cinematic(c):
    c = teal_orange(c, 0.9)
    c = contrast(c, 0.18)
    c = saturation(c, 0.9)
    return fade_blacks(c, 0.025)


def g_teal_orange(c):
    c = teal_orange(c, 1.4)
    c = contrast(c, 0.12)
    return saturation(c, 1.08)


def g_warm(c):
    c = lift_gamma_gain(c, (0.02, 0.0, -0.01), (1.05, 1.0, 0.92), (1.06, 1.0, 0.9))
    return saturation(contrast(c, 0.06), 1.08)


def g_golden_hour(c):
    c = lift_gamma_gain(c, (0.03, 0.01, -0.02), (1.08, 1.02, 0.88), (1.1, 1.0, 0.82))
    c = split_tone(c, (0.55, 0.4, 0.35), (1.0, 0.78, 0.45), 0.2)
    return saturation(contrast(c, 0.08), 1.15)


def g_cool(c):
    c = lift_gamma_gain(c, (-0.01, 0.0, 0.03), (0.95, 1.0, 1.08), (0.94, 1.0, 1.08))
    return saturation(contrast(c, 0.06), 0.95)


def g_moody(c):
    c = lift_gamma_gain(c, (0.0, 0.01, 0.02), (0.85, 0.9, 0.92), (0.95, 0.95, 0.95))
    c = split_tone(c, (0.3, 0.45, 0.5), (0.6, 0.55, 0.45), 0.15)
    c = saturation(c, 0.7)
    return contrast(c, 0.2)


def g_film_fade(c):
    c = fade_blacks(contrast(c, 0.05), 0.09, 0.04)
    c = split_tone(c, (0.4, 0.48, 0.55), (0.6, 0.55, 0.45), 0.1)
    return saturation(c, 0.82)


def g_vintage(c):
    c = lift_gamma_gain(c, (0.06, 0.04, 0.0), (1.05, 1.0, 0.85), (0.98, 0.95, 0.8))
    c = split_tone(c, (0.5, 0.45, 0.35), (0.7, 0.62, 0.45), 0.18)
    c = saturation(c, 0.7)
    return fade_blacks(c, 0.06, 0.03)


def g_sepia(c):
    m = mono(c)
    return fade_blacks(tint(m, (1.15, 0.95, 0.7), 1.0), 0.04, 0.02)


def g_bw(c):
    return contrast(mono(c), 0.1)


def g_noir(c):
    m = mono(c, (0.35, 0.55, 0.1))
    return contrast(contrast(m, 0.35), 0.15)


def g_cyberpunk(c):
    c = lift_gamma_gain(c, (0.02, -0.01, 0.05), (1.0, 0.94, 1.08), (1.02, 0.95, 1.06))
    c = split_tone(c, (0.25, 0.3, 0.75), (0.95, 0.45, 0.75), 0.12, 0.55)
    c = selective_sat(c, 0.5, 0.15, 1.5)
    return saturation(contrast(c, 0.15), 1.15)


def g_neon_night(c):
    c = lift_gamma_gain(c, (0.0, 0.01, 0.05), (0.9, 0.95, 1.1), (0.95, 1.0, 1.1))
    c = split_tone(c, (0.15, 0.3, 0.75), (0.85, 0.5, 0.8), 0.12, 0.6)
    return saturation(contrast(c, 0.2), 1.15)


def g_pastel(c):
    c = fade_blacks(c, 0.07)
    c = lift_gamma_gain(c, (0.02, 0.01, 0.03), (1.15, 1.1, 1.12), (1.0, 1.0, 1.0))
    c = split_tone(c, (0.55, 0.5, 0.65), (1.0, 0.85, 0.85), 0.12)
    return saturation(contrast(c, -0.12), 0.85)


def g_vibrant(c):
    c = saturation(c, 1.35)
    return contrast(c, 0.14)


def g_bleach(c):
    m = mono(c)
    c = c * 0.45 + m * 0.55
    return contrast(c, 0.3)


def g_matrix(c):
    c = lift_gamma_gain(c, (-0.02, 0.02, -0.02), (0.85, 1.12, 0.85), (0.85, 1.05, 0.8))
    c = saturation(c, 0.7)
    return contrast(c, 0.2)


def g_kodak(c):
    c = lift_gamma_gain(c, (0.02, 0.015, 0.0), (1.03, 1.0, 0.95), (1.04, 1.0, 0.94))
    c = selective_sat(c, 0.33, 0.12, 0.85)  # أخضر أهدأ
    c = selective_sat(c, 0.06, 0.08, 1.12)  # بشرة أدفأ
    c = contrast(c, 0.1)
    return fade_blacks(c, 0.03)


def g_fuji(c):
    c = lift_gamma_gain(c, (0.0, 0.01, 0.02), (0.98, 1.02, 1.03), (0.98, 1.0, 1.0))
    c = selective_sat(c, 0.33, 0.12, 0.75)
    c = split_tone(c, (0.45, 0.5, 0.55), (0.55, 0.52, 0.48), 0.1)
    c = saturation(c, 0.88)
    return contrast(c, 0.14)


def g_desert(c):
    c = lift_gamma_gain(c, (0.04, 0.02, 0.0), (1.08, 1.0, 0.85), (1.05, 0.98, 0.85))
    c = saturation(c, 0.75)
    return fade_blacks(contrast(c, 0.1), 0.04)


def g_arctic(c):
    c = lift_gamma_gain(c, (0.0, 0.02, 0.05), (0.95, 1.02, 1.12), (0.95, 1.0, 1.05))
    c = saturation(c, 0.6)
    return fade_blacks(contrast(c, 0.05), 0.03)


def g_horror(c):
    c = lift_gamma_gain(c, (0.0, 0.02, 0.0), (0.8, 0.9, 0.82), (0.9, 0.95, 0.88))
    c = saturation(c, 0.45)
    return contrast(c, 0.3)


def g_cross_process(c):
    c = channel_curve(c, 1.15, 1.08, 0.82)
    c = lift_gamma_gain(c, (0.0, 0.0, 0.08), (1, 1, 1), (1.05, 1.05, 0.85))
    return saturation(contrast(c, 0.15), 1.15)


def g_insta_fade(c):
    c = fade_blacks(c, 0.06, 0.02)
    c = lift_gamma_gain(c, (0.02, 0.01, 0.0), (1.05, 1.03, 1.0), (1.03, 1.0, 0.97))
    return saturation(contrast(c, 0.05), 0.95)


def g_punch(c):
    c = contrast(c, 0.3)
    return saturation(c, 1.2)


def g_dreamy(c):
    c = lift_gamma_gain(c, (0.04, 0.03, 0.05), (1.15, 1.08, 1.12), (1.0, 0.98, 1.0))
    c = split_tone(c, (0.5, 0.45, 0.6), (1.0, 0.9, 0.8), 0.12)
    return saturation(contrast(c, -0.08), 0.9)


def g_sunset_pink(c):
    c = lift_gamma_gain(c, (0.03, 0.0, 0.03), (1.08, 0.95, 1.0), (1.08, 0.95, 0.98))
    c = split_tone(c, (0.45, 0.35, 0.6), (0.95, 0.65, 0.6), 0.14)
    return saturation(contrast(c, 0.08), 1.1)


def g_day_for_night(c):
    c = lift_gamma_gain(c, (0.0, 0.0, 0.02), (0.6, 0.68, 0.85), (0.55, 0.65, 0.85))
    return saturation(contrast(c, 0.15), 0.5)


def g_retro_80s(c):
    c = lift_gamma_gain(c, (0.05, 0.0, 0.07), (1.05, 0.95, 1.05), (1.0, 0.95, 1.0))
    c = split_tone(c, (0.45, 0.3, 0.65), (0.95, 0.7, 0.55), 0.13)
    return fade_blacks(saturation(contrast(c, 0.1), 1.2), 0.04)


LUTS = {
    "cinematic":      (g_cinematic,      "سينمائي متوازن"),
    "teal-orange":    (g_teal_orange,    "تركواز وبرتقالي (أفلام هوليوود)"),
    "warm":           (g_warm,           "دافئ"),
    "golden-hour":    (g_golden_hour,    "ساعة ذهبية"),
    "cool":           (g_cool,           "بارد"),
    "moody":          (g_moody,          "مزاجي داكن"),
    "film-fade":      (g_film_fade,      "فيلم باهت"),
    "vintage":        (g_vintage,        "قديم (فينتج)"),
    "retro-80s":      (g_retro_80s,      "ريترو الثمانينات"),
    "sepia":          (g_sepia,          "بني قديم"),
    "bw":             (g_bw,             "أبيض وأسود"),
    "noir":           (g_noir,           "أبيض وأسود عالي التباين"),
    "cyberpunk":      (g_cyberpunk,      "سايبربانك"),
    "neon-night":     (g_neon_night,     "ليل نيون"),
    "pastel":         (g_pastel,         "باستيل ناعم"),
    "dreamy":         (g_dreamy,         "حالم"),
    "sunset-pink":    (g_sunset_pink,    "غروب وردي"),
    "vibrant":        (g_vibrant,        "ألوان حيوية"),
    "punch":          (g_punch,          "تباين قوي"),
    "bleach-bypass":  (g_bleach,         "بليتش (أفلام حرب/أكشن)"),
    "matrix":         (g_matrix,         "أخضر ماتريكس"),
    "kodak":          (g_kodak,          "فيلم كوداك"),
    "fuji":           (g_fuji,           "فيلم فوجي"),
    "desert":         (g_desert,         "صحراوي"),
    "arctic":         (g_arctic,         "قطبي بارد"),
    "horror":         (g_horror,         "رعب"),
    "cross-process":  (g_cross_process,  "كروس بروسس"),
    "insta-fade":     (g_insta_fade,     "إنستغرام باهت"),
    "day-for-night":  (g_day_for_night,  "تحويل النهار لليل"),
}


def lattice(size=SIZE):
    v = np.linspace(0, 1, size)
    b, g, r = np.meshgrid(v, v, v, indexing="ij")  # R الأسرع تغيراً
    return np.stack([r, g, b], axis=-1).reshape(-1, 3)


def build(name, strength=1.0, size=SIZE):
    base = lattice(size)
    out = np.clip(LUTS[name][0](base.copy()), 0, 1)
    return base + (out - base) * strength


def write_cube(path, name, strength=1.0, size=SIZE):
    data = build(name, strength, size)
    with open(path, "w") as f:
        f.write(f'TITLE "{name}"\nLUT_3D_SIZE {size}\nDOMAIN_MIN 0.0 0.0 0.0\nDOMAIN_MAX 1.0 1.0 1.0\n')
        np.savetxt(f, data, fmt="%.4f")


def apply_np(img, name, strength=1.0):
    """تطبيق مباشر على صورة float [0,1] (للمعاينات)."""
    out = np.clip(LUTS[name][0](img.copy()), 0, 1)
    return img + (out - img) * strength
