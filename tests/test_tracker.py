from datetime import date, datetime

import pytest

from med_tracker.alerts import AlertType, DuplicateDoseError, NotScheduledError
from med_tracker.models import DoseStatus, TimeSlot

DAY = date(2026, 1, 1)
MORNING_NOW = datetime(2026, 1, 1, 8, 0)


def test_nurse_can_view_all_patients_with_medications(tracker):
    patients = tracker.list_patients()
    assert len(patients) == 3
    assert all(p.medications for p in patients)


def test_doses_start_pending(tracker):
    views = tracker.doses_for_slot(DAY, TimeSlot.MORNING, now=MORNING_NOW)
    assert views
    assert {v.status for v in views} == {DoseStatus.PENDING}


def test_only_scheduled_meds_appear_in_slot(tracker):
    afternoon = tracker.doses_for_slot(DAY, TimeSlot.AFTERNOON, now=MORNING_NOW)
    assert {v.medication.id for v in afternoon} == {"MED3", "MED4"}


def test_mark_administered_marks_dose_completed(tracker):
    tracker.mark_administered("P001", "MED1", DAY, TimeSlot.MORNING, "Nurse Joy", at=MORNING_NOW)
    views = tracker.doses_for_slot(DAY, TimeSlot.MORNING, now=MORNING_NOW)
    status = {(v.patient.id, v.medication.id): v.status for v in views}
    assert status[("P001", "MED1")] is DoseStatus.ADMINISTERED
    assert status[("P001", "MED2")] is DoseStatus.PENDING


def test_duplicate_dose_raises_alert(tracker):
    tracker.mark_administered("P001", "MED1", DAY, TimeSlot.MORNING, "Nurse Joy", at=MORNING_NOW)
    with pytest.raises(DuplicateDoseError) as exc:
        tracker.mark_administered("P001", "MED1", DAY, TimeSlot.MORNING, "Nurse Ann")
    assert exc.value.alert.type is AlertType.DUPLICATE_DOSE
    assert "Nurse Joy" in exc.value.alert.message


def test_cannot_give_unscheduled_dose(tracker):
    with pytest.raises(NotScheduledError):
        tracker.mark_administered("P001", "MED2", DAY, TimeSlot.EVENING, "Nurse Joy")


def test_missed_doses_raise_alerts_after_slot_ends(tracker):
    tracker.mark_administered("P001", "MED1", DAY, TimeSlot.MORNING, "Nurse Joy", at=MORNING_NOW)
    alerts = tracker.missed_dose_alerts(DAY, now=datetime(2026, 1, 1, 13, 0))
    missed = {(a.patient_id, a.medication_id) for a in alerts}
    assert ("P001", "MED1") not in missed  # given
    assert ("P001", "MED2") in missed  # morning ended, not given
    assert all(a.type is AlertType.MISSED_DOSE for a in alerts)
    # afternoon slot hasn't ended yet, so no afternoon alerts
    assert len(alerts) == 4  # MED2, MED3, MED4, MED6 morning doses
