# Cyberwave Edge Python

[![License: MIT](https://img.shields.io/github/license/cyberwave-os/cyberwave-edge-python)](https://github.com/cyberwave-os/cyberwave-edge-python/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![GitHub stars](https://img.shields.io/github/stars/cyberwave-os/cyberwave-edge-python)](https://github.com/cyberwave-os/cyberwave-edge-python/stargazers)
[![GitHub contributors](https://img.shields.io/github/contributors/cyberwave-os/cyberwave-edge-python)](https://github.com/cyberwave-os/cyberwave-edge-python/graphs/contributors)
[![GitHub issues](https://img.shields.io/github/issues/cyberwave-os/cyberwave-edge-python)](https://github.com/cyberwave-os/cyberwave-edge-python/issues)

Simple, open-source edge software to integrate sensors (like cameras) and USB robots (like the SO-100) to Cyberwave, written in Python.

## Features

✅ **Implemented:**

- Auto-start on device boot and connect to MQTT
- Automatic reconnection with exponential backoff
- Status reporting to Cyberwave backend
- Command handling via MQTT topics
- Video streaming via WebRTC
- Configurable logging and error handling

🚧 **Coming Soon:**

- Start video stream on demand
- Camera calibration
- USB robot actuation via MQTT

## Requirements

- Ubuntu 20.04+ (or any Linux with systemd)
- Python 3.9 or higher
- Cyberwave account and API token
- Camera device (optional, for video streaming features)

## Getting Started

### Prerequisites

Before you begin, ensure you have the following:

1. **Python 3.9 or higher** installed on your system
   ```bash
   python3 --version
   ```

2. **Cyberwave Account**: Sign up at [cyberwave.com](https://cyberwave.com) to obtain:
   - API Token (from Settings → API Tokens)
   - Twin UUID (create a digital twin and copy its UUID)

3. **Hardware**: USB camera or built-in webcam (optional, for video streaming features)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/cyberwave-os/cyberwave-edge-python.git
   cd cyberwave-edge-python
   ```

2. **Install dependencies**
   ```bash
   pip install -e .
   ```

3. **Configure your environment**
   ```bash
   cp .env.example .env
   nano .env  # Edit with your Cyberwave credentials
   ```

4. **Run the service**
   ```bash
   cyberwave-edge
   ```

That's it! Your edge device should now be connected to Cyberwave.

## Installation

### 1. Development Installation

For testing and development:

```bash
# Clone the repository
git clone https://github.com/cyberwave-os/cyberwave-edge-python.git
cd cyberwave-edge-python

# Install the package
pip install -e .

# Copy the example configuration
cp .env.example .env

# Edit the configuration with your credentials
nano .env
```

### 2. Production Installation (Ubuntu/Linux)

For production deployment as a systemd service:

```bash
# Run the installation script (requires sudo)
sudo ./scripts/install.sh
```

This will:

- Create a dedicated `cyberwave` user
- Install the package to `/opt/cyberwave-edge`
- Set up systemd service for auto-start on boot
- Configure log rotation

After installation:

```bash
# Edit the configuration
sudo nano /opt/cyberwave-edge/.env

# Start the service
sudo systemctl start cyberwave-edge

# Enable auto-start on boot (already done by install.sh)
sudo systemctl enable cyberwave-edge

# Check status
sudo systemctl status cyberwave-edge

# View logs
sudo journalctl -u cyberwave-edge -f
```

## Configuration

Create a `.env` file in the installation directory with the following variables:

```bash
# Required
CYBERWAVE_TOKEN=your_api_token_here
CYBERWAVE_TWIN_UUID=your_twin_uuid_here

# Optional
CYBERWAVE_BASE_URL=https://api.cyberwave.com
CYBERWAVE_EDGE_UUID=edge-device-001

# MQTT Configuration
CYBERWAVE_MQTT_HOST=
CYBERWAVE_MQTT_PORT=1883
CYBERWAVE_MQTT_USERNAME=
CYBERWAVE_MQTT_PASSWORD=

# Camera Configuration
CAMERA_ID=0
CAMERA_FPS=10
CAMERA_WIDTH=640
CAMERA_HEIGHT=480

# Logging
LOG_LEVEL=INFO
```

### Getting Your Credentials

1. **API Token**: Log in to your Cyberwave instance → Settings → API Tokens
2. **Twin UUID**: Create a digital twin in your project and copy its UUID

## Usage

### Running Manually

For development and testing:

```bash
# Run directly
python -m cyberwave_edge.service

# Or use the installed script
cyberwave-edge
```

### Running as a Service

For production use with auto-start:

```bash
# Start/stop the service
sudo systemctl start cyberwave-edge
sudo systemctl stop cyberwave-edge

# Restart the service
sudo systemctl restart cyberwave-edge

# View status
sudo systemctl status cyberwave-edge

# View real-time logs
sudo journalctl -u cyberwave-edge -f
```

## Architecture

The edge service:

1. **Connects to Cyberwave** using the Python SDK
2. **Establishes MQTT connection** for real-time communication
3. **Subscribes to command topics**: `cyberwave/device/{device_id}/commands/#`
4. **Publishes status updates**: `cyberwave/device/{device_id}/status` (every 30 seconds)
5. **Handles commands** via registered command handlers
6. **Streams video** via WebRTC when commanded

### MQTT Topics

**Subscribed Topics:**

- `cyberwave/device/{device_id}/commands/video` - Video control commands (start_video, stop_video)
- `cyberwave/device/{device_id}/commands/sensor` - Sensor reading commands
- `cyberwave/device/{device_id}/commands/actuate` - Robot actuation commands
- `cyberwave/device/{device_id}/commands/config` - Configuration updates

**Published Topics:**

- `cyberwave/device/{device_id}/status` - Device status and health metrics
- `cyberwave/device/{device_id}/telemetry` - Sensor data and telemetry
- `cyberwave/device/{device_id}/events` - Event notifications

## Running Tests

The project includes a comprehensive test suite to ensure reliability and correctness.

### Install Test Dependencies

```bash
# Install the package with development dependencies
pip install -e ".[dev]"
```

### Run Tests

```bash
# Run all tests
pytest

# Run tests with coverage report
pytest --cov=cyberwave_edge --cov-report=html

# Run tests with verbose output
pytest -v

# Run specific test file
pytest tests/test_config.py
```

### Test Coverage

After running tests with coverage, you can view the report:

```bash
# Generate and open coverage report
pytest --cov=cyberwave_edge --cov-report=html
open htmlcov/index.html  # macOS
# xdg-open htmlcov/index.html  # Linux
```

## Uninstallation

To remove the service:

```bash
sudo ./scripts/uninstall.sh
```

This will:

- Stop and disable the systemd service
- Optionally remove the installation directory
- Optionally remove the service user

## Contributing

Contributions welcome! This is open-source software under the MIT license.

## License

MIT License. See the [LICENSE](LICENSE) file for details.

## Links

- **Repository**: https://github.com/cyberwave-os/cyberwave-edge-python
- **Template**: https://github.com/cyberwave-os/edge-template
- **Documentation**: https://docs.cyberwave.com
- **Website**: https://cyberwave.com
- **Issues**: https://github.com/cyberwave-os/cyberwave-edge-python/issues

## Related Projects

- [edge-template](https://github.com/cyberwave-os/edge-template) - Template for creating edge services in any language
- [cyberwave-python](https://github.com/cyberwave/cyberwave-python) - Python SDK for Cyberwave
