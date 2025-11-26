from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QDateEdit, QMessageBox, QFileDialog, QInputDialog
)
from PySide6.QtCore import Qt, QDate, QUrl
from PySide6.QtGui import QDesktopServices
from database_module import DatabaseManager
from datetime import datetime, timedelta
import csv
import tempfile
import os
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
except Exception:
    A4 = None


class WeeklyBillingWidget(QWidget):
    def __init__(self, db_manager: DatabaseManager, current_user: dict):
        super().__init__()
        self.db_manager = db_manager
        self.current_user = current_user
        self.week_start = None
        self.week_end = None
        self.init_ui()
        self.set_default_week()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Weekly Billing")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title)

        controls = QHBoxLayout()
        controls.setSpacing(10)

        self.start_edit = QDateEdit()
        self.start_edit.setDisplayFormat("yyyy-MM-dd")
        self.start_edit.setCalendarPopup(True)
        self.end_edit = QDateEdit()
        self.end_edit.setDisplayFormat("yyyy-MM-dd")
        self.end_edit.setCalendarPopup(True)

        prev_btn = QPushButton("Prev Week")
        next_btn = QPushButton("Next Week")
        refresh_btn = QPushButton("Refresh")
        export_pdf_btn = QPushButton("Export PDF")
        export_csv_btn = QPushButton("Export Excel")
        export_all_btn = QPushButton("Export All Receipts")
        print_all_btn = QPushButton("Print All Receipts")

        prev_btn.clicked.connect(self.prev_week)
        next_btn.clicked.connect(self.next_week)
        refresh_btn.clicked.connect(self.load_data)
        export_pdf_btn.clicked.connect(self.export_pdf)
        export_csv_btn.clicked.connect(self.export_csv)
        export_all_btn.clicked.connect(self.export_all_receipts)
        print_all_btn.clicked.connect(self.print_all_receipts)

        controls.addWidget(QLabel("Week Start"))
        controls.addWidget(self.start_edit)
        controls.addWidget(QLabel("Week End"))
        controls.addWidget(self.end_edit)
        controls.addWidget(prev_btn)
        controls.addWidget(next_btn)
        controls.addWidget(refresh_btn)
        controls.addStretch()
        controls.addWidget(export_pdf_btn)
        controls.addWidget(export_csv_btn)
        controls.addWidget(export_all_btn)
        controls.addWidget(print_all_btn)
        layout.addLayout(controls)

        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "Client", "Cylinders", "Subtotal", "Tax", "Total", "Prev Balance",
            "Payable", "Paid", "Status", "Action"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

    def set_default_week(self):
        ws, we = self.db_manager.get_week_bounds()
        self.week_start = ws
        self.week_end = we
        self.start_edit.setDate(QDate.fromString(ws, "yyyy-MM-dd"))
        self.end_edit.setDate(QDate.fromString(we, "yyyy-MM-dd"))

    def ensure_week_fields(self):
        ws = self.start_edit.date().toString("yyyy-MM-dd")
        we = self.end_edit.date().toString("yyyy-MM-dd")
        self.week_start, self.week_end = ws, we

    def prev_week(self):
        self.ensure_week_fields()
        start = datetime.strptime(self.week_start, "%Y-%m-%d") - timedelta(days=7)
        ws = start.strftime('%Y-%m-%d')
        we = (start + timedelta(days=6)).strftime('%Y-%m-%d')
        self.start_edit.setDate(QDate.fromString(ws, "yyyy-MM-dd"))
        self.end_edit.setDate(QDate.fromString(we, "yyyy-MM-dd"))
        self.load_data()

    def next_week(self):
        self.ensure_week_fields()
        start = datetime.strptime(self.week_start, "%Y-%m-%d") + timedelta(days=7)
        ws = start.strftime('%Y-%m-%d')
        we = (start + timedelta(days=6)).strftime('%Y-%m-%d')
        self.start_edit.setDate(QDate.fromString(ws, "yyyy-MM-dd"))
        self.end_edit.setDate(QDate.fromString(we, "yyyy-MM-dd"))
        self.load_data()

    def load_data(self):
        self.ensure_week_fields()
        report = self.db_manager.get_weekly_billing_report(self.week_start, self.week_end)
        self.table.setRowCount(len(report))
        for i, r in enumerate(report):
            self.table.setItem(i, 0, QTableWidgetItem(r['client_name']))
            self.table.setItem(i, 1, QTableWidgetItem(str(r['total_qty'])))
            self.table.setItem(i, 2, QTableWidgetItem(f"Rs. {r['subtotal']:,.2f}"))
            self.table.setItem(i, 3, QTableWidgetItem(f"Rs. {r['tax_amount']:,.2f}"))
            self.table.setItem(i, 4, QTableWidgetItem(f"Rs. {r['total_amount']:,.2f}"))
            self.table.setItem(i, 5, QTableWidgetItem(f"Rs. {r['previous_balance']:,.2f}"))
            self.table.setItem(i, 6, QTableWidgetItem(f"Rs. {r['payable_amount']:,.2f}"))
            self.table.setItem(i, 7, QTableWidgetItem(f"Rs. {r['amount_paid']:,.2f}"))
            status_item = QTableWidgetItem(r['status'])
            if r['status'] == 'PAID':
                status_item.setForeground(Qt.darkGreen)
            else:
                status_item.setForeground(Qt.red)
            self.table.setItem(i, 8, status_item)
            act_widget = QWidget()
            h = QHBoxLayout(act_widget)
            h.setContentsMargins(0, 0, 0, 0)
            h.setSpacing(6)
            pay_btn = QPushButton("Record Payment")
            is_allowed = self.current_user['role'] in ['Admin', 'Accountant']
            pay_btn.setEnabled(is_allowed and r['status'] != 'PAID' and r['payable_amount'] > 0)
            pay_btn.clicked.connect(lambda checked, row=i, rec=r: self.record_payment(row, rec))
            print_btn = QPushButton("Print Weekly Receipt")
            print_btn.clicked.connect(lambda checked, rec=r: self.print_receipt(rec))
            dl_btn = QPushButton("Download Weekly Receipt")
            dl_btn.clicked.connect(lambda checked, rec=r: self.download_receipt(rec))
            paid_btn = QPushButton("Mark Paid")
            paid_btn.setEnabled(is_allowed and r['status'] != 'PAID' and r['payable_amount'] > 0)
            paid_btn.clicked.connect(lambda checked, row=i, rec=r: self.mark_paid(row, rec))
            h.addWidget(pay_btn)
            h.addWidget(paid_btn)
            h.addWidget(print_btn)
            h.addWidget(dl_btn)
            self.table.setCellWidget(i, 9, act_widget)

    def is_payment_day(self) -> bool:
        wd = datetime.now().weekday()  # Mon=0
        return wd in (3, 4)

    def record_payment(self, row_index: int, rec: dict):
        if not self.is_payment_day():
            QMessageBox.warning(self, "Payment Restricted", "Payments are allowed only on Thursday or Friday.")
            return
        default_amount = max(0.0, float(rec['payable_amount']) - float(rec['amount_paid']))
        amount, ok = QInputDialog.getDouble(self, "Record Weekly Payment", f"Enter payment amount for {rec['client_name']}", default_amount, 0.0, 1e9, 2)
        if not ok:
            return
        if amount > default_amount + 1e-6:
            QMessageBox.warning(self, "Invalid Amount", "Payment cannot exceed remaining payable.")
            return
        try:
            self.db_manager.record_weekly_payment(rec['client_id'], self.week_start, self.week_end, amount, getattr(self.current_user, 'id', None) or self.current_user.get('id'))
            self.set_success_action_state(row_index)
            QMessageBox.information(self, "Success", "Payment recorded and balances updated.")
            self.load_data()
            self.trigger_global_refresh()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Weekly Billing (Excel)", f"weekly_billing_{self.week_start}_to_{self.week_end}.csv", "CSV Files (*.csv)")
        if not path:
            return
        report = self.db_manager.get_weekly_billing_report(self.week_start, self.week_end)
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Client", "Cylinders", "Subtotal", "Tax", "Total", "Prev Balance", "Payable", "Paid", "Status"])
            for r in report:
                writer.writerow([
                    r['client_name'], r['total_qty'], f"{r['subtotal']:.2f}", f"{r['tax_amount']:.2f}", f"{r['total_amount']:.2f}",
                    f"{r['previous_balance']:.2f}", f"{r['payable_amount']:.2f}", f"{r['amount_paid']:.2f}", r['status']
                ])

    def export_pdf(self):
        if A4 is None:
            QMessageBox.warning(self, "Missing Dependency", "ReportLab is not available for PDF export.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save Weekly Billing (PDF)", f"weekly_billing_{self.week_start}_to_{self.week_end}.pdf", "PDF Files (*.pdf)")
        if not path:
            return
        report = self.db_manager.get_weekly_billing_report(self.week_start, self.week_end)
        doc = SimpleDocTemplate(path, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        story.append(Paragraph(f"Weekly Billing Report ({self.week_start} to {self.week_end})", styles['Title']))
        story.append(Spacer(1, 6))
        data = [["Client", "Cylinders", "Subtotal", "Tax", "Total", "Prev Balance", "Payable", "Paid", "Status"]]
        for r in report:
            data.append([
                r['client_name'], str(r['total_qty']), f"{r['subtotal']:,.2f}", f"{r['tax_amount']:,.2f}", f"{r['total_amount']:,.2f}",
                f"{r['previous_balance']:,.2f}", f"{r['payable_amount']:,.2f}", f"{r['amount_paid']:,.2f}", r['status']
            ])
        tbl = Table(data, hAlign='LEFT')
        tbl.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.8, colors.black),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('ALIGN', (1,1), (-1,-1), 'RIGHT'),
        ]))
        story.append(tbl)
        doc.build(story)

    def refresh_data(self):
        self.load_data()

    def set_role_permissions(self):
        is_allowed = self.current_user['role'] in ['Admin', 'Accountant']
        for row in range(self.table.rowCount()):
            w = self.table.cellWidget(row, 9)
            if w:
                for idx in range(w.layout().count()):
                    btn = w.layout().itemAt(idx).widget()
                    if btn and isinstance(btn, QPushButton):
                        if btn.text() in ("Record Payment", "Mark Paid"):
                            btn.setEnabled(is_allowed)
                        else:
                            btn.setEnabled(True)

    def safe_filename(self, name: str) -> str:
        return "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in name)

    def generate_client_receipt_pdf(self, rec: dict, path: str):
        if A4 is None:
            raise Exception("ReportLab is not available")
        doc = SimpleDocTemplate(path, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        story.append(Paragraph(f"Weekly Billing Receipt ({self.week_start} to {self.week_end})", styles['Title']))
        story.append(Spacer(1, 6))
        story.append(Paragraph(f"Client: {rec['client_name']}", styles['Heading3']))
        if rec.get('phone'):
            story.append(Paragraph(f"Phone: {rec['phone']}", styles['Normal']))
        if rec.get('company'):
            story.append(Paragraph(f"Company: {rec['company']}", styles['Normal']))
        story.append(Spacer(1, 6))
        data = [["Metric", "Value"],
                ["Cylinders", str(int(rec['total_qty']))],
                ["Subtotal", f"{float(rec['subtotal']):,.2f}"],
                ["Tax", f"{float(rec['tax_amount']):,.2f}"],
                ["Total", f"{float(rec['total_amount']):,.2f}"],
                ["Previous Balance", f"{float(rec['previous_balance']):,.2f}"],
                ["Payable", f"{float(rec['payable_amount']):,.2f}"],
                ["Paid", f"{float(rec['amount_paid']):,.2f}"],
                ["Status", rec.get('status') or 'UNPAID']]
        tbl = Table(data, hAlign='LEFT')
        tbl.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.8, colors.black),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('ALIGN', (1,1), (-1,-1), 'RIGHT'),
        ]))
        story.append(tbl)
        doc.build(story)

    def print_receipt(self, rec: dict):
        if A4 is None:
            QMessageBox.warning(self, "Missing Dependency", "ReportLab is not available for PDF export.")
            return
        fn = f"weekly_receipt_{self.safe_filename(rec['client_name'])}_{self.week_start}_to_{self.week_end}.pdf"
        path = os.path.join(tempfile.gettempdir(), fn)
        try:
            self.generate_client_receipt_pdf(rec, path)
            try:
                os.startfile(path, "print")
            except Exception:
                QDesktopServices.openUrl(QUrl.fromLocalFile(path))
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def download_receipt(self, rec: dict):
        if A4 is None:
            QMessageBox.warning(self, "Missing Dependency", "ReportLab is not available for PDF export.")
            return
        suggested = f"weekly_receipt_{self.safe_filename(rec['client_name'])}_{self.week_start}_to_{self.week_end}.pdf"
        path, _ = QFileDialog.getSaveFileName(self, "Save Weekly Receipt", suggested, "PDF Files (*.pdf)")
        if not path:
            return
        try:
            self.generate_client_receipt_pdf(rec, path)
            QMessageBox.information(self, "Saved", "Weekly receipt saved.")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def export_all_receipts(self):
        if A4 is None:
            QMessageBox.warning(self, "Missing Dependency", "ReportLab is not available for PDF export.")
            return
        folder = QFileDialog.getExistingDirectory(self, "Select Folder to Save Receipts")
        if not folder:
            return
        report = self.db_manager.get_weekly_billing_report(self.week_start, self.week_end)
        count = 0
        errors = []
        for r in report:
            fn = f"weekly_receipt_{self.safe_filename(r['client_name'])}_{self.week_start}_to_{self.week_end}.pdf"
            path = os.path.join(folder, fn)
            try:
                self.generate_client_receipt_pdf(r, path)
                count += 1
            except Exception as e:
                errors.append(f"{r['client_name']}: {str(e)}")
        if errors:
            QMessageBox.warning(self, "Completed with Errors", "\n".join(errors))
        QMessageBox.information(self, "Done", f"Exported {count} receipts.")

    def print_all_receipts(self):
        if A4 is None:
            QMessageBox.warning(self, "Missing Dependency", "ReportLab is not available for PDF export.")
            return
        report = self.db_manager.get_weekly_billing_report(self.week_start, self.week_end)
        count = 0
        errors = []
        for r in report:
            fn = f"weekly_receipt_{self.safe_filename(r['client_name'])}_{self.week_start}_to_{self.week_end}.pdf"
            path = os.path.join(tempfile.gettempdir(), fn)
            try:
                self.generate_client_receipt_pdf(r, path)
                try:
                    os.startfile(path, "print")
                except Exception as pe:
                    errors.append(f"{r['client_name']}: {str(pe)}")
                count += 1
            except Exception as e:
                errors.append(f"{r['client_name']}: {str(e)}")
        if errors:
            QMessageBox.warning(self, "Completed with Errors", "\n".join(errors))
        QMessageBox.information(self, "Done", f"Printed {count} receipts.")

    def mark_paid(self, row_index: int, rec: dict):
        if not self.is_payment_day():
            QMessageBox.warning(self, "Payment Restricted", "Payments are allowed only on Thursday or Friday.")
            return
        remaining = max(0.0, float(rec['payable_amount']) - float(rec['amount_paid']))
        if remaining <= 0:
            QMessageBox.information(self, "Already Paid", "No remaining amount to mark as paid.")
            return
        try:
            self.db_manager.record_weekly_payment(rec['client_id'], self.week_start, self.week_end, remaining, getattr(self.current_user, 'id', None) or self.current_user.get('id'))
            self.set_success_action_state(row_index)
            QMessageBox.information(self, "Success", "Marked as paid and balances updated.")
            self.load_data()
            self.trigger_global_refresh()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def set_success_action_state(self, row_index: int):
        w = self.table.cellWidget(row_index, 9)
        if not w:
            return
        for idx in range(w.layout().count()):
            btn = w.layout().itemAt(idx).widget()
            if not btn or not isinstance(btn, QPushButton):
                continue
            if btn.text() in ("Record Payment", "Mark Paid"):
                btn.setText("Success")
                btn.setStyleSheet("QPushButton { background-color: #27ae60; color: white; }")
                btn.setEnabled(False)

    def trigger_global_refresh(self):
        try:
            mw = self.window()
            # Refresh key pages that display balances and recent sales
            for name in ["clients", "sales", "receipts", "reports", "dashboard"]:
                if hasattr(mw, 'refresh_current_page'):
                    mw.refresh_current_page(name)
            if hasattr(mw, 'status_bar'):
                mw.status_bar.showMessage("Weekly payment applied. All pages refreshed.")
        except Exception:
            pass
