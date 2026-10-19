"""فلاتر ألوان جديدة 2026 — طابع الأفلام والترندات الحالية."""
import numpy as np

from .luts import (luma, saturation, contrast, lift_gamma_gain, split_tone, fade_blacks, mono, tint,
                   selective_sat, hue_mask, teal_orange, channel_curve)


def soft_highlights(c, amount=0.15):
    """ضغط الإضاءات العالية (Highlight roll-off) بطابع الفيلم."""
    return c - amount * np.clip(c - 0.7, 0, 1) ** 2 * 3


def hue_shift_range(c, center, width, target_rgb, amount):
    m = hue_mask(c, center, width)
    y = luma(c)[..., None]
    tgt = np.array(target_rgb, float) * y * 2
    return c * (1 - m * amount) + tgt * m * amount


def g_tungsten_800(c):
    """فيلم ليلي تنغستن: ظلال تركوازية وأضواء دافئة."""
    c = lift_gamma_gain(c, (0.0, 0.02, 0.05), (0.95, 1.0, 1.08), (1.05, 0.98, 0.92))
    c = split_tone(c, (0.2, 0.5, 0.6), (1.0, 0.6, 0.4), 0.16)
    c = soft_highlights(contrast(c, 0.12), 0.15)
    return fade_blacks(saturation(c, 1.05), 0.03)


def g_portra(c):
    """بورتريه دافئ ناعم بطابع فيلم 400."""
    c = lift_gamma_gain(c, (0.03, 0.02, 0.0), (1.06, 1.02, 0.96), (1.02, 1.0, 0.95))
    c = selective_sat(c, 0.06, 0.08, 1.08)
    c = selective_sat(c, 0.33, 0.15, 0.75)
    c = soft_highlights(contrast(c, 0.05), 0.2)
    return fade_blacks(saturation(c, 0.92), 0.035)


def g_slide_film(c):
    """فيلم شرائح: ألوان غنية وتباين عالي."""
    c = channel_curve(c, 1.0, 1.02, 1.06)
    c = contrast(c, 0.25)
    return saturation(c, 1.3)


def g_nordic(c):
    """إسكندنافي هادئ: ألوان باهتة باردة ونظيفة."""
    c = lift_gamma_gain(c, (0.02, 0.025, 0.035), (1.05, 1.05, 1.08), (0.98, 1.0, 1.02))
    c = saturation(c, 0.6)
    return fade_blacks(contrast(c, 0.0), 0.05, 0.02)


def g_y2k_digicam(c):
    """كاميرا ديجيتال قديمة (ترند Y2K): بارد، فلاش، تباين حاد."""
    c = lift_gamma_gain(c, (0.0, 0.01, 0.04), (1.05, 1.05, 1.12), (1.08, 1.06, 1.1))
    c = contrast(c, 0.22)
    return saturation(c, 1.12)


def g_clean_glow(c):
    """مضيء ناعم ودافئ (ستايل الفلوقات النظيفة)."""
    c = lift_gamma_gain(c, (0.03, 0.025, 0.02), (1.15, 1.1, 1.05), (1.04, 1.02, 0.99))
    c = soft_highlights(c, 0.25)
    return saturation(contrast(c, -0.05), 0.95)


def g_dark_academia(c):
    c = lift_gamma_gain(c, (0.02, 0.01, 0.0), (0.88, 0.85, 0.78), (0.95, 0.9, 0.8))
    c = split_tone(c, (0.45, 0.38, 0.3), (0.8, 0.65, 0.45), 0.18)
    c = saturation(c, 0.7)
    return contrast(c, 0.18)


def g_summer(c):
    c = lift_gamma_gain(c, (0.02, 0.01, 0.0), (1.08, 1.05, 0.98), (1.06, 1.02, 0.95))
    c = selective_sat(c, 0.55, 0.12, 1.35)  # سماء وبحر
    c = selective_sat(c, 0.08, 0.1, 1.2)
    return saturation(contrast(c, 0.1), 1.15)


def g_latte(c):
    """بيج دافئ (ستايل الإيستيتك)."""
    c = lift_gamma_gain(c, (0.05, 0.035, 0.02), (1.08, 1.03, 0.95), (1.0, 0.96, 0.88))
    c = saturation(c, 0.65)
    return fade_blacks(contrast(c, 0.02), 0.05, 0.03)


def g_mint(c):
    c = lift_gamma_gain(c, (0.0, 0.03, 0.02), (0.98, 1.08, 1.04), (0.97, 1.03, 1.0))
    c = split_tone(c, (0.35, 0.55, 0.5), (0.6, 0.62, 0.55), 0.12)
    return fade_blacks(saturation(c, 0.85), 0.04)


def g_lavender(c):
    c = lift_gamma_gain(c, (0.03, 0.01, 0.05), (1.05, 0.98, 1.1), (1.0, 0.96, 1.04))
    c = split_tone(c, (0.5, 0.4, 0.65), (0.75, 0.65, 0.8), 0.15)
    return fade_blacks(saturation(contrast(c, -0.03), 0.85), 0.04)


def g_anime_sky(c):
    """سماء أنمي: أزرق عميق وألوان صافية."""
    c = selective_sat(c, 0.58, 0.14, 1.6)
    c = hue_shift_range(c, 0.5, 0.1, (0.2, 0.55, 1.0), 0.4)
    c = lift_gamma_gain(c, (0.0, 0.0, 0.02), (1.08, 1.06, 1.05), (1.0, 1.0, 1.05))
    return saturation(contrast(c, 0.1), 1.15)


def g_music_video_red(c):
    c = lift_gamma_gain(c, (0.04, 0.0, 0.0), (1.1, 0.85, 0.85), (1.1, 0.88, 0.9))
    c = selective_sat(c, 0.0, 0.08, 1.4)
    return saturation(contrast(c, 0.25), 0.95)


