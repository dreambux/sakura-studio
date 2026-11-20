"""Polecenie doctor: sprawdza środowisko i opcjonalnie robi próbną syntezę na prawdziwym silniku."""

from __future__ import annotations

import importlib.metadata as metadata
import platform
import sys
import tempfile
import time
from pathlib import Path

from .config import Settings
from .engines import create_engine
from .engines.base import AudioClip, Engine, EngineInfo, EngineState, SynthParams, VoiceRef
from .errors import VoiceMachineError
from .service import data_dir_writable
from .wavio import encode_wav_pcm16, sha256_hex

MIN_SMOKE_SECONDS = 0.3


def _version(package: str) -> str:
    try:
        return metadata.version(package)
    except metadata.PackageNotFoundError:
        return "brak"


def _line(label: str, value: str, ok: bool | None) -> bool:
    """ok=None to ostrzeżenie ([UWAGA]): widoczne, ale nie psuje wyniku doctora."""
    tag = "UWAGA" if ok is None else ("OK " if ok else "BRAK")
    print(f"[{tag}] {label}: {value}")
    return ok is not False


def _clone_checks(engine: Engine, info: EngineInfo, source: AudioClip, phrase: str, language: str, out_dir: Path) -> bool:
    """Sprawdza ścieżkę, którą idzie prawdziwe klonowanie: wczytanie pliku wzorcowego i synteza jego głosem.

    Wzorcem jest nagranie z próbnej syntezy (to mowa, więc działa na każdym silniku i nie trzeba żadnego pliku od
    użytkownika). Bez tego doctor sprawdzałby tylko głos wbudowany, a pierwsza porażka wychodziłaby dopiero przy
    dodawaniu głosu znajomego (na przykład z powodu brakującej biblioteki do wczytywania audio).
    """
    policy = info.reference
    variants: list[tuple[str, str | None]] = []
    if policy.transcript != "required":
        variants.append(("bez transkrypcji", None))
    if policy.transcript != "none":
        variants.append(("z transkrypcją", phrase))
    text = "Sprawdzam, czy głos znajomego brzmi podobnie." if language == "pl" else "Checking that the friend's voice sounds similar."
    good = True
    with tempfile.TemporaryDirectory(prefix="svm-doctor-") as tmp:
        reference = Path(tmp) / "reference.wav"
        reference.write_bytes(encode_wav_pcm16(source.samples, source.sample_rate))
        for label, transcript in variants:
            voice = VoiceRef(
                kind="cloned",
                voice_id="v_000000000000",
                name="doctor",
                fingerprint=sha256_hex(f"doctor:{label}".encode()),
                sample_paths=(reference,),
                transcript=transcript,
                language=language,
            )
            started = time.monotonic()
            try:
                clip = engine.synthesize(text, language, voice, SynthParams())
            except Exception as exc:  # noqa: BLE001 - doctor ma nazwać błąd, nie przerwać się śladem stosu
                good &= _line(f"klonowanie ({label})", f"{type(exc).__name__}: {exc}", False)
                continue
            seconds = clip.samples.shape[0] / clip.sample_rate
            good &= _line(f"klonowanie ({label})", f"{seconds:.2f} s dźwięku w {time.monotonic() - started:.1f} s", seconds > MIN_SMOKE_SECONDS)
            if seconds > MIN_SMOKE_SECONDS:
                target = out_dir / "doctor-smoke-clone.wav"
                target.write_bytes(encode_wav_pcm16(clip.samples, clip.sample_rate))
    if good:
        print(f"Zapisano {out_dir / 'doctor-smoke-clone.wav'}: ta sama próbka jako wzorzec, więc podobieństwo do pierwszego nagrania jest tu tylko sprawdzianem toru, nie jakości klonu.")
    return good


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
    try:
        checks = engine.diagnose()
    except Exception as exc:  # noqa: BLE001 - doctor ma nazwać problem, nie umrzeć na śladzie stosu
        checks = [("diagnostyka silnika", f"{type(exc).__name__}: {exc}", False)]
    for label, value, good in checks:
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
    target_dir = out_dir or Path.cwd()
    started = time.monotonic()
    try:
        clip = engine.synthesize(phrase, language, voice, SynthParams())
    except Exception as exc:  # noqa: BLE001
        _line("próbna synteza", f"{type(exc).__name__}: {exc}", False)
        engine.close()
        return 1
    elapsed = time.monotonic() - started
    target = target_dir / "doctor-smoke.wav"
    target.write_bytes(encode_wav_pcm16(clip.samples, clip.sample_rate))
    seconds = clip.samples.shape[0] / clip.sample_rate
    ok &= _line(
        "próbna synteza",
        f"{seconds:.2f} s dźwięku w {elapsed:.1f} s (głos '{name}', język {language}); zapisano {target}",
        seconds > MIN_SMOKE_SECONDS,
    )
    if seconds > MIN_SMOKE_SECONDS:
        ok &= _clone_checks(engine, info, clip, phrase, language, target_dir)
    print("Posłuchaj pliku doctor-smoke.wav: to jedyny sposób, żeby ocenić, czy głos brzmi sensownie.")
    engine.close()
    return 0 if ok else 1
