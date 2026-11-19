from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from helpers import wait_until  # noqa: E402
from voice_machine.config import Limits, Settings  # noqa: E402
from voice_machine.engines.base import EngineState  # noqa: E402
from voice_machine.engines.fake import FakeEngine  # noqa: E402
from voice_machine.service import Service  # noqa: E402


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(data_dir=tmp_path / "data", engine="fake", limits=Limits())


@pytest.fixture
def ready_service(settings: Settings, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("SVM_FAKE_LOAD_DELAY", "0")
    engine = FakeEngine()
    service = Service(settings, engine)
    engine.start_loading()
    wait_until(lambda: engine.info().state is EngineState.READY)
    yield service
    service.close()
