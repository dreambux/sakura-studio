"""Poprawki po przeglądzie kodu: błędy dysku, sesje wysyłania, usuwanie głosu w użyciu, retencja nagrań, leniwe ładowanie."""

from __future__ import annotations

import asyncio
import base64
import json
import os
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from helpers import mono_wav, wait_until
from test_service import code_of, finished, strict_service, upload  # noqa: F401 - strict_service jest fixturą
from voice_machine.__main__ import build_parser, non_negative_int, resolve_settings
from voice_machine.config import Limits, Settings
from voice_machine.engines.base import EngineState
from voice_machine.engines.fake import FakeEngine
from voice_machine.errors import (
    E_AUDIO_INVALID,
    E_BAD_REQUEST,
    E_NOT_READY,
    E_UPLOAD_NOT_FOUND,
    E_VOICE_BUSY,
    E_VOICE_NOT_FOUND,
    VoiceMachineError,
)
from voice_machine.outputs import OutputStore
from voice_machine.server import build_server
from voice_machine.service import Service
from voice_machine.voices import replace_with_retry


def start_upload(service: Service, blob: bytes) -> str:
    begin = service.upload_begin("Kuba", "pl", True, 1)
    size = begin["chunk_bytes"]
    for offset in range(0, len(blob), size):
        service.upload_chunk(begin["upload_id"], 0, offset, base64.b64encode(blob[offset : offset + size]).decode("ascii"))
    return begin["upload_id"]


def call_tool(server, name: str, **arguments):
    return asyncio.run(server.call_tool(name, arguments))


# --- leniwe ładowanie (--no-preload) ---------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "action",
    [
        pytest.param(lambda s: s.status(), id="status"),
        pytest.param(lambda s: s.upload_begin("A", "pl", True, 1), id="upload_begin"),
        pytest.param(lambda s: s.speak("builtin:demo-niski", "Tekst.", "pl", 1.0, 0.7, None), id="speak"),
    ],
)
def test_first_use_starts_loading_when_the_model_was_not_preloaded(settings: Settings, monkeypatch, action) -> None:
    monkeypatch.setenv("SVM_FAKE_LOAD_DELAY", "0")
    engine = FakeEngine()
    service = Service(settings, engine)
    try:
        assert engine.info().state is EngineState.IDLE
        try:
            action(service)
        except VoiceMachineError as exc:
            assert exc.code == E_NOT_READY  # speak odmawia, ale ładowanie już ruszyło
        assert engine.info().state in (EngineState.LOADING, EngineState.READY)
        wait_until(lambda: engine.info().state is EngineState.READY)
    finally:
        service.close()


# --- transkrypcja i sesje wysyłania ----------------------------------------------------------------------------------


def test_transcript_too_long_after_expansion_is_refused_before_any_session_is_opened(strict_service: Service) -> None:  # noqa: F811
    text = " ".join(["5 zł"] * 100)  # 499 znaków przed rozwinięciem, ponad 1200 po
    assert len(text) <= 600
    assert code_of(lambda: strict_service.upload_begin("A", "pl", True, 1, text)) == E_BAD_REQUEST
    assert strict_service.uploads._uploads == {}


def test_storage_failure_keeps_the_session_so_the_retry_needs_no_new_upload(ready_service: Service, monkeypatch) -> None:
    uid = start_upload(ready_service, mono_wav(7.0))
    real_create = ready_service.voices.create
    attempts: list[int] = []

    def flaky(*args, **kwargs):
        attempts.append(1)
        if len(attempts) == 1:
            raise PermissionError(13, "Permission denied")
        return real_create(*args, **kwargs)

    monkeypatch.setattr(ready_service.voices, "create", flaky)
    with pytest.raises(PermissionError):
        ready_service.upload_commit(uid)
    assert ready_service.voices.count() == 0
    result = ready_service.upload_commit(uid)
    assert result["voice"]["name"] == "Kuba" and ready_service.voices.count() == 1
    assert code_of(lambda: ready_service.upload_commit(uid)) == E_UPLOAD_NOT_FOUND


