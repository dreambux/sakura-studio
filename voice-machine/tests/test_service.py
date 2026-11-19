from __future__ import annotations

import base64
from pathlib import Path

import numpy as np
import pytest

from helpers import make_wav, mono_wav, sine, speechlike, speechlike_wav, wait_until
from voice_machine.config import Limits, Settings
from voice_machine.engines.fake import FakeEngine
from voice_machine.errors import (
    E_AUDIO_INVALID,
    E_AUDIO_TOO_LONG,
    E_AUDIO_TOO_SHORT,
    E_BAD_REQUEST,
    E_CONSENT_REQUIRED,
    E_LANGUAGE,
    E_NOT_READY,
    E_TEXT_EMPTY,
    E_TEXT_TOO_LONG,
    E_TRANSCRIPT_REQUIRED,
    E_VOICE_NOT_FOUND,
    VoiceMachineError,
)
from voice_machine.service import Service
from voice_machine.wavio import parse_wav


def code_of(call) -> str:
    with pytest.raises(VoiceMachineError) as exc:
        call()
    return exc.value.code


def upload(
    service: Service,
    files: list[bytes],
    name: str = "Kuba",
    language: str = "pl",
    chunk: int | None = None,
    transcript: str | None = None,
) -> dict:
    begin = service.upload_begin(name, language, True, len(files), transcript)
    size = chunk or begin["chunk_bytes"]
    for index, blob in enumerate(files):
        for offset in range(0, len(blob), size):
            part = base64.b64encode(blob[offset : offset + size]).decode("ascii")
            service.upload_chunk(begin["upload_id"], index, offset, part)
    return service.upload_commit(begin["upload_id"])


def finished(service: Service, job_id: str) -> dict:
    wait_until(lambda: service.job_status(job_id)["status"] in ("done", "failed", "cancelled"))
    return service.job_status(job_id)


def fetch_wav(service: Service, job_id: str) -> bytes:
    snap = service.job_status(job_id)
    blob = b""
    for index in range(snap["result"]["audio_chunks"]):
        blob += base64.b64decode(service.job_audio(job_id, index)["data_b64"])
    return blob


def test_status_shape(ready_service: Service) -> None:
    status = ready_service.status()
    assert status["app"]["protocol"] == 1 and status["app"]["name"] == "sakura-voice"
    assert status["engine"]["state"] == "ready" and status["engine"]["builtin_voices"] == ["demo-niski", "demo-wysoki"]
    assert status["limits"]["reference_sample_rate"] == 24_000
    assert status["voices"] == 0
    assert status["storage"]["outputs_dir"].endswith("outputs")


def test_full_clone_flow(ready_service: Service) -> None:
    result = upload(ready_service, [speechlike_wav(4.0), speechlike_wav(3.0, seed=2)], chunk=50_000)
    voice = result["voice"]
    assert voice["kind"] == "cloned" and voice["sample_count"] == 2 and voice["duration_s"] == 7.0
    assert result["warnings"] == []
    assert ready_service.list_voices()["voices"][0]["id"] == voice["id"]
    started = ready_service.speak(voice["id"], "To jest test sklonowanego głosu.", None, 1.0, 0.7, None)
    snap = finished(ready_service, started["job_id"])
    assert snap["status"] == "done" and snap["voice"] == "Kuba" and snap["language"] == "pl"
    wav = parse_wav(fetch_wav(ready_service, started["job_id"]), max_frames=10**9)
    assert wav.duration_s > 0.5


def test_voices_differ_by_fingerprint(ready_service: Service) -> None:
    a = upload(ready_service, [mono_wav(4.0, freq=200.0)], name="A")["voice"]["id"]
    b = upload(ready_service, [mono_wav(4.0, freq=350.0)], name="B")["voice"]["id"]
    text = "Ten sam tekst dla obu głosów."
    wa = fetch_wav(ready_service, finished(ready_service, ready_service.speak(a, text, None, 1.0, 0.7, None)["job_id"])["job_id"])
    wb = fetch_wav(ready_service, finished(ready_service, ready_service.speak(b, text, None, 1.0, 0.7, None)["job_id"])["job_id"])
    assert wa != wb


