"""مؤثرات صوتية جديدة 2026."""
import math
import numpy as np

from .sfx import (SR, T, white, pink, brown, sine_sweep, saw_sweep, square_sweep, lin, expo, decay, bell_env,
                  svf, bfilt, stereo, reverb, mix, at, add, click, tone, bell, pluck, whoosh, cymbal, glitch,
                  s_impact_boom, s_sub_drop, s_thud, s_punch, s_crash)


# ---------- انتقالات حديثة ----------

def s_whoosh_cinematic():
    w = whoosh(1.3, 200, 2500, 0.7, q=1.3, seed=201, sub=True, verb=0)
    hit = at(s_thud() * 0.7, 0.85)
    return reverb(mix(w, hit), 1.8, 0.3)


def s_bass_whoosh():
    d = 0.9
    n = int(d * SR)
    env = bell_env(n, 0.7, 2.0)
    sub = np.tanh(2 * sine_sweep(expo(40, 120, n))) * env
    air = svf(pink(d) * 2, 300 + 2500 * env, 1.2) * env * 0.5
    return reverb(stereo(sub + air, np.linspace(-0.6, 0.6, n)), 0.8, 0.15)


def s_glitch_whoosh():
    w = whoosh(0.7, 400, 4000, 0.55, seed=202, verb=0)
    g = glitch(0.35, 203) * 0.8
    return reverb(mix(w, at(g, 0.3)), 0.6, 0.12)


def s_swoosh_up():
    d = 0.5
    n = int(d * SR)
    env = np.linspace(0, 1, n) ** 1.5 * np.minimum(1, np.linspace(10, 0, n))
    x = svf(pink(d) * 2, expo(500, 8000, n), 1.4) * env
    s = sine_sweep(expo(300, 1500, n)) * env * 0.25
    return reverb(stereo(x + s), 0.5, 0.12)


def s_swoosh_down():
    return s_swoosh_up()[::-1].copy()


def s_riser_hit():
    d = 2.0
    n = int(d * SR)
    t = T(d)
    p = t / d
    nz = svf(pink(d) * 2, 300 * (25 ** p), 2.0) * p ** 2
    tonal = saw_sweep(expo(200, 1200, n)) * p ** 2 * 0.3
    r = stereo(nz + svf(tonal, 400 + 4000 * p, 1.0, "low"))
    return reverb(mix(r, at(s_impact_boom(), d)), 1.5, 0.2)


def s_reverse_hit():
    x = s_impact_boom()[:int(1.4 * SR)]
    return x[::-1].copy()


def s_tape_whoosh():
    d = 0.7
    n = int(d * SR)
    t = T(d)
    w = whoosh(d, 300, 3000, 0.5, seed=204, verb=0)[:n]
    wob = (1 + 0.5 * np.sin(2 * np.pi * 9 * t))[:, None]
    return reverb(w * wob, 0.5, 0.12)


def s_portal():
    d = 2.0
    n = int(d * SR)
    t = T(d)
    f = 120 + 80 * np.sin(2 * np.pi * 3 * t) + 400 * (t / d)
    x = sum(np.sin(2 * np.pi * np.cumsum(f * k) / SR) / k for k in (1, 1.5, 2.01, 3.02))
    x = x * bell_env(n, 0.5, 1.2)
    sw = svf(pink(d) * 2, 400 + 3000 * bell_env(n, 0.5, 1.0), 3.0) * 0.4 * bell_env(n, 0.5, 1)
    return reverb(stereo(x * 0.4 + sw, np.sin(2 * np.pi * 1.5 * t) * 0.7), 2.0, 0.35)


def s_teleport():
    d = 0.6
    n = int(d * SR)
    t = T(d)
    f = expo(200, 3000, n)
    x = sine_sweep(f) * np.sign(np.sin(2 * np.pi * 40 * t)).clip(0, 1) * decay(d, 0.3)
    return reverb(stereo(x * 0.5 + bfilt(white(d), "high", 4000, 2) * decay(d, 0.1) * 0.3), 0.8, 0.25)


