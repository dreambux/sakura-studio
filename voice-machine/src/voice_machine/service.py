"""Logika aplikacji bez zależności od MCP: narzędzia serwera są cienkimi wrapperami na te metody."""

from __future__ import annotations

import base64
import binascii
import logging
import threading
import unicodedata
from pathlib import Path
from typing import Any

from . import PROTOCOL_VERSION, SERVER_NAME, __version__
from .config import Limits, Settings
from .engines.base import Engine, EngineState, SynthParams, VoiceRef
from .errors import (
    E_AUDIO_TOO_LONG,
    E_AUDIO_TOO_SHORT,
    E_BAD_REQUEST,
    E_CONSENT_REQUIRED,
    E_ENGINE_FAILED,
    E_NOT_READY,
    E_TEXT_EMPTY,
    E_TEXT_TOO_LONG,
    E_TRANSCRIPT_REQUIRED,
    E_VOICE_BUSY,
    E_VOICE_LIMIT,
    E_VOICE_NOT_FOUND,
    VoiceMachineError,
)
from .jobs import JobManager, is_finite_number
from .normalize_pl import normalize_for_speech
from .outputs import OutputStore
from .textsplit import split_text
from .uploads import Upload, UploadManager
from .voices import (
    MAX_TRANSCRIPT_CHARS,
    PreparedSample,
    VoiceRecord,
    VoiceStore,
    clean_language,
    clean_name,
    clean_transcript,
    is_valid_voice_id,
)
from .wavio import MAX_SAMPLE_RATE, encode_wav_pcm16, parse_wav, reference_flags, sha256_hex

log = logging.getLogger("voice_machine.service")

BUILTIN_PREFIX = "builtin:"
MAX_SEED = 2**31 - 1


