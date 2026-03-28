"""
Configuration management for LaViewNVR.

Loads and validates config.yaml using Pydantic v2. Supports environment
variable overrides for sensitive fields.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import BaseModel, Field, field_validator


class CameraConfig(BaseModel):
    """Configuration for a single IP camera."""

    name: str
    ip: str
    username: str = "admin"
    password: str = "admin"
    rtsp_path: str = "/Streaming/Channels/101"
    sub_rtsp_path: str = "/Streaming/Channels/102"
    port: int = 554
    enabled: bool = True
    record: bool = True
    motion_enabled: bool = True
    motion_sensitivity: float = Field(default=0.5, ge=0.0, le=1.0)
    motion_min_area: int = Field(default=500, ge=1)
    motion_cooldown: float = Field(default=5.0, ge=0.0)
    auto_discovered: bool = False

    @property
    def rtsp_url(self) -> str:
        """Build full RTSP URL for the main stream."""
        return f"rtsp://{self.username}:{self.password}@{self.ip}:{self.port}{self.rtsp_path}"

    @property
    def sub_rtsp_url(self) -> str:
        """Build full RTSP URL for the sub-stream."""
        return f"rtsp://{self.username}:{self.password}@{self.ip}:{self.port}{self.sub_rtsp_path}"

    @property
    def camera_id(self) -> str:
        """Sanitized ID safe for use in file paths and URLs."""
        return self.name.lower().replace(" ", "_")


class MqttConfig(BaseModel):
    """Optional MQTT broker settings."""

    enabled: bool = False
    broker: str = "localhost"
    port: int = 1883
    username: str = ""
    password: str = ""
    topic_prefix: str = "nvr"


class NotificationConfig(BaseModel):
    """Optional notification settings."""

    email_enabled: bool = False
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    email_to: str = ""
    desktop_enabled: bool = False


class GlobalConfig(BaseModel):
    """Global NVR system settings."""

    web_port: int = 8000
    web_username: str = "admin"
    web_password: str = "changeme"
    recording_path: str = "recordings"
    motion_path: str = "motion_events"
    chunk_minutes: int = Field(default=60, ge=1)
    log_level: str = "INFO"
    log_path: str = "logs/nvr.log"
    db_path: str = "data/cameras.db"
    rediscovery_interval: int = Field(default=300, ge=30)
    default_rtsp_username: str = "admin"
    default_rtsp_password: str = "admin"

    def model_post_init(self, __context: Any) -> None:
        """Apply environment variable overrides after model init."""
        env_password = os.environ.get("NVR_WEB_PASSWORD")
        if env_password:
            object.__setattr__(self, "web_password", env_password)


class Settings(BaseModel):
    """Root settings model for the entire application."""

    global_: GlobalConfig = Field(default_factory=GlobalConfig, alias="global")
    cameras: list[CameraConfig] = Field(default_factory=list)
    mqtt: MqttConfig = Field(default_factory=MqttConfig)
    notifications: NotificationConfig = Field(default_factory=NotificationConfig)

    model_config = {"populate_by_name": True}


def load_settings(config_path: str = "config.yaml") -> Settings:
    """
    Load settings from a YAML file.

    Falls back to config.example.yaml if config.yaml does not exist.
    """
    path = Path(config_path)
    if not path.exists():
        fallback = Path("config.example.yaml")
        if fallback.exists():
            path = fallback
        else:
            # Return defaults if no config file exists
            return Settings()

    with path.open("r") as f:
        raw: dict = yaml.safe_load(f) or {}

    return Settings.model_validate(raw)


def save_settings(settings: Settings, config_path: str = "config.yaml") -> None:
    """Persist settings back to config.yaml."""
    path = Path(config_path)
    data = settings.model_dump(by_alias=True)
    with path.open("w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
