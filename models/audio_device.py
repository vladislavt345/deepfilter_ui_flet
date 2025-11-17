from dataclasses import dataclass


@dataclass
class AudioDevice:
    """Audio device model"""

    name: str
    description: str

    @property
    def display(self) -> str:
        return self.description
