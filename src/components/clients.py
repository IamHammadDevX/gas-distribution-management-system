from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                               QTableWidgetItem, QPushButton, QLineEdit, QLabel, 
                               QMessageBox, QDialog, QFormLayout, QDialogButtonBox,
                               QTextEdit, QComboBox, QHeaderView, QDoubleSpinBox, QSpinBox, QGroupBox)
from PySide6.QtCore import Qt, Signal
from src.database_module import DatabaseManager
from src.components.ui_helpers import as_text, as_money, table_batch_update

class AddClientDialog(QDialog):
    def __init__(self, db_manager: DatabaseManager, parent=None, client_data=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.client_data = client_data
        self.setWindowTitle("Add Client" if not client_data else "Edit Client")
        self.setFixedSize(700, 520)
        self.init_ui()
        
        if client_data:
            self.load_client_data()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)
        self.resize(760, 560)

        self.setStyleSheet("""
            QDialog { background: #ffffff; }
            QLabel { color: #1f2937; font-size: 13px; }
            QGroupBox {
                font-weight: 700;
                color: #111827;
                border: 1px solid #d8dde6;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
            }
            QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {
                border: 1px solid #cfd6e4;
                border-radius: 6px;
                padding: 6px 8px;
                background: #ffffff;
                color: #111827;
                font-size: 13px;
                min-height: 34px;
                selection-background-color: #dbeafe;
                selection-color: #111827;
            }
            QTextEdit { min-height: 86px; }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
                border: 1px solid #60a5fa;
            }
            QLineEdit::placeholder, QTextEdit::placeholder {
                color: #6b7280;
            }
            QPushButton {
                border-radius: 6px;
                padding: 6px 10px;
            }
        """)

        form_group = QGroupBox("Client Information")
        form_group_layout = QVBoxLayout(form_group)
        
        # Form layout
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        form_layout.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        form_layout.setFormAlignment(Qt.AlignLeft | Qt.AlignTop)
        form_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        form_layout.setHorizontalSpacing(14)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter client name")
        form_layout.addRow("Name *:", self.name_input)
        
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Enter phone number")
        form_layout.addRow("Phone *:", self.phone_input)
        
        self.address_input = QTextEdit()
        self.address_input.setPlaceholderText("Enter address")
        self.address_input.setMaximumHeight(80)
        form_layout.addRow("Address:", self.address_input)
        
        self.company_input = QLineEdit()
        self.company_input.setPlaceholderText("Enter company name (optional)")
        form_layout.addRow("Company:", self.company_input)

        self.previous_balance_input = QDoubleSpinBox()
        self.previous_balance_input.setRange(0.0, 100000000.0)
        self.previous_balance_input.setDecimals(2)
        self.previous_balance_input.setPrefix("Rs. ")
        form_layout.addRow("Previous Balance:", self.previous_balance_input)
        
        form_group_layout.addLayout(form_layout)
        layout.addWidget(form_group)

        self.initial_entries = []
        products = self.db_manager.get_gas_products()
        gas_types = sorted(list({p['gas_type'] for p in products}))
        by_gas = {}
        for p in products:
            by_gas.setdefault(p['gas_type'], set()).add(p['capacity'])

        group = QGroupBox("Initial Outstanding Empty Cylinders")
        g_layout = QVBoxLayout(group)
        row = QHBoxLayout()
        self.gas_combo = QComboBox()
        self.gas_combo.addItems(gas_types)
        self.capacity_combo = QComboBox()
        def refresh_caps():
            gt = self.gas_combo.currentText()
            caps = sorted(list(by_gas.get(gt, set())))
            self.capacity_combo.clear()
            self.capacity_combo.addItems(caps)
        self.gas_combo.currentTextChanged.connect(refresh_caps)
        refresh_caps()
        self.qty_spin = QSpinBox()
        self.qty_spin.setRange(0, 1000)
        add_btn = QPushButton("Add")
        def add_entry():
            gt = self.gas_combo.currentText()
            cap = self.capacity_combo.currentText()
            qty = int(self.qty_spin.value())
            if qty <= 0:
                QMessageBox.warning(self, "Invalid Quantity", "Enter quantity greater than zero.")
                return
            self.initial_entries.append({'gas_type': gt, 'capacity': cap, 'quantity': qty})
            self.refresh_initials_table()
        add_btn.clicked.connect(add_entry)
        row.addWidget(QLabel("Gas"))
        row.addWidget(self.gas_combo)
        row.addWidget(QLabel("Capacity"))
        row.addWidget(self.capacity_combo)
        row.addWidget(QLabel("Qty"))
        row.addWidget(self.qty_spin)
        row.addWidget(add_btn)
        g_layout.addLayout(row)

        self.initials_table = QTableWidget()
        self.initials_table.setColumnCount(4)
        self.initials_table.setHorizontalHeaderLabels(["Gas", "Capacity", "Quantity", "Remove"])
        self.initials_table.setAlternatingRowColors(True)
        self.initials_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.initials_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.initials_table.verticalHeader().setVisible(False)
        self.initials_table.setMinimumHeight(140)
        self.initials_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.initials_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.initials_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.initials_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.initials_table.verticalHeader().setVisible(False)
        g_layout.addWidget(self.initials_table)

        layout.addWidget(group)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def load_client_data(self):
        """Load existing client data for editing"""
        self.name_input.setText(self.client_data['name'])
        self.phone_input.setText(self.client_data['phone'])
        self.address_input.setPlainText(self.client_data['address'] or '')
        self.company_input.setText(self.client_data['company'] or '')
        try:
            self.previous_balance_input.setValue(float(self.client_data.get('initial_previous_balance') or 0.0))
        except Exception:
            self.previous_balance_input.setValue(0.0)

        try:
            rows = self.db_manager.execute_query(
                '''
                SELECT gas_type, capacity, quantity
                FROM client_initial_outstanding
                WHERE client_id = ?
                ORDER BY id
                ''',
                (self.client_data['id'],)
            )
            self.initial_entries = [
                {
                    'gas_type': r.get('gas_type'),
                    'capacity': r.get('capacity'),
                    'quantity': int(r.get('quantity') or 0)
                }
                for r in rows
                if int(r.get('quantity') or 0) > 0
            ]
            self.refresh_initials_table()
        except Exception:
            self.initial_entries = []
            self.refresh_initials_table()
    
    def get_client_data(self):
        """Get client data from form"""
        return {
            'name': self.name_input.text().strip(),
            'phone': self.phone_input.text().strip(),
            'address': self.address_input.toPlainText().strip(),
            'company': self.company_input.text().strip(),
            'previous_balance': float(self.previous_balance_input.value()),
            'initial_outstanding': list(self.initial_entries)
        }
    
    def validate(self):
        """Validate form data"""
        name = self.name_input.text().strip()
        phone = self.phone_input.text().strip()
        
        if not name:
            QMessageBox.warning(self, "Validation Error", "Client name is required.")
            return False
        
        if not phone:
            QMessageBox.warning(self, "Validation Error", "Phone number is required.")
            return False
        
        return True
    
    def accept(self):
        if self.validate():
            super().accept()

    def refresh_initials_table(self):
        self.initials_table.setRowCount(len(self.initial_entries))
        for i, e in enumerate(self.initial_entries):
            self.initials_table.setItem(i, 0, QTableWidgetItem(e['gas_type']))
            self.initials_table.setItem(i, 1, QTableWidgetItem(e['capacity']))
            self.initials_table.setItem(i, 2, QTableWidgetItem(str(e['quantity'])))
            btn = QPushButton("Remove")
            btn.setMinimumWidth(90)
            btn.setStyleSheet(
                "QPushButton { background-color: #e74c3c; color: white; border: 1px solid #c0392b; border-radius: 5px; padding: 5px 8px; font-weight: 600; }"
                "QPushButton:hover { background-color: #c0392b; }"
                "QPushButton:pressed { background-color: #a93226; }"
            )
            def remove_idx(idx=i):
                if 0 <= idx < len(self.initial_entries):
                    self.initial_entries.pop(idx)
                    self.refresh_initials_table()
            btn.clicked.connect(remove_idx)
            self.initials_table.setCellWidget(i, 3, btn)
            self.initials_table.setRowHeight(i, 34)

