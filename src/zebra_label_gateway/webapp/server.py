"""FastAPI server: upload a label, manipulate it live, and print over TCP.

The heavy lifting stays in the shared pipeline; this module only adds an HTTP
surface, an in-memory session store for uploaded sources, and env-based printer
configuration so the container can be pointed at a printer without editing files.
"""

from __future__ import annotations

import io
import os
import uuid
from collections import OrderedDict
from dataclasses import replace
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from PIL import Image
from pydantic import BaseModel

from ..config import PrinterConfig, load_app_config
from ..image_processor import LABEL_HEIGHT_DOTS, LABEL_WIDTH_DOTS
from ..input_detection import detect_input_type
from ..pdf_renderer import pdf_page_count_from_bytes, render_page_from_bytes
from ..pipeline import normalize_with_profile
from ..printer_tcp import decode_status, format_status, query_status_raw, send_zpl_tcp
from ..profiles import DEFAULT_PROFILE_NAME, get_profile, load_profiles
from ..zpl_encoder import build_raster_label_zpl

STATIC_DIR = Path(__file__).resolve().parent / "static"
# Longest edge of the source preview served to the browser (full-res is kept for rendering).
SOURCE_PREVIEW_MAX = 900
MAX_SESSIONS = 32


class _Session:
    """An uploaded file. PDFs keep their bytes so any page can be rendered lazily."""

    __slots__ = ("kind", "name", "data", "image", "page_count", "_page_cache")

    def __init__(self, kind: str, name: str, data: bytes | None = None,
                 image: Image.Image | None = None, page_count: int = 1) -> None:
        self.kind = kind
        self.name = name
        self.data = data  # PDF bytes (kind == "pdf")
        self.image = image  # RGB image (kind == "image")
        self.page_count = page_count
        self._page_cache: dict[int, Image.Image] = {}

    def page_image(self, page: int = 0) -> Image.Image:
        if self.kind == "image":
            return self.image
        if page not in self._page_cache:
            self._page_cache[page] = render_page_from_bytes(self.data, page)
        return self._page_cache[page]


class RenderParams(BaseModel):
    id: str
    page: int = 0
    profile: str = DEFAULT_PROFILE_NAME
    rotate: int | None = None
    threshold: int | None = None
    crop: str | list[float] | None = None  # None | "auto" | [l, t, r, b]
    crop_mode: str = "profile"  # "profile" | "auto" | "manual" | "none"


def _png_bytes(image: Image.Image) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def resolve_printer(base: PrinterConfig) -> PrinterConfig:
    """Overlay ZLG_PRINTER_HOST / ZLG_PRINTER_PORT env vars onto the config."""
    host = os.environ.get("ZLG_PRINTER_HOST") or base.tcp_host
    port = os.environ.get("ZLG_PRINTER_PORT")
    return replace(base, tcp_host=host, tcp_port=int(port) if port else base.tcp_port)


def create_app() -> FastAPI:
    app = FastAPI(title="Zebra Label Gateway", version="1.0")
    sessions: OrderedDict[str, _Session] = OrderedDict()
    printer = resolve_printer(load_app_config().printer)

    def _resolve_profile(params: RenderParams):
        base = get_profile(params.profile)
        crop = base.crop
        if params.crop_mode == "auto":
            crop = "auto"
        elif params.crop_mode == "none":
            crop = None
        elif params.crop_mode == "manual" and isinstance(params.crop, list):
            crop = tuple(params.crop)
        return replace(
            base,
            rotate=base.rotate if params.rotate is None else params.rotate,
            threshold=base.threshold if params.threshold is None else params.threshold,
            crop=crop,
        )

    def _render(params: RenderParams) -> tuple[Image.Image, str, _Session]:
        session = sessions.get(params.id)
        if session is None:
            raise HTTPException(status_code=404, detail="Unknown or expired upload id.")
        profile = _resolve_profile(params)
        source = session.page_image(params.page)
        preview = normalize_with_profile(source, profile)
        zpl = build_raster_label_zpl(preview, LABEL_WIDTH_DOTS, LABEL_HEIGHT_DOTS)
        return preview, zpl, session

    @app.get("/api/profiles")
    def api_profiles() -> list[dict]:
        return [
            {
                "name": name,
                "description": profile.description,
                "rotate": profile.rotate,
                "threshold": profile.threshold,
                "crop": profile.crop,
                "page_type": profile.page_type,
            }
            for name, profile in sorted(load_profiles().items())
        ]

    @app.get("/api/status")
    def api_status() -> dict:
        try:
            raw = query_status_raw(printer.tcp_host, printer.tcp_port, timeout=5.0)
        except OSError as exc:
            return {"ok": False, "detail": f"{type(exc).__name__}: {exc}",
                    "printer": f"{printer.tcp_host}:{printer.tcp_port}"}
        status = decode_status(raw)
        return {
            "ok": bool(status.get("strings")),
            "printer": f"{printer.tcp_host}:{printer.tcp_port}",
            "report": format_status(status),
            "flags": {k: v for k, v in status.items() if k != "strings"},
        }

    @app.post("/api/upload")
    async def api_upload(file: UploadFile) -> dict:
        raw = await file.read()
        name = file.filename or "upload"
        kind = detect_input_type(name)
        try:
            if kind == "pdf":
                page_count = pdf_page_count_from_bytes(raw)
                session = _Session("pdf", name, data=raw, page_count=page_count)
                source = session.page_image(0)  # render + cache page 0
            elif kind == "image":
                source = Image.open(io.BytesIO(raw)).convert("RGB")
                session = _Session("image", name, image=source, page_count=1)
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported file type: {name}")
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=400, detail=f"Could not read {name}: {exc}") from exc

        session_id = uuid.uuid4().hex
        sessions[session_id] = session
        while len(sessions) > MAX_SESSIONS:
            sessions.popitem(last=False)

        # Rough letter-vs-label heuristic: aspect near 4:6 (0.667) => already a label.
        ratio = source.width / source.height
        suggested = DEFAULT_PROFILE_NAME if 0.6 <= ratio <= 0.72 else "generic_letter_embedded"
        return {
            "id": session_id,
            "name": name,
            "width": source.width,
            "height": source.height,
            "pages": session.page_count,
            "source_url": f"/api/source/{session_id}",
            "suggested_profile": suggested,
        }

    @app.get("/api/source/{session_id}")
    def api_source(session_id: str, page: int = 0) -> Response:
        session = sessions.get(session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Unknown upload id.")
        preview = session.page_image(page).copy()
        preview.thumbnail((SOURCE_PREVIEW_MAX, SOURCE_PREVIEW_MAX))
        return Response(content=_png_bytes(preview), media_type="image/png")

    @app.post("/api/render")
    def api_render(params: RenderParams) -> Response:
        preview, zpl, _session = _render(params)
        return Response(
            content=_png_bytes(preview),
            media_type="image/png",
            headers={"X-Zpl-Bytes": str(len(zpl)), "Cache-Control": "no-store"},
        )

    @app.post("/api/print")
    def api_print(params: RenderParams) -> JSONResponse:
        preview, zpl, session = _render(params)
        try:
            send_zpl_tcp(zpl, printer.tcp_host, printer.tcp_port)
        except OSError as exc:
            raise HTTPException(status_code=502, detail=f"Print failed: {exc}") from exc
        return JSONResponse({
            "ok": True,
            "detail": f"Sent {len(zpl)} bytes to {printer.tcp_host}:{printer.tcp_port}",
            "zpl_bytes": len(zpl),
        })

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    return app


app = create_app()
