"""Constants for Anova Bluetooth communication."""

# Bluetooth constants from protocol documentation
DEVICE_NAME = "Anova"
SERVICE_UUID = "0000ffe0-0000-1000-8000-00805f9b34fb"
CHARACTERISTIC_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"

# Communication limits
MAX_COMMAND_LENGTH = 20
RESPONSE_TIMEOUT = 5.0
MAX_RETRY_ATTEMPTS = 6
RETRY_DELAY = 0.5

# Temperature limits (Celsius)
MIN_TEMPERATURE = 5.0
MAX_TEMPERATURE = 99.9

# Timer limits (minutes)
MIN_TIMER = 0
MAX_TIMER = 6000
