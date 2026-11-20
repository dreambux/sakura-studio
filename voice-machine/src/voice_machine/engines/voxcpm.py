"""Silnik VoxCPM2 (OpenBMB): klonowanie głosu z jednego nagrania wzorcowego i opcjonalnej transkrypcji, wyjście 48 kHz.

Fakty o API pochodzą z czytania źródeł pakietu voxcpm 2.0.3 (voxcpm/core.py, model/voxcpm2.py,
modules/audiovae/audio_vae_v2.py oraz README w METADATA). Nic z tego nie było uruchamiane w środowisku,
w którym powstał ten plik: nie było tam wag modelu ani dostępu do Hugging Face. Zachowanie na prawdziwym
modelu potwierdza dopiero `python -m voice_machine doctor --engine voxcpm --load` u użytkownika.
"""

from __future__ import annotations

import importlib.metadata as metadata
import logging
import math
import os
import platform
import re
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from ..config import Settings
from ..errors import E_ENGINE_FAILED, E_LANGUAGE, E_NOT_READY, VoiceMachineError
from .base import AudioClip, EngineInfo, EngineState, ReferencePolicy, SynthParams, VoiceRef

log = logging.getLogger("voice_machine.engines.voxcpm")

# --- wartości zależne od wersji modelu: skąd pochodzą ---------------------------------------------------------------
PINNED_VERSION = "2.0.3"  # pip install voxcpm==2.0.3 (wheel sha256 24da58a30d09...); to tę wersję czytano
MODEL_ID = "openbmb/VoxCPM2"  # voxcpm/core.py:106, domyślny hf_model_id
REFERENCE_SAMPLE_RATE = 16_000  # modules/audiovae/audio_vae_v2.py:366 (AudioVAEConfig.sample_rate); README: "Accepts 16kHz reference audio"
EXPECTED_OUTPUT_RATE = 48_000  # audio_vae_v2.py:367 (AudioVAEConfig.out_sample_rate); w trakcie pracy czytamy model.tts_model.sample_rate
DEFAULT_CFG_VALUE = 2.0  # core.py:186
DEFAULT_TIMESTEPS = 10  # core.py:187
PYTHON_RANGE = ((3, 10), (3, 13))  # README: "Python >= 3.10 (<3.13)"
BUILTIN_VOICE = "domyslny"  # generowanie bez nagrania wzorcowego: model sam dobiera głos (README: sekcja Text-to-Speech)
# README "Supported Languages (30)": nazwy angielskie przeliczone na kody ISO 639-1 (przeliczenie własne).
LANGUAGES = (
    "ar", "my", "zh", "da", "nl", "en", "fi", "fr", "de", "el", "he", "hi", "id", "it", "ja",
    "km", "ko", "lo", "ms", "no", "pl", "pt", "ru", "es", "sw", "sv", "tl", "th", "tr", "vi",
)
# NIEKALIBROWANE (własny wybór): autorzy nie podają limitu długości tekstu; zdanie lub dwa na fragment.
DEFAULT_CHUNK_CHARS = 240
# Autorzy nie podają zalecanej długości nagrania. Zakres poniżej to ostrożna reguła kciuka (niekalibrowana):
# pomiary użytkowników pokazują, że sama długość prawie nie przewiduje jakości.
REFERENCE_POLICY = ReferencePolicy(
    max_files=1,
    min_seconds=2.0,
    max_seconds=30.0,
    recommended_seconds=(6.0, 15.0),
    transcript="optional",
    note=(
        "Z transkrypcją model używa trybu „Ultimate Cloning” (autorzy zalecają go dla największego podobieństwa); "
        "bez niej klonuje z samego nagrania. Autorzy zaznaczają, że wynik bywa różny między próbami, więc warto "
        "wygenerować 1-3 razy."
    ),
)
CAPABILITIES = {"speed": False, "temperature": False, "seed": True}
MIN_VRAM_GIB = 5.5  # tolerancyjny próg ostrzeżenia o pamięci karty (6 GB to ok. 5,7 GiB)
RETRY_COOLDOWN_S = 30.0  # tyle czekamy po nieudanym ładowaniu, zanim kolejne wywołanie start_loading() spróbuje ponownie

