from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QTableWidget, QTableWidgetItem, QGroupBox, QSpinBox, QMessageBox
from PySide6.QtCore import Qt
from database_module import DatabaseManager

class CylinderTrackWidget(QWidget):
    def __init__(self, db_manager: DatabaseManager, current_user: dict):
        super().__init__()
        self.db_manager = db_manager
        self.current_user = current_user
        self.clients = []
        self.init_ui()
        self.load_clients()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(18)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Cylinder Track (Client Return Status)")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #205087; margin-bottom: 8px;")
        layout.addWidget(title)

        bar = QHBoxLayout()
        bar.setSpacing(12)
        self.client_combo = QComboBox()
        self.client_combo.setMinimumWidth(300)
        self.client_combo.currentIndexChanged.connect(self.load_summary)
        bar.addWidget(QLabel("Select Client:"))
        bar.addWidget(self.client_combo)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.setStyleSheet("""
            QPushButton { background-color: #3498db; color: white; border: 1px solid #2c81ba; border-radius: 6px; padding: 6px 12px; font-size: 13px; font-weight: 600; }
            QPushButton:hover { background-color: #2c81ba; }
            QPushButton:pressed { background-color: #256fa0; }
        """)
        refresh_btn.setMinimumWidth(96)
        refresh_btn.setFixedHeight(32)
        refresh_btn.clicked.connect(self.load_summary)
        bar.addWidget(refresh_btn)
        layout.addLayout(bar)

        # =========== MAIN TABLE: Per Cylinder Purchase Track ===========
        summary_group = QGroupBox("Client Cylinder Return Status")
        s_layout = QVBoxLayout(summary_group)
        self.summary_table = QTableWidget()
        self.summary_table.setColumnCount(7)
        self.summary_table.setHorizontalHeaderLabels([
            "Gas Type", "Sub Type", "Capacity", "Purchased", "Returned", "Status", "Return Now"
        ])
        self.summary_table.setAlternatingRowColors(True)
        self.summary_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.summary_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.summary_table.verticalHeader().setVisible(False)
        s_layout.addWidget(self.summary_table)
        layout.addWidget(summary_group)

        # =========== Entry controls ===========
        entry_group = QGroupBox("Record Cylinder Return")
        e_layout = QHBoxLayout(entry_group)
        self.gas_combo = QComboBox()
        self.capacity_combo = QComboBox()
        self.qty_spin = QSpinBox()
        self.qty_spin.setRange(1, 1000)
        save_btn = QPushButton("Save Return")
        save_btn.setStyleSheet("""
            QPushButton { background-color: #27ae60; color: white; border: 1px solid #229954; border-radius: 6px; padding: 6px 12px; font-size: 13px; font-weight: 600; }
            QPushButton:hover { background-color: #229954; }
            QPushButton:pressed { background-color: #1e8449; }
        """)
        save_btn.setMinimumWidth(120)
        save_btn.setFixedHeight(32)
        save_btn.clicked.connect(self.save_return)

        e_layout.addWidget(QLabel("Gas"))
        e_layout.addWidget(self.gas_combo)
        e_layout.addWidget(QLabel("Capacity"))
        e_layout.addWidget(self.capacity_combo)
        e_layout.addWidget(QLabel("Quantity"))
        e_layout.addWidget(self.qty_spin)
        e_layout.addWidget(save_btn)
        layout.addWidget(entry_group)

    def load_clients(self):
        self.clients = self.db_manager.get_clients()
        self.client_combo.clear()
        for c in self.clients:
            self.client_combo.addItem(f"{c['name']} ({c['phone']})", c)
        self.load_summary()

    def load_summary(self):
        current = self.client_combo.currentData()
        self.summary_table.setRowCount(0)
        if not current:
            return
        client_id = current['id']
        summary = self.db_manager.get_cylinder_summary_for_client(client_id)
        # Track for combos
        gas_types = set()
        capacities = set()
        self.summary_table.setRowCount(len(summary))
        for i, s in enumerate(summary):
            # Core info
            self.summary_table.setItem(i, 0, QTableWidgetItem(s['gas_type']))
            self.summary_table.setItem(i, 1, QTableWidgetItem(s.get('sub_type') or ''))
            self.summary_table.setItem(i, 2, QTableWidgetItem(s['capacity']))
            purchased = int(s['delivered'])
            returned = int(s['returned'])
            # Ensure returned never exceeds purchased (defensive)
            if returned > purchased:
                returned = purchased
            remaining = purchased - returned
            self.summary_table.setItem(i, 3, QTableWidgetItem(str(purchased)))
            self.summary_table.setItem(i, 4, QTableWidgetItem(str(returned)))
            status_item = QTableWidgetItem("Returned" if remaining == 0 else f"Pending ({remaining})")
            if remaining == 0:
                status_item.setForeground(Qt.darkGreen)
            else:
                status_item.setForeground(Qt.red)
            self.summary_table.setItem(i, 5, status_item)
            # Quick return button cell (for simple UI)
            btn = QPushButton("Return" if remaining > 0 else "Done")
            btn.setStyleSheet("""
                QPushButton { background-color: #8e44ad; color: white; border: 1px solid #7d3c98; border-radius: 6px; padding: 4px 10px; font-size: 12px; font-weight: 600; }
                QPushButton:hover { background-color: #7d3c98; }
                QPushButton:pressed { background-color: #6c3483; }
            """)
            btn.setMinimumWidth(80)
            btn.setFixedHeight(26)
            btn.setEnabled(remaining > 0)
            btn.clicked.connect(lambda _, gi=i: self.start_return_from_row(gi))
            self.summary_table.setCellWidget(i, 6, btn)
            gas_types.add(s['gas_type'])
            capacities.add(s['capacity'])
        # populate return entry combos from summary
        self.gas_combo.clear()
        self.gas_combo.addItems(sorted(list(gas_types)))
        self.capacity_combo.clear()
        self.capacity_combo.addItems(sorted(list(capacities)))

    def start_return_from_row(self, row):
        gas = self.summary_table.item(row, 0).text()
        cap = self.summary_table.item(row, 2).text()
        purchased = int(self.summary_table.item(row, 3).text())
        returned = int(self.summary_table.item(row, 4).text())
        remain = purchased - returned
        self.gas_combo.setCurrentText(gas)
        self.capacity_combo.setCurrentText(cap)
        self.qty_spin.setMaximum(remain)
        self.qty_spin.setValue(remain if remain < 10 and remain != 0 else 1)

    def save_return(self):
        client = self.client_combo.currentData()
        if not client:
            return
        gas = self.gas_combo.currentText()
        cap = self.capacity_combo.currentText()
        qty = int(self.qty_spin.value())
        # validate remaining against summary
        purchased = returned = remaining = 0
        for i in range(self.summary_table.rowCount()):
            if self.summary_table.item(i, 0).text() == gas and self.summary_table.item(i, 2).text() == cap:
                purchased = int(self.summary_table.item(i, 3).text())
                returned = int(self.summary_table.item(i, 4).text())
                # Ensure returned does not exceed purchased
                if returned > purchased:
                    returned = purchased
                remaining = purchased - returned
                break
        # Defensive: don't allow return more than what is remaining
        if qty > remaining:
            QMessageBox.warning(self, "Invalid Quantity", f"Return quantity {qty} exceeds pending {remaining}. Please ensure returned cylinders do not exceed purchased count.")
            return
        if qty < 1:
            QMessageBox.warning(self, "Invalid Quantity", "Please enter return quantity at least 1.")
            return
        # record return (link to cylinder row)
        try:
            self.db_manager.add_cylinder_return(client['id'], gas, cap, qty, None)
            QMessageBox.information(self, "Saved", "Cylinder return recorded.")
            self.load_summary()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))