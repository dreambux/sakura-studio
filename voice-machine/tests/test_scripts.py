"""Skrypt instalacyjny i pliki pomocnicze: kontrole, które da się zrobić bez PowerShella."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "setup-windows.ps1"


def test_setup_script_is_utf8_with_bom() -> None:
    # Windows PowerShell 5.1 czyta skrypt bez BOM jako ANSI (cp1250): polskie litery zamieniają się w krzaki,
    # a niektóre kody ("ł", "ń") dają znaki cudzysłowu, które PowerShell traktuje jako ograniczniki napisów.
    raw = SCRIPT.read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf")
    raw.decode("utf-8-sig")


def test_setup_script_here_strings_are_balanced_and_closed_at_column_zero() -> None:
    text = SCRIPT.read_text(encoding="utf-8-sig")
    opened = len(re.findall(r'@"\s*$', text, re.MULTILINE))
    closed = len(re.findall(r'^"@', text, re.MULTILINE))
    assert opened == closed >= 2
    assert not re.search(r'^\s+"@', text, re.MULTILINE)  # wcięte zamknięcie nie jest zamknięciem


def test_every_documented_install_command_survives_the_default_execution_policy() -> None:
    for name in ("README.md", "scripts/setup-windows.ps1", "artifact/maszyna-glosow.html"):
        text = (ROOT / name).read_text(encoding="utf-8-sig")
        for line in text.splitlines():
            if "setup-windows.ps1" in line and re.search(r"\.\\scripts\\setup-windows\.ps1\s+-", line):
                assert "-ExecutionPolicy" in line, f"{name}: {line.strip()}"


def test_installer_products_are_git_ignored() -> None:
    ignored = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    for pattern in ("claude-desktop-snippet.json", "doctor-smoke.wav", "doctor-smoke-clone.wav", "*.wav", ".venv/", "data/", "outputs/", "voices/"):
        assert pattern in ignored, pattern


def test_example_config_and_the_snippet_in_the_script_agree() -> None:
    import json

    example = json.loads((ROOT / "claude_desktop_config.example.json").read_text(encoding="utf-8"))
    entry = example["mcpServers"]["sakura-voice"]
    assert entry["args"] == ["-m", "voice_machine"] and entry["env"]["SVM_ENGINE"] == "voxcpm"
    script = SCRIPT.read_text(encoding="utf-8-sig")
    assert 'args    = @("-m", "voice_machine")' in script and '"sakura-voice"' in script
