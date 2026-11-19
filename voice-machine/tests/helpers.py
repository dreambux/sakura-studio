"""Pomocnicze generatory WAV do testów."""

from __future__ import annotations

import struct
import time

import numpy as np


def wait_until(predicate, timeout: float = 10.0, interval: float = 0.02) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(interval)
    raise AssertionError("timeout waiting for condition")


def make_wav(
    channels_data: list[np.ndarray],
    rate: int = 24_000,
    bits: int = 16,
    float_format: bool = False,
    extensible: bool = False,
) -> bytes:
    """channels_data: lista tablic float [-1, 1], po jednej na kanał."""
    channels = len(channels_data)
    frames = np.stack(channels_data, axis=1)  # (n, channels)
    if float_format:
        dtype = "<f4" if bits == 32 else "<f8"
        body = frames.astype(dtype).tobytes()
        tag = 3
    elif bits == 16:
        body = np.clip(np.rint(frames * 32768.0), -32768, 32767).astype("<i2").tobytes()
        tag = 1
    elif bits == 24:
        ints = np.clip(np.rint(frames * 8388608.0), -8388608, 8388607).astype(np.int32).reshape(-1)
        packed = np.stack([(ints & 0xFF), (ints >> 8) & 0xFF, (ints >> 16) & 0xFF], axis=1).astype(np.uint8)
        body = packed.tobytes()
        tag = 1
    elif bits == 32:
        body = np.clip(np.rint(frames * 2147483648.0), -2147483648, 2147483647).astype("<i4").tobytes()
        tag = 1
    else:
        raise ValueError(bits)
    block_align = channels * bits // 8
    if extensible:
        guid = struct.pack("<H", tag) + b"\x00\x00\x00\x00\x10\x00\x80\x00\x00\xaa\x00\x38\x9b\x71"
        fmt_body = struct.pack("<HHIIHH", 0xFFFE, channels, rate, rate * block_align, block_align, bits)
        fmt_body += struct.pack("<HHI", 22, bits, 3) + guid
    else:
        fmt_body = struct.pack("<HHIIHH", tag, channels, rate, rate * block_align, block_align, bits)
    out = b"fmt " + struct.pack("<I", len(fmt_body)) + fmt_body + b"data" + struct.pack("<I", len(body)) + body
    if len(body) & 1:
        out += b"\x00"
    return b"RIFF" + struct.pack("<I", 4 + len(out)) + b"WAVE" + out


def sine(seconds: float, rate: int = 24_000, freq: float = 220.0, amp: float = 0.5) -> np.ndarray:
    t = np.arange(int(seconds * rate), dtype=np.float64) / rate
    return (amp * np.sin(2 * np.pi * freq * t)).astype(np.float32)


def mono_wav(seconds: float, rate: int = 24_000, freq: float = 220.0, amp: float = 0.5) -> bytes:
    return make_wav([sine(seconds, rate, freq, amp)], rate=rate)


def speechlike(seconds: float, rate: int = 24_000, amp: float = 0.4, noise: float = 0.003, seed: int = 1) -> np.ndarray:
    """Syntetyczny sygnał o dynamice podobnej do mowy: wybuchy tonu z przerwami i cichym szumem tła."""
    rng = np.random.default_rng(seed)
    n = int(seconds * rate)
    t = np.arange(n) / rate
    gate = (np.sin(2 * np.pi * 1.7 * t) > -0.6).astype(np.float64)  # ok. 70% czasu głośno
    carrier = np.sin(2 * np.pi * 180 * t) + 0.5 * np.sin(2 * np.pi * 410 * t)
    x = amp * 0.7 * gate * carrier + noise * rng.standard_normal(n)
    return np.clip(x, -1.0, 1.0).astype(np.float32)


def speechlike_wav(seconds: float, rate: int = 24_000, **kwargs) -> bytes:
    return make_wav([speechlike(seconds, rate, **kwargs)], rate=rate)
