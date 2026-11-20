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


def run_doctor_with_fake_engine(tmp_path: Path, **env_extra: str) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "SVM_FAKE_LOAD_DELAY": "0.1", **env_extra}
    return subprocess.run(
        [sys.executable, "-m", "voice_machine", "doctor", "--engine", "fake", "--data-dir", str(tmp_path / "data"), "--load"],
        capture_output=True, text=True, timeout=60, env=env, cwd=tmp_path,
    )


def test_doctor_runs_end_to_end_with_the_fake_engine(tmp_path: Path) -> None:
    result = run_doctor_with_fake_engine(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "[OK ] Python" in result.stdout and "[OK ] próbna synteza" in result.stdout and "BRAK" not in result.stdout
    # Silnik testowy nie używa transkrypcji, więc doctor sprawdza tylko klonowanie bez niej.
    assert "[OK ] klonowanie (bez transkrypcji)" in result.stdout and "z transkrypcją" not in result.stdout
    for name in ("doctor-smoke.wav", "doctor-smoke-clone.wav"):
        wav = tmp_path / name
        assert wav.is_file() and wav.read_bytes()[:4] == b"RIFF", name


def test_doctor_checks_both_clone_variants_when_the_engine_takes_an_optional_transcript(tmp_path: Path) -> None:
    result = run_doctor_with_fake_engine(tmp_path, SVM_FAKE_REF_TRANSCRIPT="optional")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "[OK ] klonowanie (bez transkrypcji)" in result.stdout and "[OK ] klonowanie (z transkrypcją)" in result.stdout


def test_doctor_checks_only_the_transcript_variant_when_the_engine_requires_it(tmp_path: Path) -> None:
    result = run_doctor_with_fake_engine(tmp_path, SVM_FAKE_REF_TRANSCRIPT="required")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "[OK ] klonowanie (z transkrypcją)" in result.stdout and "bez transkrypcji" not in result.stdout


def test_doctor_fails_and_names_the_step_when_cloning_breaks(tmp_path: Path) -> None:
    # Fraza klonowania zawiera "Sprawdzam"; fraza próbnej syntezy nie, więc głos wbudowany przechodzi, a klonowanie nie.
    result = run_doctor_with_fake_engine(tmp_path, SVM_FAKE_FAIL_ON="Sprawdzam")
    assert result.returncode == 1, result.stdout + result.stderr
    assert "Traceback" not in result.stderr
    assert "[OK ] próbna synteza" in result.stdout and "[BRAK] klonowanie (bez transkrypcji)" in result.stdout
    assert not (tmp_path / "doctor-smoke-clone.wav").exists()


def test_doctor_reports_a_missing_engine_dependency_instead_of_crashing(tmp_path: Path) -> None:
    # Test nie zależy od tego, co jest zainstalowane: podstawiamy "torch", który przy imporcie zgłasza ImportError.
    stub = tmp_path / "stub"
    stub.mkdir()
    (stub / "torch.py").write_text('raise ImportError("PyTorch niedostępny w tym teście")\n', encoding="utf-8")
    env = {**os.environ, "PYTHONPATH": os.pathsep.join(p for p in (str(stub), os.environ.get("PYTHONPATH", "")) if p)}
    result = subprocess.run(
        [sys.executable, "-m", "voice_machine", "doctor", "--engine", "voxcpm", "--data-dir", str(tmp_path / "data")],
        capture_output=True, text=True, timeout=60, cwd=tmp_path, env=env,
    )
    assert "Traceback" not in result.stderr
    assert result.returncode == 1, result.stdout
    assert "[BRAK] PyTorch" in result.stdout
