#!/usr/bin/env python3
"""Generate original .cube LUTs and short WAV effects using only Python stdlib."""

from __future__ import annotations

import math
import random
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_RATE = 48_000

LUTS = {
    "golden-hour": (1.06, 1.08, 0.015, 0.055, 0.006, 0.045, 0.012),
    "teal-pop": (1.12, 1.16, 0.0, -0.015, 0.045, 0.018, 0.0),
    "soft-candy": (0.91, 0.88, 0.025, 0.012, 0.0, 0.015, 0.035),
    "night-neon": (1.14, 1.22, -0.018, -0.035, 0.035, 0.0, 0.0),
}
SOUNDS = {
    "whoosh": (0.72, 11),
    "riser": (1.65, 23),
    "impact": (0.62, 37),
    "snap": (0.24, 41),
    "sparkle": (1.10, 59),
}


def clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def grade(rgb: tuple[float, float, float], look: tuple[float, ...]) -> tuple[float, float, float]:
    contrast, saturation, exposure, warmth, shadow_tint, highlight_tint, fade_amount = look
    r, g, b = (clamp((c - 0.5) * contrast + 0.5 + exposure) for c in rgb)
    luma = 0.2126 * r + 0.7152 * g + 0.0722 * b
    r, g, b = (luma + (c - luma) * saturation for c in (r, g, b))
    shadow = (1.0 - luma) ** 1.7
    highlight = luma**1.7
    teal = shadow_tint * shadow
    gold = highlight_tint * highlight
    fade = fade_amount * (1.0 - luma)
    return (
        clamp(r + warmth + gold - teal * 0.35 + fade),
        clamp(g + gold * 0.12 + teal * 0.18 + fade),
        clamp(b - warmth + teal + gold * 0.55 + fade),
    )


def write_luts() -> list[Path]:
    output = ROOT / "assets" / "luts"
    output.mkdir(parents=True, exist_ok=True)
    size = 17
    paths = []
    for name, look in LUTS.items():
        path = output / f"{name}.cube"
        with path.open("w", encoding="ascii", newline="\n") as file:
            file.write(f'TITLE "{name}"\nLUT_3D_SIZE {size}\nDOMAIN_MIN 0.0 0.0 0.0\nDOMAIN_MAX 1.0 1.0 1.0\n')
            for blue in range(size):
                for green in range(size):
                    for red in range(size):
                        values = grade((red / (size - 1), green / (size - 1), blue / (size - 1)), look)
                        file.write("{:.6f} {:.6f} {:.6f}\n".format(*values))
        paths.append(path)
    return paths


def sample_for(name: str, time: float, duration: float, noise: float, rng: random.Random, state: dict[str, float]) -> float:
    progress = time / duration
    if name == "whoosh":
        white = rng.uniform(-1.0, 1.0)
        high = white - state.get("noise", 0.0) * 0.82
        state["noise"] = white
        return math.sin(math.pi * progress) ** 1.6 * (
            0.72 * high + 0.18 * math.sin(2 * math.pi * (180 + 900 * progress) * time)
        )
    if name == "riser":
        frequency = 110 + 660 * progress**1.5
        return progress**1.7 * (0.58 * math.sin(2 * math.pi * frequency * time) + 0.16 * noise)
    if name == "impact":
        low = math.sin(2 * math.pi * (42 + 20 * math.exp(-time * 8)) * time) * math.exp(-time * 8.5)
        crack = noise * math.exp(-time * 55)
        ring = math.sin(2 * math.pi * 173 * time) * math.exp(-time * 11)
        return 0.82 * low + 0.36 * crack + 0.12 * ring
    if name == "snap":
        click = noise * math.exp(-time * 42)
        body = math.sin(2 * math.pi * (520 - 250 * progress) * time) * math.exp(-time * 17)
        return 0.62 * click + 0.28 * body
    envelope = math.sin(math.pi * progress) ** 0.8
    shimmer = sum(math.sin(2 * math.pi * freq * time) for freq in (880, 1108.73, 1318.51)) / 3
    return envelope * (0.36 * shimmer + 0.1 * noise)


def write_sounds() -> list[Path]:
    output = ROOT / "assets" / "audio"
    output.mkdir(parents=True, exist_ok=True)
    paths = []
    for name, (duration, seed) in SOUNDS.items():
        count = int(SAMPLE_RATE * duration)
        rng = random.Random(seed)
        state: dict[str, float] = {}
        samples = []
        peak = 0.0
        for index in range(count):
            value = sample_for(name, index / SAMPLE_RATE, duration, rng.uniform(-1.0, 1.0), rng, state)
            samples.append(value)
            peak = max(peak, abs(value))
        scale = 0.88 / peak if peak else 1.0
        path = output / f"{name}.wav"
        with wave.open(str(path), "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(SAMPLE_RATE)
            pcm = bytearray()
            for value in samples:
                sample = int(max(-1.0, min(1.0, value * scale)) * 32767)
                pcm.extend(sample.to_bytes(2, byteorder="little", signed=True))
            wav.writeframes(pcm)
        paths.append(path)
    return paths


def main() -> None:
    files = write_luts() + write_sounds()
    for path in files:
        print(path.relative_to(ROOT))
    print(f"Generated {len(files)} assets. No external packages required.")


if __name__ == "__main__":
    main()
