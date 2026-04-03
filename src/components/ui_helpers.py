from contextlib import contextmanager
from datetime import date, datetime, time

from PySide6.QtWidgets import QApplication


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


def refresh_application_views(*page_names: str, include_dashboard: bool = True):
    try:
        main_window = None
        for widget in QApplication.topLevelWidgets():
            if hasattr(widget, "widgets") and hasattr(widget, "refresh_current_page"):
                main_window = widget
                break
        if not main_window:
            return

        if include_dashboard and hasattr(main_window, "refresh_dashboard"):
            try:
                main_window.refresh_dashboard()
            except Exception:
                pass

        ordered_pages = list(dict.fromkeys(page_names))
        for page_name in ordered_pages:
            try:
                main_window.refresh_current_page(page_name)
            except Exception:
                continue

        reports_widget = getattr(main_window, "widgets", {}).get("reports")
        if reports_widget and hasattr(reports_widget, "generate_report"):
            try:
                reports_widget.generate_report()
            except Exception:
                pass
    except Exception:
        pass
