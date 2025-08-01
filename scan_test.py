#!/usr/bin/env python3
"""Quick script to scan for Anova devices."""

import asyncio
import logging

from anovable import AnovaBLE


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    print("Scanning for Anova devices...")
    anova = AnovaBLE()

    try:
        mac_address = await anova.discover_device()
        if mac_address:
            print(f"✅ Found Anova device at: {mac_address}")
        else:
            print("❌ No Anova device found")
            print("Make sure your Anova A3 is:")
            print("- Powered on")
            print("- In Bluetooth pairing mode")
            print("- Within range")
    except Exception as e:
        print(f"Error during scan: {e}")


if __name__ == "__main__":
    asyncio.run(main())
