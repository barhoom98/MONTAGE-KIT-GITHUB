"""
مؤثرات صوتية مولّدة بالكامل بالكود (بدون حقوق، حرة الاستخدام).
كل دالة ترجع مصفوفة ستيريو (N, 2) بقيم بين -1 و 1 بتردد 48kHz.
"""
import math
import numpy as np
from scipy.signal import fftconvolve, butter, sosfilt

SR = 48000
RNG = np.random.default_rng(7)


# =================== أدوات أساسية ===================

def T(d):
    return np.arange(int(d * SR)) / SR


def white(d, rng=None):
    return (rng or RNG).standard_normal(int(d * SR))


def pink(d, rng=None):
    n = int(d * SR)
    w = (rng or RNG).standard_normal(n)
    f = np.fft.rfft(w)
    k = np.arange(len(f))
    k[0] = 1
    y = np.fft.irfft(f / np.sqrt(k), n)
    return y / (np.abs(y).max() + 1e-9)


def brown(d, rng=None):
    y = np.cumsum((rng or RNG).standard_normal(int(d * SR)))
    y = y - np.convolve(y, np.ones(4801) / 4801, mode="same")
    return y / (np.abs(y).max() + 1e-9)


def sine_sweep(f, phase0=0.0):
    """f: مصفوفة ترددات لكل عينة."""
    return np.sin(phase0 + 2 * np.pi * np.cumsum(f) / SR)


def saw_sweep(f):
    ph = np.cumsum(f) / SR
    return 2 * (ph - np.floor(ph + 0.5))


def square_sweep(f):
    return np.sign(sine_sweep(f))


def lin(a, b, n):
    return np.linspace(a, b, n)


def expo(a, b, n):
    return a * (b / a) ** np.linspace(0, 1, n)


def decay(d, tau, n=None):
    t = T(d) if n is None else np.arange(n) / SR
    return np.exp(-t / tau)


def bell_env(n, peak=0.6, sharp=2.0):
    x = np.linspace(0, 1, n)
    up = (x / peak) ** sharp
    down = ((1 - x) / (1 - peak)) ** sharp
    return np.where(x < peak, up, down)


def svf(x, fc, q=0.707, mode="band"):
    """فلتر متغير التردد (TPT state-variable). fc رقم أو مصفوفة."""
    n = len(x)
    fc = np.broadcast_to(np.clip(np.asarray(fc, float), 20, SR * 0.45), (n,))
    g = np.tan(np.pi * fc / SR)
    k = 1.0 / q
    a1 = 1.0 / (1.0 + g * (g + k))
    a2 = g * a1
    a3 = g * a2
    out = np.empty(n)
    ic1 = ic2 = 0.0
    m = {"low": 0, "band": 1, "high": 2}[mode]
    xl, a1l, a2l, a3l = x.tolist(), a1.tolist(), a2.tolist(), a3.tolist()
    o = [0.0] * n
    for i in range(n):
        v3 = xl[i] - ic2
        v1 = a1l[i] * ic1 + a2l[i] * v3
        v2 = ic2 + a2l[i] * ic1 + a3l[i] * v3
        ic1 = 2 * v1 - ic1
        ic2 = 2 * v2 - ic2
        o[i] = v2 if m == 0 else (v1 if m == 1 else xl[i] - k * v1 - v2)
    out[:] = o
    return out


def bfilt(x, kind, f, order=4):
    sos = butter(order, f, btype=kind, fs=SR, output="sos")
    return sosfilt(sos, x)


def fade(x, fin=0.003, fout=0.01):
    x = x.copy()
    a, b = int(fin * SR), int(fout * SR)
    if a:
        x[:a] *= np.linspace(0, 1, a)[:, None] if x.ndim == 2 else np.linspace(0, 1, a)
    if b:
        x[-b:] *= np.linspace(1, 0, b)[:, None] if x.ndim == 2 else np.linspace(1, 0, b)
    return x


def stereo(x, pan=0.0):
    """pan: رقم من -1 (يسار) إلى 1 (يمين) أو مصفوفة متغيرة."""
    p = (np.asarray(pan, float) + 1) * np.pi / 4
    return np.stack([x * np.cos(p), x * np.sin(p)], axis=1) * math.sqrt(2)


def reverb(st, size=1.2, mix=0.25, damp=4000, seed=3):
    r = np.random.default_rng(seed)
    n = int(size * SR)
    t = np.arange(n) / SR
    env = np.exp(-t / (size / 5))
    irs = []
    for _ in range(2):
        ir = r.standard_normal(n) * env
        ir = bfilt(ir, "low", damp, 2)
        ir[: int(0.012 * SR)] = 0
        irs.append(ir / np.sqrt((ir ** 2).sum()))
    tail = np.zeros((len(st) + n, 2))
    for c in range(2):
        y = fftconvolve(st[:, c], irs[c])[: len(st) + n]
        tail[: len(y), c] = y
    dry = np.vstack([st, np.zeros((n, 2))])
    return dry * (1 - mix) + tail * mix * 3


def mix(*parts):
    n = max(len(p) for p in parts)
    out = np.zeros((n, 2))
    for p in parts:
        if p.ndim == 1:
            p = stereo(p)
        out[: len(p)] += p
    return out


def at(x, t0):
    """إزاحة صوت ليبدأ عند الثانية t0."""
    pad = np.zeros((int(t0 * SR),) + x.shape[1:])
    return np.concatenate([pad, x])


def trim_silence(x, thr=1e-4):
    a = np.abs(x).max(axis=1) if x.ndim == 2 else np.abs(x)
    idx = np.where(a > thr * a.max())[0]
    return x[: idx[-1] + 1] if len(idx) else x


