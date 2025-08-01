"""Custom exceptions for Anova library."""


class AnovaError(Exception):
    """Base exception for Anova-related errors."""
    pass


class AnovaConnectionError(AnovaError):
    """Exception raised for connection-related errors."""
    pass


class AnovaCommandError(AnovaError):
    """Exception raised for command-related errors."""
    pass


class AnovaTimeoutError(AnovaError):
    """Exception raised when a command times out."""
    pass


class AnovaValidationError(AnovaError):
    """Exception raised for validation errors."""
    pass