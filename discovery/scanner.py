"""
Network Camera Discovery for LaViewNVR.

Performs a fast subnet ping sweep + targeted port scan to identify
potential IP cameras. Attempts common RTSP URLs with special handling
for LaView / Hikvision-style devices.
"""
from __future__ import annotations

import ipaddress
import socket
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

# Ports commonly used by IP cameras
CAMERA_PORTS = [554, 80, 443, 8000, 37777]

# RTSP path candidates ordered by priority
RTSP_PATHS = [
    # LaView / Hikvision
    "/Streaming/Channels/101",
    "/Streaming/Channels/102",
    "/Streaming/Channels/201",
    # Dahua / generic
    "/cam/realmonitor?channel=1&subtype=0",
    "/cam/realmonitor?channel=1&subtype=1",
    # Generic
    "/stream1",
    "/stream2",
    "/live/ch00_0",
    "/live/ch01_0",
    "/video1",
    "/",
]


class DiscoveredCamera:
    """Represents a camera found during network discovery."""

    __slots__ = ("ip", "open_ports", "rtsp_url", "rtsp_path")

    def __init__(self, ip: str, open_ports: list[int],
                 rtsp_url: str = "", rtsp_path: str = "") -> None:
        self.ip = ip
        self.open_ports = open_ports
        self.rtsp_url = rtsp_url
        self.rtsp_path = rtsp_path

    def __repr__(self) -> str:
        return f"<DiscoveredCamera ip={self.ip} ports={self.open_ports}>"


class NetworkScanner:
    """
    Scan the local network for IP cameras.

    Usage::

        scanner = NetworkScanner(username="admin", password="admin123")
        cameras = scanner.scan()
        for cam in cameras:
            print(cam.ip, cam.rtsp_url)
    """

    def __init__(
        self,
        subnet: Optional[str] = None,
        username: str = "admin",
        password: str = "admin",
        timeout: float = 1.0,
        max_workers: int = 64,
    ) -> None:
        self.subnet = subnet or self._detect_subnet()
        self.username = username
        self.password = password
        self.timeout = timeout
        self.max_workers = max_workers

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def scan(self) -> list[DiscoveredCamera]:
        """
        Full discovery: ping sweep → port scan → RTSP probe.

        Returns a list of DiscoveredCamera objects.
        """
        logger.info(f"Starting network scan on {self.subnet}")
        live_hosts = self._ping_sweep()
        logger.info(f"Ping sweep found {len(live_hosts)} live hosts")

        discovered: list[DiscoveredCamera] = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            futures = {pool.submit(self._scan_host, ip): ip for ip in live_hosts}
            for future in as_completed(futures):
                result = future.result()
                if result:
                    discovered.append(result)

        logger.info(f"Discovery complete — found {len(discovered)} potential cameras")
        return discovered

    # ------------------------------------------------------------------ #
    # Internal helpers                                                     #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _detect_subnet() -> str:
        """Guess the local /24 subnet by inspecting the default route."""
        try:
            # Connect to an external address to discover local IP (no packet sent)
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
            network = ipaddress.IPv4Network(f"{local_ip}/24", strict=False)
            return str(network)
        except Exception:
            return "192.168.1.0/24"

    def _ping_sweep(self) -> list[str]:
        """Return list of IPs that respond to ping in the subnet."""
        network = ipaddress.IPv4Network(self.subnet, strict=False)
        live: list[str] = []
        lock = threading.Lock()

        def _ping(ip: str) -> None:
            try:
                result = subprocess.run(
                    ["ping", "-c", "1", "-W", "1", str(ip)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=2,
                )
                if result.returncode == 0:
                    with lock:
                        live.append(str(ip))
            except Exception:
                pass

        hosts = [str(h) for h in network.hosts()]
        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            pool.map(_ping, hosts)

        return live

    def _is_port_open(self, ip: str, port: int) -> bool:
        """Return True if *port* on *ip* accepts a TCP connection."""
        try:
            with socket.create_connection((ip, port), timeout=self.timeout):
                return True
        except (OSError, ConnectionRefusedError):
            return False

    def _probe_rtsp(self, ip: str, path: str) -> bool:
        """
        Check whether an RTSP URL is likely valid using a socket handshake.

        We send a minimal RTSP OPTIONS request and look for "RTSP/1.0" in
        the response — no OpenCV needed for discovery.
        """
        try:
            with socket.create_connection((ip, 554), timeout=self.timeout) as s:
                url = f"rtsp://{ip}:554{path}"
                request = (
                    f"OPTIONS {url} RTSP/1.0\r\n"
                    f"CSeq: 1\r\n"
                    f"User-Agent: LaViewNVR/1.0\r\n\r\n"
                )
                s.sendall(request.encode())
                response = s.recv(256).decode(errors="ignore")
                return "RTSP/1.0" in response
        except Exception:
            return False

    def _scan_host(self, ip: str) -> Optional[DiscoveredCamera]:
        """Scan a single host: port check then RTSP probe."""
        open_ports = [p for p in CAMERA_PORTS if self._is_port_open(ip, p)]
        if not open_ports:
            return None

        # Only probe RTSP if port 554 is open
        if 554 not in open_ports:
            # Might still be a camera on a different port, return with no RTSP
            return DiscoveredCamera(ip=ip, open_ports=open_ports)

        for path in RTSP_PATHS:
            if self._probe_rtsp(ip, path):
                rtsp_url = (
                    f"rtsp://{self.username}:{self.password}@{ip}:554{path}"
                )
                logger.info(f"Found RTSP camera at {ip}{path}")
                return DiscoveredCamera(
                    ip=ip,
                    open_ports=open_ports,
                    rtsp_url=rtsp_url,
                    rtsp_path=path,
                )

        # Camera-like device but RTSP probe inconclusive
        return DiscoveredCamera(ip=ip, open_ports=open_ports)
