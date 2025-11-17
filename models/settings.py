import os
from dataclasses import dataclass


@dataclass
class Settings:
    """DeepFilterNet settings"""

    noise_attenuation: float = 100.0
    config_path: str = os.path.expanduser(
        "~/.config/pipewire/pipewire.conf.d/99-deepfilter.conf"
    )
    ladspa_path: str = os.path.expanduser("~/.ladspa/libdeep_filter_ladspa.so")
