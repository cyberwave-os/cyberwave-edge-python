#!/bin/bash

set -e

echo "====================================="
echo "Cyberwave Edge Python - Installation"
echo "====================================="
echo

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root (use sudo)" 
   exit 1
fi

# Configuration
INSTALL_DIR="/opt/cyberwave-edge"
SERVICE_USER="cyberwave"
SERVICE_FILE="cyberwave-edge.service"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Create service user if it doesn't exist
if ! id "$SERVICE_USER" &>/dev/null; then
    echo "Creating service user: $SERVICE_USER"
    useradd -r -s /bin/false $SERVICE_USER
else
    echo "Service user $SERVICE_USER already exists"
fi

# Install system dependencies
echo "Installing system dependencies..."
if command -v apt-get &> /dev/null; then
    apt-get update
    apt-get install -y ffmpeg python3-venv python3-full
elif command -v yum &> /dev/null; then
    yum install -y ffmpeg python3-virtualenv
elif command -v dnf &> /dev/null; then
    dnf install -y ffmpeg python3-virtualenv
elif command -v pacman &> /dev/null; then
    pacman -S --noconfirm ffmpeg python-virtualenv
else
    echo "WARNING: Could not detect package manager. Please install ffmpeg and python3-venv manually."
    echo "ffmpeg is required for video streaming functionality."
fi

# Create installation directory
echo "Creating installation directory: $INSTALL_DIR"
mkdir -p $INSTALL_DIR
cd $INSTALL_DIR

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv $INSTALL_DIR/venv

# Install Python dependencies
echo "Installing Python package..."
$INSTALL_DIR/venv/bin/pip install --upgrade pip
$INSTALL_DIR/venv/bin/pip install cyberwave-edge-python

# Copy .env.example if .env doesn't exist
if [ ! -f "$INSTALL_DIR/.env" ]; then
    echo "Creating .env file from example..."
    if [ -f "$PROJECT_ROOT/.env.example" ]; then
        cp "$PROJECT_ROOT/.env.example" "$INSTALL_DIR/.env"
        echo
        echo "⚠️  IMPORTANT: Edit $INSTALL_DIR/.env with your credentials!"
        echo
    else
        echo "Warning: .env.example not found, you'll need to create .env manually"
    fi
else
    echo ".env file already exists, skipping"
fi

# Set permissions
echo "Setting permissions..."
chown -R $SERVICE_USER:$SERVICE_USER $INSTALL_DIR
chmod 600 $INSTALL_DIR/.env

# Install systemd service
echo "Installing systemd service..."
cp "$SCRIPT_DIR/$SERVICE_FILE" /etc/systemd/system/
systemctl daemon-reload

# Enable service
echo "Enabling service to start on boot..."
systemctl enable $SERVICE_FILE

echo
echo "====================================="
echo "Installation Complete!"
echo "====================================="
echo
echo "Next steps:"
echo "1. Edit the configuration file:"
echo "   sudo nano $INSTALL_DIR/.env"
echo
echo "2. Start the service:"
echo "   sudo systemctl start cyberwave-edge"
echo
echo "3. Check service status:"
echo "   sudo systemctl status cyberwave-edge"
echo
echo "4. View logs:"
echo "   sudo journalctl -u cyberwave-edge -f"
echo

