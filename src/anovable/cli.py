"""Command-line interface for Anova control."""

import argparse
import asyncio
import logging
import sys

from .client import AnovaBLE
from .config import AnovaConfig
from .exceptions import AnovaError


async def main_async(args: argparse.Namespace) -> int:
    """Main async function for CLI."""
    # Load configuration
    config = AnovaConfig(args.config)

    # Setup logging
    log_level = (
        logging.DEBUG if args.debug else getattr(logging, config.log_level.upper())
    )
    logging.basicConfig(
        level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Get MAC address from config or command line
    mac_address = args.mac_address or config.mac_address
    if not mac_address:
        print(
            "Error: No MAC address specified. Use --mac-address or configure in anovable.yaml",
            file=sys.stderr,
        )
        return 1

    anova = AnovaBLE(mac_address)

    try:
        # Connect to device
        if not await anova.connect():
            print("Failed to connect to Anova device", file=sys.stderr)
            return 1

        print("Connected to Anova!")

        if args.command == "status":
            status = await anova.get_status()
            print(f"Status: {status}")
        elif args.command == "temp":
            temp = await anova.get_temperature()
            print(f"Current temperature: {temp}")
        elif args.command == "target":
            target = await anova.get_target_temperature()
            print(f"Target temperature: {target}")
        elif args.command == "set-temp":
            if args.value is None:
                print("Error: --value required for set-temp", file=sys.stderr)
                return 1
            response = await anova.set_temperature(float(args.value))
            print(f"Set temperature: {response}")
        elif args.command == "start":
            response = await anova.start_cooking()
            print(f"Started: {response}")
        elif args.command == "stop":
            response = await anova.stop_cooking()
            print(f"Stopped: {response}")
        elif args.command == "timer":
            timer = await anova.get_timer()
            print(f"Timer: {timer}")
        elif args.command == "set-timer":
            if args.value is None:
                print("Error: --value required for set-timer", file=sys.stderr)
                return 1
            response = await anova.set_timer(int(args.value))
            print(f"Set timer: {response}")
        elif args.command == "unit":
            unit = await anova.get_unit()
            print(f"Unit: {unit}")
        else:
            print(f"Unknown command: {args.command}", file=sys.stderr)
            return 1

        return 0

    except AnovaError as e:
        print(f"Anova error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1
    finally:
        await anova.disconnect()


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Control Anova Precision Cooker via Bluetooth LE"
    )
    parser.add_argument(
        "--mac-address", help="MAC address of Anova device (overrides config file)"
    )
    parser.add_argument(
        "--config",
        help="Path to configuration file (default: search standard locations)",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--version", action="version", version="anovable 0.1.0")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Status commands
    subparsers.add_parser("status", help="Get device status")
    subparsers.add_parser("temp", help="Get current temperature")
    subparsers.add_parser("target", help="Get target temperature")

    # Control commands
    subparsers.add_parser("start", help="Start cooking")
    subparsers.add_parser("stop", help="Stop cooking")

    # Temperature setting
    temp_parser = subparsers.add_parser("set-temp", help="Set target temperature")
    temp_parser.add_argument("--value", required=True, help="Temperature in Celsius")

    # Timer commands
    subparsers.add_parser("timer", help="Get timer status")
    timer_parser = subparsers.add_parser("set-timer", help="Set timer")
    timer_parser.add_argument("--value", required=True, help="Timer in minutes")

    # Unit commands
    subparsers.add_parser("unit", help="Get temperature unit")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    exit_code = asyncio.run(main_async(args))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
