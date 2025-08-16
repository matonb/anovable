"""Custom exceptions for Anova library."""


class AnovaError(Exception):
    """Base exception for Anova-related errors."""


class AnovaConnectionError(AnovaError):
    """Exception raised for connection-related errors."""


class AnovaCommandError(AnovaError):
    """Exception raised for command-related errors."""


class AnovaTimeoutError(AnovaError):
    """Exception raised when a command times out."""


class AnovaValidationError(AnovaError):
    """Exception raised for validation errors."""