def s_warp():
    d = 1.2
    n = int(d * SR)
    t = T(d)
    f = expo(80, 2000, n) * (1 + 0.3 * np.sin(2 * np.pi * 12 * t))
    x = saw_sweep(f) + saw_sweep(f * 1.01)
    x = svf(x, expo(200, 8000, n), 2.0, "low") * bell_env(n, 0.8, 1.5)
    return reverb(stereo(x * 0.4), 1.0, 0.2)


# ---------- ضربات حديثة ----------

def s_metal_hit():
    d = 2.2
    t = T(d)
    partials = [(523, 1.4), (747, 1.0), (1011, 0.8), (1388, 0.6), (1761, 0.45), (2296, 0.3), (2950, 0.2)]
    x = sum(np.sin(2 * np.pi * f * t) * np.exp(-t / tau) for f, tau in partials) / 4
    x = x + bfilt(white(d), "band", (1000, 6000), 2) * decay(d, 0.02)
    return reverb(stereo(x), 1.5, 0.25)


def s_hit_reverb():
    x = mix(s_punch(), stereo(bfilt(white(0.3), "low", 3000, 2) * decay(0.3, 0.05)))
    return reverb(x, 3.0, 0.5)


def s_trap_808():
    d = 1.5
    n = int(d * SR)
    f = 55 * (1 + 2 * np.exp(-T(d) / 0.03))
    x = np.tanh(2.2 * sine_sweep(f)) * decay(d, 0.6)
    return stereo(x)


def s_slap():
    d = 0.25
    x = bfilt(white(d), "band", (600, 5000), 2) * decay(d, 0.012) * 1.5
    x = add(x, np.sin(2 * np.pi * 180 * T(0.08)) * decay(0.08, 0.02) * 0.6)
    return reverb(stereo(x), 0.3, 0.12)


def s_bonk():
    d = 0.6
    t = T(d)
    x = sum(np.sin(2 * np.pi * f * t) * np.exp(-t / tau) for f, tau in ((440, 0.25), (1210, 0.08), (2380, 0.04)))
    x = add(x, click(0.01, 2500, 206))
    return reverb(stereo(x * 0.6), 0.4, 0.1)


def s_heartbeat_boom():
    beats = [at(stereo(np.tanh(2 * sine_sweep(expo(90, 45, int(0.2 * SR))) * decay(0.2, 0.06))), t0)
             for t0 in (0, 0.25, 0.9, 1.15)]
    return reverb(mix(*beats, at(s_impact_boom() * 0.9, 1.8)), 1.5, 0.2)


def s_glass_break():
    d = 1.6
    r = np.random.default_rng(207)
    n = int(d * SR)
    x = np.zeros(n)
    for i in range(60):
        t0 = abs(r.normal(0, 0.12))
        dd = r.uniform(0.1, 0.6)
        f = r.uniform(2500, 9000)
        tt = T(dd)
        shard = np.sin(2 * np.pi * f * tt) * np.exp(-tt / (dd / 4)) * r.uniform(0.2, 1)
        s = int(t0 * SR)
        x[s:s + len(shard)] += shard[: n - s]
    crash = bfilt(white(d), "high", 2500, 2) * decay(d, 0.08)
    return reverb(stereo(x * 0.3 + crash * 0.8), 1.0, 0.2)


def s_ice_crack():
    r = np.random.default_rng(208)
    x = np.zeros(int(0.8 * SR))
    for i in range(12):
        c = click(0.01, r.uniform(1500, 6000), 300 + i) * r.uniform(0.4, 1.0)
        s = int(r.uniform(0, 0.5) * SR)
        x[s:s + len(c)] += c
    x = add(x, np.sin(2 * np.pi * 120 * T(0.3)) * decay(0.3, 0.08) * 0.3)
    return reverb(stereo(x), 0.8, 0.25)


# ---------- واجهات ونوتيفيكيشن حديثة ----------

def s_pop_modern():
    d = 0.18
    n = int(d * SR)
    x = sine_sweep(expo(300, 900, n)) * bell_env(n, 0.08, 1.2)
    x = x + 0.3 * sine_sweep(expo(600, 1800, n)) * bell_env(n, 0.05, 1.5)
    return reverb(stereo(x), 0.3, 0.1)


