"""Ustawienia i limity. Wszystkie limity w jednym miejscu, żeby status() mógł je pokazać stronie."""

from __future__ import annotations

import os
import sys
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Limits:
    max_text_chars: int = 2000
    max_queue: int = 4
    max_voices: int = 50
    max_ref_files: int = 8
    min_ref_seconds: float = 3.0
    max_ref_seconds: float = 120.0
    max_ref_file_bytes: int = 32 * 1024 * 1024
    # Wejście narzędzia MCP w artefakcie ma limit 1 MiB (JSON z base64), stąd ~600 kB surowych bajtów.
    upload_chunk_bytes: int = 600_000
    # Wynik job_audio ma ten sam rząd wielkości (nie wiadomo, czy host ogranicza wyniki); 450 kB to 600 tys. znaków base64.
    audio_chunk_bytes: int = 450_000
    max_output_files: int = 300  # tyle najnowszych kopii WAV zostaje w outputs\ (0 = bez limitu)
    max_chunks_per_job: int = 90  # 2000 znaków krótkich zdań (po ok. 24 znaki) daje ok. 83 fragmenty
    max_job_seconds: float = 900.0
    max_finished_jobs: int = 8
    job_ttl_s: float = 1800.0
    upload_ttl_s: float = 900.0
    max_uploads: int = 3
    gap_ms: int = 180


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    engine: str = "voxcpm"
    device: str | None = None
    save_outputs: bool = True
    preload: bool = True
    limits: Limits = field(default_factory=Limits)

    @property
    def voices_dir(self) -> Path:
        return self.data_dir / "voices"

    @property
    def outputs_dir(self) -> Path:
        return self.data_dir / "outputs"


def default_data_dir(env: Mapping[str, str] | None = None, platform: str | None = None) -> Path:
    env = os.environ if env is None else env
    platform = sys.platform if platform is None else platform
    home = Path(env.get("USERPROFILE") or env.get("HOME") or Path.home())
    if platform.startswith("win"):
        base = env.get("LOCALAPPDATA")
        root = Path(base) if base else home / "AppData" / "Local"
        return root / "SakuraVoiceMachine"
    if platform == "darwin":
        return home / "Library" / "Application Support" / "SakuraVoiceMachine"
    xdg = env.get("XDG_DATA_HOME")
    return (Path(xdg) if xdg else home / ".local" / "share") / "sakura-voice-machine"


def env_flag(value: str | None, default: bool) -> bool:
    if value is None or not value.strip():
        return default
    return value.strip().lower() in {"1", "true", "yes", "on", "tak"}
