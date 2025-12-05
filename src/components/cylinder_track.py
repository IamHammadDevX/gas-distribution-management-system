from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QTableWidget, QTableWidgetItem, QPushButton, QDialog,
    QFormLayout, QDialogButtonBox, QSpinBox, QMessageBox
)
from PySide6.QtCore import Qt
from src.database_module import DatabaseManager


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
        layout = QVBoxLayout(self)
        form = QFormLayout()
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
            try:
                from PySide6.QtWidgets import QApplication
                mw = None
                for w in QApplication.topLevelWidgets():
                    if hasattr(w, 'refresh_dashboard'):
                        mw = w
                        break
                if mw:
                    mw.refresh_dashboard()
            except Exception:
                pass
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to save return: {str(e)}")


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
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Cylinder Track")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title)

        header = QHBoxLayout()
        header.setSpacing(10)
        header.addWidget(QLabel("Client:"))
        self.client_combo = QComboBox()
        self.client_combo.setMinimumWidth(280)
        self.client_combo.currentIndexChanged.connect(self.on_client_changed)
        header.addWidget(self.client_combo)
        layout.addLayout(header)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Product", "Capacity", "Delivered", "Returned", "Pending", "Status", "Actions"
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

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
                prods = self.db_manager.get_all_company_products()
                rows = []
                for p in prods:
                    rows.append({
                        'gas_type': p['gas_type'],
                        'sub_type': p.get('sub_type'),
                        'capacity': p['capacity'],
                        'delivered': 0,
                        'returned': 0,
                        'pending': 0,
                        'status': 'Done'
                    })
                self._populate(rows)
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to refresh data: {str(e)}")

    def _populate(self, rows):
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            prod_name = f"{r['gas_type']}{(' ' + r['sub_type']) if r.get('sub_type') else ''}"
            self.table.setItem(i, 0, QTableWidgetItem(prod_name))
            self.table.setItem(i, 1, QTableWidgetItem(r['capacity']))
            self.table.setItem(i, 2, QTableWidgetItem(str(int(r['delivered']))))
            self.table.setItem(i, 3, QTableWidgetItem(str(int(r['returned']))))
            self.table.setItem(i, 4, QTableWidgetItem(str(int(r['pending']))))
            status_item = QTableWidgetItem(r.get('status') or ('Done' if int(r['pending']) == 0 else 'Pending'))
            if int(r['pending']) > 0:
                status_item.setForeground(Qt.darkYellow)
            else:
                status_item.setForeground(Qt.darkGreen)
            self.table.setItem(i, 5, status_item)

            actions_widget = QWidget()
            h = QHBoxLayout(actions_widget)
            h.setContentsMargins(5, 5, 5, 5)
            btn = QPushButton("Return")
            btn.setEnabled(int(r['pending']) > 0 and self.current_client is not None)
            def open_dialog(row_data=r):
                if not self.current_client:
                    return
                dlg = ReturnDialog(self.db_manager, self.current_client, row_data, self)
                if dlg.exec() == QDialog.Accepted:
                    self.refresh_data()
            btn.clicked.connect(lambda _checked=False, row_data=r: open_dialog(row_data))
            h.addWidget(btn)
            self.table.setCellWidget(i, 6, actions_widget)
