"""
Tests for configuration management
"""

import os
import tempfile
from pathlib import Path

import pytest

from cyberwave_edge.config import EdgeConfig, load_config


def test_edge_config_defaults():
    """Test EdgeConfig with default values"""
    config = EdgeConfig()
    assert config.cyberwave_base_url == "https://api.cyberwave.com"
    assert config.mqtt_port == 1883
    assert config.device_id == "edge-device-001"
    assert config.camera_id == 0
    assert config.camera_fps == 10
    assert config.log_level == "INFO"


def test_edge_config_from_env():
    """Test EdgeConfig loads from environment variables"""
    os.environ["CYBERWAVE_TOKEN"] = "test_token"
    os.environ["CYBERWAVE_TWIN_UUID"] = "test_uuid"
    os.environ["CYBERWAVE_EDGE_UUID"] = "test_device"
    os.environ["CAMERA_ID"] = "1"

    config = EdgeConfig()

    assert config.cyberwave_token == "test_token"
    assert config.twin_uuid == "test_uuid"
    assert config.device_id == "test_device"
    assert config.camera_id == 1

    # Clean up
    del os.environ["CYBERWAVE_TOKEN"]
    del os.environ["CYBERWAVE_TWIN_UUID"]
    del os.environ["CYBERWAVE_EDGE_UUID"]
    del os.environ["CAMERA_ID"]


def test_config_validation():
    """Test configuration validation"""
    # Missing required fields
    config = EdgeConfig()
    assert not config.validate()

    # With required fields
    config.cyberwave_token = "test_token"
    config.twin_uuid = "test_uuid"
    assert config.validate()


def test_load_config_from_file():
    """Test loading configuration from .env file"""
    # Create temporary .env file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write("CYBERWAVE_TOKEN=file_token\n")
        f.write("CYBERWAVE_TWIN_UUID=file_uuid\n")
        f.write("CYBERWAVE_EDGE_UUID=file_device\n")
        f.write("# This is a comment\n")
        f.write("CAMERA_ID=2\n")
        temp_file = Path(f.name)

    try:
        config = load_config(temp_file)
        assert config.cyberwave_token == "file_token"
        assert config.twin_uuid == "file_uuid"
        assert config.device_id == "file_device"
        assert config.camera_id == 2
    finally:
        temp_file.unlink()


def test_load_config_missing_file():
    """Test loading configuration when .env file doesn't exist"""
    os.environ["CYBERWAVE_TOKEN"] = "env_token"
    os.environ["CYBERWAVE_TWIN_UUID"] = "env_uuid"

    try:
        # Should not raise, just use environment variables
        config = load_config(Path("nonexistent.env"))
        assert config.cyberwave_token == "env_token"
        assert config.twin_uuid == "env_uuid"
    finally:
        del os.environ["CYBERWAVE_TOKEN"]
        del os.environ["CYBERWAVE_TWIN_UUID"]


def test_load_config_validation_error():
    """Test that load_config raises on invalid configuration"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write("# Empty config - should fail validation\n")
        temp_file = Path(f.name)

    try:
        with pytest.raises(ValueError, match="Invalid configuration"):
            load_config(temp_file)
    finally:
        temp_file.unlink()
