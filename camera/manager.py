"""
Camera stream manager for LaViewNVR.

Opens RTSP streams via OpenCV, implements exponential back-off reconnect,
and exposes the latest frame for MJPEG streaming.
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Optional

import cv2
import numpy as np

from config.settings import CameraConfig
from core.database import Database

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

MAX_RETRIES = 5
BACKOFF_BASE = 2.0  # seconds, doubled each retry


@dataclass
class CameraState:
    """Runtime state for a single camera stream."""

    config: CameraConfig
    cap: Optional[cv2.VideoCapture] = field(default=None, repr=False)
    frame: Optional[np.ndarray] = field(default=None, repr=False)
    online: bool = False
    width: int = 0
    height: int = 0
    fps: float = 0.0
    last_seen: float = 0.0
    retry_count: int = 0
    thread: Optional[threading.Thread] = field(default=None, repr=False)
    stop_event: threading.Event = field(default_factory=threading.Event, repr=False)
    lock: threading.Lock = field(default_factory=threading.Lock, repr=False)


class CameraManager:
    """
    Manages all camera streams.

    Each camera runs in its own daemon thread, continuously reading frames
    and making them available via ``get_frame(camera_id)``.
    """

    def __init__(self, cameras: list[CameraConfig], db: Database) -> None:
        self.db = db
        self._states: dict[str, CameraState] = {}

        for cam in cameras:
            if cam.enabled:
                self._states[cam.camera_id] = CameraState(config=cam)
                self.db.upsert_camera(cam.camera_id, cam.name, cam.ip)

    # ------------------------------------------------------------------ #
    # Lifecycle                                                            #
    # ------------------------------------------------------------------ #

    def start_all(self) -> None:
        """Start capture threads for all enabled cameras."""
        for cam_id, state in self._states.items():
            self._start_camera(cam_id, state)

    def stop_all(self) -> None:
        """Signal all camera threads to stop and wait for them."""
        for state in self._states.values():
            state.stop_event.set()
        for state in self._states.values():
            if state.thread and state.thread.is_alive():
                state.thread.join(timeout=5)

    def _start_camera(self, cam_id: str, state: CameraState) -> None:
        """Spawn a daemon thread for a single camera."""
        state.stop_event.clear()
        state.thread = threading.Thread(
            target=self._capture_loop,
            args=(cam_id, state),
            name=f"cam-{cam_id}",
            daemon=True,
        )
        state.thread.start()
        logger.info(f"Started capture thread for {cam_id}")

    # ------------------------------------------------------------------ #
    # Capture loop                                                         #
    # ------------------------------------------------------------------ #

    def _capture_loop(self, cam_id: str, state: CameraState) -> None:
        """Continuously read frames, reconnecting with back-off on failure."""
        while not state.stop_event.is_set():
            cap = self._open_stream(state.config.rtsp_url)
            if cap is None:
                state.retry_count += 1
                if state.retry_count > MAX_RETRIES:
                    logger.warning(f"{cam_id}: max retries reached, sleeping 60s")
                    state.stop_event.wait(60)
                    state.retry_count = 0
                    continue
                wait = BACKOFF_BASE ** state.retry_count
                logger.warning(f"{cam_id}: connect failed, retry {state.retry_count}/{MAX_RETRIES} in {wait:.0f}s")
                state.stop_event.wait(wait)
                continue

            # Connected!
            state.width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            state.height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            state.fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
            state.retry_count = 0
            state.online = True
            state.cap = cap
            self.db.set_online(cam_id, True, state.width, state.height, state.fps)
            logger.info(f"{cam_id}: connected {state.width}x{state.height} @ {state.fps:.1f}fps")

            while not state.stop_event.is_set():
                ret, frame = cap.read()
                if not ret or frame is None:
                    logger.warning(f"{cam_id}: frame read failed, reconnecting")
                    break
                state.last_seen = time.time()
                with state.lock:
                    state.frame = frame

            cap.release()
            state.online = False
            state.cap = None
            self.db.set_online(cam_id, False)

    @staticmethod
    def _open_stream(url: str) -> Optional[cv2.VideoCapture]:
        """Open an RTSP stream with a short connection timeout."""
        cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)
        cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 5000)
        if cap.isOpened():
            return cap
        cap.release()
        return None

    # ------------------------------------------------------------------ #
    # Public accessors                                                     #
    # ------------------------------------------------------------------ #

    def get_frame(self, camera_id: str) -> Optional[np.ndarray]:
        """Return the latest frame for a camera (thread-safe copy)."""
        state = self._states.get(camera_id)
        if state is None:
            return None
        with state.lock:
            if state.frame is None:
                return None
            return state.frame.copy()

    def get_status(self, camera_id: str) -> dict:
        """Return status dict for a camera."""
        state = self._states.get(camera_id)
        if not state:
            return {}
        return {
            "camera_id": camera_id,
            "name": state.config.name,
            "ip": state.config.ip,
            "online": state.online,
            "width": state.width,
            "height": state.height,
            "fps": round(state.fps, 1),
            "last_seen": state.last_seen,
        }

    def get_all_statuses(self) -> list[dict]:
        """Return status for all cameras."""
        return [self.get_status(cid) for cid in self._states]

    def get_state(self, camera_id: str) -> Optional[CameraState]:
        """Return the internal CameraState (for use by recorder/motion)."""
        return self._states.get(camera_id)

    @property
    def camera_ids(self) -> list[str]:
        """List of all managed camera IDs."""
        return list(self._states.keys())
