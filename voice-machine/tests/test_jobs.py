from __future__ import annotations

import base64
import threading
from pathlib import Path

import numpy as np
import pytest

from helpers import wait_until
from voice_machine.config import Limits
from voice_machine.engines.base import AudioClip, EngineInfo, EngineState, SynthParams, VoiceRef
from voice_machine.engines.fake import FakeEngine
from voice_machine.errors import (
    E_BAD_REQUEST,
    E_ENGINE_FAILED,
    E_JOB_FAILED,
    E_JOB_NOT_DONE,
    E_JOB_NOT_FOUND,
    E_QUEUE_FULL,
    E_TEXT_TOO_LONG,
    VoiceMachineError,
)
from voice_machine.jobs import JobManager
from voice_machine.outputs import OutputStore
from voice_machine.wavio import parse_wav

VOICE = VoiceRef(kind="builtin", voice_id="builtin:test", name="test", fingerprint="ab" * 32)
TEXT = "Pierwsze zdanie testowe. Drugie zdanie testowe. Trzecie zdanie testowe."


class StubEngine:
    def __init__(self, gate: threading.Event | None = None, boom: Exception | None = None, chunk_chars: int = 30) -> None:
        self.gate = gate
        self.boom = boom
        self.chunk_chars = chunk_chars
        self.calls: list[tuple[str, int | None]] = []
        self.started = threading.Event()

    def info(self) -> EngineInfo:
        return EngineInfo("stub", "stub", EngineState.READY, "cpu", None, ("pl",), (), 16_000, 16_000)

    def start_loading(self) -> None:
        return None

    def max_chunk_chars(self, language: str) -> int:
        return self.chunk_chars

    def validate_language(self, language: str) -> str:
        return language

    def synthesize(self, text: str, language: str, voice: VoiceRef, params: SynthParams) -> AudioClip:
        self.calls.append((text, params.seed))
        self.started.set()
        if self.gate is not None:
            assert self.gate.wait(10), "gate never released"
        if self.boom is not None:
            raise self.boom
        return AudioClip(np.full(1600, 0.1, dtype=np.float32), 16_000)

    def diagnose(self) -> list[tuple[str, str, bool]]:
        return []

    def close(self) -> None:
        return None


class Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


@pytest.fixture
def make_manager(tmp_path: Path):
    created: list[JobManager] = []

    def factory(engine, limits: Limits | None = None, outputs: OutputStore | None = None, clock=None) -> JobManager:
        kwargs = {"clock": clock} if clock is not None else {}
        manager = JobManager(engine, outputs, limits or Limits(), **kwargs)
        manager.start()
        created.append(manager)
        return manager

    yield factory
    for manager in created:
        manager.close()


def finished(manager: JobManager, job_id: str) -> dict:
    wait_until(lambda: manager.snapshot(job_id)["status"] in ("done", "failed", "cancelled"))
    return manager.snapshot(job_id)


def test_job_completes_and_audio_reassembles(make_manager, tmp_path: Path) -> None:
    outputs = OutputStore(tmp_path / "out")
    limits = Limits(audio_chunk_bytes=1000, gap_ms=100)
    manager = make_manager(StubEngine(), limits, outputs)
    job_id = manager.submit(VOICE, "Kuba Żółć", TEXT, "pl", SynthParams())["job_id"]
    snap = finished(manager, job_id)
    assert snap["status"] == "done"
    assert snap["chunks_done"] == snap["chunks_total"] == 3
    result = snap["result"]
    assert result["audio_chunks"] > 1 and result["sample_rate"] == 16_000
    blob = b""
    for index in range(result["audio_chunks"]):
        part = manager.audio_chunk(job_id, index)
        assert part["count"] == result["audio_chunks"] and part["eof"] == (index == part["count"] - 1)
        blob += base64.b64decode(part["data_b64"])
    assert len(blob) == result["wav_bytes"]
    parsed = parse_wav(blob, max_frames=10**9)
    assert parsed.duration_s == pytest.approx(3 * 0.1 + 2 * 0.1, abs=1e-3)
    saved = Path(result["saved_path"])
    assert saved.read_bytes() == blob
    assert saved.name.endswith(".wav") and "kuba-zolc" in saved.name


def test_cancel_running_job_stops_between_chunks(make_manager) -> None:
    gate = threading.Event()
    engine = StubEngine(gate=gate)
    manager = make_manager(engine)
    job_id = manager.submit(VOICE, "x", TEXT, "pl", SynthParams())["job_id"]
    assert engine.started.wait(5)
    assert manager.cancel(job_id)["status"] == "running"
    gate.set()
    snap = finished(manager, job_id)
    assert snap["status"] == "cancelled"
    assert len(engine.calls) == 1


def test_cancel_queued_job_never_runs(make_manager) -> None:
    gate = threading.Event()
    engine = StubEngine(gate=gate)
    manager = make_manager(engine)
    first = manager.submit(VOICE, "x", TEXT, "pl", SynthParams())["job_id"]
    assert engine.started.wait(5)
    second = manager.submit(VOICE, "x", "Inny tekst do wypowiedzenia.", "pl", SynthParams())
    assert second["queue_position"] == 1
    assert manager.cancel(second["job_id"])["status"] == "cancelled"
    gate.set()
    assert finished(manager, first)["status"] == "done"
    assert all(text != "Inny tekst do wypowiedzenia." for text, _ in engine.calls)


