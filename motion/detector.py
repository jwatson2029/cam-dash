"""
Motion detection for LaViewNVR.

Abstract base class + OpenCV MOG2 implementation. Designed to be easily
replaced with a Frigate-style AI detector by subclassing MotionDetector.
"""
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

from config.settings import CameraConfig, GlobalConfig
from core.database import Database

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class MotionDetector(ABC):
    """
    Abstract base class for motion detectors.

    Subclass this to plug in a custom detector (e.g., AI-based).
    """

    @abstractmethod
    def detect(self, frame: np.ndarray) -> tuple[bool, float, list]:
        """
        Analyze a frame for motion.

        Returns:
            (motion_detected, confidence, bounding_boxes)
            where bounding_boxes is a list of (x, y, w, h) tuples.
        """
        ...

    def annotate_frame(self, frame: np.ndarray,
                       boxes: list) -> np.ndarray:
        """Draw bounding boxes on the frame."""
        annotated = frame.copy()
        for x, y, w, h in boxes:
            cv2.rectangle(annotated, (x, y), (x + w, y + h), (0, 255, 0), 2)
        return annotated


class OpenCVMotionDetector(MotionDetector):
    """
    MOG2 background subtractor with frame-differencing fallback.

    Sensitivity (0.0–1.0) maps to MOG2 varThreshold:
      - 0.0 = most sensitive (varThreshold ~4)
      - 1.0 = least sensitive (varThreshold ~100)
    """

    def __init__(self, sensitivity: float = 0.5, min_area: int = 500) -> None:
        threshold = int(4 + (1.0 - sensitivity) * 96)
        self._bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            detectShadows=False,
            varThreshold=threshold,
        )
        self._min_area = min_area

    def detect(self, frame: np.ndarray) -> tuple[bool, float, list]:
        """Run MOG2 and return (detected, confidence, boxes)."""
        mask = self._bg_subtractor.apply(frame)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL,
                                       cv2.CHAIN_APPROX_SIMPLE)
        boxes = []
        total_area = 0
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area >= self._min_area:
                x, y, w, h = cv2.boundingRect(cnt)
                boxes.append((x, y, w, h))
                total_area += area

        if not boxes:
            return False, 0.0, []

        frame_area = frame.shape[0] * frame.shape[1]
        confidence = min(1.0, total_area / (frame_area * 0.1))
        return True, round(confidence, 3), boxes


class MotionManager:
    """
    Runs motion detection on camera frames and handles events.

    Saves JPEG snapshots, logs to DB, and optionally publishes MQTT.
    """

    def __init__(self, cameras: list[CameraConfig], global_cfg: GlobalConfig,
                 db: Database) -> None:
        self.global_cfg = global_cfg
        self.db = db
        self._detectors: dict[str, OpenCVMotionDetector] = {}
        self._last_event: dict[str, float] = {}
        self._mqtt_client = None

        for cam in cameras:
            if cam.enabled and cam.motion_enabled:
                self._detectors[cam.camera_id] = OpenCVMotionDetector(
                    sensitivity=cam.motion_sensitivity,
                    min_area=cam.motion_min_area,
                )
                self._last_event[cam.camera_id] = 0.0

    def process_frame(self, camera_id: str, config: CameraConfig,
                      frame: np.ndarray) -> np.ndarray:
        """
        Run detection on a frame.

        Annotates the frame with bounding boxes and handles events.
        Returns the (possibly annotated) frame.
        """
        detector = self._detectors.get(camera_id)
        if detector is None:
            return frame

        detected, confidence, boxes = detector.detect(frame)

        if boxes:
            frame = detector.annotate_frame(frame, boxes)

        if detected:
            now = time.time()
            cooldown = config.motion_cooldown
            if now - self._last_event.get(camera_id, 0) >= cooldown:
                self._last_event[camera_id] = now
                snapshot_path = self._save_snapshot(camera_id, frame)
                self.db.record_motion(camera_id, snapshot_path, confidence)
                logger.info(f"{camera_id}: motion detected (conf={confidence:.2f})")

        return frame

    def _save_snapshot(self, camera_id: str, frame: np.ndarray) -> str:
        """Save a JPEG snapshot and return the file path."""
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        out_dir = Path(self.global_cfg.motion_path) / camera_id
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"{camera_id}_{ts}.jpg"
        cv2.imwrite(str(path), frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
        return str(path)
