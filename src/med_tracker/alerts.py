"""Alerts raised when a dose is skipped or given twice."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AlertType(str, Enum):
    DUPLICATE_DOSE = "duplicate_dose"
    MISSED_DOSE = "missed_dose"
    NOT_SCHEDULED = "not_scheduled"


@dataclass(frozen=True)
class Alert:
    type: AlertType
    message: str
    patient_id: str
    medication_id: str


class DoseError(Exception):
    """Raised when a dose cannot be recorded. Carries the alert to show the nurse."""

    def __init__(self, alert: Alert):
        super().__init__(alert.message)
        self.alert = alert


class DuplicateDoseError(DoseError):
    pass


class NotScheduledError(DoseError):
    pass
