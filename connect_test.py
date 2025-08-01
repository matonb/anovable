#!/usr/bin/env python3
"""Test connecting to and getting status from Anova device."""

import asyncio
import logging

from anovable import AnovaBLE, AnovaError


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    # Use the MAC address we discovered
    mac_address = "01:02:03:04:21:9C"

    print(f"Connecting to Anova device at {mac_address}...")
    anova = AnovaBLE(mac_address)

    try:
        # Connect to device
        if await anova.connect():
            print("✅ Connected successfully!")

            # Get status
            print("\n--- Device Status ---")
            status = await anova.get_status()
            print(f"Status: {status}")

            # Get temperature unit first to format temperatures properly
            unit = await anova.get_unit()
            unit_symbol = "°C" if unit.lower() == "c" else "°F"

            # Get current temperature
            temp = await anova.get_temperature()
            print(f"Current temperature: {temp}{unit_symbol}")

            # Get target temperature
            target = await anova.get_target_temperature()
            print(f"Target temperature: {target}{unit_symbol}")

            # print(f"Temperature unit: {unit_symbol}")

            # Get timer status
            timer = await anova.get_timer()
            print(f"Timer: {timer}")

        else:
            print("❌ Failed to connect")

    except AnovaError as e:
        print(f"❌ Anova error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        await anova.disconnect()
        print("\nDisconnected from device")


if __name__ == "__main__":
    asyncio.run(main())