def s_ui_hover():
    return reverb(stereo(tone(1800, 0.08, 0.02) * 0.5 + tone(2700, 0.08, 0.015) * 0.2), 0.3, 0.1)


def s_ui_confirm():
    a = tone(880, 0.12, 0.05)
    b = tone(1320, 0.25, 0.1)
    return reverb(stereo(np.concatenate([a, b])), 0.5, 0.12)


def s_pluck_notify():
    a = pluck(988, 0.5, 0.993, 1)
    b = pluck(1319, 0.8, 0.995, 2)
    return reverb(mix(stereo(a * 0.6), at(stereo(b * 0.6), 0.1)), 0.8, 0.2)


def s_phone_vibrate():
    d = 1.4
    t = T(d)
    gate = ((t % 0.7) < 0.45).astype(float)
    x = (np.sin(2 * np.pi * 170 * t) + 0.5 * np.sign(np.sin(2 * np.pi * 85 * t))) * gate
    x = bfilt(x, "low", 600, 2) * (0.7 + 0.3 * np.sin(2 * np.pi * 30 * t))
    return stereo(x * 0.5)


def s_camera_focus():
    beeps = [at(stereo(tone(3200, 0.07, 0.03) * 0.5), t0) for t0 in (0, 0.12)]
    servo = at(stereo(bfilt(white(0.25), "band", (2000, 6000), 2) * bell_env(int(0.25 * SR), 0.5, 1) * 0.25), 0.25)
    return mix(*beeps, servo)


def s_shutter_burst():
    one = np.concatenate([click(0.004, 3000, 210), bfilt(white(0.025), "band", (1500, 6000), 2) * 0.3,
                          click(0.004, 2000, 211) * 0.8])
    gap = np.zeros(int(0.07 * SR))
    return reverb(stereo(np.concatenate([one, gap] * 6)), 0.3, 0.08)


def s_typing_soft():
    r = np.random.default_rng(212)
    x = np.zeros(int(1.6 * SR))
    t = 0.02
    while t < 1.5:
        d = 0.03
        k = bfilt(r.standard_normal(int(d * SR)), "band", (800, 3000), 2) * decay(d, 0.005) * r.uniform(0.5, 1)
        s = int(t * SR)
        x[s:s + len(k)] += k
        t += r.uniform(0.07, 0.16)
    return reverb(stereo(x), 0.2, 0.06)


def s_ding_dong():
    a = bell(659.3, 1.5, 0.6)
    b = bell(523.3, 1.8, 0.7)
    return reverb(mix(stereo(a), at(stereo(b), 0.45)), 1.2, 0.2)


def s_subscribe_ding():
    a = bell(1568, 0.9, 0.35)
    b = bell(2093, 1.2, 0.45)
    c = bell(2637, 1.4, 0.5)
    return reverb(mix(stereo(a, -0.3), at(stereo(b), 0.07), at(stereo(c, 0.3), 0.14)), 1.2, 0.25)


def s_radar_ping():
    x = tone(1400, 2.0, 0.6, ((1, 1.0), (2.01, 0.15)))
    return reverb(stereo(x * 0.6), 2.5, 0.45)


def s_robot_beeps():
    r = np.random.default_rng(213)
    seg = []
    for _ in range(9):
        d = r.uniform(0.04, 0.12)
        f = r.choice([440, 660, 880, 1320, 990])
        seg.append(np.sign(np.sin(2 * np.pi * f * T(d))) * 0.35 * decay(d, d))
        seg.append(np.zeros(int(r.uniform(0.01, 0.05) * SR)))
    return reverb(stereo(bfilt(np.concatenate(seg), "low", 5000, 2)), 0.3, 0.1)


def s_electric_zap():
    d = 0.5
    r = np.random.default_rng(214)
    n = int(d * SR)
    x = np.sign(np.sin(2 * np.pi * 60 * T(d))) * 0.3 + r.standard_normal(n) * (r.random(n) > 0.7)
    x = bfilt(x, "band", (300, 8000), 2) * bell_env(n, 0.1, 0.6)
    return reverb(stereo(x * 0.6), 0.5, 0.15)