def test_unusable_audio_consumes_the_session(ready_service: Service) -> None:
    uid = start_upload(ready_service, b"to nie jest plik WAV")
    assert code_of(lambda: ready_service.upload_commit(uid)) == E_AUDIO_INVALID
    assert code_of(lambda: ready_service.upload_commit(uid)) == E_UPLOAD_NOT_FOUND


def test_parallel_commits_of_one_upload_create_exactly_one_voice(ready_service: Service) -> None:
    uid = start_upload(ready_service, mono_wav(7.0))
    outcomes: list[str] = []

    def attempt() -> None:
        try:
            ready_service.upload_commit(uid)
            outcomes.append("ok")
        except VoiceMachineError as exc:
            outcomes.append(exc.code)

    threads = [threading.Thread(target=attempt) for _ in range(5)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert outcomes.count("ok") == 1 and set(outcomes) <= {"ok", E_UPLOAD_NOT_FOUND}
    assert ready_service.voices.count() == 1


# --- usuwanie głosu, który jest w użyciu -----------------------------------------------------------------------------


def test_voice_used_by_a_job_cannot_be_deleted_and_leaves_no_ghost_directory(settings: Settings, monkeypatch) -> None:
    monkeypatch.setenv("SVM_FAKE_LOAD_DELAY", "0")
    monkeypatch.setenv("SVM_FAKE_SYNTH_DELAY", "0.5")
    engine = FakeEngine()
    service = Service(settings, engine)
    engine.start_loading()
    wait_until(lambda: engine.info().state is EngineState.READY)
    try:
        voice_id = upload(service, [mono_wav(7.0)])["voice"]["id"]
        job_id = service.speak(voice_id, "Pierwsze zdanie. Drugie zdanie.", "pl", 1.0, 0.7, None)["job_id"]
        assert code_of(lambda: service.delete_voice(voice_id)) == E_VOICE_BUSY
        assert service.voices.count() == 1
        assert finished(service, job_id)["status"] == "done"
        assert service.delete_voice(voice_id) == {"deleted": True, "voice_id": voice_id}
        assert code_of(lambda: service.speak(voice_id, "Tekst.", "pl", 1.0, 0.7, None)) == E_VOICE_NOT_FOUND
        assert [p.name for p in service.voices.root.iterdir()] == []  # ani śladu po usuniętym głosie
    finally:
        service.close()


# --- uszkodzone dane głosu -------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "mutate",
    [
        pytest.param(lambda r: r.update(consent="nie-słownik"), id="consent-not-a-dict"),
        pytest.param(lambda r: r["samples"][0].update(sample_rate=float("inf")), id="infinite-sample-rate"),
        pytest.param(lambda r: r.update(name=""), id="empty-name"),
        pytest.param(lambda r: r.update(language="!!"), id="bad-language"),
        pytest.param(lambda r: r.update(transcript="x" * 601), id="transcript-too-long"),
        pytest.param(lambda r: r["samples"][0].update(file="../../poza.wav"), id="path-escape"),
    ],
)
def test_one_damaged_voice_never_hides_the_others(ready_service: Service, mutate) -> None:
    good = upload(ready_service, [mono_wav(7.0)], name="Dobry")["voice"]["id"]
    bad = upload(ready_service, [mono_wav(7.0)], name="Zły")["voice"]["id"]
    path = ready_service.voices.root / bad / "voice.json"
    record = json.loads(path.read_text(encoding="utf-8"))
    mutate(record)
    path.write_text(json.dumps(record), encoding="utf-8")
    assert [v["id"] for v in ready_service.list_voices()["voices"]] == [good]
    assert code_of(lambda: ready_service.voices.get(bad)) == E_VOICE_NOT_FOUND


