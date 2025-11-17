import subprocess
from dataclasses import dataclass
from typing import Tuple


@dataclass
class CommandResult:
    """Result of command execution"""

    stdout: str
    stderr: str
    returncode: int

    @property
    def success(self) -> bool:
        return self.returncode == 0


class CommandExecutor:
    """Execute shell commands"""

    @staticmethod
    def run(cmd: str, timeout: int = 10) -> CommandResult:
        """Execute command and return result"""
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=timeout
            )
            return CommandResult(result.stdout, result.stderr, result.returncode)
        except subprocess.TimeoutExpired:
            return CommandResult("", "Command timed out", 1)
        except Exception as e:
            return CommandResult("", str(e), 1)
