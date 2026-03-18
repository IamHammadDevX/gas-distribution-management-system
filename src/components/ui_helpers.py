from contextlib import contextmanager
from datetime import date, datetime, time


def as_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, (datetime, date, time)):
        return str(value)
    return str(value)


def as_datetime_text(value, width: int = 16) -> str:
    text = as_text(value)
    return text[:width] if width and len(text) > width else text


def as_money(value, prefix: str = "Rs. ") -> str:
    try:
        return f"{prefix}{float(value or 0):,.2f}"
    except Exception:
        return f"{prefix}0.00"


@contextmanager
def table_batch_update(table):
    previous_sorting = table.isSortingEnabled()
    table.setSortingEnabled(False)
    table.setUpdatesEnabled(False)
    table.blockSignals(True)
    try:
        yield
    finally:
        table.blockSignals(False)
        table.setUpdatesEnabled(True)
        table.setSortingEnabled(previous_sorting)
