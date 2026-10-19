"""فلاتر ألوان — الدفعة 3: طبيعة، سفر، طعام، أفلام."""
import numpy as np

from .luts import (luma, saturation, contrast, lift_gamma_gain, split_tone, fade_blacks, mono, tint,
                   selective_sat, hue_mask, teal_orange)
from .luts2 import soft_highlights, hue_shift_range


def g_lush_green(c):
    """طبيعة خضراء غنية: أخضر عميق وسماء زرقاء."""
    c = selective_sat(c, 0.28, 0.12, 1.35)
    c = hue_shift_range(c, 0.2, 0.08, (0.35, 0.6, 0.2), 0.3)
    c = selective_sat(c, 0.58, 0.12, 1.2)
    c = lift_gamma_gain(c, (0.0, 0.01, 0.0), (1.02, 1.04, 1.0), (1.0, 1.01, 0.98))
    return contrast(c, 0.12)


def g_moody_forest(c):
    """غابة ضبابية داكنة: أخضر مطفي وظلال تركوازية."""
    c = selective_sat(c, 0.3, 0.15, 0.6)
    c = hue_shift_range(c, 0.25, 0.12, (0.25, 0.42, 0.35), 0.45)
    c = split_tone(c, (0.25, 0.45, 0.45), (0.65, 0.62, 0.55), 0.15)
    c = lift_gamma_gain(c, (0.02, 0.03, 0.04), (0.9, 0.95, 0.95), (0.95, 0.97, 0.95))
    return fade_blacks(contrast(c, 0.15), 0.03)


def g_autumn(c):
    """خريف: الأخضر يميل للذهبي والبرتقالي."""
    c = hue_shift_range(c, 0.28, 0.14, (0.75, 0.55, 0.2), 0.55)
    c = selective_sat(c, 0.08, 0.1, 1.3)
    c = lift_gamma_gain(c, (0.03, 0.01, 0.0), (1.05, 1.0, 0.9), (1.05, 0.98, 0.88))
    return contrast(c, 0.1)


def g_winter(c):
    c = lift_gamma_gain(c, (0.02, 0.03, 0.06), (1.05, 1.08, 1.15), (0.98, 1.0, 1.05))
    c = saturation(c, 0.55)
    return fade_blacks(soft_highlights(c, 0.1), 0.03)


def g_blue_hour(c):
    """الساعة الزرقاء: سماء زرقاء عميقة وأضواء دافئة."""
    c = lift_gamma_gain(c, (0.0, 0.01, 0.05), (0.92, 0.97, 1.08), (0.98, 0.98, 1.04))
    c = split_tone(c, (0.2, 0.35, 0.75), (1.0, 0.7, 0.45), 0.18, 0.6)
    return saturation(contrast(c, 0.14), 1.05)


def g_sunrise_peach(c):
    c = lift_gamma_gain(c, (0.04, 0.02, 0.03), (1.1, 1.02, 0.98), (1.05, 0.97, 0.92))
    c = split_tone(c, (0.5, 0.42, 0.55), (1.0, 0.75, 0.6), 0.16)
    return soft_highlights(saturation(contrast(c, 0.04), 1.05), 0.2)


def g_tropical(c):
    """شاطئ استوائي: تركواز صافي ورمل دافئ."""
    c = hue_shift_range(c, 0.55, 0.1, (0.1, 0.75, 0.8), 0.35)
    c = selective_sat(c, 0.5, 0.15, 1.4)
    c = selective_sat(c, 0.1, 0.08, 1.1)
    c = lift_gamma_gain(c, (0.0, 0.0, 0.0), (1.08, 1.06, 1.04), (1.02, 1.02, 1.0))
    return contrast(c, 0.1)


def g_ocean_deep(c):
    c = lift_gamma_gain(c, (0.0, 0.02, 0.05), (0.9, 1.0, 1.1), (0.92, 1.0, 1.06))
    c = selective_sat(c, 0.55, 0.15, 1.3)
    return contrast(c, 0.16)


def g_desert_gold(c):
    c = lift_gamma_gain(c, (0.04, 0.02, 0.0), (1.08, 1.0, 0.85), (1.08, 1.0, 0.82))
    c = selective_sat(c, 0.58, 0.12, 0.7)
    return soft_highlights(contrast(c, 0.12), 0.15)


