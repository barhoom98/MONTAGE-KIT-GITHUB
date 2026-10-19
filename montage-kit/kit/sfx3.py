"""مؤثرات صوتية — الدفعة 3: طبول للإيقاع، أجواء طبيعة، ميمز، واجهات."""
import math
import numpy as np

from .sfx import (SR, T, white, pink, brown, sine_sweep, saw_sweep, square_sweep, expo, decay, bell_env,
                  svf, bfilt, stereo, reverb, mix, at, add, click, tone, bell, pluck, whoosh, fade)


# ---------- طبول (لمونتاج الإيقاع / Beat Sync) ----------

def s_kick():
    d = 0.5
    n = int(d * SR)
    x = np.tanh(2.5 * sine_sweep(55 + 120 * np.exp(-T(d) / 0.025))) * decay(d, 0.18)
    x = add(x, click(0.004, 3000, 301) * 0.5)
    return stereo(x)


def s_snare():
    d = 0.35
    body = np.sin(2 * np.pi * 190 * T(d)) * decay(d, 0.05)
    nz = bfilt(white(d), "band", (1500, 8000), 2) * decay(d, 0.09)
    return reverb(stereo(body * 0.6 + nz), 0.6, 0.12)


def s_clap():
    r = np.random.default_rng(302)
    x = np.zeros(int(0.4 * SR))
    for i, t0 in enumerate((0.0, 0.01, 0.022, 0.035)):
        seg = bfilt(r.standard_normal(int(0.15 * SR)), "band", (900, 5000), 2) * decay(0.15, 0.012 if i < 3 else 0.06)
        s = int(t0 * SR)
        x[s:s + len(seg)] += seg
    return reverb(stereo(x), 0.5, 0.15)


def s_hihat():
    d = 0.12
    x = bfilt(white(d), "high", 7000, 2) * decay(d, 0.025)
    return stereo(x)


def s_open_hat():
    d = 0.5
    x = bfilt(white(d), "high", 6000, 2) * decay(d, 0.15)
    return stereo(x)


def s_tom_fill():
    parts = []
    for i, f in enumerate((220, 180, 150, 120, 95, 80)):
        d = 0.3
        x = np.tanh(1.5 * sine_sweep(f * (1 + 0.6 * np.exp(-T(d) / 0.02)))) * decay(d, 0.12)
        parts.append(at(stereo(x, 0.6 - i * 0.24), i * 0.09))
    return reverb(mix(*parts), 0.8, 0.15)


def s_beat_4():
    """مقطع إيقاع جاهز 4 ضربات (للتجربة والمقدمات)."""
    k, sn, hh = s_kick(), s_snare(), s_hihat()
    parts = []
    for i in range(8):
        t0 = i * 0.25
        parts.append(at(hh * 0.5, t0))
        if i % 4 == 0:
            parts.append(at(k, t0))
        if i % 4 == 2:
            parts.append(at(sn, t0))
    return mix(*parts)


def s_cymbal_swell():
    d = 2.0
    t = T(d)
    nz = bfilt(white(d), "high", 4000, 2) * (t / d) ** 2.5
    return reverb(stereo(nz), 1.0, 0.2)


# ---------- انتقالات حديثة ----------

def s_uplifter():
    d = 2.5
    n = int(d * SR)
    t = T(d)
    p = t / d
    nz = svf(white(d) * 0.6, 400 * (25 ** p), 1.5) * p ** 1.8
    return reverb(stereo(nz, np.sin(2 * np.pi * 1.2 * t) * 0.5 * p), 1.2, 0.2)


def s_sub_whoosh():
    d = 1.0
    n = int(d * SR)
    env = bell_env(n, 0.6, 2.0)
    x = np.tanh(2 * sine_sweep(expo(35, 90, n))) * env + svf(pink(d) * 2, 200 + 1200 * env, 1.0) * env * 0.4
    return reverb(stereo(x, np.linspace(-0.4, 0.4, n)), 0.8, 0.15)


def s_digital_transition():
    d = 0.6
    n = int(d * SR)
    t = T(d)
    step = (np.floor(t * 40) / 40)
    f = 300 + 3000 * step / d
    x = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.3 * bell_env(n, 0.5, 1.0)
    w = whoosh(d, 800, 6000, 0.5, seed=303, verb=0)[:n]
    return reverb(mix(stereo(bfilt(x, "low", 8000, 2)), w * 0.7), 0.5, 0.12)


