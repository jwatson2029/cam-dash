# LaViewNVR

A **complete, production-ready, fully local** Network Video Recorder (NVR) system built with Python, supporting LaView / Hikvision-style IP cameras. Zero cloud dependencies.

## Features

- 🔍 **Auto-discovery** of IP cameras on your local network (ping sweep + port scan)
- 📹 **Multi-stream recording** with FFmpeg H.264 encoding
- 🏃 **Motion detection** per camera (OpenCV MOG2)
- 🌐 **Web dashboard** (FastAPI + HTMX + Bootstrap 5) at `http://localhost:8000`
- 🔒 **HTTP Basic Auth** protected dashboard
- 📦 **SQLite** camera state storage
- 🐳 **Docker** support

## Quick Start (macOS)

### 1 — Install Homebrew (if you don't have it)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 2 — Install system dependencies

```bash
brew install python@3.12 ffmpeg
```

### 3 — Clone the repo and create a virtual environment

```bash
git clone https://github.com/jwatson2029/cam-dash.git
cd cam-dash

python3.12 -m venv .venv
source .venv/bin/activate
```

### 4 — Install Python dependencies

```bash
pip install -r requirements.txt
```

### 5 — Configure

```bash
cp config.example.yaml config.yaml
# Open config.yaml in your editor and fill in your camera details
```

### 6 — Run

```bash
python main.py
```

Dashboard: http://localhost:8000  
Default credentials: `admin` / `changeme`

> **Tip:** Keep the virtual environment active (`source .venv/bin/activate`) every time you open a new terminal to run the app.

---

## Quick Start (Local — Linux)

### Prerequisites

- Python 3.12+
- FFmpeg installed (`sudo apt install ffmpeg`)
- OpenCV dependencies

```bash
# Clone and install
pip install -r requirements.txt

# Copy and edit config
cp config.example.yaml config.yaml
# Edit config.yaml with your camera details

# Run
python main.py
```

Dashboard: http://localhost:8000  
Default credentials: `admin` / `changeme`

## Quick Start (Docker)

### Linux

```bash
docker compose up -d
```

### macOS

`network_mode: host` is not supported by Docker Desktop for Mac. Use the
provided macOS override file instead:

```bash
cp config.example.yaml config.yaml
# Edit config.yaml with your camera IPs and credentials
docker compose -f docker-compose.yml -f docker-compose.mac.yml up -d
```

> **Note:** Auto-discovery (`--discover`) does not work through Docker on
> macOS because Docker runs inside a Linux VM. Add cameras manually in
> `config.yaml`.

Dashboard: http://localhost:8000

## Configuration

Edit `config.yaml`:

```yaml
global:
  web_port: 8000
  web_username: admin
  web_password: changeme
  recording_path: recordings
  chunk_minutes: 60
  log_level: INFO
  rediscovery_interval: 300

cameras:
  - name: front_door
    ip: 192.168.1.100
    username: admin
    password: password123
    rtsp_path: /Streaming/Channels/101
    enabled: true
    motion_sensitivity: 0.5
    motion_min_area: 500
    motion_cooldown: 5
```

### LaView Camera Example

LaView cameras typically use Hikvision-compatible RTSP paths:
- Main stream: `/Streaming/Channels/101`
- Sub stream: `/Streaming/Channels/102`

See `config.example.yaml` for full two-camera example.

## Adding Cameras

### Manual

Add to `config.yaml` under `cameras:`:

```yaml
cameras:
  - name: backyard
    ip: 192.168.1.101
    username: admin
    password: secret
    rtsp_path: /Streaming/Channels/101
    enabled: true
```

### Auto-Discovery

```bash
python main.py --discover
```

Scans the local subnet and adds found cameras to `config.yaml`.

## API Endpoints

| Endpoint | Description |
|---|---|
| `GET /` | Main dashboard |
| `GET /video_feed/{camera_id}` | Live MJPEG stream |
| `GET /api/cameras` | Camera status JSON |
| `GET /api/health` | Health check |
| `POST /api/cameras/{id}/recording/start` | Start recording |
| `POST /api/cameras/{id}/recording/stop` | Stop recording |
| `GET /recordings` | Recording browser |
| `GET /motion` | Motion event gallery |

## Troubleshooting

**Camera shows offline:**
- Check IP and credentials in config.yaml
- Ensure camera is reachable: `ping <camera_ip>`
- Test RTSP: `ffplay rtsp://admin:password@192.168.1.100/Streaming/Channels/101`

**No video in dashboard:**
- Ensure FFmpeg is installed: `ffmpeg -version`
- Check logs: `tail -f logs/nvr.log`

**Discovery finds no cameras:**
- Ensure you are on the same network/subnet as cameras
- Try adding cameras manually

## License

MIT
