from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                               QTableWidgetItem, QPushButton, QLineEdit, QLabel, 
                               QMessageBox, QDialog, QFormLayout, QDialogButtonBox,
                               QComboBox, QSpinBox, QDoubleSpinBox, QGroupBox,
                               QTextEdit, QHeaderView, QGridLayout, QInputDialog)
from PySide6.QtCore import Qt, QDateTime
from database_module import DatabaseManager
from datetime import datetime

class SalesWidget(QWidget):
    def __init__(self, db_manager: DatabaseManager, current_user: dict):
        super().__init__()
        self.db_manager = db_manager
        self.current_user = current_user
        self.current_client = None
        self.current_products = []
        self.init_ui()
        self.load_gas_products()
        self.load_recent_sales()
    
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Left side - Sales Form
        left_widget = QWidget()
        left_widget.setFixedWidth(500)
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(15)
        
        # Title
        title_label = QLabel("New Sale")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #2c3e50;")
        left_layout.addWidget(title_label)
        
        # Client selection
        client_group = QGroupBox("Client Information")
        client_layout = QFormLayout()
        client_layout.setSpacing(10)
        
        self.client_search_input = QLineEdit()
        self.client_search_input.setPlaceholderText("Search client by name or phone...")
        self.client_search_input.textChanged.connect(self.search_clients)
        client_layout.addRow("Search Client:", self.client_search_input)
        
        self.client_combo = QComboBox()
        self.client_combo.currentTextChanged.connect(self.on_client_selected)
        client_layout.addRow("Select Client *:", self.client_combo)
        
        self.client_info_label = QLabel("No client selected")
        self.client_info_label.setStyleSheet("color: #666; font-style: italic;")
        client_layout.addRow("Client Info:", self.client_info_label)
        
        client_group.setLayout(client_layout)
        left_layout.addWidget(client_group)
        
        # Product selection
        product_group = QGroupBox("Product Details")
        product_layout = QFormLayout()
        product_layout.setSpacing(10)
        
        self.gas_product_combo = QComboBox()
        self.gas_product_combo.currentTextChanged.connect(self.on_product_selected)
        product_layout.addRow("Gas Product *:", self.gas_product_combo)
        
        self.quantity_spinbox = QSpinBox()
        self.quantity_spinbox.setRange(1, 1000)
        self.quantity_spinbox.setValue(1)
        self.quantity_spinbox.valueChanged.connect(self.calculate_totals)
        product_layout.addRow("Quantity *:", self.quantity_spinbox)
        
        self.unit_price_spinbox = QDoubleSpinBox()
        self.unit_price_spinbox.setRange(0, 100000)
        self.unit_price_spinbox.setDecimals(2)
        self.unit_price_spinbox.setPrefix("Rs. ")
        self.unit_price_spinbox.setSingleStep(100)
        self.unit_price_spinbox.valueChanged.connect(self.calculate_totals)
        product_layout.addRow("Unit Price *:", self.unit_price_spinbox)
        
        product_group.setLayout(product_layout)
        left_layout.addWidget(product_group)
        
        # Totals
        totals_group = QGroupBox("Payment Details")
        totals_layout = QFormLayout()
        totals_layout.setSpacing(10)
        
        self.subtotal_label = QLabel("Rs. 0.00")
        self.subtotal_label.setStyleSheet("font-weight: bold;")
        totals_layout.addRow("Subtotal:", self.subtotal_label)
        
        self.tax_label = QLabel("Rs. 0.00")
        self.tax_label.setStyleSheet("font-weight: bold; color: #e74c3c;")
        totals_layout.addRow("Tax (16%):", self.tax_label)
        
        self.total_label = QLabel("Rs. 0.00")
        self.total_label.setStyleSheet("font-weight: bold; font-size: 16px; color: #27ae60;")
        totals_layout.addRow("Current Product Total:", self.total_label)
        
        self.cart_total_label = QLabel("Rs. 0.00")
        self.cart_total_label.setStyleSheet("font-weight: bold; font-size: 18px; color: #e74c3c;")
        totals_layout.addRow("Cart Total:", self.cart_total_label)
        
        self.amount_paid_spinbox = QDoubleSpinBox()
        self.amount_paid_spinbox.setRange(0, 100000)
        self.amount_paid_spinbox.setDecimals(2)
        self.amount_paid_spinbox.setPrefix("Rs. ")
        self.amount_paid_spinbox.setSingleStep(100)
        self.amount_paid_spinbox.valueChanged.connect(self.calculate_balance)
        totals_layout.addRow("Amount Paid *:", self.amount_paid_spinbox)
        
        self.balance_label = QLabel("Rs. 0.00")
        self.balance_label.setStyleSheet("font-weight: bold;")
        totals_layout.addRow("Balance:", self.balance_label)
        
        # Payment controls
        payment_controls_layout = QHBoxLayout()
        payment_controls_layout.setSpacing(5)
        
        self.full_payment_btn = QPushButton("Full Payment")
        self.full_payment_btn.clicked.connect(self.set_full_payment)
        self.full_payment_btn.setStyleSheet("background-color: #3498db; color: white; font-size: 12px;")
        payment_controls_layout.addWidget(self.full_payment_btn)
        
        self.clear_payment_btn = QPushButton("Clear")
        self.clear_payment_btn.clicked.connect(self.clear_payment)
        self.clear_payment_btn.setStyleSheet("background-color: #95a5a6; color: white; font-size: 12px;")
        payment_controls_layout.addWidget(self.clear_payment_btn)
        
        payment_controls_layout.addStretch()
        totals_layout.addRow("", payment_controls_layout)
        
        totals_group.setLayout(totals_layout)
        left_layout.addWidget(totals_group)
        
        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.add_product_btn = QPushButton("Add to Cart")
        self.add_product_btn.clicked.connect(self.add_to_cart)
        button_layout.addWidget(self.add_product_btn)
        
        self.clear_form_btn = QPushButton("Clear Form")
        self.clear_form_btn.clicked.connect(self.clear_form)
        button_layout.addWidget(self.clear_form_btn)
        
        self.complete_sale_btn = QPushButton("Complete Sale")
        self.complete_sale_btn.clicked.connect(self.complete_sale)
        self.complete_sale_btn.setStyleSheet("background-color: #27ae60; font-weight: bold;")
        button_layout.addWidget(self.complete_sale_btn)
        
        left_layout.addLayout(button_layout)
        left_layout.addStretch()
        
        # Right side - Cart and Recent Sales
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setSpacing(15)
        
        # Cart
        cart_group = QGroupBox("Current Sale Cart")
        cart_layout = QVBoxLayout()
        cart_layout.setSpacing(10)
        
        self.cart_table = QTableWidget()
        self.cart_table.setColumnCount(6)
        self.cart_table.setHorizontalHeaderLabels([
            "Product", "Quantity", "Unit Price", "Subtotal", "Tax", "Total"
        ])
        self.cart_table.setAlternatingRowColors(True)
        self.cart_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.cart_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.cart_table.setMaximumHeight(200)
        cart_layout.addWidget(self.cart_table)
        
        cart_controls_layout = QHBoxLayout()
        self.remove_from_cart_btn = QPushButton("Remove Selected")
        self.remove_from_cart_btn.clicked.connect(self.remove_from_cart)
        cart_controls_layout.addWidget(self.remove_from_cart_btn)
        
        self.clear_cart_btn = QPushButton("Clear Cart")
        self.clear_cart_btn.clicked.connect(self.clear_cart)
        cart_controls_layout.addWidget(self.clear_cart_btn)
        
        cart_layout.addLayout(cart_controls_layout)
        cart_group.setLayout(cart_layout)
        right_layout.addWidget(cart_group)
        
        # Recent sales
        recent_group = QGroupBox("Recent Sales")
        recent_layout = QVBoxLayout()
        recent_layout.setSpacing(10)
        
        self.recent_sales_table = QTableWidget()
        self.recent_sales_table.setColumnCount(8)  # Added Actions column
        self.recent_sales_table.setHorizontalHeaderLabels([
            "Date", "Client", "Product", "Quantity", "Total", "Paid", "Balance", "Actions"
        ])
        self.recent_sales_table.setAlternatingRowColors(True)
        self.recent_sales_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.recent_sales_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.recent_sales_table.setColumnWidth(7, 100)  # Actions column width
        recent_layout.addWidget(self.recent_sales_table)
        
        recent_controls_layout = QHBoxLayout()
        self.refresh_recent_btn = QPushButton("Refresh Recent Sales")
        self.refresh_recent_btn.clicked.connect(self.load_recent_sales)
        recent_controls_layout.addWidget(self.refresh_recent_btn)
        
        self.generate_receipt_btn = QPushButton("Generate Receipt for Selected")
        self.generate_receipt_btn.clicked.connect(self.generate_receipt_for_selected)
        self.generate_receipt_btn.setStyleSheet("background-color: #3498db; color: white;")
        recent_controls_layout.addWidget(self.generate_receipt_btn)
        
        recent_layout.addLayout(recent_controls_layout)
        
        recent_group.setLayout(recent_layout)
        right_layout.addWidget(recent_group)
        
        # Add widgets to main layout
        layout.addWidget(left_widget)
        layout.addWidget(right_widget)
        
        # Set stretch factors
        layout.setStretch(0, 1)
        layout.setStretch(1, 1)
        
        # Set role-based permissions
        self.set_role_permissions()
    
    def set_role_permissions(self):
        """Set permissions based on user role"""
        role = self.current_user['role']
        
        if role == 'Driver':
            self.add_product_btn.setEnabled(False)
            self.complete_sale_btn.setEnabled(False)
            self.remove_from_cart_btn.setEnabled(False)
            self.clear_cart_btn.setEnabled(False)
            self.clear_form_btn.setEnabled(False)
            self.generate_receipt_btn.setEnabled(False)
    
    def load_gas_products(self):
        """Load gas products from database"""
        try:
            products = self.db_manager.get_gas_products()
            self.gas_product_combo.clear()
            
            # Ensure combo box is enabled
            self.gas_product_combo.setEnabled(True)
            
            for product in products:
                display_text = f"{product['gas_type']}"
                if product['sub_type']:
                    display_text += f" - {product['sub_type']}"
                display_text += f" - {product['capacity']}"
                
                self.gas_product_combo.addItem(display_text, product)
            
            if products:
                self.on_product_selected()
                
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load gas products: {str(e)}")
    
    def search_clients(self):
        """Search clients as user types"""
        search_text = self.client_search_input.text().strip()
        if len(search_text) < 2:  # Only search if at least 2 characters
            return
        
        try:
            clients = self.db_manager.get_clients(search_text)
            self.client_combo.clear()
            
            for client in clients:
                display_text = f"{client['name']} ({client['phone']})"
                if client['company']:
                    display_text += f" - {client['company']}"
                
                self.client_combo.addItem(display_text, client)
                
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to search clients: {str(e)}")
    
    def on_client_selected(self):
        """Handle client selection"""
        index = self.client_combo.currentIndex()
        if index >= 0:
            self.current_client = self.client_combo.itemData(index)
            client_info = f"Name: {self.current_client['name']}"
            if self.current_client['company']:
                client_info += f"\nCompany: {self.current_client['company']}"
            client_info += f"\nPhone: {self.current_client['phone']}"
            client_info += f"\nBalance: Rs. {self.current_client['balance']:,.2f}"
            self.client_info_label.setText(client_info)
        else:
            self.current_client = None
            self.client_info_label.setText("No client selected")
    
    def on_product_selected(self):
        """Handle product selection"""
        index = self.gas_product_combo.currentIndex()
        if index >= 0:
            product = self.gas_product_combo.itemData(index)
            self.unit_price_spinbox.setValue(float(product['unit_price']))
            self.calculate_totals()
    
    def calculate_totals(self):
        """Calculate subtotal, tax, and total for current product selection"""
        quantity = self.quantity_spinbox.value()
        unit_price = self.unit_price_spinbox.value()
        
        subtotal = quantity * unit_price
        tax = subtotal * 0.16  # 16% tax
        total = subtotal + tax
        
        # Update labels with current product totals (not cart totals)
        self.subtotal_label.setText(f"Rs. {subtotal:,.2f}")
        self.tax_label.setText(f"Rs. {tax:,.2f}")
        self.total_label.setText(f"Rs. {total:,.2f}")
        
        # Set default payment amount to cart total, not single product total
        if self.amount_paid_spinbox.value() == 0 and self.current_products:
            cart_total = sum(item['total'] for item in self.current_products)
            self.amount_paid_spinbox.setValue(cart_total)
        
        self.calculate_balance()
    
    def calculate_balance(self):
        """Calculate balance after payment based on cart total"""
        # Calculate total from cart, not just current product
        total_subtotal = sum(item['subtotal'] for item in self.current_products)
        total_tax = sum(item['tax'] for item in self.current_products)
        total_amount = sum(item['total'] for item in self.current_products)
        amount_paid = self.amount_paid_spinbox.value()
        
        balance = total_amount - amount_paid
        self.balance_label.setText(f"Rs. {balance:,.2f}")
        
        # Change color based on balance
        if balance > 0:
            self.balance_label.setStyleSheet("font-weight: bold; color: #e74c3c;")
        elif balance < 0:
            self.balance_label.setStyleSheet("font-weight: bold; color: #f39c12;")
        else:
            self.balance_label.setStyleSheet("font-weight: bold; color: #27ae60;")
        
        # Update cart total display
        self.cart_total_label.setText(f"Rs. {total_amount:,.2f}")
        
        # Update the current product totals display (keep them separate from cart totals)
        quantity = self.quantity_spinbox.value()
        unit_price = self.unit_price_spinbox.value()
        current_subtotal = quantity * unit_price
        current_tax = current_subtotal * 0.16
        current_total = current_subtotal + current_tax
        
        self.subtotal_label.setText(f"Rs. {current_subtotal:,.2f}")
        self.tax_label.setText(f"Rs. {current_tax:,.2f}")
        self.total_label.setText(f"Rs. {current_total:,.2f}")
    
    def add_to_cart(self):
        """Add product to cart"""
        if not self.current_client:
            QMessageBox.warning(self, "Validation Error", "Please select a client first.")
            return
        
        index = self.gas_product_combo.currentIndex()
        if index < 0:
            QMessageBox.warning(self, "Validation Error", "Please select a gas product.")
            return
        
        quantity = self.quantity_spinbox.value()
        unit_price = self.unit_price_spinbox.value()
        
        if quantity <= 0:
            QMessageBox.warning(self, "Validation Error", "Quantity must be greater than 0.")
            return
        
        if unit_price <= 0:
            QMessageBox.warning(self, "Validation Error", "Unit price must be greater than 0.")
            return
        
        product = self.gas_product_combo.itemData(index)
        
        # Calculate totals
        subtotal = quantity * unit_price
        tax = subtotal * 0.16
        total = subtotal + tax
        
        # Add to cart
        cart_item = {
            'product': product,
            'quantity': quantity,
            'unit_price': unit_price,
            'subtotal': subtotal,
            'tax': tax,
            'total': total
        }
        
        self.current_products.append(cart_item)
        self.update_cart_table()
        self.clear_form()
        
        QMessageBox.information(self, "Success", "Product added to cart!")
    
    def update_cart_table(self):
        """Update cart table display"""
        self.cart_table.setRowCount(len(self.current_products))
        
        for row, item in enumerate(self.current_products):
            product = item['product']
            product_text = f"{product['gas_type']}"
            if product['sub_type']:
                product_text += f" - {product['sub_type']}"
            product_text += f" - {product['capacity']}"
            
            self.cart_table.setItem(row, 0, QTableWidgetItem(product_text))
            self.cart_table.setItem(row, 1, QTableWidgetItem(str(item['quantity'])))
            self.cart_table.setItem(row, 2, QTableWidgetItem(f"Rs. {item['unit_price']:,.2f}"))
            self.cart_table.setItem(row, 3, QTableWidgetItem(f"Rs. {item['subtotal']:,.2f}"))
            self.cart_table.setItem(row, 4, QTableWidgetItem(f"Rs. {item['tax']:,.2f}"))
            self.cart_table.setItem(row, 5, QTableWidgetItem(f"Rs. {item['total']:,.2f}"))
    
    def remove_from_cart(self):
        """Remove selected item from cart"""
        current_row = self.cart_table.currentRow()
        if current_row >= 0:
            self.current_products.pop(current_row)
            self.update_cart_table()
            QMessageBox.information(self, "Success", "Item removed from cart!")
        else:
            QMessageBox.warning(self, "No Selection", "Please select an item to remove.")
    
    def clear_cart(self):
        """Clear all items from cart"""
        self.current_products.clear()
        self.update_cart_table()
        self.cart_total_label.setText("Rs. 0.00")
        self.calculate_balance()
    
    def clear_form(self):
        """Clear the sales form"""
        self.quantity_spinbox.setValue(1)
        self.amount_paid_spinbox.setValue(0)
        self.calculate_totals()
    
    def set_full_payment(self):
        """Set payment amount to total amount"""
        # Calculate total from current products instead of parsing label
        if not self.current_products:
            QMessageBox.warning(self, "Validation Error", "Please add products to cart first.")
            return
            
        total_amount = sum(item['total'] for item in self.current_products)
        self.amount_paid_spinbox.setValue(total_amount)
        self.calculate_balance()
    
    def clear_payment(self):
        """Clear payment amount"""
        self.amount_paid_spinbox.setValue(0)
    
    def complete_sale(self):
        """Complete the sale"""
        if not self.current_client:
            QMessageBox.warning(self, "Validation Error", "Please select a client first.")
            return
        
        if not self.current_products:
            QMessageBox.warning(self, "Validation Error", "Please add at least one product to the cart.")
            return
        
        # Calculate totals for entire cart
        total_subtotal = sum(item['subtotal'] for item in self.current_products)
        total_tax = sum(item['tax'] for item in self.current_products)
        total_amount = sum(item['total'] for item in self.current_products)
        amount_paid = self.amount_paid_spinbox.value()
        balance = total_amount - amount_paid
        
        # Validate payment amount
        if amount_paid <= 0:
            QMessageBox.warning(self, "Validation Error", "Please enter a valid payment amount.")
            self.amount_paid_spinbox.setFocus()
            return
        
        # Check if payment is less than total (partial payment)
        if amount_paid < total_amount:
            reply = QMessageBox.question(
                self,
                "Partial Payment Confirmation",
                f"The payment amount (Rs. {amount_paid:,.2f}) is less than the total amount (Rs. {total_amount:,.2f}).\n"
                f"This will create a balance of Rs. {balance:,.2f}.\n\n"
                "Do you want to proceed with partial payment?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        elif amount_paid > total_amount:
            # Overpayment confirmation
            reply = QMessageBox.question(
                self,
                "Overpayment Confirmation",
                f"The payment amount (Rs. {amount_paid:,.2f}) is more than the total amount (Rs. {total_amount:,.2f}).\n"
                f"This will create a credit of Rs. {abs(balance):,.2f}.\n\n"
                "Do you want to proceed with overpayment?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        
        # Confirm sale
        reply = QMessageBox.question(
            self,
            "Confirm Sale",
            f"Client: {self.current_client['name']}\n"
            f"Total Amount: Rs. {total_amount:,.2f}\n"
            f"Amount Paid: Rs. {amount_paid:,.2f}\n"
            f"Balance: Rs. {balance:,.2f}\n\n"
            "Do you want to complete this sale?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Store current client info before clearing
                current_client_id = self.current_client['id']
                current_client_name = self.current_client['name']
                
                # For multiple products, create a summary sale record
                # Use the first product as representative, but include total quantities and amounts
                if len(self.current_products) > 1:
                    # For multiple products, create a summary entry
                    first_product = self.current_products[0]
                    total_quantity = sum(item['quantity'] for item in self.current_products)
                    
                    # Create sale record with summary information
                    sale_id = self.db_manager.create_sale(
                        client_id=current_client_id,
                        gas_product_id=first_product['product']['id'],
                        quantity=total_quantity,  # Total quantity of all products
                        unit_price=total_subtotal / total_quantity if total_quantity > 0 else 0,  # Average unit price
                        subtotal=total_subtotal,
                        tax_amount=total_tax,
                        total_amount=total_amount,
                        amount_paid=amount_paid,
                        balance=balance,
                        created_by=self.current_user['id']
                    )
                else:
                    # For single product, use normal logic
                    first_product = self.current_products[0]
                    sale_id = self.db_manager.create_sale(
                        client_id=current_client_id,
                        gas_product_id=first_product['product']['id'],
                        quantity=first_product['quantity'],
                        unit_price=first_product['unit_price'],
                        subtotal=total_subtotal,
                        tax_amount=total_tax,
                        total_amount=total_amount,
                        amount_paid=amount_paid,
                        balance=balance,
                        created_by=self.current_user['id']
                    )
                
                # Create receipt
                receipt_number = self.db_manager.get_next_receipt_number()
                self.db_manager.create_receipt(
                    receipt_number=receipt_number,
                    sale_id=sale_id,
                    client_id=current_client_id,
                    total_amount=total_amount,
                    amount_paid=amount_paid,
                    balance=balance,
                    created_by=self.current_user['id']
                )
                

                
                # Log activity
                self.db_manager.log_activity(
                    "CREATE_SALE",
                    f"Created sale for client: {current_client_name}, Receipt: {receipt_number}",
                    self.current_user['id']
                )
                
                QMessageBox.information(
                    self,
                    "Sale Completed",
                    f"Sale completed successfully!\nReceipt Number: {receipt_number}"
                )
                
                # Clear cart and refresh
                self.clear_cart()
                self.clear_form()
                self.load_recent_sales()
                
                # Ask if user wants to create another sale for the same client
                reply = QMessageBox.question(
                    self,
                    "Create Another Sale?",
                    f"Sale completed for {current_client_name}.\n\n"
                    "Do you want to create another sale for the same client?\n"
                    "Click 'Yes' to keep this client, 'No' to select a different client.",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                
                if reply == QMessageBox.Yes:
                    # Keep the same client and refresh their info
                    self.on_client_selected()
                else:
                    # Clear client selection to force selection of new client
                    self.client_combo.setCurrentIndex(-1)
                    self.current_client = None
                    self.client_info_label.setText("No client selected")
                
            except Exception as e:
                QMessageBox.critical(self, "Database Error", f"Failed to complete sale: {str(e)}")
    
    def load_recent_sales(self):
        """Load recent sales"""
        try:
            query = '''
                SELECT s.*, c.name as client_name, c.phone as client_phone,
                       gp.gas_type, gp.sub_type, gp.capacity
                FROM sales s
                JOIN clients c ON s.client_id = c.id
                JOIN gas_products gp ON s.gas_product_id = gp.id
                ORDER BY s.created_at DESC
                LIMIT 20
            '''
            sales = self.db_manager.execute_query(query)
            
            self.recent_sales_table.setRowCount(len(sales))
            
            for row, sale in enumerate(sales):
                self.recent_sales_table.setItem(row, 0, QTableWidgetItem(sale['created_at'][:16]))
                self.recent_sales_table.setItem(row, 1, QTableWidgetItem(sale['client_name']))
                
                product_text = f"{sale['gas_type']}"
                if sale['sub_type']:
                    product_text += f" - {sale['sub_type']}"
                product_text += f" - {sale['capacity']}"
                
                self.recent_sales_table.setItem(row, 2, QTableWidgetItem(product_text))
                self.recent_sales_table.setItem(row, 3, QTableWidgetItem(str(sale['quantity'])))
                self.recent_sales_table.setItem(row, 4, QTableWidgetItem(f"Rs. {sale['total_amount']:,.2f}"))
                self.recent_sales_table.setItem(row, 5, QTableWidgetItem(f"Rs. {sale['amount_paid']:,.2f}"))
                self.recent_sales_table.setItem(row, 6, QTableWidgetItem(f"Rs. {sale['balance']:,.2f}"))
                
                # Color code based on balance
                if sale['balance'] > 0:
                    self.recent_sales_table.item(row, 6).setForeground(Qt.red)
                elif sale['balance'] < 0:
                    self.recent_sales_table.item(row, 6).setForeground(Qt.darkYellow)
                else:
                    self.recent_sales_table.item(row, 6).setForeground(Qt.darkGreen)
                
                # Add Generate Receipt button
                generate_btn = QPushButton("Generate Receipt")
                generate_btn.clicked.connect(lambda checked, s=sale: self.generate_receipt_for_sale(s))
                self.recent_sales_table.setCellWidget(row, 7, generate_btn)
            
            self.recent_sales_table.resizeColumnsToContents()
            
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load recent sales: {str(e)}")
    
    def generate_receipt_for_selected(self):
        """Generate receipt for the selected sale in recent sales table"""
        selected_items = self.recent_sales_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selection Error", "Please select a sale from the recent sales table.")
            return
        
        # Get the row of the first selected item
        row = selected_items[0].row()
        
        # Get the sale data from the table (we need to query the database to get complete sale info)
        try:
            # Get sale ID from the recent sales data (we need to modify our query to include sale ID)
            query = '''
                SELECT s.id, s.*, c.name as client_name, c.phone as client_phone,
                       gp.gas_type, gp.sub_type, gp.capacity
                FROM sales s
                JOIN clients c ON s.client_id = c.id
                JOIN gas_products gp ON s.gas_product_id = gp.id
                ORDER BY s.created_at DESC
                LIMIT 20
            '''
            sales = self.db_manager.execute_query(query)
            
            if row < len(sales):
                selected_sale = sales[row]
                self.generate_receipt_for_sale(selected_sale)
            else:
                QMessageBox.warning(self, "Error", "Could not find the selected sale.")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to get sale details: {str(e)}")
    
    def generate_receipt_for_sale(self, sale):
        """Generate receipt for a specific sale"""
        try:
            # Check if receipt already exists for this sale
            existing_receipt = self.db_manager.execute_query(
                "SELECT * FROM receipts WHERE sale_id = ?", 
                (sale['id'],)
            )
            
            if existing_receipt:
                QMessageBox.information(self, "Info", "Receipt already exists for this sale. Opening existing receipt...")
                self.open_receipt(existing_receipt[0])
                return
            
            # Generate new receipt
            # Ask for payment amount
            initial_paid = float(sale['amount_paid']) if sale['amount_paid'] is not None else 0.0
            amount_paid, ok = QInputDialog.getDouble(
                self,
                "Record Payment",
                "Enter amount paid:",
                initial_paid,
                0.0,
                float(sale['total_amount']),
                2
            )
            if not ok:
                return
            # Update sale payment before creating receipt
            self.db_manager.update_sale_payment(sale['id'], amount_paid)
            balance = float(sale['total_amount']) - amount_paid

            receipt_number = self.db_manager.get_next_receipt_number()
            receipt_id = self.db_manager.create_receipt(
                receipt_number=receipt_number,
                sale_id=sale['id'],
                client_id=sale['client_id'],
                total_amount=sale['total_amount'],
                amount_paid=amount_paid,
                balance=balance,
                created_by=self.current_user['id']
            )
            
            if receipt_id:
                # Get the newly created receipt
                new_receipt = self.db_manager.execute_query(
                    "SELECT * FROM receipts WHERE id = ?", 
                    (receipt_id,)
                )[0]
                
                QMessageBox.information(self, "Success", f"Receipt {receipt_number} generated successfully!")
                self.open_receipt(new_receipt)
                self.load_recent_sales()  # Refresh the table
            else:
                QMessageBox.critical(self, "Error", "Failed to create receipt.")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate receipt: {str(e)}")
    
    def open_receipt(self, receipt):
        """Open receipt dialog for viewing/printing"""
        try:
            # Import the receipts module
            from components.receipts import ReceiptDialog
            
            # Get complete receipt data
            receipt_data = self.db_manager.execute_query('''
                SELECT r.*, c.name as client_name, c.phone as client_phone, c.company as client_company,
                       gp.gas_type, gp.sub_type, gp.capacity, s.quantity, s.unit_price, 
                       s.subtotal, s.tax_amount, s.total_amount, u.full_name as cashier_name,
                       r.amount_paid, r.balance
                FROM receipts r
                JOIN clients c ON r.client_id = c.id
                JOIN sales s ON r.sale_id = s.id
                JOIN gas_products gp ON s.gas_product_id = gp.id
                JOIN users u ON r.created_by = u.id
                WHERE r.id = ?
            ''', (receipt['id'],))[0]
            
            # Open receipt dialog
            dialog = ReceiptDialog(self.db_manager, receipt_data, self)
            dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open receipt: {str(e)}")