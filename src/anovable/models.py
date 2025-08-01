"""Data models for Anova device communication."""

from dataclasses import dataclass
from enum import Enum


class AnovaState(Enum):
    """Anova device states."""

    STOPPED = "stopped"
    RUNNING = "running"
    DISCONNECTED = "disconnected"


@dataclass
class AnovaStatus:
    """Anova device status information."""

    state: AnovaState
    current_temp: float
    target_temp: float
    temp_unit: str
    timer_minutes: int = 0
    timer_running: bool = False
