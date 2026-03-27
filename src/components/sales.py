from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QSpinBox, QDoubleSpinBox, QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QInputDialog, QCheckBox, QFrame, QGridLayout, QHeaderView,
    QAbstractItemView, QScrollArea, QFormLayout
)
from PySide6.QtCore import Qt
from src.database_module import DatabaseManager
from src.components.ui_helpers import as_datetime_text, as_money, as_text, table_batch_update

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
        self.setStyleSheet("""
            QWidget { background-color: #f5f6f8; color: #1f2937; font-size: 13px; }
            QLabel#titleLabel { font-size: 24px; font-weight: 700; color: #1f4f82; }
            QFrame#sectionCard { background: #ffffff; border: 1px solid #dbe1e7; border-radius: 10px; }
            QLabel#sectionLabel { font-size: 15px; font-weight: 700; color: #1f2937; }
            QLabel#hintLabel { color: #4b5563; }
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
                background: #ffffff;
                border: 1px solid #cfd7df;
                border-radius: 6px;
                padding: 6px 8px;
                min-height: 30px;
            }
            QTableWidget { background: #ffffff; border: 1px solid #d7dde3; border-radius: 8px; }
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

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(10, 10, 10, 10)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        root_layout.addWidget(scroll)

        container = QWidget()
        scroll.setWidget(container)

        layout = QVBoxLayout(container)
        layout.setSpacing(10)
        layout.setContentsMargins(6, 6, 6, 6)

        title_label = QLabel("Sales & Billing")
        title_label.setObjectName("titleLabel")
        layout.addWidget(title_label)

        client_card, client_layout = self._create_section_card("Client")
        client_row = QHBoxLayout()
        client_row.setSpacing(8)
        self.client_search_input = QLineEdit()
        self.client_search_input.setPlaceholderText("Search client by name, phone, or company...")
        self.client_search_input.textChanged.connect(self.search_clients)
        self.client_combo = QComboBox()
        self.client_combo.currentIndexChanged.connect(self.on_client_selected)
        client_row.addWidget(self.client_search_input, 2)
        client_row.addWidget(self.client_combo, 1)
        client_layout.addLayout(client_row)
        self.client_info_label = QLabel("No client selected")
        self.client_info_label.setObjectName("hintLabel")
        self.client_info_label.setWordWrap(True)
        client_layout.addWidget(self.client_info_label)
        layout.addWidget(client_card)

        product_card, product_layout = self._create_section_card("Product Entry")
        product_form = QFormLayout()
        product_form.setLabelAlignment(Qt.AlignLeft)
        product_form.setFormAlignment(Qt.AlignLeft)
        product_form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        product_form.setHorizontalSpacing(12)
        product_form.setVerticalSpacing(8)

        self.gas_product_combo = QComboBox()
        self.gas_product_combo.currentIndexChanged.connect(self.on_product_selected)
        product_form.addRow("Product:", self.gas_product_combo)

        self.quantity_spinbox = QSpinBox()
        self.quantity_spinbox.setRange(1, 1000)
        self.quantity_spinbox.setValue(1)
        self.quantity_spinbox.valueChanged.connect(self.calculate_totals)
        product_form.addRow("Quantity:", self.quantity_spinbox)

        self.unit_price_spinbox = QDoubleSpinBox()
        self.unit_price_spinbox.setRange(0, 1000000)
        self.unit_price_spinbox.setDecimals(2)
        self.unit_price_spinbox.setPrefix("Rs. ")
        self.unit_price_spinbox.setSingleStep(100)
        self.unit_price_spinbox.valueChanged.connect(self.calculate_totals)
        product_form.addRow("Unit Price:", self.unit_price_spinbox)

        self.line_discount_spinbox = QDoubleSpinBox()
        self.line_discount_spinbox.setRange(0, 100000000)
        self.line_discount_spinbox.setDecimals(2)
        self.line_discount_spinbox.setPrefix("Rs. ")
        self.line_discount_spinbox.setSingleStep(50)
        self.line_discount_spinbox.valueChanged.connect(self.calculate_totals)
        product_form.addRow("Discount:", self.line_discount_spinbox)

        self.product_tax_spinbox = QDoubleSpinBox()
        self.product_tax_spinbox.setRange(0.0, 100.0)
        self.product_tax_spinbox.setDecimals(2)
        self.product_tax_spinbox.setSuffix(" %")
        self.product_tax_spinbox.setSingleStep(0.5)
        self.product_tax_spinbox.valueChanged.connect(self.calculate_totals)
        product_form.addRow("Tax Rate:", self.product_tax_spinbox)
        product_layout.addLayout(product_form)

        line_totals = QHBoxLayout()
        line_totals.setSpacing(10)
        self.subtotal_label = QLabel("Rs. 0.00")
        self.tax_label = QLabel("Rs. 0.00")
        self.total_label = QLabel("Rs. 0.00")
        self.subtotal_label.setStyleSheet("font-weight: 700;")
        self.tax_label.setStyleSheet("font-weight: 700;")
        self.total_label.setStyleSheet("font-weight: 700;")
        line_totals.addWidget(QLabel("Line Subtotal:"))
        line_totals.addWidget(self.subtotal_label)
        line_totals.addSpacing(8)
        line_totals.addWidget(QLabel("Tax:"))
        line_totals.addWidget(self.tax_label)
        line_totals.addSpacing(8)
        line_totals.addWidget(QLabel("Line Total:"))
        line_totals.addWidget(self.total_label)
        line_totals.addStretch(1)
        product_layout.addLayout(line_totals)

        product_buttons = QHBoxLayout()
        product_buttons.setSpacing(8)
        add_btn = self._create_action_button("Add to Cart", "success")
        add_btn.clicked.connect(self.add_to_cart)
        clear_btn = self._create_action_button("Clear", "secondary")
        clear_btn.clicked.connect(self.clear_form)
        product_buttons.addStretch(1)
        product_buttons.addWidget(add_btn)
        product_buttons.addWidget(clear_btn)
        product_layout.addLayout(product_buttons)
        layout.addWidget(product_card)

        cart_card, cart_layout = self._create_section_card("Cart")
        self.cart_table = QTableWidget()
        self.cart_table.setColumnCount(8)
        self.cart_table.setHorizontalHeaderLabels([
            "Products", "Quantity", "Unit Price", "Discount", "Tax (%)", "Subtotal", "Tax", "Total"
        ])
        self._setup_table(self.cart_table, min_height=170)
        cart_layout.addWidget(self.cart_table)

        cart_buttons = QHBoxLayout()
        cart_buttons.setSpacing(8)
        remove_btn = self._create_action_button("Remove Selected", "danger")
        remove_btn.clicked.connect(self.remove_from_cart)
        clear_cart_btn = self._create_action_button("Clear Cart", "danger")
        clear_cart_btn.clicked.connect(self.clear_cart)
        clear_all_btn = self._create_action_button("Cancel Sale / Clear All", "danger")
        clear_all_btn.clicked.connect(self.clear_all_sale)
        cart_buttons.addWidget(remove_btn)
        cart_buttons.addWidget(clear_cart_btn)
        cart_buttons.addWidget(clear_all_btn)
        cart_buttons.addStretch(1)
        cart_layout.addLayout(cart_buttons)
        layout.addWidget(cart_card)

        payment_card, payment_layout = self._create_section_card("Payment")
        payment_form = QFormLayout()
        payment_form.setLabelAlignment(Qt.AlignLeft)
        payment_form.setFormAlignment(Qt.AlignLeft)
        payment_form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        payment_form.setHorizontalSpacing(12)
        payment_form.setVerticalSpacing(8)

        self.cart_total_label = QLabel("Rs. 0.00")
        self.cart_tax_label = QLabel("Rs. 0.00")
        self.balance_label = QLabel("Rs. 0.00")
        self.balance_label.setStyleSheet("font-weight: bold; color: #27ae60;")

        self.overall_discount_spinbox = QDoubleSpinBox()
        self.overall_discount_spinbox.setRange(0, 100000000)
        self.overall_discount_spinbox.setDecimals(2)
        self.overall_discount_spinbox.setPrefix("Rs. ")
        self.overall_discount_spinbox.valueChanged.connect(self.calculate_balance)

        self.amount_paid_spinbox = QDoubleSpinBox()
        self.amount_paid_spinbox.setRange(0, 100000000)
        self.amount_paid_spinbox.setDecimals(2)
        self.amount_paid_spinbox.setPrefix("Rs. ")
        self.amount_paid_spinbox.valueChanged.connect(self.calculate_balance)

        payment_form.addRow("Cart Total:", self.cart_total_label)
        payment_form.addRow("Cart Tax:", self.cart_tax_label)
        payment_form.addRow("Overall Discount:", self.overall_discount_spinbox)
        payment_form.addRow("Amount Paid:", self.amount_paid_spinbox)
        payment_form.addRow("Balance:", self.balance_label)
        payment_layout.addLayout(payment_form)

        payment_buttons = QHBoxLayout()
        payment_buttons.setSpacing(8)
        payment_buttons.addStretch(1)
        full_pay_btn = self._create_action_button("Full", "primary")
        full_pay_btn.clicked.connect(self.set_full_payment)
        clear_pay_btn = self._create_action_button("Clear", "secondary")
        clear_pay_btn.clicked.connect(self.clear_payment)
        complete_btn = self._create_action_button("Confirm", "success")
        complete_btn.clicked.connect(self.complete_sale)
        payment_buttons.addWidget(full_pay_btn)
        payment_buttons.addWidget(clear_pay_btn)
        payment_buttons.addWidget(complete_btn)
        payment_layout.addLayout(payment_buttons)
        layout.addWidget(payment_card)

        recent_card, recent_layout = self._create_section_card("Recent Sales")
        self.recent_sales_table = QTableWidget()
        self.recent_sales_table.setColumnCount(8)
        self.recent_sales_table.setHorizontalHeaderLabels([
            "Date", "Client", "Products", "Quantities", "Total", "Paid", "Balance", "Actions"
        ])
        self._setup_table(self.recent_sales_table, min_height=170)
        self.recent_sales_table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeToContents)
        self.recent_sales_table.setColumnWidth(7, 150)
        recent_layout.addWidget(self.recent_sales_table)
        layout.addWidget(recent_card)

    def _create_section_card(self, title: str):
        card = QFrame()
        card.setObjectName("sectionCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 12, 12, 12)
        card_layout.setSpacing(10)

        heading = QLabel(title)
        heading.setObjectName("sectionLabel")
        card_layout.addWidget(heading)
        return card, card_layout

    def _create_action_button(self, text: str, kind: str = "secondary"):
        button = QPushButton(text)
        button.setMinimumHeight(34)

        styles = {
            "primary": (
                "QPushButton { background-color: #1a73e8; color: white; border: 1px solid #125bc4; border-radius: 6px; padding: 6px 12px; font-weight: 600; }"
                "QPushButton:hover { background-color: #1765cb; }"
                "QPushButton:pressed { background-color: #125bc4; }"
            ),
            "success": (
                "QPushButton { background-color: #28a745; color: white; border: 1px solid #1f8a3a; border-radius: 6px; padding: 6px 12px; font-weight: 600; }"
                "QPushButton:hover { background-color: #228d3d; }"
                "QPushButton:pressed { background-color: #1f8a3a; }"
            ),
            "danger": (
                "QPushButton { background-color: #dc3545; color: white; border: 1px solid #b52a37; border-radius: 6px; padding: 6px 12px; font-weight: 600; }"
                "QPushButton:hover { background-color: #c22f3d; }"
                "QPushButton:pressed { background-color: #b52a37; }"
            ),
            "secondary": (
                "QPushButton { background-color: #6c757d; color: white; border: 1px solid #596168; border-radius: 6px; padding: 6px 12px; font-weight: 600; }"
                "QPushButton:hover { background-color: #5e666d; }"
                "QPushButton:pressed { background-color: #535a61; }"
            ),
        }
        button.setStyleSheet(styles.get(kind, styles["secondary"]))
        return button

    def _setup_table(self, table: QTableWidget, min_height: int = 160):
        table.setAlternatingRowColors(True)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.setWordWrap(True)
        table.setMinimumHeight(min_height)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.horizontalHeader().setMinimumSectionSize(90)
        table.verticalHeader().setDefaultSectionSize(34)

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
                        mw.refresh_current_page("cylinder_availability")
                except Exception:
                    pass
            except Exception as e:
                QMessageBox.critical(self, "Database Error", f"Failed to complete sale: {str(e)}")

    def load_recent_sales(self):
        try:
            sales = self.db_manager.get_recent_sales_with_summaries(limit=20)
            with table_batch_update(self.recent_sales_table):
                self.recent_sales_table.setRowCount(len(sales))
                for row, sale in enumerate(sales):
                    self.recent_sales_table.setItem(row, 0, QTableWidgetItem(as_datetime_text(sale.get('created_at'), 16)))
                    self.recent_sales_table.setItem(row, 1, QTableWidgetItem(as_text(sale.get('client_name'))))
                    self.recent_sales_table.setItem(row, 2, QTableWidgetItem(as_text(sale.get('product_summary') or '')))
                    self.recent_sales_table.setItem(row, 3, QTableWidgetItem(as_text(sale.get('quantities_summary') or sale.get('quantity') or '')))
                    self.recent_sales_table.setItem(row, 4, QTableWidgetItem(as_money(sale.get('total_amount'))))
                    self.recent_sales_table.setItem(row, 5, QTableWidgetItem(as_money(sale.get('amount_paid'))))
                    self.recent_sales_table.setItem(row, 6, QTableWidgetItem(as_money(sale.get('balance'))))

                    balance_value = float(sale.get('balance') or 0)
                    if balance_value > 0:
                        self.recent_sales_table.item(row, 6).setForeground(Qt.red)
                    elif balance_value < 0:
                        self.recent_sales_table.item(row, 6).setForeground(Qt.darkYellow)
                    else:
                        self.recent_sales_table.item(row, 6).setForeground(Qt.darkGreen)

                    generate_btn = QPushButton("Generate Receipt")
                    generate_btn.setMinimumHeight(30)
                    generate_btn.setMinimumWidth(130)
                    generate_btn.setFocusPolicy(Qt.NoFocus)
                    generate_btn.setStyleSheet(
                        "QPushButton { background-color: #1a73e8; color: white; border: 1px solid #125bc4; border-radius: 6px; padding: 6px 10px; font-weight: 600; }"
                        "QPushButton:hover { background-color: #1765cb; }"
                        "QPushButton:pressed { background-color: #125bc4; }"
                        "QPushButton:focus { outline: none; }"
                    )
                    generate_btn.clicked.connect(lambda checked, s=sale: self.generate_receipt_for_sale(s))
                    self.recent_sales_table.setCellWidget(row, 7, generate_btn)
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