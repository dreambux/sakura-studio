"""Punkt wejścia: `python -m voice_machine` uruchamia serwer MCP na stdio (tak robi aplikacja Claude)."""

from __future__ import annotations

import argparse
import logging
import os
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

from .config import Settings, default_data_dir, env_flag

log = logging.getLogger("voice_machine")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="voice_machine", description="Maszyna Głosów: lokalny silnik jako serwer MCP.")
    parser.add_argument("command", nargs="?", choices=("serve", "doctor"), default="serve")
    parser.add_argument("--engine", choices=("voxcpm", "fake"), help="silnik syntezy (domyślnie voxcpm)")
    parser.add_argument("--data-dir", type=Path, help="katalog na próbki głosów i nagrania")
    parser.add_argument("--device", help="urządzenie obliczeń, np. cuda albo cpu (domyślnie automatycznie)")
    parser.add_argument("--no-preload", action="store_true", help="nie ładuj modelu przy starcie")
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
        preload=not args.no_preload,
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
