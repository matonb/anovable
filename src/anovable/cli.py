"""Command-line interface for Anova control."""

import asyncio
import json
import logging
from typing import Annotated, Optional

import typer
from typer import Argument, Option

from ._version import __version__
from .client import AnovaBLE
from .config import AnovaConfig
from .exceptions import AnovaError


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        typer.echo(__version__)
        raise typer.Exit()


app = typer.Typer(
    name="anova-cli",
    help="Control Anova Precision Cooker via Bluetooth LE",
    add_completion=True,
)


def format_response_debug(command: str, response: str, debug: bool = False) -> None:
    """Format and print response in debug mode as JSON."""
    if debug:
        response_data = {
            "command": command,
            "response": response.strip(),
            "raw_response": repr(response),
        }
        typer.echo("DEBUG Response: " + json.dumps(response_data, indent=2))


async def connect_anova(
    mac_address: Optional[str], config_path: Optional[str]
) -> AnovaBLE:
    """Connect to Anova device."""
    config = AnovaConfig(config_path)

    # Get MAC address from config or command line
    mac = mac_address or config.mac_address
    if not mac:
        typer.echo(
            "Error: No MAC address specified. Use --mac-address or configure in anovable.yaml",
            err=True,
        )
        raise typer.Exit(1)

    anova = AnovaBLE(mac)

    if not await anova.connect():
        typer.echo("Failed to connect to Anova device", err=True)
        raise typer.Exit(1)

    typer.echo("Connected to Anova!")
    return anova


@app.command()
def status(
    mac_address: Annotated[
        Optional[str], Option("--mac-address", "-m", help="MAC address of Anova device")
    ] = None,
    config: Annotated[
        Optional[str], Option("--config", "-c", help="Path to configuration file")
    ] = None,
    debug: Annotated[
        bool, Option("--debug", "-d", help="Enable debug logging")
    ] = False,
) -> None:
    """Get comprehensive device status."""
    asyncio.run(_status_async(mac_address, config, debug))


@app.command()
def state(
    mac_address: Annotated[
        Optional[str], Option("--mac-address", "-m", help="MAC address of Anova device")
    ] = None,
    config: Annotated[
        Optional[str], Option("--config", "-c", help="Path to configuration file")
    ] = None,
    debug: Annotated[
        bool, Option("--debug", "-d", help="Enable debug logging")
    ] = False,
) -> None:
    """Get comprehensive device status (alias for status)."""
    asyncio.run(_status_async(mac_address, config, debug))


async def _status_async(
    mac_address: Optional[str], config_path: Optional[str], debug: bool
) -> None:
    """Async implementation for status command."""
    if debug:
        logging.basicConfig(level=logging.DEBUG)

    anova = await connect_anova(mac_address, config_path)

    try:
        typer.echo("\n--- Device Status ---")

        # Get basic status
        status = await anova.get_status()
        format_response_debug("status", status, debug)
        typer.echo(f"Status: {status}")

        # Get temperature unit first to format temperatures properly
        unit_value = await anova.get_unit()
        format_response_debug("read unit", unit_value, debug)
        unit_symbol = "°C" if unit_value.lower() == "c" else "°F"

        # Get current temperature
        temp_value = await anova.get_temperature()
        format_response_debug("read temp", temp_value, debug)
        typer.echo(f"Current temperature: {temp_value}{unit_symbol}")

        # Get target temperature
        target = await anova.get_target_temperature()
        format_response_debug("read set temp", target, debug)
        typer.echo(f"Target temperature: {target}{unit_symbol}")

        # Get timer status (only if cooker is running)
        try:
            timer = await anova.get_timer()
            format_response_debug("read timer", timer, debug)
            typer.echo(f"Timer: {timer}")
        except Exception as e:
            typer.echo(f"Timer: {e}")

    except AnovaError as e:
        typer.echo(f"Anova error: {e}", err=True)
        raise typer.Exit(1) from e
    except Exception as e:
        typer.echo(f"Unexpected error: {e}", err=True)
        raise typer.Exit(1) from e
    finally:
        await anova.disconnect()


