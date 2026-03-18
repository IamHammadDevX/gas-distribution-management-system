from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QDateEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QFrame, QHeaderView,
    QAbstractItemView
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtPrintSupport import QPrinter, QPrintDialog
from PySide6.QtGui import QTextDocument, QFont, QPageSize, QPageLayout
from src.database_module import DatabaseManager

class DailyTransactionsWidget(QWidget):
    def __init__(self, db_manager: DatabaseManager, current_user: dict):
        super().__init__()
        self.db_manager = db_manager
        self.current_user = current_user
        self.init_ui()
        self.load_transactions()

    def init_ui(self):
        self.setStyleSheet("""
            QWidget { background-color: #f5f6f8; color: #1f2937; font-size: 13px; }
            QLabel#titleLabel { font-size: 24px; font-weight: 700; color: #1f4f82; }
            QFrame#sectionCard { background: #ffffff; border: 1px solid #dbe1e7; border-radius: 10px; }
            QDateEdit {
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
        layout.setSpacing(10)
        layout.setContentsMargins(12, 12, 12, 12)

        title = QLabel("Daily Transactions")
        title.setObjectName("titleLabel")
        layout.addWidget(title)

        controls_card = QFrame()
        controls_card.setObjectName("sectionCard")
        bar = QHBoxLayout(controls_card)
        bar.setSpacing(10)
        bar.setContentsMargins(10, 10, 10, 10)

        bar.addWidget(QLabel("Date:"))

        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.dateChanged.connect(self.load_transactions)
        bar.addWidget(self.date_edit)

        refresh_btn = self._make_small_button("Refresh", "primary")
        refresh_btn.clicked.connect(self.load_transactions)
        bar.addWidget(refresh_btn)

        print_btn = self._make_small_button("Print Day Summary", "dark")
        print_btn.clicked.connect(self.print_daily_report)
        bar.addWidget(print_btn)

        bar.addStretch(1)

        self.count_label = QLabel("Transactions: 0")
        self.total_label = QLabel("Total Sales: Rs. 0.00")
        self.total_label.setStyleSheet("font-weight: 700; color: #1f4f82;")
        bar.addWidget(self.count_label)
        bar.addSpacing(8)
        bar.addWidget(self.total_label)

        layout.addWidget(controls_card)

        sales_card = QFrame()
        sales_card.setObjectName("sectionCard")
        sales_layout = QVBoxLayout(sales_card)
        sales_layout.setContentsMargins(10, 10, 10, 10)
        sales_layout.setSpacing(8)

        sales_title = QLabel("Sales")
        sales_title.setStyleSheet("font-size: 15px; font-weight: 700;")
        sales_layout.addWidget(sales_title)

        self.sales_table = QTableWidget()
        self.sales_table.setColumnCount(8)
        self.sales_table.setHorizontalHeaderLabels(["Date", "Client", "Products", "Quantities", "Total", "Paid", "Balance", "Cashier"])
        self._setup_table()
        sales_layout.addWidget(self.sales_table)
        layout.addWidget(sales_card, 1)

    def _make_small_button(self, text: str, kind: str = "secondary"):
        button = QPushButton(text)
        button.setFixedHeight(28)
        button.setFocusPolicy(Qt.NoFocus)
        styles = {
            "primary": (
                "QPushButton { background-color: #1a73e8; color: white; border: 1px solid #125bc4; border-radius: 5px; padding: 4px 10px; font-size: 12px; font-weight: 600; }"
                "QPushButton:hover { background-color: #1765cb; }"
                "QPushButton:pressed { background-color: #125bc4; }"
            ),
            "dark": (
                "QPushButton { background-color: #2c3e50; color: white; border: 1px solid #1f2d3a; border-radius: 5px; padding: 4px 10px; font-size: 12px; font-weight: 600; }"
                "QPushButton:hover { background-color: #1f2d3a; }"
                "QPushButton:pressed { background-color: #16222c; }"
            ),
            "secondary": (
                "QPushButton { background-color: #6c757d; color: white; border: 1px solid #596168; border-radius: 5px; padding: 4px 10px; font-size: 12px; font-weight: 600; }"
                "QPushButton:hover { background-color: #5e666d; }"
                "QPushButton:pressed { background-color: #535a61; }"
            ),
        }
        button.setStyleSheet(styles.get(kind, styles["secondary"]))
        return button

    def _setup_table(self):
        self.sales_table.setAlternatingRowColors(True)
        self.sales_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.sales_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.sales_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.sales_table.setWordWrap(True)
        self.sales_table.verticalHeader().setVisible(False)
        self.sales_table.verticalHeader().setDefaultSectionSize(36)

        header = self.sales_table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)

    def load_transactions(self):
        d_str = self.date_edit.date().toString('yyyy-MM-dd')
        self.load_sales_for_date(d_str)

    def load_sales_for_date(self, day_str):
        try:
            rows = self.db_manager.get_sales_for_date_with_summaries(day_str)
            self.sales_table.setRowCount(len(rows))
            total_sales = 0.0
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
                total_sales += float(r.get('total_amount') or 0)
                self.sales_table.setRowHeight(i, 36)

            self.count_label.setText(f"Transactions: {len(rows)}")
            self.total_label.setText(f"Total Sales: Rs. {total_sales:,.2f}")
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load daily transactions: {str(e)}")

    def print_daily_report(self):
        try:
            printer = QPrinter(QPrinter.HighResolution)
            printer.setPageSize(QPageSize(QPageSize.A4))
            printer.setPageOrientation(QPageLayout.Portrait)
            printer.setResolution(300)
            dialog = QPrintDialog(printer, self)
            if dialog.exec():
                d = self.date_edit.date().toString('yyyy-MM-dd')
                total_sales = 0.0
                total_paid = 0.0
                total_balance = 0.0
                html = [
                    "<html><head><style>",
                    "body{font-family:Arial,sans-serif;color:#0f172a;margin:0}",
                    ".sheet{max-width:760px;margin:0 auto;padding:14px 18px;border:1.5px solid #1f2937;border-radius:10px}",
                    ".head{text-align:center;border-bottom:2px solid #1f4f82;padding-bottom:8px;margin-bottom:10px}",
                    ".title{font-size:18px;font-weight:800;color:#1f4f82}",
                    ".sub{font-size:12px;color:#334155;margin-top:2px}",
                    "table{width:100%;border-collapse:collapse;font-size:9.6px}",
                    "th,td{border:1px solid #334155;padding:4px 5px;text-align:center;vertical-align:middle}",
                    "th{background:#eaf0f8;font-weight:700}",
                    "tr:nth-child(even) td{background:#f8fafc}",
                    ".tot{margin-top:8px;font-size:11px;text-align:center}",
                    "</style></head><body><div class='sheet'>",
                    "<div class='head'>",
                    "<div class='title'>DAILY TRANSACTION SUMMARY</div>",
                    f"<div class='sub'>Date: {d}</div>",
                    "</div>",
                    "<table>",
                    "<tr><th>Time</th><th>Client</th><th>Products</th><th>Qty</th><th>Total</th><th>Paid</th><th>Balance</th><th>Cashier</th></tr>"
                ]
                for i in range(self.sales_table.rowCount()):
                    row = []
                    for j in range(self.sales_table.columnCount()):
                        item = self.sales_table.item(i, j)
                        row.append(item.text() if item else "")
                    display_time = row[0][11:16] if len(row[0]) >= 16 else row[0]
                    html.append(f"<tr><td>{display_time}</td><td>{row[1]}</td><td>{row[2]}</td><td>{row[3]}</td><td>{row[4]}</td><td>{row[5]}</td><td>{row[6]}</td><td>{row[7]}</td></tr>")

                    try:
                        total_sales += float((row[4] or "0").replace("Rs.", "").replace(",", "").strip())
                        total_paid += float((row[5] or "0").replace("Rs.", "").replace(",", "").strip())
                        total_balance += float((row[6] or "0").replace("Rs.", "").replace(",", "").strip())
                    except Exception:
                        pass

                if self.sales_table.rowCount() == 0:
                    html.append("<tr><td colspan='8'>No transactions found for selected date.</td></tr>")

                html.append("</table>")
                html.append(f"<div class='tot'><b>Transactions:</b> {self.sales_table.rowCount()} &nbsp;&nbsp; <b>Total Sales:</b> Rs. {total_sales:,.2f} &nbsp;&nbsp; <b>Total Paid:</b> Rs. {total_paid:,.2f} &nbsp;&nbsp; <b>Total Balance:</b> Rs. {total_balance:,.2f}</div>")
                html.append("</div></body></html>")

                doc = QTextDocument()
                doc.setDefaultFont(QFont("Arial", 10))
                doc.setHtml("".join(html))
                doc.setPageSize(printer.pageRect(QPrinter.Point).size())
                doc.print_(printer)
        except Exception as e:
            QMessageBox.critical(self, "Print Error", f"Failed to print daily summary: {str(e)}")
