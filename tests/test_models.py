from datetime import date, datetime

import pytest

from med_tracker.models import Schedule, TimeSlot


def test_schedule_requires_at_least_one_slot():
    with pytest.raises(ValueError):
        Schedule.of()


def test_schedule_is_due():
    s = Schedule.of(TimeSlot.MORNING, TimeSlot.EVENING)
    assert s.is_due(TimeSlot.MORNING)
    assert not s.is_due(TimeSlot.AFTERNOON)


@pytest.mark.parametrize(
    "slot, now, ended",
    [
        (TimeSlot.MORNING, datetime(2026, 1, 1, 11, 59), False),
        (TimeSlot.MORNING, datetime(2026, 1, 1, 12, 0), True),
        (TimeSlot.EVENING, datetime(2026, 1, 1, 23, 59), False),
        (TimeSlot.EVENING, datetime(2026, 1, 2, 0, 1), True),
    ],
)
def test_slot_has_ended(slot, now, ended):
    assert slot.has_ended(now, date(2026, 1, 1)) is ended
