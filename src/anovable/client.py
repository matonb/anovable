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
    MAX_TEMPERATURE,
    MAX_TIMER,
    MIN_TEMPERATURE,
    MIN_TIMER,
    RESPONSE_TIMEOUT,
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
                    self.logger.info(f"Found Anova device: {device.address}")
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
            self.logger.info(f"Connecting to {self.mac_address}")
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
            self.logger.error(f"Connection failed: {e}")
            await self.disconnect()
            raise AnovaConnectionError(f"Connection failed: {e}") from e

    async def disconnect(self) -> None:
        """Disconnect from device."""
        if self.client and self.client.is_connected:
            await self.client.disconnect()
        self._connected = False
        self.logger.info("Disconnected from Anova")

    def _notification_handler(
        self, characteristic: BleakGATTCharacteristic, data: bytearray
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

        self.logger.debug(f"Sending command: {command}")

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
            self.logger.debug(f"Received response: {self._last_response}")
            return self._last_response
        except asyncio.TimeoutError as e:
            self.logger.error(f"Timeout waiting for response to: {command}")
            raise AnovaTimeoutError(
                f"Timeout waiting for response to: {command}"
            ) from e

    # Status and control methods
    async def get_status(self) -> str:
        """Get device status."""
        return await self._send_command("status")

    async def start_cooking(self) -> str:
        """Start cooking."""
        return await self._send_command("start")

    async def stop_cooking(self) -> str:
        """Stop cooking."""
        return await self._send_command("stop")

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
        if not (MIN_TEMPERATURE <= temp <= MAX_TEMPERATURE):
            raise AnovaValidationError(
                f"Temperature must be between {MIN_TEMPERATURE} and {MAX_TEMPERATURE}°C"
            )
        return await self._send_command(f"set temp {temp:.1f}")

    async def get_temperature(self) -> str:
        """Get current temperature."""
        return await self._send_command("read temp")

    async def get_target_temperature(self) -> str:
        """Get target temperature."""
        return await self._send_command("read set temp")

    # Timer methods
    async def set_timer(self, minutes: int) -> str:
        """Set timer in minutes.

        Args:
            minutes: Timer duration in minutes.

        Returns:
            Response from device.

        Raises:
            AnovaValidationError: If timer value is out of range.
        """
        if not (MIN_TIMER <= minutes <= MAX_TIMER):
            raise AnovaValidationError(
                f"Timer must be between {MIN_TIMER} and {MAX_TIMER} minutes"
            )
        return await self._send_command(f"set timer {minutes}")

    async def get_timer(self) -> str:
        """Get timer status."""
        return await self._send_command("read timer")

    async def start_timer(self) -> str:
        """Start timer."""
        return await self._send_command("start time")

    async def stop_timer(self) -> str:
        """Stop timer."""
        return await self._send_command("stop time")

    # Unit methods
    async def get_unit(self) -> str:
        """Get temperature unit."""
        return await self._send_command("read unit")

    async def set_unit_celsius(self) -> str:
        """Set temperature unit to Celsius."""
        return await self._send_command("set unit c")

    async def set_unit_fahrenheit(self) -> str:
        """Set temperature unit to Fahrenheit."""
        return await self._send_command("set unit f")