def s_glitch_stutter():
    src = bfilt(white(0.05), "band", (500, 5000), 2) + np.sign(np.sin(2 * np.pi * 220 * T(0.05))) * 0.3
    parts = []
    for i in range(10):
        L = int(0.05 * SR * (1 - i * 0.07))
        parts.append(src[:L] * (1 - i * 0.06))
        parts.append(np.zeros(int(0.012 * SR)))
    return stereo(np.concatenate(parts) * 0.7)


def s_vinyl_scratch_short():
    d = 0.35
    n = int(d * SR)
    t = T(d)
    speed = np.sin(2 * np.pi * 5.5 * t)
    src = bfilt(np.random.default_rng(304).standard_normal(n * 3), "band", (300, 4000), 2)
    pos = np.clip(np.cumsum(np.abs(speed) * 2.2), 0, n * 3 - 2).astype(int)
    x = svf(src[pos] * np.abs(speed), 400 + 3500 * np.abs(speed), 2.5, "band")
    return stereo(x * 2)


def s_camera_zoom_whir():
    d = 0.8
    n = int(d * SR)
    t = T(d)
    x = np.sin(2 * np.pi * np.cumsum(expo(600, 1400, n)) / SR) * (0.5 + 0.5 * np.sin(2 * np.pi * 60 * t))
    x = bfilt(x + bfilt(white(d), "band", (2000, 6000), 2) * 0.2, "band", (400, 7000), 2) * bell_env(n, 0.5, 0.4)
    return stereo(x * 0.5)


def s_page_turn():
    d = 0.6
    n = int(d * SR)
    r = np.random.default_rng(305)
    env = bell_env(n, 0.4, 1.2)
    crinkle = (r.random(n) > 0.97) * r.standard_normal(n) * 0.6
    x = svf(pink(d, r) * 2, 1500 + 3000 * env, 0.8) * env + bfilt(crinkle, "high", 2500, 2) * env
    return reverb(stereo(x, np.linspace(-0.5, 0.5, n)), 0.3, 0.08)


def s_pen_scribble():
    d = 1.4
    n = int(d * SR)
    t = T(d)
    r = np.random.default_rng(306)
    amp = 0.4 + 0.6 * np.abs(np.sin(2 * np.pi * 3.7 * t + np.sin(2 * np.pi * 1.3 * t)))
    x = bfilt(r.standard_normal(n), "band", (2500, 9000), 2) * amp * fade(np.ones(n), 0.05, 0.1)
    return stereo(x * 0.5)


def s_zipper():
    d = 0.7
    n = int(d * SR)
    t = T(d)
    rate = 60 + 40 * (t / d)
    x = np.zeros(n)
    tt = 0.0
    r = np.random.default_rng(307)
    while tt < d - 0.01:
        c = click(0.004, r.uniform(2500, 5000), int(tt * 1e4))
        s = int(tt * SR)
        x[s:s + len(c)] += c * r.uniform(0.5, 1)
        tt += 1 / (60 + 40 * tt / d)
    return stereo(x * 0.7)


def s_door_slam():
    d = 1.5
    thud = np.tanh(2 * sine_sweep(expo(110, 50, int(0.4 * SR)))) * decay(0.4, 0.08)
    rattle = bfilt(white(0.3), "band", (400, 3000), 2) * decay(0.3, 0.04) * 0.5
    return reverb(mix(stereo(thud), stereo(rattle)), 1.2, 0.3)


def s_coins():
    r = np.random.default_rng(308)
    x = np.zeros(int(1.4 * SR))
    for i in range(14):
        t0 = abs(r.normal(0.15, 0.2))
        f = r.uniform(3000, 6500)
        c = tone(f, 0.4, r.uniform(0.05, 0.15), ((1, 1.0), (2.7, 0.4), (4.1, 0.2))) * r.uniform(0.3, 0.8)
        s = int(min(t0, 1.0) * SR)
        x[s:s + len(c)] += c
    return reverb(stereo(x * 0.5), 0.6, 0.15)


def s_magic_wand():
    d = 1.2
    t = T(d)
    f = 1200 + 2500 * (t / d)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * (0.5 + 0.5 * np.sin(2 * np.pi * 18 * t)) * bell_env(len(t), 0.3, 0.8)
    sparkle = sum(np.sin(2 * np.pi * fr * t) * np.exp(-np.maximum(0, t - i * 0.1) / 0.2) * (t >= i * 0.1)
                  for i, fr in enumerate((3136, 3951, 4699, 5274, 6272)))
    return reverb(stereo(x * 0.25 + sparkle * 0.15), 1.5, 0.4)


