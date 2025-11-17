import time

from .command_executor import CommandExecutor, CommandResult


class PipeWireController:
    """Control PipeWire/PulseAudio"""

    def __init__(self):
        self.executor = CommandExecutor()

    def list_sources(self) -> CommandResult:
        """Get list of audio sources"""
        return self.executor.run("pactl list sources")

    def list_modules(self) -> CommandResult:
        """Get list of loaded modules"""
        return self.executor.run("pactl list modules short")

    def load_loopback(
        self, source: str, sink: str, latency_ms: int = 20
    ) -> CommandResult:
        """Load loopback module"""
        cmd = f"pactl load-module module-loopback source={source} sink={sink} latency_msec={latency_ms}"
        return self.executor.run(cmd)

    def unload_module(self, module_id: str) -> CommandResult:
        """Unload module"""
        return self.executor.run(f"pactl unload-module {module_id}")

    def get_default_sink(self) -> CommandResult:
        """Get default sink"""
        return self.executor.run("pactl get-default-sink")

    def restart_pipewire(self) -> CommandResult:
        """Restart PipeWire service"""
        result = self.executor.run(
            "systemctl --user restart pipewire pipewire-pulse wireplumber"
        )
        if result.success:
            time.sleep(3)
        return result
