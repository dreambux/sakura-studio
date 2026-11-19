from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from voice_machine.__main__ import build_parser, resolve_settings
from voice_machine.config import default_data_dir, env_flag


def settings_for(argv: list[str], env: dict[str, str]):
    return resolve_settings(build_parser().parse_args(argv), env)


def test_default_data_dir_per_platform() -> None:
    assert default_data_dir({"LOCALAPPDATA": "C:\\Users\\Ala\\AppData\\Local", "USERPROFILE": "C:\\Users\\Ala"}, "win32") == Path("C:\\Users\\Ala\\AppData\\Local") / "SakuraVoiceMachine"
    assert default_data_dir({"USERPROFILE": "C:\\Users\\Ala"}, "win32") == Path("C:\\Users\\Ala") / "AppData" / "Local" / "SakuraVoiceMachine"
    assert default_data_dir({"HOME": "/Users/ala"}, "darwin") == Path("/Users/ala/Library/Application Support/SakuraVoiceMachine")
    assert default_data_dir({"HOME": "/home/ala"}, "linux") == Path("/home/ala/.local/share/sakura-voice-machine")
    assert default_data_dir({"HOME": "/home/ala", "XDG_DATA_HOME": "/data"}, "linux") == Path("/data/sakura-voice-machine")


def test_env_flag() -> None:
    assert env_flag(None, True) is True and env_flag("", False) is False
    assert all(env_flag(v, False) for v in ("1", "true", "YES", " on ", "tak"))
    assert not any(env_flag(v, True) for v in ("0", "false", "no", "off", "nie"))


def test_settings_precedence_cli_over_env_over_default() -> None:
    env = {"SVM_ENGINE": "fake", "SVM_DATA_DIR": "/from/env", "SVM_DEVICE": "cpu", "SVM_SAVE_OUTPUTS": "0"}
    from_env = settings_for([], env)
    assert (from_env.engine, str(from_env.data_dir), from_env.device, from_env.save_outputs) == ("fake", "/from/env", "cpu", False)
    from_cli = settings_for(["--engine", "voxcpm", "--data-dir", "/from/cli", "--device", "cuda", "--no-save-outputs", "--no-preload"], env)
    assert (from_cli.engine, str(from_cli.data_dir), from_cli.device, from_cli.save_outputs, from_cli.preload) == ("voxcpm", "/from/cli", "cuda", False, False)
    default = settings_for([], {"HOME": "/home/x"})
    assert default.engine == "voxcpm" and default.save_outputs is True and default.preload is True and default.device is None


def test_unknown_engine_is_rejected_by_the_parser() -> None:
    with pytest.raises(SystemExit):
        build_parser().parse_args(["--engine", "nope"])


def test_doctor_runs_end_to_end_with_the_fake_engine(tmp_path: Path) -> None:
    env = {**os.environ, "SVM_FAKE_LOAD_DELAY": "0.1"}
    result = subprocess.run(
        [sys.executable, "-m", "voice_machine", "doctor", "--engine", "fake", "--data-dir", str(tmp_path / "data"), "--load"],
        capture_output=True, text=True, timeout=60, env=env, cwd=tmp_path,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "[OK ] Python" in result.stdout and "próbna synteza" in result.stdout and "BRAK" not in result.stdout
    smoke = tmp_path / "doctor-smoke.wav"
    assert smoke.is_file() and smoke.read_bytes()[:4] == b"RIFF"


def test_doctor_reports_a_missing_engine_dependency_instead_of_crashing(tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, "-m", "voice_machine", "doctor", "--engine", "voxcpm", "--data-dir", str(tmp_path / "data")],
        capture_output=True, text=True, timeout=60, cwd=tmp_path,
    )
    assert "Traceback" not in result.stderr
    # W środowisku testowym nie ma PyTorcha ani voxcpm: doctor ma to nazwać i zakończyć się kodem 1.
    assert result.returncode == 1, result.stdout
    assert "[BRAK] PyTorch" in result.stdout and "[BRAK] voxcpm" in result.stdout
