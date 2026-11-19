from __future__ import annotations

import pytest

from voice_machine.config import Limits
from voice_machine.errors import (
    E_BAD_REQUEST,
    E_UPLOAD_LIMIT,
    E_UPLOAD_NOT_FOUND,
    E_UPLOAD_ORDER,
    VoiceMachineError,
)
from voice_machine.uploads import UploadManager


class Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def code_of(call) -> str:
    with pytest.raises(VoiceMachineError) as exc:
        call()
    return exc.value.code


def test_chunks_assemble_in_order() -> None:
    manager = UploadManager(Limits(upload_chunk_bytes=10))
    uid = manager.begin("Kuba", "pl", 2)
    assert manager.add_chunk(uid, 0, 0, b"abcde") == 5
    assert manager.add_chunk(uid, 0, 5, b"fgh") == 8
    assert manager.add_chunk(uid, 1, 0, b"xyz") == 3
    upload = manager.take(uid)
    assert [bytes(b) for b in upload.buffers] == [b"abcdefgh", b"xyz"]
    assert code_of(lambda: manager.take(uid)) == E_UPLOAD_NOT_FOUND


def test_retry_of_identical_chunk_is_idempotent_but_different_bytes_are_refused() -> None:
    manager = UploadManager(Limits(upload_chunk_bytes=10))
    uid = manager.begin("Kuba", "pl", 1)
    manager.add_chunk(uid, 0, 0, b"abcde")
    assert manager.add_chunk(uid, 0, 0, b"abcde") == 5
    assert code_of(lambda: manager.add_chunk(uid, 0, 0, b"ZZZZZ")) == E_UPLOAD_ORDER


def test_gaps_and_negative_offsets_are_refused() -> None:
    manager = UploadManager(Limits(upload_chunk_bytes=10))
    uid = manager.begin("Kuba", "pl", 1)
    assert code_of(lambda: manager.add_chunk(uid, 0, 3, b"abc")) == E_UPLOAD_ORDER
    assert code_of(lambda: manager.add_chunk(uid, 0, -1, b"abc")) == E_UPLOAD_ORDER


def test_size_limits() -> None:
    manager = UploadManager(Limits(upload_chunk_bytes=4, max_ref_file_bytes=6))
    uid = manager.begin("Kuba", "pl", 1)
    assert code_of(lambda: manager.add_chunk(uid, 0, 0, b"12345")) == E_UPLOAD_LIMIT
    assert code_of(lambda: manager.add_chunk(uid, 0, 0, b"")) == E_UPLOAD_LIMIT
    manager.add_chunk(uid, 0, 0, b"1234")
    assert code_of(lambda: manager.add_chunk(uid, 0, 4, b"567")) == E_UPLOAD_LIMIT


def test_bad_file_index_and_count() -> None:
    manager = UploadManager(Limits(max_ref_files=2))
    assert code_of(lambda: manager.begin("a", "pl", 0)) == E_BAD_REQUEST
    assert code_of(lambda: manager.begin("a", "pl", 3)) == E_BAD_REQUEST
    uid = manager.begin("a", "pl", 2)
    assert code_of(lambda: manager.add_chunk(uid, 2, 0, b"a")) == E_BAD_REQUEST


def test_sessions_expire_and_are_capped() -> None:
    clock = Clock()
    manager = UploadManager(Limits(upload_ttl_s=60, max_uploads=2), clock=clock)
    first = manager.begin("a", "pl", 1)
    manager.begin("b", "pl", 1)
    assert code_of(lambda: manager.begin("c", "pl", 1)) == E_UPLOAD_LIMIT
    clock.now += 61
    assert code_of(lambda: manager.add_chunk(first, 0, 0, b"x")) == E_UPLOAD_NOT_FOUND
    assert manager.begin("d", "pl", 1)


def test_abort() -> None:
    manager = UploadManager(Limits())
    uid = manager.begin("a", "pl", 1)
    assert manager.abort(uid) is True
    assert manager.abort(uid) is False
