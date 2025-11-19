from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                               QTableWidgetItem, QPushButton, QLineEdit, QLabel, 
                               QMessageBox, QDialog, QFormLayout, QDialogButtonBox,
                               QTextEdit, QHeaderView, QGroupBox, QGridLayout)
from PySide6.QtCore import Qt, QDateTime
from PySide6.QtPrintSupport import QPrinter, QPrintDialog
from database_module import DatabaseManager
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import os

class ReceiptDialog(QDialog):
    def __init__(self, db_manager: DatabaseManager, receipt_data: dict, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.receipt_data = receipt_data
        self.setWindowTitle(f"Receipt - {receipt_data['receipt_number']}")
        self.setFixedSize(600, 700)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header_label = QLabel("RECEIPT")
        header_label.setAlignment(Qt.AlignCenter)
        header_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(header_label)
        
        # Company info
        company_info = QLabel("""
<b>Rajput Gas Ltd.</b><br>
Industrial Area, Phase 2<br>
Phone: +92-42-1234567<br>
Email: info@rajputgas.com
        """)
        company_info.setAlignment(Qt.AlignCenter)
        layout.addWidget(company_info)
        
        # Receipt details
        details_text = f"""
<b>Receipt Number:</b> {self.receipt_data['receipt_number']}<br>
<b>Date:</b> {self.receipt_data['created_at']}<br>
<b>Client:</b> {self.receipt_data['client_name']}<br>
<b>Phone:</b> {self.receipt_data['client_phone']}<br>
<b>Company:</b> {self.receipt_data['client_company'] or 'N/A'}<br>
        """
        
        details_edit = QTextEdit()
        details_edit.setHtml(details_text)
        details_edit.setReadOnly(True)
        details_edit.setMaximumHeight(120)
        layout.addWidget(details_edit)
        
        # Items table
        items_label = QLabel("<b>Items:</b>")
        layout.addWidget(items_label)
        
        items_table = QTableWidget()
        items_table.setColumnCount(6)
        items_table.setHorizontalHeaderLabels([
            "Gas Type", "Capacity", "Quantity", "Unit Price", "Subtotal", "Total"
        ])
        items_table.setAlternatingRowColors(True)
        items_table.setEditTriggers(QTableWidget.NoEditTriggers)
        items_table.setMaximumHeight(150)
        
        # Add item data
        items_table.setRowCount(1)
        items_table.setItem(0, 0, QTableWidgetItem(self.receipt_data['gas_type']))
        items_table.setItem(0, 1, QTableWidgetItem(self.receipt_data['capacity']))
        items_table.setItem(0, 2, QTableWidgetItem(str(self.receipt_data['quantity'])))
        items_table.setItem(0, 3, QTableWidgetItem(f"Rs. {self.receipt_data['unit_price']:,.2f}"))
        items_table.setItem(0, 4, QTableWidgetItem(f"Rs. {self.receipt_data['subtotal']:,.2f}"))
        items_table.setItem(0, 5, QTableWidgetItem(f"Rs. {self.receipt_data['total_amount']:,.2f}"))
        
        items_table.resizeColumnsToContents()
        layout.addWidget(items_table)
        
        # Totals
        totals_text = f"""
<b>Subtotal:</b> Rs. {self.receipt_data['subtotal']:,.2f}<br>
<b>Tax (16%):</b> Rs. {self.receipt_data['tax_amount']:,.2f}<br>
<b>Total Amount:</b> Rs. {self.receipt_data['total_amount']:,.2f}<br>
<b>Amount Paid:</b> Rs. {self.receipt_data['amount_paid']:,.2f}<br>
<b>Balance:</b> Rs. {self.receipt_data['balance']:,.2f}<br>
        """
        
        totals_edit = QTextEdit()
        totals_edit.setHtml(totals_text)
        totals_edit.setReadOnly(True)
        totals_edit.setMaximumHeight(100)
        layout.addWidget(totals_edit)
        
        # Footer
        footer_text = f"""
<b>Cashier:</b> {self.receipt_data['cashier_name']}<br>
<b>Payment Method:</b> Cash<br>
<br>
<b>Terms & Conditions:</b><br>
1. Goods once sold cannot be returned.<br>
2. Please keep this receipt for your records.<br>
3. Outstanding balance must be cleared within 30 days.<br>
<br>
<b>Thank you for your business!</b>
        """
        
        footer_edit = QTextEdit()
        footer_edit.setHtml(footer_text)
        footer_edit.setReadOnly(True)
        footer_edit.setMaximumHeight(150)
        layout.addWidget(footer_edit)
        
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
        """Print the receipt"""
        printer = QPrinter(QPrinter.HighResolution)
        dialog = QPrintDialog(printer, self)
        
        if dialog.exec() == QDialog.Accepted:
            # Create a QTextDocument for printing
            from PySide6.QtGui import QTextDocument
            
            doc = QTextDocument()
            html_content = self.generate_receipt_html()
            doc.setHtml(html_content)
            doc.print(printer)
    
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
    
    def generate_receipt_html(self) -> str:
        """Generate HTML content for receipt"""
        return f"""
<html>
<head>
<style>
body {{ font-family: Arial, sans-serif; margin: 20px; }}
.header {{ text-align: center; margin-bottom: 20px; }}
.details {{ margin-bottom: 20px; }}
table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
th, td {{ padding: 8px; text-align: left; border: 1px solid #ddd; }}
th {{ background-color: #f2f2f2; }}
.totals {{ text-align: right; margin-bottom: 20px; }}
.footer {{ margin-top: 30px; font-size: 12px; }}
</style>
</head>
<body>
<div class="header">
<h1>RECEIPT</h1>
<h2>Rajput Gas Ltd.</h2>
<p>Industrial Area, Phase 2<br>
Phone: +92-42-1234567<br>
Email: info@rajputgas.com</p>
</div>

<div class="details">
<p><b>Receipt Number:</b> {self.receipt_data['receipt_number']}</p>
<p><b>Date:</b> {self.receipt_data['created_at']}</p>
<p><b>Client:</b> {self.receipt_data['client_name']}</p>
<p><b>Phone:</b> {self.receipt_data['client_phone']}</p>
<p><b>Company:</b> {self.receipt_data['client_company'] or 'N/A'}</p>
</div>

<table>
<tr>
<th>Gas Type</th>
<th>Capacity</th>
<th>Quantity</th>
<th>Unit Price</th>
<th>Subtotal</th>
<th>Total</th>
</tr>
<tr>
<td>{self.receipt_data['gas_type']}</td>
<td>{self.receipt_data['capacity']}</td>
<td>{self.receipt_data['quantity']}</td>
<td>Rs. {self.receipt_data['unit_price']:,.2f}</td>
<td>Rs. {self.receipt_data['subtotal']:,.2f}</td>
<td>Rs. {self.receipt_data['total_amount']:,.2f}</td>
</tr>
</table>

<div class="totals">
<p><b>Subtotal:</b> Rs. {self.receipt_data['subtotal']:,.2f}</p>
<p><b>Tax (16%):</b> Rs. {self.receipt_data['tax_amount']:,.2f}</p>
<p><b>Total Amount:</b> Rs. {self.receipt_data['total_amount']:,.2f}</p>
<p><b>Amount Paid:</b> Rs. {self.receipt_data['amount_paid']:,.2f}</p>
<p><b>Balance:</b> Rs. {self.receipt_data['balance']:,.2f}</p>
</div>

<div class="footer">
<p><b>Cashier:</b> {self.receipt_data['cashier_name']}</p>
<p><b>Payment Method:</b> Cash</p>
<p><b>Terms & Conditions:</b><br>
1. Goods once sold cannot be returned.<br>
2. Please keep this receipt for your records.<br>
3. Outstanding balance must be cleared within 30 days.</p>
<p><b>Thank you for your business!</b></p>
</div>
</body>
</html>
        """
    
    def generate_pdf_receipt(self, filename: str):
        """Generate PDF receipt using ReportLab"""
        doc = SimpleDocTemplate(filename, pagesize=A4)
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        
        company_style = ParagraphStyle(
            'CompanyStyle',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=20,
            alignment=1  # Center alignment
        )
        
        # Build PDF content
        story = []
        
        # Header
        story.append(Paragraph("RECEIPT", title_style))
        story.append(Paragraph("<b>Rajput Gas Ltd.</b>", company_style))
        story.append(Paragraph("Industrial Area, Phase 2<br/>Phone: +92-42-1234567<br/>Email: info@rajputgas.com", company_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Receipt details
        details_data = [
            ["Receipt Number:", self.receipt_data['receipt_number']],
            ["Date:", self.receipt_data['created_at']],
            ["Client:", self.receipt_data['client_name']],
            ["Phone:", self.receipt_data['client_phone']],
            ["Company:", self.receipt_data['client_company'] or 'N/A']
        ]
        
        details_table = Table(details_data, colWidths=[2*inch, 3*inch])
        details_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(details_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Items table
        story.append(Paragraph("<b>Items:</b>", styles['Heading3']))
        
        items_data = [
            ["Gas Type", "Capacity", "Quantity", "Unit Price", "Subtotal", "Total"],
            [
                self.receipt_data['gas_type'],
                self.receipt_data['capacity'],
                str(self.receipt_data['quantity']),
                f"Rs. {self.receipt_data['unit_price']:,.2f}",
                f"Rs. {self.receipt_data['subtotal']:,.2f}",
                f"Rs. {self.receipt_data['total_amount']:,.2f}"
            ]
        ]
        
        items_table = Table(items_data, colWidths=[1*inch, 1*inch, 0.8*inch, 1*inch, 1*inch, 1*inch])
        items_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ]))
        
        story.append(items_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Totals
        totals_data = [
            ["Subtotal:", f"Rs. {self.receipt_data['subtotal']:,.2f}"],
            ["Tax (16%):", f"Rs. {self.receipt_data['tax_amount']:,.2f}"],
            ["Total Amount:", f"Rs. {self.receipt_data['total_amount']:,.2f}"],
            ["Amount Paid:", f"Rs. {self.receipt_data['amount_paid']:,.2f}"],
            ["Balance:", f"Rs. {self.receipt_data['balance']:,.2f}"]
        ]
        
        totals_table = Table(totals_data, colWidths=[3*inch, 2*inch])
        totals_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 2), (1, 2), 'Helvetica-Bold'),
            ('FONTNAME', (0, 4), (1, 4), 'Helvetica-Bold'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        story.append(totals_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Footer
        footer_data = [
            ["Cashier:", self.receipt_data['cashier_name']],
            ["Payment Method:", "Cash"],
            ["", ""],
            ["Terms & Conditions:", ""],
            ["", "1. Goods once sold cannot be returned."],
            ["", "2. Please keep this receipt for your records."],
            ["", "3. Outstanding balance must be cleared within 30 days."],
            ["", ""],
            ["", "Thank you for your business!"]
        ]
        
        footer_table = Table(footer_data, colWidths=[1.5*inch, 3.5*inch])
        footer_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 3), (0, 3), 'Helvetica-Bold'),
            ('FONTNAME', (0, 8), (1, 8), 'Helvetica-Bold'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
        ]))
        
        story.append(footer_table)
        
        # Build PDF
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
            "Receipt #", "Date", "Client", "Product", "Quantity", "Total", "Paid", "Balance", "Actions"
        ])
        
        # Configure table
        self.receipts_table.setAlternatingRowColors(True)
        self.receipts_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.receipts_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.receipts_table.horizontalHeader().setStretchLastSection(True)
        self.receipts_table.setColumnWidth(0, 120)  # Receipt #
        self.receipts_table.setColumnWidth(1, 140)  # Date
        self.receipts_table.setColumnWidth(2, 150)  # Client
        self.receipts_table.setColumnWidth(3, 150)  # Product
        self.receipts_table.setColumnWidth(4, 80)   # Quantity
        self.receipts_table.setColumnWidth(5, 100)  # Total
        self.receipts_table.setColumnWidth(6, 100)  # Paid
        self.receipts_table.setColumnWidth(7, 100)  # Balance
        self.receipts_table.setColumnWidth(8, 200)  # Actions
        
        layout.addWidget(self.receipts_table)
        
        # Set role-based permissions
        self.set_role_permissions()
    
    def set_role_permissions(self):
        """Set permissions based on user role"""
        role = self.current_user['role']
        
        if role == 'Driver':
            self.receipts_table.setEnabled(False)
    
    def load_receipts(self):
        """Load all receipts from database"""
        try:
            query = '''
                SELECT r.*, c.name as client_name, c.phone as client_phone, c.company as client_company,
                       gp.gas_type, gp.sub_type, gp.capacity, s.quantity, s.unit_price, 
                       s.subtotal, s.tax_amount, s.total_amount
                FROM receipts r
                JOIN clients c ON r.client_id = c.id
                JOIN sales s ON r.sale_id = s.id
                JOIN gas_products gp ON s.gas_product_id = gp.id
                ORDER BY r.created_at DESC
                LIMIT 100
            '''
            receipts = self.db_manager.execute_query(query)
            
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
                    receipt_number = self.db_manager.get_next_receipt_number()
                    self.db_manager.create_receipt(
                        receipt_number=receipt_number,
                        sale_id=sale['id'],
                        client_id=sale['client_id'],
                        total_amount=sale['total_amount'],
                        amount_paid=sale['amount_paid'],
                        balance=sale['balance'],
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
            
            # Product
            product_text = f"{receipt['gas_type']}"
            if receipt['sub_type']:
                product_text += f" - {receipt['sub_type']}"
            product_text += f" - {receipt['capacity']}"
            self.receipts_table.setItem(row, 3, QTableWidgetItem(product_text))
            
            # Quantity
            self.receipts_table.setItem(row, 4, QTableWidgetItem(str(receipt['quantity'])))
            
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
            view_btn.clicked.connect(lambda checked, r=receipt: self.view_receipt(r))
            actions_layout.addWidget(view_btn)
            
            print_btn = QPushButton("Print")
            print_btn.clicked.connect(lambda checked, r=receipt: self.print_receipt(r))
            actions_layout.addWidget(print_btn)
            
            export_btn = QPushButton("Export PDF")
            export_btn.clicked.connect(lambda checked, r=receipt: self.export_receipt_pdf(r))
            actions_layout.addWidget(export_btn)
            
            self.receipts_table.setCellWidget(row, 8, actions_widget)
    
    def filter_receipts(self):
        """Filter receipts based on search input"""
        search_text = self.search_input.text().strip().lower()
        
        try:
            query = '''
                SELECT r.*, c.name as client_name, c.phone as client_phone, c.company as client_company,
                       gp.gas_type, gp.sub_type, gp.capacity, s.quantity, s.unit_price, 
                       s.subtotal, s.tax_amount, s.total_amount
                FROM receipts r
                JOIN clients c ON r.client_id = c.id
                JOIN sales s ON r.sale_id = s.id
                JOIN gas_products gp ON s.gas_product_id = gp.id
                WHERE LOWER(r.receipt_number) LIKE ? OR LOWER(c.name) LIKE ?
                ORDER BY r.created_at DESC
                LIMIT 100
            '''
            search_pattern = f"%{search_text}%"
            receipts = self.db_manager.execute_query(query, (search_pattern, search_pattern))
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