def s_sci_fi_scan():
    d = 1.5
    n = int(d * SR)
    t = T(d)
    f = 800 + 600 * np.sin(2 * np.pi * 2 * t)
    x = sine_sweep(f) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 16 * t))) * bell_env(n, 0.5, 0.5)
    return reverb(stereo(x * 0.4, np.sin(2 * np.pi * 0.7 * t)), 1.0, 0.25)


# ---------- ميمز وكوميدي ----------

def s_crickets():
    d = 3.0
    t = T(d)
    out = np.zeros(len(t))
    for k, (f, off) in enumerate(((4200, 0.0), (4600, 0.35))):
        chirp = np.sin(2 * np.pi * f * t) * ((np.sin(2 * np.pi * 30 * t) > 0) * 1.0)
        gate = (((t + off) % 0.9) < 0.25).astype(float)
        out += chirp * gate * 0.3
    return reverb(stereo(bfilt(out, "band", (3000, 6000), 2)), 1.0, 0.2)


def s_magic_poof():
    d = 0.8
    n = int(d * SR)
    puff = svf(pink(d) * 2, expo(3000, 400, n), 0.8) * decay(d, 0.15)
    sh = sum(np.sin(2 * np.pi * f * T(d)) * decay(d, 0.25) for f in (2637, 3136, 3951)) * 0.15
    return reverb(stereo(puff + sh), 1.0, 0.3)


def s_anime_sparkle():
    d = 1.2
    t = T(d)
    x = sum(np.sin(2 * np.pi * f * t) * np.exp(-np.maximum(0, t - i * 0.05) / 0.25) * (t >= i * 0.05)
            for i, f in enumerate((2093, 2637, 3136, 4186, 5274)))
    return reverb(stereo(x * 0.25), 1.5, 0.45, damp=10000)


def s_anime_swoosh():
    return whoosh(0.35, 2000, 10000, 0.3, q=0.6, seed=215, pan=(-1, 1), verb=0.15)


def s_jump_8bit():
    d = 0.25
    n = int(d * SR)
    x = np.sign(np.sin(2 * np.pi * np.cumsum(expo(300, 900, n)) / SR)) * decay(d, 0.12) * 0.4
    return stereo(bfilt(x, "low", 6000, 2))


def s_game_over():
    notes = [(392, 0.25), (370, 0.25), (349, 0.25), (330, 0.7)]
    seg = [np.sign(np.sin(2 * np.pi * f * T(d))) * 0.35 * np.minimum(1, (d - T(d)) / 0.05) for f, d in notes]
    return reverb(stereo(bfilt(np.concatenate(seg), "low", 5000, 2)), 0.6, 0.15)


def s_balloon_pop():
    d = 0.3
    x = bfilt(white(d), "band", (400, 7000), 2) * decay(d, 0.01) * 2
    x = add(x, np.sin(2 * np.pi * 90 * T(0.1)) * decay(0.1, 0.03))
    return reverb(stereo(x), 0.6, 0.18)


def s_water_drop():
    d = 0.3
    n = int(d * SR)
    x = sine_sweep(expo(500, 1600, n)) * bell_env(n, 0.05, 1.5)
    return reverb(stereo(x * 0.6), 0.6, 0.25)


def s_splash():
    d = 1.2
    r = np.random.default_rng(216)
    n = int(d * SR)
    x = svf(pink(d, r) * 2, expo(4000, 800, n), 0.7) * decay(d, 0.25)
    for i in range(25):
        dr = s_water_drop()[:, 0] * r.uniform(0.1, 0.3)
        s = int(r.uniform(0.05, 0.8) * SR)
        x[s:s + len(dr)] += dr[: n - s]
    return reverb(stereo(x), 0.8, 0.2)


