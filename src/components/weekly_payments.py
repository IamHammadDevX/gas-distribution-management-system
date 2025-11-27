from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QDateEdit, QComboBox, QPushButton, QTableWidget, QTableWidgetItem, QGroupBox, QMessageBox, QDialog, QTextEdit
from PySide6.QtCore import Qt, QDate
from PySide6.QtPrintSupport import QPrinter, QPrintDialog
from PySide6.QtGui import QTextDocument, QFont, QPageSize, QPageLayout
from database_module import DatabaseManager

class WeeklyClientReceiptDialog(QDialog):
    def __init__(self, invoice_row: dict, parent=None):
        super().__init__(parent)
        self.invoice = invoice_row
        self.setWindowTitle(f"Weekly Receipt - {invoice_row.get('receipt_number') or invoice_row.get('invoice_number')}")
        self.setFixedSize(600, 540)
        layout = QVBoxLayout(self)
        preview = QTextEdit()
        preview.setReadOnly(True)
        preview.setMinimumHeight(500)
        preview.setHtml(self.generate_html())
        layout.addWidget(preview)
        bar = QHBoxLayout()
        print_btn = QPushButton("Print")
        print_btn.clicked.connect(self.print_receipt)
        bar.addWidget(print_btn)
        export_btn = QPushButton("Export PDF")
        export_btn.clicked.connect(self.export_pdf)
        bar.addWidget(export_btn)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        bar.addWidget(close_btn)
        layout.addLayout(bar)

    def resolve_logo_path(self) -> str:
        import os, sys
        base_mei = getattr(sys, '_MEIPASS', None)
        exe_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(sys.argv[0])
        if base_mei:
            p = os.path.join(base_mei, 'logo.png')
            if os.path.exists(p):
                return p.replace('\\', '/')
        p = os.path.join(exe_dir, 'logo.png')
        if os.path.exists(p):
            return p.replace('\\', '/')
        fallback = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'logo.png'))
        if os.path.exists(fallback):
            return fallback.replace('\\', '/')
        return 'logo.png'

    def generate_html(self) -> str:
        style = """
body { font-family: Arial, sans-serif; color:#000; margin:0; }
.page { max-width: 700px; margin: 0 auto; padding: 20px 28px; border: 2px solid #000; border-radius: 12px; }
.header { text-align:center; border-bottom:2px solid #333; padding-bottom:8px; margin-bottom:10px; }
.title { font-size: 20px; font-weight: 800; margin: 8px 0; text-decoration: underline; }
.meta { font-size: 13px; margin-top:4px; }
.label { font-weight: 700; }
.tbl { width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 6px; }
.tbl th, .tbl td { border: 1px solid #000; padding: 6px 8px; text-align: center; }
.bill { width: 100%; border-collapse: collapse; margin-top: 10px; }
.bill td { border: 1.5px solid #000; padding: 6px 10px; font-weight: 700; text-align: center; }
.footer { text-align:center; font-size: 13px; margin-top: 12px; border-top: 2px solid #444; padding-top: 8px; }
.signature { text-align:right; font-size: 15px; font-style: italic; margin-top: 14px; }
        """
        ws = self.invoice['week_start']
        we = self.invoice['week_end']
        status = self.invoice['status']
        ref = self.invoice.get('receipt_number') or self.invoice.get('invoice_number')
        company = self.invoice.get('client_company') or ''
        phone = self.invoice.get('client_phone') or ''
        return f"""
<html><head><style>{style}</style></head><body>
<div class='page'>
  <div class='header'>
    <div style='display:flex; align-items:center; justify-content:center; gap:12px;'>
      <img src='" + self.resolve_logo_path() + "' alt='Logo' width='32' height='32' style='border:1.5px solid #444; border-radius:50%;' />
      <div>
        <div style='font-size:22px; font-weight:900;'>RAJPUT GAS TRADERS</div>
        <div class='meta' style='font-size:12px;'>Prop: Saleem Ahmad | 0301-6465144</div>
      </div>
    </div>
    <div class='meta' style='font-size:12px;'>Plot No.69C-70C, Small Industrial Estate No.2, Gujranwala</div>
    <div class='meta' style='font-size:12px;'><span class='label'>Week:</span> {ws} to {we} &nbsp;&nbsp; <span class='label'>Ref:</span> {ref} &nbsp;&nbsp; <span class='label'>Status:</span> {status}</div>
  </div>
  <div class='title'>WEEKLY BILL</div>
  <div style='text-align:center; font-size:15px;'><b>CUSTOMER :</b> {self.invoice['client_name']}</div>
  <div style='text-align:center; font-size:13px;'>Company: {company} &nbsp; Phone: {phone}</div>
  <table class='tbl'>
    <tr><th>Total Cylinders</th><th>Subtotal</th><th>Discount</th><th>Tax 16%</th><th>Total</th></tr>
    <tr>
      <td>{int(self.invoice['total_cylinders'])}</td>
      <td>{float(self.invoice['subtotal']):,.2f}</td>
      <td>{float(self.invoice['discount']):,.2f}</td>
      <td>{float(self.invoice['tax_amount']):,.2f}</td>
      <td>{float(self.invoice['total_payable']):,.2f}</td>
    </tr>
  </table>
  <table class='bill'>
    <tr><td>Previous Balance</td><td>{float(self.invoice['previous_balance']):,.2f}</td></tr>
    <tr><td>Final Payable</td><td>{float(self.invoice['final_payable']):,.2f}</td></tr>
    <tr><td>Paid Amount</td><td>{float(self.invoice['amount_paid']):,.2f}</td></tr>
    <tr><td>Remaining Balance</td><td>{max(0.0, float(self.invoice['final_payable']) - float(self.invoice['amount_paid'])):,.2f}</td></tr>
  </table>
  <div class='signature'>Signature________________</div>
  <div class='footer'>This is an auto-generated weekly receipt.</div>
  <div class='footer'>Plot No.69C-70C, Small Industrial Estate No.2, Gujranwala</div>
</div>
</body></html>
        """

    def print_receipt(self):
        printer = QPrinter(QPrinter.HighResolution)
        printer.setPageSize(QPageSize(QPageSize.A4))
        printer.setPageOrientation(QPageLayout.Portrait)
        dialog = QPrintDialog(printer, self)
        if dialog.exec():
            doc = QTextDocument()
            doc.setDefaultFont(QFont("Arial", 11))
            doc.setHtml(self.generate_html())
            doc.setPageSize(printer.pageRect(QPrinter.Point).size())
            doc.print_(printer)

    def export_pdf(self):
        from PySide6.QtWidgets import QFileDialog
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setPageSize(QPageSize(QPageSize.A4))
        printer.setPageOrientation(QPageLayout.Portrait)
        filename, _ = QFileDialog.getSaveFileName(self, "Export Weekly Receipt", f"Weekly_{self.invoice.get('receipt_number') or self.invoice.get('invoice_number')}.pdf", "PDF Files (*.pdf)")
        if filename:
            printer.setOutputFileName(filename)
            doc = QTextDocument()
            doc.setDefaultFont(QFont("Arial", 11))
            doc.setHtml(self.generate_html())
            doc.setPageSize(printer.pageRect(QPrinter.Point).size())
            doc.print_(printer)

