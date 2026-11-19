"""Kolejka zadań syntezy z jednym wątkiem roboczym (jeden GPU/CPU, jedna synteza naraz)."""

from __future__ import annotations

import base64
import logging
import math
import re
import threading
import time
import uuid
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum
from typing import Any

import numpy as np

from .config import Limits
from .engines.base import Engine, SynthParams, VoiceRef
from .errors import (
    E_BAD_REQUEST,
    E_ENGINE_FAILED,
    E_JOB_FAILED,
    E_JOB_NOT_DONE,
    E_JOB_NOT_FOUND,
    E_QUEUE_FULL,
    E_TEXT_EMPTY,
    E_TEXT_TOO_LONG,
    VoiceMachineError,
)
from .outputs import OutputStore
from .textsplit import split_text
from .wavio import encode_wav_pcm16, slice_count

log = logging.getLogger("voice_machine.jobs")

_JOB_ID_RE = re.compile(r"^j_[0-9a-f]{12}$")


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    CANCELLED = "cancelled"


_ACTIVE = (JobStatus.QUEUED, JobStatus.RUNNING)


@dataclass
class Job:
    id: str
    voice: VoiceRef
    voice_label: str
    language: str
    params: SynthParams
    chunks: list[str]
    created_at: float
    status: JobStatus = JobStatus.QUEUED
    chunks_done: int = 0
    started_at: float | None = None
    finished_at: float | None = None
    error_code: str | None = None
    error_message: str | None = None
    wav: bytes | None = None
    sample_rate: int | None = None
    duration_s: float | None = None
    saved_path: str | None = None
    save_error: str | None = None
    cancel: threading.Event = field(default_factory=threading.Event)