def s_fire_whoosh():
    d = 1.4
    n = int(d * SR)
    r = np.random.default_rng(217)
    env = bell_env(n, 0.35, 1.5)
    roar = svf(brown(d, r) * 3 + pink(d, r), 300 + 1500 * env, 1.0) * env
    crackle = (r.random(n) > 0.995) * r.standard_normal(n) * 2 * env
    return reverb(stereo(roar + bfilt(crackle, "high", 2000, 2), np.linspace(-0.5, 0.5, n)), 1.0, 0.2)


def s_lightning_crack():
    d = 3.0
    r = np.random.default_rng(218)
    crack = bfilt(white(0.15, r), "high", 1500, 2) * decay(0.15, 0.03) * 2
    rumble = bfilt(brown(d, r), "low", 200, 4) * decay(d, 0.9) * np.minimum(1, T(d) / 0.1) * 2
    return reverb(mix(stereo(crack), stereo(rumble)), 2.0, 0.3)


def s_clock_alarm():
    t = T(1.6)
    x = np.sign(np.sin(2 * np.pi * 2000 * t)) * (np.sin(2 * np.pi * 16 * t) > 0) * (((t % 0.4) < 0.25))
    return stereo(bfilt(x, "band", (1000, 6000), 2) * 0.4)


def s_cinematic_rise():
    d = 4.0
    n = int(d * SR)
    t = T(d)
    p = t / d
    pulse = (np.sin(2 * np.pi * np.cumsum(1 + 14 * p ** 2) / SR) > 0).astype(float)
    hits = np.tanh(2 * np.sin(2 * np.pi * 55 * t)) * pulse * p
    strings = sum(saw_sweep(np.full(n, f) * (1 + 0.5 * p)) for f in (220, 220.8, 330, 440.5))
    strings = svf(strings, 300 + 4000 * p, 1.0, "low") * p ** 2 * 0.25
    return reverb(stereo(hits * 0.5 + strings), 2.0, 0.3)


def s_success_fanfare():
    seq = [(523.3, 0.12), (659.3, 0.12), (784.0, 0.12), (1046.5, 0.5)]
    out = []
    for f, d in seq:
        n = int(d * SR)
        tt = T(d)
        x = sum(saw_sweep(np.full(n, f * k)) / k for k in (1, 2.003))
        x = svf(x, 1500 + 2000 * np.exp(-tt / 0.1), 1.0, "low") * np.minimum(1, tt / 0.01) * np.exp(-tt / (d * 0.9))
        out.append(x)
    return reverb(stereo(np.concatenate(out) * 0.35), 1.2, 0.2)


def s_deep_drone():
    d = 6.0
    n = int(d * SR)
    t = T(d)
    x = sum(np.sin(2 * np.pi * f * t + np.sin(2 * np.pi * 0.2 * t) * k) for k, f in enumerate((41.2, 61.7, 82.4, 123.5)))
    x = np.tanh(x * 0.6) * np.minimum(1, t / 1.5) * np.minimum(1, (d - t) / 1.0)
    return reverb(stereo(x * 0.6), 3.0, 0.3)


def s_lofi_vinyl_stop():
    d = 1.5
    n = int(d * SR)
    t = T(d)
    rate = np.clip(1 - t / d, 0, 1) ** 2
    x = sum(np.sin(2 * np.pi * np.cumsum(f * rate) / SR) for f in (261.6, 329.6, 392.0)) * 0.3
    x = svf(x, 400 + 3000 * rate, 0.8, "low")
    noise = bfilt(white(d), "band", (500, 4000), 2) * 0.03
    return stereo(x + noise)


