from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QDateEdit, QComboBox, QGroupBox, QTextEdit,
                               QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
                               QFileDialog)
from PySide6.QtCore import Qt, QDate
from src.database_module import DatabaseManager
from datetime import datetime, timedelta
import csv
import json

class ReportsWidget(QWidget):
    def __init__(self, db_manager: DatabaseManager, current_user: dict):
        super().__init__()
        self.db_manager = db_manager
        self.current_user = current_user
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        self.setStyleSheet("""
            QLabel { color: #1e293b; }
            QGroupBox {
                border: 1px solid #dbe4f0;
                border-radius: 10px;
                margin-top: 8px;
                background: #ffffff;
                font-weight: 700;
                color: #1e3a8a;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QComboBox, QDateEdit {
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 5px 8px;
                min-height: 30px;
                background: #ffffff;
            }
            QComboBox:focus, QDateEdit:focus { border: 1px solid #2563eb; }
            QTextEdit {
                border: 1px solid #dbe4f0;
                border-radius: 8px;
                background-color: #f8fbff;
                font-family: Consolas;
                font-size: 12px;
            }
            QTableWidget {
                border: 1px solid #dbe4f0;
                border-radius: 8px;
                background: #ffffff;
                gridline-color: #e5e7eb;
            }
            QTableWidget::item:selected { background-color: #e6f0ff; color: #0f172a; }
            QHeaderView::section {
                background-color: #2563eb;
                color: white;
                border: none;
                padding: 8px;
                font-weight: 700;
            }
        """)

        title_label = QLabel("Reports")
        title_label.setStyleSheet("font-size: 22px; font-weight: 700; color: #1e3a8a;")
        layout.addWidget(title_label)

        report_group = QGroupBox("Report Configuration")
        report_layout = QHBoxLayout()
        report_layout.setSpacing(10)

        report_layout.addWidget(QLabel("Report Type:"))
        self.report_type_combo = QComboBox()
        self.report_type_combo.addItems([
            "Sales Report",
            "Supplier Sales Summary",
            "Supplier Fill Payment Summary",
            "Outstanding Balances",
            "Employee Report",
            "Gas Type Summary",
            "Client Summary",
            "Pending Cylinder Summary by Client",
            "LPG Refill Report",
            "LPG Khata Summary"
        ])
        self.report_type_combo.currentTextChanged.connect(self.on_report_type_changed)
        report_layout.addWidget(self.report_type_combo)

        report_layout.addWidget(QLabel("From:"))
        self.from_date_edit = QDateEdit()
        self.from_date_edit.setDate(QDate.currentDate().addDays(-30))
        self.from_date_edit.setCalendarPopup(True)
        report_layout.addWidget(self.from_date_edit)

        report_layout.addWidget(QLabel("To:"))
        self.to_date_edit = QDateEdit()
        self.to_date_edit.setDate(QDate.currentDate())
        self.to_date_edit.setCalendarPopup(True)
        report_layout.addWidget(self.to_date_edit)

        self.generate_btn = QPushButton("Generate Report")
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #1d4ed8;
                color: white;
                border: 1px solid #1e40af;
                border-radius: 6px;
                padding: 6px 12px;
                min-height: 30px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #1e40af; }
        """)
        self.generate_btn.clicked.connect(self.generate_report)
        report_layout.addWidget(self.generate_btn)

        report_layout.addStretch()
        report_group.setLayout(report_layout)
        layout.addWidget(report_group)

        content_group = QGroupBox("Report Content")
        content_layout = QVBoxLayout()
        content_layout.setSpacing(10)

        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setMaximumHeight(160)
        content_layout.addWidget(self.summary_text)

        self.report_table = QTableWidget()
        self.report_table.setAlternatingRowColors(True)
        self.report_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.report_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.report_table.verticalHeader().setVisible(False)
        self.report_table.verticalHeader().setDefaultSectionSize(34)
        self.report_table.setFocusPolicy(Qt.NoFocus)
        content_layout.addWidget(self.report_table)

        content_group.setLayout(content_layout)
        layout.addWidget(content_group)

        export_layout = QHBoxLayout()
        export_layout.setSpacing(8)

        self.export_csv_btn = QPushButton("Export as CSV")
        self.export_csv_btn.setStyleSheet("""
            QPushButton {
                background-color: #0ea5e9;
                color: white;
                border: 1px solid #0284c7;
                border-radius: 6px;
                padding: 5px 10px;
                min-height: 28px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #0284c7; }
        """)
        self.export_csv_btn.clicked.connect(self.export_csv)
        export_layout.addWidget(self.export_csv_btn)

        self.export_json_btn = QPushButton("Export as JSON")
        self.export_json_btn.setStyleSheet("""
            QPushButton {
                background-color: #14b8a6;
                color: white;
                border: 1px solid #0f766e;
                border-radius: 6px;
                padding: 5px 10px;
                min-height: 28px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #0f766e; }
        """)
        self.export_json_btn.clicked.connect(self.export_json)
        export_layout.addWidget(self.export_json_btn)

        self.print_btn = QPushButton("Print Report")
        self.print_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                border: 1px solid #1d4ed8;
                border-radius: 6px;
                padding: 5px 10px;
                min-height: 28px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #1d4ed8; }
        """)
        self.print_btn.clicked.connect(self.print_report)
        export_layout.addWidget(self.print_btn)

        export_layout.addStretch()
        layout.addLayout(export_layout)

        self.set_role_permissions()

        self.generate_report()

    def _apply_table_resize(self, action_col=None):
        header = self.report_table.horizontalHeader()
        for index in range(self.report_table.columnCount()):
            if action_col is not None and index == action_col:
                header.setSectionResizeMode(index, QHeaderView.ResizeToContents)
            elif index == 0:
                header.setSectionResizeMode(index, QHeaderView.ResizeToContents)
            else:
                header.setSectionResizeMode(index, QHeaderView.Stretch)
    
    def set_role_permissions(self):
        """Set permissions based on user role"""
        role = self.current_user['role']
        
        if role == 'Driver':
            self.generate_btn.setEnabled(False)
            self.export_csv_btn.setEnabled(False)
            self.export_json_btn.setEnabled(False)
            self.print_btn.setEnabled(False)
    
    def on_report_type_changed(self, report_type):
        """Handle report type change"""
        # Enable/disable date range based on report type
        if report_type in ["Outstanding Balances", "Client Summary", "Employee Report", "LPG Khata Summary"]:
            self.from_date_edit.setEnabled(False)
            self.to_date_edit.setEnabled(False)
        else:
            self.from_date_edit.setEnabled(True)
            self.to_date_edit.setEnabled(True)
    
    def generate_report(self):
        """Generate selected report"""
        report_type = self.report_type_combo.currentText()
        
        try:
            if report_type == "Sales Report":
                self.generate_sales_report()
            elif report_type == "Supplier Sales Summary":
                self.generate_supplier_sales_summary()
            elif report_type == "Supplier Fill Payment Summary":
                self.generate_supplier_fill_payment_summary()
            elif report_type == "Outstanding Balances":
                self.generate_outstanding_balances_report()
            elif report_type == "Employee Report":
                self.generate_employee_report()
            elif report_type == "Gas Type Summary":
                self.generate_gas_type_summary()
            elif report_type == "Client Summary":
                self.generate_client_summary()
            elif report_type == "Pending Cylinder Summary by Client":
                self.generate_pending_cylinder_summary_report()
            elif report_type == "LPG Refill Report":
                self.generate_lpg_refill_report()
            elif report_type == "LPG Khata Summary":
                self.generate_lpg_khata_summary()
            
        except Exception as e:
            QMessageBox.critical(self, "Report Error", f"Failed to generate report: {str(e)}")
    
    def generate_sales_report(self):
        """Generate sales report"""
        from_date = self.from_date_edit.date().toPython()
        to_date = self.to_date_edit.date().toPython()
        
        # Get sales data
        sales = self.db_manager.get_sales_report(from_date, to_date)
        
        # Calculate summary
        total_sales = sum(sale['total_amount'] for sale in sales)
        total_tax = sum(sale['tax_amount'] for sale in sales)
        total_quantity = sum(sale['quantity'] for sale in sales)
        
        # Generate summary
        summary = f"""
SALES REPORT
Period: {from_date} to {to_date}
Total Sales: Rs. {total_sales:,.2f}
Total Tax: Rs. {total_tax:,.2f}
Total Quantity: {total_quantity} cylinders
Number of Transactions: {len(sales)}
        """
        self.summary_text.setPlainText(summary.strip())
        
        # Populate table
        self.report_table.setColumnCount(9)
        self.report_table.setHorizontalHeaderLabels([
            "Date", "Client", "Products", "Sources", "Quantities", "Unit Price", "Subtotal", "Tax", "Total"
        ])
        
        self.report_table.setRowCount(len(sales))
        
        for row, sale in enumerate(sales):
            self.report_table.setItem(row, 0, QTableWidgetItem(sale['created_at'][:16]))
            self.report_table.setItem(row, 1, QTableWidgetItem(sale['client_name']))
            
            self.report_table.setItem(row, 2, QTableWidgetItem(sale.get('product_summary') or ''))
            self.report_table.setItem(row, 3, QTableWidgetItem(sale.get('source_summary') or 'Company Stock'))
            self.report_table.setItem(row, 4, QTableWidgetItem(sale.get('quantities_summary') or str(sale.get('quantity') or '')))
            self.report_table.setItem(row, 5, QTableWidgetItem(f"Rs. {sale['unit_price']:,.2f}"))
            self.report_table.setItem(row, 6, QTableWidgetItem(f"Rs. {sale['subtotal']:,.2f}"))
            self.report_table.setItem(row, 7, QTableWidgetItem(f"Rs. {sale['tax_amount']:,.2f}"))
            self.report_table.setItem(row, 8, QTableWidgetItem(f"Rs. {sale['total_amount']:,.2f}"))
        
        self._apply_table_resize()

    def generate_supplier_sales_summary(self):
        from_date = self.from_date_edit.date().toPython()
        to_date = self.to_date_edit.date().toPython()
        rows = self.db_manager.get_supplier_sales_summary(from_date, to_date)
        total_sales = sum(float(row['total_amount'] or 0) for row in rows)
        total_paid = sum(float(row['allocated_paid'] or 0) for row in rows)
        total_remaining = sum(float(row['remaining_amount'] or 0) for row in rows)
        summary = f"""
SUPPLIER SALES SUMMARY
Period: {from_date} to {to_date}
Suppliers / Sources: {len(rows)}
Total Sales: Rs. {total_sales:,.2f}
Allocated Paid: Rs. {total_paid:,.2f}
Remaining: Rs. {total_remaining:,.2f}
        """
        self.summary_text.setPlainText(summary.strip())
        self.report_table.setColumnCount(8)
        self.report_table.setHorizontalHeaderLabels([
            "Source", "Clients", "Transactions", "Quantity", "Subtotal", "Tax", "Total", "Remaining"
        ])
        self.report_table.setRowCount(len(rows))
        for row_idx, row in enumerate(rows):
            self.report_table.setItem(row_idx, 0, QTableWidgetItem(row['supplier_name']))
            self.report_table.setItem(row_idx, 1, QTableWidgetItem(str(int(row['client_count'] or 0))))
            self.report_table.setItem(row_idx, 2, QTableWidgetItem(str(int(row['transaction_count'] or 0))))
            self.report_table.setItem(row_idx, 3, QTableWidgetItem(str(int(row['total_quantity'] or 0))))
            self.report_table.setItem(row_idx, 4, QTableWidgetItem(f"Rs. {float(row['subtotal'] or 0):,.2f}"))
            self.report_table.setItem(row_idx, 5, QTableWidgetItem(f"Rs. {float(row['tax_amount'] or 0):,.2f}"))
            self.report_table.setItem(row_idx, 6, QTableWidgetItem(f"Rs. {float(row['total_amount'] or 0):,.2f}"))
            self.report_table.setItem(row_idx, 7, QTableWidgetItem(f"Rs. {float(row['remaining_amount'] or 0):,.2f}"))
        self._apply_table_resize()

    def generate_supplier_fill_payment_summary(self):
        from_date = self.from_date_edit.date().toPython()
        to_date = self.to_date_edit.date().toPython()
        rows = self.db_manager.get_supplier_fill_payment_summary(start_date=from_date, end_date=to_date)
        total_fill = sum(float(row.get('fill_total') or 0) for row in rows)
        total_paid = sum(float(row.get('total_paid') or 0) for row in rows)
        total_remaining = sum(float(row.get('remaining_amount') or 0) for row in rows)
        summary = f"""
SUPPLIER FILL PAYMENT SUMMARY
Period: {from_date} to {to_date}
Suppliers: {len(rows)}
Total Fill Cost: Rs. {total_fill:,.2f}
Total Paid: Rs. {total_paid:,.2f}
Remaining Supplier Balance: Rs. {total_remaining:,.2f}
        """
        self.summary_text.setPlainText(summary.strip())
        self.report_table.setColumnCount(8)
        self.report_table.setHorizontalHeaderLabels([
            "Supplier", "Cylinders", "Other Gas Fill", "LPG Fill", "Fill Cost", "Paid", "Remaining", "Last Payment"
        ])
        self.report_table.setRowCount(len(rows))
        for row_idx, row in enumerate(rows):
            self.report_table.setItem(row_idx, 0, QTableWidgetItem(row.get('supplier_name') or ''))
            self.report_table.setItem(row_idx, 1, QTableWidgetItem(str(int(row.get('total_cylinders') or 0))))
            self.report_table.setItem(row_idx, 2, QTableWidgetItem(f"Rs. {float(row.get('other_gas_total') or 0):,.2f}"))
            self.report_table.setItem(row_idx, 3, QTableWidgetItem(f"Rs. {float(row.get('lpg_refill_total') or 0):,.2f}"))
            self.report_table.setItem(row_idx, 4, QTableWidgetItem(f"Rs. {float(row.get('fill_total') or 0):,.2f}"))
            self.report_table.setItem(row_idx, 5, QTableWidgetItem(f"Rs. {float(row.get('total_paid') or 0):,.2f}"))
            remaining_item = QTableWidgetItem(f"Rs. {float(row.get('remaining_amount') or 0):,.2f}")
            if float(row.get('remaining_amount') or 0) > 0:
                remaining_item.setForeground(Qt.red)
            else:
                remaining_item.setForeground(Qt.darkGreen)
            self.report_table.setItem(row_idx, 6, remaining_item)
            self.report_table.setItem(row_idx, 7, QTableWidgetItem(str(row.get('last_payment_date') or '')))
        self._apply_table_resize()
    
    def generate_outstanding_balances_report(self):
        """Generate outstanding balances report"""
        # Get clients with outstanding balances
        clients = self.db_manager.get_outstanding_balances()
        
        # Calculate summary
        total_outstanding = sum(client['balance'] for client in clients)
        
        # Generate summary
        summary = f"""
OUTSTANDING BALANCES REPORT
Total Outstanding: Rs. {total_outstanding:,.2f}
Number of Clients with Outstanding Balance: {len(clients)}
        """
        self.summary_text.setPlainText(summary.strip())
        
        # Populate table
        self.report_table.setColumnCount(6)
        self.report_table.setHorizontalHeaderLabels([
            "Client ID", "Name", "Phone", "Company", "Total Purchases", "Outstanding Balance"
        ])
        
        self.report_table.setRowCount(len(clients))
        
        for row, client in enumerate(clients):
            self.report_table.setItem(row, 0, QTableWidgetItem(str(client['id'])))
            self.report_table.setItem(row, 1, QTableWidgetItem(client['name']))
            self.report_table.setItem(row, 2, QTableWidgetItem(client['phone']))
            self.report_table.setItem(row, 3, QTableWidgetItem(client['company'] or ''))
            self.report_table.setItem(row, 4, QTableWidgetItem(f"Rs. {client['total_purchases']:,.2f}"))
            
            balance_item = QTableWidgetItem(f"Rs. {client['balance']:,.2f}")
            balance_item.setForeground(Qt.red)
            self.report_table.setItem(row, 5, balance_item)
        
        self._apply_table_resize()
    
    def generate_employee_report(self):
        """Generate employee report"""
        # Get employees
        employees = self.db_manager.get_employees()
        
        # Calculate summary
        total_salary = sum(employee['salary'] for employee in employees)
        
        # Role distribution
        role_counts = {}
        for employee in employees:
            role = employee['role']
            role_counts[role] = role_counts.get(role, 0) + 1
        
        # Generate summary
        summary = f"""
EMPLOYEE REPORT
Total Employees: {len(employees)}
Total Monthly Salary: Rs. {total_salary:,.2f}

Role Distribution:
{chr(10).join(f"{role}: {count}" for role, count in role_counts.items())}
        """
        self.summary_text.setPlainText(summary.strip())
        
        # Populate table
        self.report_table.setColumnCount(5)
        self.report_table.setHorizontalHeaderLabels([
            "ID", "Name", "Role", "Salary", "Contact"
        ])
        
        self.report_table.setRowCount(len(employees))
        
        for row, employee in enumerate(employees):
            self.report_table.setItem(row, 0, QTableWidgetItem(str(employee['id'])))
            self.report_table.setItem(row, 1, QTableWidgetItem(employee['name']))
            self.report_table.setItem(row, 2, QTableWidgetItem(employee['role']))
            
            salary_item = QTableWidgetItem(f"Rs. {employee['salary']:,.2f}")
            salary_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.report_table.setItem(row, 3, salary_item)
            
            self.report_table.setItem(row, 4, QTableWidgetItem(employee['contact'] or ''))
        
        self._apply_table_resize()
    
    def generate_gas_type_summary(self):
        """Generate gas type summary report"""
        from_date = self.from_date_edit.date().toPython()
        to_date = self.to_date_edit.date().toPython()
        
        # Get sales data grouped by gas type
        query = '''
            SELECT gp.gas_type, gp.sub_type, gp.capacity,
                   COUNT(s.id) as transaction_count,
                   SUM(s.quantity) as total_quantity,
                   SUM(s.total_amount) as total_amount,
                   SUM(s.tax_amount) as total_tax
            FROM sales s
            JOIN gas_products gp ON s.gas_product_id = gp.id
            WHERE DATE(s.created_at) BETWEEN ? AND ?
            GROUP BY gp.gas_type, gp.sub_type, gp.capacity
            ORDER BY gp.gas_type, gp.sub_type, gp.capacity
        '''
        
        gas_summary = self.db_manager.execute_query(query, (from_date, to_date))
        
        # Calculate totals
        total_transactions = sum(item['transaction_count'] for item in gas_summary)
        total_quantity = sum(item['total_quantity'] for item in gas_summary)
        total_amount = sum(item['total_amount'] for item in gas_summary)
        
        # Generate summary
        summary = f"""
GAS TYPE SUMMARY REPORT
Period: {from_date} to {to_date}
Total Transactions: {total_transactions}
Total Quantity: {total_quantity} cylinders
Total Sales: Rs. {total_amount:,.2f}
        """
        self.summary_text.setPlainText(summary.strip())
        
        # Populate table
        self.report_table.setColumnCount(6)
        self.report_table.setHorizontalHeaderLabels([
            "Gas Type", "Sub Type", "Capacity", "Transactions", "Quantity", "Total Sales"
        ])
        
        self.report_table.setRowCount(len(gas_summary))
        
        for row, item in enumerate(gas_summary):
            self.report_table.setItem(row, 0, QTableWidgetItem(item['gas_type']))
            self.report_table.setItem(row, 1, QTableWidgetItem(item['sub_type'] or ''))
            self.report_table.setItem(row, 2, QTableWidgetItem(item['capacity']))
            self.report_table.setItem(row, 3, QTableWidgetItem(str(item['transaction_count'])))
            self.report_table.setItem(row, 4, QTableWidgetItem(str(item['total_quantity'])))
            
            amount_item = QTableWidgetItem(f"Rs. {item['total_amount']:,.2f}")
            amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.report_table.setItem(row, 5, amount_item)
        
        self._apply_table_resize()
    
    def generate_client_summary(self):
        """Generate client summary report"""
        # Get all clients
        clients = self.db_manager.get_clients()
        
        # Calculate summary
        total_clients = len(clients)
        total_purchases = sum(client['total_purchases'] for client in clients)
        total_outstanding = sum(client['balance'] for client in clients)
        clients_with_balance = len([c for c in clients if c['balance'] > 0])
        
        # Generate summary
        summary = f"""
CLIENT SUMMARY REPORT
Total Clients: {total_clients}
Total Purchases: Rs. {total_purchases:,.2f}
Total Outstanding: Rs. {total_outstanding:,.2f}
Clients with Outstanding Balance: {clients_with_balance}
        """
        self.summary_text.setPlainText(summary.strip())
        
        # Populate table
        self.report_table.setColumnCount(6)
        self.report_table.setHorizontalHeaderLabels([
            "Client ID", "Name", "Phone", "Company", "Total Purchases", "Outstanding Balance"
        ])
        
        # Sort by outstanding balance (descending)
        clients.sort(key=lambda x: x['balance'], reverse=True)
        
        self.report_table.setRowCount(len(clients))
        
        for row, client in enumerate(clients):
            self.report_table.setItem(row, 0, QTableWidgetItem(str(client['id'])))
            self.report_table.setItem(row, 1, QTableWidgetItem(client['name']))
            self.report_table.setItem(row, 2, QTableWidgetItem(client['phone']))
            self.report_table.setItem(row, 3, QTableWidgetItem(client['company'] or ''))
            self.report_table.setItem(row, 4, QTableWidgetItem(f"Rs. {client['total_purchases']:,.2f}"))
            
            balance_item = QTableWidgetItem(f"Rs. {client['balance']:,.2f}")
            if client['balance'] > 0:
                balance_item.setForeground(Qt.red)
            self.report_table.setItem(row, 5, balance_item)
        
        self._apply_table_resize()

    def generate_pending_cylinder_summary_report(self):
        """Generate pending cylinder summary by client"""
        rows = self.db_manager.get_pending_cylinder_summary_by_client()
        total_pending = sum(r['pending_cylinders'] for r in rows)
        with_pending = len([r for r in rows if r['pending_cylinders'] > 0])
        summary = f"""
PENDING CYLINDER SUMMARY BY CLIENT
Total Pending Cylinders: {total_pending}
Clients with Pending Cylinders: {with_pending}
        """
        self.summary_text.setPlainText(summary.strip())
        self.report_table.setColumnCount(4)
        self.report_table.setHorizontalHeaderLabels(["Client", "Phone", "Company", "Pending Cylinders"])
        self.report_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.report_table.setItem(i, 0, QTableWidgetItem(r['name']))
            self.report_table.setItem(i, 1, QTableWidgetItem(r['phone']))
            self.report_table.setItem(i, 2, QTableWidgetItem(r.get('company') or ''))
            item = QTableWidgetItem(str(int(r['pending_cylinders'])))
            if int(r['pending_cylinders']) > 0:
                item.setForeground(Qt.red)
            self.report_table.setItem(i, 3, item)
        self._apply_table_resize()

    def generate_lpg_refill_report(self):
        from_date = self.from_date_edit.date().toPython()
        to_date = self.to_date_edit.date().toPython()
        rows = self.db_manager.get_lpg_refill_report(from_date, to_date)
        total_qty = sum(int(row['total_quantity'] or 0) for row in rows)
        total_amount = sum(float(row['total_amount'] or 0) for row in rows)
        summary = f"""
LPG REFILL REPORT
Period: {from_date} to {to_date}
Entries: {len(rows)}
Total Refilled Cylinders: {total_qty}
Total Refill Amount: Rs. {total_amount:,.2f}
        """
        self.summary_text.setPlainText(summary.strip())
        self.report_table.setColumnCount(6)
        self.report_table.setHorizontalHeaderLabels([
            "Client", "Phone", "Supplier", "Capacity", "Quantity", "Amount"
        ])
        self.report_table.setRowCount(len(rows))
        for row_idx, row in enumerate(rows):
            self.report_table.setItem(row_idx, 0, QTableWidgetItem(row['client_name']))
            self.report_table.setItem(row_idx, 1, QTableWidgetItem(row['client_phone']))
            self.report_table.setItem(row_idx, 2, QTableWidgetItem(row['supplier_name']))
            self.report_table.setItem(row_idx, 3, QTableWidgetItem(row['capacity']))
            self.report_table.setItem(row_idx, 4, QTableWidgetItem(str(int(row['total_quantity'] or 0))))
            self.report_table.setItem(row_idx, 5, QTableWidgetItem(f"Rs. {float(row['total_amount'] or 0):,.2f}"))
        self._apply_table_resize()

    def generate_lpg_khata_summary(self):
        rows = self.db_manager.get_lpg_khata_summary()
        total_pending = sum(int(row['pending_client'] or 0) for row in rows)
        total_refilled = sum(int(row['refilled'] or 0) for row in rows)
        total_empty_balance = sum(int(row['empty_balance'] or 0) for row in rows)
        summary = f"""
LPG KHATA SUMMARY
Clients / Rows: {len(rows)}
Pending With Client: {total_pending}
Refilled: {total_refilled}
Empty Balance: {total_empty_balance}
        """
        self.summary_text.setPlainText(summary.strip())
        self.report_table.setColumnCount(8)
        self.report_table.setHorizontalHeaderLabels([
            "Client", "Phone", "Company", "Capacity", "Delivered", "Returned", "Refilled", "Empty Balance"
        ])
        self.report_table.setRowCount(len(rows))
        for row_idx, row in enumerate(rows):
            self.report_table.setItem(row_idx, 0, QTableWidgetItem(row['client_name']))
            self.report_table.setItem(row_idx, 1, QTableWidgetItem(row['phone']))
            self.report_table.setItem(row_idx, 2, QTableWidgetItem(row['company']))
            self.report_table.setItem(row_idx, 3, QTableWidgetItem(row['capacity']))
            self.report_table.setItem(row_idx, 4, QTableWidgetItem(str(int(row['delivered'] or 0))))
            self.report_table.setItem(row_idx, 5, QTableWidgetItem(str(int(row['returned'] or 0))))
            self.report_table.setItem(row_idx, 6, QTableWidgetItem(str(int(row['refilled'] or 0))))
            self.report_table.setItem(row_idx, 7, QTableWidgetItem(str(int(row['empty_balance'] or 0))))
        self._apply_table_resize()
    
    def export_csv(self):
        """Export report as CSV"""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Report as CSV",
            f"Report_{self.report_type_combo.currentText().replace(' ', '_')}_{QDate.currentDate().toString('yyyy-MM-dd')}.csv",
            "CSV Files (*.csv)"
        )
        
        if filename:
            try:
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    
                    # Write headers
                    headers = []
                    for col in range(self.report_table.columnCount()):
                        headers.append(self.report_table.horizontalHeaderItem(col).text())
                    writer.writerow(headers)
                    
                    # Write data
                    for row in range(self.report_table.rowCount()):
                        row_data = []
                        for col in range(self.report_table.columnCount()):
                            item = self.report_table.item(row, col)
                            row_data.append(item.text() if item else '')
                        writer.writerow(row_data)
                
                QMessageBox.information(self, "Success", f"Report exported to {filename}")
                
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export CSV: {str(e)}")
    
    def export_json(self):
        """Export report as JSON"""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Report as JSON",
            f"Report_{self.report_type_combo.currentText().replace(' ', '_')}_{QDate.currentDate().toString('yyyy-MM-dd')}.json",
            "JSON Files (*.json)"
        )
        
        if filename:
            try:
                # Build JSON data
                report_data = {
                    "report_type": self.report_type_combo.currentText(),
                    "generated_date": QDate.currentDate().toString("yyyy-MM-dd"),
                    "summary": self.summary_text.toPlainText(),
                    "data": []
                }
                
                # Add table data
                for row in range(self.report_table.rowCount()):
                    row_data = {}
                    for col in range(self.report_table.columnCount()):
                        header = self.report_table.horizontalHeaderItem(col).text()
                        item = self.report_table.item(row, col)
                        row_data[header] = item.text() if item else ''
                    report_data["data"].append(row_data)
                
                with open(filename, 'w', encoding='utf-8') as jsonfile:
                    json.dump(report_data, jsonfile, indent=2, ensure_ascii=False)
                
                QMessageBox.information(self, "Success", f"Report exported to {filename}")
                
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export JSON: {str(e)}")
    
    def print_report(self):
        """Print the report"""
        from PySide6.QtPrintSupport import QPrinter, QPrintDialog
        from PySide6.QtGui import QTextDocument
        
        printer = QPrinter(QPrinter.HighResolution)
        dialog = QPrintDialog(printer, self)
        
        if dialog.exec() == QPrintDialog.Accepted:
            # Create HTML content for printing
            html_content = self.generate_print_html()
            
            doc = QTextDocument()
            doc.setHtml(html_content)
            doc.print_(printer)
    
    def generate_print_html(self):
        """Generate HTML content for printing"""
        # Build table HTML
        table_html = "<table border='1' cellpadding='5' cellspacing='0' style='width: 100%; border-collapse: collapse;'>"
        
        # Headers
        table_html += "<tr>"
        for col in range(self.report_table.columnCount()):
            header = self.report_table.horizontalHeaderItem(col).text()
            table_html += f"<th style='background-color: #f2f2f2; font-weight: bold;'>{header}</th>"
        table_html += "</tr>"
        
        # Data rows
        for row in range(self.report_table.rowCount()):
            table_html += "<tr>"
            for col in range(self.report_table.columnCount()):
                item = self.report_table.item(row, col)
                text = item.text() if item else ''
                table_html += f"<td>{text}</td>"
            table_html += "</tr>"
        
        table_html += "</table>"
        
        return f"""
<html>
<head>
<style>
body {{ font-family: Arial, sans-serif; margin: 20px; }}
h1 {{ color: #2c3e50; }}
.summary {{ background-color: #f8f9fa; padding: 15px; border: 1px solid #dee2e6; margin-bottom: 20px; }}
</style>
</head>
<body>
<h1>{self.report_type_combo.currentText()}</h1>
<div class="summary">
<pre>{self.summary_text.toPlainText()}</pre>
</div>
{table_html}
<p style="margin-top: 20px; font-size: 12px; color: #666;">
Generated on: {QDate.currentDate().toString("yyyy-MM-dd")} by {self.current_user['full_name']}
</p>
</body>
</html>
        """
