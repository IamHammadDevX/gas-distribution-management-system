from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QTableWidget, QTableWidgetItem, QPushButton, QDialog,
    QFormLayout, QDialogButtonBox, QSpinBox, QMessageBox, QDoubleSpinBox, QTextEdit,
    QFrame, QHeaderView, QAbstractItemView
)
from PySide6.QtCore import Qt
from src.database_module import DatabaseManager
from src.components.ui_helpers import refresh_application_views


class ReturnDialog(QDialog):
    def __init__(self, db_manager: DatabaseManager, client: dict, product_row: dict, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.client = client
        self.product_row = product_row
        self.setWindowTitle("Record Cylinder Return")
        self.setFixedSize(420, 240)
        self._init_ui()

    def _init_ui(self):
        self.setStyleSheet("""
            QDialog { background-color: #f5f6f8; }
            QLabel { color: #1f2937; font-size: 13px; }
            QSpinBox {
                background: #ffffff;
                border: 1px solid #cfd7df;
                border-radius: 6px;
                padding: 6px 8px;
                min-height: 28px;
            }
            QPushButton {
                border-radius: 5px;
                padding: 5px 10px;
                font-size: 12px;
                font-weight: 600;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignLeft)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(8)
        prod_name = f"{self.product_row['gas_type']}{(' ' + self.product_row['sub_type']) if self.product_row.get('sub_type') else ''}"
        form.addRow("Product:", QLabel(f"{prod_name} - {self.product_row['capacity']}"))
        form.addRow("Pending:", QLabel(str(int(self.product_row.get('pending') or 0))))
        self.qty_spin = QSpinBox()
        self.qty_spin.setRange(1, int(self.product_row.get('pending') or 0))
        self.qty_spin.setValue(int(self.product_row.get('pending') or 0))
        form.addRow("Return Qty:", self.qty_spin)
        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _save(self):
        qty = int(self.qty_spin.value())
        if qty <= 0:
            QMessageBox.warning(self, "Invalid Quantity", "Return quantity must be greater than zero.")
            return
        try:
            cap = self.product_row['capacity']
            if self.product_row['gas_type'] == 'LPG' and cap == '12/15kg':
                cap = '12kg'
            self.db_manager.add_cylinder_return(
                self.client['id'],
                self.product_row['gas_type'],
                self.product_row.get('sub_type') or None,
                cap,
                qty
            )
            refresh_application_views("cylinder_availability", "cylinder_track", "weekly_payments", "reports")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to save return: {str(e)}")


class LPGRefillDialog(QDialog):
    def __init__(self, db_manager: DatabaseManager, client: dict, product_row: dict, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.client = client
        self.product_row = product_row
        self.setWindowTitle("Record LPG Refill")
        self.setFixedSize(440, 320)
        self._init_ui()

    def _init_ui(self):
        self.setStyleSheet("""
            QDialog { background-color: #f5f6f8; }
            QLabel { color: #1f2937; font-size: 13px; }
            QSpinBox, QDoubleSpinBox, QComboBox, QTextEdit {
                background: #ffffff;
                border: 1px solid #cfd7df;
                border-radius: 6px;
                padding: 6px 8px;
                min-height: 28px;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignLeft)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(8)

        prod_name = f"{self.product_row['gas_type']} {self.product_row['capacity']}".strip()
        form.addRow("Product:", QLabel(prod_name))
        form.addRow("Empty Balance:", QLabel(str(int(self.product_row.get('empty_balance') or 0))))

        self.qty_spin = QSpinBox()
        self.qty_spin.setRange(1, max(1, int(self.product_row.get('empty_balance') or 0)))
        self.qty_spin.setValue(max(1, int(self.product_row.get('empty_balance') or 0)))
        form.addRow("Refill Qty:", self.qty_spin)

        self.supplier_combo = QComboBox()
        self.supplier_combo.addItem("Company Stock / No Supplier", None)
        for supplier in self.db_manager.get_suppliers():
            self.supplier_combo.addItem(supplier['name'], supplier)
        form.addRow("Source Supplier:", self.supplier_combo)

        self.unit_price_spin = QDoubleSpinBox()
        self.unit_price_spin.setRange(0, 1000000)
        self.unit_price_spin.setDecimals(2)
        self.unit_price_spin.setPrefix("Rs. ")
        form.addRow("Unit Price:", self.unit_price_spin)

        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(80)
        self.notes_input.setPlaceholderText("Optional notes for this refill entry")
        form.addRow("Notes:", self.notes_input)
        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _save(self):
        try:
            product_id = self.db_manager.resolve_tracking_product_id(
                self.product_row['gas_type'],
                self.product_row['capacity'],
                self.product_row.get('sub_type'),
            )
            if not product_id:
                raise ValueError("No LPG product configuration was found for this row.")
            supplier = self.supplier_combo.currentData()
            current_user = getattr(self.parent(), 'current_user', {}) or {}
            self.db_manager.add_lpg_refill(
                client_id=self.client['id'],
                gas_product_id=product_id,
                quantity=int(self.qty_spin.value()),
                supplier_id=supplier['id'] if supplier else None,
                unit_price=float(self.unit_price_spin.value()),
                notes=self.notes_input.toPlainText().strip(),
                created_by=current_user.get('id') if isinstance(current_user, dict) else None,
            )
            refresh_application_views("cylinder_track", "supplier_payments", "weekly_payments", "daily_transactions", "reports")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to save LPG refill: {str(e)}")


class CylinderTrackWidget(QWidget):
    def __init__(self, db_manager: DatabaseManager, current_user: dict):
        super().__init__()
        self.db_manager = db_manager
        self.current_user = current_user
        self.current_client = None
        self._init_ui()
        self.load_clients()
        self.refresh_data()

    def _init_ui(self):
        self.setStyleSheet("""
            QWidget { background-color: #f5f6f8; color: #1f2937; font-size: 13px; }
            QLabel#titleLabel { font-size: 24px; font-weight: 700; color: #1f4f82; }
            QFrame#sectionCard { background: #ffffff; border: 1px solid #dbe1e7; border-radius: 10px; }
            QLineEdit, QComboBox {
                background: #ffffff;
                border: 1px solid #cfd7df;
                border-radius: 6px;
                padding: 6px 8px;
                min-height: 30px;
            }
            QTableWidget {
                background: #ffffff;
                border: 1px solid #d7dde3;
                border-radius: 8px;
                gridline-color: #e9edf1;
            }
            QHeaderView::section {
                background: #1f4f82;
                color: #ffffff;
                border: none;
                border-right: 1px solid #174066;
                border-bottom: 1px solid #174066;
                padding: 8px;
                font-weight: 600;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(12, 12, 12, 12)

        title = QLabel("Cylinder Track")
        title.setObjectName("titleLabel")
        layout.addWidget(title)

        header_card = QFrame()
        header_card.setObjectName("sectionCard")
        header = QHBoxLayout(header_card)
        header.setSpacing(10)
        header.setContentsMargins(10, 10, 10, 10)
        header.addWidget(QLabel("Client:"))
        self.client_combo = QComboBox()
        self.client_combo.setMinimumWidth(300)
        self.client_combo.currentIndexChanged.connect(self.on_client_changed)
        header.addWidget(self.client_combo, 1)
        layout.addWidget(header_card)

        table_card = QFrame()
        table_card.setObjectName("sectionCard")
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(10, 10, 10, 10)
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "Product", "Capacity", "Delivered", "Returned", "Pending Client", "LPG Refilled", "Empty Balance", "Status", "Actions"
        ])
        self._setup_table_base()
        self._set_table_mode_details()
        table_layout.addWidget(self.table)
        layout.addWidget(table_card, 1)

    def _setup_table_base(self):
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setWordWrap(True)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(38)
        self.table.setMinimumHeight(340)

    def _set_table_mode_all_clients(self):
        header = self.table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.setColumnWidth(1, 140)
        self.table.setColumnWidth(2, 130)

    def _set_table_mode_details(self):
        header = self.table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.Fixed)
        self.table.setColumnWidth(8, 126)

    def load_clients(self):
        try:
            clients = self.db_manager.get_clients()
            self.client_combo.clear()
            self.client_combo.addItem("-- All Clients --", None)
            for c in clients:
                label = f"{c['name']}"
                if c.get('company'):
                    label += f" - {c['company']}"
                self.client_combo.addItem(label, c)
            self.client_combo.setCurrentIndex(0)
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load clients: {str(e)}")

    def on_client_changed(self):
        idx = self.client_combo.currentIndex()
        data = self.client_combo.itemData(idx)
        self.current_client = data
        self.refresh_data()

    def refresh_data(self):
        try:
            if self.current_client and isinstance(self.current_client, dict):
                rows = self.db_manager.get_client_cylinder_status(self.current_client['id'])
                for r in rows:
                    r['status'] = 'Done' if int(r['pending']) <= 0 else 'Pending'
                self._populate(rows)
            else:
                # Show aggregate or just empty list for "All Clients"?
                # The user wants to see cylinder track. If "All Clients" is selected, 
                # showing just zeros is misleading. 
                # Let's show all clients summary instead.
                all_status = self.db_manager.get_pending_cylinder_summary_by_client()
                self._populate_all_clients(all_status)
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to refresh data: {str(e)}")

    def _populate_all_clients(self, rows):
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Client", "Pending Cylinders", "Phone", "Company"])
        self._set_table_mode_all_clients()
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem(r['name']))
            self.table.setItem(i, 1, QTableWidgetItem(str(r['pending_cylinders'])))
            self.table.setItem(i, 2, QTableWidgetItem(r['phone']))
            self.table.setItem(i, 3, QTableWidgetItem(r.get('company') or ''))
            self.table.setRowHeight(i, 38)

    def _populate(self, rows):
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "Product", "Capacity", "Delivered", "Returned", "Pending Client", "LPG Refilled", "Empty Balance", "Status", "Actions"
        ])
        self._set_table_mode_details()
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            prod_name = f"{r['gas_type']}{(' ' + r['sub_type']) if r.get('sub_type') else ''}"
            self.table.setItem(i, 0, QTableWidgetItem(prod_name))
            self.table.setItem(i, 1, QTableWidgetItem(r['capacity']))
            self.table.setItem(i, 2, QTableWidgetItem(str(int(r['delivered']))))
            self.table.setItem(i, 3, QTableWidgetItem(str(int(r['returned']))))
            self.table.setItem(i, 4, QTableWidgetItem(str(int(r['pending']))))
            self.table.setItem(i, 5, QTableWidgetItem(str(int(r.get('refilled') or 0))))
            self.table.setItem(i, 6, QTableWidgetItem(str(int(r.get('empty_balance') or 0))))
            status_item = QTableWidgetItem(r.get('status') or ('Done' if int(r['pending']) == 0 else 'Pending'))
            if int(r['pending']) > 0:
                status_item.setForeground(Qt.darkYellow)
            else:
                status_item.setForeground(Qt.darkGreen)
            self.table.setItem(i, 7, status_item)

            actions_widget = QWidget()
            h = QHBoxLayout(actions_widget)
            h.setContentsMargins(1, 1, 1, 1)
            h.setSpacing(2)
            h.setAlignment(Qt.AlignCenter)
            btn = QPushButton("Return")
            btn.setFixedWidth(52)
            btn.setFixedHeight(22)
            btn.setFocusPolicy(Qt.NoFocus)
            btn.setStyleSheet(
                "QPushButton { background-color: #1a73e8; color: white; border: 1px solid #125bc4; border-radius: 5px; padding: 1px 4px; font-size: 10px; font-weight: 600; }"
                "QPushButton:hover { background-color: #1765cb; }"
                "QPushButton:pressed { background-color: #125bc4; }"
                "QPushButton:disabled { background-color: #aab7c4; border-color: #9aa8b6; color: #eef2f6; }"
            )
            btn.setEnabled(int(r['pending']) > 0 and self.current_client is not None)
            def open_dialog(row_data=r):
                if not self.current_client:
                    return
                dlg = ReturnDialog(self.db_manager, self.current_client, row_data, self)
                if dlg.exec() == QDialog.Accepted:
                    self.refresh_data()
            btn.clicked.connect(lambda _checked=False, row_data=r: open_dialog(row_data))
            h.addWidget(btn)
            refill_btn = QPushButton("Refill")
            refill_btn.setFixedWidth(52)
            refill_btn.setFixedHeight(22)
            refill_btn.setFocusPolicy(Qt.NoFocus)
            refill_btn.setStyleSheet(
                "QPushButton { background-color: #16a085; color: white; border: 1px solid #117864; border-radius: 5px; padding: 1px 4px; font-size: 10px; font-weight: 600; }"
                "QPushButton:hover { background-color: #138d75; }"
                "QPushButton:pressed { background-color: #117864; }"
                "QPushButton:disabled { background-color: #aab7c4; border-color: #9aa8b6; color: #eef2f6; }"
            )
            refill_btn.setEnabled(
                self.current_client is not None
                and r.get('gas_type') == 'LPG'
                and int(r.get('empty_balance') or 0) > 0
            )
            def open_refill_dialog(row_data=r):
                if not self.current_client:
                    return
                dlg = LPGRefillDialog(self.db_manager, self.current_client, row_data, self)
                if dlg.exec() == QDialog.Accepted:
                    self.refresh_data()
            refill_btn.clicked.connect(lambda _checked=False, row_data=r: open_refill_dialog(row_data))
            h.addWidget(refill_btn)
            self.table.setCellWidget(i, 8, actions_widget)
            self.table.setRowHeight(i, 34)
