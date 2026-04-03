from datetime import date

from PySide6.QtCore import Qt, QDate
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDateEdit,
    QDialog,
    QDoubleSpinBox,
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

from src.components.ui_helpers import as_datetime_text, as_money, refresh_application_views, table_batch_update
from src.database_module import DatabaseManager


class SupplierPaymentDialog(QDialog):
    def __init__(self, db_manager: DatabaseManager, supplier_row: dict, current_user: dict, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.supplier_row = supplier_row
        self.current_user = current_user
        self.setWindowTitle(f"Pay Supplier - {supplier_row['supplier_name']}")
        self.setMinimumWidth(420)
        self._init_ui()

    def _init_ui(self):
        self.setStyleSheet("""
            QDialog { background-color: #f5f6f8; }
            QLabel { color: #1f2937; }
            QComboBox, QDateEdit, QDoubleSpinBox, QTextEdit {
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

        info = QLabel(
            f"Supplier: <b>{self.supplier_row['supplier_name']}</b><br/>"
            f"Remaining Balance: <b>{as_money(self.supplier_row.get('remaining_amount'))}</b>"
        )
        info.setTextFormat(Qt.RichText)
        layout.addWidget(info)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignLeft)
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0, max(0.0, float(self.supplier_row.get('remaining_amount') or 0)))
        self.amount_spin.setDecimals(2)
        self.amount_spin.setPrefix("Rs. ")
        self.payment_date = QDateEdit()
        self.payment_date.setCalendarPopup(True)
        self.payment_date.setDate(QDate.currentDate())
        self.method_combo = QComboBox()
        self.method_combo.addItems(["Cash", "Bank Transfer", "Cheque", "Other"])
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(90)
        self.notes_input.setPlaceholderText("Optional note for this payment")

        form.addRow("Amount:", self.amount_spin)
        form.addRow("Date:", self.payment_date)
        form.addRow("Method:", self.method_combo)
        form.addRow("Notes:", self.notes_input)
        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        save_btn = QPushButton("Save Payment")
        cancel_btn = QPushButton("Cancel")
        save_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(save_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

    def accept(self):
        if float(self.amount_spin.value()) <= 0:
            QMessageBox.warning(self, "Invalid Payment", "Payment amount must be greater than zero.")
            return
        try:
            self.db_manager.record_supplier_fill_payment(
                supplier_id=int(self.supplier_row['supplier_id']),
                amount=float(self.amount_spin.value()),
                payment_date=self.payment_date.date().toString("yyyy-MM-dd"),
                payment_method=self.method_combo.currentText(),
                notes=self.notes_input.toPlainText().strip(),
                created_by=self.current_user.get('id'),
            )
        except Exception as exc:
            QMessageBox.critical(self, "Payment Error", str(exc))
            return
        super().accept()


class SupplierAccountDetailDialog(QDialog):
    def __init__(self, db_manager: DatabaseManager, supplier_row: dict, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.supplier_row = supplier_row
        self.setWindowTitle(f"Supplier Account - {supplier_row['supplier_name']}")
        self.resize(980, 700)
        self._init_ui()
        self.load_data()

    def _init_ui(self):
        self.setStyleSheet("""
            QDialog { background-color: #f5f6f8; }
            QFrame#card { background: #ffffff; border: 1px solid #dbe1e7; border-radius: 10px; }
            QLabel#titleLabel { font-size: 22px; font-weight: 700; color: #1f4f82; }
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
                padding: 8px;
                font-weight: 600;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        title = QLabel(self.supplier_row['supplier_name'])
        title.setObjectName("titleLabel")
        layout.addWidget(title)

        summary_card = QFrame()
        summary_card.setObjectName("card")
        summary_layout = QHBoxLayout(summary_card)
        summary_layout.setContentsMargins(12, 10, 12, 10)
        summary_layout.setSpacing(16)
        self.summary_label = QLabel("")
        self.summary_label.setTextFormat(Qt.RichText)
        summary_layout.addWidget(self.summary_label)
        layout.addWidget(summary_card)

        entry_card = QFrame()
        entry_card.setObjectName("card")
        entry_layout = QVBoxLayout(entry_card)
        entry_layout.setContentsMargins(10, 10, 10, 10)
        entry_layout.addWidget(QLabel("Fill Entries"))
        self.entry_table = QTableWidget()
        self.entry_table.setColumnCount(9)
        self.entry_table.setHorizontalHeaderLabels([
            "Date", "Type", "Client", "Gas", "Capacity", "Qty", "Fill Unit", "Fill Total", "Ref"
        ])
        self._setup_table(self.entry_table)
        entry_layout.addWidget(self.entry_table)
        layout.addWidget(entry_card, 1)

        payment_card = QFrame()
        payment_card.setObjectName("card")
        payment_layout = QVBoxLayout(payment_card)
        payment_layout.setContentsMargins(10, 10, 10, 10)
        payment_layout.addWidget(QLabel("Payment History"))
        self.payment_table = QTableWidget()
        self.payment_table.setColumnCount(5)
        self.payment_table.setHorizontalHeaderLabels(["Date", "Amount", "Method", "Notes", "Created"])
        self._setup_table(self.payment_table)
        payment_layout.addWidget(self.payment_table)
        layout.addWidget(payment_card, 1)

    def _setup_table(self, table: QTableWidget):
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(34)
        header = table.horizontalHeader()
        header.setStretchLastSection(True)

    def load_data(self):
        supplier_id = int(self.supplier_row['supplier_id'])
        summary = self.db_manager.get_supplier_fill_payment_summary(supplier_id=supplier_id)
        row = summary[0] if summary else self.supplier_row
        self.summary_label.setText(
            f"<b>Total Cylinders:</b> {int(row.get('total_cylinders') or 0)}"
            f" &nbsp;&nbsp; <b>Fill Cost:</b> {as_money(row.get('fill_total'))}"
            f" &nbsp;&nbsp; <b>Paid:</b> {as_money(row.get('total_paid'))}"
            f" &nbsp;&nbsp; <b>Remaining:</b> {as_money(row.get('remaining_amount'))}"
        )

        entries = self.db_manager.get_supplier_fill_entries(supplier_id=supplier_id)
        with table_batch_update(self.entry_table):
            self.entry_table.setRowCount(len(entries))
            for idx, entry in enumerate(entries):
                gas_text = entry.get('gas_type') or ''
                if entry.get('sub_type'):
                    gas_text += f" {entry['sub_type']}"
                self.entry_table.setItem(idx, 0, QTableWidgetItem(as_datetime_text(entry.get('created_at'), 16)))
                self.entry_table.setItem(idx, 1, QTableWidgetItem("LPG Refill" if entry.get('entry_type') == 'LPG_REFILL' else "Sale Fill"))
                self.entry_table.setItem(idx, 2, QTableWidgetItem(entry.get('client_name') or ''))
                self.entry_table.setItem(idx, 3, QTableWidgetItem(gas_text))
                self.entry_table.setItem(idx, 4, QTableWidgetItem(entry.get('capacity') or ''))
                self.entry_table.setItem(idx, 5, QTableWidgetItem(str(int(entry.get('quantity') or 0))))
                self.entry_table.setItem(idx, 6, QTableWidgetItem(as_money(entry.get('fill_unit_cost'))))
                self.entry_table.setItem(idx, 7, QTableWidgetItem(as_money(entry.get('fill_total'))))
                self.entry_table.setItem(idx, 8, QTableWidgetItem(entry.get('reference_no') or ''))

        payments = self.db_manager.get_supplier_fill_payment_history(supplier_id)
        with table_batch_update(self.payment_table):
            self.payment_table.setRowCount(len(payments))
            for idx, payment in enumerate(payments):
                self.payment_table.setItem(idx, 0, QTableWidgetItem(payment.get('payment_date') or ''))
                self.payment_table.setItem(idx, 1, QTableWidgetItem(as_money(payment.get('amount'))))
                self.payment_table.setItem(idx, 2, QTableWidgetItem(payment.get('payment_method') or ''))
                self.payment_table.setItem(idx, 3, QTableWidgetItem(payment.get('notes') or ''))
                self.payment_table.setItem(idx, 4, QTableWidgetItem(as_datetime_text(payment.get('created_at'), 16)))


class SupplierPaymentsWidget(QWidget):
    def __init__(self, db_manager: DatabaseManager, current_user: dict):
        super().__init__()
        self.db_manager = db_manager
        self.current_user = current_user
        self._init_ui()
        self.load_data()

    def _init_ui(self):
        self.setStyleSheet("""
            QWidget { background-color: #f5f6f8; color: #1f2937; font-size: 13px; }
            QLabel#titleLabel { font-size: 24px; font-weight: 700; color: #1f4f82; }
            QFrame#sectionCard { background: #ffffff; border: 1px solid #dbe1e7; border-radius: 10px; }
            QLineEdit, QDateEdit {
                background: #ffffff;
                border: 1px solid #cfd7df;
                border-radius: 6px;
                padding: 6px 8px;
                min-height: 28px;
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
                padding: 8px;
                font-weight: 600;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        title = QLabel("Supplier Payments")
        title.setObjectName("titleLabel")
        layout.addWidget(title)

        top_card = QFrame()
        top_card.setObjectName("sectionCard")
        top_layout = QHBoxLayout(top_card)
        top_layout.setContentsMargins(10, 10, 10, 10)
        top_layout.setSpacing(8)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search supplier name...")
        self.search_input.textChanged.connect(self.load_data)
        self.from_date = QDateEdit()
        self.from_date.setCalendarPopup(True)
        self.from_date.setDate(QDate.currentDate().addDays(-30))
        self.from_date.dateChanged.connect(self.load_data)
        self.to_date = QDateEdit()
        self.to_date.setCalendarPopup(True)
        self.to_date.setDate(QDate.currentDate())
        self.to_date.dateChanged.connect(self.load_data)
        refresh_btn = self._action_button("Refresh", "primary")
        refresh_btn.clicked.connect(self.load_data)
        top_layout.addWidget(QLabel("Search:"))
        top_layout.addWidget(self.search_input, 1)
        top_layout.addWidget(QLabel("From:"))
        top_layout.addWidget(self.from_date)
        top_layout.addWidget(QLabel("To:"))
        top_layout.addWidget(self.to_date)
        top_layout.addWidget(refresh_btn)
        layout.addWidget(top_card)

        self.summary_label = QLabel("")
        self.summary_label.setStyleSheet("font-weight: 700; color: #1f4f82;")
        layout.addWidget(self.summary_label)

        table_card = QFrame()
        table_card.setObjectName("sectionCard")
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(10, 10, 10, 10)
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Supplier", "Cylinders", "Other Gas Fill", "LPG Fill", "Total Fill Cost", "Paid", "Remaining", "Actions"
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(36)
        header = self.table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.Fixed)
        self.table.setColumnWidth(7, 132)
        table_layout.addWidget(self.table)
        layout.addWidget(table_card, 1)

    def _action_button(self, text: str, kind: str = "secondary") -> QPushButton:
        btn = QPushButton(text)
        btn.setFixedHeight(24)
        btn.setFocusPolicy(Qt.NoFocus)
        styles = {
            "primary": (
                "QPushButton { background-color: #1a73e8; color: white; border: 1px solid #125bc4; border-radius: 5px; padding: 2px 8px; font-size: 11px; font-weight: 600; }"
                "QPushButton:hover { background-color: #1765cb; }"
                "QPushButton:disabled { background-color: #aab7c4; border-color: #9aa8b6; color: #eef2f6; }"
            ),
            "success": (
                "QPushButton { background-color: #28a745; color: white; border: 1px solid #1f8a3a; border-radius: 5px; padding: 2px 8px; font-size: 11px; font-weight: 600; }"
                "QPushButton:hover { background-color: #228d3d; }"
                "QPushButton:disabled { background-color: #aab7c4; border-color: #9aa8b6; color: #eef2f6; }"
            ),
            "secondary": (
                "QPushButton { background-color: #6c757d; color: white; border: 1px solid #596168; border-radius: 5px; padding: 2px 8px; font-size: 11px; font-weight: 600; }"
                "QPushButton:hover { background-color: #5e666d; }"
                "QPushButton:disabled { background-color: #aab7c4; border-color: #9aa8b6; color: #eef2f6; }"
            ),
        }
        btn.setStyleSheet(styles.get(kind, styles["secondary"]))
        return btn

    def load_data(self):
        try:
            rows = self.db_manager.get_supplier_fill_payment_summary(
                start_date=self.from_date.date().toPython(),
                end_date=self.to_date.date().toPython(),
            )
            search_text = (self.search_input.text() or "").strip().lower()
            if search_text:
                rows = [row for row in rows if search_text in (row.get('supplier_name') or '').lower()]
            total_fill = sum(float(row.get('fill_total') or 0) for row in rows)
            total_paid = sum(float(row.get('total_paid') or 0) for row in rows)
            total_remaining = sum(float(row.get('remaining_amount') or 0) for row in rows)
            self.summary_label.setText(
                f"Suppliers: {len(rows)}   |   Total Fill Cost: {as_money(total_fill)}   |   Paid: {as_money(total_paid)}   |   Remaining: {as_money(total_remaining)}"
            )
            with table_batch_update(self.table):
                self.table.setRowCount(len(rows))
                for idx, row in enumerate(rows):
                    self.table.setItem(idx, 0, QTableWidgetItem(row.get('supplier_name') or ''))
                    self.table.setItem(idx, 1, QTableWidgetItem(str(int(row.get('total_cylinders') or 0))))
                    self.table.setItem(idx, 2, QTableWidgetItem(as_money(row.get('other_gas_total'))))
                    self.table.setItem(idx, 3, QTableWidgetItem(as_money(row.get('lpg_refill_total'))))
                    self.table.setItem(idx, 4, QTableWidgetItem(as_money(row.get('fill_total'))))
                    self.table.setItem(idx, 5, QTableWidgetItem(as_money(row.get('total_paid'))))
                    remaining_item = QTableWidgetItem(as_money(row.get('remaining_amount')))
                    if float(row.get('remaining_amount') or 0) > 0:
                        remaining_item.setForeground(Qt.red)
                    else:
                        remaining_item.setForeground(Qt.darkGreen)
                    self.table.setItem(idx, 6, remaining_item)

                    actions = QWidget()
                    actions_layout = QHBoxLayout(actions)
                    actions_layout.setContentsMargins(0, 0, 0, 0)
                    actions_layout.setSpacing(4)
                    actions_layout.setAlignment(Qt.AlignCenter)
                    view_btn = self._action_button("View", "secondary")
                    view_btn.setFixedWidth(52)
                    view_btn.clicked.connect(lambda _checked=False, data=row: self.view_supplier(data))
                    actions_layout.addWidget(view_btn)
                    pay_btn = self._action_button("Pay", "success")
                    pay_btn.setFixedWidth(46)
                    pay_btn.setEnabled(float(row.get('remaining_amount') or 0) > 0)
                    pay_btn.clicked.connect(lambda _checked=False, data=row: self.pay_supplier(data))
                    actions_layout.addWidget(pay_btn)
                    self.table.setCellWidget(idx, 7, actions)
        except Exception as exc:
            QMessageBox.critical(self, "Load Error", f"Failed to load supplier balances: {exc}")

    def view_supplier(self, row: dict):
        dlg = SupplierAccountDetailDialog(self.db_manager, row, self)
        dlg.exec()

    def pay_supplier(self, row: dict):
        dlg = SupplierPaymentDialog(self.db_manager, row, self.current_user, self)
        if not dlg.exec():
            return
        self.load_data()
        refresh_application_views("supplier_payments", "reports", "suppliers", "daily_transactions")
        QMessageBox.information(self, "Success", "Supplier payment recorded.")