def test_queue_full(make_manager) -> None:
    gate = threading.Event()
    manager = make_manager(StubEngine(gate=gate), Limits(max_queue=2))
    manager.submit(VOICE, "x", TEXT, "pl", SynthParams())
    manager.submit(VOICE, "x", TEXT, "pl", SynthParams())
    with pytest.raises(VoiceMachineError) as exc:
        manager.submit(VOICE, "x", TEXT, "pl", SynthParams())
    assert exc.value.code == E_QUEUE_FULL
    gate.set()


def test_engine_failure_is_reported_and_worker_survives(make_manager, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SVM_FAKE_LOAD_DELAY", "0")
    monkeypatch.setenv("SVM_FAKE_FAIL_ON", "BOOM")
    engine = FakeEngine()
    engine.start_loading()
    wait_until(lambda: engine.info().state is EngineState.READY)
    manager = make_manager(engine)
    bad = finished(manager, manager.submit(VOICE, "x", "To zawiera BOOM w środku.", "pl", SynthParams())["job_id"])
    assert bad["status"] == "failed" and bad["error"]["code"] == E_ENGINE_FAILED
    good = finished(manager, manager.submit(VOICE, "x", "To jest zwykły tekst.", "pl", SynthParams())["job_id"])
    assert good["status"] == "done"
    with pytest.raises(VoiceMachineError) as exc:
        manager.audio_chunk(bad["job_id"], 0)
    assert exc.value.code == E_JOB_FAILED


def test_unexpected_engine_exception_becomes_generic_failure(make_manager) -> None:
    manager = make_manager(StubEngine(boom=RuntimeError("CUDA out of memory")))
    snap = finished(manager, manager.submit(VOICE, "x", "Krótki tekst do syntezy.", "pl", SynthParams())["job_id"])
    assert snap["status"] == "failed"
    assert snap["error"]["code"] == E_ENGINE_FAILED
    assert "RuntimeError" in snap["error"]["message"]


def test_seed_is_offset_per_chunk(make_manager) -> None:
    engine = StubEngine()
    manager = make_manager(engine)
    finished(manager, manager.submit(VOICE, "x", TEXT, "pl", SynthParams(seed=5))["job_id"])
    assert [seed for _, seed in engine.calls] == [5, 6, 7]


def test_unseeded_jobs_pass_no_seed(make_manager) -> None:
    engine = StubEngine()
    manager = make_manager(engine)
    finished(manager, manager.submit(VOICE, "x", TEXT, "pl", SynthParams())["job_id"])
    assert {seed for _, seed in engine.calls} == {None}


def test_finished_jobs_expire_and_are_capped(make_manager) -> None:
    clock = Clock()
    manager = make_manager(StubEngine(), Limits(job_ttl_s=100, max_finished_jobs=2), clock=clock)
    ids = []
    for index in range(3):
        job_id = manager.submit(VOICE, "x", f"Tekst numer {index} do wypowiedzenia.", "pl", SynthParams())["job_id"]
        finished(manager, job_id)
        clock.now += 1
        ids.append(job_id)
    manager.submit(VOICE, "x", "Czwarty tekst do wypowiedzenia.", "pl", SynthParams())
    with pytest.raises(VoiceMachineError) as exc:
        manager.snapshot(ids[0])
    assert exc.value.code == E_JOB_NOT_FOUND
    assert manager.snapshot(ids[2])["status"] == "done"
    clock.now += 1000
    manager.submit(VOICE, "x", "Piąty tekst do wypowiedzenia.", "pl", SynthParams())
    with pytest.raises(VoiceMachineError):
        manager.snapshot(ids[2])


def test_audio_chunk_errors(make_manager) -> None:
    gate = threading.Event()
    manager = make_manager(StubEngine(gate=gate))
    job_id = manager.submit(VOICE, "x", "Krótki tekst do syntezy.", "pl", SynthParams())["job_id"]
    with pytest.raises(VoiceMachineError) as exc:
        manager.audio_chunk(job_id, 0)
    assert exc.value.code == E_JOB_NOT_DONE
    gate.set()
    finished(manager, job_id)
    for bad_index in (-1, 99):
        with pytest.raises(VoiceMachineError) as exc:
            manager.audio_chunk(job_id, bad_index)
        assert exc.value.code == E_BAD_REQUEST
    for bad_id in ("", "j_nope", "../etc", "j_" + "0" * 12):
        with pytest.raises(VoiceMachineError) as exc:
            manager.snapshot(bad_id)
        assert exc.value.code == E_JOB_NOT_FOUND


def test_save_failure_does_not_fail_the_job(make_manager, tmp_path: Path) -> None:
    blocker = tmp_path / "not-a-dir"
    blocker.write_text("x")
    manager = make_manager(StubEngine(), outputs=OutputStore(blocker))
    snap = finished(manager, manager.submit(VOICE, "x", "Krótki tekst do syntezy.", "pl", SynthParams())["job_id"])
    assert snap["status"] == "done"
    assert snap["result"]["saved_path"] is None and snap["result"]["save_error"]


def test_too_many_chunks_is_refused_up_front(make_manager) -> None:
    manager = make_manager(StubEngine(chunk_chars=20), Limits(max_chunks_per_job=3))
    with pytest.raises(VoiceMachineError) as exc:
        manager.submit(VOICE, "x", " ".join(f"Zdanie numer {i} jest tutaj." for i in range(10)), "pl", SynthParams())
    assert exc.value.code == E_TEXT_TOO_LONG


def test_close_returns_promptly_with_work_queued(make_manager) -> None:
    gate = threading.Event()
    manager = make_manager(StubEngine(gate=gate))
    for index in range(3):
        manager.submit(VOICE, "x", f"Tekst numer {index} do wypowiedzenia.", "pl", SynthParams())
    gate.set()
    manager.close()
    assert manager._thread is not None and not manager._thread.is_alive()
