"""FastAPI server: upload a label, manipulate it live, and print over TCP.

The heavy lifting stays in the shared pipeline; this module only adds an HTTP
surface, an in-memory session store for uploaded sources, and env-based printer
configuration so the container can be pointed at a printer without editing files.
"""

from __future__ import annotations

import io
import json
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

from ..config import PrinterConfig, data_dir, load_app_config
from ..image_processor import LABEL_HEIGHT_DOTS, LABEL_WIDTH_DOTS
from ..input_detection import detect_input_type, read_zpl
from ..pdf_renderer import pdf_page_count_from_bytes, render_page_from_bytes
from ..pipeline import normalize_with_profile
from ..printer_tcp import decode_status, format_status, query_status_raw, send_zpl_tcp
from ..profiles import DEFAULT_PROFILE_NAME, get_profile, load_profiles
from ..storage import HistoryStore
from ..zpl_encoder import build_raster_label_zpl

STATIC_DIR = Path(__file__).resolve().parent / "static"
# Longest edge of the source preview served to the browser (full-res is kept for rendering).
SOURCE_PREVIEW_MAX = 900
MAX_SESSIONS = 32


class _Session:
    """An uploaded file. PDFs keep their bytes so any page can be rendered lazily."""

    __slots__ = ("kind", "name", "data", "image", "zpl", "page_count", "_page_cache")

    def __init__(self, kind: str, name: str, data: bytes | None = None,
                 image: Image.Image | None = None, zpl: str | None = None,
                 page_count: int = 1) -> None:
        self.kind = kind
        self.name = name
        self.data = data  # PDF bytes (kind == "pdf")
        self.image = image  # RGB image (kind == "image")
        self.zpl = zpl  # ASCII ZPL (kind == "zpl")
        self.page_count = page_count
        self._page_cache: dict[int, Image.Image] = {}

    def page_image(self, page: int = 0) -> Image.Image:
        if self.kind == "zpl":
            raise HTTPException(status_code=400, detail="Raw ZPL has no preview; print it directly.")
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


class SettingsParams(BaseModel):
    printer_host: str | None = None
    printer_port: int | None = None


class SaveProfileParams(BaseModel):
    name: str
    description: str = ""
    page_type: str = "letter"
    rotate: int = 0
    threshold: int = 128
    crop: str | list[float] | None = None  # None | "auto" | [l, t, r, b]


def _png_bytes(image: Image.Image) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def resolve_printer(base: PrinterConfig) -> PrinterConfig:
    """Overlay ZLG_PRINTER_HOST / ZLG_PRINTER_PORT env vars onto the config."""
    host = os.environ.get("ZLG_PRINTER_HOST") or base.tcp_host
    port = os.environ.get("ZLG_PRINTER_PORT")
    return replace(base, tcp_host=host, tcp_port=int(port) if port else base.tcp_port)


def _settings_path() -> Path:
    return data_dir() / "settings.json"


def load_settings() -> dict:
    path = _settings_path()
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def save_settings(data: dict) -> None:
    path = _settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def env_printer_locked() -> bool:
    return bool(os.environ.get("ZLG_PRINTER_HOST"))


def current_printer() -> PrinterConfig:
    """Resolve the printer at call time: base config < saved settings < env vars.

    Env wins (so a container's ZLG_PRINTER_HOST is authoritative); when unset —
    e.g. a desktop install — the in-app Settings value applies.
    """
    base = load_app_config().printer
    settings = load_settings()
    host = os.environ.get("ZLG_PRINTER_HOST") or settings.get("printer_host") or base.tcp_host
    port = os.environ.get("ZLG_PRINTER_PORT") or settings.get("printer_port") or base.tcp_port
    return replace(base, tcp_host=str(host), tcp_port=int(port))