def finish(x, peak_db=-1.0, target_rms_db=-16.0):
    """تنظيف وتوحيد مستوى الصوت: كل المؤثرات بعلو متقارب وبدون تشويه."""
    if x.ndim == 1:
        x = stereo(x)
    x = trim_silence(x, 1e-3)
    x = x - x.mean(axis=0)
    x = fade(x, 0.002, 0.02)
    p = np.abs(x).max() + 1e-12
    a = np.abs(x).max(axis=1)
    active = x[a > p * 0.01]
    rms = np.sqrt((active ** 2).mean()) + 1e-12
    g = min(10 ** (peak_db / 20) / p, 10 ** (target_rms_db / 20) / rms)
    return x * g


def tone(f, d, tau=0.3, partials=((1, 1.0),), attack=0.002):
    t = T(d)
    y = sum(a * np.sin(2 * np.pi * f * r * t) * np.exp(-t / (tau / (1 + 0.6 * (r - 1)))) for r, a in partials)
    a = int(attack * SR)
    y[:a] *= np.linspace(0, 1, a)
    return y


BELL = ((1, 1.0), (2.0, 0.5), (2.76, 0.35), (4.07, 0.2), (5.4, 0.12))


def bell(f, d=1.2, tau=0.45):
    return tone(f, d, tau, BELL)


def pluck(f, d=1.0, damping=0.996, seed=0):
    """Karplus-Strong وتر منقور."""
    n = int(d * SR)
    p = max(2, int(SR / f))
    buf = np.random.default_rng(seed).uniform(-1, 1, p).tolist()
    out = [0.0] * n
    for i in range(n):
        v = buf[i % p]
        out[i] = v
        buf[i % p] = damping * 0.5 * (v + buf[(i + 1) % p])
    return np.array(out)


def add(*xs):
    """جمع أصوات أحادية بأطوال مختلفة."""
    n = max(len(x) for x in xs)
    out = np.zeros(n)
    for x in xs:
        out[: len(x)] += x
    return out


def click(d=0.004, f=3000, seed=None):
    r = np.random.default_rng(seed)
    x = r.standard_normal(int(d * SR)) * decay(d, d / 4)
    return bfilt(x, "band", (f * 0.5, min(f * 2, 20000)), 2)


# =================== Whooshes / انتقالات ===================

def whoosh(d=0.8, f0=400, f1=3500, peak=0.55, q=1.2, pan=(-0.7, 0.7), seed=1, verb=0.15, sub=False):
    n = int(d * SR)
    r = np.random.default_rng(seed)
    env = bell_env(n, peak, 1.6)
    fc = f0 + (f1 - f0) * env
    x = svf(pink(d, r) * 3, fc, q, "band") + 0.25 * svf(white(d, r), fc * 2, 0.8, "band")
    x = x * env
    if sub:
        x = x + 0.6 * sine_sweep(lin(50, 110, n) * (0.5 + env)) * env ** 1.5
    st = stereo(x, np.linspace(pan[0], pan[1], n))
    return reverb(st, 0.8, verb) if verb else st


def s_whoosh_short():
    return whoosh(0.55, 500, 4000, 0.55)


def s_whoosh_long():
    return whoosh(1.5, 250, 3000, 0.6, q=1.0, seed=2, verb=0.2)


def s_whoosh_deep():
    return whoosh(1.1, 120, 1200, 0.55, q=1.4, seed=3, sub=True)


def s_swoosh_fast():
    return whoosh(0.3, 1200, 7000, 0.5, q=0.9, seed=4, pan=(-0.3, 0.3), verb=0.08)


def s_swish_air():
    return whoosh(0.45, 2500, 9000, 0.45, q=0.7, seed=5, verb=0.1)


def s_whip():
    w = whoosh(0.22, 1500, 8000, 0.75, q=0.8, seed=6, pan=(-0.9, 0.9), verb=0)
    crack = click(0.012, 4000, 9) * 0.8
    return reverb(mix(w, at(stereo(crack, 0.6), 0.16)), 0.6, 0.12)


def s_whoosh_reverse():
    return whoosh(0.9, 300, 4000, 0.9, q=1.1, seed=8, sub=True, verb=0.05)


def s_whoosh_double():
    a = whoosh(0.45, 600, 4000, 0.5, seed=10, verb=0)
    b = whoosh(0.45, 600, 4500, 0.5, seed=11, pan=(0.7, -0.7), verb=0)
    return reverb(mix(a, at(b, 0.28)), 0.8, 0.15)


def s_zoom_in():
    d = 0.6
    n = int(d * SR)
    env = np.linspace(0, 1, n) ** 2
    s = sine_sweep(expo(150, 1400, n)) * env * 0.5
    w = svf(pink(d) * 2, expo(300, 6000, n), 1.2) * env
    return reverb(stereo(s + w), 0.5, 0.1)


def s_zoom_out():
    return s_zoom_in()[::-1].copy()


# =================== Impacts / ضربات ===================

def s_impact_boom():
    d = 3.2
    n = int(d * SR)
    sub = sine_sweep(expo(70, 32, n)) * decay(d, 0.55)
    body = bfilt(white(d), "low", 400, 4) * decay(d, 0.08) * 1.5
    hit = click(0.01, 2500, 1) * 1.2
    x = np.tanh(1.6 * mix(stereo(sub), stereo(body)) )
    return reverb(mix(x, stereo(hit)), 2.0, 0.25)


def s_cinematic_hit():
    d = 3.0
    boom = s_impact_boom()
    t = T(d)
    metal = sum(np.sin(2 * np.pi * f * t) * np.exp(-t / tau) * a for f, tau, a in
                ((181, 1.2, 0.5), (237, 0.9, 0.4), (411, 0.7, 0.3), (523, 0.6, 0.25), (789, 0.4, 0.2), (1123, 0.3, 0.12)))
    metal = metal * np.minimum(1, (d - t) / 0.8)
    return reverb(mix(boom, stereo(metal * 0.5)), 2.5, 0.35)


