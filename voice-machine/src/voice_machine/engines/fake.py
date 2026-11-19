"""Silnik testowy: generuje tony, nie mowę. Służy do testów protokołu i interfejsu bez modelu.

Zmienne środowiskowe (tylko dla testów):
  SVM_FAKE_LOAD_DELAY    sekundy ładowania (domyślnie 0.3)
  SVM_FAKE_SYNTH_DELAY   sekundy na fragment (domyślnie 0)
  SVM_FAKE_FAIL_ON       podciąg tekstu, który wywołuje błąd silnika
  SVM_FAKE_NOISY_STDOUT  1 = pisz śmieci na stdout (test higieny protokołu)
  SVM_FAKE_REF_TRANSCRIPT none|optional|required  polityka transkrypcji nagrania wzorcowego
  SVM_FAKE_REF_MAX_FILES  najwyżej tyle nagrań na głos (domyślnie 8)
  SVM_FAKE_REF_MIN_SECONDS / SVM_FAKE_REF_MAX_SECONDS  granice łącznej długości nagrań
  SVM_FAKE_NO_CAPS       lista po przecinku regulacji, których silnik "nie ma": speed, temperature, seed
"""

from __future__ import annotations

import os
import threading
import time

import numpy as np

from ..errors import E_ENGINE_FAILED, E_LANGUAGE, E_NOT_READY, VoiceMachineError
from .base import AudioClip, EngineInfo, EngineState, ReferencePolicy, SynthParams, VoiceRef

SAMPLE_RATE = 24_000
LANGUAGES = ("pl", "en")
BUILTIN = ("demo-niski", "demo-wysoki")


def _noise(message: str) -> None:
    if os.environ.get("SVM_FAKE_NOISY_STDOUT") == "1":
        print(message)
        os.write(1, (message + " (raw fd 1)\n").encode())


class FakeEngine:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._state = EngineState.IDLE
        self._error: str | None = None
        self._thread: threading.Thread | None = None

    def info(self) -> EngineInfo:
        with self._lock:
            state, error = self._state, self._error
        ready = state is EngineState.READY
        return EngineInfo(
            id="fake",
            name="Silnik testowy (tony, nie mowa)",
            state=state,
            device="cpu" if ready else None,
            error=error,
            languages=LANGUAGES,
            builtin_voices=BUILTIN if ready else (),
            sample_rate=SAMPLE_RATE,
            reference_sample_rate=SAMPLE_RATE,
            notes=("TRYB TESTOWY: ten silnik generuje tony, nie klonuje głosu.",),
            capabilities={
                name: name not in {c.strip() for c in os.environ.get("SVM_FAKE_NO_CAPS", "").split(",")}
                for name in ("speed", "temperature", "seed")
            },
            reference=ReferencePolicy(
                max_files=int(os.environ.get("SVM_FAKE_REF_MAX_FILES", "8")),
                min_seconds=float(os.environ.get("SVM_FAKE_REF_MIN_SECONDS", "3")),
                max_seconds=float(os.environ.get("SVM_FAKE_REF_MAX_SECONDS", "120")),
                transcript=os.environ.get("SVM_FAKE_REF_TRANSCRIPT", "none"),  # type: ignore[arg-type]
            ),
        )

    def start_loading(self) -> None:
        with self._lock:
            if self._state is not EngineState.IDLE:
                return
            self._state = EngineState.LOADING
            self._thread = threading.Thread(target=self._load, name="svm-fake-load", daemon=True)
            self._thread.start()

    def _load(self) -> None:
        _noise("fake engine: loading")
        time.sleep(float(os.environ.get("SVM_FAKE_LOAD_DELAY", "0.3")))
        with self._lock:
            self._state = EngineState.READY

    def max_chunk_chars(self, language: str) -> int:
        return 120

    def validate_language(self, language: str) -> str:
        code = language.strip().lower()
        if code not in LANGUAGES:
            raise VoiceMachineError(E_LANGUAGE, f"Język '{language}' nie jest obsługiwany. Dostępne: {', '.join(LANGUAGES)}.")
        return code

    def synthesize(self, text: str, language: str, voice: VoiceRef, params: SynthParams) -> AudioClip:
        if self.info().state is not EngineState.READY:
            raise VoiceMachineError(E_NOT_READY, "Silnik nie jest gotowy.")
        _noise("fake engine: synthesize")
        trigger = os.environ.get("SVM_FAKE_FAIL_ON")
        if trigger and trigger in text:
            raise VoiceMachineError(E_ENGINE_FAILED, "Silnik testowy zgłosił błąd na żądanie.")
        delay = float(os.environ.get("SVM_FAKE_SYNTH_DELAY", "0"))
        if delay > 0:
            time.sleep(delay)
        base = 180 + int(voice.fingerprint[:8], 16) % 400
        seconds = max(0.25, len(text) * 0.055 / params.speed)
        n = int(SAMPLE_RATE * seconds)
        t = np.arange(n, dtype=np.float32) / SAMPLE_RATE
        envelope = np.sqrt(np.clip(np.sin(np.pi * np.linspace(0.0, 1.0, n, dtype=np.float32)), 0.0, None))
        wobble = 1.0 + 0.02 * np.sin(2 * np.pi * 5.0 * t)
        samples = (0.25 * np.sin(2 * np.pi * base * wobble * t) * envelope).astype(np.float32)
        return AudioClip(samples=samples, sample_rate=SAMPLE_RATE)

    def diagnose(self) -> list[tuple[str, str, bool]]:
        return [("silnik", "testowy (tony, nie mowa)", True)]

    def close(self) -> None:
        return None