def create_app() -> FastAPI:
    app = FastAPI(title="Zebra Label Gateway", version="1.0")

    # Optional CORS for cross-origin callers (e.g. an Office add-in hosted
    # elsewhere). Same-origin callers — including the bundled add-in — don't
    # need this. Set ZLG_CORS_ORIGINS to a comma-separated origin list.
    cors = os.environ.get("ZLG_CORS_ORIGINS")
    if cors:
        from fastapi.middleware.cors import CORSMiddleware

        app.add_middleware(
            CORSMiddleware,
            allow_origins=[o.strip() for o in cors.split(",") if o.strip()],
            allow_methods=["*"],
            allow_headers=["*"],
        )

    sessions: OrderedDict[str, _Session] = OrderedDict()
    history = HistoryStore()

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

    @app.post("/api/profiles/save")
    def api_save_profile(spec: SaveProfileParams) -> dict:
        from ..profiles import Profile, save_profile

        name = spec.name.strip()
        if not name:
            raise HTTPException(status_code=400, detail="Profile name is required.")
        crop = tuple(spec.crop) if isinstance(spec.crop, list) else spec.crop
        try:
            profile = Profile(
                name=name,
                description=spec.description,
                page_type=spec.page_type,
                rotate=spec.rotate,
                threshold=spec.threshold,
                crop=crop,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        save_profile(profile)
        return {"ok": True, "name": name}

    @app.get("/api/status")
    def api_status() -> dict:
        printer = current_printer()
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

    @app.get("/api/settings")
    def api_get_settings() -> dict:
        printer = current_printer()
        return {
            "printer_host": printer.tcp_host,
            "printer_port": printer.tcp_port,
            "env_locked": env_printer_locked(),
        }

    @app.post("/api/settings")
    def api_set_settings(spec: SettingsParams) -> dict:
        data = load_settings()
        if spec.printer_host is not None:
            data["printer_host"] = spec.printer_host.strip()
        if spec.printer_port is not None:
            data["printer_port"] = int(spec.printer_port)
        save_settings(data)
        printer = current_printer()
        return {"ok": True, "printer_host": printer.tcp_host, "printer_port": printer.tcp_port}

    @app.post("/api/upload")
    async def api_upload(file: UploadFile) -> dict:
        raw = await file.read()
        name = file.filename or "upload"
        kind = detect_input_type(name)
        source = None
        try:
            if kind == "pdf":
                page_count = pdf_page_count_from_bytes(raw)
                session = _Session("pdf", name, data=raw, page_count=page_count)
                source = session.page_image(0)  # render + cache page 0
            elif kind == "image":
                source = Image.open(io.BytesIO(raw)).convert("RGB")
                session = _Session("image", name, image=source, page_count=1)
            elif kind == "zpl":
                zpl = read_zpl(raw)
                if not zpl.strip():
                    raise HTTPException(status_code=400, detail=f"Empty ZPL file: {name}")
                session = _Session("zpl", name, zpl=zpl)
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

        if kind == "zpl":
            return {
                "id": session_id,
                "kind": kind,
                "name": name,
                "pages": 1,
                "zpl_bytes": len(session.zpl or ""),
                "suggested_profile": DEFAULT_PROFILE_NAME,
            }

        # Rough letter-vs-label heuristic: aspect near 4:6 (0.667) => already a label.
        assert source is not None
        ratio = source.width / source.height
        suggested = DEFAULT_PROFILE_NAME if 0.6 <= ratio <= 0.72 else "generic_letter_embedded"
        return {
            "id": session_id,
            "kind": kind,
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
        session = sessions.get(params.id)
        preview = None
        if session is not None and session.kind == "zpl":
            zpl = session.zpl or ""
        else:
            preview, zpl, session = _render(params)
        printer = current_printer()
        try:
            send_zpl_tcp(zpl, printer.tcp_host, printer.tcp_port)
        except OSError as exc:
            raise HTTPException(status_code=502, detail=f"Print failed: {exc}") from exc
        if preview is not None:
            history.add(session.name, params.profile, params.page, _png_bytes(preview), zpl, printed=True)
        raw = "raw ZPL " if session.kind == "zpl" else ""
        return JSONResponse({
            "ok": True,
            "detail": f"Sent {raw}{len(zpl)} bytes to {printer.tcp_host}:{printer.tcp_port}",
            "zpl_bytes": len(zpl),
        })

    @app.get("/api/history")
    def api_history() -> list[dict]:
        return history.list()

    @app.get("/api/history/{entry_id}/preview")
    def api_history_preview(entry_id: str) -> FileResponse:
        path = history.preview_path(entry_id)
        if path is None:
            raise HTTPException(status_code=404, detail="No such history entry.")
        return FileResponse(path, media_type="image/png")

    @app.post("/api/history/{entry_id}/reprint")
    def api_history_reprint(entry_id: str) -> JSONResponse:
        zpl = history.zpl(entry_id)
        if zpl is None:
            raise HTTPException(status_code=404, detail="No such history entry.")
        printer = current_printer()
        try:
            send_zpl_tcp(zpl, printer.tcp_host, printer.tcp_port)
        except OSError as exc:
            raise HTTPException(status_code=502, detail=f"Reprint failed: {exc}") from exc
        return JSONResponse({"ok": True, "detail": f"Reprinted to {printer.tcp_host}:{printer.tcp_port}"})

    @app.delete("/api/history/{entry_id}")
    def api_history_delete(entry_id: str) -> JSONResponse:
        if not history.delete(entry_id):
            raise HTTPException(status_code=404, detail="No such history entry.")
        return JSONResponse({"ok": True})

    @app.get("/")
    def index() -> FileResponse:
        # Prefer the built Svelte SPA; fall back to the legacy page before a build.
        dist_index = STATIC_DIR / "dist" / "index.html"
        if dist_index.exists():
            return FileResponse(dist_index)
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/sw.js")
    def service_worker() -> FileResponse:
        # Served from root so its scope covers the whole app.
        return FileResponse(
            STATIC_DIR / "pwa" / "sw.js",
            media_type="application/javascript",
            headers={"Service-Worker-Allowed": "/", "Cache-Control": "no-cache"},
        )

    @app.get("/manifest.webmanifest")
    def manifest() -> FileResponse:
        return FileResponse(
            STATIC_DIR / "pwa" / "manifest.webmanifest",
            media_type="application/manifest+json",
        )

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    return app


app = create_app()