def s_bass_drop():
    d = 1.8
    n = int(d * SR)
    f = expo(140, 28, n)
    x = np.tanh(2.5 * sine_sweep(f)) * np.minimum(1, np.linspace(0, 30, n)) * decay(d, 0.9)
    return stereo(x)


def s_sub_drop():
    d = 2.0
    n = int(d * SR)
    return stereo(sine_sweep(expo(90, 25, n)) * decay(d, 0.8) * np.minimum(1, np.linspace(0, 40, n)))


def s_thud():
    d = 0.5
    n = int(d * SR)
    x = sine_sweep(expo(110, 45, n)) * decay(d, 0.09) + bfilt(white(d), "low", 300, 2) * decay(d, 0.03)
    return reverb(stereo(x), 0.5, 0.1)


def s_punch():
    d = 0.4
    n = int(d * SR)
    low = sine_sweep(expo(160, 60, n)) * decay(d, 0.06)
    snap = bfilt(white(d), "band", (800, 3500), 2) * decay(d, 0.015) * 1.6
    return reverb(stereo(np.tanh(2 * (low + snap))), 0.4, 0.1)


def s_braam():
    d = 3.2
    n = int(d * SR)
    t = T(d)
    env = np.minimum(1, t / 0.08) * np.exp(-np.maximum(0, t - 0.4) / 1.2) * np.minimum(1, (d - t) / 0.8)
    notes = [55.0, 82.41, 110.0, 54.6, 110.6]
    x = sum(saw_sweep(np.full(n, f)) for f in notes)
    cut = 150 + 1600 * np.exp(-t / 0.7) * np.minimum(1, t / 0.15)
    x = svf(x, cut, 1.5, "low")
    x = np.tanh(1.5 * x / np.abs(x).max()) * env
    return reverb(stereo(x), 3.0, 0.35, damp=2500)


def s_slam():
    d = 1.0
    x = mix(s_punch(), stereo(bfilt(white(d), "high", 2000, 2) * decay(d, 0.12) * 0.5))
    return reverb(x, 1.2, 0.25)


# =================== Risers / تصاعد ===================

def riser(d=3.0, seed=12):
    n = int(d * SR)
    t = T(d)
    p = (t / d)
    env = p ** 2.2
    nz = svf(pink(d, np.random.default_rng(seed)) * 2, 300 * (20 ** p), 2.0) * env
    trem = 0.6 + 0.4 * np.sin(2 * np.pi * np.cumsum(2 + 18 * p ** 2) / SR)
    tonal = (saw_sweep(expo(110, 880, n)) * 0.3 + saw_sweep(expo(110 * 1.005, 880 * 1.005, n)) * 0.3)
    tonal = svf(tonal, 400 + 5000 * p, 1.0, "low") * env * trem
    st = stereo(nz + tonal * 0.8, np.sin(2 * np.pi * 0.5 * t) * 0.4 * p)
    return reverb(st, 1.5, 0.2)


def s_riser_tension():
    return riser(3.0)


def s_riser_short():
    return riser(1.5, 13)


def s_downlifter():
    d = 2.5
    n = int(d * SR)
    t = T(d)
    p = t / d
    env = (1 - p) ** 2
    nz = svf(pink(d) * 2, 6000 * (0.02 ** p), 1.5) * env
    s = sine_sweep(expo(400, 40, n)) * env * 0.6
    return reverb(stereo(nz + s), 1.5, 0.2)


def cymbal(d=2.0, seed=20):
    r = np.random.default_rng(seed)
    t = T(d)
    nz = bfilt(r.standard_normal(len(t)), "high", 5000, 2)
    ring = sum(np.sign(np.sin(2 * np.pi * f * t)) for f in (523, 811, 1129, 1597, 2207)) * 0.08
    ring = bfilt(ring, "high", 3000, 2)
    return (nz + ring) * np.exp(-t / 0.6)


def s_reverse_cymbal():
    c = cymbal(2.2)[::-1].copy()
    return reverb(stereo(c), 1.0, 0.15)


def s_crash():
    return reverb(stereo(cymbal(2.5, 21)), 1.5, 0.2)


# =================== UI / واجهات وتنبيهات ===================

def s_pop():
    d = 0.12
    n = int(d * SR)
    return reverb(stereo(sine_sweep(expo(900, 250, n)) * decay(d, 0.03)), 0.3, 0.08)


def s_bubble_pop():
    d = 0.15
    n = int(d * SR)
    return reverb(stereo(sine_sweep(expo(280, 1300, n)) * bell_env(n, 0.15, 1.0)), 0.3, 0.08)


def s_click():
    return stereo(add(click(0.006, 3000, 2), tone(2200, 0.03, 0.004) * 0.4))


def s_mouse_click():
    a = add(click(0.005, 2800, 3), tone(1800, 0.02, 0.003) * 0.3)
    b = click(0.004, 3500, 4) * 0.6
    return stereo(np.concatenate([a, np.zeros(int(0.07 * SR)), b]))


def s_tick():
    return stereo(add(tone(1500, 0.05, 0.006), click(0.003, 5000, 5) * 0.4))


def s_notification():
    return reverb(mix(stereo(bell(1320, 1.2, 0.35)), at(stereo(bell(1760, 1.2, 0.4) * 0.8), 0.12)), 0.8, 0.15)


def s_success():
    notes = [1046.5, 1318.5, 1568.0, 2093.0]
    parts = [at(stereo(bell(f, 1.2, 0.4) * (0.9 - i * 0.1), (i - 1.5) * 0.3), i * 0.08) for i, f in enumerate(notes)]
    return reverb(mix(*parts), 1.2, 0.2)


def s_error():
    d = 0.18
    n = int(d * SR)
    b = (square_sweep(np.full(n, 150)) + square_sweep(np.full(n, 157))) * 0.5
    b = bfilt(b, "low", 2500, 2) * np.minimum(1, np.linspace(0, 60, n))
    return stereo(np.concatenate([b, np.zeros(int(0.06 * SR)), b]))