# Nazwy argumentów, które przekazujemy do biblioteki. Test kontraktowy porównuje je z sygnaturami w źródłach.
FROM_PRETRAINED_KWARGS = ("load_denoiser", "optimize", "device", "local_files_only")
GENERATE_KWARGS = (
    "text", "cfg_value", "inference_timesteps", "normalize", "denoise",
    "prompt_wav_path", "prompt_text", "reference_wav_path",
)


@dataclass(frozen=True)
class VoxCpmConfig:
    model: str = MODEL_ID
    cfg_value: float = DEFAULT_CFG_VALUE
    timesteps: int = DEFAULT_TIMESTEPS
    optimize: bool = False  # torch.compile bywa kłopotliwe na Windows (kompilator, Triton); włącz SVM_VOXCPM_OPTIMIZE=1
    chunk_chars: int = DEFAULT_CHUNK_CHARS
    warnings: tuple[str, ...] = ()

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "VoxCpmConfig":
        env = os.environ if env is None else env
        problems: list[str] = []

        def number(name: str, default: float, low: float, high: float, integer: bool = False) -> float:
            raw = env.get(name)
            if raw is None or not raw.strip():
                return default
            try:
                value = float(raw.replace(",", "."))
                if not math.isfinite(value) or not low <= value <= high:
                    raise ValueError
                return int(value) if integer else value
            except ValueError:
                problems.append(f"{name}={raw!r} poza zakresem {low:g}-{high:g}, używam {default:g}")
                return default

        optimize_raw = (env.get("SVM_VOXCPM_OPTIMIZE") or "").strip().lower()
        return cls(
            model=(env.get("SVM_VOXCPM_MODEL") or MODEL_ID).strip() or MODEL_ID,
            cfg_value=float(number("SVM_VOXCPM_CFG", DEFAULT_CFG_VALUE, 0.5, 10.0)),
            timesteps=int(number("SVM_VOXCPM_TIMESTEPS", DEFAULT_TIMESTEPS, 1, 100, integer=True)),
            optimize=optimize_raw in {"1", "true", "yes", "on", "tak"},
            chunk_chars=int(number("SVM_VOXCPM_CHUNK_CHARS", DEFAULT_CHUNK_CHARS, 60, 800, integer=True)),
            warnings=tuple(problems),
        )


_WINERROR_HINTS = {
    "126": "Brakuje biblioteki systemowej: zainstaluj „Visual C++ Redistributable x64” (https://aka.ms/vs/17/release/vc_redist.x64.exe) i uruchom ponownie.",
    "1114": "Nie udało się zainicjować biblioteki: zainstaluj „Visual C++ Redistributable x64” i zaktualizuj sterownik karty NVIDIA.",
    "1455": "Za mały plik stronicowania Windows: zwiększ plik wymiany (Pamięć wirtualna w ustawieniach zaawansowanych systemu) albo zamknij inne programy.",
}
# Wyłącznie oznaki problemu z siecią. Gołe słowa "huggingface" i "resolve" pasowały też do błędu złego katalogu modelu.
_NETWORK_MARKERS = (
    "max retries", "getaddrinfo", "connection error", "connection refused", "connection reset", "name or service not known",
    "temporary failure in name resolution", "timed out", "connecterror", "connecttimeout", "offlinemodeisenabled", "localentrynotfound",
)


def explain_failure(exc: BaseException) -> str:
    """Zamienia wyjątek z biblioteki na komunikat z podpowiedzią (po polsku, bez śladu stosu)."""
    if isinstance(exc, VoiceMachineError):
        return exc.message
    name = type(exc).__name__
    text = f"{name}: {str(exc)[:300]}".strip()
    lowered = text.lower()
    if "out of memory" in lowered or "outofmemory" in lowered:
        return f"Za mało pamięci karty graficznej (model potrzebuje około 8 GB wg autorów). Skróć tekst albo zamknij inne programy korzystające z karty. {text}"
    winerror = re.search(r"winerror (\d+)", lowered)
    if winerror and winerror.group(1) in _WINERROR_HINTS:
        return f"{_WINERROR_HINTS[winerror.group(1)]} ({text})"
    if "kv cache is full" in lowered:
        return f"Tekst razem z nagraniem wzorcowym jest za długi dla modelu. Skróć tekst albo użyj krótszego nagrania. {text}"
    if isinstance(exc, FileNotFoundError) and "reference" in lowered:
        return f"Nie znaleziono pliku nagrania wzorcowego (czy głos został usunięty?). {text}"
    if isinstance(exc, (ConnectionError, TimeoutError)) or any(marker in lowered for marker in _NETWORK_MARKERS):
        return f"Nie udało się pobrać modelu z Hugging Face: sprawdź internet i dostęp do huggingface.co. {text}"
    return text


