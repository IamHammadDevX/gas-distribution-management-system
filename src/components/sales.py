from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QSpinBox, QDoubleSpinBox, QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QInputDialog, QCheckBox
)
from PySide6.QtCore import Qt
from src.database_module import DatabaseManager

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
        title_label.setStyleSheet("font-size: 26px; font-weight: bold; color: #205087; margin-bottom: 7px;")
        layout.addWidget(title_label)

        clients_layout = QHBoxLayout()
        clients_layout.setSpacing(10)
        self.client_search_input = QLineEdit()
        self.client_search_input.setPlaceholderText("Search client by name, phone, or company...")
        self.client_search_input.textChanged.connect(self.search_clients)
        clients_layout.addWidget(self.client_search_input)

        self.client_combo = QComboBox()
        self.client_combo.setMinimumWidth(300)
        self.client_combo.currentIndexChanged.connect(self.on_client_selected)
        clients_layout.addWidget(self.client_combo)

        layout.addLayout(clients_layout)

        self.client_info_label = QLabel("No client selected")
        self.client_info_label.setStyleSheet("font-size: 14px; color: #555; margin-bottom:6px;")
        layout.addWidget(self.client_info_label)

        # Product Line Entry (Easy UI with tax and discount per product)
        product_layout = QHBoxLayout()
        product_layout.setSpacing(10)

        self.gas_product_combo = QComboBox()
        self.gas_product_combo.setMinimumWidth(220)
        self.gas_product_combo.currentIndexChanged.connect(self.on_product_selected)
        product_layout.addWidget(QLabel("Product:"))
        product_layout.addWidget(self.gas_product_combo)

        self.quantity_spinbox = QSpinBox()
        self.quantity_spinbox.setRange(1, 1000)
        self.quantity_spinbox.setValue(1)
        self.quantity_spinbox.valueChanged.connect(self.calculate_totals)
        product_layout.addWidget(QLabel("Qty:"))
        product_layout.addWidget(self.quantity_spinbox)

        self.unit_price_spinbox = QDoubleSpinBox()
        self.unit_price_spinbox.setRange(0, 1000000)
        self.unit_price_spinbox.setDecimals(2)
        self.unit_price_spinbox.setPrefix("Rs. ")
        self.unit_price_spinbox.setSingleStep(100)
        self.unit_price_spinbox.valueChanged.connect(self.calculate_totals)
        product_layout.addWidget(QLabel("Unit Price:"))
        product_layout.addWidget(self.unit_price_spinbox)

        self.line_discount_spinbox = QDoubleSpinBox()
        self.line_discount_spinbox.setRange(0, 100000000)
        self.line_discount_spinbox.setDecimals(2)
        self.line_discount_spinbox.setPrefix("Rs. ")
        self.line_discount_spinbox.setSingleStep(50)
        self.line_discount_spinbox.valueChanged.connect(self.calculate_totals)
        product_layout.addWidget(QLabel("Discount:"))
        product_layout.addWidget(self.line_discount_spinbox)

        self.product_tax_spinbox = QDoubleSpinBox()
        self.product_tax_spinbox.setRange(0.0, 100.0)
        self.product_tax_spinbox.setDecimals(2)
        self.product_tax_spinbox.setSuffix(" %")
        self.product_tax_spinbox.setSingleStep(0.5)
        self.product_tax_spinbox.valueChanged.connect(self.calculate_totals)
        product_layout.addWidget(QLabel("Tax rate:"))
        product_layout.addWidget(self.product_tax_spinbox)

        add_btn = QPushButton("Add to Cart")
        add_btn.setStyleSheet(
            "QPushButton { background-color: #28a745; color: white; border: 1px solid #1e7e34; border-radius: 6px; padding: 6px 12px; font-size: 13px; font-weight: 600; }"
            "QPushButton:hover { background-color: #218838; }"
            "QPushButton:pressed { background-color: #1e7e34; }"
        )
        add_btn.setMinimumWidth(110)
        add_btn.setFixedHeight(32)
        add_btn.clicked.connect(self.add_to_cart)
        product_layout.addWidget(add_btn)

        clear_btn = QPushButton("Clear")
        clear_btn.setStyleSheet(
            "QPushButton { background-color: #6c757d; color: white; border: 1px solid #5a6268; border-radius: 6px; padding: 6px 12px; font-size: 13px; font-weight: 600; }"
            "QPushButton:hover { background-color: #5a6268; }"
            "QPushButton:pressed { background-color: #545b62; }"
        )
        clear_btn.setMinimumWidth(96)
        clear_btn.setFixedHeight(32)
        clear_btn.clicked.connect(self.clear_form)
        product_layout.addWidget(clear_btn)

        layout.addLayout(product_layout)

        # Totals for the current line (product about-to-add)
        totals_layout = QHBoxLayout()
        totals_layout.setSpacing(12)
        self.subtotal_label = QLabel("Rs. 0.00")
        self.tax_label = QLabel("Rs. 0.00")
        self.total_label = QLabel("Rs. 0.00")
        self.subtotal_label.setStyleSheet("font-weight: bold;")
        self.tax_label.setStyleSheet("font-weight: bold;")
        self.total_label.setStyleSheet("font-weight: bold;")
        totals_layout.addWidget(QLabel("Line Subtotal:"))
        totals_layout.addWidget(self.subtotal_label)
        totals_layout.addWidget(QLabel("Tax:"))
        totals_layout.addWidget(self.tax_label)
        totals_layout.addWidget(QLabel("Line Total:"))
        totals_layout.addWidget(self.total_label)
        layout.addLayout(totals_layout)

        self.cart_table = QTableWidget()
        self.cart_table.setColumnCount(8)
        self.cart_table.setHorizontalHeaderLabels([
            "Products", "Quantity", "Unit Price", "Discount", "Tax (%)", "Subtotal", "Tax", "Total"
        ])
        self.cart_table.setAlternatingRowColors(True)
        self.cart_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.cart_table)

        cart_actions = QHBoxLayout()
        remove_btn = QPushButton("Remove Selected")
        remove_btn.setStyleSheet(
            "QPushButton { background-color: #dc3545; color: white; border: 1px solid #bd2130; border-radius: 6px; padding: 6px 12px; font-size: 13px; font-weight: 600; }"
            "QPushButton:hover { background-color: #c82333; }"
            "QPushButton:pressed { background-color: #bd2130; }"
        )
        remove_btn.setMinimumWidth(140)
        remove_btn.setFixedHeight(32)
        remove_btn.clicked.connect(self.remove_from_cart)
        clear_cart_btn = QPushButton("Clear Cart")
        clear_cart_btn.setStyleSheet(
            "QPushButton { background-color: #dc3545; color: white; border: 1px solid #bd2130; border-radius: 6px; padding: 6px 12px; font-size: 13px; font-weight: 600; }"
            "QPushButton:hover { background-color: #c82333; }"
            "QPushButton:pressed { background-color: #bd2130; }"
        )
        clear_cart_btn.setMinimumWidth(110)
        clear_cart_btn.setFixedHeight(32)
        clear_cart_btn.clicked.connect(self.clear_cart)
        clear_all_btn = QPushButton("Cancel Sale / Clear All")
        clear_all_btn.setStyleSheet(
            "QPushButton { background-color: #dc3545; color: white; border: 1px solid #bd2130; border-radius: 6px; padding: 6px 12px; font-size: 13px; font-weight: 600; }"
            "QPushButton:hover { background-color: #c82333; }"
            "QPushButton:pressed { background-color: #bd2130; }"
        )
        clear_all_btn.setMinimumWidth(180)
        clear_all_btn.setFixedHeight(32)
        clear_all_btn.clicked.connect(self.clear_all_sale)
        cart_actions.addWidget(remove_btn)
        cart_actions.addWidget(clear_cart_btn)
        cart_actions.addWidget(clear_all_btn)
        layout.addLayout(cart_actions)

        payment_layout = QHBoxLayout()
        payment_layout.setSpacing(18)
        self.cart_total_label = QLabel("Rs. 0.00")
        self.cart_tax_label = QLabel("Rs. 0.00")
        self.overall_discount_spinbox = QDoubleSpinBox()
        self.overall_discount_spinbox.setRange(0, 100000000)
        self.overall_discount_spinbox.setDecimals(2)
        self.overall_discount_spinbox.setPrefix("Rs. ")
        self.overall_discount_spinbox.valueChanged.connect(self.calculate_balance)
        self.overall_discount_spinbox.setFixedWidth(110)
        self.amount_paid_spinbox = QDoubleSpinBox()
        self.amount_paid_spinbox.setRange(0, 100000000)
        self.amount_paid_spinbox.setDecimals(2)
        self.amount_paid_spinbox.setPrefix("Rs. ")
        self.amount_paid_spinbox.valueChanged.connect(self.calculate_balance)
        self.amount_paid_spinbox.setFixedWidth(110)
        self.balance_label = QLabel("Rs. 0.00")
        self.balance_label.setStyleSheet("font-weight: bold; color: #27ae60;")
        lbl_cart_total = QLabel("Cart Total:")
        lbl_cart_tax = QLabel("Cart Tax:")
        lbl_overall_disc = QLabel("Overall Disc:")
        lbl_amount_paid = QLabel("Amount Paid:")
        lbl_balance = QLabel("Balance:")
        for lbl in (lbl_cart_total, lbl_cart_tax, lbl_overall_disc, lbl_amount_paid, lbl_balance):
            lbl.setStyleSheet("padding-right:6px;")
        payment_layout.addWidget(lbl_cart_total)
        payment_layout.addWidget(self.cart_total_label)
        payment_layout.addSpacing(12)
        payment_layout.addWidget(lbl_cart_tax)
        payment_layout.addWidget(self.cart_tax_label)
        payment_layout.addSpacing(12)
        payment_layout.addWidget(lbl_overall_disc)
        payment_layout.addWidget(self.overall_discount_spinbox)
        payment_layout.addSpacing(12)
        payment_layout.addWidget(lbl_amount_paid)
        payment_layout.addWidget(self.amount_paid_spinbox)
        payment_layout.addSpacing(12)
        payment_layout.addWidget(lbl_balance)
        self.balance_label.setFixedWidth(80)
        payment_layout.addWidget(self.balance_label)
        full_pay_btn = QPushButton("Full")
        full_pay_btn.setStyleSheet(
            "QPushButton { background-color: #007bff; color: white; border: 1px solid #0069d9; border-radius: 6px; padding: 6px 12px; font-size: 13px; font-weight: 600; }"
            "QPushButton:hover { background-color: #0069d9; }"
            "QPushButton:pressed { background-color: #005cbf; }"
        )
        full_pay_btn.setMinimumWidth(80)
        full_pay_btn.setFixedHeight(32)
        full_pay_btn.clicked.connect(self.set_full_payment)
        clear_pay_btn = QPushButton("Clear")
        clear_pay_btn.setStyleSheet(
            "QPushButton { background-color: #6c757d; color: white; border: 1px solid #5a6268; border-radius: 6px; padding: 6px 12px; font-size: 13px; font-weight: 600; }"
            "QPushButton:hover { background-color: #5a6268; }"
            "QPushButton:pressed { background-color: #545b62; }"
        )
        clear_pay_btn.setMinimumWidth(80)
        clear_pay_btn.setFixedHeight(32)
        clear_pay_btn.clicked.connect(self.clear_payment)
        complete_btn = QPushButton("Confirm")
        complete_btn.setStyleSheet(
            "QPushButton { background-color: #28a745; color: white; border: 1px solid #1e7e34; border-radius: 6px; padding: 6px 14px; font-size: 13px; font-weight: 600; }"
            "QPushButton:hover { background-color: #218838; }"
            "QPushButton:pressed { background-color: #1e7e34; }"
        )
        complete_btn.setMinimumWidth(110)
        complete_btn.setFixedHeight(32)
        complete_btn.clicked.connect(self.complete_sale)
        payment_layout.addStretch(1)
        payment_layout.addWidget(full_pay_btn)
        payment_layout.addWidget(clear_pay_btn)
        payment_layout.addWidget(complete_btn)
        layout.addLayout(payment_layout)

        self.recent_sales_table = QTableWidget()
        self.recent_sales_table.setColumnCount(8)
        self.recent_sales_table.setHorizontalHeaderLabels([
            "Date", "Client", "Products", "Quantities", "Total", "Paid", "Balance", "Actions"
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
        line_discount = self.line_discount_spinbox.value()
        subtotal = max(0.0, quantity * unit_price - line_discount)
        tax_rate = self.product_tax_spinbox.value() / 100.0
        tax = round(subtotal * tax_rate, 2) if tax_rate > 0 else 0.00
        total = subtotal + tax
        self.subtotal_label.setText(f"Rs. {subtotal:,.2f}")
        self.tax_label.setText(f"Rs. {tax:,.2f}")
        self.total_label.setText(f"Rs. {total:,.2f}")

    def calculate_balance(self):
        self.recalc_cart_totals()
        total_subtotal = sum(item['subtotal'] for item in self.current_products)
        total_tax = sum(item['tax'] for item in self.current_products)
        total_amount = sum(item['total'] for item in self.current_products)
        overall_discount = self.overall_discount_spinbox.value()
        total_after_discount = max(0.0, total_amount - overall_discount)
        amount_paid = self.amount_paid_spinbox.value()
        balance = total_after_discount - amount_paid
        self.balance_label.setText(f"Rs. {balance:,.2f}")
        if balance > 0:
            self.balance_label.setStyleSheet("font-weight: bold; color: #e74c3c;")
        elif balance < 0:
            self.balance_label.setStyleSheet("font-weight: bold; color: #f39c12;")
        else:
            self.balance_label.setStyleSheet("font-weight: bold; color: #27ae60;")
        self.cart_total_label.setText(f"Rs. {total_after_discount:,.2f}")
        self.cart_tax_label.setText(f"Rs. {total_tax:,.2f}")

    def recalc_cart_totals(self):
        for item in self.current_products:
            # Each product uses its own tax rate and discount!
            quantity = item['quantity']
            unit_price = item['unit_price']
            discount = item.get('discount', 0.0)
            subtotal = max(0.0, quantity * unit_price - discount)
            tax_rate = item.get('tax_rate', 0.0)
            tax = round(subtotal * tax_rate, 2) if tax_rate > 0 else 0.00
            total = subtotal + tax
            item['subtotal'] = subtotal
            item['tax'] = tax
            item['total'] = total

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
        line_discount = self.line_discount_spinbox.value()
        tax_rate = self.product_tax_spinbox.value() / 100.0
        subtotal = max(0.0, quantity * unit_price - line_discount)
        tax = round(subtotal * tax_rate, 2) if tax_rate > 0 else 0.00
        total = subtotal + tax
        cart_item = {
            'product': product,
            'quantity': quantity,
            'unit_price': unit_price,
            'discount': line_discount,
            'tax_rate': tax_rate,
            'subtotal': subtotal,
            'tax': tax,
            'total': total
        }
        self.current_products.append(cart_item)
        self.update_cart_table()
        self.clear_form()
        self.calculate_balance()
        QMessageBox.information(self, "Success", "Product added to cart!")

    def update_cart_table(self):
        self.cart_table.setRowCount(len(self.current_products))
        for row, item in enumerate(self.current_products):
            product = item['product']
            product_text = f"{product['gas_type']}"
            if product.get('sub_type'):
                product_text += f" - {product['sub_type']}"
            product_text += f" - {product['capacity']}"
            self.cart_table.setItem(row, 0, QTableWidgetItem(product_text))
            self.cart_table.setItem(row, 1, QTableWidgetItem(str(item['quantity'])))
            self.cart_table.setItem(row, 2, QTableWidgetItem(f"Rs. {item['unit_price']:,.2f}"))
            self.cart_table.setItem(row, 3, QTableWidgetItem(f"Rs. {item.get('discount', 0.0):,.2f}"))
            self.cart_table.setItem(row, 4, QTableWidgetItem(f"{item['tax_rate']*100:.2f} %"))
            self.cart_table.setItem(row, 5, QTableWidgetItem(f"Rs. {item['subtotal']:,.2f}"))
            self.cart_table.setItem(row, 6, QTableWidgetItem(f"Rs. {item['tax']:,.2f}"))
            self.cart_table.setItem(row, 7, QTableWidgetItem(f"Rs. {item['total']:,.2f}"))

    def remove_from_cart(self):
        current_row = self.cart_table.currentRow()
        if current_row >= 0:
            self.current_products.pop(current_row)
            self.update_cart_table()
            self.calculate_balance()
            QMessageBox.information(self, "Success", "Item removed from cart!")
        else:
            QMessageBox.warning(self, "No Selection", "Please select an item to remove.")

    def clear_cart(self):
        self.current_products.clear()
        self.update_cart_table()
        self.calculate_balance()

    def clear_form(self):
        self.quantity_spinbox.setValue(1)
        self.line_discount_spinbox.setValue(0)
        self.unit_price_spinbox.setValue(0)
        self.product_tax_spinbox.setValue(0.00)
        self.overall_discount_spinbox.setValue(0)
        self.amount_paid_spinbox.setValue(0)
        self.calculate_totals()

    def clear_all_sale(self):
        self.current_products.clear()
        self.update_cart_table()
        self.client_combo.setCurrentIndex(-1)
        self.current_client = None
        self.client_info_label.setText("No client selected")
        self.client_search_input.clear()
        self.quantity_spinbox.setValue(1)
        self.unit_price_spinbox.setValue(0)
        self.line_discount_spinbox.setValue(0)
        self.product_tax_spinbox.setValue(0.00)
        self.overall_discount_spinbox.setValue(0)
        self.amount_paid_spinbox.setValue(0)
        self.subtotal_label.setText("Rs. 0.00")
        self.tax_label.setText("Rs. 0.00")
        self.total_label.setText("Rs. 0.00")
        self.cart_total_label.setText("Rs. 0.00")
        self.cart_tax_label.setText("Rs. 0.00")
        self.balance_label.setText("Rs. 0.00")
        self.balance_label.setStyleSheet("font-weight: bold; color: #27ae60;")
        self.gas_product_combo.setCurrentIndex(-1)
        self.calculate_totals()
        self.calculate_balance()

    def set_full_payment(self):
        if not self.current_products:
            QMessageBox.warning(self, "Validation Error", "Please add products to cart first.")
            return
        total_amount = sum(item['total'] for item in self.current_products)
        overall_discount = self.overall_discount_spinbox.value()
        self.amount_paid_spinbox.setValue(max(0.0, total_amount - overall_discount))
        self.calculate_balance()

    def clear_payment(self):
        self.amount_paid_spinbox.setValue(0)
        self.calculate_balance()

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
        overall_discount = self.overall_discount_spinbox.value()
        total_amount_after_discount = max(0.0, total_amount - overall_discount)
        amount_paid = self.amount_paid_spinbox.value()
        balance = total_amount_after_discount - amount_paid
        if amount_paid < total_amount_after_discount:
            reply = QMessageBox.question(
                self,
                "Partial Payment Confirmation",
                f"The payment amount (Rs. {amount_paid:,.2f}) is less than the total amount after discount (Rs. {total_amount_after_discount:,.2f}).\n"
                f"Balance: Rs. {balance:,.2f}.\n\n"
                "Do you want to proceed with partial payment?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        elif amount_paid > total_amount_after_discount:
            reply = QMessageBox.question(
                self,
                "Overpayment Confirmation",
                f"The payment amount (Rs. {amount_paid:,.2f}) is more than the total amount after discount (Rs. {total_amount_after_discount:,.2f}).\n"
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
            f"Total Amount (after discount): Rs. {total_amount_after_discount:,.2f}\n"
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
                # Create a sale header referencing the first product but store all items in sale_items
                first_product = self.current_products[0]
                sale_id = self.db_manager.create_sale(
                    client_id=current_client_id,
                    gas_product_id=first_product['product']['id'],
                    quantity=first_product['quantity'],
                    unit_price=first_product['unit_price'],
                    subtotal=total_subtotal,
                    tax_amount=total_tax,
                    total_amount=total_amount_after_discount,
                    amount_paid=amount_paid,
                    balance=balance,
                    created_by=self.current_user['id']
                )
                for item in self.current_products:
                    self.db_manager.add_sale_item(
                        sale_id=sale_id,
                        gas_product_id=item['product']['id'],
                        quantity=item['quantity'],
                        unit_price=item['unit_price'],
                        subtotal=item['subtotal'],
                        tax_amount=item['tax'],
                        total_amount=item['total']
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
                try:
                    from datetime import date, timedelta
                    d = date.today()
                    wd = d.weekday()
                    sat_offset = (wd - 5) % 7
                    week_start = d if wd == 5 else (d - timedelta(days=sat_offset))
                    week_end = week_start + timedelta(days=6)
                    ws = week_start.strftime('%Y-%m-%d')
                    we = week_end.strftime('%Y-%m-%d')
                    self.db_manager.upsert_weekly_invoice(current_client_id, ws, we, self.current_user.get('id'))
                except Exception:
                    pass
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
                try:
                    from PySide6.QtWidgets import QApplication
                    mw = None
                    for w in QApplication.topLevelWidgets():
                        if hasattr(w, 'refresh_dashboard'):
                            mw = w
                            break
                    if mw:
                        mw.refresh_dashboard()
                        mw.refresh_current_page("weekly_payments")
                except Exception:
                    pass
            except Exception as e:
                QMessageBox.critical(self, "Database Error", f"Failed to complete sale: {str(e)}")

    def load_recent_sales(self):
        try:
            sales = self.db_manager.get_recent_sales_with_summaries(limit=20)
            self.recent_sales_table.setRowCount(len(sales))
            for row, sale in enumerate(sales):
                self.recent_sales_table.setItem(row, 0, QTableWidgetItem(sale['created_at'][:16]))
                self.recent_sales_table.setItem(row, 1, QTableWidgetItem(sale['client_name']))
                self.recent_sales_table.setItem(row, 2, QTableWidgetItem(sale.get('product_summary') or ''))
                self.recent_sales_table.setItem(row, 3, QTableWidgetItem(sale.get('quantities_summary') or str(sale.get('quantity') or '')))
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
            from src.components.receipts import ReceiptDialog
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
                if product.get('sub_type'):
                    product_text += f" - {product['sub_type']}"
                product_text += f" - {product['capacity']}"
                self.gas_product_combo.addItem(product_text, product)
            if products:
                self.gas_product_combo.setCurrentIndex(0)
                self.on_product_selected()
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load gas products: {str(e)}")
