from __future__ import annotations

import struct

import numpy as np
import pytest

from helpers import make_wav, mono_wav, sine, speechlike
from voice_machine.errors import E_AUDIO_INVALID, E_AUDIO_TOO_LONG, VoiceMachineError
from voice_machine.wavio import encode_wav_pcm16, parse_wav, reference_flags, slice_count

BIG = 10**9


def test_pcm16_roundtrip_is_exact() -> None:
    samples = sine(0.5, 22_050, 440.0, 0.8)
    wav = encode_wav_pcm16(samples, 22_050)
    parsed = parse_wav(wav, max_frames=BIG)
    assert parsed.sample_rate == 22_050
    assert parsed.channels == 1
    assert parsed.frames == samples.shape[0]
    again = encode_wav_pcm16(parsed.samples, parsed.sample_rate)
    assert again == wav


def test_header_fields_of_encoded_wav() -> None:
    wav = encode_wav_pcm16(np.zeros(100, dtype=np.float32), 16_000)
    assert wav[:4] == b"RIFF" and wav[8:12] == b"WAVE"
    assert struct.unpack_from("<I", wav, 4)[0] == len(wav) - 8
    assert struct.unpack_from("<HHIIHH", wav, 20) == (1, 1, 16_000, 32_000, 2, 16)
    assert struct.unpack_from("<I", wav, 40)[0] == 200


def test_stereo_is_mixed_down() -> None:
    left = np.full(2000, 0.5, dtype=np.float32)
    right = np.full(2000, -0.5, dtype=np.float32)
    parsed = parse_wav(make_wav([left, right]), max_frames=BIG)
    assert parsed.channels == 2
    assert float(np.max(np.abs(parsed.samples))) < 1e-4


@pytest.mark.parametrize(
    "kwargs",
    [
        {"bits": 24},
        {"bits": 32},
        {"bits": 32, "float_format": True},
        {"bits": 64, "float_format": True},
        {"bits": 16, "extensible": True},
    ],
)
def test_other_sample_formats_parse(kwargs: dict) -> None:
    samples = sine(0.25, 24_000, 330.0, 0.6)
    parsed = parse_wav(make_wav([samples], **kwargs), max_frames=BIG)
    assert parsed.frames == samples.shape[0]
    assert np.max(np.abs(parsed.samples - samples)) < 1e-3


def test_statistics() -> None:
    parsed = parse_wav(mono_wav(0.5, amp=0.5), max_frames=BIG)
    assert 0.49 < parsed.peak <= 0.5
    assert 0.34 < parsed.rms < 0.36
    assert parsed.duration_s == pytest.approx(0.5, abs=1e-3)


@pytest.mark.parametrize(
    "blob",
    [
        b"",
        b"RIFF",
        b"not a wav file at all, definitely longer than forty-four bytes of nonsense data....",
        b"RIFF\x00\x00\x00\x00WAVE" + b"\x00" * 40,
    ],
)
def test_garbage_is_rejected(blob: bytes) -> None:
    with pytest.raises(VoiceMachineError) as exc:
        parse_wav(blob, max_frames=BIG)
    assert exc.value.code == E_AUDIO_INVALID


def test_rejects_unsupported_layouts() -> None:
    three = [sine(0.1)] * 3
    with pytest.raises(VoiceMachineError):
        parse_wav(make_wav(three), max_frames=BIG)
    with pytest.raises(VoiceMachineError):
        parse_wav(mono_wav(0.2, rate=4_000), max_frames=BIG)
    with pytest.raises(VoiceMachineError):
        parse_wav(mono_wav(0.2, rate=192_000), max_frames=BIG)


def test_rejects_non_finite_float_samples() -> None:
    bad = np.array([0.0, np.nan, 0.5, np.inf] * 500, dtype=np.float32)
    with pytest.raises(VoiceMachineError) as exc:
        parse_wav(make_wav([bad], bits=32, float_format=True), max_frames=BIG)
    assert exc.value.code == E_AUDIO_INVALID


def test_too_long_by_frame_count() -> None:
    with pytest.raises(VoiceMachineError) as exc:
        parse_wav(mono_wav(1.0), max_frames=1000)
    assert exc.value.code == E_AUDIO_TOO_LONG


def test_data_size_larger_than_file_is_clamped_not_overread() -> None:
    wav = bytearray(mono_wav(0.5))
    struct.pack_into("<I", wav, 40, 0xFFFFFFFF)  # nagłówek "strumieniowy"
    parsed = parse_wav(bytes(wav), max_frames=BIG)
    assert parsed.frames == 12_000


def test_block_align_mismatch_is_rejected() -> None:
    wav = bytearray(mono_wav(0.2))
    struct.pack_into("<H", wav, 32, 4)
    with pytest.raises(VoiceMachineError):
        parse_wav(bytes(wav), max_frames=BIG)


def test_reference_flags_on_synthetic_material() -> None:
    assert reference_flags(speechlike(8.0), 24_000) == set()
    assert reference_flags(speechlike(8.0, amp=0.01, noise=1e-5), 24_000) == {"quiet"}
    assert "clipping" in reference_flags(np.clip(speechlike(8.0, amp=3.0), -1.0, 1.0), 24_000)
    hiss = (np.random.default_rng(3).standard_normal(24_000 * 8) * 0.1).astype(np.float32)
    assert "noisy" in reference_flags(hiss, 24_000)
    mostly_quiet = np.concatenate([speechlike(1.0), np.full(24_000 * 7, 1e-5, dtype=np.float32)])
    flags = reference_flags(mostly_quiet, 24_000)
    assert "silence" in flags and "noisy" not in flags


def test_reference_flags_edge_cases() -> None:
    assert reference_flags(np.zeros(0, dtype=np.float32), 24_000) == set()
    assert reference_flags(speechlike(0.2), 24_000) <= {"quiet", "clipping"}  # za krótkie na analizę dynamiki
    assert "quiet" in reference_flags(np.zeros(48_000, dtype=np.float32), 24_000)


def test_slice_count() -> None:
    assert slice_count(0, 10) == 1
    assert slice_count(10, 10) == 1
    assert slice_count(11, 10) == 2
    assert slice_count(95, 10) == 10
