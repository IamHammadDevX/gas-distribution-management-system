from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                               QTableWidgetItem, QPushButton, QLineEdit, QLabel, 
                               QMessageBox, QDialog, QFormLayout, QDialogButtonBox,
                               QTextEdit, QHeaderView, QGroupBox, QGridLayout)
from PySide6.QtCore import Qt, QDateTime
from PySide6.QtPrintSupport import QPrinter, QPrintDialog
from PySide6.QtGui import QTextDocument
from PySide6.QtCore import QSizeF
from PySide6.QtGui import QPageSize, QPageLayout
from PySide6.QtPrintSupport import QPrinter, QPrintDialog
from database_module import DatabaseManager
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
        self.setFixedSize(520, 680)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        preview = QTextEdit()
        preview.setReadOnly(True)
        preview.setStyleSheet("font-size: 12px;")
        preview.setHtml(self.generate_receipt_html())
        layout.addWidget(preview)
        
        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        print_btn = QPushButton("Print")
        print_btn.clicked.connect(self.print_receipt)
        button_layout.addWidget(print_btn)
        
        export_btn = QPushButton("Export PDF")
        export_btn.clicked.connect(self.export_pdf)
        button_layout.addWidget(export_btn)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def print_receipt(self):
        """Print the receipt (A4, small logo, fit content)"""
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
            doc.setPageSize(QSizeF(650, 900))  # Equivalent to usable A4, after margins
            doc.print_(printer)
    
    def export_pdf(self):
        """Export receipt as PDF"""
        from PySide6.QtWidgets import QFileDialog
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Receipt as PDF",
            f"Receipt_{self.receipt_data['receipt_number']}.pdf",
            "PDF Files (*.pdf)"
        )
        
        if filename:
            try:
                self.generate_pdf_receipt(filename)
                QMessageBox.information(self, "Success", f"Receipt exported to {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export PDF: {str(e)}")
    
    def generate_receipt_html(self, for_print: bool = False) -> str:
        logo_path = "logo.png"
        items = self.db_manager.get_sale_items(self.receipt_data['sale_id'])
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
        style_a4_fit = """
body { font-family: Arial, sans-serif; color: #000; background: #fff; margin: 0; }
.receipt { 
    max-width: 650px; 
    min-width: 650px;
    margin: 0 auto; 
    padding: 24px 35px; 
    border: 2px solid #000; 
    border-radius: 12px;
    background: #fff;
}
.header { 
    border-bottom: 2px solid #333; 
    padding: 6px 0 8px 0; 
    margin-bottom: 10px;
    display: grid;
    grid-template-columns: 160px 1fr;
    align-items: center;
}
.logo { width: 48px; height: 48px; border-radius: 50%; border: 1.5px solid #444; object-fit: cover; margin-right: 0; justify-self: start; }
.header-content { display: inline-block; text-align: center; }
.store-title { font-weight: 900; font-size: 28px; margin-bottom:2px; text-align: center;}
.info { font-size: 13px; margin-top: 3px; text-align: center;}
.meta-row { font-size: 13px; margin-top:6px; display:flex; justify-content:center; text-align:center; }
.meta-row .label {font-weight: bold;}
.title { text-align: center; font-size: 18px; font-weight: 700; margin: 14px 0 7px 0; text-decoration: underline;}
.customer { font-size: 15px; margin: 8px 0 8px 0; text-align: center; }
.tbl { width: 100%; border-collapse: collapse; margin: 8px auto 6px auto; font-size: 13px; background: #fff;}
.tbl th, .tbl td { border: 1px solid #344; padding: 5px 3px; text-align: center; font-size: 13px;}
.totals { font-size: 14px; font-weight: 700; text-align: center; margin-top: 4px;}
.bill-box { margin-top: 8px; }
.box-label { font-weight:700; margin-right: 6px;}
.bill-table { width: 100%; margin: 0 auto 6px auto;}
.bill-table td { border: 1.5px solid #000; font-size: 15px; font-weight:700; padding: 4px 11px; text-align:center;}
.footer { font-size: 13px; font-weight:600; text-align: center; border-top: 2px solid #444; padding-top: 9px; margin-top: 10px;}
.signature { text-align:center; font-size:15px; font-style:italic; margin-top:13px;}
        """
        style = style_a4_fit
        rows_parts = []
        if for_print:
            for it in items:
                prod = f"{it['gas_type']}{(' ' + it['sub_type']) if it.get('sub_type') else ''} {it['capacity']}".strip()
                disc = max(0.0, float(it['quantity']) * float(it['unit_price']) - float(it['subtotal']))
                rows_parts.append(
                    f"<tr><td>{str(it['created_at'])[:10]}</td><td>{prod}</td><td>{it['quantity']}</td><td>{disc:,.2f}</td><td>{float(it['subtotal']):,.2f}</td><td>{float(it['tax_amount']):,.2f}</td><td>{float(it['total_amount']):,.2f}</td></tr>"
                )
        else:
            summaries = self.db_manager.get_sale_item_summaries(self.receipt_data['sale_id'])
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
        # HTML structure: logo is small and inline, everything fits
        return f"""
<html>
<head>
<style>{style}</style>
</head>
<body>
<div class="receipt"> 
  <div class="header">
    <img src="{logo_path}" class="logo" alt="Logo" width="48" height="48"/>
    <div class="header-content">
      <div class="store-title">RAJPUT GAS TRADERS</div>
      <div class="info">Prop: Saleem Ahmad | 0301-6465144</div>
      <div class="info">Date: {self.receipt_data['created_at'][:10]} &nbsp;&nbsp; Ref: {self.receipt_data.get('receipt_number','')}</div>
    </div>
  </div>
  <div class="title">GAS BILL</div>
  <div class="customer"><b>CUSTOMER NAME :</b> {self.receipt_data['client_name']}</div>
  <table class="tbl">
{('<tr><th>DATE</th><th>PRODUCTS</th><th>QUA</th><th>DISC</th><th>SUB-T</th><th>TAX</th><th>TOTAL</th></tr>' if for_print else '<tr><th>DATE</th><th>PRODUCTS</th><th>QUA</th><th>SUB-T</th><th>TAX</th><th>TOTAL</th></tr>')}
{rows_html}
<tr style="font-weight:bold; background:#fff;">
{('<td colspan="4" style="text-align:right;">TOTAL QTY</td><td>' + str(total_qty) + '</td><td style="text-align:right;">GRAND TOTAL</td><td>' + f"{float(self.receipt_data['total_amount']):,.2f}" + '</td>' if for_print else '<td colspan="3" style="text-align:right;">TOTAL QTY</td><td>' + str(total_qty) + '</td><td style="text-align:right;">GRAND TOTAL</td><td>' + f"{float(self.receipt_data['total_amount']):,.0f}" + '</td>' )}
</tr>
</table>
  <div class="bill-box">
    <table class="bill-table">
        {bill_extra_rows}
        <tr>
            <td class="box-label">Pending Bill</td>
            <td>{self.receipt_data['balance']:,.2f}</td>
        </tr>
        <tr>
            <td class="box-label">Total Bill</td>
            <td>{float(self.receipt_data['total_amount']):,.2f}</td>
        </tr>
    </table>
  </div>
  <div class="signature">Signature________________</div>
  <div class="footer">Plot No.69C-70C, Small Industrial Estate No.2, Gujranwala</div>
</div>
</body>
</html>
        """

    def generate_pdf_receipt(self, filename: str):
        logo_path = "logo.png" # update as needed
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
        logo_path = "logo.png"  # Update as needed; must be in your project root or use correct path
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
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title_label = QLabel("Receipts")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title_label)
        
        # Search and controls
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(10)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by receipt number or client name...")
        self.search_input.textChanged.connect(self.filter_receipts)
        controls_layout.addWidget(self.search_input)
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.load_receipts)
        controls_layout.addWidget(self.refresh_btn)
        
        self.generate_missing_btn = QPushButton("Generate Missing Receipts")
        self.generate_missing_btn.clicked.connect(self.generate_missing_receipts)
        self.generate_missing_btn.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")
        controls_layout.addWidget(self.generate_missing_btn)
        
        layout.addLayout(controls_layout)
        
        # Receipts table
        self.receipts_table = QTableWidget()
        self.receipts_table.setColumnCount(9)
        self.receipts_table.setHorizontalHeaderLabels([
            "Receipt #", "Date", "Client", "Products", "Quantities", "Total", "Paid", "Balance", "Actions"
        ])
        self.receipts_table.setAlternatingRowColors(True)
        self.receipts_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.receipts_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.receipts_table.horizontalHeader().setStretchLastSection(True)
        self.receipts_table.setColumnWidth(0, 120)
        self.receipts_table.setColumnWidth(1, 140)
        self.receipts_table.setColumnWidth(2, 180)
        self.receipts_table.setColumnWidth(3, 200)
        self.receipts_table.setColumnWidth(4, 90)
        self.receipts_table.setColumnWidth(5, 120)
        self.receipts_table.setColumnWidth(6, 120)
        self.receipts_table.setColumnWidth(7, 120)
        self.receipts_table.setColumnWidth(8, 160)
        layout.addWidget(self.receipts_table)

        self.set_role_permissions()
    
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
                # Show a message when no receipts exist
                self.receipts_table.setRowCount(1)
                self.receipts_table.setItem(0, 0, QTableWidgetItem("No receipts found"))
                self.receipts_table.setSpan(0, 0, 1, 9)  # Span across all columns
                self.receipts_table.item(0, 0).setTextAlignment(Qt.AlignCenter)
                self.receipts_table.item(0, 0).setForeground(Qt.gray)
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
        self.receipts_table.setRowCount(len(receipts))
        
        for row, receipt in enumerate(receipts):
            # Receipt Number
            self.receipts_table.setItem(row, 0, QTableWidgetItem(receipt['receipt_number']))
            
            # Date
            self.receipts_table.setItem(row, 1, QTableWidgetItem(receipt['created_at'][:16]))
            
            # Client
            client_text = receipt['client_name']
            if receipt['client_company']:
                client_text += f" ({receipt['client_company']})"
            self.receipts_table.setItem(row, 2, QTableWidgetItem(client_text))
            
            # Products
            product_text = receipt.get('product_summary') or ''
            self.receipts_table.setItem(row, 3, QTableWidgetItem(product_text))
            
            # Quantities
            quantities_text = receipt.get('quantities_summary') or str(receipt.get('quantity') or '')
            self.receipts_table.setItem(row, 4, QTableWidgetItem(quantities_text))
            
            # Total
            total_item = QTableWidgetItem(f"Rs. {receipt['total_amount']:,.2f}")
            total_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.receipts_table.setItem(row, 5, total_item)
            
            # Paid
            paid_item = QTableWidgetItem(f"Rs. {receipt['amount_paid']:,.2f}")
            paid_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.receipts_table.setItem(row, 6, paid_item)
            
            # Balance
            balance_item = QTableWidgetItem(f"Rs. {receipt['balance']:,.2f}")
            balance_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if receipt['balance'] > 0:
                balance_item.setForeground(Qt.red)
            elif receipt['balance'] < 0:
                balance_item.setForeground(Qt.darkYellow)
            else:
                balance_item.setForeground(Qt.darkGreen)
            self.receipts_table.setItem(row, 7, balance_item)
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setSpacing(5)
            actions_layout.setContentsMargins(5, 5, 5, 5)
            
            view_btn = QPushButton("View")
            view_btn.setStyleSheet("""
                QPushButton { background-color: #17a2b8; color: white; border: 1px solid #138496; border-radius: 6px; padding: 6px 12px; font-size: 13px; font-weight: 600; }
                QPushButton:hover { background-color: #138496; }
                QPushButton:pressed { background-color: #117a8b; }
            """)
            view_btn.setMinimumWidth(96)
            view_btn.setFixedHeight(32)
            view_btn.clicked.connect(lambda checked, r=receipt: self.view_receipt(r))
            actions_layout.addWidget(view_btn)

            print_btn = QPushButton("Print")
            print_btn.setStyleSheet("""
                QPushButton { background-color: #f39c12; color: white; border: 1px solid #d68910; border-radius: 6px; padding: 6px 12px; font-size: 13px; font-weight: 600; }
                QPushButton:hover { background-color: #d68910; }
                QPushButton:pressed { background-color: #b9770e; }
            """)
            print_btn.setMinimumWidth(96)
            print_btn.setFixedHeight(32)
            print_btn.clicked.connect(lambda checked, r=receipt: self.print_receipt(r))
            actions_layout.addWidget(print_btn)

            export_btn = QPushButton("Export PDF")
            export_btn.setStyleSheet("""
                QPushButton { background-color: #2c3e50; color: white; border: 1px solid #1f2d3a; border-radius: 6px; padding: 6px 12px; font-size: 13px; font-weight: 600; }
                QPushButton:hover { background-color: #1f2d3a; }
                QPushButton:pressed { background-color: #16222c; }
            """)
            export_btn.setMinimumWidth(110)
            export_btn.setFixedHeight(32)
            export_btn.clicked.connect(lambda checked, r=receipt: self.export_receipt_pdf(r))
            actions_layout.addWidget(export_btn)
            
            self.receipts_table.setCellWidget(row, 8, actions_widget)
    
    def filter_receipts(self):
        """Filter receipts based on search input"""
        search_text = self.search_input.text().strip().lower()
        
        try:
            receipts = self.db_manager.get_receipts_with_summaries(limit=100, search=search_text if search_text else None)
            self.populate_table(receipts)
            
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
        self.view_receipt(receipt_data)
    
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
            try:
                # Get full receipt data
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