def test_replace_with_retry_survives_a_short_lock_and_eventually_gives_up(tmp_path: Path, monkeypatch) -> None:
    real_replace = os.replace
    calls = {"n": 0}

    def flaky(src, dst):
        calls["n"] += 1
        if calls["n"] < 3:
            raise PermissionError(13, "plik zajęty")
        return real_replace(src, dst)

    monkeypatch.setattr("voice_machine.voices.os.replace", flaky)
    monkeypatch.setattr("voice_machine.voices.time.sleep", lambda _s: None)
    source = tmp_path / "a"
    source.mkdir()
    replace_with_retry(source, tmp_path / "b")
    assert (tmp_path / "b").is_dir() and calls["n"] == 3

    calls["n"] = 0

    def always_locked(src, dst):
        calls["n"] += 1
        raise PermissionError(13, "plik zajęty")

    monkeypatch.setattr("voice_machine.voices.os.replace", always_locked)
    with pytest.raises(PermissionError):
        replace_with_retry(tmp_path / "b", tmp_path / "c", attempts=4)
    assert calls["n"] == 4


# --- kopie nagrań na dysku -------------------------------------------------------------------------------------------


def test_output_store_keeps_the_newest_own_files_and_never_touches_foreign_ones(tmp_path: Path) -> None:
    out = tmp_path / "out"
    out.mkdir()
    (out / "moj-plik.wav").write_bytes(b"x")
    (out / "notatki.txt").write_text("x")
    store = OutputStore(out, max_files=3)
    start = datetime(2026, 11, 20, 12, 0, 0, tzinfo=timezone.utc)
    for i in range(5):
        store.save(b"RIFF", "Kuba", f"j_{i:012x}", start + timedelta(seconds=i))
    ours = sorted(p.name for p in out.glob("*.wav") if p.name != "moj-plik.wav")
    assert [n[:15] for n in ours] == ["20261120-120002", "20261120-120003", "20261120-120004"]
    assert (out / "moj-plik.wav").exists() and (out / "notatki.txt").exists()


def test_output_store_without_a_limit_keeps_everything(tmp_path: Path) -> None:
    store = OutputStore(tmp_path / "out", max_files=0)
    start = datetime(2026, 11, 20, 12, 0, 0, tzinfo=timezone.utc)
    for i in range(6):
        store.save(b"RIFF", "Kuba", f"j_{i:012x}", start + timedelta(seconds=i))
    assert len(list((tmp_path / "out").glob("*.wav"))) == 6


def test_output_store_removes_partial_files_at_start_and_after_a_failed_save(tmp_path: Path, monkeypatch) -> None:
    out = tmp_path / "out"
    out.mkdir()
    (out / "stary.wav.part").write_bytes(b"x")
    store = OutputStore(out)
    assert list(out.glob("*.part")) == []

    def no_space(_src, _dst):
        raise OSError(28, "No space left on device")

    monkeypatch.setattr("voice_machine.outputs.os.replace", no_space)
    with pytest.raises(OSError):
        store.save(b"RIFF", "Kuba", "j_000000000001", datetime.now(timezone.utc))
    assert list(out.glob("*.part")) == [] and list(out.glob("*.wav")) == []


def test_service_passes_the_output_limit_to_the_store(tmp_path: Path) -> None:
    settings = Settings(data_dir=tmp_path / "data", engine="fake", limits=Limits(max_output_files=2))
    service = Service(settings, FakeEngine())
    try:
        assert service.outputs is not None and service.outputs.max_files == 2
    finally:
        service.close()


def test_max_outputs_setting_is_parsed_safely() -> None:
    assert non_negative_int(None, 300, "X") == 300 and non_negative_int("  ", 300, "X") == 300
    assert non_negative_int("0", 300, "X") == 0 and non_negative_int(" 25 ", 300, "X") == 25
    assert non_negative_int("-1", 300, "X") == 300 and non_negative_int("abc", 300, "X") == 300
    parsed = resolve_settings(build_parser().parse_args([]), {"SVM_MAX_OUTPUTS": "7", "HOME": "/h"})
    assert parsed.limits.max_output_files == 7
    assert resolve_settings(build_parser().parse_args([]), {"HOME": "/h"}).limits.max_output_files == 300


# --- warstwa MCP -----------------------------------------------------------------------------------------------------


def test_storage_errors_reach_the_client_with_a_code(ready_service: Service, monkeypatch) -> None:
    server = build_server(ready_service)

    def locked(_voice_id):
        raise PermissionError(13, "Permission denied")

    monkeypatch.setattr(ready_service.voices, "delete", locked)
    with pytest.raises(ToolError) as exc:
        call_tool(server, "delete_voice", voice_id="v_0123456789ab")
    text = str(exc.value)
    assert "[E_STORAGE]" in text and "Permission denied" in text and "Traceback" not in text


