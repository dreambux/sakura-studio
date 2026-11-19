"""Biblioteka głosów znajomych na dysku. Zapis atomowy: katalog głosu powstaje w .tmp i jest przemianowywany."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import shutil
import threading
import unicodedata
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .errors import (
    E_BAD_REQUEST,
    E_VOICE_LIMIT,
    E_VOICE_NOT_FOUND,
    VoiceMachineError,
)

log = logging.getLogger("voice_machine.voices")

SCHEMA = 1
CONSENT_STATEMENT_VERSION = 1
CONSENT_STATEMENT_PL = "Osoba, której głos dodaję, wie o tym i zgodziła się na użycie jej głosu w tym narzędziu."
MAX_NAME_CHARS = 40
MAX_TRANSCRIPT_CHARS = 600

_VOICE_ID_RE = re.compile(r"^v_[0-9a-f]{12}$")
_LANGUAGE_RE = re.compile(r"^[a-z]{2,3}(-[a-z]{2,4})?$")


def is_valid_voice_id(voice_id: str) -> bool:
    return isinstance(voice_id, str) and _VOICE_ID_RE.fullmatch(voice_id) is not None


def clean_name(name: str) -> str:
    text = unicodedata.normalize("NFC", name)
    if any(unicodedata.category(ch) in ("Cc", "Cf", "Zl", "Zp") for ch in text):
        raise VoiceMachineError(E_BAD_REQUEST, "Nazwa głosu zawiera niedozwolone znaki.")
    text = " ".join(text.split())
    if not text:
        raise VoiceMachineError(E_BAD_REQUEST, "Podaj nazwę głosu.")
    if len(text) > MAX_NAME_CHARS:
        raise VoiceMachineError(E_BAD_REQUEST, f"Nazwa głosu może mieć najwyżej {MAX_NAME_CHARS} znaków.")
    return text


def clean_transcript(text: str | None) -> str | None:
    """Transkrypcja nagrania wzorcowego: jedna linia, bez znaków sterujących, najwyżej MAX_TRANSCRIPT_CHARS."""
    if text is None:
        return None
    cleaned = unicodedata.normalize("NFC", text)
    if any(unicodedata.category(ch) in ("Cc", "Cf", "Zl", "Zp") and ch not in "\n\r\t" for ch in cleaned):
        raise VoiceMachineError(E_BAD_REQUEST, "Transkrypcja zawiera niedozwolone znaki.")
    cleaned = " ".join(cleaned.split())
    if not cleaned:
        return None
    if len(cleaned) > MAX_TRANSCRIPT_CHARS:
        raise VoiceMachineError(E_BAD_REQUEST, f"Transkrypcja może mieć najwyżej {MAX_TRANSCRIPT_CHARS} znaków.")
    return cleaned


def clean_language(language: str) -> str:
    code = language.strip().lower()
    if not _LANGUAGE_RE.fullmatch(code):
        raise VoiceMachineError(E_BAD_REQUEST, "Nieprawidłowy kod języka.")
    return code


@dataclass(frozen=True)
class PreparedSample:
    data: bytes  # WAV PCM 16-bit mono
    sample_rate: int
    frames: int
    sha256: str

    @property
    def duration_s(self) -> float:
        return self.frames / self.sample_rate


@dataclass(frozen=True)
class SampleInfo:
    file: str
    sha256: str
    duration_s: float
    sample_rate: int
    frames: int


@dataclass(frozen=True)
class VoiceRecord:
    id: str
    name: str
    language: str
    created_at: str
    consent_at: str
    samples: tuple[SampleInfo, ...]
    fingerprint: str
    transcript: str | None = None

    @property
    def duration_s(self) -> float:
        return sum(s.duration_s for s in self.samples)

    def to_public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "kind": "cloned",
            "language": self.language,
            "created_at": self.created_at,
            "duration_s": round(self.duration_s, 1),
            "sample_count": len(self.samples),
            "has_transcript": self.transcript is not None,
            "consent": {"confirmed": True, "at": self.consent_at},
        }

    def to_json(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "id": self.id,
            "name": self.name,
            "language": self.language,
            "transcript": self.transcript,
            "created_at": self.created_at,
            "consent": {
                "confirmed": True,
                "at": self.consent_at,
                "statement_version": CONSENT_STATEMENT_VERSION,
                "statement": CONSENT_STATEMENT_PL,
            },
            "fingerprint": self.fingerprint,
            "samples": [
                {
                    "file": s.file,
                    "sha256": s.sha256,
                    "duration_s": s.duration_s,
                    "sample_rate": s.sample_rate,
                    "frames": s.frames,
                }
                for s in self.samples
            ],
        }


def _parse_record(raw: Any, expected_id: str) -> VoiceRecord:
    if not isinstance(raw, dict) or raw.get("schema") != SCHEMA or raw.get("id") != expected_id:
        raise ValueError("unexpected schema or id")
    consent = raw["consent"]
    if consent.get("confirmed") is not True:
        raise ValueError("consent not confirmed")
    samples = tuple(
        SampleInfo(
            file=str(s["file"]),
            sha256=str(s["sha256"]),
            duration_s=float(s["duration_s"]),
            sample_rate=int(s["sample_rate"]),
            frames=int(s["frames"]),
        )
        for s in raw["samples"]
    )
    if not samples or any(not re.fullmatch(r"s[0-9]{1,2}\.wav", s.file) for s in samples):
        raise ValueError("bad samples")
    transcript = raw.get("transcript")
    if transcript is not None and not isinstance(transcript, str):
        raise ValueError("bad transcript")
    return VoiceRecord(
        id=expected_id,
        name=clean_name(str(raw["name"])),
        language=clean_language(str(raw["language"])),
        created_at=str(raw["created_at"]),
        consent_at=str(consent["at"]),
        samples=samples,
        fingerprint=str(raw["fingerprint"]),
        transcript=clean_transcript(transcript),
    )


def fingerprint_of(samples: Sequence[PreparedSample], transcript: str | None = None) -> str:
    """Odcisk głosu: zmienia się, gdy zmienią się próbki albo transkrypcja (to unieważnia pamięć podręczną silnika)."""
    material = ",".join(s.sha256 for s in samples)
    if transcript:
        material += "|" + transcript
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


class VoiceStore:
    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._sweep()

    def _sweep(self) -> None:
        for entry in self.root.iterdir():
            if entry.is_dir() and entry.name.startswith((".tmp-", ".trash-")):
                shutil.rmtree(entry, ignore_errors=True)

    def _dir(self, voice_id: str) -> Path:
        if not is_valid_voice_id(voice_id):
            raise VoiceMachineError(E_VOICE_NOT_FOUND, "Nie ma takiego głosu.")
        return self.root / voice_id

    def _ids(self) -> list[str]:
        return sorted(p.name for p in self.root.iterdir() if p.is_dir() and is_valid_voice_id(p.name))

    def count(self) -> int:
        with self._lock:
            return len(self._ids())

    def list(self) -> list[VoiceRecord]:
        with self._lock:
            records = []
            for voice_id in self._ids():
                try:
                    records.append(self._load(voice_id))
                except (OSError, ValueError, KeyError, TypeError) as exc:
                    log.warning("skipping unreadable voice %s: %s", voice_id, exc)
            return sorted(records, key=lambda r: r.created_at)

    def _load(self, voice_id: str) -> VoiceRecord:
        raw = json.loads((self._dir(voice_id) / "voice.json").read_text(encoding="utf-8"))
        return _parse_record(raw, voice_id)

    def get(self, voice_id: str) -> VoiceRecord:
        with self._lock:
            directory = self._dir(voice_id)
            if not directory.is_dir():
                raise VoiceMachineError(E_VOICE_NOT_FOUND, "Nie ma takiego głosu.")
            try:
                return self._load(voice_id)
            except (OSError, ValueError, KeyError, TypeError) as exc:
                log.warning("unreadable voice %s: %s", voice_id, exc)
                raise VoiceMachineError(E_VOICE_NOT_FOUND, "Dane tego głosu są uszkodzone.") from exc

    def sample_paths(self, voice_id: str) -> tuple[Path, ...]:
        record = self.get(voice_id)
        base = self._dir(voice_id) / "samples"
        return tuple(base / s.file for s in record.samples)

    def cache_dir(self, voice_id: str) -> Path:
        directory = self._dir(voice_id) / "cache"
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    def create(
        self,
        name: str,
        language: str,
        samples: Sequence[PreparedSample],
        *,
        max_voices: int,
        now: datetime | None = None,
        transcript: str | None = None,
    ) -> VoiceRecord:
        name = clean_name(name)
        language = clean_language(language)
        transcript = clean_transcript(transcript)
        if not samples:
            raise VoiceMachineError(E_BAD_REQUEST, "Brak próbek głosu.")
        stamp = (now or datetime.now(timezone.utc)).strftime("%Y-%m-%dT%H:%M:%SZ")
        with self._lock:
            if len(self._ids()) >= max_voices:
                raise VoiceMachineError(E_VOICE_LIMIT, f"Osiągnięto limit {max_voices} głosów. Usuń któryś, żeby dodać nowy.")
            voice_id = f"v_{uuid.uuid4().hex[:12]}"
            while (self.root / voice_id).exists():
                voice_id = f"v_{uuid.uuid4().hex[:12]}"
            tmp = self.root / f".tmp-{uuid.uuid4().hex}"
            (tmp / "samples").mkdir(parents=True)
            try:
                infos = []
                for index, sample in enumerate(samples):
                    filename = f"s{index}.wav"
                    (tmp / "samples" / filename).write_bytes(sample.data)
                    infos.append(
                        SampleInfo(
                            file=filename,
                            sha256=sample.sha256,
                            duration_s=round(sample.duration_s, 3),
                            sample_rate=sample.sample_rate,
                            frames=sample.frames,
                        )
                    )
                record = VoiceRecord(
                    id=voice_id,
                    name=name,
                    language=language,
                    created_at=stamp,
                    consent_at=stamp,
                    samples=tuple(infos),
                    fingerprint=fingerprint_of(samples, transcript),
                    transcript=transcript,
                )
                (tmp / "voice.json").write_text(
                    json.dumps(record.to_json(), ensure_ascii=False, indent=2), encoding="utf-8"
                )
                os.replace(tmp, self.root / voice_id)
            except BaseException:
                shutil.rmtree(tmp, ignore_errors=True)
                raise
            return record

    def delete(self, voice_id: str) -> None:
        with self._lock:
            directory = self._dir(voice_id)
            if not directory.is_dir():
                raise VoiceMachineError(E_VOICE_NOT_FOUND, "Nie ma takiego głosu.")
            trash = self.root / f".trash-{uuid.uuid4().hex}"
            os.replace(directory, trash)
            shutil.rmtree(trash, ignore_errors=True)
