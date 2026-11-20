"""Punkt wejścia: `python -m voice_machine` uruchamia serwer MCP na stdio (tak robi aplikacja Claude)."""

from __future__ import annotations

import argparse
import logging
import os
import sys
from collections.abc import Mapping, Sequence
from dataclasses import replace
from pathlib import Path

from .config import Limits, Settings, default_data_dir, env_flag

log = logging.getLogger("voice_machine")


def non_negative_int(raw: str | None, default: int, name: str) -> int:
    """Liczba całkowita >= 0 ze zmiennej środowiskowej; zła wartość daje domyślną i ostrzeżenie na stderr."""
    if raw is None or not raw.strip():
        return default
    try:
        value = int(raw.strip())
    except ValueError:
        value = -1
    if value < 0:
        log.warning("%s=%r nie jest liczbą całkowitą >= 0; używam %d", name, raw, default)
        return default
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="voice_machine", description="Maszyna Głosów: lokalny silnik jako serwer MCP.")
    parser.add_argument("command", nargs="?", choices=("serve", "doctor"), default="serve")
    parser.add_argument("--engine", choices=("voxcpm", "fake"), help="silnik syntezy (domyślnie voxcpm)")
    parser.add_argument("--data-dir", type=Path, help="katalog na próbki głosów i nagrania")
    parser.add_argument("--device", help="urządzenie obliczeń, np. cuda albo cpu (domyślnie automatycznie)")
    parser.add_argument(
        "--no-preload", action="store_true", help="nie ładuj modelu przy starcie (załaduje się przy pierwszym użyciu)"
    )
    parser.add_argument("--no-save-outputs", action="store_true", help="nie zapisuj kopii nagrań na dysku")
    parser.add_argument("--load", action="store_true", help="doctor: załaduj model i zrób próbną syntezę")
    return parser


def resolve_settings(args: argparse.Namespace, env: Mapping[str, str]) -> Settings:
    data_dir = args.data_dir or (Path(env["SVM_DATA_DIR"]) if env.get("SVM_DATA_DIR") else default_data_dir(env))
    return Settings(
        data_dir=data_dir,
        engine=args.engine or env.get("SVM_ENGINE") or "voxcpm",
        device=args.device or env.get("SVM_DEVICE") or None,
        save_outputs=False if args.no_save_outputs else env_flag(env.get("SVM_SAVE_OUTPUTS"), True),
        preload=not args.no_preload and env_flag(env.get("SVM_PRELOAD"), True),
        limits=replace(
            Limits(), max_output_files=non_negative_int(env.get("SVM_MAX_OUTPUTS"), Limits().max_output_files, "SVM_MAX_OUTPUTS")
        ),
    )


def serve(settings: Settings) -> int:
    from .engines import create_engine
    from .server import build_server
    from .service import Service

    engine = create_engine(settings)
    service = Service(settings, engine)
    server = build_server(service, preload=settings.preload)
    log.info("sakura-voice ready: engine=%s data_dir=%s", settings.engine, settings.data_dir)
    try:
        server.run("stdio")
    finally:
        service.close()
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    # Logi wyłącznie na stderr: stdout należy do protokołu MCP.
    logging.basicConfig(
        stream=sys.stderr, level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    settings = resolve_settings(args, os.environ)
    if args.command == "doctor":
        for stream in (sys.stdout, sys.stderr):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
            except (AttributeError, ValueError):
                pass
        from . import doctor

        return doctor.run(settings, load=args.load)
    try:
        return serve(settings)
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
