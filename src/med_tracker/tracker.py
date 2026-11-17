"""Business logic: what is due, what was given, and what was missed."""

from __future__ import annotations

from datetime import date, datetime

from .alerts import Alert, AlertType, DuplicateDoseError, NotScheduledError
from .models import DoseRecord, DoseStatus, DoseView, Patient, TimeSlot


class MedicationTracker:
    """In-memory tracker. Swap the dicts for a repository/DB layer later."""

    def __init__(self, patients: list[Patient] | None = None):
        self._patients: dict[str, Patient] = {p.id: p for p in patients or []}
        self._records: dict[tuple, DoseRecord] = {}

    # --- patients -------------------------------------------------------
    def add_patient(self, patient: Patient) -> None:
        self._patients[patient.id] = patient

    def list_patients(self) -> list[Patient]:
        return sorted(self._patients.values(), key=lambda p: p.room)

    def get_patient(self, patient_id: str) -> Patient:
        try:
            return self._patients[patient_id]
        except KeyError:
            raise KeyError(f"Unknown patient {patient_id}") from None

    # --- doses ----------------------------------------------------------
    def doses_for_slot(
        self, day: date, slot: TimeSlot, now: datetime | None = None
    ) -> list[DoseView]:
        """Every dose due in a slot, with pending / administered / missed status."""
        now = now or datetime.now()
        views = []
        for patient in self.list_patients():
            for med in patient.medications:
                if not med.schedule.is_due(slot):
                    continue
                record = self._records.get((patient.id, med.id, day, slot))
                if record:
                    status = DoseStatus.ADMINISTERED
                elif slot.has_ended(now, day):
                    status = DoseStatus.MISSED
                else:
                    status = DoseStatus.PENDING
                views.append(DoseView(patient, med, day, slot, status, record))
        return views

    def mark_administered(
        self,
        patient_id: str,
        medication_id: str,
        day: date,
        slot: TimeSlot,
        nurse: str,
        at: datetime | None = None,
    ) -> DoseRecord:
        patient = self.get_patient(patient_id)
        med = patient.medication(medication_id)

        if not med.schedule.is_due(slot):
            raise NotScheduledError(
                Alert(
                    AlertType.NOT_SCHEDULED,
                    f"{med.name} is not scheduled for {patient.name} in the {slot.value} slot.",
                    patient_id,
                    medication_id,
                )
            )

        key = (patient_id, medication_id, day, slot)
        if existing := self._records.get(key):
            raise DuplicateDoseError(
                Alert(
                    AlertType.DUPLICATE_DOSE,
                    f"{med.name} for {patient.name} ({slot.value}) was already given "
                    f"at {existing.administered_at:%H:%M} by {existing.administered_by}.",
                    patient_id,
                    medication_id,
                )
            )

        record = DoseRecord(patient_id, medication_id, day, slot, at or datetime.now(), nurse)
        self._records[key] = record
        return record

    def missed_dose_alerts(self, day: date, now: datetime | None = None) -> list[Alert]:
        """Alerts for every scheduled dose whose slot has ended without a record."""
        alerts = []
        for slot in TimeSlot:
            for view in self.doses_for_slot(day, slot, now):
                if view.status is DoseStatus.MISSED:
                    alerts.append(
                        Alert(
                            AlertType.MISSED_DOSE,
                            f"{view.medication.name} for {view.patient.name} "
                            f"(room {view.patient.room}) was not given in the {slot.value} slot.",
                            view.patient.id,
                            view.medication.id,
                        )
                    )
        return alerts
