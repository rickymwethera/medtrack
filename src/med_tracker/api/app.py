from datetime import date, datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from med_tracker.alerts import DoseError, DuplicateDoseError
from med_tracker.models import TimeSlot
from med_tracker.seed import sample_patients
from med_tracker.tracker import MedicationTracker

app = FastAPI(title="Medication Tracker API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # the React (Vite) dev server
    allow_methods=["*"],
    allow_headers=["*"],
)
tracker = MedicationTracker(sample_patients())


# ---- shapes of the JSON going in and out --------------------------------
class MedicationOut(BaseModel):
    id: str
    name: str
    dosage: str
    instructions: str
    slots: list[TimeSlot]


class PatientOut(BaseModel):
    id: str
    name: str
    room: str
    medications: list[MedicationOut]


class DoseOut(BaseModel):
    patient_id: str
    patient_name: str
    room: str
    medication_id: str
    medication_name: str
    dosage: str
    slot: TimeSlot
    status: str  # pending / administered / missed
    administered_at: datetime | None = None
    administered_by: str | None = None


class AdministerIn(BaseModel):
    patient_id: str
    medication_id: str
    slot: TimeSlot
    nurse: str
    day: date | None = None


class AlertOut(BaseModel):
    type: str
    message: str
    patient_id: str
    medication_id: str


# ---- helpers -------------------------------------------------------------
def to_patient_out(p) -> PatientOut:
    return PatientOut(
        id=p.id,
        name=p.name,
        room=p.room,
        medications=[
            MedicationOut(
                id=m.id,
                name=m.name,
                dosage=m.dosage,
                instructions=m.instructions,
                slots=[s for s in TimeSlot if m.schedule.is_due(s)],
            )
            for m in p.medications
        ],
    )


# ---- endpoints -----------------------------------------------------------
@app.get("/api/patients", response_model=list[PatientOut])
def list_patients():
    return [to_patient_out(p) for p in tracker.list_patients()]


@app.get("/api/patients/{patient_id}", response_model=PatientOut)
def get_patient(patient_id: str):
    try:
        return to_patient_out(tracker.get_patient(patient_id))
    except KeyError:
        raise HTTPException(404, f"Patient {patient_id} not found")


@app.get("/api/doses", response_model=list[DoseOut])
def doses_for_slot(slot: TimeSlot, day: date | None = None, now: datetime | None = None):
    """`now` lets you simulate the time of day, e.g. 2026-11-17T13:00 to see missed morning doses."""
    views = tracker.doses_for_slot(day or date.today(), slot, now)
    return [
        DoseOut(
            patient_id=v.patient.id,
            patient_name=v.patient.name,
            room=v.patient.room,
            medication_id=v.medication.id,
            medication_name=v.medication.name,
            dosage=v.medication.dosage,
            slot=v.slot,
            status=v.status.value,
            administered_at=v.record.administered_at if v.record else None,
            administered_by=v.record.administered_by if v.record else None,
        )
        for v in views
    ]


@app.post("/api/doses/administer", status_code=201)
def administer(body: AdministerIn):
    try:
        record = tracker.mark_administered(
            body.patient_id, body.medication_id, body.day or date.today(), body.slot, body.nurse
        )
    except DuplicateDoseError as e:
        raise HTTPException(409, e.alert.message)  # 409 = conflict: already given
    except DoseError as e:
        raise HTTPException(400, e.alert.message)  # not scheduled in this slot
    except KeyError as e:
        raise HTTPException(404, str(e))
    return {"message": "Dose recorded", "administered_at": record.administered_at}


@app.get("/api/alerts", response_model=list[AlertOut])
def missed_alerts(day: date | None = None, now: datetime | None = None):
    alerts = tracker.missed_dose_alerts(day or date.today(), now)
    return [AlertOut(type=a.type.value, message=a.message, patient_id=a.patient_id,
                     medication_id=a.medication_id) for a in alerts]


@app.post("/api/demo/reset")
def reset_demo():
    global tracker
    tracker = MedicationTracker(sample_patients())
    return {"message": "Demo data reset"}