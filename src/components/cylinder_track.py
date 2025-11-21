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
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Cylinder Track")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title)

        bar = QHBoxLayout()
        bar.setSpacing(10)
        self.client_combo = QComboBox()
        self.client_combo.currentIndexChanged.connect(self.load_summary)
        bar.addWidget(self.client_combo)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_summary)
        bar.addWidget(refresh_btn)
        layout.addLayout(bar)

        summary_group = QGroupBox("Per-client Cylinder Summary")
        s_layout = QVBoxLayout(summary_group)
        self.summary_table = QTableWidget()
        self.summary_table.setColumnCount(6)
        self.summary_table.setHorizontalHeaderLabels(["Gas Type", "Sub Type", "Capacity", "Delivered", "Returned", "Remaining"])
        self.summary_table.setAlternatingRowColors(True)
        self.summary_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.summary_table.setEditTriggers(QTableWidget.NoEditTriggers)
        s_layout.addWidget(self.summary_table)
        layout.addWidget(summary_group)

        deliveries_group = QGroupBox("Deliveries & Returns (Gate Passes)")
        d_layout = QVBoxLayout(deliveries_group)
        self.deliveries_table = QTableWidget()
        self.deliveries_table.setColumnCount(9)
        self.deliveries_table.setHorizontalHeaderLabels(["Gate Pass #", "Gas", "Sub Type", "Capacity", "Delivered", "Returned", "Remaining", "Out", "In"])
        self.deliveries_table.setAlternatingRowColors(True)
        self.deliveries_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.deliveries_table.setEditTriggers(QTableWidget.NoEditTriggers)
        d_layout.addWidget(self.deliveries_table)
        layout.addWidget(deliveries_group)

        entry_group = QGroupBox("Record Cylinder Return")
        e_layout = QHBoxLayout(entry_group)
        self.gas_combo = QComboBox()
        self.capacity_combo = QComboBox()
        self.qty_spin = QSpinBox()
        self.qty_spin.setRange(1, 1000)
        save_btn = QPushButton("Save Return")
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
        if not current:
            self.summary_table.setRowCount(0)
            return
        client_id = current['id']
        summary = self.db_manager.get_cylinder_summary_for_client(client_id)
        self.summary_table.setRowCount(len(summary))
        gas_types = set()
        capacities = set()
        for i, s in enumerate(summary):
            self.summary_table.setItem(i, 0, QTableWidgetItem(s['gas_type']))
            self.summary_table.setItem(i, 1, QTableWidgetItem(s.get('sub_type') or ''))
            self.summary_table.setItem(i, 2, QTableWidgetItem(s['capacity']))
            self.summary_table.setItem(i, 3, QTableWidgetItem(str(s['delivered'])))
            self.summary_table.setItem(i, 4, QTableWidgetItem(str(s['returned'])))
            rem_item = QTableWidgetItem(str(s['remaining']))
            if s['remaining'] > 0:
                rem_item.setForeground(Qt.red)
            else:
                rem_item.setForeground(Qt.darkGreen)
            self.summary_table.setItem(i, 5, rem_item)
            gas_types.add(s['gas_type'])
            capacities.add(s['capacity'])
        # populate return entry combos from summary
        self.gas_combo.clear()
        self.gas_combo.addItems(sorted(list(gas_types)))
        self.capacity_combo.clear()
        self.capacity_combo.addItems(sorted(list(capacities)))

        # load deliveries table
        deliveries = self.db_manager.get_client_deliveries_with_returns(client_id)
        self.deliveries_table.setRowCount(len(deliveries))
        for i, d in enumerate(deliveries):
            self.deliveries_table.setItem(i, 0, QTableWidgetItem(d['gate_pass_number']))
            self.deliveries_table.setItem(i, 1, QTableWidgetItem(d['gas_type']))
            self.deliveries_table.setItem(i, 2, QTableWidgetItem(d.get('sub_type') or ''))
            self.deliveries_table.setItem(i, 3, QTableWidgetItem(d['capacity']))
            self.deliveries_table.setItem(i, 4, QTableWidgetItem(str(d['delivered'])))
            self.deliveries_table.setItem(i, 5, QTableWidgetItem(str(d['returned'])))
            rem = QTableWidgetItem(str(d['remaining']))
            if d['remaining'] > 0:
                rem.setForeground(Qt.red)
            else:
                rem.setForeground(Qt.darkGreen)
            self.deliveries_table.setItem(i, 6, rem)
            out_item = QTableWidgetItem(d['time_out'][:16] if d['time_out'] else '')
            self.deliveries_table.setItem(i, 7, out_item)
            in_item = QTableWidgetItem(d['time_in'][:16] if d['time_in'] else 'Not returned')
            if not d['time_in']:
                in_item.setForeground(Qt.red)
            else:
                in_item.setForeground(Qt.darkGreen)
            self.deliveries_table.setItem(i, 8, in_item)

    def save_return(self):
        client = self.client_combo.currentData()
        if not client:
            return
        gas = self.gas_combo.currentText()
        cap = self.capacity_combo.currentText()
        qty = int(self.qty_spin.value())
        # try to link to selected delivery row if any
        gate_pass_id = None
        delivery_row = self.deliveries_table.currentRow()
        if delivery_row >= 0:
            dp_gas = self.deliveries_table.item(delivery_row, 1).text()
            dp_cap = self.deliveries_table.item(delivery_row, 2).text()
            if dp_gas == gas and dp_cap == cap:
                # hidden mapping via loading sequence; we need gate_pass_id via fetch again
                deliveries = self.db_manager.get_client_deliveries_with_returns(client['id'])
                if 0 <= delivery_row < len(deliveries):
                    gate_pass_id = deliveries[delivery_row]['gate_pass_id']
        if gate_pass_id is None:
            gate_pass_id = self.db_manager.find_latest_gate_pass_for_product(client['id'], gas, cap)
        # validate remaining against summary
        remaining = 0
        for i in range(self.summary_table.rowCount()):
            if self.summary_table.item(i, 0).text() == gas and self.summary_table.item(i, 2).text() == cap:
                remaining = int(self.summary_table.item(i, 5).text())
                break
        if qty > remaining and remaining > 0:
            QMessageBox.warning(self, "Invalid Quantity", f"Return quantity {qty} exceeds remaining {remaining}.")
            return
        self.db_manager.add_cylinder_return(client['id'], gas, cap, qty, gate_pass_id)
        QMessageBox.information(self, "Saved", "Cylinder return recorded.")
        self.load_summary()