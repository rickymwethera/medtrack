"""Sample ward data for demos and tests."""

from .models import Medication, Patient, Schedule, TimeSlot

M, A, E = TimeSlot.MORNING, TimeSlot.AFTERNOON, TimeSlot.EVENING


def sample_patients() -> list[Patient]:
    return [
        Patient(
            id="P001",
            name="Grace Wanjiru",
            room="101",
            medications=[
                Medication("MED1", "Metformin", "500 mg", Schedule.of(M, E)),
                Medication("MED2", "Lisinopril", "10 mg", Schedule.of(M)),
            ],
        ),
        Patient(
            id="P002",
            name="John Otieno",
            room="102",
            medications=[
                Medication("MED3", "Amoxicillin", "250 mg", Schedule.of(M, A, E)),
            ],
        ),
        Patient(
            id="P003",
            name="Amina Hassan",
            room="103",
            medications=[
                Medication("MED4", "Paracetamol", "1 g", Schedule.of(M, A, E)),
                Medication("MED5", "Atorvastatin", "20 mg", Schedule.of(E)),
                Medication("MED6", "Omeprazole", "20 mg", Schedule.of(M)),
            ],
        ),
    ]