def s_level_complete():
    seq = [(523.3, 0.1), (659.3, 0.1), (784.0, 0.1), (1046.5, 0.1), (784.0, 0.1), (1046.5, 0.4)]
    parts = []
    for f, d in seq:
        x = np.sign(np.sin(2 * np.pi * f * T(d))) * 0.3 * np.minimum(1, (d - T(d)) / 0.02)
        x = x + np.sign(np.sin(2 * np.pi * f * 1.5 * T(d))) * 0.12
        parts.append(x)
    return reverb(stereo(bfilt(np.concatenate(parts), "low", 6000, 2)), 0.7, 0.15)


def s_notification_soft():
    a = tone(880, 0.6, 0.25, ((1, 1.0), (2, 0.2)))
    b = tone(1318.5, 0.9, 0.35, ((1, 1.0), (2, 0.2)))
    return reverb(mix(stereo(a), at(stereo(b), 0.09)), 1.0, 0.25)


def s_enter_key():
    a = add(click(0.006, 2200, 309), np.sin(2 * np.pi * 170 * T(0.05)) * decay(0.05, 0.012) * 0.6)
    return reverb(stereo(a), 0.2, 0.06)


def s_mouse_scroll():
    parts = [at(stereo(click(0.003, 4000, 310 + i) * (0.5 + 0.3 * (i % 2))), i * 0.045) for i in range(10)]
    return mix(*parts)


def s_timer_end():
    t = T(1.2)
    x = np.sin(2 * np.pi * 2093 * t) * ((t % 0.3) < 0.18) * 0.5
    return reverb(stereo(x), 0.4, 0.1)


def s_heartbeat_fast():
    def beat(f=60, a=1.0):
        d = 0.15
        return np.tanh(2 * sine_sweep(expo(f * 1.5, f, int(d * SR)))) * decay(d, 0.04) * a
    one = np.concatenate([beat(60), np.zeros(int(0.08 * SR)), beat(50, 0.7), np.zeros(int(0.22 * SR))])
    return stereo(np.tile(one, 4))


# ---------- ميمز ----------

def s_airhorn():
    d = 1.4
    n = int(d * SR)
    t = T(d)
    blasts = ((t < 0.18) | ((t > 0.26) & (t < 0.44)) | (t > 0.55)).astype(float)
    x = sum(saw_sweep(np.full(n, f) * (1 + 0.004 * np.sin(2 * np.pi * 6 * t))) for f in (466, 587, 698, 932))
    x = svf(x, 2500, 1.2, "low") * blasts
    x = fade(x, 0.005, 0.15)
    return reverb(stereo(np.tanh(x * 0.6)), 0.6, 0.15)


def s_whistle_up():
    d = 0.9
    n = int(d * SR)
    t = T(d)
    f = expo(900, 2400, n) * (1 + 0.012 * np.sin(2 * np.pi * 7 * t))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * bell_env(n, 0.75, 0.6) + bfilt(white(d), "band", (2000, 5000), 2) * 0.05
    return reverb(stereo(x * 0.5), 0.5, 0.12)


def s_wolf_whistle():
    d1, d2 = 0.35, 0.6
    a = np.sin(2 * np.pi * np.cumsum(expo(900, 2600, int(d1 * SR))) / SR) * bell_env(int(d1 * SR), 0.7, 0.6)
    f2 = np.concatenate([expo(1800, 2700, int(0.15 * SR)), expo(2700, 900, int((d2 - 0.15) * SR))])
    b = np.sin(2 * np.pi * np.cumsum(f2) / SR) * bell_env(len(f2), 0.3, 0.6)
    return reverb(stereo(np.concatenate([a, np.zeros(int(0.12 * SR)), b]) * 0.5), 0.5, 0.15)


def s_dun_dun():
    def hit(f, d):
        n = int(d * SR)
        x = sum(saw_sweep(np.full(n, f * k)) / k for k in (1, 1.5, 2))
        return svf(x, 900, 1.0, "low") * np.minimum(1, T(d) / 0.01) * np.exp(-T(d) / (d * 0.5))
    x = np.concatenate([hit(110, 0.35), np.zeros(int(0.1 * SR)), hit(104, 0.35), np.zeros(int(0.1 * SR)), hit(98, 1.4)])
    return reverb(stereo(x * 0.4), 2.0, 0.3)


def s_tada_short():
    a = bell(1046.5, 0.8, 0.3)
    b = bell(1568, 1.2, 0.5)
    return reverb(mix(stereo(a), at(stereo(b), 0.1)), 1.0, 0.2)


