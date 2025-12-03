import os
import sys
from datetime import date, timedelta

# Ensure the project root is on sys.path so that `src` is importable
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.database_module.database_manager import DatabaseManager


def main():
    workdir = PROJECT_ROOT
    db_path = os.path.join(workdir, "rajput_gas_test.db")
    if os.path.exists(db_path):
        os.remove(db_path)

    mgr = DatabaseManager(db_path=db_path)

    # Create client with initial previous balance
    client_id = mgr.add_client("Test Client", "555-000", "Addr", "Comp", 123.45)

    # Record initial outstanding empties
    mgr.add_client_initial_outstanding(client_id, "LPG", "12kg", 3)

    # Check cylinder summary
    s1 = mgr.get_cylinder_summary_for_client(client_id)
    print("SUMMARY_1", s1)

    # Return some cylinders
    mgr.add_cylinder_return(client_id, "LPG", "12kg", 2)

    s2 = mgr.get_cylinder_summary_for_client(client_id)
    print("SUMMARY_2", s2)

    # Compute weekly summary for this week
    # Choose week_start as last Saturday and week_end as Friday
    weekday = date.today().weekday()  # Mon=0 .. Sun=6
    sat_offset = (weekday - 5) % 7
    week_start = date.today() - timedelta(days=sat_offset)
    week_end = week_start + timedelta(days=6)
    ws = week_start.strftime('%Y-%m-%d')
    we = week_end.strftime('%Y-%m-%d')
    summary_week = mgr.compute_weekly_summary_for_client(client_id, ws, we)
    print("WEEK_SUMMARY", summary_week)

    # Simple validations
    # Expect remaining = 1 for LPG 12/15kg grouping
    rem_ok = False
    for row in s2:
        if row.get("gas_type") == "LPG" and row.get("capacity") in ("12/15kg", "12kg"):
            rem_ok = (
                int(row.get("remaining", 0)) == 1
                and int(row.get("delivered", 0)) == 3
                and int(row.get("returned", 0)) == 2
            )
            break
    prev_ok = abs(float(summary_week.get("previous_balance", 0.0)) - 123.45) < 1e-6
    print("RESULT", {"cylinder_summary_ok": rem_ok, "weekly_prev_balance_ok": prev_ok})


if __name__ == "__main__":
    main()