def test_consent_is_mandatory_and_opens_no_session(ready_service: Service) -> None:
    for value in (False, None, "true", 1):
        assert code_of(lambda v=value: ready_service.upload_begin("Kuba", "pl", v, 1)) == E_CONSENT_REQUIRED
    assert ready_service.uploads._uploads == {}


def test_bad_audio_is_rejected_with_file_number(ready_service: Service) -> None:
    assert code_of(lambda: upload(ready_service, [mono_wav(1.0)])) == E_AUDIO_TOO_SHORT
    with pytest.raises(VoiceMachineError) as exc:
        upload(ready_service, [mono_wav(4.0), b"to nie jest plik wav" * 10])
    assert exc.value.code == E_AUDIO_INVALID and "Plik 2" in exc.value.message
    assert ready_service.voices.count() == 0


def test_too_long_reference_is_rejected(settings: Settings, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SVM_FAKE_LOAD_DELAY", "0")
    limits = Limits(max_ref_seconds=5.0)
    service = Service(Settings(data_dir=settings.data_dir, engine="fake", limits=limits), FakeEngine())
    try:
        assert code_of(lambda: upload(service, [mono_wav(4.0), mono_wav(4.0)])) == E_AUDIO_TOO_LONG
        assert code_of(lambda: upload(service, [mono_wav(8.0)])) == E_AUDIO_TOO_LONG
    finally:
        service.close()


def test_empty_file_and_bad_base64(ready_service: Service) -> None:
    begin = ready_service.upload_begin("Kuba", "pl", True, 1)
    assert code_of(lambda: ready_service.upload_chunk(begin["upload_id"], 0, 0, "@@@not-base64@@@")) == E_BAD_REQUEST
    assert code_of(lambda: ready_service.upload_commit(begin["upload_id"])) == E_BAD_REQUEST


def test_quality_warnings(ready_service: Service) -> None:
    assert upload(ready_service, [speechlike_wav(7.0, amp=0.01, noise=1e-5)], name="Cichy")["warnings"] == ["quiet"]
    loud = make_wav([np.clip(speechlike(7.0, amp=3.0), -1.0, 1.0)])
    assert "clipping" in upload(ready_service, [loud], name="Głośny")["warnings"]
    assert "short" in upload(ready_service, [speechlike_wav(4.0)], name="Krótki")["warnings"]
    hiss = make_wav([(np.random.default_rng(3).standard_normal(24_000 * 7) * 0.1).astype(np.float32)])
    assert "noisy" in upload(ready_service, [hiss], name="Szum")["warnings"]
    mostly_quiet = make_wav([np.concatenate([speechlike(1.0), np.full(24_000 * 7, 1e-5, dtype=np.float32)])])
    flags = upload(ready_service, [mostly_quiet], name="Cisza")["warnings"]
    assert "silence" in flags and "noisy" not in flags


def test_stereo_upload_is_stored_as_mono(ready_service: Service) -> None:
    stereo = make_wav([sine(4.0, 44_100), sine(4.0, 44_100, freq=330.0)], rate=44_100)
    voice_id = upload(ready_service, [stereo])["voice"]["id"]
    stored = ready_service.voices.sample_paths(voice_id)[0].read_bytes()
    parsed = parse_wav(stored, max_frames=10**9)
    assert parsed.channels == 1 and parsed.sample_rate == 44_100


def test_builtin_voice_speaks_and_needs_language(ready_service: Service) -> None:
    assert code_of(lambda: ready_service.speak("builtin:demo-niski", "Tekst.", None, 1.0, 0.7, None)) == E_BAD_REQUEST
    started = ready_service.speak("builtin:demo-niski", "Tekst do wypowiedzenia.", "pl", 1.0, 0.7, 3)
    assert finished(ready_service, started["job_id"])["status"] == "done"
    assert code_of(lambda: ready_service.speak("builtin:nie-ma", "Tekst.", "pl", 1.0, 0.7, None)) == E_VOICE_NOT_FOUND


@pytest.mark.parametrize(
    "kwargs, code",
    [
        ({"text": ""}, E_TEXT_EMPTY),
        ({"text": "   \n "}, E_TEXT_EMPTY),
        ({"text": "x" * 2001}, E_TEXT_TOO_LONG),
        ({"language": "de"}, E_LANGUAGE),
        ({"speed": 0.1}, E_BAD_REQUEST),
        ({"speed": float("nan")}, E_BAD_REQUEST),
        ({"speed": True}, E_BAD_REQUEST),
        ({"temperature": 5.0}, E_BAD_REQUEST),
        ({"seed": -1}, E_BAD_REQUEST),
        ({"seed": 2**31}, E_BAD_REQUEST),
        ({"seed": True}, E_BAD_REQUEST),
        ({"voice_id": "../etc/passwd"}, E_VOICE_NOT_FOUND),
        ({"voice_id": "v_000000000000"}, E_VOICE_NOT_FOUND),
    ],
)
def test_speak_validation(ready_service: Service, kwargs: dict, code: str) -> None:
    args = {"voice_id": "builtin:demo-niski", "text": "Zwykły tekst.", "language": "pl", "speed": 1.0, "temperature": 0.7, "seed": None}
    args.update(kwargs)
    assert code_of(lambda: ready_service.speak(**args)) == code


def test_speak_requires_a_ready_engine(settings: Settings, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SVM_FAKE_LOAD_DELAY", "30")
    engine = FakeEngine()
    service = Service(settings, engine)
    try:
        assert code_of(lambda: service.speak("builtin:demo-niski", "Tekst.", "pl", 1.0, 0.7, None)) == E_NOT_READY
        engine.start_loading()
        assert code_of(lambda: service.speak("builtin:demo-niski", "Tekst.", "pl", 1.0, 0.7, None)) == E_NOT_READY
        assert service.status()["engine"]["state"] == "loading"
    finally:
        service.close()


@pytest.fixture
def strict_service(settings: Settings, monkeypatch: pytest.MonkeyPatch):
    """Silnik z wymagającą polityką nagrań: jedno nagranie 4-10 s i obowiązkowa transkrypcja."""
    monkeypatch.setenv("SVM_FAKE_LOAD_DELAY", "0")
    monkeypatch.setenv("SVM_FAKE_REF_MAX_FILES", "1")
    monkeypatch.setenv("SVM_FAKE_REF_MIN_SECONDS", "4")
    monkeypatch.setenv("SVM_FAKE_REF_MAX_SECONDS", "10")
    monkeypatch.setenv("SVM_FAKE_REF_TRANSCRIPT", "required")
    engine = FakeEngine()
    service = Service(settings, engine)
    engine.start_loading()
    wait_until(lambda: engine.info().state.value == "ready")
    yield service
    service.close()


def test_reference_policy_is_published_and_narrows_the_limits(strict_service: Service) -> None:
    status = strict_service.status()
    assert status["engine"]["reference"] == {
        "max_files": 1, "min_seconds": 4.0, "max_seconds": 10.0, "recommended_seconds": [8.0, 20.0], "transcript": "required", "note": "",
    }
    assert (status["limits"]["max_ref_files"], status["limits"]["min_ref_seconds"], status["limits"]["max_ref_seconds"]) == (1, 4.0, 10.0)


def test_reference_policy_is_enforced(strict_service: Service) -> None:
    assert code_of(lambda: strict_service.upload_begin("A", "pl", True, 2, "tekst")) == E_BAD_REQUEST
    assert code_of(lambda: strict_service.upload_begin("A", "pl", True, 1, None)) == E_TRANSCRIPT_REQUIRED
    assert code_of(lambda: strict_service.upload_begin("A", "pl", True, 1, "  \n ")) == E_TRANSCRIPT_REQUIRED
    assert code_of(lambda: strict_service.upload_begin("A", "pl", True, 1, "x" * 601)) == E_BAD_REQUEST
    assert code_of(lambda: upload(strict_service, [speechlike_wav(3.0)], transcript="Za krótkie nagranie")) == E_AUDIO_TOO_SHORT
    assert code_of(lambda: upload(strict_service, [speechlike_wav(12.0)], transcript="Za długie nagranie")) == E_AUDIO_TOO_LONG
    assert strict_service.voices.count() == 0


def test_transcript_is_normalised_stored_and_reaches_the_engine(strict_service: Service) -> None:
    result = upload(strict_service, [speechlike_wav(8.0)], transcript="  Mam 5 złotych,\n i 12,50 zł.  ")
    voice_id = result["voice"]["id"]
    assert result["voice"]["has_transcript"] is True
    stored = strict_service.voices.get(voice_id)
    assert stored.transcript == "Mam pięć złotych, i dwanaście złotych pięćdziesiąt groszy."
    ref, label, language = strict_service._resolve_voice(voice_id)
    assert ref.transcript == stored.transcript and ref.language == "pl" == language and label == "Kuba"


def test_transcript_is_optional_when_the_engine_does_not_need_it(ready_service: Service) -> None:
    plain = upload(ready_service, [speechlike_wav(8.0)], name="Bez")
    assert plain["voice"]["has_transcript"] is False
    with_text = upload(ready_service, [speechlike_wav(8.0)], name="Z", transcript="Dzień dobry")
    assert with_text["voice"]["has_transcript"] is True


def test_delete_voice(ready_service: Service) -> None:
    voice_id = upload(ready_service, [mono_wav(7.0)])["voice"]["id"]
    assert ready_service.delete_voice(voice_id) == {"deleted": True, "voice_id": voice_id}
    assert code_of(lambda: ready_service.delete_voice(voice_id)) == E_VOICE_NOT_FOUND
    assert code_of(lambda: ready_service.delete_voice("../x")) == E_VOICE_NOT_FOUND
    assert ready_service.list_voices() == {"voices": []}


def test_voice_default_language_is_used_for_clones(ready_service: Service) -> None:
    voice_id = upload(ready_service, [mono_wav(7.0)], language="en")["voice"]["id"]
    job = ready_service.speak(voice_id, "Hello there my friend.", None, 1.0, 0.7, None)
    assert finished(ready_service, job["job_id"])["language"] == "en"


def test_speak_normalizes_polish_and_reports_what_is_read(ready_service: Service) -> None:
    started = ready_service.speak("builtin:demo-niski", "Mam 5 zł o 14:30.", "pl", 1.0, 0.7, None)
    assert started["spoken_text"] == "Mam pięć złotych o czternastej trzydzieści." and started["changed"] is True
    raw = ready_service.speak("builtin:demo-niski", "Mam 5 zł o 14:30.", "pl", 1.0, 0.7, None, normalize=False)
    assert raw["spoken_text"] == "Mam 5 zł o 14:30." and raw["changed"] is False
    english = ready_service.speak("builtin:demo-niski", "I have 5 dollars.", "en", 1.0, 0.7, None)
    assert english["spoken_text"] == "I have 5 dollars." and english["changed"] is False


def test_decomposed_polish_letters_are_composed_before_synthesis(ready_service: Service) -> None:
    decomposed = "Zażółć gęślą jaźń."  # ó, ź i ń jako litera + znak łączący
    composed = "Zażółć gęślą jaźń."
    assert ready_service.preview_text(decomposed, "pl", True)["spoken_text"] == composed
    started = ready_service.speak("builtin:demo-niski", decomposed, "pl", 1.0, 0.7, None)
    assert started["spoken_text"] == composed


def test_preview_text(ready_service: Service) -> None:
    preview = ready_service.preview_text("Jutro o 9:05 zapłacę 12,50 zł.", "pl", True)
    assert preview["spoken_text"] == "Jutro o dziewiątej zero pięć zapłacę dwanaście złotych pięćdziesiąt groszy."
    assert preview["changed"] is True and "".join(preview["chunks"]).replace(" ", "") == preview["spoken_text"].replace(" ", "")
    assert ready_service.preview_text("Bez zmian.", "pl", True)["changed"] is False
    assert ready_service.preview_text("   ", "pl", True)["chunks"] == []
    assert code_of(lambda: ready_service.preview_text("x" * 2001, "pl", True)) == E_TEXT_TOO_LONG
    assert code_of(lambda: ready_service.preview_text("x", "../", True)) == E_BAD_REQUEST


def test_outputs_are_written_to_disk(ready_service: Service) -> None:
    job = ready_service.speak("builtin:demo-wysoki", "Zapisz mnie na dysku.", "pl", 1.0, 0.7, None)
    snap = finished(ready_service, job["job_id"])
    saved = Path(snap["result"]["saved_path"])
    assert saved.is_file() and saved.read_bytes() == fetch_wav(ready_service, job["job_id"])
