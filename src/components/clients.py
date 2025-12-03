from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                               QTableWidgetItem, QPushButton, QLineEdit, QLabel, 
                               QMessageBox, QDialog, QFormLayout, QDialogButtonBox,
                               QTextEdit, QComboBox, QHeaderView, QDoubleSpinBox, QSpinBox, QGroupBox)
from PySide6.QtCore import Qt, Signal
from src.database_module import DatabaseManager

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
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Form layout
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
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
        
        layout.addLayout(form_layout)

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
        self.initials_table.horizontalHeader().setStretchLastSection(True)
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
            def remove_idx(idx=i):
                if 0 <= idx < len(self.initial_entries):
                    self.initial_entries.pop(idx)
                    self.refresh_initials_table()
            btn.clicked.connect(remove_idx)
            self.initials_table.setCellWidget(i, 3, btn)

class ClientsWidget(QWidget):
    def __init__(self, db_manager: DatabaseManager, current_user: dict):
        super().__init__()
        self.db_manager = db_manager
        self.current_user = current_user
        self.init_ui()
        self.load_clients()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title_label = QLabel("Client Management")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50;")
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
        controls_layout.addWidget(self.add_client_btn)
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.load_clients)
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
        self.clients_table.horizontalHeader().setStretchLastSection(True)
        self.clients_table.setColumnWidth(0, 50)   # ID
        self.clients_table.setColumnWidth(1, 200)  # Name
        self.clients_table.setColumnWidth(2, 120)  # Phone
        self.clients_table.setColumnWidth(3, 150)  # Company
        self.clients_table.setColumnWidth(4, 120)  # Total Purchases
        self.clients_table.setColumnWidth(5, 120)  # Total Paid
        self.clients_table.setColumnWidth(6, 100)  # Balance
        self.clients_table.setColumnWidth(7, 150)  # Actions
        
        layout.addWidget(self.clients_table)
        
        # Set role-based permissions
        self.set_role_permissions()
    
    def set_role_permissions(self):
        """Set permissions based on user role"""
        role = self.current_user['role']
        
        if role == 'Driver':
            self.add_client_btn.setEnabled(False)
    
    def load_clients(self):
        """Load all clients from database"""
        try:
            clients = self.db_manager.get_clients()
            self.populate_table(clients)
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load clients: {str(e)}")
    
    def populate_table(self, clients):
        """Populate table with client data"""
        self.clients_table.setRowCount(len(clients))
        
        for row, client in enumerate(clients):
            # ID
            self.clients_table.setItem(row, 0, QTableWidgetItem(str(client['id'])))
            
            # Name
            self.clients_table.setItem(row, 1, QTableWidgetItem(client['name']))
            
            # Phone
            self.clients_table.setItem(row, 2, QTableWidgetItem(client['phone']))
            
            # Company
            self.clients_table.setItem(row, 3, QTableWidgetItem(client['company'] or ''))
            
            # Total Purchases
            purchases_item = QTableWidgetItem(f"Rs. {client['total_purchases']:,.2f}")
            purchases_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.clients_table.setItem(row, 4, purchases_item)
            
            # Total Paid
            paid_item = QTableWidgetItem(f"Rs. {client['total_paid']:,.2f}")
            paid_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.clients_table.setItem(row, 5, paid_item)
            
            # Balance
            balance_item = QTableWidgetItem(f"Rs. {client['balance']:,.2f}")
            balance_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if client['balance'] > 0:
                balance_item.setForeground(Qt.red)
            self.clients_table.setItem(row, 6, balance_item)
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setSpacing(5)
            actions_layout.setContentsMargins(5, 5, 5, 5)
            
            view_btn = QPushButton("View")
            view_btn.setStyleSheet("""
                QPushButton {
                    background-color: #17a2b8;
                    color: white;
                    border: 1px solid #138496;
                    border-radius: 4px;
                    padding: 6px 12px;
                    font-size: 12px;
                    font-weight: 500;
                    min-width: 60px;
                }
                QPushButton:hover {
                    background-color: #138496;
                    border-color: #117a8b;
                }
                QPushButton:pressed {
                    background-color: #117a8b;
                    border-color: #0c5460;
                }
            """)
            view_btn.clicked.connect(lambda checked, c=client: self.view_client(c))
            actions_layout.addWidget(view_btn)
            
            edit_btn = QPushButton("Edit")
            edit_btn.setStyleSheet("""
                QPushButton {
                    background-color: #28a745;
                    color: white;
                    border: 1px solid #1e7e34;
                    border-radius: 4px;
                    padding: 6px 12px;
                    font-size: 12px;
                    font-weight: 500;
                    min-width: 60px;
                }
                QPushButton:hover {
                    background-color: #218838;
                    border-color: #1e7e34;
                }
                QPushButton:pressed {
                    background-color: #1e7e34;
                    border-color: #155724;
                }
            """)
            edit_btn.clicked.connect(lambda checked, c=client: self.edit_client(c))
            actions_layout.addWidget(edit_btn)
            
            if self.current_user['role'] == 'Admin':
                delete_btn = QPushButton("Delete")
                delete_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #dc3545;
                        color: white;
                        border: 1px solid #bd2130;
                        border-radius: 4px;
                        padding: 6px 12px;
                        font-size: 12px;
                        font-weight: 500;
                        min-width: 60px;
                    }
                    QPushButton:hover {
                        background-color: #c82333;
                        border-color: #bd2130;
                    }
                    QPushButton:pressed {
                        background-color: #bd2130;
                        border-color: #721c24;
                    }
                """)
                delete_btn.clicked.connect(lambda checked, c=client: self.delete_client(c))
                actions_layout.addWidget(delete_btn)
            
            self.clients_table.setCellWidget(row, 7, actions_widget)
    
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
                try:
                    from PySide6.QtWidgets import QApplication
                    mw = None
                    for w in QApplication.topLevelWidgets():
                        if hasattr(w, 'refresh_dashboard'):
                            mw = w
                            break
                    if mw:
                        mw.refresh_dashboard()
                except Exception:
                    pass
                
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
                else:
                    QMessageBox.warning(self, "Error", "Failed to update client.")
                    
            except Exception as e:
                QMessageBox.critical(self, "Database Error", f"Failed to update client: {str(e)}")
    
    def view_client(self, client):
        """View client details and purchase history"""
        from PySide6.QtWidgets import QTextEdit
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Client Details - {client['name']}")
        dialog.setFixedSize(600, 500)
        
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
        
        layout.addWidget(purchases_table)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
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
                
            except Exception as e:
                QMessageBox.critical(self, "Database Error", f"Failed to delete client: {str(e)}")