def s_message():
    a = sine_sweep(expo(700, 1100, int(0.07 * SR))) * decay(0.07, 0.03)
    b = sine_sweep(expo(900, 1500, int(0.09 * SR))) * decay(0.09, 0.04)
    return reverb(stereo(np.concatenate([a, np.zeros(int(0.04 * SR)), b])), 0.4, 0.1)


def s_swipe():
    return whoosh(0.18, 2000, 8000, 0.4, 0.8, seed=30, pan=(0.5, -0.5), verb=0.05)


def s_toggle():
    return stereo(np.concatenate([add(click(0.004, 2500, 6), tone(900, 0.03, 0.005) * 0.4),
                                  np.zeros(int(0.03 * SR)), click(0.004, 4000, 7) * 0.7]))


def s_coin():
    d = 0.5
    t = T(d)
    x = np.where(t < 0.07, np.sign(np.sin(2 * np.pi * 988 * t)), np.sign(np.sin(2 * np.pi * 1319 * t)))
    x = bfilt(x, "low", 6000, 2) * np.exp(-np.maximum(0, t - 0.07) / 0.15) * 0.5
    return stereo(x)


def s_level_up():
    notes = [523, 659, 784, 1047, 1319]
    seg = []
    for f in notes:
        d = 0.07
        seg.append(np.sign(np.sin(2 * np.pi * f * T(d))) * 0.4)
    x = np.concatenate(seg + [np.sign(np.sin(2 * np.pi * 1568 * T(0.3))) * 0.4 * decay(0.3, 0.12)])
    return reverb(stereo(bfilt(x, "low", 7000, 2)), 0.6, 0.12)


# =================== Glitch / رقمي ===================

