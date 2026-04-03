from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QHeaderView,
)

from src.components.ui_helpers import refresh_application_views, table_batch_update
from src.database_module import DatabaseManager


class SupplierDialog(QDialog):
    def __init__(self, db_manager: DatabaseManager, supplier_data: dict | None = None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.supplier_data = supplier_data or {}
        self.setWindowTitle("Edit Supplier" if supplier_data else "Add Supplier")
        self.setMinimumWidth(420)
        self._init_ui()
        if supplier_data:
            self._load_data()

    def _init_ui(self):
        self.setStyleSheet("""
            QDialog { background-color: #f5f6f8; }
            QLineEdit, QTextEdit {
                background: #ffffff;
                border: 1px solid #cfd7df;
                border-radius: 6px;
                padding: 6px 8px;
            }
            QLabel { color: #1f2937; }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignLeft)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(8)

        self.name_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.address_input = QLineEdit()
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(90)

        form.addRow("Name *", self.name_input)
        form.addRow("Phone", self.phone_input)
        form.addRow("Address", self.address_input)
        form.addRow("Notes", self.notes_input)
        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_data(self):
        self.name_input.setText(self.supplier_data.get("name") or "")
        self.phone_input.setText(self.supplier_data.get("phone") or "")
        self.address_input.setText(self.supplier_data.get("address") or "")
        self.notes_input.setPlainText(self.supplier_data.get("notes") or "")

    def get_payload(self) -> dict:
        return {
            "name": self.name_input.text().strip(),
            "phone": self.phone_input.text().strip(),
            "address": self.address_input.text().strip(),
            "notes": self.notes_input.toPlainText().strip(),
        }

    def accept(self):
        payload = self.get_payload()
        if not payload["name"]:
            QMessageBox.warning(self, "Validation Error", "Supplier name is required.")
            return
        super().accept()


class SuppliersWidget(QWidget):
    def __init__(self, db_manager: DatabaseManager, current_user: dict):
        super().__init__()
        self.db_manager = db_manager
        self.current_user = current_user
        self._init_ui()
        self.load_suppliers()

    def _init_ui(self):
        self.setStyleSheet("""
            QWidget { background-color: #f5f6f8; color: #1f2937; font-size: 13px; }
            QLabel#titleLabel { font-size: 24px; font-weight: 700; color: #1f4f82; }
            QFrame#sectionCard { background: #ffffff; border: 1px solid #dbe1e7; border-radius: 10px; }
            QLineEdit {
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
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        title = QLabel("Suppliers")
        title.setObjectName("titleLabel")
        layout.addWidget(title)

        top_card = QFrame()
        top_card.setObjectName("sectionCard")
        top_layout = QHBoxLayout(top_card)
        top_layout.setContentsMargins(10, 10, 10, 10)
        top_layout.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search supplier by name, phone, or address...")
        self.search_input.textChanged.connect(self.load_suppliers)
        top_layout.addWidget(self.search_input, 1)

        self.add_btn = self._small_button("Add Supplier", "success")
        self.add_btn.clicked.connect(self.add_supplier)
        top_layout.addWidget(self.add_btn)

        refresh_btn = self._small_button("Refresh", "primary")
        refresh_btn.clicked.connect(self.load_suppliers)
        top_layout.addWidget(refresh_btn)
        layout.addWidget(top_card)

        table_card = QFrame()
        table_card.setObjectName("sectionCard")
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(10, 10, 10, 10)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Name", "Phone", "Address", "Status", "Actions"])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(38)
        header = self.table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        self.table.setColumnWidth(4, 145)
        table_layout.addWidget(self.table)
        layout.addWidget(table_card, 1)

        self.set_role_permissions()

    def _small_button(self, text: str, kind: str = "secondary") -> QPushButton:
        btn = QPushButton(text)
        btn.setFixedHeight(26)
        btn.setFocusPolicy(Qt.NoFocus)
        styles = {
            "primary": (
                "QPushButton { background-color: #1a73e8; color: white; border: 1px solid #125bc4; border-radius: 5px; padding: 3px 8px; font-size: 11px; font-weight: 600; }"
                "QPushButton:hover { background-color: #1765cb; }"
            ),
            "success": (
                "QPushButton { background-color: #28a745; color: white; border: 1px solid #1f8a3a; border-radius: 5px; padding: 3px 8px; font-size: 11px; font-weight: 600; }"
                "QPushButton:hover { background-color: #228d3d; }"
            ),
            "warning": (
                "QPushButton { background-color: #f39c12; color: white; border: 1px solid #d68910; border-radius: 5px; padding: 3px 8px; font-size: 11px; font-weight: 600; }"
                "QPushButton:hover { background-color: #d68910; }"
            ),
            "danger": (
                "QPushButton { background-color: #dc3545; color: white; border: 1px solid #b52a37; border-radius: 5px; padding: 3px 8px; font-size: 11px; font-weight: 600; }"
                "QPushButton:hover { background-color: #c22f3d; }"
            ),
            "secondary": (
                "QPushButton { background-color: #6c757d; color: white; border: 1px solid #596168; border-radius: 5px; padding: 3px 8px; font-size: 11px; font-weight: 600; }"
                "QPushButton:hover { background-color: #5e666d; }"
            ),
        }
        btn.setStyleSheet(styles.get(kind, styles["secondary"]))
        return btn

    def set_role_permissions(self):
        if self.current_user["role"] not in ["Admin", "Accountant"]:
            self.add_btn.setEnabled(False)

    def load_suppliers(self):
        try:
            suppliers = self.db_manager.get_suppliers(self.search_input.text().strip(), active_only=False)
            with table_batch_update(self.table):
                self.table.setRowCount(len(suppliers))
                for row, supplier in enumerate(suppliers):
                    self.table.setItem(row, 0, QTableWidgetItem(supplier.get("name") or ""))
                    self.table.setItem(row, 1, QTableWidgetItem(supplier.get("phone") or ""))
                    self.table.setItem(row, 2, QTableWidgetItem(supplier.get("address") or ""))
                    status_item = QTableWidgetItem("Active" if supplier.get("is_active") else "Inactive")
                    status_item.setForeground(Qt.darkGreen if supplier.get("is_active") else Qt.darkYellow)
                    self.table.setItem(row, 3, status_item)

                    actions = QWidget()
                    action_layout = QHBoxLayout(actions)
                    action_layout.setContentsMargins(0, 0, 0, 0)
                    action_layout.setSpacing(4)
                    action_layout.setAlignment(Qt.AlignCenter)

                    edit_btn = self._small_button("Edit", "warning")
                    edit_btn.setFixedWidth(48)
                    edit_btn.clicked.connect(lambda _checked=False, data=supplier: self.edit_supplier(data))
                    action_layout.addWidget(edit_btn)

                    disable_btn = self._small_button("Disable", "danger")
                    disable_btn.setFixedWidth(68)
                    disable_btn.setEnabled(bool(supplier.get("is_active")))
                    disable_btn.clicked.connect(lambda _checked=False, sid=supplier["id"]: self.deactivate_supplier(sid))
                    action_layout.addWidget(disable_btn)
                    self.table.setCellWidget(row, 4, actions)
        except Exception as exc:
            QMessageBox.critical(self, "Database Error", f"Failed to load suppliers: {exc}")

    def add_supplier(self):
        dlg = SupplierDialog(self.db_manager, parent=self)
        if not dlg.exec():
            return
        payload = dlg.get_payload()
        try:
            self.db_manager.add_supplier(**payload)
            self.load_suppliers()
            refresh_application_views("suppliers", "supplier_payments", "sales", "weekly_payments", "receipts", "daily_transactions")
            QMessageBox.information(self, "Success", "Supplier added successfully.")
        except Exception as exc:
            QMessageBox.critical(self, "Database Error", f"Failed to add supplier: {exc}")

    def edit_supplier(self, supplier_data: dict):
        dlg = SupplierDialog(self.db_manager, supplier_data=supplier_data, parent=self)
        if not dlg.exec():
            return
        payload = dlg.get_payload()
        try:
            self.db_manager.update_supplier(supplier_data["id"], **payload, is_active=bool(supplier_data.get("is_active")))
            self.load_suppliers()
            refresh_application_views("suppliers", "supplier_payments", "sales", "weekly_payments", "receipts", "daily_transactions")
            QMessageBox.information(self, "Success", "Supplier updated successfully.")
        except Exception as exc:
            QMessageBox.critical(self, "Database Error", f"Failed to update supplier: {exc}")

    def deactivate_supplier(self, supplier_id: int):
        reply = QMessageBox.question(
            self,
            "Deactivate Supplier",
            "Do you want to deactivate this supplier? Existing sales will stay unchanged.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        try:
            self.db_manager.deactivate_supplier(supplier_id)
            self.load_suppliers()
            refresh_application_views("suppliers", "supplier_payments", "sales", "weekly_payments", "receipts", "daily_transactions")
            QMessageBox.information(self, "Success", "Supplier deactivated.")
        except Exception as exc:
            QMessageBox.critical(self, "Database Error", f"Failed to deactivate supplier: {exc}")
