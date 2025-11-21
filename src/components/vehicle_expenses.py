from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QDateEdit, QComboBox, QLineEdit, QDoubleSpinBox, QPushButton, QTableWidget, QTableWidgetItem, QGroupBox
from PySide6.QtCore import Qt, QDate
from database_module import DatabaseManager

class VehicleExpensesWidget(QWidget):
    def __init__(self, db_manager: DatabaseManager, current_user: dict):
        super().__init__()
        self.db_manager = db_manager
        self.current_user = current_user
        self.init_ui()
        self.load_employees()
        self.load_expenses()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Vehicle Expenses")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title)

        # Entry form
        form = QGroupBox("Add Expense")
        f = QHBoxLayout(form)
        self.driver_combo = QComboBox()
        self.vehicle_input = QLineEdit()
        self.vehicle_input.setPlaceholderText("Vehicle number")
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Diesel", "Maintenance", "Toll", "Other"])
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setRange(0, 1000000)
        self.amount_input.setDecimals(2)
        self.amount_input.setPrefix("Rs. ")
        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText("Notes (optional)")
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_expense)

        f.addWidget(QLabel("Driver"))
        f.addWidget(self.driver_combo)
        f.addWidget(QLabel("Vehicle"))
        f.addWidget(self.vehicle_input)
        f.addWidget(QLabel("Type"))
        f.addWidget(self.type_combo)
        f.addWidget(QLabel("Amount"))
        f.addWidget(self.amount_input)
        f.addWidget(QLabel("Date"))
        f.addWidget(self.date_edit)
        f.addWidget(self.notes_input)
        f.addWidget(save_btn)
        layout.addWidget(form)

        # Listing
        list_group = QGroupBox("Expenses (By Day)")
        l = QHBoxLayout(list_group)
        self.list_date = QDateEdit()
        self.list_date.setDate(QDate.currentDate())
        self.list_date.setCalendarPopup(True)
        refresh_btn = QPushButton("Load")
        refresh_btn.clicked.connect(self.load_expenses)
        l.addWidget(self.list_date)
        l.addWidget(refresh_btn)
        layout.addWidget(list_group)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Driver", "Vehicle", "Type", "Amount", "Date", "Notes"])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

    def load_employees(self):
        emps = self.db_manager.get_employees()
        self.driver_combo.clear()
        self.driver_combo.addItem("-", {"id": None, "name": "-"})
        for e in emps:
            if e['role'] == 'Driver':
                self.driver_combo.addItem(e['name'], e)

    def save_expense(self):
        driver = self.driver_combo.currentData()
        driver_id = driver.get('id') if driver else None
        driver_name = driver.get('name') if driver else self.current_user.get('full_name', '')
        vehicle = self.vehicle_input.text().strip()
        ex_type = self.type_combo.currentText()
        amount = float(self.amount_input.value())
        notes = self.notes_input.text().strip()
        day = self.date_edit.date().toPython()
        self.db_manager.add_vehicle_expense(driver_id, driver_name, vehicle, ex_type, amount, notes, day)
        self.load_expenses()

    def load_expenses(self):
        day = self.list_date.date().toPython()
        rows = self.db_manager.get_vehicle_expenses_by_date(day.strftime('%Y-%m-%d'))
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem(r.get('driver_name') or ''))
            self.table.setItem(i, 1, QTableWidgetItem(r.get('vehicle_number') or ''))
            self.table.setItem(i, 2, QTableWidgetItem(r.get('expense_type') or ''))
            amt = QTableWidgetItem(f"Rs. {float(r.get('amount', 0)):,.2f}")
            amt.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(i, 3, amt)
            self.table.setItem(i, 4, QTableWidgetItem(str(r.get('expense_date'))))
            self.table.setItem(i, 5, QTableWidgetItem(r.get('notes') or ''))