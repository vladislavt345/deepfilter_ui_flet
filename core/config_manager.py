import os

from models.settings import Settings


class ConfigManager:
    """Manage PipeWire configuration"""

    def __init__(self, settings: Settings):
        self.settings = settings

    def update_config(self) -> bool:
        """Update PipeWire configuration file"""
        try:
            config_content = f"""context.modules = [
  {{   name = libpipewire-module-filter-chain
      args = {{
          node.description = "DeepFilter Noise Cancelling"
          media.name       = "DeepFilter Noise Cancelling"
          filter.graph = {{
              nodes = [
                  {{
                      type   = ladspa
                      name   = deep_filter
                      plugin = "{self.settings.ladspa_path}"
                      label  = deep_filter_mono
                      control = {{
                          "Attenuation Limit (dB)" = {self.settings.noise_attenuation}
                      }}
                  }}
              ]
          }}
          audio.rate = 48000
          audio.channels = 1
          audio.position = [ MONO ]
          capture.props = {{
              node.name      = "effect_input.deep_filter"
              media.class    = Audio/Sink
              audio.rate     = 48000
              audio.channels = 1
              stream.capture.sink = true
              node.passive   = true
          }}
          playback.props = {{
              node.name      = "effect_output.deep_filter"
              media.class    = Audio/Source
              audio.rate     = 48000
              audio.channels = 1
          }}
      }}
  }}
]
"""
            os.makedirs(os.path.dirname(self.settings.config_path), exist_ok=True)

            with open(self.settings.config_path, "w") as f:
                f.write(config_content)

            return True
        except Exception as e:
            print(f"Config update error: {e}")
            return False
