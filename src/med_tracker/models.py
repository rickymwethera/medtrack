"""Core domain models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time
from enum import Enum


class TimeSlot(str, Enum):
    MORNING = "morning"
    AFTERNOON = "afternoon"
    EVENING = "evening"

    @property
    def window(self) -> tuple[time, time]:
        """Start (inclusive) and end (exclusive) of the slot's administration window."""
        return SLOT_WINDOWS[self]

    def has_ended(self, now: datetime, on: date) -> bool:
        """True once the slot's window on the given day is over."""
        _, end = self.window
        if end == time(0, 0):  # evening runs until midnight
            return now.date() > on
        return now >= datetime.combine(on, end)


SLOT_WINDOWS: dict[TimeSlot, tuple[time, time]] = {
    TimeSlot.MORNING: (time(6, 0), time(12, 0)),
    TimeSlot.AFTERNOON: (time(12, 0), time(18, 0)),
    TimeSlot.EVENING: (time(18, 0), time(0, 0)),
}


class DoseStatus(str, Enum):
    PENDING = "pending"
    ADMINISTERED = "administered"
    MISSED = "missed"


@dataclass(frozen=True)
class Schedule:
    """Which of the three daily slots a medication is due in."""

    slots: frozenset[TimeSlot]

    def __post_init__(self) -> None:
        if not self.slots:
            raise ValueError("A schedule needs at least one time slot")

    @classmethod
    def of(cls, *slots: TimeSlot) -> "Schedule":
        return cls(frozenset(slots))

    def is_due(self, slot: TimeSlot) -> bool:
        return slot in self.slots


@dataclass
class Medication:
    id: str
    name: str
    dosage: str  # e.g. "500 mg", "10 ml"
    schedule: Schedule
    instructions: str = ""


@dataclass
class Patient:
    id: str
    name: str
    room: str
    medications: list[Medication] = field(default_factory=list)

    def medication(self, medication_id: str) -> Medication:
        for med in self.medications:
            if med.id == medication_id:
                return med
        raise KeyError(f"Patient {self.id} has no medication {medication_id}")


@dataclass(frozen=True)
class DoseRecord:
    """A dose that was actually administered."""

    patient_id: str
    medication_id: str
    day: date
    slot: TimeSlot
    administered_at: datetime
    administered_by: str

    @property
    def key(self) -> tuple[str, str, date, TimeSlot]:
        return (self.patient_id, self.medication_id, self.day, self.slot)


@dataclass(frozen=True)
class DoseView:
    """A scheduled dose with its current status, for display."""

    patient: Patient
    medication: Medication
    day: date
    slot: TimeSlot
    status: DoseStatus
    record: DoseRecord | None = None
