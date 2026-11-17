import pytest

from med_tracker.seed import sample_patients
from med_tracker.tracker import MedicationTracker


@pytest.fixture
def tracker() -> MedicationTracker:
    return MedicationTracker(sample_patients())
