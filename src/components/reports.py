from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QDateEdit, QComboBox, QGroupBox, QTextEdit,
                               QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
                               QFileDialog)
from PySide6.QtCore import Qt, QDate
from database_module import DatabaseManager
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
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title_label = QLabel("Reports")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title_label)
        
        # Report type selection
        report_group = QGroupBox("Report Configuration")
        report_layout = QHBoxLayout()
        report_layout.setSpacing(15)
        
        # Report type
        report_layout.addWidget(QLabel("Report Type:"))
        self.report_type_combo = QComboBox()
        self.report_type_combo.addItems([
            "Sales Report",
            "Outstanding Balances",
            "Gate Activity Report",
            "Employee Report",
            "Gas Type Summary",
            "Client Summary"
        ])
        self.report_type_combo.currentTextChanged.connect(self.on_report_type_changed)
        report_layout.addWidget(self.report_type_combo)
        
        # Date range
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
        
        # Generate button
        self.generate_btn = QPushButton("Generate Report")
        self.generate_btn.clicked.connect(self.generate_report)
        report_layout.addWidget(self.generate_btn)
        
        report_layout.addStretch()
        report_group.setLayout(report_layout)
        layout.addWidget(report_group)
        
        # Report content
        content_group = QGroupBox("Report Content")
        content_layout = QVBoxLayout()
        content_layout.setSpacing(10)
        
        # Report summary
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setMaximumHeight(150)
        self.summary_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                font-family: 'Courier New';
                font-size: 12px;
            }
        """)
        content_layout.addWidget(self.summary_text)
        
        # Report table
        self.report_table = QTableWidget()
        self.report_table.setAlternatingRowColors(True)
        self.report_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.report_table.setEditTriggers(QTableWidget.NoEditTriggers)
        content_layout.addWidget(self.report_table)
        
        content_group.setLayout(content_layout)
        layout.addWidget(content_group)
        
        # Export controls
        export_layout = QHBoxLayout()
        export_layout.setSpacing(10)
        
        self.export_csv_btn = QPushButton("Export as CSV")
        self.export_csv_btn.clicked.connect(self.export_csv)
        export_layout.addWidget(self.export_csv_btn)
        
        self.export_json_btn = QPushButton("Export as JSON")
        self.export_json_btn.clicked.connect(self.export_json)
        export_layout.addWidget(self.export_json_btn)
        
        self.print_btn = QPushButton("Print Report")
        self.print_btn.clicked.connect(self.print_report)
        export_layout.addWidget(self.print_btn)
        
        export_layout.addStretch()
        layout.addLayout(export_layout)
        
        # Set role-based permissions
        self.set_role_permissions()
        
        # Generate initial report
        self.generate_report()
    
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
        if report_type in ["Outstanding Balances", "Client Summary", "Employee Report"]:
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
            elif report_type == "Outstanding Balances":
                self.generate_outstanding_balances_report()
            elif report_type == "Gate Activity Report":
                self.generate_gate_activity_report()
            elif report_type == "Employee Report":
                self.generate_employee_report()
            elif report_type == "Gas Type Summary":
                self.generate_gas_type_summary()
            elif report_type == "Client Summary":
                self.generate_client_summary()
            
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
        self.report_table.setColumnCount(8)
        self.report_table.setHorizontalHeaderLabels([
            "Date", "Client", "Products", "Quantities", "Unit Price", "Subtotal", "Tax", "Total"
        ])
        
        self.report_table.setRowCount(len(sales))
        
        for row, sale in enumerate(sales):
            self.report_table.setItem(row, 0, QTableWidgetItem(sale['created_at'][:16]))
            self.report_table.setItem(row, 1, QTableWidgetItem(sale['client_name']))
            
            self.report_table.setItem(row, 2, QTableWidgetItem(sale.get('product_summary') or ''))
            self.report_table.setItem(row, 3, QTableWidgetItem(sale.get('quantities_summary') or str(sale.get('quantity') or '')))
            self.report_table.setItem(row, 4, QTableWidgetItem(f"Rs. {sale['unit_price']:,.2f}"))
            self.report_table.setItem(row, 5, QTableWidgetItem(f"Rs. {sale['subtotal']:,.2f}"))
            self.report_table.setItem(row, 6, QTableWidgetItem(f"Rs. {sale['tax_amount']:,.2f}"))
            self.report_table.setItem(row, 7, QTableWidgetItem(f"Rs. {sale['total_amount']:,.2f}"))
        
        self.report_table.resizeColumnsToContents()
    
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
        
        self.report_table.resizeColumnsToContents()
    
    def generate_gate_activity_report(self):
        """Generate gate activity report"""
        from_date = self.from_date_edit.date().toPython()
        to_date = self.to_date_edit.date().toPython()
        
        # Get gate activity data
        gate_passes = self.db_manager.get_gate_activity_report(from_date, to_date)
        
        # Calculate summary
        total_out = len([gp for gp in gate_passes if gp['time_out']])
        total_in = len([gp for gp in gate_passes if gp['time_in']])
        
        # Generate summary
        summary = f"""
GATE ACTIVITY REPORT
Period: {from_date} to {to_date}
Total Gate Passes Created: {len(gate_passes)}
Total Cylinders Out: {total_out}
Total Cylinders In: {total_in}
Pending Return: {total_out - total_in}
        """
        self.summary_text.setPlainText(summary.strip())
        
        # Populate table
        self.report_table.setColumnCount(7)
        self.report_table.setHorizontalHeaderLabels([
            "Gate Pass #", "Receipt #", "Client", "Driver", "Vehicle", "Time Out", "Time In"
        ])
        
        self.report_table.setRowCount(len(gate_passes))
        
        for row, gate_pass in enumerate(gate_passes):
            self.report_table.setItem(row, 0, QTableWidgetItem(gate_pass['gate_pass_number']))
            self.report_table.setItem(row, 1, QTableWidgetItem(gate_pass['receipt_number']))
            self.report_table.setItem(row, 2, QTableWidgetItem(gate_pass['client_name']))
            self.report_table.setItem(row, 3, QTableWidgetItem(gate_pass['driver_name']))
            self.report_table.setItem(row, 4, QTableWidgetItem(gate_pass['vehicle_number']))
            
            time_out = gate_pass['time_out'][:16] if gate_pass['time_out'] else ""
            self.report_table.setItem(row, 5, QTableWidgetItem(time_out))
            
            time_in = gate_pass['time_in'][:16] if gate_pass['time_in'] else "Not returned"
            time_in_item = QTableWidgetItem(time_in)
            if not gate_pass['time_in']:
                time_in_item.setForeground(Qt.red)
            self.report_table.setItem(row, 6, time_in_item)
        
        self.report_table.resizeColumnsToContents()
    
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
        
        self.report_table.resizeColumnsToContents()
    
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
        
        self.report_table.resizeColumnsToContents()
    
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
        
        self.report_table.resizeColumnsToContents()
    
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
