"""Main Anova Bluetooth LE client."""

import asyncio
import logging
from typing import Optional

try:
    from bleak import BleakClient, BleakScanner
    from bleak.backends.characteristic import BleakGATTCharacteristic
except ImportError as err:
    raise ImportError("Please install bleak: pip install bleak") from err

from .constants import (
    CHARACTERISTIC_UUID,
    DEVICE_NAME,
    MAX_COMMAND_LENGTH,
    MAX_RETRY_ATTEMPTS,
    MAX_TEMPERATURE,
    MAX_TIMER,
    MIN_TEMPERATURE,
    MIN_TIMER,
    RESPONSE_TIMEOUT,
    RETRY_DELAY,
)
from .exceptions import (
    AnovaCommandError,
    AnovaConnectionError,
    AnovaTimeoutError,
    AnovaValidationError,
)


class AnovaBLE:
    """Anova Precision Cooker Bluetooth LE client."""

    def __init__(self, mac_address: Optional[str] = None):
        """Initialize the Anova client.

        Args:
            mac_address: MAC address of the Anova device. If None, will auto-discover.
        """
        self.mac_address = mac_address
        self.client: Optional[BleakClient] = None
        self.characteristic: Optional[BleakGATTCharacteristic] = None
        self._response_buffer = ""
        self._response_event = asyncio.Event()
        self._last_response = ""
        self._connected = False

        # Setup logging
        self.logger = logging.getLogger(__name__)

    async def discover_device(self) -> Optional[str]:
        """Discover Anova device and return MAC address.

        Returns:
            MAC address of discovered device, or None if not found.

        Raises:
            AnovaConnectionError: If scanning fails.
        """
        self.logger.info("Scanning for Anova devices...")

        try:
            devices = await BleakScanner.discover()
            for device in devices:
                if device.name == DEVICE_NAME:
                    self.logger.info("Found Anova device: %s", device.address)
                    return str(device.address)

            self.logger.warning("No Anova device found")
            return None
        except Exception as e:
            raise AnovaConnectionError(f"Failed to scan for devices: {e}") from e

    async def connect(self) -> bool:
        """Connect to Anova device.

        Returns:
            True if connection successful, False otherwise.

        Raises:
            AnovaConnectionError: If connection fails.
        """
        if not self.mac_address:
            self.mac_address = await self.discover_device()
            if not self.mac_address:
                return False

        try:
            self.logger.info("Connecting to %s", self.mac_address)
            self.client = BleakClient(self.mac_address)
            await self.client.connect()

            # Find the characteristic
            self.characteristic = self.client.services.get_characteristic(
                CHARACTERISTIC_UUID
            )
            if not self.characteristic:
                self.logger.error("Failed to find Anova characteristic")
                await self.disconnect()
                raise AnovaConnectionError("Failed to find Anova characteristic")

            # Start notifications
            await self.client.start_notify(
                self.characteristic, self._notification_handler
            )
            self._connected = True
            self.logger.info("Successfully connected to Anova")
            return True

        except Exception as e:
            self.logger.error("Connection failed: %s", e)
            await self.disconnect()
            raise AnovaConnectionError(f"Connection failed: {e}") from e

    async def disconnect(self) -> None:
        """Disconnect from device."""
        if self.client and self.client.is_connected:
            await self.client.disconnect()
        self._connected = False
        self.logger.info("Disconnected from Anova")

    def _notification_handler(
        self, _characteristic: BleakGATTCharacteristic, data: bytearray
    ) -> None:
        """Handle notifications from device."""
        response = data.decode("ascii")
        self._response_buffer += response

        # Check if we have a complete response (ends with \r)
        if "\r" in self._response_buffer:
            self._last_response = self._response_buffer.split("\r")[0]
            self._response_buffer = ""
            self._response_event.set()

    async def _send_command(self, command: str) -> str:
        """Send command and wait for response.

        Args:
            command: Command to send to device.

        Returns:
            Response from device.

        Raises:
            AnovaConnectionError: If not connected to device.
            AnovaCommandError: If command is invalid.
            AnovaTimeoutError: If command times out.
        """
        if not self._connected or not self.client or not self.characteristic:
            raise AnovaConnectionError("Not connected to device")

        # Add carriage return terminator
        full_command = command + "\r"

        # Commands must be max 20 bytes
        if len(full_command.encode()) > MAX_COMMAND_LENGTH:
            raise AnovaCommandError(f"Command too long: {command}")

        self.logger.debug("Sending command: %s", command)

        # Clear previous response
        self._response_event.clear()
        self._last_response = ""

        # Send command
        await self.client.write_gatt_char(self.characteristic, full_command.encode())

        # Wait for response with timeout
        try:
            await asyncio.wait_for(
                self._response_event.wait(), timeout=RESPONSE_TIMEOUT
            )
            self.logger.debug("Received response: %s", self._last_response)
            return self._last_response
        except asyncio.TimeoutError as e:
            self.logger.error("Timeout waiting for response to: %s", command)
            raise AnovaTimeoutError(
                f"Timeout waiting for response to: {command}"
            ) from e

    async def _send_command_with_retry(self, command: str) -> str:
        """Send command with retry logic for improved reliability.

        Args:
            command: Command to send to device.

        Returns:
            Response from device.

        Raises:
            AnovaConnectionError: If not connected to device.
            AnovaCommandError: If command is invalid.
            AnovaTimeoutError: If command times out after all retries.
        """
        last_exception = None

        for attempt in range(MAX_RETRY_ATTEMPTS):
            try:
                response = await self._send_command(command)

                return response

            except AnovaTimeoutError as e:
                last_exception = e
                if attempt < MAX_RETRY_ATTEMPTS - 1:
                    self.logger.warning(
                        "Command '%s' timed out on attempt %d, retrying...",
                        command,
                        attempt + 1,
                    )
                    await asyncio.sleep(RETRY_DELAY)
                    continue
                break

        raise AnovaTimeoutError(
            f"Command '{command}' failed after {MAX_RETRY_ATTEMPTS} attempts: {last_exception}"
        )

    # Status and control methods
    async def get_status(self) -> str:
        """Get device status."""
        return await self._send_command("status")

    async def start_cooking(self) -> str:
        """Start cooking."""
        return await self._send_command_with_retry("start")

    async def stop_cooking(self) -> str:
        """Stop cooking."""
        return await self._send_command_with_retry("stop")

    # Temperature methods
    async def set_temperature(self, temp: float) -> str:
        """Set target temperature (Celsius).

        Args:
            temp: Target temperature in Celsius.

        Returns:
            Response from device.

        Raises:
            AnovaValidationError: If temperature is out of range.
        """
        if not MIN_TEMPERATURE <= temp <= MAX_TEMPERATURE:
            raise AnovaValidationError(
                f"Temperature must be between {MIN_TEMPERATURE} and {MAX_TEMPERATURE}°C"
            )
        return await self._send_command_with_retry(f"set temp {temp:.1f}")

    async def get_temperature(self) -> str:
        """Get current temperature."""
        return await self._send_command("read temp")

    async def get_target_temperature(self) -> str:
        """Get target temperature."""
        return await self._send_command("read set temp")

    # Timer methods
    async def set_timer(self, minutes: int, auto_start: bool = True) -> str:
        """Set timer in minutes and optionally start it automatically.

        Args:
            minutes: Timer duration in minutes.
            auto_start: Whether to automatically start the timer after setting it.

        Returns:
            Response from device.

        Raises:
            AnovaValidationError: If timer value is out of range.
            AnovaCommandError: If timer setting failed verification.
        """
        if not MIN_TIMER <= minutes <= MAX_TIMER:
            raise AnovaValidationError(
                f"Timer must be between {MIN_TIMER} and {MAX_TIMER} minutes"
            )

        # Set the timer
        response = await self._send_command_with_retry(f"set timer {minutes}")
        self.logger.info("Timer set to %d minutes", minutes)

        # Check if cooker is running first
        status = await self.get_status()
        if status.lower() != "running" and auto_start:
            await self.start_cooking()
            self.logger.info("Cooker started for timer auto-start")

        # Start the timer
        try:
            start_response = await self.start_timer()
            self.logger.info("Timer started: %s", start_response)

            # Verify timer is now readable
            await asyncio.sleep(0.5)
            timer_status = await self.get_timer()
            self.logger.info("Timer verification after start: %s", timer_status)

            return f"{response}; Timer started: {start_response}"
        except (AnovaConnectionError, AnovaCommandError, AnovaTimeoutError) as e:
            self.logger.warning("Failed to start timer: %s", e)
            return f"{response}; Warning: Could not start timer"

    async def get_timer(self) -> str:
        """Get timer status."""
        # Check if cooker is running first - timer is only available when running
        status = await self.get_status()
        if status.lower() != "running":
            raise AnovaCommandError("Timer status unavailable - cooker is not running")

        return await self._send_command_with_retry("read timer")

    async def start_timer(self) -> str:
        """Start timer."""
        return await self._send_command_with_retry("start time")

    async def stop_timer(self) -> str:
        """Stop timer."""
        return await self._send_command_with_retry("stop time")

    # Unit methods
    async def get_unit(self) -> str:
        """Get temperature unit."""
        return await self._send_command("read unit")

    async def set_unit_celsius(self) -> str:
        """Set temperature unit to Celsius."""
        return await self._send_command_with_retry("set unit c")

    async def set_unit_fahrenheit(self) -> str:
        """Set temperature unit to Fahrenheit."""
        return await self._send_command_with_retry("set unit f")

    # Network/WiFi configuration methods
    async def get_device_id(self) -> str:
        """Get device ID card for network authentication."""
        return await self._send_command("get id card")

    async def get_version(self) -> str:
        """Get device firmware version."""
        return await self._send_command("version")

    async def set_device_name(self, name: str) -> str:
        """Set device name.

        Args:
            name: Device name to set.

        Returns:
            Response from device.
        """
        return await self._send_command_with_retry(f"set name {name}")

    async def set_secret_key(self, key: str) -> str:
        """Set device secret key for network authentication.

        Args:
            key: Secret key for device authentication.

        Returns:
            Response from device.
        """
        return await self._send_command_with_retry(f"set number {key}")

    async def start_smartlink(self) -> str:
        """Start WiFi smartlink setup mode.

        Returns:
            Response from device.
        """
        return await self._send_command_with_retry("smartlink start")

    async def configure_server(self, ip: str, port: int = 8080) -> str:
        """Configure server parameters for network communication.

        Args:
            ip: Server IP address.
            port: Server port (default 8080).

        Returns:
            Response from device.
        """
        return await self._send_command_with_retry(f"server para {ip} {port}")

    async def configure_wifi(self, ssid: str, password: str) -> str:
        """Configure WiFi network settings.

        Args:
            ssid: WiFi network name.
            password: WiFi network password.

        Returns:
            Response from device.

        Note:
            This uses WPA2PSK AES security by default.
        """
        return await self._send_command_with_retry(
            f"wifi para 2 {ssid} {password} WPA2PSK AES"
        )

    # Additional utility methods
    async def set_speaker_off(self) -> str:
        """Disable device speaker."""
        return await self._send_command_with_retry("set speaker off")

    async def clear_alarm(self) -> str:
        """Clear timer alarm."""
        return await self._send_command_with_retry("clear alarm")

    async def get_date(self) -> str:
        """Get device date/time."""
        return await self._send_command("read date")

    async def set_date(self, date: str) -> str:
        """Set device date/time.

        Args:
            date: Date/time string to set.

        Returns:
            Response from device.
        """
        return await self._send_command_with_retry(f"set date {date}")

    async def get_calibration(self) -> str:
        """Get temperature calibration offset."""
        return await self._send_command("read cal")

    async def set_calibration(self, offset: float) -> str:
        """Set temperature calibration offset.

        Args:
            offset: Calibration offset in degrees.

        Returns:
            Response from device.
        """
        return await self._send_command_with_retry(f"cal {offset:.1f}")

    async def set_led_color(self, red: int, green: int, blue: int) -> str:
        """Set LED color (if supported by device).

        Args:
            red: Red value (0-255).
            green: Green value (0-255).
            blue: Blue value (0-255).

        Returns:
            Response from device.
        """
        return await self._send_command_with_retry(f"set led {red} {green} {blue}")

    async def get_extended_data(self) -> str:
        """Get extended device data/status."""
        return await self._send_command("read data")
