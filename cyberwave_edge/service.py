"""
Main service for Cyberwave Edge
"""

import asyncio
import logging
import signal
import sys
import time
from pathlib import Path
from typing import Any, Optional

from cyberwave import Cyberwave  # type: ignore[import-untyped]
from cyberwave.utils import TimeReference  # type: ignore[import-untyped]

from .config import EdgeConfig, load_config

logger = logging.getLogger(__name__)


class EdgeService:
    """
    Main edge service that connects to Cyberwave and handles MQTT commands
    """

    def __init__(self, config: EdgeConfig):
        self.config = config
        self.running = False
        self.start_time = time.time()
        self.client: Cyberwave | None = None
        self.video_stream: Optional[Any] = None
        self.event_loop: Optional[asyncio.AbstractEventLoop] = None
        self._video_operation_lock = asyncio.Lock()

    async def connect(self):
        """Connect to Cyberwave backend and MQTT broker"""
        self.client = Cyberwave(
            token=self.config.cyberwave_token,
            base_url=self.config.cyberwave_base_url,
            mqtt_host=self.config.mqtt_host,
            mqtt_port=self.config.mqtt_port,
            mqtt_username=self.config.mqtt_username,
            mqtt_password=self.config.mqtt_password,
        )

        if not self.client.mqtt.connected:
            self.client.mqtt.connect()
        
        await self._subscribe_to_commands()

    async def run(self):
        """Run the edge service"""
        self.running = True
        self.event_loop = asyncio.get_running_loop()

        try:
            await self.connect()
            await asyncio.sleep(3)
            logger.info("Edge service is running. Press Ctrl+C to stop.")

            while self.running:
                await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"Error in edge service: {e}", exc_info=True)
            raise
        finally:
            await self.shutdown()

    async def _subscribe_to_commands(self):
        """
        Subscribe to command messages from the backend.
        
        Expected MQTT Command Message Format:
        -------------------------------------
        Message Payload (JSON):
        {
            "command": "start_video" | "stop_video",  # Required: command type
            "timestamp": 1234567890.123               # Optional: Unix timestamp
        }
        
        Supported Commands:
        - "start_video": Starts the video stream for the twin
        - "stop_video": Stops the video stream for the twin
        
        The MQTT client automatically parses JSON messages, so the handler
        receives a Python dictionary.
        """
        if not self.client or not self.config.twin_uuid:
            logger.error("Client or twin_uuid not available for command subscription")
            return
        
        def on_command_message(data):
            """Handle incoming command messages."""
            try:
                payload = data if isinstance(data, dict) else {}
                
                if "status" in payload:
                    return
                
                command_type = payload.get("command")
                
                if not command_type:
                    logger.warning("Command message missing command field")
                    return
                
                if self.event_loop is None:
                    logger.error("Event loop not available, cannot process command")
                    return
                
                if command_type == "start_video":
                    asyncio.run_coroutine_threadsafe(
                        self._handle_start_video_command(), self.event_loop
                    )
                elif command_type == "stop_video":
                    asyncio.run_coroutine_threadsafe(
                        self._handle_stop_video_command(), self.event_loop
                    )
                else:
                    logger.warning(f"Unknown command type: {command_type}")
                    
            except Exception as e:
                logger.error(f"Error processing command message: {e}", exc_info=True)
        
        self.client.mqtt.subscribe_command_message(self.config.twin_uuid, on_command_message)
    
    async def _handle_start_video_command(self):
        """Handle start_video command"""
        if not self.client:
            logger.error("Client not available")
            return
        
        async with self._video_operation_lock:
            try:
                video_already_running = (
                    hasattr(self, "video_stream") and self.video_stream is not None
                )
                
                if not video_already_running:
                    await self.start_video_stream()
                
                self.client.mqtt.publish_command_message(self.config.twin_uuid, "ok")
                
            except Exception as e:
                logger.error(f"Error handling start_video command: {e}", exc_info=True)
                if self.client:
                    self.client.mqtt.publish_command_message(self.config.twin_uuid, "error")
    
    async def _handle_stop_video_command(self):
        """Handle stop_video command"""
        if not self.client:
            logger.error("Client not available")
            return
        
        async with self._video_operation_lock:
            try:
                video_was_running = (
                    hasattr(self, "video_stream") and self.video_stream is not None
                )
                
                if video_was_running:
                    await self.stop_video_stream()
                
                self.client.mqtt.publish_command_message(self.config.twin_uuid, "ok")
                
            except Exception as e:
                logger.error(f"Error handling stop_video command: {e}", exc_info=True)
                if self.client:
                    self.client.mqtt.publish_command_message(self.config.twin_uuid, "error")

    async def start_video_stream(self):
        """Start the video stream"""
        if not self.client:
            logger.error("Client not connected")
            raise RuntimeError("Client not connected")
        
        if self.video_stream is not None:
            try:
                await self.stop_video_stream()
            except Exception as e:
                logger.error(f"Error stopping existing stream: {e}", exc_info=True)
        
        video_stream = None
        try:
            # Create a TimeReference for frame timestamping
            time_reference = TimeReference()
            
            video_stream = self.client.video_stream(
                twin_uuid=self.config.twin_uuid,
                camera_id=self.config.camera_id or 0,
                fps=self.config.camera_fps or 20,
                time_reference=time_reference,
            )
            
            await video_stream.start()
            self.video_stream = video_stream
            await self._setup_frame_monitoring(video_stream)
        except Exception as e:
            logger.error(f"Error starting video stream: {e}", exc_info=True)
            if video_stream is not None:
                try:
                    await video_stream.stop()
                except Exception as cleanup_error:
                    logger.error(f"Error during cleanup: {cleanup_error}", exc_info=True)
            self.video_stream = None
            raise 

    async def _setup_frame_monitoring(self, video_stream):
        """Set up monitoring and logging for video frame publishing"""
        try:
            if hasattr(video_stream, 'pc') and video_stream.pc:
                pc = video_stream.pc
                
                @pc.on("connectionstatechange")
                def on_connection_state_change():
                    state = pc.connectionState
                    if state == "failed":
                        logger.error("WebRTC connection failed")
                
                @pc.on("iceconnectionstatechange")
                def on_ice_connection_state_change():
                    state = pc.iceConnectionState
                    if state == "failed":
                        logger.error("ICE connection failed - check TURN/STUN servers")
                
                senders = pc.getSenders()
                if senders:
                    for sender in senders:
                        if sender.track and sender.track.readyState == "live":
                            logger.debug(f"Video track active: {sender.track.id}")
                
                if hasattr(video_stream, 'streamer') and video_stream.streamer:
                    streamer = video_stream.streamer
                    if hasattr(streamer, 'frame_count'):
                        asyncio.create_task(self._log_frame_count_periodically(streamer))
        except Exception as e:
            logger.warning(f"Error setting up frame monitoring: {e}")
    
    async def _log_frame_count_periodically(self, streamer):
        """Periodically log frame count to verify frames are being sent"""
        try:
            last_count = 0
            while self.running and self.video_stream is not None:
                await asyncio.sleep(5)
                
                if hasattr(streamer, 'frame_count'):
                    current_count = streamer.frame_count
                    frames_sent = current_count - last_count
                    if frames_sent > 0:
                        logger.debug(f"Video frames: {frames_sent} in last 5s (total: {current_count})")
                    else:
                        logger.warning(f"No frames sent in last 5 seconds (total: {current_count})")
                    last_count = current_count
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in frame count monitoring: {e}")

    async def stop_video_stream(self):
        """Stop the video stream"""
        if self.video_stream is not None:
            stream_to_stop = self.video_stream
            self.video_stream = None
            
            try:
                if hasattr(stream_to_stop, 'pc') and stream_to_stop.pc:
                    try:
                        await stream_to_stop.pc.close()
                        await asyncio.sleep(0.2)
                    except Exception as pc_error:
                        logger.warning(f"Error closing peer connection: {pc_error}")
                
                if hasattr(stream_to_stop, 'streamer') and stream_to_stop.streamer:
                    try:
                        stream_to_stop.streamer.close()
                    except Exception as streamer_error:
                        logger.warning(f"Error closing streamer: {streamer_error}")

                try:
                    await stream_to_stop.stop()
                except Exception as e:
                    logger.error(f"Error stopping stream: {e}")
                
            except Exception as e:
                logger.error(f"Error stopping video stream: {e}", exc_info=True)
                try:
                    if hasattr(stream_to_stop, 'streamer') and stream_to_stop.streamer:
                        if hasattr(stream_to_stop.streamer, 'release'):
                            stream_to_stop.streamer.release()
                except Exception as cleanup_error:
                    logger.error(f"Error during cleanup: {cleanup_error}")

    async def shutdown(self):
        """Shutdown the edge service gracefully"""
        self.running = False

        if hasattr(self, "video_stream") and self.video_stream:
            await self.stop_video_stream()

        if self.client and self.client.mqtt:
            try:
                self.client.mqtt.disconnect()
            except Exception as e:
                logger.error(f"Error disconnecting from MQTT: {e}")
            
            if hasattr(self.client, "disconnect"):
                try:
                    self.client.disconnect()
                except Exception as e:
                    logger.error(f"Error disconnecting from Cyberwave client: {e}")


async def async_main():
    """Async main entry point for the edge service"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("./logs/cyberwave-edge.log")
            if Path("./logs").exists()
            else logging.NullHandler(),
        ],
    )

    logger.info("Starting Cyberwave Edge Python service...")

    try:
        config = load_config()
        logger.info(f"Configuration loaded for edge device: {config.edge_uuid}")
        logging.getLogger().setLevel(getattr(logging, config.log_level.upper()))

        service = EdgeService(config)

        def signal_handler(sig, frame):
            logger.info(f"Received signal {sig}, initiating shutdown...")
            service.running = False

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        await service.run()

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


def main():
    """Main entry point wrapper for CLI"""
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
