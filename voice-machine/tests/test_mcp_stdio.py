"""Prawdziwy serwer jako podproces, prawdziwy klient MCP po stdio: tak łączy się aplikacja Claude."""

from __future__ import annotations

import asyncio
import base64
import sys
from pathlib import Path
from typing import Any

import pytest
from mcp import ClientSession, StdioServerParameters, stdio_client

from helpers import mono_wav
from voice_machine.server import TOOL_NAMES
from voice_machine.wavio import parse_wav

READ_ONLY = {"status", "list_voices", "preview_text", "job_status", "job_audio"}


def params(tmp_path: Path, **env: str) -> StdioServerParameters:
    return StdioServerParameters(
        command=sys.executable,
        args=["-m", "voice_machine", "--engine", "fake", "--data-dir", str(tmp_path / "data")],
        env={"SVM_FAKE_LOAD_DELAY": "0.2", "SVM_FAKE_NOISY_STDOUT": "1", "PYTHONUNBUFFERED": "1", **env},
    )


async def call(session: ClientSession, tool: str, /, **arguments: Any) -> dict[str, Any]:
    result = await session.call_tool(tool, arguments)
    assert not result.is_error, getattr(result.content[0], "text", result.content)
    assert isinstance(result.structured_content, dict)
    return result.structured_content


async def call_error(session: ClientSession, tool: str, /, **arguments: Any) -> str:
    result = await session.call_tool(tool, arguments)
    assert result.is_error
    return result.content[0].text


async def wait_for(predicate_coro, timeout: float = 20.0) -> Any:
    deadline = asyncio.get_running_loop().time() + timeout
    while True:
        value = await predicate_coro()
        if value:
            return value
        if asyncio.get_running_loop().time() > deadline:
            raise AssertionError("timeout")
        await asyncio.sleep(0.1)


def run(coro) -> None:
    asyncio.run(asyncio.wait_for(coro, 90))


def test_protocol_end_to_end(tmp_path: Path) -> None:
    errlog_path = tmp_path / "server-stderr.log"

    async def scenario() -> None:
        with errlog_path.open("w", encoding="utf-8") as errlog:
            async with stdio_client(params(tmp_path), errlog=errlog) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()

                    tools = (await session.list_tools()).tools
                    assert {t.name for t in tools} == set(TOOL_NAMES)
                    by_name = {t.name: t for t in tools}
                    for name, tool in by_name.items():
                        assert bool(tool.annotations.read_only_hint) == (name in READ_ONLY), name
                    assert by_name["delete_voice"].annotations.destructive_hint is True

                    async def ready() -> dict | None:
                        status = await call(session, "status")
                        return status if status["engine"]["state"] == "ready" else None

                    status = await wait_for(ready)
                    assert status["app"]["protocol"] == 1
                    assert status["engine"]["builtin_voices"] == ["demo-niski", "demo-wysoki"]

                    begin = await call(
                        session, "voice_upload_begin", name="Kuba", language="pl", consent_confirmed=True, file_count=1
                    )
                    blob = mono_wav(8.0)
                    step = 100_000
                    assert len(blob) > step
                    for offset in range(0, len(blob), step):
                        piece = base64.b64encode(blob[offset : offset + step]).decode("ascii")
                        reply = await call(
                            session,
                            "voice_upload_chunk",
                            upload_id=begin["upload_id"],
                            file_index=0,
                            offset=offset,
                            data_b64=piece,
                        )
                        assert reply["received"] == min(offset + step, len(blob))
                    committed = await call(session, "voice_upload_commit", upload_id=begin["upload_id"])
                    voice = committed["voice"]
                    assert voice["name"] == "Kuba" and voice["consent"]["confirmed"] is True
                    assert (await call(session, "list_voices"))["voices"][0]["id"] == voice["id"]

                    started = await call(
                        session, "speak", voice_id=voice["id"], text="Dzień dobry, to jest test połączenia.", seed=7
                    )

                    async def done() -> dict | None:
                        snap = await call(session, "job_status", job_id=started["job_id"])
                        assert snap["status"] in ("queued", "running", "done"), snap
                        return snap if snap["status"] == "done" else None

                    snap = await wait_for(done)
                    audio = b""
                    for index in range(snap["result"]["audio_chunks"]):
                        part = await call(session, "job_audio", job_id=started["job_id"], index=index)
                        audio += base64.b64decode(part["data_b64"])
                    parsed = parse_wav(audio, max_frames=10**9)
                    assert parsed.sample_rate == 24_000 and parsed.duration_s > 0.8
                    assert Path(snap["result"]["saved_path"]).read_bytes() == audio

                    assert "[E_TEXT_EMPTY]" in await call_error(session, "speak", voice_id=voice["id"], text="  ")
                    assert "[E_CONSENT_REQUIRED]" in await call_error(
                        session, "voice_upload_begin", name="X", language="pl", consent_confirmed=False, file_count=1
                    )
                    assert "[E_VOICE_NOT_FOUND]" in await call_error(session, "delete_voice", voice_id="../etc")
                    assert (await session.call_tool("job_audio", {"job_id": started["job_id"], "index": "x"})).is_error
                    assert (await call(session, "delete_voice", voice_id=voice["id"]))["deleted"] is True

        stderr = errlog_path.read_text(encoding="utf-8")
        assert "raw fd 1" in stderr, "stdout noise should have been diverted to stderr, not lost or sent on the wire"

    run(scenario())


def test_cancel_over_protocol(tmp_path: Path) -> None:
    async def scenario() -> None:
        env = {"SVM_FAKE_SYNTH_DELAY": "0.4", "SVM_FAKE_NOISY_STDOUT": "0"}
        async with stdio_client(params(tmp_path, **env)) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                async def ready() -> bool:
                    return (await call(session, "status"))["engine"]["state"] == "ready"

                await wait_for(ready)
                text = " ".join(f"To jest zdanie numer {i} do wypowiedzenia." for i in range(6))
                started = await call(session, "speak", voice_id="builtin:demo-niski", text=text, language="pl")
                assert started["chunks_total"] >= 3

                async def progressed() -> bool:
                    return (await call(session, "job_status", job_id=started["job_id"]))["chunks_done"] >= 1

                await wait_for(progressed)
                await call(session, "job_cancel", job_id=started["job_id"])

                async def cancelled() -> dict | None:
                    snap = await call(session, "job_status", job_id=started["job_id"])
                    return snap if snap["status"] == "cancelled" else None

                snap = await wait_for(cancelled)
                assert snap["chunks_done"] < snap["chunks_total"]
                assert "[E_JOB_NOT_DONE]" in await call_error(session, "job_audio", job_id=started["job_id"], index=0)

    run(scenario())


def test_server_survives_garbage_on_stdin_and_exits_on_eof(tmp_path: Path) -> None:
    async def scenario() -> None:
        process = await asyncio.create_subprocess_exec(
            *([sys.executable, "-m", "voice_machine", "--engine", "fake", "--data-dir", str(tmp_path / "data")]),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        assert process.stdin is not None
        process.stdin.write(b"this is not json-rpc\n")
        await process.stdin.drain()
        process.stdin.close()
        stdout, _stderr = await asyncio.wait_for(process.communicate(), 30)
        assert process.returncode == 0
        assert stdout == b"" or all(line.startswith(b"{") for line in stdout.splitlines())

    run(scenario())
