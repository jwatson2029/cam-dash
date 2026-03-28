"""
FastAPI web dashboard for LaViewNVR.

Provides:
  - Live MJPEG streams (/video_feed/{camera_id})
  - Camera status grid (/)
  - Recording browser (/recordings)
  - Motion event gallery (/motion)
  - REST API for camera control (/api/*)
  - HTTP Basic Auth protection
"""
from __future__ import annotations

import asyncio
import secrets
from pathlib import Path
from typing import Optional, AsyncGenerator

import cv2
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.status import HTTP_401_UNAUTHORIZED

from config.settings import Settings
from core.database import Database

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

# Will be populated by create_app()
_camera_manager = None
_recorder = None
_motion_manager = None
_settings: Optional[Settings] = None
_db: Optional[Database] = None

security = HTTPBasic()

TEMPLATES_DIR = Path(__file__).parent / "templates"


def create_app(settings: Settings, db: Database,
               camera_manager, recorder, motion_manager) -> FastAPI:
    """Factory function that wires up the FastAPI app."""
    global _camera_manager, _recorder, _motion_manager, _settings, _db
    _camera_manager = camera_manager
    _recorder = recorder
    _motion_manager = motion_manager
    _settings = settings
    _db = db

    app = FastAPI(title="LaViewNVR", version="1.0.0")
    templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

    # Mount static files for recordings and motion snapshots
    rec_path = Path(settings.global_.recording_path)
    rec_path.mkdir(parents=True, exist_ok=True)
    app.mount("/static/recordings", StaticFiles(directory=str(rec_path)), name="recordings")

    motion_path = Path(settings.global_.motion_path)
    motion_path.mkdir(parents=True, exist_ok=True)
    app.mount("/static/motion", StaticFiles(directory=str(motion_path)), name="motion")

    # ------------------------------------------------------------------ #
    # Auth                                                                 #
    # ------------------------------------------------------------------ #

    def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
        """Validate HTTP Basic Auth credentials."""
        correct_user = secrets.compare_digest(
            credentials.username, settings.global_.web_username
        )
        correct_pass = secrets.compare_digest(
            credentials.password, settings.global_.web_password
        )
        if not (correct_user and correct_pass):
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Basic"},
            )
        return credentials.username

    # ------------------------------------------------------------------ #
    # HTML pages                                                           #
    # ------------------------------------------------------------------ #

    @app.get("/", response_class=HTMLResponse)
    async def dashboard(request: Request, _=Depends(verify_credentials)):
        cameras = _camera_manager.get_all_statuses()
        for cam in cameras:
            db_row = _db.get_camera(cam["camera_id"]) or {}
            cam["recording"] = bool(db_row.get("recording", 0))
            cam["last_motion"] = db_row.get("last_motion", "—")
        return templates.TemplateResponse("index.html", {
            "request": request,
            "cameras": cameras,
        })

    @app.get("/recordings", response_class=HTMLResponse)
    async def recordings_page(request: Request, _=Depends(verify_credentials)):
        rec_dir = Path(settings.global_.recording_path)
        files = []
        if rec_dir.exists():
            for mp4 in sorted(rec_dir.rglob("*.mp4"), reverse=True)[:200]:
                rel = mp4.relative_to(rec_dir)
                files.append({
                    "path": str(rel),
                    "name": mp4.name,
                    "size_mb": round(mp4.stat().st_size / 1_048_576, 1),
                })
        return templates.TemplateResponse("recordings.html", {
            "request": request,
            "recordings": files,
        })

    @app.get("/motion", response_class=HTMLResponse)
    async def motion_page(request: Request, _=Depends(verify_credentials)):
        events = _db.get_motion_events(limit=100)
        return templates.TemplateResponse("motion_events.html", {
            "request": request,
            "events": events,
        })

    # ------------------------------------------------------------------ #
    # MJPEG stream                                                         #
    # ------------------------------------------------------------------ #

    async def _mjpeg_generator(camera_id: str) -> AsyncGenerator[bytes, None]:
        """Yield MJPEG frames from the camera manager."""
        boundary = b"--frame\r\nContent-Type: image/jpeg\r\n\r\n"
        while True:
            frame = _camera_manager.get_frame(camera_id)
            if frame is None:
                # Send a placeholder if offline
                await asyncio.sleep(0.5)
                continue

            # Run motion detection and annotation inline
            if _motion_manager:
                cam_state = _camera_manager.get_state(camera_id)
                if cam_state:
                    frame = _motion_manager.process_frame(
                        camera_id, cam_state.config, frame
                    )

            _, jpeg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
            yield boundary + jpeg.tobytes() + b"\r\n"
            await asyncio.sleep(1 / 15)  # ~15 fps for dashboard

    @app.get("/video_feed/{camera_id}")
    async def video_feed(camera_id: str, _=Depends(verify_credentials)):
        return StreamingResponse(
            _mjpeg_generator(camera_id),
            media_type="multipart/x-mixed-replace; boundary=frame",
        )

    # ------------------------------------------------------------------ #
    # REST API                                                             #
    # ------------------------------------------------------------------ #

    @app.get("/api/health")
    async def health():
        return {"status": "ok", "cameras": len(_camera_manager.camera_ids)}

    @app.get("/api/cameras")
    async def api_cameras(_=Depends(verify_credentials)):
        return _camera_manager.get_all_statuses()

    @app.post("/api/cameras/{camera_id}/recording/start")
    async def start_recording(camera_id: str, _=Depends(verify_credentials)):
        ok = _recorder.start_camera(camera_id)
        if not ok:
            raise HTTPException(404, f"Camera {camera_id} not found")
        return {"status": "started", "camera_id": camera_id}

    @app.post("/api/cameras/{camera_id}/recording/stop")
    async def stop_recording(camera_id: str, _=Depends(verify_credentials)):
        ok = _recorder.stop_camera(camera_id)
        if not ok:
            raise HTTPException(404, f"Camera {camera_id} not found")
        return {"status": "stopped", "camera_id": camera_id}

    return app
