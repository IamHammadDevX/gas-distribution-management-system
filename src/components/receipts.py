from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                               QTableWidgetItem, QPushButton, QLineEdit, QLabel, 
                               QMessageBox, QDialog, QFormLayout, QDialogButtonBox,
                               QTextEdit, QHeaderView, QGroupBox, QGridLayout,
                               QFrame, QScrollArea, QAbstractItemView)
from PySide6.QtCore import Qt, QDateTime
from PySide6.QtPrintSupport import QPrinter, QPrintDialog
from PySide6.QtGui import QTextDocument
from PySide6.QtCore import QSizeF
from PySide6.QtGui import QPageSize, QPageLayout
from PySide6.QtPrintSupport import QPrinter, QPrintDialog
from src.database_module import DatabaseManager
from src.components.ui_helpers import as_datetime_text, as_money, as_text, table_batch_update
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.lib import colors
import os

class ReceiptDialog(QDialog):
    def __init__(self, db_manager: DatabaseManager, receipt_data: dict, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.receipt_data = receipt_data
        self.setWindowTitle(f"Receipt - {receipt_data['receipt_number']}")
        self.resize(620, 700)
        self.setMinimumSize(520, 560)
        self.init_ui()
    
    def init_ui(self):
        self.setStyleSheet("""
            QDialog { background-color: #f5f6f8; }
            QFrame#receiptCard { background: #ffffff; border: 1px solid #dbe1e7; border-radius: 10px; }
            QLabel#titleLabel { font-size: 18px; font-weight: 700; color: #1f4f82; }
            QTextEdit {
                background: #ffffff;
                border: 1px solid #d0d7df;
                border-radius: 8px;
                padding: 4px;
                font-size: 12px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(12, 12, 12, 12)

        title = QLabel("Receipt Preview")
        title.setObjectName("titleLabel")
        layout.addWidget(title)

        card = QFrame()
        card.setObjectName("receiptCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(10, 10, 10, 10)
        card_layout.setSpacing(8)

        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setMinimumHeight(360)
        try:
            self.preview.setHtml(self.generate_receipt_html())
        except Exception as e:
            self.preview.setPlainText(f"Unable to render receipt preview.\n\nError: {str(e)}")
            QMessageBox.warning(self, "Preview Error", f"Failed to render receipt preview: {str(e)}")
        card_layout.addWidget(self.preview)
        layout.addWidget(card, 1)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        button_layout.addStretch(1)

        print_btn = self._make_small_button("Print", "warning")
        print_btn.clicked.connect(self.print_receipt)
        button_layout.addWidget(print_btn)

        export_btn = self._make_small_button("Export PDF", "dark")
        export_btn.clicked.connect(self.export_pdf)
        button_layout.addWidget(export_btn)

        close_btn = self._make_small_button("Close", "secondary")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

    def _make_small_button(self, text: str, kind: str = "secondary") -> QPushButton:
        btn = QPushButton(text)
        btn.setMinimumWidth(82)
        btn.setFixedHeight(28)
        btn.setFocusPolicy(Qt.NoFocus)
        styles = {
            "warning": (
                "QPushButton { background-color: #f39c12; color: white; border: 1px solid #d68910; border-radius: 5px; padding: 4px 8px; font-size: 12px; font-weight: 600; }"
                "QPushButton:hover { background-color: #d68910; }"
                "QPushButton:pressed { background-color: #b9770e; }"
            ),
            "dark": (
                "QPushButton { background-color: #2c3e50; color: white; border: 1px solid #1f2d3a; border-radius: 5px; padding: 4px 8px; font-size: 12px; font-weight: 600; }"
                "QPushButton:hover { background-color: #1f2d3a; }"
                "QPushButton:pressed { background-color: #16222c; }"
            ),
            "secondary": (
                "QPushButton { background-color: #6c757d; color: white; border: 1px solid #596168; border-radius: 5px; padding: 4px 8px; font-size: 12px; font-weight: 600; }"
                "QPushButton:hover { background-color: #5e666d; }"
                "QPushButton:pressed { background-color: #535a61; }"
            ),
        }
        btn.setStyleSheet(styles.get(kind, styles["secondary"]))
        return btn
    def _logo_path(self) -> str:
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
    
    def print_receipt(self):
        """Print the receipt (A4, small logo, fit content)"""
        try:
            from PySide6.QtGui import QTextDocument
            from PySide6.QtPrintSupport import QPrinter, QPrintDialog
            from PySide6.QtGui import QPageSize, QPageLayout
            from PySide6.QtCore import QSizeF

            printer = QPrinter(QPrinter.HighResolution)
            printer.setPageSize(QPageSize(QPageSize.A4))
            printer.setPageOrientation(QPageLayout.Portrait)
            printer.setFullPage(False)

            dialog = QPrintDialog(printer, self)
            if dialog.exec() == QDialog.Accepted:
                doc = QTextDocument()
                html_content = self.generate_receipt_html(for_print=True)
                doc.setHtml(html_content)
                doc.setPageSize(QSizeF(650, 900))
                doc.print_(printer)
        except Exception as e:
            QMessageBox.critical(self, "Print Error", f"Failed to print receipt: {str(e)}")
    
    def export_pdf(self):
        """Export receipt as PDF"""
        from PySide6.QtWidgets import QFileDialog

        try:
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Export Receipt as PDF",
                f"Receipt_{self.receipt_data['receipt_number']}.pdf",
                "PDF Files (*.pdf)"
            )

            if filename:
                if not filename.lower().endswith('.pdf'):
                    filename += '.pdf'
                self.generate_pdf_receipt(filename)
                QMessageBox.information(self, "Success", f"Receipt exported to {filename}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export PDF: {str(e)}")
    
    def generate_receipt_html(self, for_print: bool = False) -> str:
        logo_path = self._logo_path()
        try:
            items = self.db_manager.get_sale_items(self.receipt_data['sale_id'])
        except Exception:
            items = []
        total_qty = sum(item['quantity'] for item in items) if items else int(self.receipt_data.get('quantity', 0))
        total_tax_val = sum(float(i['tax_amount']) for i in items) if items else float(self.receipt_data.get('tax_amount', 0) or 0)
        sum_subtotal = sum(float(i['subtotal']) for i in items) if items else float(self.receipt_data.get('subtotal', 0) or 0)
        pre_discount_total = sum(float(i['total_amount']) for i in items) if items else (float(self.receipt_data.get('subtotal', 0) or 0) + float(self.receipt_data.get('tax_amount', 0) or 0))
        overall_discount_val = max(0.0, pre_discount_total - float(self.receipt_data.get('total_amount', 0) or 0))
        bill_extra_rows = ""
        if total_tax_val > 0:
            bill_extra_rows += f"<tr><td class=\"box-label\">Tax</td><td>{total_tax_val:,.2f}</td></tr>"
        if overall_discount_val > 0:
            bill_extra_rows += f"<tr><td class=\"box-label\">Order Discount</td><td>{overall_discount_val:,.2f}</td></tr>"
        style = """
body { font-family: Arial, sans-serif; color: #111; background: #fff; margin: 0; padding: 0; }
.receipt {
    width: 78mm;
    margin: 0 auto;
    padding: 6px 6px 8px 6px;
    border: 1px solid #333;
    border-radius: 6px;
    background: #fff;
}
.brand { text-align: center; border-bottom: 1px dashed #666; padding-bottom: 4px; margin-bottom: 6px; }
.logo-wrap { text-align: center; margin-bottom: 3px; }
.logo { width: 26mm; height: auto; max-height: 14mm; object-fit: contain; }
.store-title { font-size: 12px; font-weight: 800; letter-spacing: .3px; }
.info { font-size: 9px; margin-top: 1px; }
.bill-title { text-align: center; font-size: 10px; font-weight: 700; margin: 4px 0; }
.customer { font-size: 9px; margin-bottom: 4px; line-height: 1.35; }
.tbl { width: 100%; border-collapse: collapse; font-size: 8.4px; }
.tbl th, .tbl td { border: 1px solid #555; padding: 2px 2px; text-align: center; }
.tbl th { background: #f2f4f7; }
.summary { width: 100%; border-collapse: collapse; margin-top: 4px; font-size: 8.8px; }
.summary td { border: 1px solid #555; padding: 2px 3px; }
.summary .label { font-weight: 700; }
.signature { margin-top: 8px; font-size: 9px; }
.footer { margin-top: 6px; padding-top: 4px; border-top: 1px dashed #666; text-align: center; font-size: 8.4px; }
        """
        rows_parts = []
        if for_print:
            for it in items:
                prod = f"{it['gas_type']}{(' ' + it['sub_type']) if it.get('sub_type') else ''} {it['capacity']}".strip()
                disc = max(0.0, float(it['quantity']) * float(it['unit_price']) - float(it['subtotal']))
                rows_parts.append(
                    f"<tr><td>{str(it['created_at'])[:10]}</td><td>{prod}</td><td>{it['quantity']}</td><td>{disc:,.0f}</td><td>{float(it['subtotal']):,.0f}</td><td>{float(it['tax_amount']):,.0f}</td><td>{float(it['total_amount']):,.0f}</td></tr>"
                )
        else:
            try:
                summaries = self.db_manager.get_sale_item_summaries(self.receipt_data['sale_id'])
            except Exception:
                summaries = {}
            products_text = summaries.get('product_summary') or (f"{self.receipt_data.get('gas_type','')} {self.receipt_data.get('capacity','')}".strip())
            quantities_text = summaries.get('quantities_summary') or str(self.receipt_data.get('quantity') or '')
            rows_parts.append(
                f"<tr>"
                f"<td>{self.receipt_data['created_at'][:10]}</td>"
                f"<td>{products_text}</td>"
                f"<td>{quantities_text}</td>"
                f"<td>{sum_subtotal:,.0f}</td>"
                f"<td>{total_tax_val:,.0f}</td>"
                f"<td>{float(self.receipt_data['total_amount']):,.0f}</td>"
                f"</tr>"
            )
        rows_html = "".join(rows_parts)
        logo_html = f'<div class="logo-wrap"><img src="{logo_path}" class="logo" alt="Logo"/></div>' if os.path.exists(logo_path) else ''

        return f"""
<html>
<head>
<style>{style}</style>
</head>
<body>
<div class="receipt"> 
    <div class="brand">
        {logo_html}
        <div class="store-title">RAJPUT GAS TRADERS</div>
        <div class="info">Prop: Saleem Ahmad | 0301-6465144</div>
        <div class="info">Date: {self.receipt_data['created_at'][:10]} | Ref: {self.receipt_data.get('receipt_number','')}</div>
  </div>
    <div class="bill-title">TAX INVOICE / CASH RECEIPT</div>
    <div class="customer"><b>Customer:</b> {self.receipt_data['client_name']}</div>
  <table class="tbl">
{('<tr><th>DATE</th><th>PRODUCTS</th><th>QUA</th><th>DISC</th><th>SUB-T</th><th>TAX</th><th>TOTAL</th></tr>' if for_print else '<tr><th>DATE</th><th>PRODUCTS</th><th>QUA</th><th>SUB-T</th><th>TAX</th><th>TOTAL</th></tr>')}
{rows_html}
<tr style="font-weight:bold; background:#fff;">
{('<td colspan="4" style="text-align:right;">TOTAL QTY</td><td>' + str(total_qty) + '</td><td style="text-align:right;">GRAND TOTAL</td><td>' + f"{float(self.receipt_data['total_amount']):,.2f}" + '</td>' if for_print else '<td colspan="3" style="text-align:right;">TOTAL QTY</td><td>' + str(total_qty) + '</td><td style="text-align:right;">GRAND TOTAL</td><td>' + f"{float(self.receipt_data['total_amount']):,.0f}" + '</td>' )}
</tr>
</table>
    <table class="summary">
        {bill_extra_rows}
        <tr>
                        <td class="label">Pending Bill</td>
            <td>{self.receipt_data['balance']:,.2f}</td>
        </tr>
        <tr>
                        <td class="label">Total Bill</td>
            <td>{float(self.receipt_data['total_amount']):,.2f}</td>
        </tr>
    </table>
    <div class="signature">Signature: ____________________</div>
  <div class="footer">Plot No.69C-70C, Small Industrial Estate No.2, Gujranwala</div>
</div>
</body>
</html>
        """

    def generate_pdf_receipt(self, filename: str):
        logo_path = self._logo_path()
        items = self.db_manager.get_sale_items(self.receipt_data['sale_id'])
        total_qty = sum(item['quantity'] for item in items) if items else int(self.receipt_data.get('quantity', 0))
        total_tax_val = sum(float(i['tax_amount']) for i in items) if items else float(self.receipt_data.get('tax_amount', 0) or 0)
        pre_discount_total = sum(float(i['total_amount']) for i in items) if items else (float(self.receipt_data.get('subtotal', 0) or 0) + float(self.receipt_data.get('tax_amount', 0) or 0))
        overall_discount_val = max(0.0, pre_discount_total - float(self.receipt_data.get('total_amount', 0) or 0))
        doc = SimpleDocTemplate(
            filename,
            pagesize=(80 * mm, 200 * mm),
            leftMargin=5 * mm,
            rightMargin=5 * mm,
            topMargin=7 * mm,
            bottomMargin=5 * mm,
        )
        styles = getSampleStyleSheet()
        story = []
        # Logo -- (will skip if logo isn't found)
        if os.path.exists(logo_path):
            story.append(Image(logo_path, width=38*mm, height=19*mm))

        # Top Title
        story.append(Paragraph('<b style="font-size:16pt;">RAJPUT GAS TRADERS</b>', ParagraphStyle('store', parent=styles['Normal'], alignment=1, fontSize=16)))
        story.append(Paragraph('Prop: Saleem Ahmad | 0301-6465144', ParagraphStyle('prop', parent=styles['Normal'], alignment=1, fontSize=10)))
        story.append(Spacer(1, 4))
        # Meta row
        meta_row = f"""
            <b>Date:</b> {self.receipt_data['created_at'][:10]}
            &nbsp;&nbsp; <b>Ref:</b> {self.receipt_data.get('receipt_number', '')}
        """
        story.append(Paragraph(meta_row, ParagraphStyle('meta', parent=styles['Normal'], alignment=0, fontSize=10)))
        story.append(Spacer(1, 4))
        story.append(Paragraph('GAS BILL', ParagraphStyle('bill', parent=styles['Heading2'], alignment=1, fontSize=13)))
        story.append(Spacer(1, 3))
        story.append(Paragraph(f'<b>CUSTOMER NAME :</b> {self.receipt_data["client_name"]}', ParagraphStyle('cust', parent=styles['Normal'], alignment=0, fontSize=11)))
        story.append(Spacer(1, 6))
        summaries = self.db_manager.get_sale_item_summaries(self.receipt_data['sale_id'])
        products_text = summaries.get('product_summary') or (f"{self.receipt_data.get('gas_type','')} {self.receipt_data.get('capacity','')}".strip())
        quantities_text = summaries.get('quantities_summary') or str(self.receipt_data.get('quantity') or '')
        sum_subtotal = sum(float(i['subtotal']) for i in items) if items else float(self.receipt_data.get('subtotal', 0) or 0)
        items_data = [['DATE', 'PRODUCTS', 'QUANTITIES', 'SUBTOTAL', 'TAX', 'TOTAL'], [
            self.receipt_data['created_at'][:10],
            products_text,
            quantities_text,
            f"{sum_subtotal:,.0f}",
            f"{total_tax_val:,.0f}",
            f"{float(self.receipt_data['total_amount']):,.0f}"
        ]]
        items_table = Table(items_data, colWidths=[20*mm, 24*mm, 18*mm, 12*mm, 10*mm, 12*mm])
        items_table.hAlign = 'CENTER'
        items_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1.5, colors.black),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ]))
        story.append(items_table)
        # Footer row for totals
        totals_data = [["", "", "TOTAL QTY", total_qty, "GRAND TOTAL", f"{self.receipt_data['total_amount']:,.0f}"]]
        totals_table = Table(totals_data, colWidths=[20*mm,24*mm,18*mm,12*mm,10*mm,12*mm])
        totals_table.hAlign = 'CENTER'
        totals_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1.5, colors.black),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        story.append(totals_table)
        story.append(Spacer(1, 7))
        # Bill/Pending Box
        labels = []
        if total_tax_val > 0:
            labels.append(['Tax', f"{total_tax_val:,.0f}"])
        if overall_discount_val > 0:
            labels.append(['Order Discount', f"{overall_discount_val:,.0f}"])
        labels.append(['Pending Bill', f"{self.receipt_data['balance']:,.0f}"])
        labels.append(['Total Bill', f"{self.receipt_data['total_amount']:,.0f}"])
        bill_table = Table(labels, colWidths=[24*mm, 24*mm])
        bill_table.hAlign = 'CENTER'
        bill_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1.5, colors.black),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
        ]))
        story.append(bill_table)
        story.append(Spacer(1, 8))
        # Signature
        story.append(Paragraph('Signature________________', ParagraphStyle('sign', parent=styles['Normal'], alignment=2, fontSize=12)))
        story.append(Spacer(1, 7))
        # Footer
        story.append(Paragraph('Plot No.69C-70C, Small Industrial Estate No.2, Gujranwala', ParagraphStyle('foot', parent=styles['Normal'], alignment=1, fontSize=12, textColor=colors.black, spaceBefore=12, spaceAfter=8)))
        doc.build(story)
    
    def generate_pdf_receipt(self, filename: str):
        logo_path = self._logo_path()
        items = self.db_manager.get_sale_items(self.receipt_data['sale_id'])
        total_qty = sum(item['quantity'] for item in items) if items else int(self.receipt_data.get('quantity', 0))
        total_tax_val = sum(float(i['tax_amount']) for i in items) if items else float(self.receipt_data.get('tax_amount', 0) or 0)
        pre_discount_total = sum(float(i['total_amount']) for i in items) if items else (float(self.receipt_data.get('subtotal', 0) or 0) + float(self.receipt_data.get('tax_amount', 0) or 0))
        overall_discount_val = max(0.0, pre_discount_total - float(self.receipt_data.get('total_amount', 0) or 0))
        from reportlab.lib.pagesizes import A4

        # -- Layout for A4 --
        doc = SimpleDocTemplate(
            filename,
            pagesize=A4,
            leftMargin=25 * mm,
            rightMargin=25 * mm,
            topMargin=20 * mm,
            bottomMargin=15 * mm,
        )
        styles = getSampleStyleSheet()
        styleTitle = ParagraphStyle('store', parent=styles['Normal'], alignment=1, fontSize=22, spaceAfter=8)
        styleContact = ParagraphStyle('contact', parent=styles['Normal'], alignment=1, fontSize=13, spaceAfter=4)
        styleMeta = ParagraphStyle('meta', parent=styles['Normal'], alignment=1, fontSize=13, spaceAfter=10)
        styleBillTitle = ParagraphStyle('bill', parent=styles['Normal'], alignment=1, fontSize=17, spaceAfter=7)
        styleLabel = ParagraphStyle('label', parent=styles['Normal'], alignment=0, fontSize=14, spaceAfter=0)
        styleFooter = ParagraphStyle('footer', parent=styles['Normal'], alignment=1, fontSize=14, spaceBefore=14)
        styleSignature = ParagraphStyle('sign', parent=styles['Normal'], alignment=2, fontSize=15, italic=True)
        
        story = []
        # -- Logo (small, centered) --
        if os.path.exists(logo_path):
            img = Image(logo_path)
            img.drawHeight = 18 * mm
            img.drawWidth = 36 * mm
            img.hAlign = 'CENTER'
            story.append(img)
            story.append(Spacer(1, 6))
        # -- Business Info --
        story.append(Paragraph("RAJPUT GAS TRADERS", styleTitle))
        story.append(Paragraph("Prop: Saleem Ahmad | 0301-6465144", styleContact))
        story.append(Spacer(1, 3))
        # -- Meta Info --
        meta_row = f"<b>Date:</b> {self.receipt_data['created_at'][:10]} &nbsp;&nbsp;&nbsp; <b>Ref:</b> {self.receipt_data.get('receipt_number', '')}"
        story.append(Paragraph(meta_row, styleMeta))
        story.append(Paragraph("GAS BILL", styleBillTitle))
        story.append(Paragraph(f"<b>CUSTOMER NAME :</b> {self.receipt_data['client_name']}", styleLabel))
        story.append(Spacer(1, 8))
        items_data = [['DATE', 'PRODUCTS', 'QUANTITIES', 'DISCOUNT', 'SUBTOTAL', 'TAX', 'TOTAL']]
        for it in items:
            prod = f"{it['gas_type']}{(' ' + it['sub_type']) if it.get('sub_type') else ''} {it['capacity']}".strip()
            disc = max(0.0, float(it['quantity']) * float(it['unit_price']) - float(it['subtotal']))
            items_data.append([
                str(it['created_at'])[:10],
                prod,
                str(it['quantity']),
                f"{disc:,.2f}",
                f"{float(it['subtotal']):,.2f}",
                f"{float(it['tax_amount']):,.2f}",
                f"{float(it['total_amount']):,.2f}"
            ])
        items_table = Table(items_data, colWidths=[24*mm, 56*mm, 18*mm, 16*mm, 16*mm, 12*mm, 18*mm], hAlign='CENTER')
        items_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1.2, colors.black),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('FONTSIZE', (0, 1), (-1, -1), 11),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('BACKGROUND', (0, 0), (-1, 0), colors.white),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('TOPPADDING', (0, 1), (-1, -1), 4),
        ]))
        story.append(items_table)
        totals_data = [["", "", "", "TOTAL QTY", total_qty, "GRAND TOTAL", f"{self.receipt_data['total_amount']:,.2f}"]]
        totals_table = Table(totals_data, colWidths=[24*mm, 56*mm, 18*mm, 16*mm, 16*mm, 12*mm, 18*mm], hAlign='CENTER')
        totals_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1.4, colors.black),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(totals_table)
        story.append(Spacer(1, 14))
        labels = []
        if total_tax_val > 0:
            labels.append(['Tax', f"{total_tax_val:,.2f}"])
        if overall_discount_val > 0:
            labels.append(['Order Discount', f"{overall_discount_val:,.2f}"])
        labels.append(['Pending Bill', f"{self.receipt_data['balance']:,.2f}"])
        labels.append(['Total Bill', f"{self.receipt_data['total_amount']:,.2f}"])
        bill_table = Table(labels, colWidths=[32*mm, 40*mm], hAlign='CENTER')
        bill_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1.4, colors.black),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        story.append(bill_table)
        story.append(Spacer(1, 8))
        story.append(Paragraph('Signature________________', styleSignature))
        story.append(Spacer(1, 7))
        story.append(Paragraph('Plot No.69C-70C, Small Industrial Estate No.2, Gujranwala', styleFooter))
        doc.build(story)

class ReceiptsWidget(QWidget):
    def __init__(self, db_manager: DatabaseManager, current_user: dict):
        super().__init__()
        self.db_manager = db_manager
        self.current_user = current_user
        self.init_ui()
        self.load_receipts()
    
    def init_ui(self):
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
        layout.setSpacing(10)
        layout.setContentsMargins(12, 12, 12, 12)

        title_label = QLabel("Receipts")
        title_label.setObjectName("titleLabel")
        layout.addWidget(title_label)

        top_card = QFrame()
        top_card.setObjectName("sectionCard")
        top_layout = QHBoxLayout(top_card)
        top_layout.setSpacing(8)
        top_layout.setContentsMargins(10, 10, 10, 10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by receipt number or client name...")
        self.search_input.textChanged.connect(self.filter_receipts)
        top_layout.addWidget(self.search_input, 2)

        self.refresh_btn = self._create_small_button("Refresh", "primary")
        self.refresh_btn.clicked.connect(self.load_receipts)
        top_layout.addWidget(self.refresh_btn)

        self.generate_missing_btn = self._create_small_button("Generate Missing", "success")
        self.generate_missing_btn.clicked.connect(self.generate_missing_receipts)
        top_layout.addWidget(self.generate_missing_btn)

        layout.addWidget(top_card)

        table_card = QFrame()
        table_card.setObjectName("sectionCard")
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(10, 10, 10, 10)

        self.receipts_table = QTableWidget()
        self.receipts_table.setColumnCount(9)
        self.receipts_table.setHorizontalHeaderLabels([
            "Receipt #", "Date", "Client", "Products", "Quantities", "Total", "Paid", "Balance", "Actions"
        ])
        self._setup_receipts_table()
        table_layout.addWidget(self.receipts_table)
        layout.addWidget(table_card, 1)

        self.set_role_permissions()

    def _create_small_button(self, text: str, kind: str = "secondary") -> QPushButton:
        btn = QPushButton(text)
        btn.setMinimumWidth(70)
        btn.setFixedHeight(24)
        btn.setFocusPolicy(Qt.NoFocus)
        styles = {
            "primary": (
                "QPushButton { background-color: #1a73e8; color: white; border: 1px solid #125bc4; border-radius: 5px; padding: 4px 8px; font-size: 12px; font-weight: 600; }"
                "QPushButton:hover { background-color: #1765cb; }"
                "QPushButton:pressed { background-color: #125bc4; }"
            ),
            "success": (
                "QPushButton { background-color: #28a745; color: white; border: 1px solid #1f8a3a; border-radius: 5px; padding: 4px 8px; font-size: 12px; font-weight: 600; }"
                "QPushButton:hover { background-color: #228d3d; }"
                "QPushButton:pressed { background-color: #1f8a3a; }"
            ),
            "info": (
                "QPushButton { background-color: #17a2b8; color: white; border: 1px solid #138496; border-radius: 5px; padding: 4px 8px; font-size: 12px; font-weight: 600; }"
                "QPushButton:hover { background-color: #138496; }"
                "QPushButton:pressed { background-color: #117a8b; }"
            ),
            "warning": (
                "QPushButton { background-color: #f39c12; color: white; border: 1px solid #d68910; border-radius: 5px; padding: 4px 8px; font-size: 12px; font-weight: 600; }"
                "QPushButton:hover { background-color: #d68910; }"
                "QPushButton:pressed { background-color: #b9770e; }"
            ),
            "dark": (
                "QPushButton { background-color: #2c3e50; color: white; border: 1px solid #1f2d3a; border-radius: 5px; padding: 4px 8px; font-size: 12px; font-weight: 600; }"
                "QPushButton:hover { background-color: #1f2d3a; }"
                "QPushButton:pressed { background-color: #16222c; }"
            ),
            "secondary": (
                "QPushButton { background-color: #6c757d; color: white; border: 1px solid #596168; border-radius: 5px; padding: 4px 8px; font-size: 12px; font-weight: 600; }"
                "QPushButton:hover { background-color: #5e666d; }"
                "QPushButton:pressed { background-color: #535a61; }"
            ),
        }
        btn.setStyleSheet(styles.get(kind, styles["secondary"]))
        return btn

    def _setup_receipts_table(self):
        self.receipts_table.setAlternatingRowColors(True)
        self.receipts_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.receipts_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.receipts_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.receipts_table.setWordWrap(True)
        self.receipts_table.verticalHeader().setVisible(False)
        self.receipts_table.verticalHeader().setDefaultSectionSize(44)
        self.receipts_table.setMinimumHeight(360)

        header = self.receipts_table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.Fixed)

        self.receipts_table.setColumnWidth(8, 250)

    def _show_no_receipts_message(self):
        with table_batch_update(self.receipts_table):
            self.receipts_table.clearSpans()
            self.receipts_table.setRowCount(1)
            self.receipts_table.setItem(0, 0, QTableWidgetItem("No receipts found"))
            self.receipts_table.setSpan(0, 0, 1, 9)
            item = self.receipts_table.item(0, 0)
            item.setTextAlignment(Qt.AlignCenter)
            item.setForeground(Qt.gray)
    
    def set_role_permissions(self):
        """Set permissions based on user role"""
        role = self.current_user['role']
        
        if role == 'Driver':
            self.receipts_table.setEnabled(False)
            self.generate_missing_btn.setEnabled(False)
        elif role not in ['Admin', 'Accountant']:
            self.generate_missing_btn.setEnabled(False)
    
    def load_receipts(self):
        """Load all receipts from database"""
        try:
            receipts = self.db_manager.get_receipts_with_summaries(limit=100)
            
            if not receipts:
                self._show_no_receipts_message()
            else:
                self.populate_table(receipts)
            
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load receipts: {str(e)}")
    
    def generate_missing_receipts(self):
        """Generate receipts for sales that don't have receipts yet"""
        try:
            # Find sales without receipts
            query = '''
                SELECT s.*, c.name as client_name, c.phone as client_phone, c.company as client_company,
                       gp.gas_type, gp.sub_type, gp.capacity
                FROM sales s
                JOIN clients c ON s.client_id = c.id
                JOIN gas_products gp ON s.gas_product_id = gp.id
                WHERE s.id NOT IN (SELECT sale_id FROM receipts)
                ORDER BY s.created_at DESC
            '''
            sales_without_receipts = self.db_manager.execute_query(query)
            
            if not sales_without_receipts:
                QMessageBox.information(self, "Info", "All sales already have receipts.")
                return
            
            # Generate receipts for these sales
            generated_count = 0
            for sale in sales_without_receipts:
                try:
                    from PySide6.QtWidgets import QInputDialog
                    # Ask for amount paid for this sale
                    initial_paid = float(sale['amount_paid']) if sale['amount_paid'] is not None else 0.0
                    amount_paid, ok = QInputDialog.getDouble(
                        self,
                        "Record Payment",
                        f"Enter amount paid for sale #{sale['id']} (client: {sale['client_name']}):",
                        initial_paid,
                        0.0,
                        float(sale['total_amount']),
                        2
                    )
                    if not ok:
                        continue
                    # Update sale payment
                    self.db_manager.update_sale_payment(sale['id'], amount_paid)
                    balance = float(sale['total_amount']) - amount_paid
                    receipt_number = self.db_manager.get_next_receipt_number()
                    self.db_manager.create_receipt(
                        receipt_number=receipt_number,
                        sale_id=sale['id'],
                        client_id=sale['client_id'],
                        total_amount=sale['total_amount'],
                        amount_paid=amount_paid,
                        balance=balance,
                        created_by=self.current_user['id']
                    )
                    generated_count += 1
                except Exception as e:
                    print(f"Error generating receipt for sale {sale['id']}: {str(e)}")
                    continue
            
            QMessageBox.information(self, "Success", f"Generated {generated_count} missing receipts.")
            self.load_receipts()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate missing receipts: {str(e)}")
    
    def populate_table(self, receipts):
        """Populate table with receipt data"""
        with table_batch_update(self.receipts_table):
            self.receipts_table.clearSpans()
            self.receipts_table.setRowCount(len(receipts))

            for row, receipt in enumerate(receipts):
                self.receipts_table.setItem(row, 0, QTableWidgetItem(as_text(receipt.get('receipt_number'))))
                self.receipts_table.setItem(row, 1, QTableWidgetItem(as_datetime_text(receipt.get('created_at'), 16)))

                client_text = as_text(receipt.get('client_name'))
                if receipt.get('client_company'):
                    client_text += f" ({receipt['client_company']})"
                self.receipts_table.setItem(row, 2, QTableWidgetItem(client_text))

                product_text = as_text(receipt.get('product_summary') or '')
                self.receipts_table.setItem(row, 3, QTableWidgetItem(product_text))

                quantities_text = as_text(receipt.get('quantities_summary') or receipt.get('quantity') or '')
                self.receipts_table.setItem(row, 4, QTableWidgetItem(quantities_text))

                total_item = QTableWidgetItem(as_money(receipt.get('total_amount')))
                total_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.receipts_table.setItem(row, 5, total_item)

                paid_item = QTableWidgetItem(as_money(receipt.get('amount_paid')))
                paid_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.receipts_table.setItem(row, 6, paid_item)

                balance_value = float(receipt.get('balance') or 0)
                balance_item = QTableWidgetItem(as_money(balance_value))
                balance_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if balance_value > 0:
                    balance_item.setForeground(Qt.red)
                elif balance_value < 0:
                    balance_item.setForeground(Qt.darkYellow)
                else:
                    balance_item.setForeground(Qt.darkGreen)
                self.receipts_table.setItem(row, 7, balance_item)
            
                actions_widget = QWidget()
                actions_widget.setMinimumHeight(34)
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setSpacing(4)
                actions_layout.setContentsMargins(2, 2, 2, 2)
                actions_layout.setAlignment(Qt.AlignCenter)
            
                view_btn = self._create_small_button("View", "info")
                view_btn.setMinimumWidth(62)
                view_btn.clicked.connect(lambda checked, r=receipt: self.view_receipt(r))
                actions_layout.addWidget(view_btn)

                print_btn = self._create_small_button("Print", "warning")
                print_btn.setMinimumWidth(62)
                print_btn.clicked.connect(lambda checked, r=receipt: self.print_receipt(r))
                actions_layout.addWidget(print_btn)

                export_btn = self._create_small_button("Export", "dark")
                export_btn.setMinimumWidth(66)
                export_btn.clicked.connect(lambda checked, r=receipt: self.export_receipt_pdf(r))
                actions_layout.addWidget(export_btn)

                self.receipts_table.setCellWidget(row, 8, actions_widget)
                self.receipts_table.setRowHeight(row, 44)
    
    def filter_receipts(self):
        """Filter receipts based on search input"""
        search_text = self.search_input.text().strip().lower()
        
        try:
            receipts = self.db_manager.get_receipts_with_summaries(limit=100, search=search_text if search_text else None)
            if receipts:
                self.populate_table(receipts)
            else:
                self._show_no_receipts_message()
            
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to filter receipts: {str(e)}")
    
    def view_receipt(self, receipt_data: dict):
        """View receipt details"""
        # Get additional receipt details
        try:
            query = '''
                SELECT r.*, c.name as client_name, c.phone as client_phone, c.company as client_company,
                       u.full_name as cashier_name, gp.gas_type, gp.sub_type, gp.capacity, 
                       s.quantity, s.unit_price, s.subtotal, s.tax_amount, s.total_amount,
                       r.amount_paid, r.balance
                FROM receipts r
                JOIN clients c ON r.client_id = c.id
                JOIN users u ON r.created_by = u.id
                JOIN sales s ON r.sale_id = s.id
                JOIN gas_products gp ON s.gas_product_id = gp.id
                WHERE r.id = ?
            '''
            result = self.db_manager.execute_query(query, (receipt_data['id'],))
            
            if result:
                full_receipt_data = result[0]
                dialog = ReceiptDialog(self.db_manager, full_receipt_data, self)
                dialog.exec()
            else:
                QMessageBox.warning(self, "Not Found", "Receipt details not found.")
                
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load receipt details: {str(e)}")
    
    def print_receipt(self, receipt_data: dict):
        """Print receipt"""
        try:
            query = '''
                SELECT r.*, c.name as client_name, c.phone as client_phone, c.company as client_company,
                       u.full_name as cashier_name, gp.gas_type, gp.sub_type, gp.capacity,
                       s.quantity, s.unit_price, s.subtotal, s.tax_amount, s.total_amount,
                       r.amount_paid, r.balance
                FROM receipts r
                JOIN clients c ON r.client_id = c.id
                JOIN users u ON r.created_by = u.id
                JOIN sales s ON r.sale_id = s.id
                JOIN gas_products gp ON s.gas_product_id = gp.id
                WHERE r.id = ?
            '''
            result = self.db_manager.execute_query(query, (receipt_data['id'],))
            if not result:
                QMessageBox.warning(self, "Not Found", "Receipt details not found.")
                return
            dialog = ReceiptDialog(self.db_manager, result[0], self)
            dialog.print_receipt()
        except Exception as e:
            QMessageBox.critical(self, "Print Error", f"Failed to print receipt: {str(e)}")
    
    def export_receipt_pdf(self, receipt_data: dict):
        """Export receipt as PDF"""
        from PySide6.QtWidgets import QFileDialog

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Receipt as PDF",
            f"Receipt_{receipt_data['receipt_number']}.pdf",
            "PDF Files (*.pdf)"
        )

        if filename:
            if not filename.lower().endswith('.pdf'):
                filename += '.pdf'
            try:
                query = '''
                    SELECT r.*, c.name as client_name, c.phone as client_phone, c.company as client_company,
                           u.full_name as cashier_name, gp.gas_type, gp.sub_type, gp.capacity,
                           s.quantity, s.unit_price, s.subtotal, s.tax_amount, s.total_amount
                    FROM receipts r
                    JOIN clients c ON r.client_id = c.id
                    JOIN users u ON r.created_by = u.id
                    JOIN sales s ON r.sale_id = s.id
                    JOIN gas_products gp ON s.gas_product_id = gp.id
                    WHERE r.id = ?
                '''
                result = self.db_manager.execute_query(query, (receipt_data['id'],))

                if result:
                    full_receipt_data = result[0]
                    dialog = ReceiptDialog(self.db_manager, full_receipt_data, self)
                    dialog.generate_pdf_receipt(filename)
                    QMessageBox.information(self, "Success", f"Receipt exported to {filename}")
                else:
                    QMessageBox.warning(self, "Not Found", "Receipt details not found.")

            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export PDF: {str(e)}")
