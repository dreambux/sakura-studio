"""Serwer MCP: cienkie narzędzia nad Service. Kontrakt (nazwy i parametry) jest używany przez artefakt."""

from __future__ import annotations

import functools
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from typing import Any

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations

from . import SERVER_NAME, __version__
from .errors import VoiceMachineError
from .service import Service

INSTRUCTIONS = (
    "Lokalny silnik głosów Sakura Studio. Błędy mają postać '[KOD] opis'. "
    "Mowa powstaje w zadaniach: speak -> job_status (odpytywanie) -> job_audio (kawałki WAV w base64). "
    "Próbki głosu wysyła się w kawałkach: voice_upload_begin -> voice_upload_chunk* -> voice_upload_commit."
)

TOOL_NAMES = (
    "status",
    "list_voices",
    "preview_text",
    "voice_upload_begin",
    "voice_upload_chunk",
    "voice_upload_commit",
    "voice_upload_abort",
    "delete_voice",
    "speak",
    "job_status",
    "job_audio",
    "job_cancel",
)


def build_server(service: Service, *, preload: bool = False) -> MCPServer:
    @asynccontextmanager
    async def lifespan(_app: MCPServer) -> AsyncIterator[dict[str, Any]]:
        # Ładowanie modelu startuje dopiero tutaj, czyli po tym, jak transport stdio zajął
        # deskryptory: wszystko, co biblioteki wypiszą na stdout w trakcie ładowania, trafia
        # na stderr zamiast zepsuć strumień JSON-RPC.
        if preload:
            service.engine.start_loading()
        yield {}

    server = MCPServer(SERVER_NAME, instructions=INSTRUCTIONS, version=__version__, lifespan=lifespan)

    def tool(*, title: str, read_only: bool = False, destructive: bool = False) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        annotations = ToolAnnotations(
            title=title,
            read_only_hint=read_only,
            destructive_hint=None if read_only else destructive,
            idempotent_hint=read_only,
            open_world_hint=False,
        )

        def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
            @functools.wraps(fn)
            def guarded(*args: Any, **kwargs: Any) -> Any:
                try:
                    return fn(*args, **kwargs)
                except VoiceMachineError as exc:
                    raise ToolError(str(exc)) from None

            server.tool(name=fn.__name__, title=title, annotations=annotations)(guarded)
            return fn

        return decorator

    @tool(title="Stan silnika i limity", read_only=True)
    def status() -> dict[str, Any]:
        """Stan silnika (idle/loading/ready/error), dostępne języki i głosy wbudowane, limity, katalogi danych."""
        return service.status()

    @tool(title="Lista głosów znajomych", read_only=True)
    def list_voices() -> dict[str, Any]:
        """Zapisane głosy sklonowane z próbek (głosy wbudowane są w status().engine.builtin_voices)."""
        return service.list_voices()

    @tool(title="Podgląd czytanego tekstu", read_only=True)
    def preview_text(text: str, language: str = "pl", normalize: bool = True) -> dict[str, Any]:
        """Zwraca tekst po normalizacji (liczby, daty, skróty na słowa) i podział na fragmenty. Nie generuje dźwięku."""
        return service.preview_text(text, language, normalize)

    @tool(title="Rozpocznij dodawanie głosu")
    def voice_upload_begin(
        name: str,
        language: str,
        consent_confirmed: bool,
        file_count: int,
        transcript: str | None = None,
    ) -> dict[str, Any]:
        """Otwiera sesję wysyłania próbek. consent_confirmed musi być true (zgoda osoby, której głos dodajesz).
        transcript: dokładny tekst nagrania wzorcowego (status().engine.reference.transcript mówi, czy model go wymaga)."""
        return service.upload_begin(name, language, consent_confirmed, file_count, transcript)

    @tool(title="Wyślij kawałek próbki")
    def voice_upload_chunk(upload_id: str, file_index: int, offset: int, data_b64: str) -> dict[str, Any]:
        """Dokleja kawałek (base64) do pliku file_index; offset musi równać się dotychczasowej długości pliku."""
        return service.upload_chunk(upload_id, file_index, offset, data_b64)

    @tool(title="Zapisz głos")
    def voice_upload_commit(upload_id: str) -> dict[str, Any]:
        """Waliduje wysłane pliki WAV i zapisuje nowy głos na dysku."""
        return service.upload_commit(upload_id)

    @tool(title="Anuluj wysyłanie")
    def voice_upload_abort(upload_id: str) -> dict[str, Any]:
        """Porzuca sesję wysyłania i usuwa wysłane dane."""
        return service.upload_abort(upload_id)

    @tool(title="Usuń głos", destructive=True)
    def delete_voice(voice_id: str) -> dict[str, Any]:
        """Trwale usuwa głos znajomego i jego próbki z dysku."""
        return service.delete_voice(voice_id)

    @tool(title="Wygeneruj mowę")
    def speak(
        voice_id: str,
        text: str,
        language: str | None = None,
        speed: float = 1.0,
        temperature: float = 0.7,
        seed: int | None = None,
        normalize: bool = True,
    ) -> dict[str, Any]:
        """Kolejkuje syntezę. voice_id: id głosu znajomego albo 'builtin:<nazwa>'. Zwraca job_id i czytany tekst."""
        return service.speak(voice_id, text, language, speed, temperature, seed, normalize)

    @tool(title="Postęp zadania", read_only=True)
    def job_status(job_id: str) -> dict[str, Any]:
        """Status zadania, postęp (chunks_done/chunks_total) i opis wyniku."""
        return service.job_status(job_id)

    @tool(title="Pobierz kawałek nagrania", read_only=True)
    def job_audio(job_id: str, index: int) -> dict[str, Any]:
        """Kawałek pliku WAV (base64) gotowego zadania; count mówi, ile kawałków trzeba pobrać."""
        return service.job_audio(job_id, index)

    @tool(title="Anuluj zadanie")
    def job_cancel(job_id: str) -> dict[str, Any]:
        """Anuluje zadanie w kolejce albo w trakcie syntezy (po bieżącym fragmencie)."""
        return service.job_cancel(job_id)

    return server