def test_job_audio_carries_the_base64_once_and_stays_well_under_one_mebibyte(settings: Settings, monkeypatch) -> None:
    monkeypatch.setenv("SVM_FAKE_LOAD_DELAY", "0")
    engine = FakeEngine()
    service = Service(settings, engine)
    engine.start_loading()
    wait_until(lambda: engine.info().state is EngineState.READY)
    try:
        server = build_server(service)
        text = " ".join(["Kolejne zdanie do przeczytania na głos."] * 16)
        job_id = service.speak("builtin:demo-niski", text, "pl", 1.0, 0.7, None)["job_id"]
        assert finished(service, job_id)["status"] == "done"
        count = service.job_status(job_id)["result"]["audio_chunks"]
        assert count >= 2
        first = call_tool(server, "job_audio", job_id=job_id, index=0)
        assert first.structured_content["data_b64"] and first.structured_content["count"] == count
        summary = json.loads(first.content[0].text)
        assert "data_b64" not in summary and summary["index"] == 0 and summary["count"] == count
        assert len(first.model_dump_json(by_alias=True)) < 1_000_000
        last = call_tool(server, "job_audio", job_id=job_id, index=count - 1)
        assert last.structured_content["eof"] is True
    finally:
        service.close()


# --- doctor, ustawienia, normalizacja w serwisie ---------------------------------------------------------------------


def test_doctor_marks_warnings_without_failing(capsys) -> None:
    from voice_machine.doctor import _line

    assert _line("karta CUDA", "niedostępna", None) is True
    assert _line("Python", "3.11", True) is True
    assert _line("PyTorch", "brak", False) is False
    out = capsys.readouterr().out
    assert "[UWAGA] karta CUDA" in out and "[OK ] Python" in out and "[BRAK] PyTorch" in out


def test_doctor_survives_a_diagnose_that_raises(tmp_path: Path) -> None:
    import subprocess
    import sys

    stub = tmp_path / "stub"
    stub.mkdir()
    # torch, który przy imporcie rzuca OSError jak zepsuta instalacja na Windows, a nie ImportError
    (stub / "torch.py").write_text('raise OSError("[WinError 126] The specified module could not be found")\n', encoding="utf-8")
    env = {**os.environ, "PYTHONPATH": os.pathsep.join([str(stub), os.environ.get("PYTHONPATH", "")]).rstrip(os.pathsep)}
    result = subprocess.run(
        [sys.executable, "-m", "voice_machine", "doctor", "--engine", "voxcpm", "--data-dir", str(tmp_path / "data")],
        capture_output=True, text=True, timeout=60, env=env, cwd=tmp_path,
    )
    assert result.returncode == 1 and "Traceback" not in result.stderr
    assert "[BRAK] PyTorch" in result.stdout and "Visual C++" in result.stdout


def test_preload_can_be_switched_off_from_the_environment() -> None:
    parse = lambda argv: build_parser().parse_args(argv)  # noqa: E731
    assert resolve_settings(parse([]), {"HOME": "/h"}).preload is True
    assert resolve_settings(parse([]), {"HOME": "/h", "SVM_PRELOAD": "0"}).preload is False
    assert resolve_settings(parse(["--no-preload"]), {"HOME": "/h", "SVM_PRELOAD": "1"}).preload is False


def test_a_crashing_normaliser_falls_back_to_the_typed_text(ready_service: Service, monkeypatch) -> None:
    def boom(_text, _language):
        raise KeyError("nieznany miesiąc")

    monkeypatch.setattr("voice_machine.service.normalize_for_speech", boom)
    preview = ready_service.preview_text("Mam 5 zł.", "pl", True)
    assert preview["spoken_text"] == "Mam 5 zł." and preview["changed"] is False
    job = ready_service.speak("builtin:demo-niski", "Mam 5 zł.", "pl", 1.0, 0.7, None)
    assert job["spoken_text"] == "Mam 5 zł."
