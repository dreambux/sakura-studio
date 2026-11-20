"""Sesje wysyłania próbek w kawałkach (wejście narzędzia MCP w artefakcie ma limit 1 MiB)."""

from __future__ import annotations

import threading
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field

from .config import Limits
from .errors import (
    E_BAD_REQUEST,
    E_UPLOAD_LIMIT,
    E_UPLOAD_NOT_FOUND,
    E_UPLOAD_ORDER,
    VoiceMachineError,
)


@dataclass
class Upload:
    id: str
    name: str
    language: str
    buffers: list[bytearray]
    touched: float = field(default=0.0)
    transcript: str | None = None
    claimed: bool = False  # true, gdy trwa zapis głosu (commit): w tym czasie sesja jest zamrożona


class UploadManager:
    def __init__(self, limits: Limits, clock: Callable[[], float] = time.monotonic) -> None:
        self._limits = limits
        self._clock = clock
        self._lock = threading.Lock()
        self._uploads: dict[str, Upload] = {}

    def _sweep_locked(self) -> None:
        now = self._clock()
        for key in [k for k, u in self._uploads.items() if now - u.touched > self._limits.upload_ttl_s]:
            del self._uploads[key]

    def begin(self, name: str, language: str, file_count: int, transcript: str | None = None) -> str:
        if not 1 <= file_count <= self._limits.max_ref_files:
            raise VoiceMachineError(E_BAD_REQUEST, f"Liczba plików musi być od 1 do {self._limits.max_ref_files}.")
        with self._lock:
            self._sweep_locked()
            if len(self._uploads) >= self._limits.max_uploads:
                raise VoiceMachineError(E_UPLOAD_LIMIT, "Za dużo równoczesnych wysyłek. Poczekaj chwilę i spróbuj ponownie.")
            upload_id = f"u_{uuid.uuid4().hex[:16]}"
            self._uploads[upload_id] = Upload(
                id=upload_id,
                name=name,
                language=language,
                buffers=[bytearray() for _ in range(file_count)],
                touched=self._clock(),
                transcript=transcript,
            )
            return upload_id

    def add_chunk(self, upload_id: str, file_index: int, offset: int, data: bytes) -> int:
        if len(data) == 0 or len(data) > self._limits.upload_chunk_bytes:
            raise VoiceMachineError(E_UPLOAD_LIMIT, f"Kawałek musi mieć od 1 do {self._limits.upload_chunk_bytes} bajtów.")
        with self._lock:
            self._sweep_locked()
            upload = self._uploads.get(upload_id)
            if upload is None:
                raise VoiceMachineError(E_UPLOAD_NOT_FOUND, "Sesja wysyłania wygasła lub nie istnieje.")
            if upload.claimed:
                raise VoiceMachineError(E_BAD_REQUEST, "Ta wysyłka jest właśnie zapisywana i nie przyjmuje już kawałków.")
            if not 0 <= file_index < len(upload.buffers):
                raise VoiceMachineError(E_BAD_REQUEST, "Nieprawidłowy numer pliku.")
            buffer = upload.buffers[file_index]
            if offset < 0:
                raise VoiceMachineError(E_UPLOAD_ORDER, "Nieprawidłowe przesunięcie.")
            if offset + len(data) <= len(buffer):
                # Ponowienie kawałka po utraconej odpowiedzi: potwierdzamy tylko identyczne bajty.
                if bytes(buffer[offset : offset + len(data)]) == data:
                    upload.touched = self._clock()
                    return len(buffer)
                raise VoiceMachineError(E_UPLOAD_ORDER, "Kawałek różni się od już zapisanego.")
            if offset != len(buffer):
                raise VoiceMachineError(E_UPLOAD_ORDER, f"Oczekiwano przesunięcia {len(buffer)}, otrzymano {offset}.")
            if len(buffer) + len(data) > self._limits.max_ref_file_bytes:
                raise VoiceMachineError(E_UPLOAD_LIMIT, "Plik jest za duży.")
            buffer.extend(data)
            upload.touched = self._clock()
            return len(buffer)

    def claim(self, upload_id: str) -> Upload:
        """Zajmuje sesję do zapisu głosu. Druga próba w tym samym czasie dostaje błąd, więc z jednej wysyłki nie powstaną dwa głosy."""
        with self._lock:
            self._sweep_locked()
            upload = self._uploads.get(upload_id)
            if upload is None or upload.claimed:
                raise VoiceMachineError(
                    E_UPLOAD_NOT_FOUND, "Sesja wysyłania wygasła, nie istnieje albo jest właśnie zapisywana."
                )
            upload.claimed = True
            return upload

    def release(self, upload_id: str, *, keep: bool) -> None:
        """Kończy zapis. keep=False usuwa sesję (sukces albo dane, które i tak się nie nadają); keep=True zostawia ją
        do ponowienia, bo zawiodła tylko pamięć masowa, a nie same nagrania."""
        with self._lock:
            if not keep:
                self._uploads.pop(upload_id, None)
                return
            upload = self._uploads.get(upload_id)
            if upload is not None:
                upload.claimed = False
                upload.touched = self._clock()

    def abort(self, upload_id: str) -> bool:
        with self._lock:
            return self._uploads.pop(upload_id, None) is not None
