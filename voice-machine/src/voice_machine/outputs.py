"""Kopie wygenerowanych nagrań na dysku (Discord i edytory chcą prawdziwych plików WAV)."""

from __future__ import annotations

import os
import re
import unicodedata
from datetime import datetime
from pathlib import Path

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(text: str, max_len: int = 24) -> str:
    folded = text.replace("ł", "l").replace("Ł", "L")
    ascii_text = unicodedata.normalize("NFKD", folded).encode("ascii", "ignore").decode("ascii").lower()
    slug = _SLUG_RE.sub("-", ascii_text).strip("-")[:max_len].strip("-")
    return slug or "glos"


class OutputStore:
    def __init__(self, directory: Path) -> None:
        self.directory = Path(directory)

    def save(self, wav: bytes, voice_name: str, job_id: str, when: datetime) -> Path:
        self.directory.mkdir(parents=True, exist_ok=True)
        stem = f"{when.strftime('%Y%m%d-%H%M%S')}_{slugify(voice_name)}_{job_id[-6:]}"
        target = self.directory / f"{stem}.wav"
        partial = self.directory / f"{stem}.wav.part"
        partial.write_bytes(wav)
        os.replace(partial, target)
        return target
