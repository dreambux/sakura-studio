"""Kontrakt silnika syntezy. Reszta aplikacji nie wie nic o tensorach ani o konkretnym modelu."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Literal, Protocol

import numpy as np


class EngineState(str, Enum):
    IDLE = "idle"
    LOADING = "loading"
    READY = "ready"
    ERROR = "error"


@dataclass(frozen=True)
class VoiceRef:
    kind: Literal["builtin", "cloned"]
    voice_id: str
    name: str
    fingerprint: str
    sample_paths: tuple[Path, ...] = ()
    cache_dir: Path | None = None
    transcript: str | None = None  # dokładny tekst nagrania wzorcowego, jeśli model go używa
    language: str | None = None  # język nagrania wzorcowego


@dataclass(frozen=True)
class ReferencePolicy:
    """Czego konkretny model potrzebuje od nagrania wzorcowego. Strona i serwer egzekwują to przy dodawaniu głosu."""

    max_files: int = 8
    min_seconds: float = 3.0
    max_seconds: float = 120.0
    recommended_seconds: tuple[float, float] = (8.0, 20.0)
    transcript: Literal["none", "optional", "required"] = "none"
    note: str = ""

    def to_public(self) -> dict[str, Any]:
        return {
            "max_files": self.max_files,
            "min_seconds": self.min_seconds,
            "max_seconds": self.max_seconds,
            "recommended_seconds": list(self.recommended_seconds),
            "transcript": self.transcript,
            "note": self.note,
        }


@dataclass(frozen=True)
class SynthParams:
    speed: float = 1.0
    temperature: float = 0.7
    seed: int | None = None


@dataclass(frozen=True)
class AudioClip:
    samples: np.ndarray  # float32, mono, [-1, 1]
    sample_rate: int


@dataclass(frozen=True)
class EngineInfo:
    id: str
    name: str
    state: EngineState
    device: str | None
    error: str | None
    languages: tuple[str, ...]
    builtin_voices: tuple[str, ...]
    sample_rate: int | None
    reference_sample_rate: int
    notes: tuple[str, ...] = ()
    reference: ReferencePolicy = ReferencePolicy()
    # Które regulacje model naprawdę respektuje; strona ukrywa te, których nie ma.
    capabilities: Mapping[str, bool] = field(default_factory=lambda: {"speed": True, "temperature": True, "seed": True})

    def to_public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "state": self.state.value,
            "device": self.device,
            "error": self.error,
            "languages": list(self.languages),
            "builtin_voices": list(self.builtin_voices),
            "sample_rate": self.sample_rate,
            "reference_sample_rate": self.reference_sample_rate,
            "notes": list(self.notes),
            "reference": self.reference.to_public(),
            "capabilities": dict(self.capabilities),
        }


class Engine(Protocol):
    def info(self) -> EngineInfo: ...

    def start_loading(self) -> None:
        """Nieblokujące i idempotentne. Błąd ładowania ląduje w info().error."""

    def max_chunk_chars(self, language: str) -> int: ...

    def validate_language(self, language: str) -> str:
        """Zwraca znormalizowany kod języka albo rzuca VoiceMachineError(E_LANGUAGE)."""

    def synthesize(self, text: str, language: str, voice: VoiceRef, params: SynthParams) -> AudioClip: ...

    def diagnose(self) -> list[tuple[str, str, bool | None]]:
        """Pary (etykieta, wartość, czy_ok) dla polecenia doctor."""

    def close(self) -> None: ...
