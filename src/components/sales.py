from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QSpinBox, QDoubleSpinBox, QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QInputDialog
)
from PySide6.QtCore import Qt
from database_module import DatabaseManager

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
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        title_label = QLabel("Sales & Billing")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title_label)

        clients_layout = QHBoxLayout()
        clients_layout.setSpacing(10)
        self.client_search_input = QLineEdit()
        self.client_search_input.setPlaceholderText("Search client by name, phone, or company...")
        self.client_search_input.textChanged.connect(self.search_clients)
        clients_layout.addWidget(self.client_search_input)

        self.client_combo = QComboBox()
        self.client_combo.currentIndexChanged.connect(self.on_client_selected)
        clients_layout.addWidget(self.client_combo)

        layout.addLayout(clients_layout)

        self.client_info_label = QLabel("No client selected")
        self.client_info_label.setStyleSheet("font-size: 13px; color: #555;")
        layout.addWidget(self.client_info_label)

        product_layout = QHBoxLayout()
        product_layout.setSpacing(10)

        self.gas_product_combo = QComboBox()
        self.gas_product_combo.currentIndexChanged.connect(self.on_product_selected)
        product_layout.addWidget(self.gas_product_combo)

        self.quantity_spinbox = QSpinBox()
        self.quantity_spinbox.setRange(1, 1000)
        self.quantity_spinbox.setValue(1)
        self.quantity_spinbox.valueChanged.connect(self.calculate_totals)
        product_layout.addWidget(self.quantity_spinbox)

        self.unit_price_spinbox = QDoubleSpinBox()
        self.unit_price_spinbox.setRange(0, 1000000)
        self.unit_price_spinbox.setDecimals(2)
        self.unit_price_spinbox.setPrefix("Rs. ")
        self.unit_price_spinbox.setSingleStep(100)
        self.unit_price_spinbox.valueChanged.connect(self.calculate_totals)
        product_layout.addWidget(self.unit_price_spinbox)

        add_btn = QPushButton("Add to Cart")
        add_btn.clicked.connect(self.add_to_cart)
        product_layout.addWidget(add_btn)

        layout.addLayout(product_layout)

        totals_layout = QHBoxLayout()
        totals_layout.setSpacing(20)
        self.subtotal_label = QLabel("Rs. 0.00")
        self.tax_label = QLabel("Rs. 0.00")
        self.total_label = QLabel("Rs. 0.00")
        self.subtotal_label.setStyleSheet("font-weight: bold;")
        self.tax_label.setStyleSheet("font-weight: bold;")
        self.total_label.setStyleSheet("font-weight: bold;")
        totals_layout.addWidget(QLabel("Subtotal:"))
        totals_layout.addWidget(self.subtotal_label)
        totals_layout.addWidget(QLabel("Tax:"))
        totals_layout.addWidget(self.tax_label)
        totals_layout.addWidget(QLabel("Total:"))
        totals_layout.addWidget(self.total_label)
        layout.addLayout(totals_layout)

        self.cart_table = QTableWidget()
        self.cart_table.setColumnCount(6)
        self.cart_table.setHorizontalHeaderLabels([
            "Product", "Quantity", "Unit Price", "Subtotal", "Tax", "Total"
        ])
        self.cart_table.setAlternatingRowColors(True)
        self.cart_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.cart_table)

        cart_actions = QHBoxLayout()
        remove_btn = QPushButton("Remove Selected")
        remove_btn.clicked.connect(self.remove_from_cart)
        clear_btn = QPushButton("Clear Cart")
        clear_btn.clicked.connect(self.clear_cart)
        cart_actions.addWidget(remove_btn)
        cart_actions.addWidget(clear_btn)
        layout.addLayout(cart_actions)

        payment_layout = QHBoxLayout()
        payment_layout.setSpacing(20)
        self.cart_total_label = QLabel("Rs. 0.00")
        self.amount_paid_spinbox = QDoubleSpinBox()
        self.amount_paid_spinbox.setRange(0, 100000000)
        self.amount_paid_spinbox.setDecimals(2)
        self.amount_paid_spinbox.setPrefix("Rs. ")
        self.amount_paid_spinbox.valueChanged.connect(self.calculate_balance)
        self.balance_label = QLabel("Rs. 0.00")
        self.balance_label.setStyleSheet("font-weight: bold; color: #27ae60;")
        payment_layout.addWidget(QLabel("Cart Total:"))
        payment_layout.addWidget(self.cart_total_label)
        payment_layout.addWidget(QLabel("Amount Paid:"))
        payment_layout.addWidget(self.amount_paid_spinbox)
        payment_layout.addWidget(QLabel("Balance:"))
        payment_layout.addWidget(self.balance_label)
        full_pay_btn = QPushButton("Full Payment")
        full_pay_btn.clicked.connect(self.set_full_payment)
        clear_pay_btn = QPushButton("Clear Payment")
        clear_pay_btn.clicked.connect(self.clear_payment)
        complete_btn = QPushButton("Complete Sale")
        complete_btn.clicked.connect(self.complete_sale)
        payment_layout.addWidget(full_pay_btn)
        payment_layout.addWidget(clear_pay_btn)
        payment_layout.addWidget(complete_btn)
        layout.addLayout(payment_layout)

        self.recent_sales_table = QTableWidget()
        self.recent_sales_table.setColumnCount(8)
        self.recent_sales_table.setHorizontalHeaderLabels([
            "Date", "Client", "Product", "Quantity", "Total", "Paid", "Balance", "Actions"
        ])
        self.recent_sales_table.setAlternatingRowColors(True)
        self.recent_sales_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.recent_sales_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.recent_sales_table)

    def search_clients(self):
        search_text = self.client_search_input.text().strip()
        if not search_text:
            self.client_combo.clear()
            self.current_client = None
            self.client_info_label.setText("No client selected")
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
        index = self.gas_product_combo.currentIndex()
        if index >= 0:
            product = self.gas_product_combo.itemData(index)
            self.unit_price_spinbox.setValue(float(product['unit_price']))
            self.calculate_totals()

    def calculate_totals(self):
        quantity = self.quantity_spinbox.value()
        unit_price = self.unit_price_spinbox.value()
        subtotal = quantity * unit_price
        tax = subtotal * 0.16
        total = subtotal + tax
        self.subtotal_label.setText(f"Rs. {subtotal:,.2f}")
        self.tax_label.setText(f"Rs. {tax:,.2f}")
        self.total_label.setText(f"Rs. {total:,.2f}")
        if self.amount_paid_spinbox.value() == 0 and self.current_products:
            cart_total = sum(item['total'] for item in self.current_products)
            self.amount_paid_spinbox.setValue(cart_total)
        self.calculate_balance()

    def calculate_balance(self):
        total_subtotal = sum(item['subtotal'] for item in self.current_products)
        total_tax = sum(item['tax'] for item in self.current_products)
        total_amount = sum(item['total'] for item in self.current_products)
        amount_paid = self.amount_paid_spinbox.value()
        balance = total_amount - amount_paid
        self.balance_label.setText(f"Rs. {balance:,.2f}")
        if balance > 0:
            self.balance_label.setStyleSheet("font-weight: bold; color: #e74c3c;")
        elif balance < 0:
            self.balance_label.setStyleSheet("font-weight: bold; color: #f39c12;")
        else:
            self.balance_label.setStyleSheet("font-weight: bold; color: #27ae60;")
        self.cart_total_label.setText(f"Rs. {total_amount:,.2f}")
        quantity = self.quantity_spinbox.value()
        unit_price = self.unit_price_spinbox.value()
        current_subtotal = quantity * unit_price
        current_tax = current_subtotal * 0.16
        current_total = current_subtotal + current_tax
        self.subtotal_label.setText(f"Rs. {current_subtotal:,.2f}")
        self.tax_label.setText(f"Rs. {current_tax:,.2f}")
        self.total_label.setText(f"Rs. {current_total:,.2f}")

    def add_to_cart(self):
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
        subtotal = quantity * unit_price
        tax = subtotal * 0.16
        total = subtotal + tax
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
        current_row = self.cart_table.currentRow()
        if current_row >= 0:
            self.current_products.pop(current_row)
            self.update_cart_table()
            QMessageBox.information(self, "Success", "Item removed from cart!")
        else:
            QMessageBox.warning(self, "No Selection", "Please select an item to remove.")

    def clear_cart(self):
        self.current_products.clear()
        self.update_cart_table()
        self.cart_total_label.setText("Rs. 0.00")
        self.calculate_balance()

    def clear_form(self):
        self.quantity_spinbox.setValue(1)
        self.amount_paid_spinbox.setValue(0)
        self.calculate_totals()

    def set_full_payment(self):
        if not self.current_products:
            QMessageBox.warning(self, "Validation Error", "Please add products to cart first.")
            return
        total_amount = sum(item['total'] for item in self.current_products)
        self.amount_paid_spinbox.setValue(total_amount)
        self.calculate_balance()

    def clear_payment(self):
        self.amount_paid_spinbox.setValue(0)

    def complete_sale(self):
        if not self.current_client:
            QMessageBox.warning(self, "Validation Error", "Please select a client first.")
            return
        if not self.current_products:
            QMessageBox.warning(self, "Validation Error", "Please add at least one product to the cart.")
            return
        total_subtotal = sum(item['subtotal'] for item in self.current_products)
        total_tax = sum(item['tax'] for item in self.current_products)
        total_amount = sum(item['total'] for item in self.current_products)
        amount_paid = self.amount_paid_spinbox.value()
        balance = total_amount - amount_paid
        if amount_paid <= 0:
            QMessageBox.warning(self, "Validation Error", "Please enter a valid payment amount.")
            self.amount_paid_spinbox.setFocus()
            return
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
                current_client_id = self.current_client['id']
                current_client_name = self.current_client['name']
                if len(self.current_products) > 1:
                    first_product = self.current_products[0]
                    total_quantity = sum(item['quantity'] for item in self.current_products)
                    sale_id = self.db_manager.create_sale(
                        client_id=current_client_id,
                        gas_product_id=first_product['product']['id'],
                        quantity=total_quantity,
                        unit_price=total_subtotal / total_quantity if total_quantity > 0 else 0,
                        subtotal=total_subtotal,
                        tax_amount=total_tax,
                        total_amount=total_amount,
                        amount_paid=amount_paid,
                        balance=balance,
                        created_by=self.current_user['id']
                    )
                else:
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
                self.clear_cart()
                self.clear_form()
                self.load_recent_sales()
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
                    self.on_client_selected()
                else:
                    self.client_combo.setCurrentIndex(-1)
                    self.current_client = None
                    self.client_info_label.setText("No client selected")
            except Exception as e:
                QMessageBox.critical(self, "Database Error", f"Failed to complete sale: {str(e)}")

    def load_recent_sales(self):
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
                if sale['balance'] > 0:
                    self.recent_sales_table.item(row, 6).setForeground(Qt.red)
                elif sale['balance'] < 0:
                    self.recent_sales_table.item(row, 6).setForeground(Qt.darkYellow)
                else:
                    self.recent_sales_table.item(row, 6).setForeground(Qt.darkGreen)
                generate_btn = QPushButton("Generate Receipt")
                generate_btn.clicked.connect(lambda checked, s=sale: self.generate_receipt_for_sale(s))
                self.recent_sales_table.setCellWidget(row, 7, generate_btn)
            self.recent_sales_table.resizeColumnsToContents()
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load recent sales: {str(e)}")

    def generate_receipt_for_selected(self):
        selected_items = self.recent_sales_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selection Error", "Please select a sale from the recent sales table.")
            return
        row = selected_items[0].row()
        try:
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
        try:
            existing_receipt = self.db_manager.execute_query(
                "SELECT * FROM receipts WHERE sale_id = ?",
                (sale['id'],)
            )
            if existing_receipt:
                QMessageBox.information(self, "Info", "Receipt already exists for this sale. Opening existing receipt...")
                self.open_receipt(existing_receipt[0])
                return
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
                new_receipt = self.db_manager.execute_query(
                    "SELECT * FROM receipts WHERE id = ?",
                    (receipt_id,)
                )[0]
                QMessageBox.information(self, "Success", f"Receipt {receipt_number} generated successfully!")
                self.open_receipt(new_receipt)
                self.load_recent_sales()
            else:
                QMessageBox.critical(self, "Error", "Failed to create receipt.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate receipt: {str(e)}")

    def open_receipt(self, receipt):
        try:
            from components.receipts import ReceiptDialog
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
            dialog = ReceiptDialog(self.db_manager, receipt_data, self)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open receipt: {str(e)}")

    def load_gas_products(self):
        try:
            products = self.db_manager.get_gas_products()
            self.gas_product_combo.clear()
            for product in products:
                product_text = f"{product['gas_type']}"
                if product['sub_type']:
                    product_text += f" - {product['sub_type']}"
                product_text += f" - {product['capacity']}"
                self.gas_product_combo.addItem(product_text, product)
            if products:
                self.gas_product_combo.setCurrentIndex(0)
                self.on_product_selected()
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load gas products: {str(e)}")