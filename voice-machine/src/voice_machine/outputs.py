"""Kopie wygenerowanych nagrań na dysku (Discord i edytory chcą prawdziwych plików WAV)."""

from __future__ import annotations

import contextlib
import logging
import os
import re
import unicodedata
from datetime import datetime
from pathlib import Path

log = logging.getLogger("voice_machine.outputs")

_SLUG_RE = re.compile(r"[^a-z0-9]+")
# Nazwa pliku, który zapisuje ta aplikacja: RRRRMMDD-GGMMSS_<głos>_<6 znaków id zadania>.wav. Czyścimy tylko takie pliki.
_OWN_NAME_RE = re.compile(r"^\d{8}-\d{6}_[a-z0-9-]+_[0-9a-f]{6}\.wav$")


def slugify(text: str, max_len: int = 24) -> str:
    folded = text.replace("ł", "l").replace("Ł", "L")
    ascii_text = unicodedata.normalize("NFKD", folded).encode("ascii", "ignore").decode("ascii").lower()
    slug = _SLUG_RE.sub("-", ascii_text).strip("-")[:max_len].strip("-")
    return slug or "glos"


class OutputStore:
    def __init__(self, directory: Path, max_files: int = 0) -> None:
        """max_files: ile najnowszych własnych nagrań zostaje w katalogu (0 = bez limitu)."""
        self.directory = Path(directory)
        self.max_files = max(0, int(max_files))
        self._sweep_partials()

    def _sweep_partials(self) -> None:
        """Niedokończone zapisy (*.wav.part) po awarii albo braku miejsca nie mają właściciela: usuwamy je przy starcie."""
        try:
            for entry in self.directory.glob("*.wav.part"):
                with contextlib.suppress(OSError):
                    entry.unlink()
        except OSError:
            pass

    def save(self, wav: bytes, voice_name: str, job_id: str, when: datetime) -> Path:
        self.directory.mkdir(parents=True, exist_ok=True)
        stem = f"{when.strftime('%Y%m%d-%H%M%S')}_{slugify(voice_name)}_{job_id[-6:]}"
        target = self.directory / f"{stem}.wav"
        partial = self.directory / f"{stem}.wav.part"
        try:
            partial.write_bytes(wav)
            os.replace(partial, target)
        except BaseException:
            with contextlib.suppress(OSError):
                partial.unlink()
            raise
        self._prune()
        return target

    def _prune(self) -> None:
        """Zostawia najnowsze max_files własnych nagrań; pliki o innych nazwach (np. wrzucone ręcznie) nie są ruszane."""
        if self.max_files <= 0:
            return
        try:
            ours = sorted(p for p in self.directory.glob("*.wav") if _OWN_NAME_RE.fullmatch(p.name))
        except OSError:
            return
        for old in ours[: max(0, len(ours) - self.max_files)]:
            try:
                old.unlink()
            except OSError as exc:
                log.warning("could not remove old output %s: %s", old.name, exc)