class Service:
    def __init__(self, settings: Settings, engine: Engine) -> None:
        self.settings = settings
        self.limits: Limits = settings.limits
        self.engine = engine
        self.voices = VoiceStore(settings.voices_dir)
        self.uploads = UploadManager(self.limits)
        self.outputs = OutputStore(settings.outputs_dir, self.limits.max_output_files) if settings.save_outputs else None
        self.jobs = JobManager(engine, self.outputs, self.limits)
        # Chroni parę "sprawdź, czy głos jest używany + usuń" przed równoległym "znajdź głos + zakolejkuj zadanie".
        self._voice_lock = threading.Lock()
        self.jobs.start()

    def close(self) -> None:
        self.jobs.close()
        self.engine.close()

    def _ensure_loading(self) -> None:
        """Przy --no-preload model ładuje się przy pierwszym użyciu (status, dodawanie głosu, synteza). Po błędzie ładowania
        silnik sam decyduje, czy już można spróbować ponownie (odstęp), więc zwykłe odpytywanie stanu go "naprawia". Idempotentne."""
        if self.engine.info().state in (EngineState.IDLE, EngineState.ERROR):
            self.engine.start_loading()

    @staticmethod
    def _normalized(text: str, language: str) -> str:
        """Normalizacja tekstu do czytania. Gdyby reguła kiedyś rzuciła wyjątek, czytamy tekst bez rozwijania zamiast padać."""
        try:
            return normalize_for_speech(text, language)
        except Exception:  # noqa: BLE001
            log.exception("text normalisation failed; using the text as typed")
            return text

    def _ref_bounds(self) -> tuple[int, float, float]:
        """Obowiązujące granice nagrań wzorcowych: węższe z limitów aplikacji i wymagań silnika."""
        policy = self.engine.info().reference
        lim = self.limits
        return (
            min(lim.max_ref_files, policy.max_files),
            max(lim.min_ref_seconds, policy.min_seconds),
            min(lim.max_ref_seconds, policy.max_seconds),
        )

    # --- odczyt -------------------------------------------------------------
    def status(self) -> dict[str, Any]:
        self._ensure_loading()
        info = self.engine.info()
        lim = self.limits
        max_files, min_s, max_s = self._ref_bounds()
        return {
            "app": {"name": SERVER_NAME, "version": __version__, "protocol": PROTOCOL_VERSION},
            "engine": info.to_public(),
            "limits": {
                "max_text_chars": lim.max_text_chars,
                "min_ref_seconds": min_s,
                "max_ref_seconds": max_s,
                "max_ref_files": max_files,
                "max_voices": lim.max_voices,
                "upload_chunk_bytes": lim.upload_chunk_bytes,
                "audio_chunk_bytes": lim.audio_chunk_bytes,
                "max_queue": lim.max_queue,
                "reference_sample_rate": info.reference_sample_rate,
            },
            "voices": self.voices.count(),
            "storage": {
                "data_dir": str(self.settings.data_dir),
                "outputs_dir": str(self.settings.outputs_dir) if self.outputs is not None else None,
            },
        }

    def list_voices(self) -> dict[str, Any]:
        return {"voices": [record.to_public() for record in self.voices.list()]}

    # --- dodawanie głosu ----------------------------------------------------
    def upload_begin(
        self,
        name: str,
        language: str,
        consent_confirmed: bool,
        file_count: int,
        transcript: str | None = None,
    ) -> dict[str, Any]:
        if consent_confirmed is not True:
            raise VoiceMachineError(
                E_CONSENT_REQUIRED, "Potrzebne jest potwierdzenie, że osoba, której głos dodajesz, wyraziła na to zgodę."
            )
        self._ensure_loading()
        name = clean_name(name)
        language = clean_language(language)
        cleaned_transcript = clean_transcript(transcript)
        if cleaned_transcript is not None:
            # Transkrypcja nagrania wzorcowego ma być zapisem słów, więc liczby i skróty rozwijamy tak samo jak w tekście
            # do czytania. Robimy to już tutaj, żeby za długą transkrypcję odrzucić zanim poleci choćby jeden bajt nagrania.
            cleaned_transcript = self._normalized(cleaned_transcript, language)
            if len(cleaned_transcript) > MAX_TRANSCRIPT_CHARS:
                raise VoiceMachineError(
                    E_BAD_REQUEST,
                    f"Transkrypcja po rozwinięciu liczb i skrótów ma {len(cleaned_transcript)} znaków; limit to {MAX_TRANSCRIPT_CHARS}. Skróć ją.",
                )
        policy = self.engine.info().reference
        max_files, _min_s, _max_s = self._ref_bounds()
        if file_count > max_files:
            raise VoiceMachineError(
                E_BAD_REQUEST,
                f"Ten silnik używa najwyżej {max_files} {'nagrania' if max_files < 5 else 'nagrań'} na jeden głos.",
            )
        if policy.transcript == "required" and cleaned_transcript is None:
            raise VoiceMachineError(
                E_TRANSCRIPT_REQUIRED,
                "Ten model potrzebuje dokładnej transkrypcji nagrania: wpisz słowo w słowo, co mówi osoba na nagraniu.",
            )
        if self.voices.count() >= self.limits.max_voices:
            raise VoiceMachineError(E_VOICE_LIMIT, f"Osiągnięto limit {self.limits.max_voices} głosów.")
        upload_id = self.uploads.begin(name, language, file_count, cleaned_transcript)
        return {
            "upload_id": upload_id,
            "chunk_bytes": self.limits.upload_chunk_bytes,
            "expires_in_s": int(self.limits.upload_ttl_s),
        }

    def upload_chunk(self, upload_id: str, file_index: int, offset: int, data_b64: str) -> dict[str, Any]:
        try:
            data = base64.b64decode(data_b64, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise VoiceMachineError(E_BAD_REQUEST, "Dane kawałka nie są poprawnym base64.") from exc
        received = self.uploads.add_chunk(upload_id, file_index, offset, data)
        return {"received": received}

    def upload_commit(self, upload_id: str) -> dict[str, Any]:
        upload = self.uploads.claim(upload_id)
        keep = False
        try:
            record, warnings = self._store_upload(upload)
        except OSError:
            keep = True  # zawiodła pamięć masowa, a nie nagrania: sesję da się ponowić bez wysyłania wszystkiego od nowa
            raise
        finally:
            self.uploads.release(upload_id, keep=keep)
        return {"voice": record.to_public(), "warnings": sorted(warnings)}

    def _store_upload(self, upload: Upload) -> tuple[VoiceRecord, set[str]]:
        lim = self.limits
        _max_files, min_s, max_s = self._ref_bounds()
        max_frames = int(MAX_SAMPLE_RATE * lim.max_ref_seconds)
        prepared: list[PreparedSample] = []
        warnings: set[str] = set()
        total = 0.0
        for index, buffer in enumerate(upload.buffers):
            if len(buffer) == 0:
                raise VoiceMachineError(E_BAD_REQUEST, f"Plik {index + 1} jest pusty.")
            try:
                wav = parse_wav(bytes(buffer), max_frames=max_frames)
            except VoiceMachineError as exc:
                raise VoiceMachineError(exc.code, f"Plik {index + 1}: {exc.message}") from None
            total += wav.duration_s
            warnings |= reference_flags(wav.samples, wav.sample_rate)
            data = encode_wav_pcm16(wav.samples, wav.sample_rate)
            prepared.append(
                PreparedSample(data=data, sample_rate=wav.sample_rate, frames=wav.frames, sha256=sha256_hex(data))
            )
        if total < min_s:
            raise VoiceMachineError(
                E_AUDIO_TOO_SHORT, f"Nagrania mają razem {total:.1f} s; potrzeba co najmniej {min_s:g} s."
            )
        if total > max_s:
            raise VoiceMachineError(
                E_AUDIO_TOO_LONG, f"Nagrania mają razem {total:.1f} s; maksimum dla tego silnika to {max_s:g} s."
            )
        if total < 6.0:
            warnings.add("short")
        # upload.transcript jest już rozwinięty i sprawdzony w upload_begin.
        record = self.voices.create(
            upload.name, upload.language, prepared, max_voices=lim.max_voices, transcript=upload.transcript
        )
        return record, warnings

    def upload_abort(self, upload_id: str) -> dict[str, Any]:
        return {"aborted": self.uploads.abort(upload_id)}

    def delete_voice(self, voice_id: str) -> dict[str, Any]:
        if not is_valid_voice_id(voice_id):
            raise VoiceMachineError(E_VOICE_NOT_FOUND, "Nie ma takiego głosu.")
        with self._voice_lock:
            if self.jobs.uses_voice(voice_id):
                raise VoiceMachineError(
                    E_VOICE_BUSY, "Ten głos jest teraz używany przez zadanie syntezy. Poczekaj, aż się skończy, albo je anuluj."
                )
            self.voices.delete(voice_id)
        return {"deleted": True, "voice_id": voice_id}

    # --- synteza ------------------------------------------------------------
    def _resolve_voice(self, voice_id: str) -> tuple[VoiceRef, str, str | None]:
        """Zwraca (VoiceRef, etykieta, domyślny język)."""
        if isinstance(voice_id, str) and voice_id.startswith(BUILTIN_PREFIX):
            name = voice_id[len(BUILTIN_PREFIX) :]
            if name not in self.engine.info().builtin_voices:
                raise VoiceMachineError(E_VOICE_NOT_FOUND, "Nie ma takiego głosu wbudowanego.")
            ref = VoiceRef(kind="builtin", voice_id=voice_id, name=name, fingerprint=sha256_hex(voice_id.encode("utf-8")))
            return ref, name, None
        record = self.voices.get(voice_id)
        ref = VoiceRef(
            kind="cloned",
            voice_id=record.id,
            name=record.name,
            fingerprint=record.fingerprint,
            sample_paths=self.voices.sample_paths(record.id),
            transcript=record.transcript,
            language=record.language,
        )
        return ref, record.name, record.language

    def preview_text(self, text: str, language: str, normalize: bool) -> dict[str, Any]:
        """Jak tekst zostanie przeczytany: po normalizacji i podziale na fragmenty. Nie wymaga gotowego silnika."""
        stripped = unicodedata.normalize("NFC", text).strip() if isinstance(text, str) else ""
        if len(stripped) > self.limits.max_text_chars:
            raise VoiceMachineError(
                E_TEXT_TOO_LONG, f"Tekst ma {len(stripped)} znaków; limit to {self.limits.max_text_chars}."
            )
        code = clean_language(language)
        spoken = self._normalized(stripped, code) if normalize else stripped
        try:
            chunks = split_text(spoken, self.engine.max_chunk_chars(code)) if spoken else []
        except (VoiceMachineError, ValueError):
            chunks = []
        return {"spoken_text": spoken, "changed": spoken != stripped, "chunks": chunks[:200]}

    def speak(
        self,
        voice_id: str,
        text: str,
        language: str | None,
        speed: float,
        temperature: float,
        seed: int | None,
        normalize: bool = True,
    ) -> dict[str, Any]:
        self._ensure_loading()
        info = self.engine.info()
        if info.state is not EngineState.READY:
            detail = info.error or {"idle": "nie uruchomiony", "loading": "ładuje się", "error": "błąd"}[info.state.value]
            code = E_ENGINE_FAILED if info.state is EngineState.ERROR else E_NOT_READY
            raise VoiceMachineError(code, f"Silnik nie jest gotowy ({detail}).")
        stripped = unicodedata.normalize("NFC", text).strip() if isinstance(text, str) else ""
        if not stripped:
            raise VoiceMachineError(E_TEXT_EMPTY, "Wpisz tekst do wypowiedzenia.")
        if len(stripped) > self.limits.max_text_chars:
            raise VoiceMachineError(
                E_TEXT_TOO_LONG, f"Tekst ma {len(stripped)} znaków; limit to {self.limits.max_text_chars}."
            )
        if not (is_finite_number(speed) and 0.5 <= speed <= 2.0):
            raise VoiceMachineError(E_BAD_REQUEST, "Tempo musi być liczbą od 0,5 do 2.")
        if not (is_finite_number(temperature) and 0.1 <= temperature <= 1.5):
            raise VoiceMachineError(E_BAD_REQUEST, "Ekspresja musi być liczbą od 0,1 do 1,5.")
        if seed is not None and not (isinstance(seed, int) and not isinstance(seed, bool) and 0 <= seed <= MAX_SEED):
            raise VoiceMachineError(E_BAD_REQUEST, f"Ziarno musi być liczbą całkowitą od 0 do {MAX_SEED}.")
        with self._voice_lock:  # od znalezienia głosu do zakolejkowania zadania nikt go nie usunie
            voice, label, default_language = self._resolve_voice(voice_id)
            chosen = language or default_language
            if not chosen:
                raise VoiceMachineError(E_BAD_REQUEST, "Wybierz język wypowiedzi.")
            chosen = self.engine.validate_language(chosen)
            spoken = self._normalized(stripped, chosen) if normalize else stripped
            params = SynthParams(speed=float(speed), temperature=float(temperature), seed=seed)
            snapshot = self.jobs.submit(voice, label, spoken, chosen, params)
        return {
            "job_id": snapshot["job_id"],
            "chunks_total": snapshot["chunks_total"],
            "queue_position": snapshot["queue_position"],
            "spoken_text": spoken,
            "changed": spoken != stripped,
        }

    def job_status(self, job_id: str) -> dict[str, Any]:
        return self.jobs.snapshot(job_id)

    def job_audio(self, job_id: str, index: int) -> dict[str, Any]:
        return self.jobs.audio_chunk(job_id, index)

    def job_cancel(self, job_id: str) -> dict[str, Any]:
        return self.jobs.cancel(job_id)


def data_dir_writable(path: Path) -> tuple[bool, str]:
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".write-probe"
        probe.write_bytes(b"ok")
        probe.unlink()
        return True, str(path)
    except OSError as exc:
        return False, f"{path} ({exc.strerror or type(exc).__name__})"
