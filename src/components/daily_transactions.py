from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QDateEdit, QPushButton, QTableWidget, QTableWidgetItem, QGroupBox
from PySide6.QtCore import Qt, QDate
from PySide6.QtPrintSupport import QPrinter, QPrintDialog
from PySide6.QtGui import QTextDocument, QFont, QPageSize, QPageLayout
from database_module import DatabaseManager

class DailyTransactionsWidget(QWidget):
    def __init__(self, db_manager: DatabaseManager, current_user: dict):
        super().__init__()
        self.db_manager = db_manager
        self.current_user = current_user
        self.init_ui()
        self.load_transactions()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Daily Transactions")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title)

        bar = QHBoxLayout()
        bar.setSpacing(10)

        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.dateChanged.connect(self.load_transactions)
        bar.addWidget(self.date_edit)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_transactions)
        bar.addWidget(refresh_btn)

        print_btn = QPushButton("Print Day Summary")
        print_btn.clicked.connect(self.print_daily_report)
        bar.addWidget(print_btn)

        layout.addLayout(bar)

        sales_group = QGroupBox("Sales")
        sales_layout = QVBoxLayout(sales_group)
        self.sales_table = QTableWidget()
        self.sales_table.setColumnCount(8)
        self.sales_table.setHorizontalHeaderLabels(["Date", "Client", "Products", "Quantities", "Total", "Paid", "Balance", "Cashier"])
        self.sales_table.setAlternatingRowColors(True)
        self.sales_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.sales_table.setEditTriggers(QTableWidget.NoEditTriggers)
        sales_layout.addWidget(self.sales_table)
        layout.addWidget(sales_group)

        gate_group = QGroupBox("Gate Activity")
        gate_layout = QVBoxLayout(gate_group)
        self.gate_table = QTableWidget()
        self.gate_table.setColumnCount(8)
        self.gate_table.setHorizontalHeaderLabels(["Gate Pass #", "Client", "Driver", "Vehicle", "Gas", "Capacity", "Out", "In"])
        self.gate_table.setAlternatingRowColors(True)
        self.gate_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.gate_table.setEditTriggers(QTableWidget.NoEditTriggers)
        gate_layout.addWidget(self.gate_table)
        layout.addWidget(gate_group)

    def load_transactions(self):
        d_str = self.date_edit.date().toString('yyyy-MM-dd')
        self.load_sales_for_date(d_str)
        self.load_gate_for_date(d_str)

    def load_sales_for_date(self, day_str):
        rows = self.db_manager.get_sales_for_date_with_summaries(day_str)
        self.sales_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.sales_table.setItem(i, 0, QTableWidgetItem(r['created_at'][:16]))
            client = r['client_name']
            self.sales_table.setItem(i, 1, QTableWidgetItem(client))
            self.sales_table.setItem(i, 2, QTableWidgetItem(r.get('product_summary') or ''))
            self.sales_table.setItem(i, 3, QTableWidgetItem(r.get('quantities_summary') or str(r.get('quantity') or '')))
            total_item = QTableWidgetItem(f"Rs. {r['total_amount']:,.2f}")
            total_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.sales_table.setItem(i, 4, total_item)
            paid_item = QTableWidgetItem(f"Rs. {r['amount_paid']:,.2f}")
            paid_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.sales_table.setItem(i, 5, paid_item)
            bal_item = QTableWidgetItem(f"Rs. {r['balance']:,.2f}")
            bal_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if r['balance'] > 0:
                bal_item.setForeground(Qt.red)
            elif r['balance'] < 0:
                bal_item.setForeground(Qt.darkYellow)
            else:
                bal_item.setForeground(Qt.darkGreen)
            self.sales_table.setItem(i, 6, bal_item)
            self.sales_table.setItem(i, 7, QTableWidgetItem(r['cashier_name']))

    def load_gate_for_date(self, day_str):
        rows = self.db_manager.execute_query('''
            SELECT gp.*, c.name as client_name
            FROM gate_passes gp
            JOIN clients c ON gp.client_id = c.id
            WHERE DATE(gp.time_out, 'localtime') = ?
            ORDER BY gp.created_at DESC
        ''', (day_str,))
        self.gate_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.gate_table.setItem(i, 0, QTableWidgetItem(r['gate_pass_number']))
            self.gate_table.setItem(i, 1, QTableWidgetItem(r['client_name']))
            self.gate_table.setItem(i, 2, QTableWidgetItem(r['driver_name']))
            self.gate_table.setItem(i, 3, QTableWidgetItem(r['vehicle_number']))
            self.gate_table.setItem(i, 4, QTableWidgetItem(r['gas_type']))
            self.gate_table.setItem(i, 5, QTableWidgetItem(r['capacity']))
            out_item = QTableWidgetItem(r['time_out'][:16] if r['time_out'] else "")
            self.gate_table.setItem(i, 6, out_item)
            in_item = QTableWidgetItem(r['time_in'][:16] if r['time_in'] else "Not returned")
            if not r['time_in']:
                in_item.setForeground(Qt.red)
            else:
                in_item.setForeground(Qt.darkGreen)
            self.gate_table.setItem(i, 7, in_item)

    def print_daily_report(self):
        printer = QPrinter(QPrinter.HighResolution)
        printer.setPageSize(QPageSize(QPageSize.A4))
        printer.setPageOrientation(QPageLayout.Portrait)
        printer.setResolution(300)
        dialog = QPrintDialog(printer, self)
        if dialog.exec():
            d = self.date_edit.date().toString('yyyy-MM-dd')
            html = [
                f"<h2 style='text-align:center; font-size:16pt;'>Daily Transactions - {d}</h2>",
                "<h3 style='font-size:12pt;'>Sales</h3>",
                "<table border='1' cellspacing='0' cellpadding='6' style='width:100%; font-size:10pt; border-collapse:collapse;'>",
                "<tr><th>Date</th><th>Client</th><th>Products</th><th>Quantities</th><th>Total</th><th>Paid</th><th>Balance</th><th>Cashier</th></tr>"
            ]
            for i in range(self.sales_table.rowCount()):
                row = []
                for j in range(self.sales_table.columnCount()):
                    item = self.sales_table.item(i, j)
                    row.append(item.text() if item else "")
                html.append(f"<tr><td>{row[0]}</td><td>{row[1]}</td><td>{row[2]}</td><td>{row[3]}</td><td>{row[4]}</td><td>{row[5]}</td><td>{row[6]}</td><td>{row[7]}</td></tr>")
            html.extend(["</table>", "<h3 style='font-size:12pt;'>Gate Activity</h3>", "<table border='1' cellspacing='0' cellpadding='6' style='width:100%; font-size:10pt; border-collapse:collapse;'>",
                         "<tr><th>Gate Pass #</th><th>Client</th><th>Driver</th><th>Vehicle</th><th>Gas</th><th>Capacity</th><th>Out</th><th>In</th></tr>"])
            for i in range(self.gate_table.rowCount()):
                row = []
                for j in range(self.gate_table.columnCount()):
                    item = self.gate_table.item(i, j)
                    row.append(item.text() if item else "")
                html.append(f"<tr><td>{row[0]}</td><td>{row[1]}</td><td>{row[2]}</td><td>{row[3]}</td><td>{row[4]}</td><td>{row[5]}</td><td>{row[6]}</td><td>{row[7]}</td></tr>")
            html.append("</table>")
            cats = self.db_manager.get_empty_stock_by_category(d)
            html.extend(["<h3 style='font-size:12pt;'>Empty Stock Summary</h3>",
                         "<table border='1' cellspacing='0' cellpadding='6' style='width:60%; font-size:10pt; border-collapse:collapse;'>",
                         "<tr><th>Category</th><th>Quantity</th></tr>"])
            for c in cats:
                label = f"{c['gas_type']} - {c['capacity']}"
                html.append(f"<tr><td>{label}</td><td style='text-align:right;'>{c['quantity']}</td></tr>")
            html.append("</table>")
            doc = QTextDocument()
            doc.setDefaultFont(QFont("Arial", 10))
            doc.setHtml("".join(html))
            doc.setPageSize(printer.pageRect(QPrinter.Point).size())
            doc.print_(printer)
