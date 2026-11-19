"""Polecenie doctor: sprawdza środowisko i opcjonalnie robi próbną syntezę na prawdziwym silniku."""

from __future__ import annotations

import importlib.metadata as metadata
import platform
import sys
import time
from pathlib import Path

from .config import Settings
from .engines import create_engine
from .engines.base import EngineState, SynthParams, VoiceRef
from .errors import VoiceMachineError
from .service import data_dir_writable
from .wavio import encode_wav_pcm16, sha256_hex


def _version(package: str) -> str:
    try:
        return metadata.version(package)
    except metadata.PackageNotFoundError:
        return "brak"


def _line(label: str, value: str, ok: bool) -> bool:
    print(f"[{'OK ' if ok else 'BRAK'}] {label}: {value}")
    return ok


def run(settings: Settings, *, load: bool, out_dir: Path | None = None) -> int:
    ok = True
    ok &= _line("Python", f"{platform.python_version()} ({platform.system()} {platform.machine()})", sys.version_info >= (3, 10))
    ok &= _line("mcp", _version("mcp"), _version("mcp") != "brak")
    ok &= _line("numpy", _version("numpy"), _version("numpy") != "brak")
    writable, detail = data_dir_writable(settings.data_dir)
    ok &= _line("katalog danych (próbki głosów, nagrania)", detail, writable)

    try:
        engine = create_engine(settings)
    except (VoiceMachineError, ImportError) as exc:
        _line("silnik", f"{settings.engine}: {exc}", False)
        return 1
    for label, value, good in engine.diagnose():
        ok &= _line(label, value, good)

    if not load:
        print("\nPominięto próbne ładowanie modelu. Uruchom z --load, żeby sprawdzić prawdziwą syntezę.")
        engine.close()
        return 0 if ok else 1

    print("\nŁadowanie modelu (pierwsze uruchomienie pobiera pliki, może potrwać kilka minut)...")
    started = time.monotonic()
    engine.start_loading()
    while True:
        info = engine.info()
        if info.state is EngineState.READY:
            break
        if info.state is EngineState.ERROR:
            _line("ładowanie modelu", info.error or "nieznany błąd", False)
            engine.close()
            return 1
        time.sleep(0.5)
    _line("ładowanie modelu", f"{time.monotonic() - started:.1f} s, urządzenie: {info.device}", True)

    if not info.builtin_voices:
        _line("głosy wbudowane", "silnik nie zgłosił żadnych głosów wbudowanych", False)
        engine.close()
        return 1
    language = "pl" if "pl" in info.languages else info.languages[0]
    name = info.builtin_voices[0]
    voice = VoiceRef(kind="builtin", voice_id=f"builtin:{name}", name=name, fingerprint=sha256_hex(name.encode("utf-8")))
    phrase = "Dzień dobry, to jest próbna synteza mowy." if language == "pl" else "Hello, this is a test."
    started = time.monotonic()
    try:
        clip = engine.synthesize(phrase, language, voice, SynthParams())
    except Exception as exc:  # noqa: BLE001
        _line("próbna synteza", f"{type(exc).__name__}: {exc}", False)
        engine.close()
        return 1
    elapsed = time.monotonic() - started
    target = (out_dir or Path.cwd()) / "doctor-smoke.wav"
    target.write_bytes(encode_wav_pcm16(clip.samples, clip.sample_rate))
    seconds = clip.samples.shape[0] / clip.sample_rate
    _line(
        "próbna synteza",
        f"{seconds:.2f} s dźwięku w {elapsed:.1f} s (głos '{name}', język {language}); zapisano {target}",
        seconds > 0.3,
    )
    print("Posłuchaj pliku doctor-smoke.wav: to jedyny sposób, żeby ocenić, czy głos brzmi sensownie.")
    engine.close()
    return 0 if ok else 1