_RE_LEADING_BRACKET_PAIR = re.compile(r"^\s*[(（]([^()（）]*)[)）]\s*")
_RE_LEADING_BRACKET = re.compile(r"^\s*[(（]\s*")


def guard_control_prefix(text: str) -> str:
    """Tekst zaczynający się od nawiasu VoxCPM2 czyta jako opis głosu ("(młoda kobieta)Tekst"), a nie jako treść.
    Zdejmujemy nawias i zostawiamy jego zawartość: "(Uwaga!) Dzień dobry" -> "Uwaga! Dzień dobry"."""
    if _RE_LEADING_BRACKET_PAIR.match(text):
        return _RE_LEADING_BRACKET_PAIR.sub(lambda m: f"{m.group(1).strip()} ", text, count=1).strip()
    return _RE_LEADING_BRACKET.sub("", text, count=1)


def hf_hub_cache_dir() -> Path:
    """Katalog pamięci podręcznej Hugging Face (kolejność jak w bibliotece: HF_HUB_CACHE, HF_HOME/hub, ~/.cache/huggingface/hub)."""
    explicit = os.environ.get("HF_HUB_CACHE")
    if explicit:
        return Path(explicit)
    home = os.environ.get("HF_HOME")
    return (Path(home) if home else Path.home() / ".cache" / "huggingface") / "hub"


def model_is_cached(model: str) -> bool:
    """Czy migawka modelu z Hugging Face leży już na dysku. Lokalny katalog modelu to inny przypadek (jego biblioteka
    i tak używa bez sieci), więc tu daje false. Pomyłka w którąkolwiek stronę jest bezpieczna: patrz _load_model."""
    if Path(model).is_dir():
        return False
    snapshots = hf_hub_cache_dir() / f"models--{model.replace('/', '--')}" / "snapshots"
    try:
        return any(entry.is_dir() for entry in snapshots.iterdir())
    except OSError:
        return False


