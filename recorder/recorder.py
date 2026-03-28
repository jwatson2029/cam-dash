"""
Video recorder for LaViewNVR.

Uses FFmpeg (via subprocess) for H.264 encoding. OpenCV provides frames
for preview; FFmpeg handles final file output for maximum compatibility.
"""
from __future__ import annotations

import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from config.settings import CameraConfig, GlobalConfig
from core.database import Database

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class CameraRecorder:
    """
    Records a single camera's RTSP stream using FFmpeg.

    Splits recordings into chunks of configurable length (default 60 min).
    Output path: recordings/<camera_name>/<YYYY-MM-DD>/<name>_YYYY-MM-DD_HH-MM-SS.mp4
    """

    def __init__(self, config: CameraConfig, global_cfg: GlobalConfig,
                 db: Database) -> None:
        self.config = config
        self.global_cfg = global_cfg
        self.db = db
        self._process: Optional[subprocess.Popen] = None
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self.recording = False

    def start(self) -> None:
        """Start continuous chunked recording in a background thread."""
        if self.recording:
            logger.warning(f"{self.config.camera_id}: already recording")
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._recording_loop,
            name=f"rec-{self.config.camera_id}",
            daemon=True,
        )
        self._thread.start()
        self.recording = True
        self.db.set_recording(self.config.camera_id, True)
        logger.info(f"{self.config.camera_id}: recording started")

    def stop(self) -> None:
        """Stop recording gracefully."""
        self._stop_event.set()
        self._kill_process()
        if self._thread:
            self._thread.join(timeout=10)
        self.recording = False
        self.db.set_recording(self.config.camera_id, False)
        logger.info(f"{self.config.camera_id}: recording stopped")

    def _recording_loop(self) -> None:
        """Loop, spawning a new FFmpeg process each chunk period."""
        while not self._stop_event.is_set():
            output_path = self._make_output_path()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            duration = self.global_cfg.chunk_minutes * 60

            cmd = self._build_ffmpeg_cmd(str(output_path), duration)
            logger.info(f"{self.config.camera_id}: recording → {output_path.name}")

            try:
                self._process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                )
                # Wait for the chunk duration or stop signal
                start = time.time()
                while not self._stop_event.is_set():
                    elapsed = time.time() - start
                    if elapsed >= duration:
                        break
                    if self._process.poll() is not None:
                        # FFmpeg exited early (likely stream error)
                        err = self._process.stderr.read().decode(errors="ignore")
                        logger.warning(f"{self.config.camera_id}: FFmpeg exited: {err[-200:]}")
                        time.sleep(5)
                        break
                    time.sleep(1)
            except Exception as exc:
                logger.error(f"{self.config.camera_id}: recording error: {exc}")
                time.sleep(5)
            finally:
                self._kill_process()

    def _kill_process(self) -> None:
        """Terminate the FFmpeg subprocess."""
        if self._process and self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
        self._process = None

    def _make_output_path(self) -> Path:
        """Build timestamped output file path."""
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        ts_str = now.strftime("%Y-%m-%d_%H-%M-%S")
        name = self.config.camera_id
        return (
            Path(self.global_cfg.recording_path)
            / name
            / date_str
            / f"{name}_{ts_str}.mp4"
        )

    def _build_ffmpeg_cmd(self, output: str, duration: int) -> list[str]:
        """Build the FFmpeg command list."""
        return [
            "ffmpeg",
            "-y",                            # overwrite without asking
            "-rtsp_transport", "tcp",        # more reliable than UDP
            "-i", self.config.rtsp_url,
            "-t", str(duration),             # chunk duration
            "-c:v", "copy",                  # stream-copy video (no re-encode)
            "-c:a", "aac",                   # encode audio to AAC
            "-movflags", "+faststart",       # web-playback friendly
            output,
        ]


class Recorder:
    """Manages recorders for all enabled cameras."""

    def __init__(self, cameras: list[CameraConfig], global_cfg: GlobalConfig,
                 db: Database) -> None:
        self._recorders: dict[str, CameraRecorder] = {
            cam.camera_id: CameraRecorder(cam, global_cfg, db)
            for cam in cameras
            if cam.enabled and cam.record
        }

    def start_all(self) -> None:
        """Start recording on all cameras marked record=true."""
        for rec in self._recorders.values():
            rec.start()

    def stop_all(self) -> None:
        """Stop all active recorders."""
        for rec in self._recorders.values():
            rec.stop()

    def start_camera(self, camera_id: str) -> bool:
        """Start recording for a specific camera. Returns True if started."""
        rec = self._recorders.get(camera_id)
        if rec:
            rec.start()
            return True
        return False

    def stop_camera(self, camera_id: str) -> bool:
        """Stop recording for a specific camera. Returns True if stopped."""
        rec = self._recorders.get(camera_id)
        if rec:
            rec.stop()
            return True
        return False

    def is_recording(self, camera_id: str) -> bool:
        rec = self._recorders.get(camera_id)
        return rec.recording if rec else False
