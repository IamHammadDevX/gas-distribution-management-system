from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QTableWidget, QTableWidgetItem, QGroupBox, QSpinBox, QMessageBox
from PySide6.QtCore import Qt
from src.database_module import DatabaseManager

class CylinderTrackWidget(QWidget):
    def __init__(self, db_manager: DatabaseManager, current_user: dict):
        super().__init__()
        self.db_manager = db_manager
        self.current_user = current_user
        self.catalog_map = {}
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

        # =========== MAIN TABLE: Per Cylinder Purchase Track ==========
        summary_group = QGroupBox("Client Cylinder Return Status")
        s_layout = QVBoxLayout(summary_group)
        self.summary_table = QTableWidget()
        self.summary_table.setColumnCount(7)
        self.summary_table.setHorizontalHeaderLabels([
            "Gas Type", "Sub Type", "Capacity", "Purchased", "Returned", "Pending", "Return Now"
        ])
        self.summary_table.setAlternatingRowColors(True)
        self.summary_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.summary_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.summary_table.verticalHeader().setVisible(False)
        s_layout.addWidget(self.summary_table)
        layout.addWidget(summary_group)

        type_group = QGroupBox("Empty Cylinders Summary (By Gas Type)")
        t_layout = QVBoxLayout(type_group)
        self.type_table = QTableWidget()
        self.type_table.setColumnCount(4)
        self.type_table.setHorizontalHeaderLabels(["Gas Type", "Delivered", "Returned", "Remaining"])
        self.type_table.setAlternatingRowColors(True)
        self.type_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.type_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.type_table.verticalHeader().setVisible(False)
        t_layout.addWidget(self.type_table)
        layout.addWidget(type_group)

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
        self.save_btn = save_btn

        e_layout.addWidget(QLabel("Gas"))
        e_layout.addWidget(self.gas_combo)
        e_layout.addWidget(QLabel("Capacity"))
        e_layout.addWidget(self.capacity_combo)
        e_layout.addWidget(QLabel("Quantity"))
        e_layout.addWidget(self.qty_spin)
        e_layout.addWidget(save_btn)
        layout.addWidget(entry_group)

        edit_group = QGroupBox("Edit Returned Total")
        ed_layout = QHBoxLayout(edit_group)
        self.edit_gas_combo = QComboBox()
        self.edit_capacity_combo = QComboBox()
        self.edit_total_spin = QSpinBox()
        self.edit_total_spin.setRange(0, 100000)
        save_edit_btn = QPushButton("Update Total Returned")
        save_edit_btn.setStyleSheet("""
            QPushButton { background-color: #e67e22; color: white; border: 1px solid #d35400; border-radius: 6px; padding: 6px 12px; font-size: 13px; font-weight: 600; }
            QPushButton:hover { background-color: #d35400; }
            QPushButton:pressed { background-color: #ba4a00; }
        """)
        save_edit_btn.setMinimumWidth(160)
        save_edit_btn.setFixedHeight(32)
        save_edit_btn.clicked.connect(self.save_edit_return_total)
        ed_layout.addWidget(QLabel("Gas"))
        ed_layout.addWidget(self.edit_gas_combo)
        ed_layout.addWidget(QLabel("Capacity"))
        ed_layout.addWidget(self.edit_capacity_combo)
        ed_layout.addWidget(QLabel("Total Returned"))
        ed_layout.addWidget(self.edit_total_spin)
        ed_layout.addWidget(save_edit_btn)
        layout.addWidget(edit_group)

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
        self.pending_map = self.db_manager.get_pending_capacity_map_for_client(client_id)

        def norm_cap(gas_type: str, capacity: str) -> str:
            cap_norm = (capacity or '').replace(' ', '').lower()
            gt = (gas_type or '').strip().upper()
            if gt == 'LPG' and cap_norm in ('12kg', '15kg'):
                return '12/15kg'
            if gt == 'LPG' and cap_norm in ('45kg',):
                return '45kg'
            return capacity or ''

        # Build catalog maps from all company products
        products = self.db_manager.get_gas_products()
        cat_map_norm = {}
        cat_map_raw = {}
        cat_keys = []
        for p in products:
            gt = (p.get('gas_type') or '').strip()
            st = (p.get('sub_type') or '')
            raw_cp = (p.get('capacity') or '')
            cp = norm_cap(gt, raw_cp)
            caps_norm = cat_map_norm.get(gt) or set()
            caps_norm.add(cp)
            cat_map_norm[gt] = caps_norm
            caps_raw = cat_map_raw.get(gt) or set()
            caps_raw.add(raw_cp)
            cat_map_raw[gt] = caps_raw
            key = (gt, cp, st)
            if key not in cat_keys:
                cat_keys.append(key)
        # Persist catalog maps for combos (raw) and summary (normalized)
        self.catalog_map = {gt: sorted(list(caps_norm)) for gt, caps_norm in cat_map_norm.items()}
        self.catalog_map_raw = {gt: sorted(list(caps_raw)) for gt, caps_raw in cat_map_raw.items()}

        # Map summary to quick lookup
        sum_map = {}
        for s in summary:
            k = ((s.get('gas_type') or ''), (s.get('capacity') or ''), (s.get('sub_type') or ''))
            sum_map[k] = {
                'delivered': int(s.get('delivered') or 0),
                'returned': int(s.get('returned') or 0)
            }

        # Render table for all catalog products (initially zeros where absent)
        cat_keys.sort(key=lambda x: (x[0], x[2], x[1]))
        self.summary_table.setRowCount(len(cat_keys))
        for i, (gt, cp, st) in enumerate(cat_keys):
            self.summary_table.setItem(i, 0, QTableWidgetItem(gt))
            self.summary_table.setItem(i, 1, QTableWidgetItem(st))
            self.summary_table.setItem(i, 2, QTableWidgetItem(cp))
            vals = sum_map.get((gt, cp, st)) or {'delivered': 0, 'returned': 0}
            purchased = int(vals['delivered'])
            returned = int(vals['returned'])
            if returned > purchased:
                returned = purchased
            remaining = purchased - returned
            self.summary_table.setItem(i, 3, QTableWidgetItem(str(purchased)))
            self.summary_table.setItem(i, 4, QTableWidgetItem(str(returned)))
            pending_item = QTableWidgetItem(str(remaining))
            if remaining == 0:
                pending_item.setForeground(Qt.darkGreen)
            else:
                pending_item.setForeground(Qt.red)
            self.summary_table.setItem(i, 5, pending_item)
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
        # Type-level aggregation
        type_map = {}
        for s in summary:
            gt = s['gas_type']
            d = int(s['delivered'])
            r = int(s['returned'])
            prev = type_map.get(gt)
            if prev:
                prev['delivered'] += d
                prev['returned'] += r
            else:
                type_map[gt] = {'delivered': d, 'returned': r}
        types = sorted(list(type_map.keys()))
        self.type_table.setRowCount(len(types))
        for i, gt in enumerate(types):
            d = type_map[gt]['delivered']
            r = type_map[gt]['returned']
            rem = d - r
            self.type_table.setItem(i, 0, QTableWidgetItem(gt))
            self.type_table.setItem(i, 1, QTableWidgetItem(str(d)))
            self.type_table.setItem(i, 2, QTableWidgetItem(str(r)))
            self.type_table.setItem(i, 3, QTableWidgetItem(str(rem)))
        # populate return entry combos from full catalog (raw capacities)
        self.gas_combo.clear()
        self.gas_combo.addItems(sorted(list(self.catalog_map_raw.keys())))
        self.capacity_combo.clear()
        first_gas = self.gas_combo.currentText()
        caps = sorted(self.catalog_map_raw.get(first_gas, []))
        self.capacity_combo.addItems(caps)
        self.gas_combo.currentTextChanged.connect(self.update_return_capacities_from_map)
        self.capacity_combo.currentTextChanged.connect(self.update_return_qty_limit)
        # populate edit combos for products (full catalog, raw capacities)
        gas_all = sorted(list(self.catalog_map_raw.keys()))
        self.edit_gas_combo.blockSignals(True)
        self.edit_capacity_combo.blockSignals(True)
        self.edit_gas_combo.clear()
        self.edit_gas_combo.addItems(gas_all)
        self.edit_gas_combo.blockSignals(False)
        self.edit_gas_combo.currentTextChanged.connect(self.update_edit_capacities)
        self.edit_capacity_combo.clear()
        self.update_edit_capacities()
        self.edit_capacity_combo.currentTextChanged.connect(self.update_edit_spin_limits)
        self.update_edit_spin_limits()

    def start_return_from_row(self, row):
        gas = self.summary_table.item(row, 0).text()
        cap = self.summary_table.item(row, 2).text()
        if gas.upper() == 'LPG' and cap.strip() == '12/15kg':
            caps = self.catalog_map_raw.get('LPG', []) if hasattr(self, 'catalog_map_raw') else []
            best_cap = None
            best_remaining = -1
            client = self.client_combo.currentData()
            if client:
                for c in caps:
                    d_rows = self.db_manager.execute_query(
                        'SELECT COALESCE(SUM(quantity),0) as total FROM gate_passes WHERE client_id = ? AND gas_type = ? AND capacity = ?',
                        (client['id'], gas, c)
                    )
                    i_rows = self.db_manager.execute_query(
                        'SELECT COALESCE(SUM(quantity),0) as total FROM client_initial_outstanding WHERE client_id = ? AND gas_type = ? AND capacity = ?',
                        (client['id'], gas, c)
                    )
                    r_rows = self.db_manager.execute_query(
                        'SELECT COALESCE(SUM(quantity),0) as total FROM cylinder_returns WHERE client_id = ? AND gas_type = ? AND capacity = ?',
                        (client['id'], gas, c)
                    )
                    delivered = int(d_rows[0]['total']) if d_rows else 0
                    initial_delivered = int(i_rows[0]['total']) if i_rows else 0
                    returned = int(r_rows[0]['total']) if r_rows else 0
                    remaining = (delivered + initial_delivered) - returned
                    if remaining > best_remaining:
                        best_remaining = remaining
                        best_cap = c
            cap = best_cap or (caps[0] if caps else cap)
        self.gas_combo.setCurrentText(gas)
        self.capacity_combo.setCurrentText(cap)
        self.update_return_qty_limit()

    def save_return(self):
        client = self.client_combo.currentData()
        if not client:
            return
        gas = self.gas_combo.currentText()
        cap = self.capacity_combo.currentText()
        qty = int(self.qty_spin.value())
        # Validate remaining directly from DB for selected gas/capacity
        d_rows = self.db_manager.execute_query(
            'SELECT COALESCE(SUM(quantity),0) as total FROM gate_passes WHERE client_id = ? AND gas_type = ? AND capacity = ?',
            (client['id'], gas, cap)
        )
        i_rows = self.db_manager.execute_query(
            'SELECT COALESCE(SUM(quantity),0) as total FROM client_initial_outstanding WHERE client_id = ? AND gas_type = ? AND capacity = ?',
            (client['id'], gas, cap)
        )
        r_rows = self.db_manager.execute_query(
            'SELECT COALESCE(SUM(quantity),0) as total FROM cylinder_returns WHERE client_id = ? AND gas_type = ? AND capacity = ?',
            (client['id'], gas, cap)
        )
        delivered = int(d_rows[0]['total']) if d_rows else 0
        initial_delivered = int(i_rows[0]['total']) if i_rows else 0
        returned = int(r_rows[0]['total']) if r_rows else 0
        remaining = (delivered + initial_delivered) - returned
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

    def update_return_capacities_from_map(self):
        g = self.gas_combo.currentText()
        caps = sorted(self.catalog_map_raw.get(g, []))
        self.capacity_combo.blockSignals(True)
        self.capacity_combo.clear()
        self.capacity_combo.addItems(caps)
        self.capacity_combo.blockSignals(False)
        self.update_return_qty_limit()

    def update_return_qty_limit(self):
        g = self.gas_combo.currentText()
        c = self.capacity_combo.currentText()
        current = self.client_combo.currentData()
        if not current or not g or not c:
            return
        client_id = current['id']
        d_rows = self.db_manager.execute_query(
            'SELECT COALESCE(SUM(quantity),0) as total FROM gate_passes WHERE client_id = ? AND gas_type = ? AND capacity = ?',
            (client_id, g, c)
        )
        i_rows = self.db_manager.execute_query(
            'SELECT COALESCE(SUM(quantity),0) as total FROM client_initial_outstanding WHERE client_id = ? AND gas_type = ? AND capacity = ?',
            (client_id, g, c)
        )
        r_rows = self.db_manager.execute_query(
            'SELECT COALESCE(SUM(quantity),0) as total FROM cylinder_returns WHERE client_id = ? AND gas_type = ? AND capacity = ?',
            (client_id, g, c)
        )
        delivered = int(d_rows[0]['total']) if d_rows else 0
        initial_delivered = int(i_rows[0]['total']) if i_rows else 0
        returned = int(r_rows[0]['total']) if r_rows else 0
        rem = max(0, (delivered + initial_delivered) - returned)
        self.qty_spin.setMinimum(0)
        self.qty_spin.setMaximum(rem)
        self.qty_spin.setValue(rem if rem > 0 else 0)
        if hasattr(self, 'save_btn'):
            self.save_btn.setEnabled(rem > 0)

    def update_edit_capacities(self):
        gt = self.edit_gas_combo.currentText()
        caps = sorted(self.catalog_map_raw.get(gt, []))
        self.edit_capacity_combo.clear()
        self.edit_capacity_combo.addItems(caps)

    def update_edit_spin_limits(self):
        current = self.client_combo.currentData()
        if not current:
            return
        client_id = current['id']
        g = self.edit_gas_combo.currentText()
        c = self.edit_capacity_combo.currentText()
        d_rows = self.db_manager.execute_query(
            'SELECT COALESCE(SUM(quantity),0) as total FROM gate_passes WHERE client_id = ? AND gas_type = ? AND capacity = ?',
            (client_id, g, c)
        )
        i_rows = self.db_manager.execute_query(
            'SELECT COALESCE(SUM(quantity),0) as total FROM client_initial_outstanding WHERE client_id = ? AND gas_type = ? AND capacity = ?',
            (client_id, g, c)
        )
        r_rows = self.db_manager.execute_query(
            'SELECT COALESCE(SUM(quantity),0) as total FROM cylinder_returns WHERE client_id = ? AND gas_type = ? AND capacity = ?',
            (client_id, g, c)
        )
        purchased = int(d_rows[0]['total']) + int(i_rows[0]['total']) if d_rows and i_rows else 0
        returned = int(r_rows[0]['total']) if r_rows else 0
        self.edit_total_spin.setMaximum(purchased)
        self.edit_total_spin.setValue(returned)

    def save_edit_return_total(self):
        client = self.client_combo.currentData()
        if not client:
            return
        g = self.edit_gas_combo.currentText()
        c = self.edit_capacity_combo.currentText()
        new_total = int(self.edit_total_spin.value())
        d_rows = self.db_manager.execute_query(
            'SELECT COALESCE(SUM(quantity),0) as total FROM gate_passes WHERE client_id = ? AND gas_type = ? AND capacity = ?',
            (client['id'], g, c)
        )
        i_rows = self.db_manager.execute_query(
            'SELECT COALESCE(SUM(quantity),0) as total FROM client_initial_outstanding WHERE client_id = ? AND gas_type = ? AND capacity = ?',
            (client['id'], g, c)
        )
        purchased = int(d_rows[0]['total']) + int(i_rows[0]['total']) if d_rows and i_rows else 0
        if new_total > purchased:
            QMessageBox.warning(self, "Invalid Quantity", f"Total returned {new_total} cannot exceed delivered {purchased}.")
            return
        try:
            self.db_manager.update_total_return_for_client_product(client['id'], g, c, new_total)
            QMessageBox.information(self, "Updated", "Total returned updated.")
            self.load_summary()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