class WeeklyPaymentsWidget(QWidget):
    def __init__(self, db_manager: DatabaseManager, current_user: dict):
        super().__init__()
        self.db_manager = db_manager
        self.current_user = current_user
        self.init_ui()
        self.load_weekly_invoices()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        title = QLabel("Weekly Payments")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title)
        bar = QHBoxLayout()
        bar.setSpacing(10)
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.dateChanged.connect(self.load_weekly_invoices)
        bar.addWidget(QLabel("Pick any day in week:"))
        bar.addWidget(self.date_edit)
        self.end_day_combo = QComboBox()
        self.end_day_combo.addItems(["Friday", "Thursday"])
        self.end_day_combo.currentTextChanged.connect(self.load_weekly_invoices)
        bar.addWidget(QLabel("Week end:"))
        bar.addWidget(self.end_day_combo)
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_weekly_invoices)
        bar.addWidget(refresh_btn)
        print_btn = QPushButton("Print Weekly List")
        print_btn.clicked.connect(self.print_weekly_list)
        bar.addWidget(print_btn)
        layout.addLayout(bar)
        group = QGroupBox("Weekly Billing Details")
        g_layout = QVBoxLayout(group)
        self.table = QTableWidget()
        self.table.setColumnCount(12)
        self.table.setHorizontalHeaderLabels([
            "Client", "Cylinders", "Subtotal", "Discount", "Tax (16%)", "Total Payable", "Prev Balance", "Final Payable", "Paid", "Status", "Actions", "Week"
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setColumnWidth(10, 360)
        g_layout.addWidget(self.table)
        layout.addWidget(group)

    def get_week_range(self):
        d = self.date_edit.date().toPython()
        weekday = d.weekday()
        sat_offset = (weekday - 5) % 7
        from datetime import timedelta
        week_start = d if weekday == 5 else (d - timedelta(days=sat_offset))
        end_choice = self.end_day_combo.currentText()
        if end_choice == "Friday":
            week_end = week_start + timedelta(days=6)
        else:
            week_end = week_start + timedelta(days=5)
        return week_start.strftime('%Y-%m-%d'), week_end.strftime('%Y-%m-%d')

    def load_weekly_invoices(self):
        ws, we = self.get_week_range()
        clients = self.db_manager.get_clients()
        for c in clients:
            try:
                self.db_manager.upsert_weekly_invoice(c['id'], ws, we, self.current_user.get('id'))
            except Exception:
                continue
        rows = self.db_manager.get_weekly_invoices(ws, we)
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            client_text = r['client_name']
            if r.get('client_company'):
                client_text += f" ({r['client_company']})"
            self.table.setItem(i, 0, QTableWidgetItem(client_text))
            self.table.setItem(i, 1, QTableWidgetItem(str(int(r['total_cylinders']))))
            self.table.setItem(i, 2, QTableWidgetItem(f"Rs. {float(r['subtotal']):,.2f}"))
            self.table.setItem(i, 3, QTableWidgetItem(f"Rs. {float(r['discount']):,.2f}"))
            self.table.setItem(i, 4, QTableWidgetItem(f"Rs. {float(r['tax_amount']):,.2f}"))
            self.table.setItem(i, 5, QTableWidgetItem(f"Rs. {float(r['total_payable']):,.2f}"))
            self.table.setItem(i, 6, QTableWidgetItem(f"Rs. {float(r['previous_balance']):,.2f}"))
            self.table.setItem(i, 7, QTableWidgetItem(f"Rs. {float(r['final_payable']):,.2f}"))
            self.table.setItem(i, 8, QTableWidgetItem(f"Rs. {float(r['amount_paid']):,.2f}"))
            status_item = QTableWidgetItem(r['status'])
            if r['status'] == 'PAID':
                status_item.setForeground(Qt.darkGreen)
            else:
                status_item.setForeground(Qt.red)
            self.table.setItem(i, 9, status_item)
            actions = QWidget()
            h = QHBoxLayout(actions)
            h.setContentsMargins(5, 5, 5, 5)
            h.setSpacing(6)
            btn_print = QPushButton("Print Client Details")
            btn_print.setStyleSheet(
                """
                QPushButton { background-color: #f39c12; color: white; border: 1px solid #d68910; border-radius: 6px; padding: 8px 16px; font-size: 14px; font-weight: 700; }
                QPushButton:hover { background-color: #d68910; }
                QPushButton:pressed { background-color: #b9770e; }
                """
            )
            btn_print.setMinimumWidth(160)
            btn_print.setFixedHeight(40)
            btn_print.clicked.connect(lambda checked=False, row=r: self.print_client(row))
            h.addWidget(btn_print)
            btn_pay = QPushButton("Record Payment")
            btn_pay.setStyleSheet(
                """
                QPushButton { background-color: #28a745; color: white; border: 1px solid #1e7e34; border-radius: 6px; padding: 8px 16px; font-size: 14px; font-weight: 700; }
                QPushButton:hover { background-color: #218838; }
                QPushButton:pressed { background-color: #1e7e34; }
                """
            )
            btn_pay.setMinimumWidth(160)
            btn_pay.setFixedHeight(40)
            btn_pay.clicked.connect(lambda checked=False, row=r: self.record_payment(row))
            h.addWidget(btn_pay)
            btn_mark = QPushButton("Mark as PAID")
            btn_mark.setStyleSheet(
                """
                QPushButton { background-color: #3498db; color: white; border: 1px solid #2c81ba; border-radius: 6px; padding: 8px 16px; font-size: 14px; font-weight: 700; }
                QPushButton:hover { background-color: #2c81ba; }
                QPushButton:pressed { background-color: #256fa0; }
                QPushButton:disabled { background-color: #95a5a6; color: #ecf0f1; border-color: #7f8c8d; }
                """
            )
            btn_mark.setMinimumWidth(160)
            btn_mark.setFixedHeight(40)
            btn_mark.setEnabled(max(0.0, float(r['final_payable']) - float(r['amount_paid'])) == 0.0 and r['status'] != 'PAID')
            btn_mark.clicked.connect(lambda checked=False, row=r: self.mark_paid(row))
            h.addWidget(btn_mark)
            actions.setLayout(h)
            self.table.setCellWidget(i, 10, actions)
            self.table.setItem(i, 11, QTableWidgetItem(f"{r['week_start']} to {r['week_end']}"))

    def print_client(self, invoice_row: dict):
        dlg = WeeklyClientReceiptDialog(invoice_row, self)
        dlg.exec()

    def record_payment(self, invoice_row: dict):
        from PySide6.QtWidgets import QInputDialog
        remaining = max(0.0, float(invoice_row['final_payable']) - float(invoice_row['amount_paid']))
        if remaining <= 0:
            QMessageBox.information(self, "Info", "No remaining balance.")
            return
        amount, ok = QInputDialog.getDouble(self, "Record Payment", f"Enter payment amount for {invoice_row['client_name']}", 0.0, 0.0, float(remaining), 2)
        if not ok:
            return
        try:
            day = QDate.currentDate().toString('yyyy-MM-dd')
            self.db_manager.record_weekly_payment(invoice_row['id'], float(amount), day, self.current_user.get('id'))
            QMessageBox.information(self, "Success", "Payment recorded.")
            self.load_weekly_invoices()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def mark_paid(self, invoice_row: dict):
        try:
            self.db_manager.mark_weekly_invoice_paid(invoice_row['id'])
            QMessageBox.information(self, "Success", "Weekly invoice marked as PAID.")
            self.load_weekly_invoices()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def print_weekly_list(self):
        printer = QPrinter(QPrinter.HighResolution)
        printer.setPageSize(QPageSize(QPageSize.A4))
        printer.setPageOrientation(QPageLayout.Portrait)
        dialog = QPrintDialog(printer, self)
        if dialog.exec():
            ws, we = self.get_week_range()
            html = [
                f"<h2 style='text-align:center; font-size:16pt;'>Weekly Billing List - {ws} to {we}</h2>",
                "<table border='1' cellspacing='0' cellpadding='6' style='width:100%; font-size:10pt; border-collapse:collapse;'>",
                "<tr><th>Client</th><th>Cylinders</th><th>Subtotal</th><th>Discount</th><th>Tax</th><th>Total</th><th>Prev</th><th>Final</th><th>Paid</th><th>Status</th></tr>"
            ]
            for i in range(self.table.rowCount()):
                client = self.table.item(i, 0).text() if self.table.item(i, 0) else ""
                cyl = self.table.item(i, 1).text() if self.table.item(i, 1) else ""
                sub = self.table.item(i, 2).text() if self.table.item(i, 2) else ""
                disc = self.table.item(i, 3).text() if self.table.item(i, 3) else ""
                tax = self.table.item(i, 4).text() if self.table.item(i, 4) else ""
                tot = self.table.item(i, 5).text() if self.table.item(i, 5) else ""
                prev = self.table.item(i, 6).text() if self.table.item(i, 6) else ""
                final = self.table.item(i, 7).text() if self.table.item(i, 7) else ""
                paid = self.table.item(i, 8).text() if self.table.item(i, 8) else ""
                status = self.table.item(i, 9).text() if self.table.item(i, 9) else ""
                html.append(f"<tr><td>{client}</td><td>{cyl}</td><td>{sub}</td><td>{disc}</td><td>{tax}</td><td>{tot}</td><td>{prev}</td><td>{final}</td><td>{paid}</td><td>{status}</td></tr>")
            html.append("</table>")
            doc = QTextDocument()
            doc.setDefaultFont(QFont("Arial", 10))
            doc.setHtml("".join(html))
            doc.setPageSize(printer.pageRect(QPrinter.Point).size())
            doc.print_(printer)