def g_matte_black(c):
    c = contrast(c, 0.15)
    c = saturation(c, 0.8)
    return fade_blacks(c, 0.1, 0.04)


def g_high_key(c):
    c = lift_gamma_gain(c, (0.06, 0.06, 0.06), (1.35, 1.33, 1.32), (1.0, 1.0, 1.0))
    return saturation(contrast(c, -0.1), 0.8)


def g_polaroid(c):
    c = lift_gamma_gain(c, (0.05, 0.04, 0.06), (1.05, 1.0, 0.92), (0.97, 0.95, 0.85))
    c = split_tone(c, (0.35, 0.5, 0.55), (0.8, 0.7, 0.5), 0.15)
    c = saturation(c, 0.8)
    return fade_blacks(contrast(c, 0.08), 0.07, 0.04)


def g_green_90s(c):
    c = lift_gamma_gain(c, (0.01, 0.04, 0.02), (0.95, 1.06, 0.92), (0.96, 1.0, 0.9))
    return fade_blacks(saturation(contrast(c, 0.1), 0.85), 0.05)


def g_dune(c):
    """صحراء برتقالية أحادية (ستايل أفلام الخيال الملحمي)."""
    y = luma(c)[..., None]
    orange = np.array([1.0, 0.62, 0.32])
    mono_o = np.clip(y * orange * 1.25, 0, 1)
    c = c * 0.35 + mono_o * 0.65
    c = contrast(c, 0.15)
    return fade_blacks(c, 0.02)


def g_night_city(c):
    c = lift_gamma_gain(c, (0.0, 0.01, 0.03), (0.85, 0.92, 1.0), (0.9, 0.95, 1.05))
    c = teal_orange(c, 0.8)
    return saturation(contrast(c, 0.25), 0.85)


def g_pastel_symmetry(c):
    """ألوان باستيل متناسقة (ستايل الأفلام الكوميدية الحالمة)."""
    c = lift_gamma_gain(c, (0.04, 0.03, 0.04), (1.1, 1.05, 1.0), (1.02, 0.98, 0.95))
    c = selective_sat(c, 0.95, 0.12, 1.3)  # وردي
    c = selective_sat(c, 0.12, 0.08, 1.2)  # أصفر
    c = split_tone(c, (0.55, 0.5, 0.55), (1.0, 0.85, 0.75), 0.12)
    return saturation(contrast(c, -0.04), 0.95)


def g_cyber_teal(c):
    c = hue_shift_range(c, 0.33, 0.15, (0.0, 0.6, 0.6), 0.6)
    c = lift_gamma_gain(c, (0.0, 0.02, 0.03), (0.95, 1.0, 1.05), (1.0, 1.0, 1.0))
    c = split_tone(c, (0.2, 0.45, 0.55), (0.9, 0.55, 0.75), 0.14)
    return saturation(contrast(c, 0.2), 1.1)


def g_golden_film(c):
    c = lift_gamma_gain(c, (0.04, 0.02, 0.0), (1.05, 1.0, 0.85), (1.05, 0.98, 0.82))
    c = soft_highlights(contrast(c, 0.1), 0.2)
    return fade_blacks(saturation(c, 1.05), 0.04)


def g_bw_film(c):
    m = mono(c, (0.3, 0.6, 0.1))
    m = soft_highlights(contrast(m, 0.2), 0.2)
    return fade_blacks(tint(m, (1.02, 1.0, 0.96), 1.0), 0.04)


def g_sunset_orange(c):
    c = lift_gamma_gain(c, (0.03, 0.0, 0.02), (1.12, 0.98, 0.9), (1.1, 0.95, 0.85))
    c = split_tone(c, (0.4, 0.3, 0.55), (1.0, 0.6, 0.3), 0.2)
    return saturation(contrast(c, 0.12), 1.15)


LUTS2 = {
    "tungsten-800":    (g_tungsten_800,    "فيلم ليلي تنغستن (ترند 2026)"),
    "portra":          (g_portra,          "بورتريه فيلم دافئ"),
    "slide-film":      (g_slide_film,      "فيلم شرائح ألوان غنية"),
    "golden-film":     (g_golden_film,     "فيلم ذهبي"),
    "bw-film":         (g_bw_film,         "أبيض وأسود فيلم"),
    "y2k-digicam":     (g_y2k_digicam,     "كاميرا ديجيتال Y2K"),
    "polaroid":        (g_polaroid,        "بولارويد"),
    "green-90s":       (g_green_90s,       "تسعينات مخضر"),
    "nordic":          (g_nordic,          "إسكندنافي هادئ"),
    "clean-glow":      (g_clean_glow,      "مضيء نظيف (فلوق)"),
    "latte":           (g_latte,           "بيج لاتيه"),
    "mint":            (g_mint,            "نعناعي"),
    "lavender":        (g_lavender,        "لافندر"),
    "dark-academia":   (g_dark_academia,   "داكن أكاديمي"),
    "summer":          (g_summer,          "صيفي"),
    "sunset-orange":   (g_sunset_orange,   "غروب برتقالي"),
    "anime-sky":       (g_anime_sky,       "سماء أنمي"),
    "music-video-red": (g_music_video_red, "أحمر فيديو كليب"),
    "matte-black":     (g_matte_black,     "أسود مطفي"),
    "high-key":        (g_high_key,        "إضاءة عالية بيضاء"),
    "dune":            (g_dune,            "صحراء ملحمية برتقالية"),
    "night-city":      (g_night_city,      "مدينة ليلية"),
    "pastel-symmetry": (g_pastel_symmetry, "باستيل حالم"),
    "cyber-teal":      (g_cyber_teal,      "سايبر تركوازي"),
}
