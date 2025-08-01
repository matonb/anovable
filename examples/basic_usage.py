#!/usr/bin/env python3
"""Basic usage example for anovable library."""

import asyncio
import logging

from anovable import AnovaBLE, AnovaError


async def main() -> None:
    """Example usage of the anovable library."""
    logging.basicConfig(level=logging.INFO)

    anova = AnovaBLE()

    try:
        # Connect to device
        if await anova.connect():
            print("Connected to Anova!")

            # Get status
            status = await anova.get_status()
            print(f"Status: {status}")

            # Get temperature
            temp = await anova.get_temperature()
            print(f"Current temp: {temp}")

            # Get target temperature
            target = await anova.get_target_temperature()
            print(f"Target temp: {target}")

            # Get unit
            unit = await anova.get_unit()
            print(f"Unit: {unit}")

        else:
            print("Failed to connect")

    except AnovaError as e:
        print(f"Anova error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        await anova.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
