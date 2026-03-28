"""
SQLite database for persistent camera state.

Stores online/offline status, last seen timestamp, resolution, and FPS.
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Generator, Optional


class Database:
    """Thin wrapper around SQLite for camera state persistence."""

    def __init__(self, db_path: str = "data/cameras.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextmanager
    def _conn(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager yielding a thread-safe connection."""
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_schema(self) -> None:
        """Create tables if they don't already exist."""
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cameras (
                    camera_id   TEXT PRIMARY KEY,
                    name        TEXT NOT NULL,
                    ip          TEXT NOT NULL,
                    online      INTEGER DEFAULT 0,
                    width       INTEGER,
                    height      INTEGER,
                    fps         REAL,
                    last_seen   TEXT,
                    last_motion TEXT,
                    recording   INTEGER DEFAULT 0,
                    created_at  TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS motion_events (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    camera_id   TEXT NOT NULL,
                    timestamp   TEXT NOT NULL,
                    snapshot    TEXT,
                    confidence  REAL,
                    FOREIGN KEY (camera_id) REFERENCES cameras(camera_id)
                )
            """)

    # ------------------------------------------------------------------ #
    # Camera state                                                         #
    # ------------------------------------------------------------------ #

    def upsert_camera(self, camera_id: str, name: str, ip: str) -> None:
        """Insert or update basic camera info."""
        with self._conn() as conn:
            conn.execute("""
                INSERT INTO cameras (camera_id, name, ip)
                VALUES (?, ?, ?)
                ON CONFLICT(camera_id) DO UPDATE SET name=excluded.name, ip=excluded.ip
            """, (camera_id, name, ip))

    def set_online(self, camera_id: str, online: bool,
                   width: Optional[int] = None, height: Optional[int] = None,
                   fps: Optional[float] = None) -> None:
        """Update online status and stream info for a camera."""
        now = datetime.utcnow().isoformat()
        with self._conn() as conn:
            conn.execute("""
                UPDATE cameras
                SET online=?, width=?, height=?, fps=?, last_seen=?
                WHERE camera_id=?
            """, (int(online), width, height, fps, now if online else None, camera_id))

    def set_recording(self, camera_id: str, recording: bool) -> None:
        """Mark a camera as currently recording."""
        with self._conn() as conn:
            conn.execute("UPDATE cameras SET recording=? WHERE camera_id=?",
                         (int(recording), camera_id))

    def get_all_cameras(self) -> list[dict]:
        """Return all camera rows as a list of dicts."""
        with self._conn() as conn:
            rows = conn.execute("SELECT * FROM cameras").fetchall()
        return [dict(row) for row in rows]

    def get_camera(self, camera_id: str) -> Optional[dict]:
        """Return a single camera row or None."""
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM cameras WHERE camera_id=?",
                               (camera_id,)).fetchone()
        return dict(row) if row else None

    # ------------------------------------------------------------------ #
    # Motion events                                                        #
    # ------------------------------------------------------------------ #

    def record_motion(self, camera_id: str, snapshot: Optional[str],
                      confidence: float) -> None:
        """Insert a motion event record."""
        now = datetime.utcnow().isoformat()
        with self._conn() as conn:
            conn.execute("""
                INSERT INTO motion_events (camera_id, timestamp, snapshot, confidence)
                VALUES (?, ?, ?, ?)
            """, (camera_id, now, snapshot, confidence))
            conn.execute("UPDATE cameras SET last_motion=? WHERE camera_id=?",
                         (now, camera_id))

    def get_motion_events(self, camera_id: Optional[str] = None,
                          limit: int = 100) -> list[dict]:
        """Return recent motion events, optionally filtered by camera."""
        with self._conn() as conn:
            if camera_id:
                rows = conn.execute("""
                    SELECT * FROM motion_events WHERE camera_id=?
                    ORDER BY timestamp DESC LIMIT ?
                """, (camera_id, limit)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT * FROM motion_events
                    ORDER BY timestamp DESC LIMIT ?
                """, (limit,)).fetchall()
        return [dict(row) for row in rows]
