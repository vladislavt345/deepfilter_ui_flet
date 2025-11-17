import re
from typing import List, Optional

from models.audio_device import AudioDevice
from system.pipewire_controller import PipeWireController


class DeviceManager:
    """Manage audio devices"""

    def __init__(self):
        self.controller = PipeWireController()
        self.devices: List[AudioDevice] = []

    def refresh_devices(self) -> bool:
        """Refresh list of audio devices"""
        result = self.controller.list_sources()
        if not result.success:
            return False

        self.devices = []
        sources = re.split(r"^Source #\d+", result.stdout, flags=re.MULTILINE)

        for source in sources:
            if not source.strip():
                continue

            name_match = re.search(r"Name:\s*(.+)", source)
            desc_match = re.search(r"Description:\s*(.+)", source)

            if name_match and desc_match:
                device_name = name_match.group(1).strip()
                description = desc_match.group(1).strip()

                # Filter out monitors and effect devices
                if (
                    not device_name.startswith("Monitor of")
                    and "effect_" not in device_name
                ):
                    self.devices.append(AudioDevice(device_name, description))

        return True

    def find_device_by_display(self, display: str) -> Optional[AudioDevice]:
        """Find device by display name"""
        for device in self.devices:
            if device.display == display:
                return device
        return None

    def get_devices(self) -> List[AudioDevice]:
        """Get list of devices"""
        return self.devices
