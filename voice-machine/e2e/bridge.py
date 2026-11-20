"""Most testowy e2e: HTTP -> prawdziwy serwer MCP po stdio (silnik testowy). Tylko do testów strony.

Serwuje też stronę artefaktu w osłonce przypominającej tę z publikacji (szkielet + CSP) i atrapę
środowiska `window.claude`, która przekazuje callTool do tego mostu.
"""

from __future__ import annotations

import argparse
import contextlib
import os
import sys
from collections.abc import AsyncIterator
from pathlib import Path

import uvicorn
from mcp import ClientSession, StdioServerParameters, stdio_client
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, PlainTextResponse
from starlette.routing import Route

HERE = Path(__file__).resolve().parent
ARTIFACT = HERE.parent / "artifact" / "maszyna-glosow.html"
MOCK = HERE / "claude-mock.js"

SKELETON = (
    '<!doctype html><html><head><meta charset="utf-8">'
    '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
    "<style>:root{color-scheme:light;padding:env(safe-area-inset-top,0px) 0 env(safe-area-inset-bottom,0px)}"
    "body{margin:0;font:14px system-ui,sans-serif}img{max-width:100%}</style>"
    '<script src="/mock.js"></script></head><body>\n{content}\n</body></html>'
)

# Przybliżenie CSP artefaktu: skrypty i style inline oraz Google Fonts; fetch tylko do własnego źródła (most testowy).
CSP = (
    "default-src 'none'; script-src 'unsafe-inline' 'self' https://cdnjs.cloudflare.com; "
    "style-src 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; "
    "img-src data: blob:; media-src data: blob:; connect-src 'self'; worker-src blob:"
)


def create_app(data_dir: Path) -> Starlette:
    passthrough = {k: v for k, v in os.environ.items() if k.startswith("SVM_")}
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "voice_machine", "--engine", "fake", "--data-dir", str(data_dir)],
        env={"PYTHONUNBUFFERED": "1", **passthrough},
    )

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                app.state.session = session
                yield

    async def health(_: Request) -> PlainTextResponse:
        return PlainTextResponse("ok")

    async def tools(request: Request) -> JSONResponse:
        listed = await request.app.state.session.list_tools()
        return JSONResponse(
            {
                "tools": [
                    {
                        "name": t.name,
                        "description": t.description or "",
                        "annotations": t.annotations.model_dump(by_alias=True, exclude_none=True) if t.annotations else {},
                    }
                    for t in listed.tools
                ]
            }
        )

    async def call(request: Request) -> JSONResponse:
        body = await request.json()
        result = await request.app.state.session.call_tool(body["tool"], body.get("input") or {})
        return JSONResponse(result.model_dump(by_alias=True, exclude_none=True, mode="json"))

    async def page(_: Request) -> HTMLResponse:
        html = SKELETON.replace("{content}", ARTIFACT.read_text(encoding="utf-8"))
        return HTMLResponse(html, headers={"Content-Security-Policy": CSP})

    async def mock_js(_: Request) -> PlainTextResponse:
        return PlainTextResponse(MOCK.read_text(encoding="utf-8"), media_type="text/javascript")

    return Starlette(
        routes=[Route("/health", health), Route("/tools", tools), Route("/call", call, methods=["POST"]), Route("/page", page), Route("/mock.js", mock_js)],
        lifespan=lifespan,
        middleware=[Middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])],
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--data-dir", type=Path, required=True)
    args = parser.parse_args()
    uvicorn.run(create_app(args.data_dir), host="127.0.0.1", port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
