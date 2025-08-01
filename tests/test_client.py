"""Tests for the AnovaBLE client."""

from unittest.mock import AsyncMock

import pytest
from anovable import AnovaBLE, AnovaValidationError


class TestAnovaBLE:
    """Test cases for AnovaBLE class."""

    def test_init(self) -> None:
        """Test initialization."""
        client = AnovaBLE()
        assert client.mac_address is None
        assert not client._connected

        client_with_mac = AnovaBLE("AA:BB:CC:DD:EE:FF")
        assert client_with_mac.mac_address == "AA:BB:CC:DD:EE:FF"

    async def test_set_temperature_validation(self) -> None:
        """Test temperature validation."""
        client = AnovaBLE()

        # Test valid temperature
        client._send_command = AsyncMock(return_value="OK")
        client._connected = True
        await client.set_temperature(50.0)

        # Test invalid temperatures
        with pytest.raises(AnovaValidationError):
            await client.set_temperature(4.0)  # Too low

        with pytest.raises(AnovaValidationError):
            await client.set_temperature(100.0)  # Too high

    async def test_set_timer_validation(self) -> None:
        """Test timer validation."""
        client = AnovaBLE()
        client._send_command = AsyncMock(return_value="OK")
        client._connected = True

        # Test valid timer
        await client.set_timer(60)

        # Test invalid timers
        with pytest.raises(AnovaValidationError):
            await client.set_timer(-1)  # Too low

        with pytest.raises(AnovaValidationError):
            await client.set_timer(7000)  # Too high
