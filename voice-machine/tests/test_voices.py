from __future__ import annotations

import json
from pathlib import Path

import pytest

from voice_machine.errors import E_BAD_REQUEST, E_VOICE_LIMIT, E_VOICE_NOT_FOUND, VoiceMachineError
from voice_machine.voices import (
    CONSENT_STATEMENT_VERSION,
    PreparedSample,
    VoiceStore,
    clean_language,
    clean_name,
    is_valid_voice_id,
)
from voice_machine.wavio import sha256_hex


def sample(seconds: float = 4.0, rate: int = 24_000, tag: bytes = b"a") -> PreparedSample:
    data = b"RIFFfake" + tag * 100
    return PreparedSample(data=data, sample_rate=rate, frames=int(seconds * rate), sha256=sha256_hex(data))


def test_create_list_get_delete(tmp_path: Path) -> None:
    store = VoiceStore(tmp_path)
    record = store.create("Kuba", "pl", [sample(), sample(tag=b"b")], max_voices=5)
    assert is_valid_voice_id(record.id)
    assert store.count() == 1
    assert store.get(record.id).name == "Kuba"
    assert [r.id for r in store.list()] == [record.id]
    paths = store.sample_paths(record.id)
    assert [p.name for p in paths] == ["s0.wav", "s1.wav"]
    assert all(p.is_file() for p in paths)
    public = record.to_public()
    assert public["kind"] == "cloned" and public["sample_count"] == 2 and public["consent"]["confirmed"] is True
    store.delete(record.id)
    assert store.count() == 0
    assert not (tmp_path / record.id).exists()


def test_consent_is_recorded_on_disk(tmp_path: Path) -> None:
    store = VoiceStore(tmp_path)
    record = store.create("Ola", "pl", [sample()], max_voices=5)
    raw = json.loads((tmp_path / record.id / "voice.json").read_text(encoding="utf-8"))
    assert raw["consent"]["confirmed"] is True
    assert raw["consent"]["statement_version"] == CONSENT_STATEMENT_VERSION
    assert "zgodziła się" in raw["consent"]["statement"]
    assert raw["fingerprint"] == record.fingerprint


@pytest.mark.parametrize("bad", ["", "../x", "v_zzzzzzzzzzzz", "v_" + "a" * 11, "v_" + "a" * 12 + "/..", "V_" + "a" * 12, "..", "v_abcdef012345\x00"])
def test_voice_id_validation_blocks_path_tricks(tmp_path: Path, bad: str) -> None:
    store = VoiceStore(tmp_path)
    assert not is_valid_voice_id(bad)
    with pytest.raises(VoiceMachineError) as exc:
        store.get(bad)
    assert exc.value.code == E_VOICE_NOT_FOUND
    with pytest.raises(VoiceMachineError):
        store.delete(bad)


def test_voice_limit(tmp_path: Path) -> None:
    store = VoiceStore(tmp_path)
    store.create("A", "pl", [sample()], max_voices=1)
    with pytest.raises(VoiceMachineError) as exc:
        store.create("B", "pl", [sample()], max_voices=1)
    assert exc.value.code == E_VOICE_LIMIT


def test_failed_create_leaves_nothing_behind(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    store = VoiceStore(tmp_path)
    original = Path.write_bytes
    calls = {"n": 0}

    def flaky(self: Path, data: bytes) -> int:
        calls["n"] += 1
        if calls["n"] == 2:
            raise OSError("disk full")
        return original(self, data)

    monkeypatch.setattr(Path, "write_bytes", flaky)
    with pytest.raises(OSError):
        store.create("Kuba", "pl", [sample(), sample(tag=b"b")], max_voices=5)
    monkeypatch.undo()
    assert store.count() == 0
    assert [p.name for p in tmp_path.iterdir()] == []


def test_corrupt_voice_is_skipped_in_list_and_reported_on_get(tmp_path: Path) -> None:
    store = VoiceStore(tmp_path)
    good = store.create("Dobry", "pl", [sample()], max_voices=5)
    bad = store.create("Zepsuty", "pl", [sample(tag=b"z")], max_voices=5)
    (tmp_path / bad.id / "voice.json").write_text("{not json", encoding="utf-8")
    assert [r.id for r in store.list()] == [good.id]
    with pytest.raises(VoiceMachineError) as exc:
        store.get(bad.id)
    assert exc.value.code == E_VOICE_NOT_FOUND


def test_startup_sweeps_temp_and_trash_dirs(tmp_path: Path) -> None:
    (tmp_path / ".tmp-abc").mkdir()
    (tmp_path / ".trash-def").mkdir()
    (tmp_path / "unrelated").mkdir()
    VoiceStore(tmp_path)
    assert sorted(p.name for p in tmp_path.iterdir()) == ["unrelated"]


def test_transcript_is_stored_cleaned_and_changes_the_fingerprint(tmp_path: Path) -> None:
    store = VoiceStore(tmp_path)
    plain = store.create("A", "pl", [sample()], max_voices=5)
    spoken = store.create("B", "pl", [sample()], max_voices=5, transcript="  Dzień\n dobry  ")
    assert plain.transcript is None and spoken.transcript == "Dzień dobry"
    assert plain.fingerprint != spoken.fingerprint
    reloaded = store.get(spoken.id)
    assert reloaded.transcript == "Dzień dobry" and reloaded.to_public()["has_transcript"] is True
    raw = json.loads((tmp_path / spoken.id / "voice.json").read_text(encoding="utf-8"))
    assert raw["transcript"] == "Dzień dobry"


def test_clean_transcript_rules() -> None:
    from voice_machine.voices import clean_transcript

    assert clean_transcript(None) is None and clean_transcript("   ") is None
    assert clean_transcript("Zażółć") == "Zażółć"
    for bad in ["a\x00b", "a​b", "x" * 601]:
        with pytest.raises(VoiceMachineError) as exc:
            clean_transcript(bad)
        assert exc.value.code == E_BAD_REQUEST


def test_voice_json_without_transcript_field_still_loads(tmp_path: Path) -> None:
    store = VoiceStore(tmp_path)
    record = store.create("Stary", "pl", [sample()], max_voices=5)
    path = tmp_path / record.id / "voice.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    del raw["transcript"]
    path.write_text(json.dumps(raw), encoding="utf-8")
    assert store.get(record.id).transcript is None


def test_clean_name_rules() -> None:
    assert clean_name("  Kuba   Nowak ") == "Kuba Nowak"
    assert clean_name("Zażółć") == "Zażółć"
    for bad in ["", "   ", "a\nb", "x" * 41, "a​b"]:
        with pytest.raises(VoiceMachineError) as exc:
            clean_name(bad)
        assert exc.value.code == E_BAD_REQUEST


def test_clean_language_rules() -> None:
    assert clean_language(" PL ") == "pl"
    assert clean_language("zh-cn") == "zh-cn"
    for bad in ["", "polish", "p", "pl_PL", "../"]:
        with pytest.raises(VoiceMachineError):
            clean_language(bad)
