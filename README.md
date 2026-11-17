# Medication Tracking System

A Python system that helps nursing staff track each patient's prescribed medications and daily dosage schedule (morning, afternoon, evening), so patients get the right medication at the right time without errors or omissions.

> Status: **initial scaffold**. Core domain model, business rules, seed data, a basic CLI and tests are in place. See the roadmap below for what comes next.

## User story

> As a nurse, I want to track patients' prescribed medications along with their daily dosage schedule, so that patients receive the correct medications at the right time without errors or omissions.

## Acceptance criteria

| # | Criterion | Where it lives |
|---|-----------|----------------|
| 1 | A nurse can view all assigned patients | `MedicationTracker.list_patients`, `med-tracker patients` |
| 2 | Each patient record shows one or more medications | `Patient.medications` |
| 3 | Each medication has a schedule with up to three doses (morning, afternoon, evening) | `Schedule`, `TimeSlot` |
| 4 | The system shows pending vs completed doses per time slot | `MedicationTracker.doses_for_slot`, `DoseStatus` |
| 5 | A nurse can mark a dose as administered | `MedicationTracker.mark_administered` |
| 6 | Alerts prevent duplicate or missed entries | `DuplicateDoseError`, `missed_dose_alerts` |

## Plan

### Architecture

```
src/med_tracker/
  models.py    domain models (Patient, Medication, Schedule, DoseRecord, TimeSlot, DoseStatus)
  alerts.py    Alert types and the errors that carry them
  tracker.py   business logic: what's due, record a dose, detect duplicates / missed doses
  seed.py      sample ward data
  cli.py       command-line interface for nurses
  api/         (planned) FastAPI app: JSON endpoints + nurse web UI
    templates/ (planned) Jinja2 + htmx pages
tests/         pytest suite mapped to the acceptance criteria
```

The layers are kept separate so the interface (CLI and web UI) and the storage (in-memory today, SQLite later) can change without touching the business rules. The CLI and the web UI both call the same `MedicationTracker`.

### Web UI (planned)

A small browser UI so a nurse can try the system end to end. It is a FastAPI app that serves server-rendered pages (Jinja2 templates, with htmx for in-place updates, so there's no separate JS build).

- **Ward overview**: all assigned patients with room, medications and dosage. (Criteria 1, 2)
- **Medication round**: tabs for Morning / Afternoon / Evening, defaulting to the current slot. Each dose is a row with a status badge: pending (grey), administered (green, with nurse and time), missed (red). (Criteria 3, 4)
- **Mark as given**: a button on each pending row records the dose and flips the badge without a page reload. (Criterion 5)
- **Alerts**: a banner when a nurse tries to give a dose twice (shows who gave it and when) or a dose that isn't scheduled, plus a missed-dose panel listing every overdue dose. (Criterion 6)
- **Patient detail**: one patient's schedule as a grid of medications by slot, showing today's status in each cell.
- **Nurse sign-in**: a simple name picker (no real auth) so each record says who gave it.
- **Demo controls**: reset to seed data, and a "simulate time" setting so the tester can see missed-dose alerts without waiting for a slot to end.

Endpoints behind it (also usable as a JSON API):

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/patients` | List patients and medications |
| GET | `/patients/{id}` | One patient's schedule and today's status |
| GET | `/doses?slot=morning&day=YYYY-MM-DD` | Doses for a slot with status |
| POST | `/doses/administer` | Mark a dose as given (409 with alert on duplicate) |
| GET | `/alerts?day=YYYY-MM-DD` | Missed-dose alerts |

The UI is tested with FastAPI's `TestClient` (status codes, duplicate returns 409, rendered pages show the right badges).

### Data model

- **Patient**: id, name, room, list of medications
- **Medication**: id, name, dosage (e.g. "500 mg"), instructions, schedule
- **Schedule**: the set of `TimeSlot`s the medication is due in (at least one)
- **TimeSlot**: `morning` (06:00-12:00), `afternoon` (12:00-18:00), `evening` (18:00-24:00)
- **DoseRecord**: patient, medication, day, slot, time given, nurse. One record per (patient, medication, day, slot), which is what makes duplicates detectable.
- **DoseStatus** (derived, not stored): `pending` (slot open, not given), `administered` (record exists), `missed` (slot ended, no record)

### Alert rules

- **Duplicate dose**: recording a dose that already has a record for that day and slot is rejected with an alert saying who gave it and when.
- **Not scheduled**: recording a dose in a slot the medication isn't scheduled for is rejected.
- **Missed dose**: once a slot's window ends, any scheduled dose without a record is reported as missed.

### Roadmap

1. ~~Scaffold: models, tracker logic, seed data, CLI, tests~~ (this commit)
2. **Web UI for nurses** (FastAPI + Jinja2 + htmx, see above), so the system can be demoed and tested in a browser
3. Persistence (SQLite via `sqlite3` or SQLAlchemy) so records survive restarts
4. Assign patients to nurses / shifts, and filter the view per nurse
5. Optional: undo / correct a record with an audit trail, and record "refused / withheld" with a reason
6. Optional: polish CLI output (e.g. `rich` tables, colour for missed doses)

## Getting started

Requires Python 3.10+.

```bash
git clone https://github.com/rickymwethera/medtrack.git
cd medtrack
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### Run

```bash
med-tracker patients            # list patients and their medications
med-tracker due morning         # pending / administered / missed doses for a slot
med-tracker round               # interactive round: show, give, alerts
# once the web UI lands:
# uvicorn med_tracker.api.app:app --reload   then open http://127.0.0.1:8000
```

Example round:

```
Nurse name: Joy
> show morning
> give P001 MED1 morning
> give P001 MED1 morning
ALERT: Metformin for Grace Wanjiru (morning) was already given at 08:02 by Joy.
> alerts
```

### Test

```bash
pytest
```