@app.command()
def temperature(
    mac_address: Annotated[
        Optional[str], Option("--mac-address", "-m", help="MAC address of Anova device")
    ] = None,
    config: Annotated[
        Optional[str], Option("--config", "-c", help="Path to configuration file")
    ] = None,
    debug: Annotated[
        bool, Option("--debug", "-d", help="Enable debug logging")
    ] = False,
) -> None:
    """Get current temperature."""
    asyncio.run(_temperature_async(mac_address, config, debug))


async def _temperature_async(
    mac_address: Optional[str], config_path: Optional[str], debug: bool
) -> None:
    """Async implementation for temperature command."""
    if debug:
        logging.basicConfig(level=logging.DEBUG)

    anova = await connect_anova(mac_address, config_path)

    try:
        temp_value = await anova.get_temperature()
        format_response_debug("read temp", temp_value, debug)
        typer.echo(f"Current temperature: {temp_value}")
    except AnovaError as e:
        typer.echo(f"Anova error: {e}", err=True)
        raise typer.Exit(1) from e
    except Exception as e:
        typer.echo(f"Unexpected error: {e}", err=True)
        raise typer.Exit(1) from e
    finally:
        await anova.disconnect()


@app.command()
def target(
    mac_address: Annotated[
        Optional[str], Option("--mac-address", "-m", help="MAC address of Anova device")
    ] = None,
    config: Annotated[
        Optional[str], Option("--config", "-c", help="Path to configuration file")
    ] = None,
    debug: Annotated[
        bool, Option("--debug", "-d", help="Enable debug logging")
    ] = False,
) -> None:
    """Get target temperature."""
    asyncio.run(_target_async(mac_address, config, debug))


async def _target_async(
    mac_address: Optional[str], config_path: Optional[str], debug: bool
) -> None:
    """Async implementation for target command."""
    if debug:
        logging.basicConfig(level=logging.DEBUG)

    anova = await connect_anova(mac_address, config_path)

    try:
        target_temperature = await anova.get_target_temperature()
        format_response_debug("read set temp", target_temperature, debug)
        typer.echo(f"Target temperature: {target_temperature}")
    except AnovaError as e:
        typer.echo(f"Anova error: {e}", err=True)
        raise typer.Exit(1) from e
    except Exception as e:
        typer.echo(f"Unexpected error: {e}", err=True)
        raise typer.Exit(1) from e
    finally:
        await anova.disconnect()


@app.command("set-temp")
def set_temp(
    temperature: Annotated[float, Argument(help="Temperature in Celsius")],
    mac_address: Annotated[
        Optional[str], Option("--mac-address", "-m", help="MAC address of Anova device")
    ] = None,
    config: Annotated[
        Optional[str], Option("--config", "-c", help="Path to configuration file")
    ] = None,
    debug: Annotated[
        bool, Option("--debug", "-d", help="Enable debug logging")
    ] = False,
) -> None:
    """Set target temperature."""
    asyncio.run(_set_temp_async(temperature, mac_address, config, debug))


async def _set_temp_async(
    temperature: float,
    mac_address: Optional[str],
    config_path: Optional[str],
    debug: bool,
) -> None:
    """Async implementation for set-temp command."""
    if debug:
        logging.basicConfig(level=logging.DEBUG)

    anova = await connect_anova(mac_address, config_path)

    try:
        response = await anova.set_temperature(temperature)
        format_response_debug(f"set temp {temperature}", response, debug)
        typer.echo(f"Set temperature: {response}")
    except AnovaError as e:
        typer.echo(f"Anova error: {e}", err=True)
        raise typer.Exit(1) from e
    except Exception as e:
        typer.echo(f"Unexpected error: {e}", err=True)
        raise typer.Exit(1) from e
    finally:
        await anova.disconnect()


@app.command()
def start(
    mac_address: Annotated[
        Optional[str], Option("--mac-address", "-m", help="MAC address of Anova device")
    ] = None,
    config: Annotated[
        Optional[str], Option("--config", "-c", help="Path to configuration file")
    ] = None,
    debug: Annotated[
        bool, Option("--debug", "-d", help="Enable debug logging")
    ] = False,
) -> None:
    """Start cooking."""
    asyncio.run(_start_async(mac_address, config, debug))


