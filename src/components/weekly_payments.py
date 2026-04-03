from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QDateEdit, QComboBox,
    QPushButton, QTableWidget, QTableWidgetItem, QGroupBox, QMessageBox,
    QDialog, QTextEdit, QLineEdit, QFormLayout, QDoubleSpinBox,
    QFrame, QHeaderView, QAbstractItemView
)
from PySide6.QtCore import Qt, QDate, QSizeF
from PySide6.QtPrintSupport import QPrinter, QPrintDialog
from PySide6.QtGui import QTextDocument, QFont, QPageSize, QPageLayout
from src.database_module import DatabaseManager
from src.components.ui_helpers import refresh_application_views

class WeeklyClientReceiptDialog(QDialog):
    def __init__(self, db_manager: DatabaseManager, invoice_row: dict, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.invoice = invoice_row
        self.setWindowTitle(f"Weekly Receipt - {invoice_row.get('receipt_number') or invoice_row.get('invoice_number')}")
        self.resize(760, 700)
        self.setMinimumSize(560, 560)

        self.setStyleSheet("""
            QDialog { background-color: #f5f6f8; }
            QTextEdit {
                background: #ffffff;
                border: 1px solid #d7dde3;
                border-radius: 8px;
                padding: 6px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        preview = QTextEdit()
        preview.setReadOnly(True)
        preview.setMinimumHeight(420)
        preview.setHtml(self.generate_html())
        layout.addWidget(preview)
        bar = QHBoxLayout()
        bar.addStretch(1)
        print_btn = QPushButton("Print")
        print_btn.setFixedHeight(28)
        print_btn.setFocusPolicy(Qt.NoFocus)
        print_btn.clicked.connect(self.print_receipt)
        bar.addWidget(print_btn)
        export_btn = QPushButton("Export PDF")
        export_btn.setFixedHeight(28)
        export_btn.setFocusPolicy(Qt.NoFocus)
        export_btn.clicked.connect(self.export_pdf)
        bar.addWidget(export_btn)
        close_btn = QPushButton("Close")
        close_btn.setFixedHeight(28)
        close_btn.setFocusPolicy(Qt.NoFocus)
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
        logo = self.resolve_logo_path()
        ws = self.invoice['week_start']
        we = self.invoice['week_end']
        status = self.invoice['status']
        ref = self.invoice.get('receipt_number') or self.invoice.get('invoice_number')
        company = self.invoice.get('client_company') or ''
        phone = self.invoice.get('client_phone') or ''
        cyl_breakdown = self.db_manager.get_weekly_sales_breakdown(self.invoice['client_id'], ws, we)
        empty_breakdown = self.db_manager.get_weekly_returns_breakdown(self.invoice['client_id'], ws, we)
        supplier_breakdown = self.db_manager.get_weekly_supplier_breakdown_text(self.invoice['client_id'], ws, we)
        lpg_refill_breakdown = self.db_manager.get_weekly_lpg_refill_breakdown(self.invoice['client_id'], ws, we)

        style = """
    body { font-family: Arial, sans-serif; color:#111827; margin:0; }
    .page { width: 176mm; margin: 0 auto; padding: 8mm 9mm; border: 1.2px solid #1f2937; border-radius: 8px; box-sizing: border-box; }
    .header { text-align:center; border-bottom: 1.8px solid #1f4f82; padding-bottom: 5px; margin-bottom: 7px; }
    .brand { display:flex; align-items:center; justify-content:center; gap:8px; }
    .logo { width: 26px; height: 26px; border:1px solid #334155; border-radius:50%; object-fit: cover; }
    .store { font-size: 16px; font-weight: 800; letter-spacing: .2px; color: #1f4f82; }
    .sub { font-size: 10px; color: #334155; margin-top: 1px; }
    .title { text-align:center; font-size: 13px; font-weight: 800; margin: 6px 0; color:#0f172a; }
    .meta-line { text-align:center; font-size: 10px; margin-bottom: 6px; color:#334155; }
    .label { font-weight: 700; }
    .table { width: 100%; border-collapse: collapse; font-size: 10px; margin-top: 5px; }
    .table th, .table td { border: 1px solid #334155; padding: 3px 4px; text-align: center; }
    .table th { background: #eaf0f8; }
    .summary { width: 100%; border-collapse: collapse; margin-top: 6px; font-size: 10px; }
    .summary td { border: 1px solid #334155; padding: 4px 5px; }
    .summary .k { font-weight: 700; background: #f8fafc; width: 45%; }
    .footer { text-align:center; font-size: 9px; margin-top: 7px; border-top: 1px dashed #64748b; padding-top: 5px; color:#475569; }
    .signature { text-align:right; font-size: 10px; margin-top: 8px; }
        """

        return f"""
<html><head><style>{style}</style></head><body>
<div class='page'>
  <div class='header'>
        <div class='brand'>
            <img src='{logo}' class='logo' alt='Logo'/>
            <div>
                <div class='store'>RAJPUT GAS TRADERS</div>
                <div class='sub'>Prop: Saleem Ahmad | 0301-6465144</div>
            </div>
    </div>
        <div class='sub'>Plot No.69C-70C, Small Industrial Estate No.2, Gujranwala</div>
  </div>
    <div class='title'>WEEKLY CLIENT STATEMENT</div>
    <div class='meta-line'><span class='label'>Week:</span> {ws} to {we} &nbsp;&nbsp; <span class='label'>Ref:</span> {ref} &nbsp;&nbsp; <span class='label'>Status:</span> {status}</div>
    <div style='text-align:center; font-size:11px; margin-bottom:3px;'><b>Customer:</b> {self.invoice['client_name']}</div>
    <div style='text-align:center; font-size:10px; color:#334155;'>Company: {company} &nbsp;|&nbsp; Phone: {phone}</div>

    <table class='summary'>
        <tr><td class='k'>Cylinders Delivered</td><td>{cyl_breakdown or '0'}</td></tr>
        <tr><td class='k'>Empty Return</td><td>{empty_breakdown or '0'}</td></tr>
        <tr><td class='k'>Source Breakdown</td><td>{supplier_breakdown or '0'}</td></tr>
        <tr><td class='k'>LPG Refill</td><td>{lpg_refill_breakdown or '0'}</td></tr>
    </table>

    <table class='table'>
    <tr><th>Total Cylinders</th><th>Subtotal</th><th>Discount</th><th>Tax 16%</th><th>Total</th></tr>
    <tr>
      <td>{int(self.invoice['total_cylinders'])}</td>
      <td>{float(self.invoice['subtotal']):,.2f}</td>
      <td>{float(self.invoice['discount']):,.2f}</td>
      <td>{float(self.invoice['tax_amount']):,.2f}</td>
      <td>{float(self.invoice['total_payable']):,.2f}</td>
    </tr>
  </table>
    <table class='summary'>
        <tr><td class='k'>Previous Balance</td><td>{float(self.invoice['previous_balance']):,.2f}</td></tr>
        <tr><td class='k'>Final Payable</td><td>{float(self.invoice['final_payable']):,.2f}</td></tr>
        <tr><td class='k'>Paid Amount</td><td>{float(self.invoice['amount_paid']):,.2f}</td></tr>
        <tr><td class='k'>Remaining Balance</td><td>{max(0.0, float(self.invoice['final_payable']) - float(self.invoice['amount_paid'])):,.2f}</td></tr>
  </table>

  <div class='signature'>Signature________________</div>
    <div class='footer'>This is an auto-generated one-page weekly statement.</div>
</div>
</body></html>
        """

    def print_receipt(self):
        printer = QPrinter(QPrinter.HighResolution)
        printer.setPageSize(QPageSize(QPageSize.A4))
        printer.setPageOrientation(QPageLayout.Portrait)
        printer.setFullPage(False)
        dialog = QPrintDialog(printer, self)
        if dialog.exec():
            if not printer.isValid():
                QMessageBox.critical(self, "Printer Error", "The selected printer is not valid.")
                return
            doc = QTextDocument()
            doc.setDefaultFont(QFont("Arial", 11))
            doc.setHtml(self.generate_html())
            rect = printer.pageRect(QPrinter.Point)
            if rect.isValid() and rect.width() > 0:
                doc.setPageSize(rect.size())
            else:
                doc.setPageSize(QSizeF(595, 842))
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
        self.refresh_filters()
        self.load_weekly_invoices()

    def init_ui(self):
        self.setStyleSheet("""
            QWidget { background-color: #f5f6f8; color: #1f2937; font-size: 13px; }
            QLabel#titleLabel { font-size: 24px; font-weight: 700; color: #1f4f82; }
            QFrame#sectionCard { background: #ffffff; border: 1px solid #dbe1e7; border-radius: 10px; }
            QLineEdit, QComboBox, QDateEdit {
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
                border-right: 1px solid #174066;
                border-bottom: 1px solid #174066;
                padding: 8px;
                font-weight: 600;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(12, 12, 12, 12)
        title = QLabel("Weekly Payments")
        title.setObjectName("titleLabel")
        layout.addWidget(title)

        controls_card = QFrame()
        controls_card.setObjectName("sectionCard")
        bar = QHBoxLayout(controls_card)
        bar.setSpacing(10)
        bar.setContentsMargins(10, 10, 10, 10)
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
        self.client_filter = QComboBox()
        self.client_filter.currentIndexChanged.connect(self.load_weekly_invoices)
        bar.addWidget(QLabel("Client:"))
        bar.addWidget(self.client_filter)
        self.supplier_filter = QComboBox()
        self.supplier_filter.currentIndexChanged.connect(self.load_weekly_invoices)
        bar.addWidget(QLabel("Source:"))
        bar.addWidget(self.supplier_filter)
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All", "PAID", "UNPAID"])
        self.status_filter.currentTextChanged.connect(self.load_weekly_invoices)
        bar.addWidget(QLabel("Status:"))
        bar.addWidget(self.status_filter)
        self.min_remaining = QLineEdit()
        self.min_remaining.setPlaceholderText("Min Remaining")
        self.min_remaining.textChanged.connect(self.load_weekly_invoices)
        self.max_remaining = QLineEdit()
        self.max_remaining.setPlaceholderText("Max Remaining")
        self.max_remaining.textChanged.connect(self.load_weekly_invoices)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search client/company/source/status/ref/week...")
        self.search_input.textChanged.connect(self.load_weekly_invoices)

        self.week_label = QLabel("Week: -")
        self.week_label.setStyleSheet("font-weight: 700; color: #1f4f82;")

        bar.addWidget(self.min_remaining)
        bar.addWidget(self.max_remaining)
        bar.addWidget(self.search_input)
        refresh_btn = self._small_button("Refresh", "primary")
        refresh_btn.clicked.connect(self.load_weekly_invoices)
        bar.addWidget(refresh_btn)
        print_btn = self._small_button("Print Weekly List", "dark")
        print_btn.clicked.connect(self.print_weekly_list)
        bar.addWidget(print_btn)
        bar.addWidget(self.week_label)

        layout.addWidget(controls_card)

        group = QFrame()
        group.setObjectName("sectionCard")
        g_layout = QVBoxLayout(group)
        g_layout.setContentsMargins(10, 10, 10, 10)
        g_layout.setSpacing(8)

        group_title = QLabel("Weekly Billing Details")
        group_title.setStyleSheet("font-size: 15px; font-weight: 700;")
        g_layout.addWidget(group_title)

        self.table = QTableWidget()
        self.table.setColumnCount(15)
        self.table.setHorizontalHeaderLabels([
            "Client", "Cylinders", "Empty Return", "Sources", "Subtotal", "Discount", "Tax (16%)", "Total Payable", "Prev Balance", "Final Payable", "Paid", "Remaining", "Status", "Actions", "Week"
        ])
        self._setup_table()
        g_layout.addWidget(self.table)
        layout.addWidget(group, 1)

    def _small_button(self, text: str, kind: str = "secondary") -> QPushButton:
        b = QPushButton(text)
        b.setFixedHeight(20)
        b.setFocusPolicy(Qt.NoFocus)
        styles = {
            "primary": (
                "QPushButton { background-color: #1a73e8; color: white; border: 1px solid #125bc4; border-radius: 4px; padding: 0 7px; font-size: 10px; font-weight: 600; min-height: 18px; max-height: 18px; }"
                "QPushButton:hover { background-color: #1765cb; }"
                "QPushButton:pressed { background-color: #125bc4; }"
            ),
            "success": (
                "QPushButton { background-color: #28a745; color: white; border: 1px solid #1e7e34; border-radius: 4px; padding: 0 7px; font-size: 10px; font-weight: 600; min-height: 18px; max-height: 18px; }"
                "QPushButton:hover { background-color: #218838; }"
                "QPushButton:pressed { background-color: #1e7e34; }"
            ),
            "warning": (
                "QPushButton { background-color: #f39c12; color: white; border: 1px solid #d68910; border-radius: 4px; padding: 0 7px; font-size: 10px; font-weight: 600; min-height: 18px; max-height: 18px; }"
                "QPushButton:hover { background-color: #d68910; }"
                "QPushButton:pressed { background-color: #b9770e; }"
            ),
            "dark": (
                "QPushButton { background-color: #2c3e50; color: white; border: 1px solid #1f2d3a; border-radius: 4px; padding: 0 7px; font-size: 10px; font-weight: 600; min-height: 18px; max-height: 18px; }"
                "QPushButton:hover { background-color: #1f2d3a; }"
                "QPushButton:pressed { background-color: #16222c; }"
            ),
            "secondary": (
                "QPushButton { background-color: #6c757d; color: white; border: 1px solid #596168; border-radius: 4px; padding: 0 7px; font-size: 10px; font-weight: 600; min-height: 18px; max-height: 18px; }"
                "QPushButton:hover { background-color: #5e666d; }"
                "QPushButton:pressed { background-color: #535a61; }"
            ),
        }
        b.setStyleSheet(styles.get(kind, styles["secondary"]))
        return b

    def _setup_table(self):
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setWordWrap(True)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(36)
        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        hh = self.table.horizontalHeader()
        hh.setStretchLastSection(False)
        hh.setMinimumSectionSize(70)
        for idx in range(15):
            hh.setSectionResizeMode(idx, QHeaderView.Fixed)

        self.table.setColumnWidth(0, 180)
        self.table.setColumnWidth(1, 170)
        self.table.setColumnWidth(2, 170)
        self.table.setColumnWidth(3, 220)
        self.table.setColumnWidth(4, 95)
        self.table.setColumnWidth(5, 95)
        self.table.setColumnWidth(6, 90)
        self.table.setColumnWidth(7, 110)
        self.table.setColumnWidth(8, 105)
        self.table.setColumnWidth(9, 110)
        self.table.setColumnWidth(10, 90)
        self.table.setColumnWidth(11, 105)
        self.table.setColumnWidth(12, 85)
        hh.setSectionResizeMode(13, QHeaderView.Fixed)
        self.table.setColumnWidth(13, 230)
        self.table.setColumnWidth(14, 170)

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

    def refresh_filters(self):
        current_client = self.client_filter.currentData() if self.client_filter.count() else None
        current_supplier = self.supplier_filter.currentData() if self.supplier_filter.count() else None

        self.client_filter.blockSignals(True)
        self.client_filter.clear()
        self.client_filter.addItem("All Clients", None)
        for client in self.db_manager.get_clients():
            self.client_filter.addItem(client['name'], client['id'])
        for idx in range(self.client_filter.count()):
            if self.client_filter.itemData(idx) == current_client:
                self.client_filter.setCurrentIndex(idx)
                break
        self.client_filter.blockSignals(False)

        self.supplier_filter.blockSignals(True)
        self.supplier_filter.clear()
        self.supplier_filter.addItem("All Sources", None)
        for supplier in self.db_manager.get_suppliers():
            self.supplier_filter.addItem(supplier['name'], supplier['id'])
        for idx in range(self.supplier_filter.count()):
            if self.supplier_filter.itemData(idx) == current_supplier:
                self.supplier_filter.setCurrentIndex(idx)
                break
        self.supplier_filter.blockSignals(False)

    def load_weekly_invoices(self):
        self.refresh_filters()
        ws, we = self.get_week_range()
        self.week_label.setText(f"Week: {ws} to {we}")
        clients = self.db_manager.get_clients()
        for c in clients:
            try:
                self.db_manager.upsert_weekly_invoice(c['id'], ws, we, self.current_user.get('id'))
            except Exception:
                continue
        rows = self.db_manager.get_weekly_invoices(ws, we)

        search_text = (self.search_input.text() or "").strip().lower()

        cid = self.client_filter.currentData()
        if cid:
            rows = [r for r in rows if r['client_id'] == cid]
        selected_supplier = self.supplier_filter.currentData()
        if selected_supplier:
            filtered_rows = []
            for row in rows:
                supplier_rows = self.db_manager.get_weekly_supplier_breakdown(row['client_id'], ws, we)
                if any(int(s.get('supplier_key') or 0) == int(selected_supplier) for s in supplier_rows):
                    filtered_rows.append(row)
            rows = filtered_rows
        st = self.status_filter.currentText()
        if st in ("PAID", "UNPAID"):
            rows = [r for r in rows if r['status'] == st]
        try:
            mn = float(self.min_remaining.text()) if self.min_remaining.text().strip() else None
        except Exception:
            mn = None
        try:
            mx = float(self.max_remaining.text()) if self.max_remaining.text().strip() else None
        except Exception:
            mx = None
        if mn is not None or mx is not None:
            frows = []
            for r in rows:
                rem = max(0.0, float(r['final_payable']) - float(r['amount_paid']))
                if mn is not None and rem < mn:
                    continue
                if mx is not None and rem > mx:
                    continue
                frows.append(r)
            rows = frows

        if search_text:
            filtered = []
            for r in rows:
                hay = " ".join([
                    str(r.get('client_name') or ''),
                    str(r.get('client_company') or ''),
                    str(r.get('status') or ''),
                    str(r.get('invoice_number') or ''),
                    str(r.get('receipt_number') or ''),
                    self.db_manager.get_weekly_supplier_breakdown_text(r['client_id'], ws, we),
                    str(r.get('week_start') or ''),
                    str(r.get('week_end') or ''),
                ]).lower()
                if search_text in hay:
                    filtered.append(r)
            rows = filtered

        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            client_text = r['client_name']
            if r.get('client_company'):
                client_text += f" ({r['client_company']})"
            self.table.setItem(i, 0, QTableWidgetItem(client_text))
            
            # Cylinder breakdown and Empty Return
            cyl_breakdown = self.db_manager.get_weekly_sales_breakdown(r['client_id'], ws, we)
            empty_returns = self.db_manager.get_weekly_returns_breakdown(r['client_id'], ws, we)
            supplier_breakdown = self.db_manager.get_weekly_supplier_breakdown_text(r['client_id'], ws, we)
            self.table.setItem(i, 1, QTableWidgetItem(cyl_breakdown))
            self.table.setItem(i, 2, QTableWidgetItem(empty_returns))
            self.table.setItem(i, 3, QTableWidgetItem(supplier_breakdown))
            
            self.table.setItem(i, 4, QTableWidgetItem(f"{float(r['subtotal']):,.2f}"))
            self.table.setItem(i, 5, QTableWidgetItem(f"{float(r['discount']):,.2f}"))
            self.table.setItem(i, 6, QTableWidgetItem(f"{float(r['tax_amount']):,.2f}"))
            self.table.setItem(i, 7, QTableWidgetItem(f"{float(r['total_payable']):,.2f}"))
            self.table.setItem(i, 8, QTableWidgetItem(f"{float(r['previous_balance']):,.2f}"))
            self.table.setItem(i, 9, QTableWidgetItem(f"{float(r['final_payable']):,.2f}"))
            self.table.setItem(i, 10, QTableWidgetItem(f"{float(r['amount_paid']):,.2f}"))
            remaining_val = max(0.0, float(r['final_payable']) - float(r['amount_paid']))
            self.table.setItem(i, 11, QTableWidgetItem(f"{remaining_val:,.2f}"))
            status_item = QTableWidgetItem(r['status'])
            if r['status'] == 'PAID':
                status_item.setForeground(Qt.darkGreen)
            else:
                status_item.setForeground(Qt.red)
            self.table.setItem(i, 12, status_item)

            for col_idx in [4, 5, 6, 7, 8, 9, 10, 11]:
                item = self.table.item(i, col_idx)
                if item:
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            actions = QWidget()
            actions.setMinimumHeight(22)
            h = QHBoxLayout(actions)
            h.setContentsMargins(0, 0, 0, 0)
            h.setSpacing(2)
            h.setAlignment(Qt.AlignCenter)
            btn_print = self._small_button("View", "warning")
            btn_print.setFixedWidth(50)
            btn_print.clicked.connect(lambda checked=False, row=r: self.print_client(row))
            h.addWidget(btn_print)
            btn_pay = self._small_button("Pay", "success")
            btn_pay.setFixedWidth(50)
            btn_pay.clicked.connect(lambda checked=False, row=r: self.record_payment(row))
            h.addWidget(btn_pay)
            btn_mark = self._small_button("Mark Paid", "primary")
            btn_mark.setFixedWidth(68)
            btn_mark.setEnabled(max(0.0, float(r['final_payable']) - float(r['amount_paid'])) <= 0.01 and r['status'] != 'PAID')
            btn_mark.clicked.connect(lambda checked=False, row=r: self.mark_paid(row))
            h.addWidget(btn_mark)
            actions.setLayout(h)
            self.table.setCellWidget(i, 13, actions)
            self.table.setItem(i, 14, QTableWidgetItem(f"{r['week_start']} to {r['week_end']}"))
            self.table.setRowHeight(i, 28)

    def print_client(self, invoice_row: dict):
        dlg = WeeklyClientReceiptDialog(self.db_manager, invoice_row, self)
        dlg.exec()

    def record_payment(self, invoice_row: dict):
        remaining = max(0.0, float(invoice_row['final_payable']) - float(invoice_row['amount_paid']))
        if remaining <= 0:
            QMessageBox.information(self, "Info", "No remaining balance.")
            return
        dlg = QDialog(self)
        dlg.setWindowTitle("Record Payment")
        f = QFormLayout(dlg)
        amt = QDoubleSpinBox()
        amt.setMaximum(remaining)
        amt.setDecimals(2)
        date_edit = QDateEdit()
        date_edit.setCalendarPopup(True)
        date_edit.setDate(QDate.currentDate())
        method = QComboBox()
        method.addItems(["Cash", "Bank Transfer", "Cheque", "Other"])
        ok_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        h = QHBoxLayout()
        h.addWidget(ok_btn)
        h.addWidget(cancel_btn)
        f.addRow("Amount", amt)
        f.addRow("Date", date_edit)
        f.addRow("Method", method)
        f.addRow(h)
        ok_btn.clicked.connect(dlg.accept)
        cancel_btn.clicked.connect(dlg.reject)
        if not dlg.exec():
            return
        amount = float(amt.value())
        if amount <= 0:
            QMessageBox.warning(self, "Invalid", "Amount must be greater than zero.")
            return
        if amount > remaining:
            QMessageBox.warning(self, "Invalid", "Amount cannot exceed the remaining balance.")
            return
        try:
            day = date_edit.date().toString('yyyy-MM-dd')
            self.db_manager.record_weekly_payment(invoice_row['id'], amount, day, self.current_user.get('id'), method.currentText())
            QMessageBox.information(self, "Success", "Payment recorded.")
            self.load_weekly_invoices()
            refresh_application_views("weekly_payments", "clients", "receipts", "cylinder_track", "reports")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def mark_paid(self, invoice_row: dict):
        try:
            self.db_manager.mark_weekly_invoice_paid(invoice_row['id'])
            QMessageBox.information(self, "Success", "Weekly invoice marked as PAID.")
            self.load_weekly_invoices()
            refresh_application_views("weekly_payments", "clients", "receipts", "cylinder_track", "reports")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

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

    def print_weekly_list(self):
        try:
            printer = QPrinter(QPrinter.HighResolution)
            printer.setPageSize(QPageSize(QPageSize.A4))
            printer.setPageOrientation(QPageLayout.Landscape)
            printer.setFullPage(False)
            dialog = QPrintDialog(printer, self)
            if dialog.exec():
                if not printer.isValid():
                    QMessageBox.critical(self, "Printer Error", "The selected printer is not valid.")
                    return

                ws, we = self.get_week_range()
                logo = self.resolve_logo_path()
                total_clients = self.table.rowCount()
                total_final = 0.0
                total_paid = 0.0
                total_remaining = 0.0

                html = [
                    "<html><head><style>",
                    "body{font-family:Arial,sans-serif;color:#0f172a;margin:0}",
                    ".sheet{padding:14px 18px}",
                    ".head{border-bottom:2px solid #1f4f82;padding-bottom:8px;margin-bottom:10px;text-align:center}",
                    ".brand{display:flex;align-items:center;justify-content:center;gap:10px}",
                    ".logo{width:36px;height:36px;border:1px solid #334155;border-radius:50%}",
                    ".t1{font-size:20px;font-weight:800;color:#1f4f82}",
                    ".t2{font-size:11px;color:#334155}",
                    ".title{font-size:14px;font-weight:700;text-align:center;margin:6px 0 8px 0}",
                    ".summary{font-size:11px;text-align:center;margin-bottom:8px}",
                    "table{width:100%;border-collapse:collapse;font-size:9.2px}",
                    "th,td{border:1px solid #334155;padding:3px 4px;text-align:center;vertical-align:middle}",
                    "th{background:#eaf0f8;font-weight:700}",
                    "tr:nth-child(even) td{background:#f8fafc}",
                    ".status-paid{color:#166534;font-weight:700}",
                    ".status-unpaid{color:#b91c1c;font-weight:700}",
                    "</style></head><body><div class='sheet'>",
                    "<div class='head'>",
                    "<div class='brand'>",
                    f"<img src='{logo}' class='logo' alt='Logo'/>",
                    "<div><div class='t1'>RAJPUT GAS TRADERS</div><div class='t2'>Prop: Saleem Ahmad | 0301-6465144</div></div>",
                    "</div>",
                    "<div class='t2'>Plot No.69C-70C, Small Industrial Estate No.2, Gujranwala</div>",
                    "</div>",
                    f"<div class='title'>WEEKLY BILLING STATEMENT ({ws} to {we})</div>",
                ]

                html.append("<table><tr><th>#</th><th>First Name</th><th>Cylinders</th><th>Empty Return</th><th>Sources</th><th>Subtotal</th><th>Discount</th><th>Tax</th><th>Total</th><th>Prev</th><th>Final</th><th>Paid</th><th>Remaining</th><th>Status</th></tr>")

                for i in range(self.table.rowCount()):
                    raw_client = self.table.item(i, 0).text() if self.table.item(i, 0) else ""
                    full_name = raw_client.split(' (')[0].strip()
                    first_name = full_name.split()[0] if full_name else "-"
                    cyl = self.table.item(i, 1).text() if self.table.item(i, 1) else ""
                    empty = self.table.item(i, 2).text() if self.table.item(i, 2) else ""
                    source = self.table.item(i, 3).text() if self.table.item(i, 3) else ""
                    sub = self.table.item(i, 4).text() if self.table.item(i, 4) else ""
                    disc = self.table.item(i, 5).text() if self.table.item(i, 5) else ""
                    tax = self.table.item(i, 6).text() if self.table.item(i, 6) else ""
                    tot = self.table.item(i, 7).text() if self.table.item(i, 7) else ""
                    prev = self.table.item(i, 8).text() if self.table.item(i, 8) else ""
                    final = self.table.item(i, 9).text() if self.table.item(i, 9) else ""
                    paid = self.table.item(i, 10).text() if self.table.item(i, 10) else ""
                    remaining = self.table.item(i, 11).text() if self.table.item(i, 11) else ""
                    status = self.table.item(i, 12).text() if self.table.item(i, 12) else ""

                    try:
                        total_final += float((final or "0").replace(',', ''))
                        total_paid += float((paid or "0").replace(',', ''))
                        total_remaining += float((remaining or "0").replace(',', ''))
                    except Exception:
                        pass

                    status_cls = "status-paid" if status == "PAID" else "status-unpaid"
                    html.append(
                        f"<tr><td>{i+1}</td><td>{first_name}</td><td>{cyl}</td><td>{empty}</td><td>{source}</td><td>{sub}</td><td>{disc}</td><td>{tax}</td><td>{tot}</td><td>{prev}</td><td>{final}</td><td>{paid}</td><td>{remaining}</td><td class='{status_cls}'>{status}</td></tr>"
                    )

                html.append("</table>")
                html.append(f"<div class='summary'><b>Clients:</b> {total_clients} &nbsp;&nbsp; <b>Final Total:</b> {total_final:,.2f} &nbsp;&nbsp; <b>Paid:</b> {total_paid:,.2f} &nbsp;&nbsp; <b>Remaining:</b> {total_remaining:,.2f}</div>")
                html.append("</div></body></html>")

                doc = QTextDocument()
                doc.setDefaultFont(QFont("Arial", 9))
                doc.setHtml("".join(html))
                rect = printer.pageRect(QPrinter.Point)
                if rect.isValid() and rect.width() > 0:
                    doc.setPageSize(rect.size())
                else:
                    doc.setPageSize(QSizeF(842, 595))
                doc.print_(printer)
        except Exception as e:
            QMessageBox.critical(self, "Print Error", f"Failed to print weekly statement: {str(e)}")

