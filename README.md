# Anovable

Python library for controlling Anova Precision Cookers via Bluetooth LE.

## Installation

```bash
pip install anovable
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

    await anova.disconnect()

asyncio.run(main())
```

## CLI Usage

The CLI automatically uses your MAC address from `anovable.yaml`:

### Status Commands
```bash
# Get device status
anova-cli status

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
# Start cooking
anova-cli start

# Stop cooking
anova-cli stop

# Set target temperature (Celsius)
anova-cli set-temp --value 60.0

# Set timer (minutes)
anova-cli set-timer --value 120
```

### Options
```bash
# Override MAC address
anova-cli --mac-address aa:bb:cc:dd:ee:ff status

# Use custom config file
anova-cli --config /path/to/config.yaml status

# Enable debug logging
anova-cli --debug status

# Show version
anova-cli --version
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