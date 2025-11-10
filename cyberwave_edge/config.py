"""
Configuration management for Cyberwave Edge
"""

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()


@dataclass
class EdgeConfig:
    """
    Configuration for Cyberwave Edge service

    Loads from environment variables or .env file
    """

    # Cyberwave API
    cyberwave_token: Optional[str] = None
    cyberwave_base_url: str = "https://api.cyberwave.com"

    # MQTT
    mqtt_host: Optional[str] = None
    mqtt_port: int = 1883
    mqtt_username: Optional[str] = None
    mqtt_password: Optional[str] = None

    # Device
    edge_uuid: str = "edge-device-001"
    twin_uuid: Optional[str] = None

    # Camera
    camera_id: int = 0
    camera_fps: int = 10

    # Logging
    log_level: str = "INFO"


    def __post_init__(self):
        """Load configuration from environment variables"""
        self.cyberwave_token = os.getenv("CYBERWAVE_TOKEN", self.cyberwave_token)
        self.cyberwave_base_url = os.getenv("CYBERWAVE_BASE_URL", self.cyberwave_base_url)

        self.mqtt_host = os.getenv("CYBERWAVE_MQTT_HOST", self.mqtt_host)
        self.mqtt_port = int(os.getenv("CYBERWAVE_MQTT_PORT", self.mqtt_port))
        self.mqtt_username = os.getenv("CYBERWAVE_MQTT_USERNAME", self.mqtt_username)
        self.mqtt_password = os.getenv("CYBERWAVE_MQTT_PASSWORD", self.mqtt_password)

        self.edge_uuid = os.getenv("CYBERWAVE_EDGE_UUID", self.edge_uuid)
        self.twin_uuid = os.getenv("CYBERWAVE_TWIN_UUID", self.twin_uuid)

        self.camera_id = int(os.getenv("CAMERA_ID", self.camera_id))
        self.camera_fps = int(os.getenv("CAMERA_FPS", self.camera_fps))

        self.log_level = os.getenv("LOG_LEVEL", self.log_level)

        logger.info(f"Configuration loaded: {self}")

    def validate(self) -> bool:
        """Validate required configuration"""
        if not self.cyberwave_token:
            logger.error("CYBERWAVE_TOKEN is required")
            return False

        if not self.twin_uuid:
            logger.error("CYBERWAVE_TWIN_UUID is required")
            return False

        return True


def load_config(env_file: Optional[Path] = None) -> EdgeConfig:
    """
    Load configuration from .env file and environment variables

    Args:
        env_file: Path to .env file (defaults to .env in current directory)

    Returns:
        EdgeConfig instance
    """
    if env_file is None:
        env_file = Path(".env")
    
    # Load .env file if it exists using python-dotenv
    if env_file.exists():
        logger.info(f"Loading configuration from {env_file}")
        load_dotenv(dotenv_path=env_file, override=False)

    env_value = os.getenv("ENVIRONMENT", "").strip()
    if not env_value:
        os.environ["ENVIRONMENT"] = "production"
    else:
        logger.warning(f".env file not found at {env_file}, using environment variables only")

    config = EdgeConfig()

    if not config.validate():
        raise ValueError(
            "Invalid configuration. Please check your .env file or environment variables."
        )

    return config
