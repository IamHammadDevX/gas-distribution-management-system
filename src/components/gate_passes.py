from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                               QTableWidgetItem, QPushButton, QLineEdit, QLabel, 
                               QMessageBox, QDialog, QFormLayout, QDialogButtonBox,
                               QComboBox, QSpinBox, QGroupBox, QTextEdit, QHeaderView,
                               QDateTimeEdit, QCheckBox)
from PySide6.QtCore import Qt, QDateTime, QTimer
from database_module import DatabaseManager
from datetime import datetime

class GatePassDialog(QDialog):
    def __init__(self, db_manager: DatabaseManager, current_user: dict, parent=None, gate_pass_data=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.current_user = current_user
        self.gate_pass_data = gate_pass_data
        self.setWindowTitle("Create Gate Pass" if not gate_pass_data else "Edit Gate Pass" if self.is_editable() else "View Gate Pass")
        self.setFixedSize(600, 500)
        self.init_ui()
        
        if gate_pass_data:
            self.load_gate_pass_data()
            if not self.is_editable():
                self.set_read_only()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title_label = QLabel("Gate Pass")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title_label)
        
        # Form layout
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        # Gate Pass Number (auto-generated)
        self.gate_pass_number_label = QLabel("Auto-generated")
        form_layout.addRow("Gate Pass #:", self.gate_pass_number_label)
        
        # Receipt search
        self.receipt_search_input = QLineEdit()
        self.receipt_search_input.setPlaceholderText("Enter receipt number...")
        self.receipt_search_input.textChanged.connect(self.search_receipts)
        form_layout.addRow("Receipt # *:", self.receipt_search_input)
        
        # Receipt info
        self.receipt_info_label = QLabel("No receipt selected")
        self.receipt_info_label.setStyleSheet("color: #666; font-style: italic;")
        form_layout.addRow("Receipt Info:", self.receipt_info_label)
        
        # Client info (auto-filled from receipt)
        self.client_info_label = QLabel("Client info will appear here")
        self.client_info_label.setStyleSheet("color: #666; font-style: italic;")
        form_layout.addRow("Client Info:", self.client_info_label)
        
        # Driver name
        self.driver_name_input = QLineEdit()
        self.driver_name_input.setPlaceholderText("Enter driver name")
        form_layout.addRow("Driver Name *:", self.driver_name_input)
        
        # Vehicle number
        self.vehicle_number_input = QLineEdit()
        self.vehicle_number_input.setPlaceholderText("Enter vehicle number (e.g., ABC-123)")
        form_layout.addRow("Vehicle Number *:", self.vehicle_number_input)
        
        # Gas type and capacity (auto-filled from receipt)
        self.gas_info_label = QLabel("Gas information will appear here")
        self.gas_info_label.setStyleSheet("color: #666; font-style: italic;")
        form_layout.addRow("Gas Info:", self.gas_info_label)
        
        # Quantity
        self.quantity_spinbox = QSpinBox()
        self.quantity_spinbox.setRange(1, 100)
        self.quantity_spinbox.setValue(1)
        form_layout.addRow("Quantity *:", self.quantity_spinbox)
        
        # Time out
        self.time_out_datetime = QDateTimeEdit()
        self.time_out_datetime.setDateTime(QDateTime.currentDateTime())
        self.time_out_datetime.setDisplayFormat("yyyy-MM-dd hh:mm")
        form_layout.addRow("Time Out:", self.time_out_datetime)
        
        # Time in (for viewing/editing existing gate passes)
        self.time_in_datetime = QDateTimeEdit()
        self.time_in_datetime.setDisplayFormat("yyyy-MM-dd hh:mm")
        self.time_in_checkbox = QCheckBox("Mark as returned")
        self.time_in_checkbox.toggled.connect(self.on_time_in_toggled)
        
        time_in_layout = QHBoxLayout()
        time_in_layout.addWidget(self.time_in_checkbox)
        time_in_layout.addWidget(self.time_in_datetime)
        self.time_in_datetime.setEnabled(False)
        
        form_layout.addRow("Time In:", time_in_layout)

        # Expected return time
        self.expected_in_datetime = QDateTimeEdit()
        self.expected_in_datetime.setDisplayFormat("yyyy-MM-dd hh:mm")
        self.expected_in_datetime.setDateTime(QDateTime.currentDateTime())
        form_layout.addRow("Expected Return:", self.expected_in_datetime)
        
        # Gate operator
        self.operator_label = QLabel(f"{self.current_user['full_name']}")
        form_layout.addRow("Gate Operator:", self.operator_label)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def on_time_in_toggled(self, checked):
        """Handle time in checkbox toggle"""
        self.time_in_datetime.setEnabled(checked)
        if checked:
            self.time_in_datetime.setDateTime(QDateTime.currentDateTime())
    
    def search_receipts(self):
        """Search receipts as user types"""
        search_text = self.receipt_search_input.text().strip()
        if len(search_text) < 3:  # Only search if at least 3 characters
            return
        
        try:
            query = '''
                SELECT r.*, c.name as client_name, c.phone as client_phone,
                       gp.gas_type, gp.sub_type, gp.capacity, s.quantity, s.total_amount
                FROM receipts r
                JOIN clients c ON r.client_id = c.id
                JOIN sales s ON r.sale_id = s.id
                JOIN gas_products gp ON s.gas_product_id = gp.id
                WHERE LOWER(r.receipt_number) LIKE ? AND r.balance = 0
                ORDER BY r.created_at DESC
                LIMIT 10
            '''
            search_pattern = f"%{search_text.lower()}%"
            receipts = self.db_manager.execute_query(query, (search_pattern,))
            
            if receipts:
                self.current_receipt = receipts[0]
                self.update_receipt_info()
            else:
                self.receipt_info_label.setText("No valid receipt found")
                self.client_info_label.setText("Client info will appear here")
                self.gas_info_label.setText("Gas information will appear here")
                self.current_receipt = None
                
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to search receipts: {str(e)}")
    
    def update_receipt_info(self):
        """Update receipt information display"""
        if self.current_receipt:
            receipt_info = f"Receipt: {self.current_receipt['receipt_number']}"
            receipt_info += f"\nDate: {self.current_receipt['created_at'][:10]}"
            receipt_info += f"\nAmount: Rs. {self.current_receipt['total_amount']:,.2f}"
            self.receipt_info_label.setText(receipt_info)
            
            client_info = f"Name: {self.current_receipt['client_name']}"
            client_info += f"\nPhone: {self.current_receipt['client_phone']}"
            self.client_info_label.setText(client_info)
            
            gas_info = f"Type: {self.current_receipt['gas_type']}"
            if self.current_receipt['sub_type']:
                gas_info += f" - {self.current_receipt['sub_type']}"
            gas_info += f"\nCapacity: {self.current_receipt['capacity']}"
            gas_info += f"\nQuantity: {self.current_receipt['quantity']}"
            self.gas_info_label.setText(gas_info)
    
    def load_gate_pass_data(self):
        """Load existing gate pass data for viewing/editing"""
        if self.gate_pass_data:
            self.gate_pass_number_label.setText(self.gate_pass_data['gate_pass_number'])
            
            # Load receipt info
            try:
                query = '''
                    SELECT r.*, c.name as client_name, c.phone as client_phone,
                           gp.gas_type, gp.sub_type, gp.capacity, s.quantity
                    FROM receipts r
                    JOIN clients c ON r.client_id = c.id
                    JOIN sales s ON r.sale_id = s.id
                    JOIN gas_products gp ON s.gas_product_id = gp.id
                    WHERE r.id = ?
                '''
                result = self.db_manager.execute_query(query, (self.gate_pass_data['receipt_id'],))
                
                if result:
                    self.current_receipt = result[0]
                    self.receipt_search_input.setText(self.current_receipt['receipt_number'])
                    self.update_receipt_info()
                    
            except Exception as e:
                QMessageBox.critical(self, "Database Error", f"Failed to load receipt: {str(e)}")
            
            # Set other fields
            self.driver_name_input.setText(self.gate_pass_data['driver_name'])
            self.vehicle_number_input.setText(self.gate_pass_data['vehicle_number'])
            self.quantity_spinbox.setValue(self.gate_pass_data['quantity'])
            
            # Parse and set datetime
            if self.gate_pass_data['time_out']:
                time_out = QDateTime.fromString(self.gate_pass_data['time_out'], "yyyy-MM-dd hh:mm:ss")
                self.time_out_datetime.setDateTime(time_out)
            
            if self.gate_pass_data['time_in']:
                time_in = QDateTime.fromString(self.gate_pass_data['time_in'], "yyyy-MM-dd hh:mm:ss")
                self.time_in_datetime.setDateTime(time_in)
                self.time_in_checkbox.setChecked(True)
            else:
                self.time_in_checkbox.setChecked(False)
            if self.gate_pass_data.get('expected_time_in'):
                exp_in = QDateTime.fromString(self.gate_pass_data['expected_time_in'], "yyyy-MM-dd hh:mm:ss")
                if exp_in.isValid():
                    self.expected_in_datetime.setDateTime(exp_in)
    
    def is_editable(self):
        """Check if gate pass can be edited"""
        if not self.gate_pass_data:
            return True  # New gate pass is always editable
        
        # Can only edit if not returned and user is Admin or Gate Operator
        if (self.gate_pass_data.get('time_in') and 
            self.current_user['role'] not in ['Admin']):
            return False
        
        return self.current_user['role'] in ['Admin', 'Gate Operator']
    
    def set_read_only(self):
        """Set form to read-only mode for viewing"""
        self.receipt_search_input.setEnabled(False)
        self.driver_name_input.setEnabled(False)
        self.vehicle_number_input.setEnabled(False)
        self.quantity_spinbox.setEnabled(False)
        self.time_out_datetime.setEnabled(False)
        
        # Change button text
        button_box = self.findChild(QDialogButtonBox)
        if button_box:
            button_box.button(QDialogButtonBox.Ok).setText("Close")
            button_box.button(QDialogButtonBox.Cancel).hide()
    
    def validate(self):
        """Validate form data"""
        # Only validate receipt for new gate passes, not when editing
        if not self.gate_pass_data and not self.current_receipt:
            QMessageBox.warning(self, "Validation Error", "Please select a valid receipt.")
            return False
        
        driver_name = self.driver_name_input.text().strip()
        if not driver_name:
            QMessageBox.warning(self, "Validation Error", "Driver name is required.")
            return False
        
        vehicle_number = self.vehicle_number_input.text().strip()
        if not vehicle_number:
            QMessageBox.warning(self, "Validation Error", "Vehicle number is required.")
            return False
        
        quantity = self.quantity_spinbox.value()
        if quantity <= 0:
            QMessageBox.warning(self, "Validation Error", "Quantity must be greater than 0.")
            return False
        
        # Only check receipt quantity for new gate passes
        if not self.gate_pass_data and self.current_receipt and quantity > self.current_receipt['quantity']:
            QMessageBox.warning(
                self,
                "Validation Error",
                f"Quantity cannot exceed receipt quantity ({self.current_receipt['quantity']})."
            )
            return False
        
        return True
    
    def get_gate_pass_data(self):
        """Get gate pass data from form"""
        time_in = None
        if self.time_in_checkbox.isChecked():
            time_in = self.time_in_datetime.dateTime().toString("yyyy-MM-dd hh:mm:ss")
        
        # For editing, we don't need receipt data since it's already set
        data = {
            'driver_name': self.driver_name_input.text().strip(),
            'vehicle_number': self.vehicle_number_input.text().strip(),
            'quantity': self.quantity_spinbox.value(),
            'time_out': self.time_out_datetime.dateTime().toString("yyyy-MM-dd hh:mm:ss"),
            'time_in': time_in,
            'gate_operator_id': self.current_user['id']
        }
        data['expected_time_in'] = self.expected_in_datetime.dateTime().toString("yyyy-MM-dd hh:mm:ss")
        
        # Add receipt data for new gate passes
        if self.current_receipt:
            data['receipt_id'] = self.current_receipt['id']
            data['client_id'] = self.current_receipt['client_id']
            data['gas_type'] = self.current_receipt['gas_type']
            data['capacity'] = self.current_receipt['capacity']
        
        return data
    
    def accept(self):
        if self.gate_pass_data and not self.is_editable():
            # View mode - just close
            super().accept()
        else:
            # Create/Edit mode - validate and proceed
            if self.validate():
                super().accept()

