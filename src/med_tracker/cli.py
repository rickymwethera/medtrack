"""Command-line interface for nurses.

State is in memory for now, so the `round` command runs an interactive
session over the seed data. Persistence comes in a later iteration.
"""

from __future__ import annotations

import argparse
from datetime import date

from .alerts import DoseError
from .models import DoseStatus, TimeSlot
from .seed import sample_patients
from .tracker import MedicationTracker

ICONS = {DoseStatus.PENDING: "[ ]", DoseStatus.ADMINISTERED: "[x]", DoseStatus.MISSED: "[!]"}


def print_patients(tracker: MedicationTracker) -> None:
    for p in tracker.list_patients():
        print(f"{p.id}  {p.name}  (room {p.room})")
        for m in p.medications:
            slots = ", ".join(s.value for s in TimeSlot if m.schedule.is_due(s))
            print(f"    {m.id}  {m.name} {m.dosage}  [{slots}]  {m.instructions}")


def print_slot(tracker: MedicationTracker, day: date, slot: TimeSlot) -> None:
    print(f"\n== {slot.value.upper()} doses for {day} ==")
    for v in tracker.doses_for_slot(day, slot):
        print(f"  {ICONS[v.status]} {v.patient.name:<15} {v.medication.name} {v.medication.dosage}"
              f"  ({v.patient.id}/{v.medication.id})  {v.status.value}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="med-tracker")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("patients", help="List patients and their medications")
    due = sub.add_parser("due", help="Show doses for a time slot")
    due.add_argument("slot", choices=[s.value for s in TimeSlot])
    sub.add_parser("round", help="Interactive medication round")
    args = parser.parse_args(argv)

    tracker = MedicationTracker(sample_patients())
    today = date.today()

    if args.command == "patients":
        print_patients(tracker)
    elif args.command == "due":
        print_slot(tracker, today, TimeSlot(args.slot))
    elif args.command == "round":
        nurse = input("Nurse name: ").strip() or "nurse"
        print("Commands: show <slot> | give <patient> <med> <slot> | alerts | quit")
        while True:
            try:
                parts = input("> ").split()
            except EOFError:
                break
            if not parts:
                continue
            cmd = parts[0]
            try:
                if cmd == "quit":
                    break
                elif cmd == "show" and len(parts) == 2:
                    print_slot(tracker, today, TimeSlot(parts[1]))
                elif cmd == "give" and len(parts) == 4:
                    rec = tracker.mark_administered(parts[1], parts[2], today, TimeSlot(parts[3]), nurse)
                    print(f"Recorded at {rec.administered_at:%H:%M}.")
                elif cmd == "alerts":
                    alerts = tracker.missed_dose_alerts(today)
                    print("\n".join(f"ALERT: {a.message}" for a in alerts) or "No missed doses.")
                else:
                    print("Unknown command.")
            except DoseError as e:
                print(f"ALERT: {e.alert.message}")
            except (KeyError, ValueError) as e:
                print(f"Error: {e}")


if __name__ == "__main__":
    main()