class VoxCpmEngine:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._cfg = VoxCpmConfig.from_env()
        self._lock = threading.Lock()
        self._gen_lock = threading.Lock()
        self._state = EngineState.IDLE
        self._error: str | None = None
        self._thread: threading.Thread | None = None
        self._failed_at = 0.0
        self._model: Any = None
        self._torch: Any = None
        self._rate: int | None = None
        self._device: str | None = None

    # --- stan -------------------------------------------------------------------------------------------------------
    def info(self) -> EngineInfo:
        with self._lock:
            state, error, rate, device = self._state, self._error, self._rate, self._device
        ready = state is EngineState.READY
        notes = list(self._cfg.warnings)
        if ready and device and device.startswith("cpu"):
            notes.insert(0, "Model działa na procesorze, bez karty graficznej: synteza będzie bardzo wolna (model ma około 2 mld parametrów).")
        return EngineInfo(
            id="voxcpm2",
            name="VoxCPM2 (OpenBMB)",
            state=state,
            device=device if ready else None,
            error=error,
            languages=LANGUAGES,
            builtin_voices=(BUILTIN_VOICE,) if ready else (),
            sample_rate=rate,
            reference_sample_rate=REFERENCE_SAMPLE_RATE,
            notes=tuple(notes),
            reference=REFERENCE_POLICY,
            capabilities=dict(CAPABILITIES),
        )

    def start_loading(self) -> None:
        """Rusza ładowanie modelu. Po nieudanym ładowaniu (np. zerwane pobieranie) próbuje znowu, ale najwcześniej po
        RETRY_COOLDOWN_S sekundach, żeby odpytywanie stanu nie uruchamiało pobierania w pętli."""
        with self._lock:
            if self._state is EngineState.ERROR and time.monotonic() - self._failed_at >= RETRY_COOLDOWN_S:
                self._state = EngineState.IDLE
                self._error = None
            if self._state is not EngineState.IDLE:
                return
            self._state = EngineState.LOADING
            self._thread = threading.Thread(target=self._load, name="svm-voxcpm-load", daemon=True)
            self._thread.start()

    def _load(self) -> None:
        try:
            model, torch, rate, device = self._load_model()
        except BaseException as exc:  # noqa: BLE001 - błąd ładowania ma trafić do stanu, nie zabić wątku
            log.exception("VoxCPM2 failed to load")
            with self._lock:
                self._state = EngineState.ERROR
                self._error = explain_failure(exc)
                self._failed_at = time.monotonic()
            return
        with self._lock:
            self._model, self._torch, self._rate, self._device = model, torch, rate, device
            self._state = EngineState.READY

    def _load_model(self) -> tuple[Any, Any, int, str]:
        low, high = PYTHON_RANGE
        if not low <= sys.version_info[:2] < high:
            raise VoiceMachineError(
                E_ENGINE_FAILED,
                f"VoxCPM2 działa na Pythonie 3.10-3.12, a to jest {platform.python_version()}. Zainstaluj Pythona 3.11 i utwórz nowe środowisko.",
            )
        try:
            import torch
            from voxcpm import VoxCPM
        except ImportError as exc:
            raise VoiceMachineError(
                E_ENGINE_FAILED,
                f'Brak zależności silnika ({exc}). Zainstaluj PyTorch (pytorch.org) i wykonaj: pip install -e ".[voxcpm]".',
            ) from exc
        except OSError as exc:  # na Windows brak biblioteki DLL (VC++ Redistributable, plik stronicowania) to OSError, nie ImportError
            raise VoiceMachineError(E_ENGINE_FAILED, f"Nie udało się wczytać PyTorch. {explain_failure(exc)}") from exc
        kwargs: dict[str, Any] = {"load_denoiser": False, "optimize": self._cfg.optimize, "device": self._settings.device}
        model = None
        if model_is_cached(self._cfg.model):
            # Model już leży na dysku: nie pytamy Hugging Face przy każdym starcie (działa bez internetu, a wersja modelu
            # nie zmienia się sama po aktualizacji repozytorium). Bez tego biblioteka odpytuje sieć za każdym razem.
            try:
                model = VoxCPM.from_pretrained(self._cfg.model, local_files_only=True, **kwargs)
            except Exception:  # noqa: BLE001 - niepełna kopia na dysku: dociągnij brakujące pliki zwykłym ładowaniem
                log.warning("cached model snapshot could not be used offline; falling back to a normal load", exc_info=True)
        if model is None:
            model = VoxCPM.from_pretrained(self._cfg.model, **kwargs)
        rate = int(model.tts_model.sample_rate)
        if not 8_000 <= rate <= 96_000:
            raise VoiceMachineError(E_ENGINE_FAILED, f"Model zgłosił nieprawdopodobną częstotliwość próbkowania: {rate} Hz.")
        device = str(getattr(model.tts_model, "device", None) or self._settings.device or "auto")
        return model, torch, rate, device

    # --- język i podział tekstu ---------------------------------------------------------------------------------------
    def max_chunk_chars(self, language: str) -> int:
        return self._cfg.chunk_chars

    def validate_language(self, language: str) -> str:
        code = language.strip().lower().split("-")[0]
        if code not in LANGUAGES:
            raise VoiceMachineError(E_LANGUAGE, f"Język '{language}' nie jest obsługiwany przez VoxCPM2.")
        return code

    # --- synteza ------------------------------------------------------------------------------------------------------
    def synthesize(self, text: str, language: str, voice: VoiceRef, params: SynthParams) -> AudioClip:
        with self._lock:
            model, torch, rate, state = self._model, self._torch, self._rate, self._state
        if state is not EngineState.READY or model is None or rate is None:
            raise VoiceMachineError(E_NOT_READY, "Silnik nie jest gotowy.")
        kwargs: dict[str, Any] = {
            "cfg_value": self._cfg.cfg_value,
            "inference_timesteps": self._cfg.timesteps,
            "normalize": False,  # polską normalizację robi voice_machine.normalize_pl; wbudowana jest na chiński i angielski
            "denoise": False,  # odszumianie wzorca bywa przyczyną przekłamań (zgłoszenia użytkowników), więc wyłączone
        }
        if voice.kind == "cloned":
            if not voice.sample_paths:
                raise VoiceMachineError(E_ENGINE_FAILED, "Ten głos nie ma zapisanego nagrania wzorcowego.")
            reference = str(voice.sample_paths[0])
            if voice.transcript:
                kwargs.update(prompt_wav_path=reference, prompt_text=voice.transcript, reference_wav_path=reference)
            else:
                kwargs["reference_wav_path"] = reference
        try:
            with self._gen_lock:
                if params.seed is not None:
                    torch.manual_seed(params.seed)
                    if torch.cuda.is_available():
                        torch.cuda.manual_seed_all(params.seed)
                wav = model.generate(text=guard_control_prefix(text), **kwargs)
        except VoiceMachineError:
            raise
        except Exception as exc:  # noqa: BLE001 - brak pamięci karty, błąd modelu: właściciel dostaje podpowiedź zamiast surowego wyjątku
            log.exception("VoxCPM2 synthesis failed")
            raise VoiceMachineError(E_ENGINE_FAILED, explain_failure(exc)) from exc
        audio = np.asarray(wav, dtype=np.float32).reshape(-1)
        if audio.size == 0 or not np.all(np.isfinite(audio)):
            raise VoiceMachineError(E_ENGINE_FAILED, "Model zwrócił puste lub nieprawidłowe audio.")
        return AudioClip(samples=audio, sample_rate=rate)

    # --- doctor -------------------------------------------------------------------------------------------------------
    def diagnose(self) -> list[tuple[str, str, bool]]:
        out: list[tuple[str, str, bool]] = []
        low, high = PYTHON_RANGE
        out.append(("Python (VoxCPM2: 3.10-3.12)", platform.python_version(), low <= sys.version_info[:2] < high))
        torch = None
        try:
            import torch  # type: ignore[no-redef]

            out.append(("PyTorch", str(torch.__version__), True))
        except ImportError:
            out.append(("PyTorch", "brak: zainstaluj wersję z pytorch.org (CUDA dla karty NVIDIA)", False))
        except OSError as exc:  # Windows: brakująca biblioteka DLL to OSError
            out.append(("PyTorch", f"nie wczytuje się. {explain_failure(exc)}", False))
        if torch is not None:
            if torch.cuda.is_available():
                props = torch.cuda.get_device_properties(0)
                gigabytes = props.total_memory / 2**30
                # Karty "6 GB" zgłaszają zwykle nieco mniej niż 6 GiB, więc próg jest tolerancyjny (autorzy podają ok. 8 GB).
                out.append(
                    (
                        "karta CUDA",
                        f"{props.name}, {gigabytes:.1f} GB (autorzy podają ok. 8 GB, zgłoszono działanie na 6 GB)",
                        True if gigabytes >= MIN_VRAM_GIB else None,
                    )
                )
            else:
                # To ostrzeżenie, nie błąd: na procesorze model działa, tylko bardzo wolno. Skrypt instalacyjny sam pilnuje,
                # czy ktoś, kto wybrał wersję CUDA, faktycznie ją dostał.
                out.append(("karta CUDA", "niedostępna: synteza na procesorze będzie bardzo wolna", None))
        try:
            version = metadata.version("voxcpm")
            note = "" if version == PINNED_VERSION else f" (adapter sprawdzono tylko z {PINNED_VERSION})"
            out.append(("voxcpm", version + note, True))
        except metadata.PackageNotFoundError:
            out.append(("voxcpm", f'brak: pip install -e ".[voxcpm]" (wersja {PINNED_VERSION})', False))
        if Path(self._cfg.model).is_dir():
            has_config = (Path(self._cfg.model) / "config.json").is_file()
            out.append(("model na dysku", f"lokalny katalog {self._cfg.model}" + ("" if has_config else " (brak config.json)"), has_config))
        else:
            cached = model_is_cached(self._cfg.model)
            out.append(
                (
                    "model na dysku",
                    "jest (kolejne starty nie łączą się z internetem)" if cached else "brak, zostanie pobrany przy pierwszym uruchomieniu (kilka GB)",
                    True,
                )
            )
        return out

    def close(self) -> None:
        with self._lock:
            model, torch = self._model, self._torch
            self._model = None
        del model
        try:
            if torch is not None and torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:  # noqa: BLE001 - sprzątanie nie może przerwać zamykania
            pass