def s_record_rewind_long():
    d = 1.8
    n = int(d * SR)
    t = T(d)
    rate = 1 + 3 * (t / d) ** 2
    f = np.array([392, 494, 587])
    x = sum(np.sin(2 * np.pi * np.cumsum(-fr * rate) / SR) for fr in f) * 0.2
    x = x + bfilt(white(d), "band", (1500, 6000), 2) * 0.06 * rate / 4
    return stereo(x * bell_env(n, 0.85, 0.5))


# ---------- أجواء طبيعة ----------

def _chirp(f0, f1, d, seed):
    n = int(d * SR)
    r = np.random.default_rng(seed)
    f = expo(f0, f1, n) * (1 + 0.04 * np.sin(2 * np.pi * r.uniform(20, 40) * T(d)))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * bell_env(n, 0.3, 1.0)


def s_forest_birds():
    d = 8.0
    r = np.random.default_rng(320)
    n = int(d * SR)
    bed = svf(pink(d, r) * 0.6, 900, 0.7) * 0.25
    x = np.zeros((n, 2))
    x[:, 0] += bed
    x[:, 1] += bed
    for i in range(40):
        t0 = r.uniform(0, d - 0.6)
        kind = r.integers(0, 3)
        if kind == 0:
            c = np.concatenate([_chirp(r.uniform(3000, 4500), r.uniform(4500, 6500), r.uniform(0.05, 0.1), 400 + i * 3 + k)
                                for k in range(int(r.integers(2, 5)))])
        elif kind == 1:
            c = _chirp(r.uniform(5000, 6500), r.uniform(2500, 3500), r.uniform(0.15, 0.3), 500 + i)
        else:
            f0 = r.uniform(2300, 3800)
            c = np.concatenate([np.concatenate([_chirp(f0 * (1 + 0.03 * k), f0 * 1.12, 0.05, 600 + i * 7 + k),
                                                np.zeros(int(r.uniform(0.02, 0.06) * SR))])
                                for k in range(int(r.integers(2, 5)))])
        st = stereo(c * r.uniform(0.15, 0.45) * 0.4, r.uniform(-0.9, 0.9))
        s = int(t0 * SR)
        e = min(n, s + len(st))
        x[s:e] += st[: e - s]
    return reverb(fade(x, 1.0, 1.0), 1.2, 0.2, damp=7000)


def s_ocean_waves():
    d = 10.0
    t = T(d)
    r = np.random.default_rng(321)
    swell = (0.5 + 0.5 * np.sin(2 * np.pi * t / 5.0 - 1.5)) ** 2
    x = svf(pink(d, r) * 2, 300 + 2500 * swell, 0.6) * (0.3 + 0.7 * swell)
    hiss = bfilt(white(d, r), "high", 3000, 2) * swell ** 3 * 0.15
    return fade(stereo(x + hiss, 0.3 * np.sin(2 * np.pi * t / 9)), 1.0, 1.0)


def s_stream():
    d = 8.0
    r = np.random.default_rng(322)
    n = int(d * SR)
    base = svf(pink(d, r) * 1.5, 1800, 0.8) * 0.35
    x = np.zeros(n)
    for i in range(500):
        f = r.uniform(600, 2200)
        dd = r.uniform(0.02, 0.06)
        bub = np.sin(2 * np.pi * np.cumsum(expo(f, f * 1.6, int(dd * SR))) / SR) * bell_env(int(dd * SR), 0.2, 1.0)
        s = r.integers(0, n - len(bub))
        x[s:s + len(bub)] += bub * r.uniform(0.05, 0.2)
    return fade(stereo(base + x, 0.0), 1.0, 1.0)


def s_campfire():
    d = 8.0
    r = np.random.default_rng(323)
    n = int(d * SR)
    roar = svf(brown(d, r) * 2, 350, 0.7) * 0.5
    crack = np.zeros(n)
    for i in range(160):
        c = click(r.uniform(0.002, 0.008), r.uniform(1500, 6000), 700 + i) * r.uniform(0.2, 1.0)
        s = r.integers(0, n - 500)
        crack[s:s + len(c)] += c
    return fade(stereo(roar + crack * 0.8), 1.0, 1.0)


def s_night_ambience():
    d = 8.0
    t = T(d)
    r = np.random.default_rng(324)
    bed = svf(pink(d, r) * 0.5, 600, 0.7) * 0.2
    cr = np.sin(2 * np.pi * 4400 * t) * (np.sin(2 * np.pi * 28 * t) > 0) * ((t % 1.3) < 0.35) * 0.08
    cr2 = np.sin(2 * np.pi * 3900 * t) * (np.sin(2 * np.pi * 31 * t) > 0) * (((t + 0.6) % 1.7) < 0.3) * 0.06
    return fade(mix(stereo(bed), stereo(cr, -0.6), stereo(cr2, 0.6)), 1.0, 1.0)