SFX2 = {
    "whoosh-cinematic": (s_whoosh_cinematic, "انتقالات", "ووش سينمائي مع ضربة"),
    "bass-whoosh":      (s_bass_whoosh,      "انتقالات", "ووش باص"),
    "glitch-whoosh":    (s_glitch_whoosh,    "انتقالات", "ووش مع غلتش"),
    "swoosh-up":        (s_swoosh_up,        "انتقالات", "سووش صاعد"),
    "swoosh-down":      (s_swoosh_down,      "انتقالات", "سووش نازل"),
    "tape-whoosh":      (s_tape_whoosh,      "انتقالات", "ووش شريط متموج"),
    "riser-hit":        (s_riser_hit,        "تصاعد", "تصاعد ينتهي بضربة"),
    "reverse-hit":      (s_reverse_hit,      "تصاعد", "ضربة معكوسة"),
    "cinematic-rise":   (s_cinematic_rise,   "تصاعد", "تصاعد سينمائي بنبض"),
    "portal":           (s_portal,           "خيال علمي", "بوابة"),
    "teleport":         (s_teleport,         "خيال علمي", "انتقال آني"),
    "warp":             (s_warp,             "خيال علمي", "قفزة فضائية"),
    "sci-fi-scan":      (s_sci_fi_scan,      "خيال علمي", "مسح ضوئي"),
    "robot-beeps":      (s_robot_beeps,      "خيال علمي", "روبوت"),
    "electric-zap":     (s_electric_zap,     "خيال علمي", "صعقة كهرباء"),
    "radar-ping":       (s_radar_ping,       "خيال علمي", "رادار"),
    "metal-hit":        (s_metal_hit,        "ضربات", "ضربة معدن"),
    "hit-reverb":       (s_hit_reverb,       "ضربات", "ضربة بصدى"),
    "trap-808":         (s_trap_808,         "ضربات", "باص 808"),
    "slap":             (s_slap,             "ضربات", "صفعة"),
    "heartbeat-boom":   (s_heartbeat_boom,   "ضربات", "نبضتين ثم بوم"),
    "glass-break":      (s_glass_break,      "ضربات", "تكسير زجاج"),
    "ice-crack":        (s_ice_crack,        "ضربات", "تشقق جليد"),
    "lightning-crack":  (s_lightning_crack,  "ضربات", "رعد"),
    "pop-modern":       (s_pop_modern,       "واجهات", "بوب حديث"),
    "ui-hover":         (s_ui_hover,         "واجهات", "مرور على زر"),
    "ui-confirm":       (s_ui_confirm,       "واجهات", "تأكيد"),
    "pluck-notify":     (s_pluck_notify,     "واجهات", "تنبيه نقر وتر"),
    "subscribe-ding":   (s_subscribe_ding,   "واجهات", "جرس اشتراك"),
    "ding-dong":        (s_ding_dong,        "واجهات", "جرس باب"),
    "phone-vibrate":    (s_phone_vibrate,    "واجهات", "اهتزاز جوال"),
    "camera-focus":     (s_camera_focus,     "واجهات", "تركيز كاميرا"),
    "shutter-burst":    (s_shutter_burst,    "واجهات", "تصوير متتابع"),
    "typing-soft":      (s_typing_soft,      "واجهات", "كتابة ناعمة"),
    "clock-alarm":      (s_clock_alarm,      "واجهات", "منبه"),
    "bonk":             (s_bonk,             "ميمز", "بونك"),
    "crickets":         (s_crickets,         "ميمز", "صراصير (صمت محرج)"),
    "magic-poof":       (s_magic_poof,       "ميمز", "بوف سحري"),
    "anime-sparkle":    (s_anime_sparkle,    "ميمز", "لمعة أنمي"),
    "anime-swoosh":     (s_anime_swoosh,     "ميمز", "سووش أنمي"),
    "jump-8bit":        (s_jump_8bit,        "ميمز", "قفزة 8bit"),
    "game-over":        (s_game_over,        "ميمز", "خسارة لعبة"),
    "success-fanfare":  (s_success_fanfare,  "ميمز", "احتفال فوز"),
    "balloon-pop":      (s_balloon_pop,      "واقعية", "انفجار بالون"),
    "water-drop":       (s_water_drop,       "واقعية", "قطرة ماء"),
    "splash":           (s_splash,           "واقعية", "رشة ماء"),
    "fire-whoosh":      (s_fire_whoosh,      "واقعية", "اشتعال نار"),
    "deep-drone":       (s_deep_drone,       "موسيقية", "خلفية عميقة"),
    "lofi-vinyl-stop":  (s_lofi_vinyl_stop,  "موسيقية", "توقف لوفاي"),
}