async def _start_async(
    mac_address: Optional[str], config_path: Optional[str], debug: bool
) -> None:
    """Async implementation for start command."""
    if debug:
        logging.basicConfig(level=logging.DEBUG)

    anova = await connect_anova(mac_address, config_path)

    try:
        response = await anova.start_cooking()
        format_response_debug("start", response, debug)
        typer.echo(f"Started: {response}")
    except AnovaError as e:
        typer.echo(f"Anova error: {e}", err=True)
        raise typer.Exit(1) from e
    except Exception as e:
        typer.echo(f"Unexpected error: {e}", err=True)
        raise typer.Exit(1) from e
    finally:
        await anova.disconnect()


@app.command()
def stop(
    mac_address: Annotated[
        Optional[str], Option("--mac-address", "-m", help="MAC address of Anova device")
    ] = None,
    config: Annotated[
        Optional[str], Option("--config", "-c", help="Path to configuration file")
    ] = None,
    debug: Annotated[
        bool, Option("--debug", "-d", help="Enable debug logging")
    ] = False,
) -> None:
    """Stop cooking."""
    asyncio.run(_stop_async(mac_address, config, debug))


async def _stop_async(
    mac_address: Optional[str], config_path: Optional[str], debug: bool
) -> None:
    """Async implementation for stop command."""
    if debug:
        logging.basicConfig(level=logging.DEBUG)

    anova = await connect_anova(mac_address, config_path)

    try:
        response = await anova.stop_cooking()
        format_response_debug("stop", response, debug)
        typer.echo(f"Stopped: {response}")
    except AnovaError as e:
        typer.echo(f"Anova error: {e}", err=True)
        raise typer.Exit(1) from e
    except Exception as e:
        typer.echo(f"Unexpected error: {e}", err=True)
        raise typer.Exit(1) from e
    finally:
        await anova.disconnect()


@app.command()
def timer(
    mac_address: Annotated[
        Optional[str], Option("--mac-address", "-m", help="MAC address of Anova device")
    ] = None,
    config: Annotated[
        Optional[str], Option("--config", "-c", help="Path to configuration file")
    ] = None,
    debug: Annotated[
        bool, Option("--debug", "-d", help="Enable debug logging")
    ] = False,
) -> None:
    """Get timer status."""
    asyncio.run(_timer_async(mac_address, config, debug))


async def _timer_async(
    mac_address: Optional[str], config_path: Optional[str], debug: bool
) -> None:
    """Async implementation for timer command."""
    if debug:
        logging.basicConfig(level=logging.DEBUG)

    anova = await connect_anova(mac_address, config_path)

    try:
        timer_value = await anova.get_timer()
        format_response_debug("read timer", timer_value, debug)
        typer.echo(f"Timer: {timer_value}")
    except AnovaError as e:
        typer.echo(f"Anova error: {e}", err=True)
        raise typer.Exit(1) from e
    except Exception as e:
        typer.echo(f"Unexpected error: {e}", err=True)
        raise typer.Exit(1) from e
    finally:
        await anova.disconnect()


@app.command("set-timer")
def set_timer(
    minutes: Annotated[int, Argument(help="Timer duration in minutes")],
    no_auto_start: Annotated[
        bool, Option("--no-auto-start", help="Don't automatically start the timer")
    ] = False,
    mac_address: Annotated[
        Optional[str], Option("--mac-address", "-m", help="MAC address of Anova device")
    ] = None,
    config: Annotated[
        Optional[str], Option("--config", "-c", help="Path to configuration file")
    ] = None,
    debug: Annotated[
        bool, Option("--debug", "-d", help="Enable debug logging")
    ] = False,
) -> None:
    """Set timer (automatically starts by default)."""
    asyncio.run(
        _set_timer_async(minutes, not no_auto_start, mac_address, config, debug)
    )


async def _set_timer_async(
    minutes: int,
    auto_start: bool,
    mac_address: Optional[str],
    config_path: Optional[str],
    debug: bool,
) -> None:
    """Async implementation for set-timer command."""
    if debug:
        logging.basicConfig(level=logging.DEBUG)

    anova = await connect_anova(mac_address, config_path)

    try:
        response = await anova.set_timer(minutes, auto_start=auto_start)
        format_response_debug(f"set timer {minutes}", response, debug)
        typer.echo(f"Set timer: {response}")
    except AnovaError as e:
        typer.echo(f"Anova error: {e}", err=True)
        raise typer.Exit(1) from e
    except Exception as e:
        typer.echo(f"Unexpected error: {e}", err=True)
        raise typer.Exit(1) from e
    finally:
        await anova.disconnect()