class JobManager:
    def __init__(
        self,
        engine: Engine,
        outputs: OutputStore | None,
        limits: Limits,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._engine = engine
        self._outputs = outputs
        self._limits = limits
        self._clock = clock
        self._cv = threading.Condition()
        self._jobs: dict[str, Job] = {}
        self._queue: deque[Job] = deque()
        self._running: Job | None = None
        self._stop = False
        self._thread: threading.Thread | None = None

    # --- cykl życia ---------------------------------------------------------
    def start(self) -> None:
        with self._cv:
            if self._thread is not None:
                return
            self._thread = threading.Thread(target=self._loop, name="svm-worker", daemon=True)
            self._thread.start()

    def close(self) -> None:
        with self._cv:
            self._stop = True
            for job in self._jobs.values():
                job.cancel.set()
            self._cv.notify_all()
            thread = self._thread
        if thread is not None:
            thread.join(timeout=5.0)

    # --- API ----------------------------------------------------------------
    def submit(self, voice: VoiceRef, voice_label: str, text: str, language: str, params: SynthParams) -> dict[str, Any]:
        chunks = split_text(text, self._engine.max_chunk_chars(language))
        if not chunks:
            raise VoiceMachineError(E_TEXT_EMPTY, "Wpisz tekst do wypowiedzenia.")
        if len(chunks) > self._limits.max_chunks_per_job:
            raise VoiceMachineError(
                E_TEXT_TOO_LONG, f"Tekst dzieli się na {len(chunks)} fragmentów; limit to {self._limits.max_chunks_per_job}."
            )
        with self._cv:
            self._purge_locked()
            if sum(1 for j in self._jobs.values() if j.status in _ACTIVE) >= self._limits.max_queue:
                raise VoiceMachineError(E_QUEUE_FULL, "Kolejka jest pełna. Poczekaj, aż poprzednie nagrania się skończą.")
            job_id = f"j_{uuid.uuid4().hex[:12]}"
            job = Job(
                id=job_id,
                voice=voice,
                voice_label=voice_label,
                language=language,
                params=params,
                chunks=chunks,
                created_at=self._clock(),
            )
            self._jobs[job_id] = job
            self._queue.append(job)
            self._cv.notify()
            return self._snapshot_locked(job)

    def snapshot(self, job_id: str) -> dict[str, Any]:
        with self._cv:
            return self._snapshot_locked(self._get_locked(job_id))

    def cancel(self, job_id: str) -> dict[str, Any]:
        with self._cv:
            job = self._get_locked(job_id)
            if job.status is JobStatus.QUEUED:
                self._finish_locked(job, JobStatus.CANCELLED)
            elif job.status is JobStatus.RUNNING:
                job.cancel.set()
            return self._snapshot_locked(job)

    def audio_chunk(self, job_id: str, index: int) -> dict[str, Any]:
        size = self._limits.audio_chunk_bytes
        with self._cv:
            job = self._get_locked(job_id)
            if job.status is JobStatus.FAILED:
                raise VoiceMachineError(E_JOB_FAILED, job.error_message or "Zadanie zakończyło się błędem.")
            if job.status is not JobStatus.DONE or job.wav is None:
                raise VoiceMachineError(E_JOB_NOT_DONE, "Nagranie nie jest jeszcze gotowe.")
            count = slice_count(len(job.wav), size)
            if not isinstance(index, int) or not 0 <= index < count:
                raise VoiceMachineError(E_BAD_REQUEST, f"Numer kawałka musi być od 0 do {count - 1}.")
            part = job.wav[index * size : (index + 1) * size]
        return {
            "index": index,
            "count": count,
            "eof": index == count - 1,
            "data_b64": base64.b64encode(part).decode("ascii"),
        }

    # --- wnętrze ------------------------------------------------------------
    def _get_locked(self, job_id: str) -> Job:
        job = self._jobs.get(job_id) if isinstance(job_id, str) and _JOB_ID_RE.fullmatch(job_id) else None
        if job is None:
            raise VoiceMachineError(E_JOB_NOT_FOUND, "Nie ma takiego zadania (mogło wygasnąć).")
        return job

    def _snapshot_locked(self, job: Job) -> dict[str, Any]:
        position: int | None = None
        if job.status is JobStatus.QUEUED:
            position = list(self._queue).index(job) + (1 if self._running is not None else 0)
        result = None
        if job.status is JobStatus.DONE and job.wav is not None:
            result = {
                "sample_rate": job.sample_rate,
                "duration_s": round(job.duration_s or 0.0, 2),
                "wav_bytes": len(job.wav),
                "audio_chunks": slice_count(len(job.wav), self._limits.audio_chunk_bytes),
                "saved_path": job.saved_path,
                "save_error": job.save_error,
            }
        error = None
        if job.status is JobStatus.FAILED:
            error = {"code": job.error_code, "message": job.error_message}
        return {
            "job_id": job.id,
            "status": job.status.value,
            "voice": job.voice_label,
            "language": job.language,
            "chunks_done": job.chunks_done,
            "chunks_total": len(job.chunks),
            "queue_position": position,
            "error": error,
            "result": result,
        }

    def _finish_locked(
        self, job: Job, status: JobStatus, code: str | None = None, message: str | None = None
    ) -> None:
        job.status = status
        job.finished_at = self._clock()
        job.error_code = code
        job.error_message = message
        if job in self._queue:
            self._queue.remove(job)
        self._cv.notify_all()

    def _purge_locked(self) -> None:
        now = self._clock()
        finished = [j for j in self._jobs.values() if j.status not in _ACTIVE and j.finished_at is not None]
        for job in finished:
            if now - (job.finished_at or now) > self._limits.job_ttl_s:
                del self._jobs[job.id]
        finished = sorted(
            (j for j in self._jobs.values() if j.status not in _ACTIVE), key=lambda j: j.finished_at or 0.0
        )
        for job in finished[: max(0, len(finished) - self._limits.max_finished_jobs)]:
            del self._jobs[job.id]

    def _loop(self) -> None:
        while True:
            with self._cv:
                while not self._queue and not self._stop:
                    self._cv.wait(timeout=0.5)
                if self._stop:
                    return
                job = self._queue.popleft()
                if job.cancel.is_set():
                    self._finish_locked(job, JobStatus.CANCELLED)
                    continue
                job.status = JobStatus.RUNNING
                job.started_at = self._clock()
                self._running = job
            try:
                self._run(job)
            finally:
                with self._cv:
                    self._running = None
                    self._cv.notify_all()

    def _run(self, job: Job) -> None:
        pieces: list[np.ndarray] = []
        rate: int | None = None
        total_frames = 0
        try:
            for index, chunk in enumerate(job.chunks):
                if job.cancel.is_set():
                    with self._cv:
                        self._finish_locked(job, JobStatus.CANCELLED)
                    return
                params = job.params if job.params.seed is None else replace(job.params, seed=job.params.seed + index)
                clip = self._engine.synthesize(chunk, job.language, job.voice, params)
                samples = np.asarray(clip.samples, dtype=np.float32)
                if samples.ndim != 1 or samples.size == 0 or not np.all(np.isfinite(samples)):
                    raise VoiceMachineError(E_ENGINE_FAILED, "Silnik zwrócił nieprawidłowe audio.")
                if clip.sample_rate <= 0 or (rate is not None and clip.sample_rate != rate):
                    raise VoiceMachineError(E_ENGINE_FAILED, "Silnik zwrócił niespójną częstotliwość próbkowania.")
                rate = clip.sample_rate
                total_frames += samples.size
                if total_frames / rate > self._limits.max_job_seconds:
                    raise VoiceMachineError(E_JOB_FAILED, "Wynik byłby zbyt długi.")
                pieces.append(samples)
                with self._cv:
                    job.chunks_done = index + 1
            if job.cancel.is_set():
                with self._cv:
                    self._finish_locked(job, JobStatus.CANCELLED)
                return
            assert rate is not None
            gap = np.zeros(int(rate * self._limits.gap_ms / 1000), dtype=np.float32)
            joined: list[np.ndarray] = []
            for i, piece in enumerate(pieces):
                if i:
                    joined.append(gap)
                joined.append(piece)
            audio = np.concatenate(joined)
            wav = encode_wav_pcm16(audio, rate)
            saved_path: str | None = None
            save_error: str | None = None
            if self._outputs is not None:
                try:
                    saved_path = str(self._outputs.save(wav, job.voice_label, job.id, datetime.now(timezone.utc)))
                except OSError as exc:
                    log.warning("could not save output copy: %s", exc)
                    save_error = f"Nie udało się zapisać kopii na dysku: {exc.strerror or type(exc).__name__}"
            with self._cv:
                job.wav = wav
                job.sample_rate = rate
                job.duration_s = audio.size / rate
                job.saved_path = saved_path
                job.save_error = save_error
                self._finish_locked(job, JobStatus.DONE)
        except VoiceMachineError as exc:
            with self._cv:
                self._finish_locked(job, JobStatus.FAILED, exc.code, exc.message)
        except Exception as exc:  # noqa: BLE001 - silnik może rzucić cokolwiek (CUDA OOM, błąd modelu)
            log.exception("synthesis failed for job %s", job.id)
            detail = f"{type(exc).__name__}: {str(exc)[:200]}".strip()
            with self._cv:
                self._finish_locked(job, JobStatus.FAILED, E_ENGINE_FAILED, f"Silnik zgłosił błąd ({detail}).")


def is_finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