class GatePassesWidget(QWidget):
    def __init__(self, db_manager: DatabaseManager, current_user: dict):
        super().__init__()
        self.db_manager = db_manager
        self.current_user = current_user
        self.init_ui()
        self.load_gate_passes()
        self.auto_timer = QTimer(self)
        self.auto_timer.setInterval(60000)
        self.auto_timer.timeout.connect(self.run_auto_returns)
        self.auto_timer.start()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title_label = QLabel("Gate Pass Management")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title_label)
        
        # Search and controls
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(10)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by gate pass number, receipt number, or driver name...")
        self.search_input.textChanged.connect(self.filter_gate_passes)
        controls_layout.addWidget(self.search_input)
        
        self.create_pass_btn = QPushButton("Create Gate Pass")
        self.create_pass_btn.clicked.connect(self.create_gate_pass)
        controls_layout.addWidget(self.create_pass_btn)
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.load_gate_passes)
        controls_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(controls_layout)
        
        # Gate passes table
        self.gate_passes_table = QTableWidget()
        self.gate_passes_table.setColumnCount(11)
        self.gate_passes_table.setHorizontalHeaderLabels([
            "Gate Pass #", "Receipt #", "Client", "Driver", "Vehicle", "Gas Type", "Quantity", "Time Out", "Expected In", "Time In", "Actions"
        ])
        self.gate_passes_table.setAlternatingRowColors(True)
        self.gate_passes_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.gate_passes_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.gate_passes_table.horizontalHeader().setStretchLastSection(True)
        self.gate_passes_table.setColumnWidth(0, 120)
        self.gate_passes_table.setColumnWidth(1, 120)
        self.gate_passes_table.setColumnWidth(2, 180)
        self.gate_passes_table.setColumnWidth(3, 140)
        self.gate_passes_table.setColumnWidth(4, 120)
        self.gate_passes_table.setColumnWidth(5, 160)
        self.gate_passes_table.setColumnWidth(6, 90)
        self.gate_passes_table.setColumnWidth(7, 140)
        self.gate_passes_table.setColumnWidth(8, 140)
        self.gate_passes_table.setColumnWidth(9, 140)
        self.gate_passes_table.setColumnWidth(10, 180)
        layout.addWidget(self.gate_passes_table)

        self.set_role_permissions()
    
    def set_role_permissions(self):
        """Set permissions based on user role"""
        role = self.current_user['role']
        
        if role == 'Driver':
            self.create_pass_btn.setEnabled(False)
            self.gate_passes_table.setEnabled(False)
    
    def load_gate_passes(self):
        """Load all gate passes from database"""
        try:
            query = '''
                SELECT gp.*, c.name as client_name, c.phone as client_phone,
                       r.receipt_number, u.full_name as operator_name
                FROM gate_passes gp
                JOIN clients c ON gp.client_id = c.id
                JOIN receipts r ON gp.receipt_id = r.id
                JOIN users u ON gp.gate_operator_id = u.id
                ORDER BY gp.created_at DESC
                LIMIT 100
            '''
            gate_passes = self.db_manager.execute_query(query)
            self.populate_table(gate_passes)
            
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load gate passes: {str(e)}")
    
    def populate_table(self, gate_passes):
        """Populate table with gate pass data"""
        self.gate_passes_table.setRowCount(len(gate_passes))
        
        for row, gate_pass in enumerate(gate_passes):
            # Gate Pass Number
            self.gate_passes_table.setItem(row, 0, QTableWidgetItem(gate_pass['gate_pass_number']))
            
            # Receipt Number
            self.gate_passes_table.setItem(row, 1, QTableWidgetItem(gate_pass['receipt_number']))
            
            # Client
            self.gate_passes_table.setItem(row, 2, QTableWidgetItem(gate_pass['client_name']))
            
            # Driver
            self.gate_passes_table.setItem(row, 3, QTableWidgetItem(gate_pass['driver_name']))
            
            # Vehicle
            self.gate_passes_table.setItem(row, 4, QTableWidgetItem(gate_pass['vehicle_number']))
            
            # Gas Type
            gas_type_text = f"{gate_pass['gas_type']} - {gate_pass['capacity']}"
            self.gate_passes_table.setItem(row, 5, QTableWidgetItem(gas_type_text))
            
            # Quantity
            self.gate_passes_table.setItem(row, 6, QTableWidgetItem(str(gate_pass['quantity'])))
            
            # Time Out
            time_out = gate_pass['time_out'][:16] if gate_pass['time_out'] else ""
            self.gate_passes_table.setItem(row, 7, QTableWidgetItem(time_out))
            
            # Expected In
            expected_in = gate_pass['expected_time_in'][:16] if gate_pass.get('expected_time_in') else ""
            self.gate_passes_table.setItem(row, 8, QTableWidgetItem(expected_in))

            # Time In
            time_in = gate_pass['time_in'][:16] if gate_pass['time_in'] else "Not returned"
            time_in_item = QTableWidgetItem(time_in)
            if not gate_pass['time_in']:
                time_in_item.setForeground(Qt.red)
            else:
                time_in_item.setForeground(Qt.darkGreen)
            self.gate_passes_table.setItem(row, 9, time_in_item)
            
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
            view_btn.clicked.connect(lambda checked, gp=gate_pass: self.view_gate_pass(gp))
            actions_layout.addWidget(view_btn)
            
            # Add edit button for Admin and Gate Operator
            if self.current_user['role'] in ['Admin', 'Gate Operator']:
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
                edit_btn.clicked.connect(lambda checked, gp=gate_pass: self.edit_gate_pass(gp))
                actions_layout.addWidget(edit_btn)
            
            if not gate_pass['time_in'] and self.current_user['role'] in ['Admin', 'Gate Operator']:
                return_btn = QPushButton("Mark Returned")
                return_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #27ae60;
                        color: white;
                        border: 1px solid #229954;
                        border-radius: 4px;
                        padding: 6px 12px;
                        font-size: 12px;
                        font-weight: 500;
                        min-width: 60px;
                    }
                    QPushButton:hover {
                        background-color: #229954;
                        border-color: #1e8449;
                    }
                    QPushButton:pressed {
                        background-color: #1e8449;
                        border-color: #186a3b;
                    }
                """)
                return_btn.clicked.connect(lambda checked, gp=gate_pass: self.mark_returned(gp))
                actions_layout.addWidget(return_btn)
            
            self.gate_passes_table.setCellWidget(row, 10, actions_widget)
    
    def filter_gate_passes(self):
        """Filter gate passes based on search input"""
        search_text = self.search_input.text().strip().lower()
        
        try:
            query = '''
                SELECT gp.*, c.name as client_name, c.phone as client_phone,
                       r.receipt_number, u.full_name as operator_name
                FROM gate_passes gp
                JOIN clients c ON gp.client_id = c.id
                JOIN receipts r ON gp.receipt_id = r.id
                JOIN users u ON gp.gate_operator_id = u.id
                WHERE LOWER(gp.gate_pass_number) LIKE ? 
                   OR LOWER(r.receipt_number) LIKE ?
                   OR LOWER(gp.driver_name) LIKE ?
                   OR LOWER(gp.vehicle_number) LIKE ?
                ORDER BY gp.created_at DESC
                LIMIT 100
            '''
            search_pattern = f"%{search_text}%"
            gate_passes = self.db_manager.execute_query(query, (search_pattern, search_pattern, search_pattern, search_pattern))
            self.populate_table(gate_passes)
            
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to filter gate passes: {str(e)}")
    
    def create_gate_pass(self):
        """Create new gate pass"""
        dialog = GatePassDialog(self.db_manager, self.current_user, self)
        if dialog.exec() == QDialog.Accepted:
            try:
                gate_pass_data = dialog.get_gate_pass_data()
                
                # Generate gate pass number
                gate_pass_number = self.db_manager.get_next_gate_pass_number()
                
                # Create gate pass
                gate_pass_id = self.db_manager.create_gate_pass(
                    gate_pass_number=gate_pass_number,
                    receipt_id=gate_pass_data['receipt_id'],
                    client_id=gate_pass_data['client_id'],
                    driver_name=gate_pass_data['driver_name'],
                    vehicle_number=gate_pass_data['vehicle_number'],
                    gas_type=gate_pass_data['gas_type'],
                    capacity=gate_pass_data['capacity'],
                    quantity=gate_pass_data['quantity'],
                    gate_operator_id=gate_pass_data['gate_operator_id'],
                    expected_time_in=gate_pass_data.get('expected_time_in')
                )
                
                self.db_manager.log_activity(
                    "CREATE_GATE_PASS",
                    f"Created gate pass: {gate_pass_number}",
                    self.current_user['id']
                )
                
                QMessageBox.information(
                    self,
                    "Success",
                    f"Gate pass created successfully!\nGate Pass Number: {gate_pass_number}"
                )
                
                self.load_gate_passes()
                
            except Exception as e:
                QMessageBox.critical(self, "Database Error", f"Failed to create gate pass: {str(e)}")
    
    def edit_gate_pass(self, gate_pass_data: dict):
        """Edit gate pass details"""
        dialog = GatePassDialog(self.db_manager, self.current_user, self, gate_pass_data)
        if dialog.exec() == QDialog.Accepted:
            try:
                updated_data = dialog.get_gate_pass_data()
                
                # Update gate pass in database
                query = '''
                    UPDATE gate_passes 
                    SET driver_name = ?, vehicle_number = ?, quantity = ?, time_out = ?, expected_time_in = ?, time_in = COALESCE(?, time_in)
                    WHERE id = ?
                '''
                self.db_manager.execute_update(query, (
                    updated_data['driver_name'],
                    updated_data['vehicle_number'],
                    updated_data['quantity'],
                    updated_data['time_out'],
                    updated_data.get('expected_time_in'),
                    updated_data.get('time_in'),
                    gate_pass_data['id']
                ))
                
                self.db_manager.log_activity(
                    "EDIT_GATE_PASS",
                    f"Updated gate pass: {gate_pass_data['gate_pass_number']}",
                    self.current_user['id']
                )
                
                QMessageBox.information(self, "Success", "Gate pass updated successfully!")
                self.load_gate_passes()
                
            except Exception as e:
                QMessageBox.critical(self, "Database Error", f"Failed to update gate pass: {str(e)}")
    
    def view_gate_pass(self, gate_pass_data: dict):
        """View gate pass details"""
        dialog = GatePassDialog(self.db_manager, self.current_user, self, gate_pass_data)
        dialog.exec()

    def run_auto_returns(self):
        try:
            changed = self.db_manager.auto_mark_due_returns()
            if changed:
                self.load_gate_passes()
        except Exception:
            pass
    
    def mark_returned(self, gate_pass_data: dict):
        """Mark gate pass as returned"""
        reply = QMessageBox.question(
            self,
            "Mark as Returned",
            f"Mark gate pass {gate_pass_data['gate_pass_number']} as returned?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                query = '''
                    UPDATE gate_passes 
                    SET time_in = CURRENT_TIMESTAMP 
                    WHERE id = ?
                '''
                self.db_manager.execute_update(query, (gate_pass_data['id'],))
                
                self.db_manager.log_activity(
                    "MARK_RETURNED",
                    f"Marked gate pass as returned: {gate_pass_data['gate_pass_number']}",
                    self.current_user['id']
                )
                
                QMessageBox.information(self, "Success", "Gate pass marked as returned!")
                self.load_gate_passes()
                
            except Exception as e:
                QMessageBox.critical(self, "Database Error", f"Failed to mark as returned: {str(e)}")