@app.command("start-timer")
def start_timer(
    mac_address: Annotated[
        Optional[str], Option("--mac-address", "-m", help="MAC address of Anova device")
    ] = None,
    config: Annotated[
        Optional[str], Option("--config", "-c", help="Path to configuration file")
    ] = None,
    debug: Annotated[
        bool, Option("--debug", "-d", help="Enable debug logging")
    ] = False,
) -> None:
    """Start timer."""
    asyncio.run(_start_timer_async(mac_address, config, debug))


async def _start_timer_async(
    mac_address: Optional[str], config_path: Optional[str], debug: bool
) -> None:
    """Async implementation for start-timer command."""
    if debug:
        logging.basicConfig(level=logging.DEBUG)

    anova = await connect_anova(mac_address, config_path)

    try:
        response = await anova.start_timer()
        format_response_debug("start time", response, debug)
        typer.echo(f"Started timer: {response}")
    except AnovaError as e:
        typer.echo(f"Anova error: {e}", err=True)
        raise typer.Exit(1) from e
    except Exception as e:
        typer.echo(f"Unexpected error: {e}", err=True)
        raise typer.Exit(1) from e
    finally:
        await anova.disconnect()


@app.command("stop-timer")
def stop_timer(
    mac_address: Annotated[
        Optional[str], Option("--mac-address", "-m", help="MAC address of Anova device")
    ] = None,
    config: Annotated[
        Optional[str], Option("--config", "-c", help="Path to configuration file")
    ] = None,
    debug: Annotated[
        bool, Option("--debug", "-d", help="Enable debug logging")
    ] = False,
) -> None:
    """Stop timer."""
    asyncio.run(_stop_timer_async(mac_address, config, debug))


async def _stop_timer_async(
    mac_address: Optional[str], config_path: Optional[str], debug: bool
) -> None:
    """Async implementation for stop-timer command."""
    if debug:
        logging.basicConfig(level=logging.DEBUG)

    anova = await connect_anova(mac_address, config_path)

    try:
        response = await anova.stop_timer()
        format_response_debug("stop time", response, debug)
        typer.echo(f"Stopped timer: {response}")
    except AnovaError as e:
        typer.echo(f"Anova error: {e}", err=True)
        raise typer.Exit(1) from e
    except Exception as e:
        typer.echo(f"Unexpected error: {e}", err=True)
        raise typer.Exit(1) from e
    finally:
        await anova.disconnect()


@app.command()
def unit(
    mac_address: Annotated[
        Optional[str], Option("--mac-address", "-m", help="MAC address of Anova device")
    ] = None,
    config: Annotated[
        Optional[str], Option("--config", "-c", help="Path to configuration file")
    ] = None,
    debug: Annotated[
        bool, Option("--debug", "-d", help="Enable debug logging")
    ] = False,
) -> None:
    """Get temperature unit."""
    asyncio.run(_unit_async(mac_address, config, debug))


async def _unit_async(
    mac_address: Optional[str], config_path: Optional[str], debug: bool
) -> None:
    """Async implementation for unit command."""
    if debug:
        logging.basicConfig(level=logging.DEBUG)

    anova = await connect_anova(mac_address, config_path)

    try:
        unit_value = await anova.get_unit()
        format_response_debug("read unit", unit_value, debug)
        typer.echo(f"Unit: {unit_value}")
    except AnovaError as e:
        typer.echo(f"Anova error: {e}", err=True)
        raise typer.Exit(1) from e
    except Exception as e:
        typer.echo(f"Unexpected error: {e}", err=True)
        raise typer.Exit(1) from e
    finally:
        await anova.disconnect()


@app.callback()
def main(
    _version: Annotated[
        Optional[bool],
        Option(
            "--version",
            callback=version_callback,
            is_eager=True,
            help="Show version and exit",
        ),
    ] = None,
) -> None:
    """Control Anova Precision Cooker via Bluetooth LE."""


if __name__ == "__main__":
    app()
