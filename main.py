#!/usr/bin/env python3
"""
LaViewNVR - Main entry point.

Starts the FastAPI web server, camera capture threads, recorder, and
optional auto-discovery. All components run concurrently using asyncio
(for the web server) and background threads (for OpenCV/FFmpeg).

Usage:
    python main.py                  # Start normally
    python main.py --discover       # Run subnet discovery first
    python main.py --config path/to/config.yaml
"""
from __future__ import annotations

import argparse
import signal
import sys
from pathlib import Path

import uvicorn

from camera.manager import CameraManager
from config.settings import CameraConfig, load_settings, save_settings
from core.database import Database
from core.logging_setup import setup_logging
from discovery.scanner import NetworkScanner
from motion.detector import MotionManager
from recorder.recorder import Recorder
from utils.helpers import ensure_dirs
from web.app import create_app

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


def run_discovery(settings, config_path: str) -> None:
    """Scan the local subnet and append new cameras to the config."""
    global_cfg = settings.global_
    logger.info("Starting network camera discovery...")
    scanner = NetworkScanner(
        username=global_cfg.default_rtsp_username,
        password=global_cfg.default_rtsp_password,
    )
    found = scanner.scan()
    existing_ips = {cam.ip for cam in settings.cameras}
    added = 0
    for disc in found:
        if disc.ip in existing_ips:
            continue
        name = f"camera_{disc.ip.replace('.', '_')}"
        cam = CameraConfig(
            name=name,
            ip=disc.ip,
            username=global_cfg.default_rtsp_username,
            password=global_cfg.default_rtsp_password,
            rtsp_path=disc.rtsp_path or "/Streaming/Channels/101",
            auto_discovered=True,
        )
        settings.cameras.append(cam)
        added += 1
        logger.info(f"Discovered camera: {disc.ip} → added as '{name}'")
    if added:
        save_settings(settings, config_path)
        logger.info(f"Added {added} new cameras to {config_path}")
    else:
        logger.info("No new cameras found on the network.")


def main() -> None:
    parser = argparse.ArgumentParser(description="LaViewNVR - Local NVR System")
    parser.add_argument("--config", default="config.yaml",
                        help="Path to config file (default: config.yaml)")
    parser.add_argument("--discover", action="store_true",
                        help="Run subnet discovery before starting")
    args = parser.parse_args()

    # ------------------------------------------------------------------ #
    # Load configuration                                                   #
    # ------------------------------------------------------------------ #
    settings = load_settings(args.config)
    global_cfg = settings.global_

    # ------------------------------------------------------------------ #
    # Set up logging and directories                                       #
    # ------------------------------------------------------------------ #
    setup_logging(global_cfg.log_path, global_cfg.log_level)
    ensure_dirs(
        global_cfg.recording_path,
        global_cfg.motion_path,
        str(Path(global_cfg.log_path).parent),
        str(Path(global_cfg.db_path).parent),
    )

    logger.info("=" * 60)
    logger.info("LaViewNVR starting up")
    logger.info(f"Config: {args.config}")
    logger.info(f"Cameras: {len(settings.cameras)}")
    logger.info(f"Web port: {global_cfg.web_port}")
    logger.info("=" * 60)

    # ------------------------------------------------------------------ #
    # Optional discovery                                                   #
    # ------------------------------------------------------------------ #
    if args.discover:
        run_discovery(settings, args.config)

    # ------------------------------------------------------------------ #
    # Initialise components                                                #
    # ------------------------------------------------------------------ #
    db = Database(global_cfg.db_path)
    camera_manager = CameraManager(settings.cameras, db)
    recorder = Recorder(settings.cameras, global_cfg, db)
    motion_manager = MotionManager(settings.cameras, global_cfg, db)
    app = create_app(settings, db, camera_manager, recorder, motion_manager)

    # ------------------------------------------------------------------ #
    # Start background threads                                             #
    # ------------------------------------------------------------------ #
    camera_manager.start_all()
    recorder.start_all()
    logger.info("Camera capture and recording threads started")

    # ------------------------------------------------------------------ #
    # Graceful shutdown                                                    #
    # ------------------------------------------------------------------ #
    def shutdown(signum, frame):
        logger.info("Shutting down LaViewNVR...")
        recorder.stop_all()
        camera_manager.stop_all()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # ------------------------------------------------------------------ #
    # Start web server (blocks here)                                       #
    # ------------------------------------------------------------------ #
    logger.info(f"Dashboard → http://localhost:{global_cfg.web_port}")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=global_cfg.web_port,
        log_level=global_cfg.log_level.lower(),
        access_log=False,
    )


if __name__ == "__main__":
    main()
