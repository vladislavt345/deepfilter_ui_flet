import re
from typing import Optional, Tuple

from models.audio_device import AudioDevice
from models.settings import Settings
from system.pipewire_controller import PipeWireController

from core.config_manager import ConfigManager
from core.device_manager import DeviceManager


class DeepFilterConnector:
    """Main business logic for DeepFilterNet"""

    def __init__(self):
        self.settings = Settings()
        self.device_manager = DeviceManager()
        self.config_manager = ConfigManager(self.settings)
        self.controller = PipeWireController()
        self.current_loopback_id: Optional[str] = None

    def get_devices(self) -> list:
        """Get list of audio devices"""
        success = self.device_manager.refresh_devices()
        if success:
            return self.device_manager.get_devices()
        return []

    def check_existing_connection(self) -> Optional[str]:
        """Check for existing loopback connection"""
        result = self.controller.list_modules()
        if not result.success:
            return None

        for line in result.stdout.split("\n"):
            if "module-loopback" in line and "sink=effect_input.deep_filter" in line:
                parts = line.split("\t")
                if len(parts) > 2:
                    module_id = parts[0]
                    args = parts[2].split()

                    for arg in args:
                        if arg.startswith("source="):
                            source_name = arg.split("=")[1]
                            self.current_loopback_id = module_id
                            return source_name
        return None

    def connect_microphone(self, device: AudioDevice) -> Tuple[bool, str]:
        """Connect microphone to noise suppression"""
        result = self.controller.load_loopback(
            device.name, "effect_input.deep_filter", 20
        )

        if result.success and result.stdout.strip():
            self.current_loopback_id = result.stdout.strip()
            return True, "Successfully connected"
        return False, result.stderr

    def disconnect_microphone(self) -> Tuple[bool, str]:
        """Disconnect microphone"""
        if not self.current_loopback_id:
            return True, "No active connections"

        result = self.controller.unload_module(self.current_loopback_id)
        if result.success:
            self.current_loopback_id = None
            return True, "Successfully disconnected"
        return False, result.stderr

    def apply_settings(self) -> Tuple[bool, str]:
        """Apply settings with PipeWire restart"""
        was_connected = self.current_loopback_id is not None
        connected_source = None

        if was_connected:
            result = self.controller.list_modules()
            for line in result.stdout.split("\n"):
                if self.current_loopback_id in line and "module-loopback" in line:
                    args = line.split()
                    for arg in args:
                        if arg.startswith("source="):
                            connected_source = arg.split("=")[1]
                            break

            self.disconnect_microphone()

        if not self.config_manager.update_config():
            return False, "Failed to update configuration"

        result = self.controller.restart_pipewire()
        if not result.success:
            return False, f"PipeWire restart error: {result.stderr}"

        if was_connected and connected_source:
            for device in self.device_manager.get_devices():
                if device.name == connected_source:
                    self.connect_microphone(device)
                    break

        return (
            True,
            f"Settings applied: Attenuation Limit = {self.settings.noise_attenuation} dB",
        )

    def start_monitoring(self) -> Tuple[bool, str]:
        """Start real-time monitoring"""
        result = self.controller.get_default_sink()
        if not result.success or not result.stdout.strip():
            return False, "Failed to get default sink"

        default_sink = result.stdout.strip()
        result = self.controller.load_loopback(
            "effect_output.deep_filter", default_sink, 1
        )

        if result.success and result.stdout.strip():
            return True, result.stdout.strip()
        return False, result.stderr

    def stop_monitoring(self, module_id: str) -> Tuple[bool, str]:
        """Stop monitoring"""
        result = self.controller.unload_module(module_id)
        if result.success:
            return True, "Monitoring stopped"
        return False, result.stderr
