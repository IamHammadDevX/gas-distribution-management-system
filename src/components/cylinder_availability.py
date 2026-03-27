from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QInputDialog, QFrame
)
from PySide6.QtCore import Qt
from src.database_module import DatabaseManager


class CylinderAvailabilityWidget(QWidget):
    def __init__(self, db_manager: DatabaseManager, current_user: dict):
        super().__init__()
        self.db_manager = db_manager
        self.current_user = current_user
        self.current_rows = []
        self.init_ui()
        self.load_data()

    def init_ui(self):
        self.setStyleSheet("""
            QWidget { background-color: #f7f9fc; color: #1f2937; }
            QLabel#titleLabel { font-size: 22px; font-weight: 700; color: #0f172a; }
            QLabel#hintLabel { font-size: 12px; color: #475569; }
            QLineEdit {
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 6px 8px;
                min-height: 30px;
                background: #ffffff;
            }
            QLineEdit:focus { border: 1px solid #2563eb; }
            QFrame#summaryCard, QFrame#equationCard {
                background: #ffffff;
                border: 1px solid #dbe4f0;
                border-radius: 10px;
            }
            QTableWidget {
                border: 1px solid #dbe4f0;
                border-radius: 8px;
                background: #ffffff;
                gridline-color: #e5e7eb;
            }
            QTableWidget::item { padding: 6px; }
            QTableWidget::item:selected { background-color: #e6f0ff; color: #0f172a; }
            QHeaderView::section {
                background-color: #2563eb;
                color: white;
                border: none;
                padding: 8px;
                font-weight: 700;
            }
            QPushButton { border-radius: 6px; padding: 5px 10px; min-height: 28px; font-weight: 600; }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        title = QLabel("Cylinder Availability")
        title.setObjectName("titleLabel")
        root.addWidget(title)

        hint = QLabel("Set Opening once, then system auto updates: Available = Opening + Returned - Sold")
        hint.setObjectName("hintLabel")
        root.addWidget(hint)

        controls = QHBoxLayout()
        controls.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by gas type, subtype, or capacity...")
        self.search_input.textChanged.connect(self.filter_rows)
        controls.addWidget(self.search_input)

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #0ea5e9;
                color: white;
                border: 1px solid #0284c7;
            }
            QPushButton:hover { background-color: #0284c7; }
        """)
        self.refresh_btn.clicked.connect(self.load_data)
        controls.addWidget(self.refresh_btn)

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #334155;
                border: 1px solid #cbd5e1;
            }
            QPushButton:hover { background-color: #f8fafc; }
        """)
        self.clear_btn.clicked.connect(self.clear_search)
        controls.addWidget(self.clear_btn)

        root.addLayout(controls)

        summary_card = QFrame()
        summary_card.setObjectName("summaryCard")
        summary_layout = QHBoxLayout(summary_card)
        summary_layout.setContentsMargins(12, 10, 12, 10)
        summary_layout.setSpacing(14)

        self.opening_label = QLabel("Opening: 0")
        self.returned_label = QLabel("Returned: 0")
        self.sold_label = QLabel("Sold: 0")
        self.available_label = QLabel("Available: 0")

        for lbl in [self.opening_label, self.returned_label, self.sold_label, self.available_label]:
            lbl.setStyleSheet("font-size: 13px; font-weight: 700;")
            summary_layout.addWidget(lbl)

        summary_layout.addStretch()
        root.addWidget(summary_card)

        equation_card = QFrame()
        equation_card.setObjectName("equationCard")
        equation_layout = QHBoxLayout(equation_card)
        equation_layout.setContentsMargins(12, 8, 12, 8)
        self.equation_label = QLabel("Formula: 0 + 0 - 0 = 0")
        self.equation_label.setStyleSheet("font-size: 13px; font-weight: 700; color: #1d4ed8;")
        equation_layout.addWidget(self.equation_label)
        equation_layout.addStretch()
        root.addWidget(equation_card)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Product", "Opening", "Returned", "Sold", "Available", "Updated", "Set Opening"
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(38)
        self.table.setFocusPolicy(Qt.NoFocus)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.Fixed)
        self.table.setColumnWidth(6, 112)

        root.addWidget(self.table, 1)

        self.set_role_permissions()

    def set_role_permissions(self):
        role = self.current_user.get('role')
        self.can_edit_opening = role in ['Admin', 'Accountant']

    def load_data(self):
        try:
            self.current_rows = self.db_manager.get_cylinder_availability_rows()
            self.populate_table(self.current_rows)
            self.update_totals()
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load cylinder availability: {str(e)}")

    def filter_rows(self):
        search = self.search_input.text().strip()
        try:
            rows = self.db_manager.get_cylinder_availability_rows(search)
            self.current_rows = rows
            self.populate_table(rows)
            self.update_totals()
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to filter cylinder availability: {str(e)}")

    def clear_search(self):
        self.search_input.clear()
        self.load_data()

    def update_totals(self):
        try:
            totals = self.db_manager.get_cylinder_availability_totals()
            opening = int(totals.get('opening_total') or 0)
            returned = int(totals.get('returned_total') or 0)
            sold = int(totals.get('sold_total') or 0)
            available = int(totals.get('available_total') or 0)
            self.opening_label.setText(f"Opening: {opening}")
            self.returned_label.setText(f"Returned: {returned}")
            self.sold_label.setText(f"Sold: {sold}")
            self.available_label.setText(f"Available: {available}")
            self.equation_label.setText(f"Formula: {opening} + {returned} - {sold} = {available}")
        except Exception:
            self.opening_label.setText("Opening: 0")
            self.returned_label.setText("Returned: 0")
            self.sold_label.setText("Sold: 0")
            self.available_label.setText("Available: 0")
            self.equation_label.setText("Formula: 0 + 0 - 0 = 0")

    def populate_table(self, rows):
        self.table.setRowCount(len(rows))
        for row, data in enumerate(rows):
            product_name = f"{data.get('gas_type') or ''}"
            if data.get('sub_type'):
                product_name += f" {data.get('sub_type')}"
            if data.get('capacity'):
                product_name += f" - {data.get('capacity')}"

            self.table.setItem(row, 0, QTableWidgetItem(product_name.strip()))
            self.table.setItem(row, 1, QTableWidgetItem(str(int(data.get('opening_count') or 0))))
            self.table.setItem(row, 2, QTableWidgetItem(str(int(data.get('returned_count') or 0))))
            self.table.setItem(row, 3, QTableWidgetItem(str(int(data.get('sold_count') or 0))))

            available = int(data.get('available_count') or 0)
            avail_item = QTableWidgetItem(str(available))
            if available < 0:
                avail_item.setForeground(Qt.red)
            elif available == 0:
                avail_item.setForeground(Qt.darkYellow)
            else:
                avail_item.setForeground(Qt.darkGreen)
            self.table.setItem(row, 4, avail_item)

            self.table.setItem(row, 5, QTableWidgetItem(str(data.get('updated_at') or '')))

            set_btn = QPushButton("Set Opening")
            set_btn.setEnabled(self.can_edit_opening)
            set_btn.setFocusPolicy(Qt.NoFocus)
            set_btn.setStyleSheet("""
                QPushButton {
                    background-color: #1d4ed8;
                    color: white;
                    border: 1px solid #1e40af;
                    border-radius: 5px;
                    padding: 3px 8px;
                    min-height: 24px;
                    max-height: 24px;
                    font-size: 11px;
                    font-weight: 600;
                }
                QPushButton:hover { background-color: #1e40af; }
                QPushButton:disabled { background-color: #a5b4fc; border-color: #a5b4fc; color: #eef2ff; }
            """)
            set_btn.clicked.connect(lambda _checked=False, d=data: self.set_opening_for_row(d))
            self.table.setCellWidget(row, 6, set_btn)

    def set_opening_for_row(self, row_data: dict):
        if not self.can_edit_opening:
            return

        product = f"{row_data.get('gas_type') or ''}"
        if row_data.get('sub_type'):
            product += f" {row_data.get('sub_type')}"
        product += f" - {row_data.get('capacity') or ''}"

        current_opening = int(row_data.get('opening_count') or 0)
        value, ok = QInputDialog.getInt(
            self,
            "Set Opening Cylinder Count",
            f"Enter opening cylinders for:\n{product}",
            current_opening,
            0,
            10_000_000,
            1,
        )
        if not ok:
            return

        try:
            self.db_manager.set_cylinder_opening_count(
                int(row_data['gas_product_id']),
                int(value),
                self.current_user.get('id')
            )
            QMessageBox.information(self, "Success", "Opening cylinder count updated.")
            self.load_data()
            try:
                from PySide6.QtWidgets import QApplication
                for widget in QApplication.topLevelWidgets():
                    if hasattr(widget, 'refresh_dashboard'):
                        widget.refresh_dashboard()
                        break
            except Exception:
                pass
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to set opening stock: {str(e)}")
