import threading

import flet as ft
from core.connector import DeepFilterConnector


class MainWindow:
    """Main application window"""

    def __init__(self, page: ft.Page):
        self.page = page
        self.connector = DeepFilterConnector()
        self.test_loopback_id = None

        self.page.title = "DeepFilterNet Microphone Connector"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.padding = 20
        self.page.window.width = 850
        self.page.window.height = 750
        self.page.window.min_width = 650
        self.page.window.min_height = 550

        self._create_components()

    def _create_components(self):
        """Create UI components"""
        self.title = ft.Text(
            "DeepFilterNet Microphone Connector",
            size=24,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.BLUE_200,
        )

        self.status_text = ft.Text("Ready to connect", color=ft.Colors.GREEN_200)
        self.progress_bar = ft.ProgressBar(visible=False, width=400)

        self.devices_dropdown = ft.Dropdown(
            label="Select microphone", options=[], width=400
        )

        # Buttons
        self.connect_btn = ft.ElevatedButton(
            text="Connect to Noise Suppression",
            icon=ft.Icons.CONNECT_WITHOUT_CONTACT,
            on_click=lambda _: self._connect_mic(),
            style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=ft.Colors.GREEN_600),
        )

        self.disconnect_btn = ft.ElevatedButton(
            text="Disconnect",
            icon=ft.Icons.LINK_OFF,
            on_click=lambda _: self._disconnect_mic(),
            style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=ft.Colors.RED_600),
            disabled=True,
        )

        self.test_btn = ft.ElevatedButton(
            text="Real-time Test",
            icon=ft.Icons.HEARING,
            on_click=lambda _: self._toggle_monitoring(),
            style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=ft.Colors.BLUE_600),
            disabled=True,
        )

        self.refresh_btn = ft.ElevatedButton(
            text="Refresh Devices",
            icon=ft.Icons.REFRESH,
            on_click=lambda _: self._refresh_devices(),
            style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=ft.Colors.ORANGE_600),
        )

        self.attenuation_value_text = ft.Text(
            f"Attenuation Limit: {self.connector.settings.noise_attenuation} dB",
            size=14,
            color=ft.Colors.BLUE_200,
        )

        self.noise_attenuation_slider = ft.Slider(
            min=0.0,
            max=100.0,
            value=self.connector.settings.noise_attenuation,
            divisions=100,
            label="{value} dB",
            on_change=lambda e: self._update_attenuation(e.control.value),
        )

        self.apply_settings_btn = ft.ElevatedButton(
            text="Apply Settings (PipeWire Restart)",
            icon=ft.Icons.SETTINGS_APPLICATIONS,
            on_click=lambda _: self._apply_settings(),
            style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=ft.Colors.PURPLE_600),
            width=400,
        )

        self.devices_info = ft.TextField(
            label="Available devices",
            multiline=True,
            min_lines=8,
            max_lines=10,
            read_only=True,
            border_color=ft.Colors.BLUE_GREY_400,
        )

    def _show_snackbar(self, message: str, color=ft.Colors.BLUE_200):
        """Show snackbar notification"""
        self.page.snack_bar = ft.SnackBar(ft.Text(message), bgcolor=color)
        self.page.snack_bar.open = True
        self.page.update()

    def _update_attenuation(self, value: float):
        """Update attenuation value"""
        self.connector.settings.noise_attenuation = round(value, 1)
        self.attenuation_value_text.value = (
            f"Attenuation Limit: {self.connector.settings.noise_attenuation} dB"
        )
        self.page.update()

    def _refresh_devices(self):
        """Refresh device list"""
        self.progress_bar.visible = True
        self.status_text.value = "Updating device list..."
        self.page.update()

        def do_refresh():
            devices = self.connector.get_devices()
            self.page.run_thread(lambda: self._on_devices_refreshed(devices))

        threading.Thread(target=do_refresh, daemon=True).start()

    def _on_devices_refreshed(self, devices):
        """Handle refreshed devices"""
        self.progress_bar.visible = False

        if devices:
            self.devices_dropdown.options = [
                ft.dropdown.Option(device.display) for device in devices
            ]

            connected_source = self.connector.check_existing_connection()

            if connected_source:
                for device in devices:
                    if device.name == connected_source:
                        self.devices_dropdown.value = device.display
                        self.status_text.value = f"Connected: {device.display}"
                        self.status_text.color = ft.Colors.GREEN_200
                        self.connect_btn.disabled = True
                        self.disconnect_btn.disabled = False
                        self.test_btn.disabled = False
                        break
            else:
                if devices:
                    self.devices_dropdown.value = devices[0].display
                self.status_text.value = "Ready to connect"
                self.status_text.color = ft.Colors.GREEN_200
                self.connect_btn.disabled = False
                self.disconnect_btn.disabled = True
                self.test_btn.disabled = True

            self.devices_info.value = "\n".join([f"• {d.display}" for d in devices])
        else:
            self.status_text.value = "Error getting devices"
            self.status_text.color = ft.Colors.RED_200
            self._show_snackbar("Failed to get device list", ft.Colors.RED_400)

        self.page.update()

    def _connect_mic(self):
        """Connect microphone"""
        if not self.devices_dropdown.value:
            self._show_snackbar("Select microphone from list", ft.Colors.RED_400)
            return

        device = self.connector.device_manager.find_device_by_display(
            self.devices_dropdown.value
        )
        if not device:
            self._show_snackbar("Device not found", ft.Colors.RED_400)
            return

        self.progress_bar.visible = True
        self.status_text.value = "Connecting..."
        self.page.update()

        def do_connect():
            success, message = self.connector.connect_microphone(device)
            self.page.run_thread(
                lambda: self._on_connect_complete(success, message, device)
            )

        threading.Thread(target=do_connect, daemon=True).start()

    def _on_connect_complete(self, success, message, device):
        """Handle connection complete"""
        self.progress_bar.visible = False

        if success:
            self.status_text.value = f"Connected: {device.display}"
            self.status_text.color = ft.Colors.GREEN_200
            self.connect_btn.disabled = True
            self.disconnect_btn.disabled = False
            self.test_btn.disabled = False
            self._show_snackbar("Successfully connected", ft.Colors.GREEN_400)
        else:
            self.status_text.value = "Connection error"
            self.status_text.color = ft.Colors.RED_200
            self._show_snackbar(f"Error: {message}", ft.Colors.RED_400)

        self.page.update()

    def _disconnect_mic(self):
        """Disconnect microphone"""
        self.progress_bar.visible = True
        self.status_text.value = "Disconnecting..."
        self.page.update()

        def do_disconnect():
            if self.test_loopback_id:
                self.connector.stop_monitoring(self.test_loopback_id)

            success, message = self.connector.disconnect_microphone()
            self.page.run_thread(lambda: self._on_disconnect_complete(success, message))

        threading.Thread(target=do_disconnect, daemon=True).start()

    def _on_disconnect_complete(self, success, message):
        """Handle disconnection complete"""
        self.progress_bar.visible = False

        if success:
            self.status_text.value = "Ready to connect"
            self.status_text.color = ft.Colors.GREEN_200
            self.connect_btn.disabled = False
            self.disconnect_btn.disabled = True
            self.test_btn.disabled = True
            self.test_loopback_id = None
            self._show_snackbar(message, ft.Colors.BLUE_400)
        else:
            self.status_text.value = "Disconnection error"
            self.status_text.color = ft.Colors.RED_200
            self._show_snackbar(f"Error: {message}", ft.Colors.RED_400)

        self.page.update()

    def _apply_settings(self):
        """Apply settings"""
        self.progress_bar.visible = True
        self.status_text.value = "Applying settings..."
        self.page.update()

        def do_apply():
            success, message = self.connector.apply_settings()
            self.page.run_thread(lambda: self._on_settings_applied(success, message))

        threading.Thread(target=do_apply, daemon=True).start()

    def _on_settings_applied(self, success, message):
        """Handle settings applied"""
        self.progress_bar.visible = False

        if success:
            self._show_snackbar(message, ft.Colors.GREEN_400)
            self._refresh_devices()
        else:
            self.status_text.value = "Error applying settings"
            self.status_text.color = ft.Colors.RED_200
            self._show_snackbar(f"Error: {message}", ft.Colors.RED_400)

        self.page.update()

    def _toggle_monitoring(self):
        """Toggle monitoring"""
        if self.test_loopback_id:
            self._stop_monitoring()
        else:
            self._start_monitoring()

    def _start_monitoring(self):
        """Start monitoring"""
        if not self.connector.current_loopback_id:
            self._show_snackbar("First connect microphone", ft.Colors.ORANGE_400)
            return

        self.progress_bar.visible = True
        self.status_text.value = "Starting monitoring..."
        self.page.update()

        def do_start():
            success, result = self.connector.start_monitoring()
            self.page.run_thread(lambda: self._on_monitoring_start(success, result))

        threading.Thread(target=do_start, daemon=True).start()

    def _on_monitoring_start(self, success, result):
        """Handle monitoring started"""
        self.progress_bar.visible = False

        if success:
            self.test_loopback_id = result
            self.status_text.value = "Monitoring in progress..."
            self.status_text.color = ft.Colors.BLUE_200
            self.test_btn.text = "Stop Test"
            self.test_btn.icon = ft.Icons.STOP
            self._show_snackbar("Monitoring started", ft.Colors.GREEN_400)
        else:
            self.status_text.value = "Error starting monitoring"
            self.status_text.color = ft.Colors.RED_200
            self._show_snackbar(f"Error: {result}", ft.Colors.RED_400)

        self.page.update()

    def _stop_monitoring(self):
        """Stop monitoring"""
        self.progress_bar.visible = True
        self.status_text.value = "Stopping monitoring..."
        self.page.update()

        def do_stop():
            success, message = self.connector.stop_monitoring(self.test_loopback_id)
            self.page.run_thread(lambda: self._on_monitoring_stop(success, message))

        threading.Thread(target=do_stop, daemon=True).start()

    def _on_monitoring_stop(self, success, message):
        """Handle monitoring stopped"""
        self.progress_bar.visible = False

        if success:
            self.test_loopback_id = None
            self.status_text.value = f"Connected: {self.devices_dropdown.value}"
            self.status_text.color = ft.Colors.GREEN_200
            self.test_btn.text = "Real-time Test"
            self.test_btn.icon = ft.Icons.HEARING
            self._show_snackbar("Monitoring stopped", ft.Colors.BLUE_400)
        else:
            self.status_text.value = "Error stopping monitoring"
            self.status_text.color = ft.Colors.RED_200
            self._show_snackbar(f"Error: {message}", ft.Colors.RED_400)

        self.page.update()

    def initialize(self):
        """Initialize and build UI"""
        # Build layout
        header = ft.Container(
            content=ft.Column(
                [self.title, ft.Row([self.status_text, self.progress_bar])]
            ),
            padding=10,
        )

        controls_row = ft.Row([self.devices_dropdown])

        buttons_row1 = ft.Row(
            [
                self.connect_btn,
                self.disconnect_btn,
                self.test_btn,
            ]
        )

        buttons_row2 = ft.Row([self.refresh_btn])

        settings_card = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text(
                            "Noise Suppression Settings",
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.BLUE_200,
                        ),
                        ft.Divider(height=1, thickness=1),
                        self.attenuation_value_text,
                        self.noise_attenuation_slider,
                        ft.Text(
                            "0 dB = minimal, 100 dB = maximum suppression",
                            size=11,
                            color=ft.Colors.GREY_400,
                        ),
                        ft.Container(height=10),
                        self.apply_settings_btn,
                        ft.Text(
                            "Settings require PipeWire restart.\n"
                            "Connection will be restored automatically.",
                            size=11,
                            color=ft.Colors.GREY_400,
                            italic=True,
                        ),
                    ]
                ),
                padding=15,
            ),
            elevation=2,
        )

        main_column = ft.Column(
            [
                header,
                controls_row,
                buttons_row1,
                buttons_row2,
                settings_card,
                self.devices_info,
            ],
            spacing=15,
        )

        self.page.add(main_column)

        # Auto-refresh on startup
        self._refresh_devices()