def g_food_pop(c):
    """طعام شهي: دفء وتشبع للأحمر والأصفر."""
    c = selective_sat(c, 0.02, 0.08, 1.25)
    c = selective_sat(c, 0.12, 0.08, 1.2)
    c = lift_gamma_gain(c, (0.01, 0.0, 0.0), (1.06, 1.03, 0.98), (1.04, 1.02, 0.97))
    return contrast(c, 0.12)


def g_warm_vlog(c):
    c = lift_gamma_gain(c, (0.02, 0.015, 0.01), (1.08, 1.04, 0.98), (1.03, 1.0, 0.95))
    c = soft_highlights(c, 0.15)
    return saturation(contrast(c, 0.06), 1.06)


def g_kodachrome(c):
    c = contrast(c, 0.22)
    c = selective_sat(c, 0.0, 0.08, 1.35)
    c = selective_sat(c, 0.6, 0.12, 1.2)
    c = lift_gamma_gain(c, (0.0, 0.0, 0.0), (1.0, 0.98, 0.95), (1.02, 1.0, 0.96))
    return saturation(c, 1.1)


def g_ektachrome(c):
    c = lift_gamma_gain(c, (0.0, 0.01, 0.03), (0.98, 1.02, 1.06), (1.0, 1.0, 1.03))
    c = selective_sat(c, 0.58, 0.14, 1.35)
    return saturation(contrast(c, 0.18), 1.1)


def g_cine_500t(c):
    """فيلم ليلي 500T: هالات دافئة وظلال زرقاء."""
    c = lift_gamma_gain(c, (0.0, 0.02, 0.05), (0.97, 1.0, 1.06), (1.06, 0.98, 0.9))
    c = split_tone(c, (0.15, 0.45, 0.6), (1.0, 0.55, 0.35), 0.15, 0.55)
    c = soft_highlights(contrast(c, 0.1), 0.2)
    return fade_blacks(c, 0.035)


def g_red_noir(c):
    """أبيض وأسود مع إبقاء الأحمر (Sin City)."""
    m = hue_mask(c, 0.0, 0.06)
    g = contrast(mono(c), 0.25)
    red = saturation(c, 1.3)
    return g * (1 - m) + red * m


def g_neon_pink(c):
    c = lift_gamma_gain(c, (0.04, 0.0, 0.05), (1.08, 0.92, 1.08), (1.06, 0.94, 1.04))
    c = split_tone(c, (0.35, 0.2, 0.6), (1.0, 0.5, 0.75), 0.14)
    return saturation(contrast(c, 0.14), 1.15)


def g_cool_shadows(c):
    c = split_tone(c, (0.15, 0.4, 0.6), (0.6, 0.55, 0.5), 0.18, 0.4)
    return contrast(c, 0.1)


def g_sepia_gold(c):
    m = mono(c)
    return fade_blacks(contrast(tint(m, (1.18, 0.98, 0.65), 1.0), 0.12), 0.03)


LUTS3 = {
    "lush-green":   (g_lush_green,   "طبيعة خضراء غنية"),
    "moody-forest": (g_moody_forest, "غابة ضبابية داكنة"),
    "autumn":       (g_autumn,       "خريفي ذهبي"),
    "winter":       (g_winter,       "شتوي بارد"),
    "blue-hour":    (g_blue_hour,    "الساعة الزرقاء"),
    "sunrise-peach": (g_sunrise_peach, "شروق خوخي"),
    "tropical":     (g_tropical,     "شاطئ استوائي"),
    "ocean-deep":   (g_ocean_deep,   "بحر عميق"),
    "desert-gold":  (g_desert_gold,  "صحراء ذهبية"),
    "food-pop":     (g_food_pop,     "طعام شهي"),
    "warm-vlog":    (g_warm_vlog,    "فلوق دافئ"),
    "kodachrome":   (g_kodachrome,   "كوداكروم كلاسيكي"),
    "ektachrome":   (g_ektachrome,   "إكتاكروم أزرق"),
    "cine-500t":    (g_cine_500t,    "فيلم ليلي 500T"),
    "red-noir":     (g_red_noir,     "أبيض وأسود مع الأحمر"),
    "neon-pink":    (g_neon_pink,    "نيون وردي"),
    "cool-shadows": (g_cool_shadows, "ظلال باردة"),
    "sepia-gold":   (g_sepia_gold,   "بني ذهبي"),
}
