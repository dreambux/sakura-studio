"""Ścisły parser i koder WAV. Czysty Python + numpy: nieufne bajty nie trafiają do bibliotek natywnych."""

from __future__ import annotations

import hashlib
import math
import struct
from dataclasses import dataclass

import numpy as np

from .errors import E_AUDIO_INVALID, E_AUDIO_TOO_LONG, VoiceMachineError

MIN_SAMPLE_RATE = 8_000
MAX_SAMPLE_RATE = 96_000

_FORMAT_PCM = 1
_FORMAT_FLOAT = 3
_FORMAT_EXTENSIBLE = 0xFFFE


@dataclass(frozen=True)
class WavData:
    samples: np.ndarray  # float32, mono, zakres [-1, 1]
    sample_rate: int
    channels: int
    peak: float
    rms: float

    @property
    def frames(self) -> int:
        return int(self.samples.shape[0])

    @property
    def duration_s(self) -> float:
        return self.frames / self.sample_rate


def _invalid(detail: str) -> VoiceMachineError:
    return VoiceMachineError(E_AUDIO_INVALID, f"Nieprawidłowy plik WAV: {detail}.")


def parse_wav(data: bytes, *, max_frames: int) -> WavData:
    """Czyta WAV PCM 16/24/32-bit lub float 32/64-bit, 1-2 kanały. Miksuje do mono."""
    if len(data) < 44 or data[0:4] != b"RIFF" or data[8:12] != b"WAVE":
        raise _invalid("brak nagłówka RIFF/WAVE")

    fmt: tuple[int, int, int, int, int] | None = None  # tag, channels, rate, block_align, bits
    body: tuple[int, int] | None = None
    pos = 12
    while pos + 8 <= len(data):
        chunk_id = data[pos : pos + 4]
        size = struct.unpack_from("<I", data, pos + 4)[0]
        start = pos + 8
        if chunk_id == b"fmt ":
            if size < 16 or start + 16 > len(data):
                raise _invalid("uszkodzony blok fmt")
            tag, channels, rate, _byte_rate, block_align, bits = struct.unpack_from("<HHIIHH", data, start)
            if tag == _FORMAT_EXTENSIBLE:
                if size < 40 or start + 26 > len(data):
                    raise _invalid("uszkodzony blok fmt (extensible)")
                tag = struct.unpack_from("<H", data, start + 24)[0]
            fmt = (tag, channels, rate, block_align, bits)
        elif chunk_id == b"data":
            available = max(0, len(data) - start)
            body = (start, min(size, available))
            break
        pos = start + size + (size & 1)

    if fmt is None or body is None:
        raise _invalid("brak bloku fmt lub data")
    tag, channels, rate, block_align, bits = fmt
    if channels not in (1, 2):
        raise _invalid(f"obsługiwane są 1-2 kanały, plik ma {channels}")
    if not MIN_SAMPLE_RATE <= rate <= MAX_SAMPLE_RATE:
        raise _invalid(f"częstotliwość {rate} Hz poza zakresem {MIN_SAMPLE_RATE}-{MAX_SAMPLE_RATE}")
    supported = {(_FORMAT_PCM, 16), (_FORMAT_PCM, 24), (_FORMAT_PCM, 32), (_FORMAT_FLOAT, 32), (_FORMAT_FLOAT, 64)}
    if (tag, bits) not in supported:
        raise _invalid(f"nieobsługiwany format (tag {tag}, {bits} bit); użyj PCM 16-bit")
    frame_bytes = channels * bits // 8
    if block_align != frame_bytes:
        raise _invalid("niespójny block_align")

    start, length = body
    frames = length // frame_bytes
    if frames == 0:
        raise _invalid("brak próbek")
    if frames > max_frames:
        raise VoiceMachineError(E_AUDIO_TOO_LONG, "Nagranie jest za długie.")
    raw = data[start : start + frames * frame_bytes]

    if tag == _FORMAT_PCM and bits == 16:
        values = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
    elif tag == _FORMAT_PCM and bits == 24:
        b = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3).astype(np.int32)
        packed = b[:, 0] | (b[:, 1] << 8) | (b[:, 2] << 16)
        values = ((packed ^ 0x800000) - 0x800000).astype(np.float32) / 8388608.0
    elif tag == _FORMAT_PCM:
        values = np.frombuffer(raw, dtype="<i4").astype(np.float32) / 2147483648.0
    elif bits == 32:
        values = np.frombuffer(raw, dtype="<f4").astype(np.float32)
    else:
        values = np.frombuffer(raw, dtype="<f8").astype(np.float32)

    if not np.all(np.isfinite(values)):
        raise _invalid("próbki zawierają NaN lub nieskończoność")
    mono = values.reshape(-1, channels).mean(axis=1, dtype=np.float32) if channels == 2 else values
    mono = np.clip(mono, -1.0, 1.0).astype(np.float32, copy=False)
    peak = float(np.max(np.abs(mono)))
    rms = float(math.sqrt(float(np.mean(np.square(mono, dtype=np.float64)))))
    return WavData(samples=mono, sample_rate=rate, channels=channels, peak=peak, rms=rms)


def reference_flags(samples: np.ndarray, sample_rate: int) -> set[str]:
    """Heurystyczne ostrzeżenia o jakości nagrania wzorcowego. Progi NIEKALIBROWANE: to wskazówki, nie werdykty.

    quiet    - szczyt poniżej 0,05 pełnej skali
    clipping - szczyt przy pełnej skali
    noisy    - rozpiętość poziomów ramek (90. minus 10. percentyl) poniżej 12 dB: szum, muzyka lub kompresja
    silence  - mniej niż połowa ramek jest w zasięgu 25 dB od szczytu mowy
    """
    flags: set[str] = set()
    x = np.asarray(samples, dtype=np.float32)
    if x.size == 0:
        return flags
    peak = float(np.max(np.abs(x)))
    if peak < 0.05:
        flags.add("quiet")
    if peak >= 0.999:
        flags.add("clipping")
    frame = int(sample_rate * 0.025)
    if frame > 0 and x.size >= frame * 40:
        frames = x[: x.size // frame * frame].reshape(-1, frame).astype(np.float64)
        db = 20.0 * np.log10(np.maximum(np.sqrt(np.mean(np.square(frames), axis=1)), 1e-7))
        top = float(np.percentile(db, 90))
        floor = float(np.percentile(db, 10))
        if top - floor < 12.0:
            flags.add("noisy")
        if float(np.mean(db > top - 25.0)) < 0.5:
            flags.add("silence")
    return flags


def encode_wav_pcm16(samples: np.ndarray, sample_rate: int) -> bytes:
    """Koduje mono float32 [-1, 1] do WAV PCM 16-bit (skala 32768, zgodna z parse_wav)."""
    x = np.nan_to_num(np.asarray(samples, dtype=np.float32), nan=0.0, posinf=1.0, neginf=-1.0)
    pcm = np.clip(np.rint(x * 32768.0), -32768, 32767).astype("<i2").tobytes()
    header = (
        b"RIFF"
        + struct.pack("<I", 36 + len(pcm))
        + b"WAVE"
        + b"fmt "
        + struct.pack("<IHHIIHH", 16, _FORMAT_PCM, 1, sample_rate, sample_rate * 2, 2, 16)
        + b"data"
        + struct.pack("<I", len(pcm))
    )
    return header + pcm


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def slice_count(total: int, chunk_size: int) -> int:
    return max(1, -(-total // chunk_size))
