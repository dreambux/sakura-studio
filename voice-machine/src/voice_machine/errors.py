"""Błędy domenowe. Komunikat ma postać "[KOD] opis", żeby strona mogła rozpoznać kod.

Uwaga o transporcie: SDK MCP 2.3.0 dokleja przed komunikatem narzędzia "Error executing tool <nazwa>: ",
więc klient widzi "Error executing tool speak: [E_NOT_READY] opis". Kod w nawiasach kwadratowych zawsze jest w tekście.
"""

from __future__ import annotations

E_NOT_READY = "E_NOT_READY"
E_ENGINE_FAILED = "E_ENGINE_FAILED"
E_LICENSE = "E_LICENSE"
E_BAD_REQUEST = "E_BAD_REQUEST"
E_TEXT_EMPTY = "E_TEXT_EMPTY"
E_TEXT_TOO_LONG = "E_TEXT_TOO_LONG"
E_LANGUAGE = "E_LANGUAGE"
E_VOICE_NOT_FOUND = "E_VOICE_NOT_FOUND"
E_VOICE_LIMIT = "E_VOICE_LIMIT"
E_VOICE_BUSY = "E_VOICE_BUSY"
E_STORAGE = "E_STORAGE"
E_CONSENT_REQUIRED = "E_CONSENT_REQUIRED"
E_TRANSCRIPT_REQUIRED = "E_TRANSCRIPT_REQUIRED"
E_AUDIO_INVALID = "E_AUDIO_INVALID"
E_AUDIO_TOO_SHORT = "E_AUDIO_TOO_SHORT"
E_AUDIO_TOO_LONG = "E_AUDIO_TOO_LONG"
E_UPLOAD_NOT_FOUND = "E_UPLOAD_NOT_FOUND"
E_UPLOAD_LIMIT = "E_UPLOAD_LIMIT"
E_UPLOAD_ORDER = "E_UPLOAD_ORDER"
E_QUEUE_FULL = "E_QUEUE_FULL"
E_JOB_NOT_FOUND = "E_JOB_NOT_FOUND"
E_JOB_NOT_DONE = "E_JOB_NOT_DONE"
E_JOB_FAILED = "E_JOB_FAILED"


class VoiceMachineError(Exception):
    """Przewidziany błąd: trafia do klienta jako wynik narzędzia z isError=true."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"[{code}] {message}")
        self.code = code
        self.message = message
