# Anovable

Python library for controlling Anova Precision Cookers via Bluetooth LE.

## Installation

```bash
pip install matonb-anovable
```

## Configuration

Create an `anovable.yaml` configuration file (Home Assistant compatible format):

```yaml
# Anovable Configuration File
anova:
  mac_address: "01:02:03:04:05:06"  # Your Anova device MAC address

  connection:
    timeout: 5.0
    retry_attempts: 3

  temperature:
    default_unit: "celsius"

  logging:
    level: "INFO"
```

## Python Usage

```python
import asyncio
from anovable import AnovaBLE

async def main():
    # Auto-discovers device or uses config file
    anova = AnovaBLE()

    if await anova.connect():
        # Get status
        status = await anova.get_status()
        print(f"Status: {status}")

        # Set temperature
        await anova.set_temperature(60.0)

        # Start cooking
        await anova.start_cooking()

        # Set timer (auto-starts by default, but only if cooker is running)
        await anova.set_timer(120)  # 120 minutes, auto-starts if cooker running

        # Or set timer without auto-starting
        await anova.set_timer(120, auto_start=False)

    await anova.disconnect()

asyncio.run(main())
```

## CLI Usage

The CLI automatically uses your MAC address from `anovable.yaml`:

### Status Commands
```bash
# Get comprehensive device status
anova-cli status
# or
anova-cli state

# Get current temperature
anova-cli temp

# Get target temperature
anova-cli target

# Get timer status
anova-cli timer

# Get temperature unit
anova-cli unit
```

### Control Commands
```bash
# Typical workflow
anova-cli set-temp 60.0    # Set target temperature
anova-cli start            # Start cooking
anova-cli set-timer 120    # Set timer (auto-starts since cooker is running)

# Individual commands
anova-cli start            # Start cooking
anova-cli stop             # Stop cooking

# Set target temperature (°C or °F) - uses positional argument
anova-cli set-temp 60.0

# Set timer (minutes) - automatically starts timer if cooker is running
anova-cli set-timer 120

# Set timer without auto-starting
anova-cli set-timer 120 --no-auto-start

# Manual timer control (requires cooker to be running)
anova-cli start-timer
anova-cli stop-timer
```

### Options
```bash
# Override MAC address
anova-cli --mac-address aa:bb:cc:dd:ee:ff status
anova-cli -m aa:bb:cc:dd:ee:ff status

# Use custom config file
anova-cli --config /path/to/config.yaml status
anova-cli -c /path/to/config.yaml status

# Enable debug logging
anova-cli --debug status
anova-cli -d status

# Show version
anova-cli --version

# Get help for any command
anova-cli --help
anova-cli status --help

# Enable shell completion (bash, zsh, fish, PowerShell)
anova-cli --install-completion
anova-cli --show-completion  # Show completion script to copy manually
```

## Device Discovery

If you don't know your Anova's MAC address:

```python
import asyncio
from anovable import AnovaBLE

async def find_device():
    anova = AnovaBLE()
    mac_address = await anova.discover_device()
    if mac_address:
        print(f"Found Anova at: {mac_address}")
    else:
        print("No Anova device found")

asyncio.run(find_device())
```
