from __future__ import annotations

from ..config import Settings
from ..errors import E_BAD_REQUEST, VoiceMachineError
from .base import Engine

ENGINE_NAMES = ("voxcpm", "fake")


def create_engine(settings: Settings) -> Engine:
    """Importy są leniwe: ciężkie zależności ładują się dopiero w wątku ładowania wybranego silnika."""
    if settings.engine == "fake":
        from .fake import FakeEngine

        return FakeEngine()
    if settings.engine == "voxcpm":
        from .voxcpm import VoxCpmEngine

        return VoxCpmEngine(settings)
    raise VoiceMachineError(E_BAD_REQUEST, f"Nieznany silnik: {settings.engine}. Dostępne: {', '.join(ENGINE_NAMES)}.")