def glitch(d=0.8, seed=40):
    r = np.random.default_rng(seed)
    out = []
    total = 0
    n = int(d * SR)
    while total < n:
        L = int(r.uniform(0.015, 0.07) * SR)
        kind = r.integers(0, 5)
        tt = np.arange(L) / SR
        if kind == 0:
            seg = np.sign(np.sin(2 * np.pi * r.uniform(80, 2000) * tt))
        elif kind == 1:
            seg = r.standard_normal(L) * 0.7
        elif kind == 2:
            base = np.sin(2 * np.pi * r.uniform(200, 1200) * tt)
            seg = np.round(base * 3) / 3
        elif kind == 3:
            seg = np.zeros(L)
        else:
            q = max(1, int(r.uniform(10, 80)))
            src = r.standard_normal(L)
            seg = np.repeat(src[::q], q)[:L]
        if r.random() < 0.3 and out:
            seg = np.tile(out[-1][: L // 3 or 1], 4)[:L]
        out.append(seg * r.uniform(0.4, 1.0))
        total += L
    x = np.concatenate(out)[:n]
    pan = np.repeat(r.uniform(-0.8, 0.8, n // 2000 + 1), 2000)[:n]
    return stereo(x * 0.6, pan)


def s_glitch_1():
    return glitch(0.7, 41)


def s_glitch_2():
    return glitch(1.2, 42)


def s_glitch_short():
    return glitch(0.25, 43)


def s_static():
    d = 0.6
    r = np.random.default_rng(44)
    x = bfilt(r.standard_normal(int(d * SR)), "band", (800, 9000), 2)
    crackle = (r.random(int(d * SR)) > 0.997) * r.standard_normal(int(d * SR)) * 4
    env = bell_env(int(d * SR), 0.1, 0.5)
    return stereo((x * 0.5 + crackle) * env)


def s_data_beeps():
    r = np.random.default_rng(45)
    seg = []
    for _ in range(16):
        L = r.uniform(0.02, 0.05)
        seg.append(np.sin(2 * np.pi * r.choice([1800, 2400, 3000, 3600]) * T(L)) * 0.5)
        seg.append(np.zeros(int(r.uniform(0.005, 0.03) * SR)))
    return stereo(np.concatenate(seg))


def s_bleep():
    return stereo(np.sin(2 * np.pi * 1000 * T(0.6)) * 0.7)


def s_countdown():
    parts = []
    for i in range(3):
        parts.append(at(stereo(np.sin(2 * np.pi * 880 * T(0.15)) * 0.6), i))
    parts.append(at(stereo(np.sin(2 * np.pi * 1760 * T(0.6)) * 0.6 * decay(0.6, 0.4)), 3))
    return mix(*parts)


def s_laser():
    d = 0.3
    n = int(d * SR)
    f = expo(3000, 200, n)
    mod = np.sin(2 * np.pi * np.cumsum(f * 0.5) / SR) * f * 0.8
    return reverb(stereo(sine_sweep(f + mod) * decay(d, 0.12)), 0.5, 0.15)


def s_power_down():
    d = 1.4
    n = int(d * SR)
    t = T(d)
    x = saw_sweep(expo(420, 30, n)) + saw_sweep(expo(424, 30.5, n))
    x = svf(x, expo(5000, 150, n), 1.2, "low") * (1 - t / d) ** 0.8
    return stereo(x * 0.6)


def s_power_up():
    d = 1.2
    n = int(d * SR)
    t = T(d)
    x = saw_sweep(expo(60, 650, n)) + saw_sweep(expo(61, 655, n))
    x = svf(x, expo(200, 7000, n), 1.2, "low") * (t / d) ** 0.7
    return reverb(stereo(x * 0.6), 0.8, 0.15)


def s_camera_flash():
    d = 0.9
    n = int(d * SR)
    t = T(d)
    whine = np.sin(2 * np.pi * np.cumsum(expo(2000, 9000, n)) / SR) * (t / d) ** 2 * 0.2
    pop = at(stereo(bfilt(white(0.08), "band", (500, 6000), 2) * decay(0.08, 0.02) * 1.2), d)
    return reverb(mix(stereo(whine), pop), 0.6, 0.15)


# =================== Cartoon / كرتون ومرح ===================

def s_boing():
    d = 0.9
    n = int(d * SR)
    t = T(d)
    f = 120 + 220 * (1 - np.exp(-t / 0.05)) + 60 * np.sin(2 * np.pi * 14 * t) * np.exp(-t / 0.4)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.3 * np.sin(4 * np.pi * np.cumsum(f) / SR)
    return stereo(x * decay(d, 0.3) * 0.6)


def slide_whistle(up=True):
    d = 0.8
    n = int(d * SR)
    t = T(d)
    f = expo(500, 1900, n) if up else expo(1900, 500, n)
    f = f * (1 + 0.01 * np.sin(2 * np.pi * 6 * t))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.08 * bfilt(white(d), "band", (1000, 4000), 2)
    return reverb(stereo(x * bell_env(n, 0.3, 0.7) * 0.6), 0.5, 0.12)


def s_slide_up():
    return slide_whistle(True)


def s_slide_down():
    return slide_whistle(False)


def s_cartoon_pop():
    d = 0.25
    n = int(d * SR)
    x = bfilt(white(d), "band", (300, 2500), 2) * decay(d, 0.01) * 1.5 + sine_sweep(expo(500, 180, n)) * decay(d, 0.05)
    return reverb(stereo(x), 0.3, 0.1)


def s_spring():
    d = 0.7
    t = T(d)
    f = 300 + 150 * np.sin(2 * np.pi * 28 * t)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * decay(d, 0.22)
    x = x + 0.4 * np.sin(2 * np.pi * np.cumsum(f * 2.7) / SR) * decay(d, 0.12)
    return stereo(x * 0.6)


def s_sad_trombone():
    seq = [(392, 0.35), (370, 0.35), (349, 0.35), (330, 1.3)]
    out = []
    for i, (f, d) in enumerate(seq):
        n = int(d * SR)
        t = T(d)
        vib = 1 + (0.02 * np.sin(2 * np.pi * 5.5 * t) * np.minimum(1, t / 0.3) if i == 3 else 0)
        x = saw_sweep(f * vib * np.ones(n))
        wah = 400 + 1500 * bell_env(n, 0.25, 1.0)
        x = svf(x, wah, 2.5, "low") * np.minimum(1, t / 0.03) * np.minimum(1, (d - t) / 0.05)
        out.append(x)
    return reverb(stereo(np.concatenate(out) * 0.6), 1.0, 0.18)


def s_drum_roll():
    d = 2.2
    r = np.random.default_rng(50)
    n = int(d * SR)
    x = np.zeros(n)
    t = 0.0
    while t < d - 0.05:
        rate = 10 + 18 * (t / d)
        hit = bfilt(r.standard_normal(int(0.05 * SR)), "band", (900, 6000), 2) * decay(0.05, 0.015)
        hit = hit * (0.3 + 0.7 * t / d) * r.uniform(0.7, 1.0)
        i = int(t * SR)
        x[i:i + len(hit)] += hit[: n - i]
        t += 1 / rate
    roll = stereo(x)
    end = at(mix(s_crash(), s_thud()), d)
    return reverb(mix(roll, end), 1.0, 0.15)


def s_ta_da():
    chord = [523.25, 659.25, 783.99, 1046.5]
    def brass(fs, d):
        n = int(d * SR)
        t = T(d)
        x = sum(saw_sweep(np.full(n, f)) + saw_sweep(np.full(n, f * 1.004)) for f in fs)
        x = svf(x, 800 + 3000 * np.minimum(1, t / 0.05), 1.0, "low")
        return x * np.minimum(1, t / 0.01) * np.exp(-t / (d * 0.8))
    a = brass(chord[:3], 0.18)
    b = brass(chord, 1.2)
    return reverb(stereo(np.concatenate([a, np.zeros(int(0.06 * SR)), b]) * 0.3), 1.2, 0.2)


# =================== Foley / أصوات واقعية ===================

def s_camera_shutter():
    a = click(0.006, 2500, 60) * 1.0
    mech = bfilt(white(0.05), "band", (1500, 7000), 2) * bell_env(int(0.05 * SR), 0.3, 1.0) * 0.4
    b = click(0.008, 1800, 61) * 0.9
    return reverb(stereo(np.concatenate([a, mech, np.zeros(int(0.03 * SR)), b])), 0.3, 0.1)


def keypress(seed):
    r = np.random.default_rng(seed)
    d = 0.06
    k = bfilt(r.standard_normal(int(d * SR)), "band", (r.uniform(1500, 2500), 7000), 2) * decay(d, 0.006)
    th = np.sin(2 * np.pi * r.uniform(180, 260) * T(d)) * decay(d, 0.012) * 0.5
    return (k + th) * r.uniform(0.6, 1.0)


def s_typing():
    r = np.random.default_rng(70)
    d = 2.4
    x = np.zeros(int(d * SR))
    t = 0.05
    i = 0
    while t < d - 0.1:
        kp = keypress(100 + i)
        s = int(t * SR)
        x[s:s + len(kp)] += kp
        t += r.choice([0.08, 0.1, 0.12, 0.15, 0.3], p=[0.3, 0.3, 0.2, 0.15, 0.05])
        i += 1
    return reverb(stereo(x), 0.3, 0.08)


def s_typewriter_ding():
    return reverb(stereo(bell(2100, 1.5, 0.6)), 0.8, 0.15)


def s_heartbeat():
    def beat(f=55, a=1.0):
        d = 0.18
        n = int(d * SR)
        return sine_sweep(expo(f * 1.5, f, n)) * decay(d, 0.05) * a
    one = np.concatenate([beat(60), np.zeros(int(0.12 * SR)), beat(50, 0.7), np.zeros(int(0.55 * SR))])
    return stereo(np.tanh(2 * np.tile(one, 2)))


def s_clock_tick():
    tk = add(tone(2600, 0.04, 0.005), click(0.003, 6000, 80) * 0.5)
    tc = add(tone(1900, 0.04, 0.005), click(0.003, 4500, 81) * 0.5)
    gap = np.zeros(int(0.5 * SR) - len(tk))
    return reverb(stereo(np.concatenate([tk, gap, tc, gap] * 2)), 0.4, 0.1)


def s_cash_register():
    r = np.random.default_rng(90)
    rattle = np.zeros(int(0.25 * SR))
    for i in range(8):
        c = click(0.01, r.uniform(2000, 5000), 200 + i) * r.uniform(0.3, 0.7)
        s = int(r.uniform(0, 0.22) * SR)
        rattle[s:s + len(c)] += c
    ding = mix(stereo(bell(2637, 1.4, 0.5)), at(stereo(bell(3520, 1.4, 0.5) * 0.7), 0.1))
    return reverb(mix(stereo(rattle), at(ding, 0.22)), 0.8, 0.15)


def s_record_scratch():
    d = 0.6
    n = int(d * SR)
    t = T(d)
    speed = np.sin(2 * np.pi * 3.3 * t) * (1 - t / d)
    src = bfilt(np.random.default_rng(91).standard_normal(n * 3), "band", (200, 4000), 2)
    pos = np.clip(np.cumsum(np.abs(speed) * 2.5) , 0, n * 3 - 2).astype(int)
    x = src[pos] * np.abs(speed)
    x = svf(x, 500 + 3000 * np.abs(speed), 2.0, "band")
    return stereo(x * 2)


def s_tape_stop():
    d = 1.3
    n = int(d * SR)
    t = T(d)
    rate = (1 - t / d) ** 1.5
    f = np.array([220, 277.2, 329.6])
    x = sum(saw_sweep(fr * rate) for fr in f)
    x = svf(x, 300 + 3000 * rate, 1.0, "low") * np.minimum(1, rate * 4)
    return stereo(x * 0.4)


def s_rewind():
    d = 1.2
    n = int(d * SR)
    t = T(d)
    r = np.random.default_rng(92)
    chirps = np.sin(2 * np.pi * np.cumsum(2500 + 1500 * np.sin(2 * np.pi * 23 * t)) / SR)
    chirps *= (r.random(n) > 0.0) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 17 * t)))
    hiss = bfilt(r.standard_normal(n), "band", (2000, 9000), 2) * 0.3
    return stereo((chirps * 0.4 + hiss) * bell_env(n, 0.1, 0.4))


def s_vinyl_crackle():
    d = 6.0
    r = np.random.default_rng(93)
    n = int(d * SR)
    hiss = bfilt(r.standard_normal(n), "band", (300, 5000), 2) * 0.05
    pops = np.zeros(n)
    idx = r.choice(n - 400, 140, replace=False)
    for i in idx:
        c = click(0.002, r.uniform(1500, 6000), int(i)) * r.uniform(0.2, 1.0)
        pops[i:i + len(c)] += c
    return stereo(hiss + pops * 0.6)


def s_footsteps():
    r = np.random.default_rng(94)
    x = np.zeros(int(2.2 * SR))
    for i in range(4):
        d = 0.12
        st = bfilt(r.standard_normal(int(d * SR)), "low", 900, 2) * decay(d, 0.025)
        st = st + np.sin(2 * np.pi * 85 * T(d)) * decay(d, 0.03) * 0.6
        s = int((0.1 + i * 0.5) * SR)
        x[s:s + len(st)] += st
    return reverb(stereo(x), 0.5, 0.12)


def s_door_knock():
    r = np.random.default_rng(95)
    x = np.zeros(int(1.0 * SR))
    for i, t0 in enumerate((0.05, 0.25, 0.45)):
        d = 0.15
        k = sum(np.sin(2 * np.pi * f * T(d)) * decay(d, tau) for f, tau in ((180, 0.04), (420, 0.02), (900, 0.01)))
        k = k + bfilt(r.standard_normal(int(d * SR)), "band", (400, 2500), 2) * decay(d, 0.008)
        s = int(t0 * SR)
        x[s:s + len(k)] += k
    return reverb(stereo(x), 0.6, 0.15)


# =================== Stingers / موسيقية ===================

def s_magic_shimmer():
    d = 2.0
    r = np.random.default_rng(100)
    n = int(d * SR)
    x = np.zeros((n, 2))
    for i in range(70):
        t0 = (i / 70) * 1.2 + r.uniform(0, 0.08)
        f = 2000 + 6000 * (i / 70) + r.uniform(-300, 300)
        dd = 0.4
        s = np.sin(2 * np.pi * f * T(dd)) * decay(dd, 0.12) * r.uniform(0.3, 1.0)
        st = stereo(s, r.uniform(-0.9, 0.9))
        j = int(t0 * SR)
        x[j:j + len(st)] += st[: n - j]
    return reverb(x * 0.3, 2.0, 0.45, damp=9000)


def s_harp_gliss():
    scale = [261.6, 293.7, 329.6, 392.0, 440.0, 523.3, 587.3, 659.3, 784.0, 880.0, 1046.5, 1174.7, 1318.5]
    parts = [at(stereo(pluck(f, 1.6, 0.997, i) * 0.4, -0.8 + 1.6 * i / len(scale)), i * 0.045)
             for i, f in enumerate(scale)]
    return reverb(mix(*parts), 1.5, 0.3)


def s_dramatic_sting():
    def hit(fs, d):
        n = int(d * SR)
        t = T(d)
        x = sum(saw_sweep(np.full(n, f)) + saw_sweep(np.full(n, f * 1.006)) for f in fs)
        x = svf(x, 300 + 1800 * np.exp(-t / 0.25), 1.2, "low")
        return np.tanh(x / 3) * np.minimum(1, t / 0.01) * np.exp(-t / (d * 0.6))
    a = hit([73.4, 110, 146.8], 0.35)
    b = hit([69.3, 103.8, 138.6], 0.35)
    c = hit([65.4, 98, 130.8, 155.6], 2.2)
    g = np.zeros(int(0.15 * SR))
    x = np.concatenate([a, g, b, g, c])
    return reverb(mix(stereo(x * 0.6), at(s_sub_drop() * 0.5, 1.0)), 2.5, 0.3)


def s_suspense_drone():
    d = 6.0
    n = int(d * SR)
    t = T(d)
    x = sum(saw_sweep(np.full(n, f)) for f in (55, 55.3, 82.4, 82.0, 58.3))
    x = svf(x, 200 + 300 * (0.5 + 0.5 * np.sin(2 * np.pi * 0.15 * t)), 1.5, "low")
    nz = svf(pink(d) * 2, 1200 + 600 * np.sin(2 * np.pi * 0.2 * t), 3.0) * 0.3
    env = np.minimum(1, t / 1.5) * np.minimum(1, (d - t) / 1.0)
    return reverb(stereo((x / 5 + nz) * env, 0.3 * np.sin(2 * np.pi * 0.1 * t)), 3.0, 0.35)


def s_correct():
    a = bell(1318.5, 0.8, 0.25)
    b = bell(1760, 1.2, 0.4)
    return reverb(mix(stereo(a), at(stereo(b), 0.12)), 0.8, 0.15)


def s_wrong_buzzer():
    d = 0.8
    n = int(d * SR)
    x = (saw_sweep(np.full(n, 110)) + square_sweep(np.full(n, 116))) * 0.5
    x = bfilt(x, "low", 3000, 2) * np.minimum(1, np.linspace(0, 80, n)) * np.minimum(1, np.linspace(8, 0, n))
    return stereo(x)


def s_suspense_hit():
    d = 2.5
    t = T(d)
    tones = sum(np.sin(2 * np.pi * f * t) * np.exp(-t / 0.9) for f in (311, 330, 466))
    x = mix(stereo(tones * 0.3), s_thud())
    return reverb(x, 2.5, 0.4)


def s_meme_bruh():
    # نغمة هبوط مضحكة قصيرة
    d = 0.5
    n = int(d * SR)
    x = saw_sweep(expo(180, 90, n))
    x = svf(x, expo(1500, 400, n), 3.0, "low") * bell_env(n, 0.1, 0.6)
    return stereo(x * 0.8)


def s_vine_boom():
    d = 1.6
    n = int(d * SR)
    x = sine_sweep(expo(95, 40, n)) * decay(d, 0.4)
    x = x + bfilt(white(d), "low", 250, 4) * decay(d, 0.05)
    return reverb(stereo(np.tanh(3 * x)), 1.5, 0.3)


# =================== Ambience / أجواء ===================

def s_wind():
    d = 8.0
    t = T(d)
    r = np.random.default_rng(110)
    mod = 500 + 400 * np.sin(2 * np.pi * 0.13 * t) + 200 * np.sin(2 * np.pi * 0.37 * t + 1)
    x = svf(brown(d, r) * 3 + pink(d, r), mod, 2.0)
    amp = 0.6 + 0.4 * np.sin(2 * np.pi * 0.11 * t)
    st = stereo(x * amp, 0.4 * np.sin(2 * np.pi * 0.07 * t))
    return fade(st, 0.8, 0.8)


def s_rain():
    d = 8.0
    r = np.random.default_rng(111)
    n = int(d * SR)
    base = bfilt(pink(d, r), "band", (400, 8000), 2)
    drops = np.zeros((n, 2))
    for i in range(1200):
        c = click(0.003, r.uniform(2000, 8000), 1000 + i) * r.uniform(0.05, 0.4)
        s = r.integers(0, n - 200)
        p = r.uniform(-1, 1)
        drops[s:s + len(c)] += stereo(c, p)
    return fade(mix(stereo(base * 0.5), drops), 0.8, 0.8)


def s_crowd_cheer():
    d = 3.0
    r = np.random.default_rng(112)
    n = int(d * SR)
    t = T(d)
    voices = np.zeros(n)
    for i in range(40):
        f0 = r.uniform(150, 400)
        f = f0 * (1 + 0.15 * np.sin(2 * np.pi * r.uniform(2, 6) * t + r.uniform(0, 6)))
        v = saw_sweep(f)
        v = svf(v, r.uniform(700, 2500), 4.0)
        voices += v * r.uniform(0.3, 1.0)
    clap = np.zeros(n)
    for i in range(500):
        c = bfilt(r.standard_normal(int(0.01 * SR)), "band", (1000, 5000), 2) * decay(0.01, 0.002)
        s = r.integers(0, n - 500)
        clap[s:s + len(c)] += c * r.uniform(0.2, 1.0)
    env = np.minimum(1, t / 0.3) * np.minimum(1, (d - t) / 1.2)
    return reverb(stereo((voices / 20 + clap * 0.5) * env), 1.5, 0.3)


# =================== السجل ===================

SFX = {
    # name: (fn, التصنيف, الوصف)
    "whoosh-short": (s_whoosh_short, "انتقالات", "ووش قصير"),
    "whoosh-long": (s_whoosh_long, "انتقالات", "ووش طويل"),
    "whoosh-deep": (s_whoosh_deep, "انتقالات", "ووش عميق بباص"),
    "whoosh-double": (s_whoosh_double, "انتقالات", "ووش مزدوج"),
    "whoosh-reverse": (s_whoosh_reverse, "انتقالات", "ووش يتصاعد وينقطع"),
    "swoosh-fast": (s_swoosh_fast, "انتقالات", "سووش سريع"),
    "swish-air": (s_swish_air, "انتقالات", "هواء خفيف"),
    "whip": (s_whip, "انتقالات", "ضربة سوط سريعة"),
    "zoom-in": (s_zoom_in, "انتقالات", "صوت زوم داخل"),
    "zoom-out": (s_zoom_out, "انتقالات", "صوت زوم خارج"),
    "swipe": (s_swipe, "انتقالات", "سحب سريع"),
    "impact-boom": (s_impact_boom, "ضربات", "بوم سينمائي"),
    "cinematic-hit": (s_cinematic_hit, "ضربات", "ضربة سينمائية معدنية"),
    "bass-drop": (s_bass_drop, "ضربات", "باص دروب"),
    "sub-drop": (s_sub_drop, "ضربات", "هبوط باص عميق"),
    "thud": (s_thud, "ضربات", "ضربة مكتومة"),
    "punch": (s_punch, "ضربات", "لكمة"),
    "slam": (s_slam, "ضربات", "ضربة قوية"),
    "braam": (s_braam, "ضربات", "برااام سينمائي (ترايلر)"),
    "vine-boom": (s_vine_boom, "ضربات", "بوم الميمز"),
    "riser-tension": (s_riser_tension, "تصاعد", "تصاعد توتر 3 ثواني"),
    "riser-short": (s_riser_short, "تصاعد", "تصاعد قصير"),
    "downlifter": (s_downlifter, "تصاعد", "هبوط تدريجي"),
    "reverse-cymbal": (s_reverse_cymbal, "تصاعد", "صنج معكوس"),
    "crash": (s_crash, "تصاعد", "صنج كراش"),
    "drum-roll": (s_drum_roll, "تصاعد", "قرع طبول مع ضربة"),
    "pop": (s_pop, "واجهات", "بوب"),
    "bubble-pop": (s_bubble_pop, "واجهات", "فقاعة"),
    "click": (s_click, "واجهات", "نقرة"),
    "mouse-click": (s_mouse_click, "واجهات", "كبسة ماوس"),
    "tick": (s_tick, "واجهات", "تك"),
    "toggle": (s_toggle, "واجهات", "مفتاح تشغيل"),
    "notification": (s_notification, "واجهات", "تنبيه"),
    "message": (s_message, "واجهات", "رسالة واصلة"),
    "success": (s_success, "واجهات", "نجاح"),
    "error": (s_error, "واجهات", "خطأ"),
    "coin": (s_coin, "واجهات", "عملة (ألعاب)"),
    "level-up": (s_level_up, "واجهات", "ليفل أب (ألعاب)"),
    "correct": (s_correct, "واجهات", "إجابة صحيحة"),
    "wrong-buzzer": (s_wrong_buzzer, "واجهات", "إجابة خاطئة"),
    "glitch-1": (s_glitch_1, "رقمي", "غلتش"),
    "glitch-2": (s_glitch_2, "رقمي", "غلتش طويل"),
    "glitch-short": (s_glitch_short, "رقمي", "غلتش قصير"),
    "static": (s_static, "رقمي", "تشويش"),
    "data-beeps": (s_data_beeps, "رقمي", "بيانات تقنية"),
    "bleep": (s_bleep, "رقمي", "صفير حجب الكلام"),
    "countdown": (s_countdown, "رقمي", "عد تنازلي 3-2-1"),
    "laser": (s_laser, "رقمي", "ليزر"),
    "power-up": (s_power_up, "رقمي", "تشغيل"),
    "power-down": (s_power_down, "رقمي", "إطفاء"),
    "camera-flash": (s_camera_flash, "رقمي", "فلاش كاميرا"),
    "boing": (s_boing, "كرتون", "بوينغ"),
    "slide-up": (s_slide_up, "كرتون", "صفارة صاعدة"),
    "slide-down": (s_slide_down, "كرتون", "صفارة نازلة"),
    "cartoon-pop": (s_cartoon_pop, "كرتون", "فلينة"),
    "spring": (s_spring, "كرتون", "زنبرك"),
    "sad-trombone": (s_sad_trombone, "كرتون", "ترومبون حزين (فشل)"),
    "meme-bruh": (s_meme_bruh, "كرتون", "نغمة ميمز هابطة"),
    "ta-da": (s_ta_da, "كرتون", "تا-دا"),
    "camera-shutter": (s_camera_shutter, "واقعية", "غالق كاميرا"),
    "typing": (s_typing, "واقعية", "كتابة على كيبورد"),
    "typewriter-ding": (s_typewriter_ding, "واقعية", "جرس آلة كاتبة"),
    "heartbeat": (s_heartbeat, "واقعية", "نبض قلب"),
    "clock-tick": (s_clock_tick, "واقعية", "تكتكة ساعة"),
    "cash-register": (s_cash_register, "واقعية", "كاشير (كا-تشينغ)"),
    "record-scratch": (s_record_scratch, "واقعية", "خدش أسطوانة"),
    "tape-stop": (s_tape_stop, "واقعية", "توقف شريط"),
    "rewind": (s_rewind, "واقعية", "ترجيع"),
    "vinyl-crackle": (s_vinyl_crackle, "واقعية", "طقطقة أسطوانة قديمة"),
    "footsteps": (s_footsteps, "واقعية", "خطوات"),
    "door-knock": (s_door_knock, "واقعية", "طرق باب"),
    "magic-shimmer": (s_magic_shimmer, "موسيقية", "لمعة سحرية"),
    "harp-gliss": (s_harp_gliss, "موسيقية", "هارب صاعد (حلم/ذكرى)"),
    "dramatic-sting": (s_dramatic_sting, "موسيقية", "دن دن دااان"),
    "suspense-hit": (s_suspense_hit, "موسيقية", "ضربة غموض"),
    "suspense-drone": (s_suspense_drone, "موسيقية", "خلفية توتر"),
    "wind": (s_wind, "أجواء", "رياح"),
    "rain": (s_rain, "أجواء", "مطر"),
    "crowd-cheer": (s_crowd_cheer, "أجواء", "تشجيع وتصفيق"),
}


def render(name):
    return finish(SFX[name][0]())