class ClientsWidget(QWidget):
    def __init__(self, db_manager: DatabaseManager, current_user: dict):
        super().__init__()
        self.db_manager = db_manager
        self.current_user = current_user
        self.init_ui()
        self.load_clients()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        self.setStyleSheet("""
            QLabel { color: #1e293b; }
            QLineEdit {
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 6px 8px;
                min-height: 30px;
                background: #ffffff;
            }
            QLineEdit:focus { border: 1px solid #2563eb; }
            QTableWidget {
                border: 1px solid #dbe4f0;
                border-radius: 8px;
                background: #ffffff;
                gridline-color: #e5e7eb;
            }
            QTableWidget::item { padding: 6px; }
            QTableWidget::item:selected { background-color: #e6f0ff; color: #0f172a; }
            QHeaderView::section {
                background-color: #2563eb;
                color: white;
                border: none;
                padding: 8px;
                font-weight: 700;
            }
        """)
        
        title_label = QLabel("Client Management")
        title_label.setStyleSheet("font-size: 22px; font-weight: 700; color: #1e3a8a;")
        layout.addWidget(title_label)
        
        # Search and controls
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(10)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by name, phone, or company...")
        self.search_input.textChanged.connect(self.filter_clients)
        controls_layout.addWidget(self.search_input)
        
        self.add_client_btn = QPushButton("Add New Client")
        self.add_client_btn.clicked.connect(self.add_client)
        self.add_client_btn.setStyleSheet("""
            QPushButton {
                background-color: #16a34a;
                color: white;
                border: 1px solid #15803d;
                border-radius: 6px;
                padding: 6px 12px;
                min-height: 30px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #15803d; }
        """)
        controls_layout.addWidget(self.add_client_btn)
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.load_clients)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #0ea5e9;
                color: white;
                border: 1px solid #0284c7;
                border-radius: 6px;
                padding: 6px 12px;
                min-height: 30px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #0284c7; }
        """)
        controls_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(controls_layout)
        
        # Clients table
        self.clients_table = QTableWidget()
        self.clients_table.setColumnCount(8)
        self.clients_table.setHorizontalHeaderLabels([
            "ID", "Name", "Phone", "Company", "Total Purchases", "Total Paid", "Balance", "Actions"
        ])
        
        # Configure table
        self.clients_table.setAlternatingRowColors(True)
        self.clients_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.clients_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.clients_table.setFocusPolicy(Qt.NoFocus)
        self.clients_table.verticalHeader().setVisible(False)
        self.clients_table.setShowGrid(True)
        self.clients_table.setWordWrap(False)
        self.clients_table.horizontalHeader().setStretchLastSection(False)
        self.clients_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.clients_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.clients_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.clients_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.clients_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.clients_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.clients_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.clients_table.horizontalHeader().setSectionResizeMode(7, QHeaderView.Fixed)
        self.clients_table.setColumnWidth(0, 50)   # ID
        self.clients_table.setColumnWidth(1, 200)  # Name
        self.clients_table.setColumnWidth(2, 120)  # Phone
        self.clients_table.setColumnWidth(3, 150)  # Company
        self.clients_table.setColumnWidth(4, 120)  # Total Purchases
        self.clients_table.setColumnWidth(5, 120)  # Total Paid
        self.clients_table.setColumnWidth(6, 100)  # Balance
        self.clients_table.setColumnWidth(7, 225)  # Actions
        
        layout.addWidget(self.clients_table)
        
        # Set role-based permissions
        self.set_role_permissions()
    
    def set_role_permissions(self):
        """Set permissions based on user role"""
        role = self.current_user['role']
        
        if role == 'Driver':
            self.add_client_btn.setEnabled(False)

    def _refresh_application_after_client_change(self):
        """Refresh all dependent pages so client balance/cylinder changes are visible immediately."""
        try:
            from PySide6.QtWidgets import QApplication

            main_window = None
            for widget in QApplication.topLevelWidgets():
                if hasattr(widget, 'widgets') and hasattr(widget, 'refresh_current_page'):
                    main_window = widget
                    break

            if not main_window:
                return

            # Dashboard aggregates and every dependent page should update immediately.
            main_window.refresh_dashboard()
            for page_name in [
                "clients",
                "cylinder_track",
                "cylinder_availability",
                "weekly_payments",
                "receipts",
                "daily_transactions",
            ]:
                try:
                    main_window.refresh_current_page(page_name)
                except Exception:
                    continue

            # Reports page does not expose refresh_current_page hook; force regenerate if loaded.
            reports_widget = main_window.widgets.get("reports") if hasattr(main_window, 'widgets') else None
            if reports_widget and hasattr(reports_widget, 'generate_report'):
                try:
                    reports_widget.generate_report()
                except Exception:
                    pass

            # Keep sales client panel consistent if currently selected.
            sales_widget = main_window.widgets.get("sales") if hasattr(main_window, 'widgets') else None
            if sales_widget and hasattr(sales_widget, 'on_client_selected'):
                try:
                    sales_widget.on_client_selected()
                except Exception:
                    pass
        except Exception:
            pass
    
    def load_clients(self):
        """Load all clients from database"""
        try:
            clients = self.db_manager.get_clients()
            self.populate_table(clients)
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load clients: {str(e)}")
    
    def populate_table(self, clients):
        """Populate table with client data"""
        with table_batch_update(self.clients_table):
            self.clients_table.setRowCount(len(clients))

            for row, client in enumerate(clients):
                self.clients_table.setItem(row, 0, QTableWidgetItem(as_text(client.get('id'))))
                self.clients_table.setItem(row, 1, QTableWidgetItem(as_text(client.get('name'))))
                self.clients_table.setItem(row, 2, QTableWidgetItem(as_text(client.get('phone'))))
                self.clients_table.setItem(row, 3, QTableWidgetItem(as_text(client.get('company') or '')))

                purchases_item = QTableWidgetItem(as_money(client.get('total_purchases')))
                purchases_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.clients_table.setItem(row, 4, purchases_item)

                paid_item = QTableWidgetItem(as_money(client.get('total_paid')))
                paid_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.clients_table.setItem(row, 5, paid_item)

                balance_value = float(client.get('balance') or 0)
                balance_item = QTableWidgetItem(as_money(balance_value))
                balance_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if balance_value > 0:
                    balance_item.setForeground(Qt.red)
                self.clients_table.setItem(row, 6, balance_item)
            
                actions_widget = QWidget()
                actions_widget.setMinimumHeight(32)
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setSpacing(4)
                actions_layout.setContentsMargins(2, 2, 2, 2)
                actions_layout.setAlignment(Qt.AlignCenter)

                view_btn = QPushButton("View")
                view_btn.setMinimumWidth(58)
                view_btn.setMaximumWidth(66)
                view_btn.setFixedHeight(24)
                view_btn.setFocusPolicy(Qt.NoFocus)
                view_btn.setStyleSheet("""
                    QPushButton { background-color: #17a2b8; color: white; border: 1px solid #138496; border-radius: 5px; padding: 3px 8px; font-size: 11px; font-weight: 600; }
                    QPushButton:hover { background-color: #138496; }
                    QPushButton:pressed { background-color: #117a8b; }
                """)
                view_btn.clicked.connect(lambda checked, c=client: self.view_client(c))
                actions_layout.addWidget(view_btn)
            
                edit_btn = QPushButton("Edit")
                edit_btn.setMinimumWidth(58)
                edit_btn.setMaximumWidth(66)
                edit_btn.setFixedHeight(24)
                edit_btn.setFocusPolicy(Qt.NoFocus)
                edit_btn.setStyleSheet("""
                    QPushButton { background-color: #28a745; color: white; border: 1px solid #1e7e34; border-radius: 5px; padding: 3px 8px; font-size: 11px; font-weight: 600; }
                    QPushButton:hover { background-color: #218838; }
                    QPushButton:pressed { background-color: #1e7e34; }
                """)
                edit_btn.clicked.connect(lambda checked, c=client: self.edit_client(c))
                actions_layout.addWidget(edit_btn)
            
                if self.current_user['role'] == 'Admin':
                    delete_btn = QPushButton("Delete")
                    delete_btn.setMinimumWidth(58)
                    delete_btn.setMaximumWidth(66)
                    delete_btn.setFixedHeight(24)
                    delete_btn.setFocusPolicy(Qt.NoFocus)
                    delete_btn.setStyleSheet("""
                        QPushButton { background-color: #dc3545; color: white; border: 1px solid #bd2130; border-radius: 5px; padding: 3px 8px; font-size: 11px; font-weight: 600; }
                        QPushButton:hover { background-color: #c82333; }
                        QPushButton:pressed { background-color: #bd2130; }
                    """)
                    delete_btn.clicked.connect(lambda checked, c=client: self.delete_client(c))
                    actions_layout.addWidget(delete_btn)

                actions_layout.addStretch()

                self.clients_table.setCellWidget(row, 7, actions_widget)
                self.clients_table.setRowHeight(row, 40)
    
    def filter_clients(self):
        """Filter clients based on search input"""
        search_text = self.search_input.text().strip()
        try:
            clients = self.db_manager.get_clients(search_text)
            self.populate_table(clients)
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to filter clients: {str(e)}")
    
    def add_client(self):
        """Add new client"""
        dialog = AddClientDialog(self.db_manager, self)
        if dialog.exec() == QDialog.Accepted:
            try:
                client_data = dialog.get_client_data()
                client_id = self.db_manager.add_client(
                    client_data['name'],
                    client_data['phone'],
                    client_data['address'],
                    client_data['company'],
                    client_data.get('previous_balance') or 0.0
                )
                initials = client_data.get('initial_outstanding') or []
                for e in initials:
                    try:
                        self.db_manager.add_client_initial_outstanding(client_id, e['gas_type'], e['capacity'], int(e['quantity']))
                    except Exception:
                        continue
                
                self.db_manager.log_activity(
                    "ADD_CLIENT",
                    f"Added new client: {client_data['name']}",
                    self.current_user['id']
                )
                
                QMessageBox.information(self, "Success", "Client added successfully!")
                self.load_clients()
                self._refresh_application_after_client_change()

            except Exception as e:
                QMessageBox.critical(self, "Database Error", f"Failed to add client: {str(e)}")
    
    def edit_client(self, client):
        """Edit existing client"""
        dialog = AddClientDialog(self.db_manager, self, client)
        if dialog.exec() == QDialog.Accepted:
            try:
                client_data = dialog.get_client_data()
                success = self.db_manager.update_client(
                    client['id'],
                    client_data['name'],
                    client_data['phone'],
                    client_data['address'],
                    client_data['company'],
                    client_data.get('previous_balance')
                )
                
                if success:
                    self.db_manager.log_activity(
                        "EDIT_CLIENT",
                        f"Updated client: {client_data['name']}",
                        self.current_user['id']
                    )
                    
                    QMessageBox.information(self, "Success", "Client updated successfully!")
                    self.load_clients()
                    self._refresh_application_after_client_change()
                else:
                    QMessageBox.warning(self, "Error", "Failed to update client.")
                    
            except Exception as e:
                QMessageBox.critical(self, "Database Error", f"Failed to update client: {str(e)}")
    
    def view_client(self, client):
        """View client details and purchase history"""
        from PySide6.QtWidgets import QTextEdit
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Client Details - {client['name']}")
        dialog.setMinimumSize(900, 620)
        dialog.resize(980, 700)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Client details
        details_text = f"""
<b>Client Information:</b><br>
Name: {client['name']}<br>
Phone: {client['phone']}<br>
Address: {client['address'] or 'N/A'}<br>
Company: {client['company'] or 'N/A'}<br>
<br>
<b>Financial Summary:</b><br>
Total Purchases: Rs. {client['total_purchases']:,.2f}<br>
Total Paid: Rs. {client['total_paid']:,.2f}<br>
Outstanding Balance: Rs. {client['balance']:,.2f}<br>
        """
        
        details_edit = QTextEdit()
        details_edit.setHtml(details_text)
        details_edit.setReadOnly(True)
        details_edit.setMaximumHeight(150)
        layout.addWidget(details_edit)
        
        # Recent purchases
        layout.addWidget(QLabel("<b>Recent Purchases:</b>"))
        
        purchases_table = QTableWidget()
        purchases_table.setColumnCount(6)
        purchases_table.setHorizontalHeaderLabels([
            "Date", "Products", "Quantities", "Unit Price", "Total", "Balance"
        ])
        purchases_table.setAlternatingRowColors(True)
        purchases_table.setSelectionBehavior(QTableWidget.SelectRows)
        purchases_table.setEditTriggers(QTableWidget.NoEditTriggers)
        purchases_table.verticalHeader().setVisible(False)
        purchases_table.setMinimumHeight(180)
        p_header = purchases_table.horizontalHeader()
        p_header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        p_header.setSectionResizeMode(1, QHeaderView.Stretch)
        p_header.setSectionResizeMode(2, QHeaderView.Stretch)
        p_header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        p_header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        p_header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        
        # Load recent purchases for this client
        try:
            purchases = self.db_manager.get_client_purchases_with_summaries(client['id'], limit=10)
            
            purchases_table.setRowCount(len(purchases))
            for row, purchase in enumerate(purchases):
                purchases_table.setItem(row, 0, QTableWidgetItem(purchase['created_at'][:10]))
                purchases_table.setItem(row, 1, QTableWidgetItem(purchase.get('product_summary') or ''))
                purchases_table.setItem(row, 2, QTableWidgetItem(purchase.get('quantities_summary') or str(purchase.get('quantity') or '')))
                purchases_table.setItem(row, 3, QTableWidgetItem(f"Rs. {purchase['unit_price']:,.2f}"))
                purchases_table.setItem(row, 4, QTableWidgetItem(f"Rs. {purchase['total_amount']:,.2f}"))
                purchases_table.setItem(row, 5, QTableWidgetItem(f"Rs. {purchase['balance']:,.2f}"))
            
            purchases_table.resizeColumnsToContents()
            
        except Exception as e:
            QMessageBox.warning(self, "Database Error", f"Failed to load purchase history: {str(e)}")
        
        layout.addWidget(purchases_table, 1)
        layout.addWidget(QLabel("<b>Pending Cylinders Summary:</b>"))
        cyl_table = QTableWidget()
        cyl_table.setColumnCount(6)
        cyl_table.setHorizontalHeaderLabels(["Product", "Capacity", "Delivered", "Returned", "Pending", "Status"])
        cyl_table.setAlternatingRowColors(True)
        cyl_table.setSelectionBehavior(QTableWidget.SelectRows)
        cyl_table.setEditTriggers(QTableWidget.NoEditTriggers)
        cyl_table.verticalHeader().setVisible(False)
        cyl_table.setMinimumHeight(180)
        c_header = cyl_table.horizontalHeader()
        c_header.setSectionResizeMode(0, QHeaderView.Stretch)
        c_header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        c_header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        c_header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        c_header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        c_header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        try:
            rows = self.db_manager.get_client_cylinder_status(client['id'])
            cyl_table.setRowCount(len(rows))
            for i, r in enumerate(rows):
                prod_name = f"{r['gas_type']}{(' ' + r['sub_type']) if r.get('sub_type') else ''}"
                cyl_table.setItem(i, 0, QTableWidgetItem(prod_name))
                cyl_table.setItem(i, 1, QTableWidgetItem(r['capacity']))
                cyl_table.setItem(i, 2, QTableWidgetItem(str(int(r['delivered']))))
                cyl_table.setItem(i, 3, QTableWidgetItem(str(int(r['returned']))))
                cyl_table.setItem(i, 4, QTableWidgetItem(str(int(r['pending']))))
                status = 'Done' if int(r['pending']) <= 0 else 'Pending'
                cyl_table.setItem(i, 5, QTableWidgetItem(status))
            cyl_table.resizeColumnsToContents()
        except Exception:
            pass
        layout.addWidget(cyl_table, 2)
        
        dialog.exec()
    
    def delete_client(self, client):
        """Delete client (Admin only)"""
        if self.current_user['role'] != 'Admin':
            QMessageBox.warning(self, "Permission Denied", "Only administrators can delete clients.")
            return
        
        reply = QMessageBox.question(
            self,
            "Delete Client",
            f"Are you sure you want to delete client '{client['name']}'?\n\n"
            "This action cannot be undone and will affect all related transactions.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Check if client has any sales
                query = 'SELECT COUNT(*) as count FROM sales WHERE client_id = ?'
                result = self.db_manager.execute_query(query, (client['id'],))
                sales_count = result[0]['count'] if result else 0
                
                if sales_count > 0:
                    QMessageBox.warning(
                        self,
                        "Cannot Delete",
                        f"Cannot delete client '{client['name']}' because they have {sales_count} sales transactions."
                    )
                    return
                
                # Delete client
                query = 'DELETE FROM clients WHERE id = ?'
                self.db_manager.execute_update(query, (client['id'],))
                
                self.db_manager.log_activity(
                    "DELETE_CLIENT",
                    f"Deleted client: {client['name']}",
                    self.current_user['id']
                )
                
                QMessageBox.information(self, "Success", "Client deleted successfully!")
                self.load_clients()
                self._refresh_application_after_client_change()
                
            except Exception as e:
                QMessageBox.critical(self, "Database Error", f"Failed to delete client: {str(e)}")