def s_thunder_roll():
    d = 6.0
    t = T(d)
    r = np.random.default_rng(325)
    env = np.exp(-t / 2.2) * (0.6 + 0.4 * np.abs(np.sin(2 * np.pi * 0.7 * t + np.sin(2 * np.pi * 0.3 * t))))
    env *= np.minimum(1, t / 0.4)
    x = bfilt(brown(d, r), "low", 180, 4) * env * 2 + bfilt(pink(d, r), "band", (200, 1200), 2) * env * 0.3
    return reverb(stereo(x), 2.5, 0.3)


def s_wind_gust():
    d = 3.0
    n = int(d * SR)
    env = bell_env(n, 0.45, 1.5)
    x = svf(pink(d) * 2 + brown(d), 300 + 1500 * env, 3.0) * env
    return stereo(x, np.linspace(-0.7, 0.7, n))


SFX3 = {
    "kick":              (s_kick,              "طبول", "طبلة كيك"),
    "snare":             (s_snare,             "طبول", "سنير"),
    "clap":              (s_clap,              "طبول", "تصفيقة"),
    "hihat":             (s_hihat,             "طبول", "هاي هات مغلق"),
    "open-hat":          (s_open_hat,          "طبول", "هاي هات مفتوح"),
    "tom-fill":          (s_tom_fill,          "طبول", "فيل طبول نازل"),
    "beat-4":            (s_beat_4,            "طبول", "إيقاع جاهز ثانيتين"),
    "cymbal-swell":      (s_cymbal_swell,      "طبول", "صنج يتصاعد"),
    "uplifter":          (s_uplifter,          "انتقالات", "رايزر هوائي"),
    "sub-whoosh":        (s_sub_whoosh,        "انتقالات", "ووش باص عميق"),
    "digital-transition": (s_digital_transition, "انتقالات", "انتقال رقمي"),
    "glitch-stutter":    (s_glitch_stutter,    "انتقالات", "تقطيع غلتش"),
    "vinyl-scratch-short": (s_vinyl_scratch_short, "انتقالات", "سكراتش قصير"),
    "camera-zoom-whir":  (s_camera_zoom_whir,  "واقعية", "محرك زوم كاميرا"),
    "page-turn":         (s_page_turn,         "واقعية", "قلب صفحة"),
    "pen-scribble":      (s_pen_scribble,      "واقعية", "شخبطة قلم"),
    "zipper":            (s_zipper,            "واقعية", "سحّاب"),
    "door-slam":         (s_door_slam,         "واقعية", "إغلاق باب بقوة"),
    "coins":             (s_coins,             "واقعية", "عملات معدنية"),
    "magic-wand":        (s_magic_wand,        "واجهات", "عصا سحرية"),
    "level-complete":    (s_level_complete,    "واجهات", "إنهاء مرحلة"),
    "notification-soft": (s_notification_soft, "واجهات", "تنبيه ناعم"),
    "enter-key":         (s_enter_key,         "واجهات", "زر Enter"),
    "mouse-scroll":      (s_mouse_scroll,      "واجهات", "تمرير الماوس"),
    "timer-end":         (s_timer_end,         "واجهات", "انتهاء المؤقت"),
    "heartbeat-fast":    (s_heartbeat_fast,    "واجهات", "نبض سريع (توتر)"),
    "airhorn":           (s_airhorn,           "ميمز", "بوق الاحتفال (Airhorn)"),
    "whistle-up":        (s_whistle_up,        "ميمز", "صفرة صاعدة"),
    "wolf-whistle":      (s_wolf_whistle,      "ميمز", "صفرة إعجاب"),
    "dun-dun":           (s_dun_dun,           "ميمز", "دن دن (درامي)"),
    "tada-short":        (s_tada_short,        "ميمز", "تادا قصيرة"),
    "record-rewind-long": (s_record_rewind_long, "ميمز", "ترجيع طويل"),
    "forest-birds":      (s_forest_birds,      "طبيعة", "عصافير في غابة"),
    "ocean-waves":       (s_ocean_waves,       "طبيعة", "أمواج بحر"),
    "stream":            (s_stream,            "طبيعة", "جدول ماء"),
    "campfire":          (s_campfire,          "طبيعة", "نار مخيم"),
    "night-ambience":    (s_night_ambience,    "طبيعة", "ليل وصراصير"),
    "thunder-roll":      (s_thunder_roll,      "طبيعة", "رعد متدحرج"),
    "wind-gust":         (s_wind_gust,         "طبيعة", "هبّة ريح"),
}
