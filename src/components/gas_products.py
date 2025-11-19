from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                               QTableWidgetItem, QPushButton, QLineEdit, QLabel, 
                               QMessageBox, QDialog, QFormLayout, QDialogButtonBox,
                               QComboBox, QDoubleSpinBox, QTextEdit, QHeaderView)
from PySide6.QtCore import Qt
from database_module import DatabaseManager

class AddGasProductDialog(QDialog):
    def __init__(self, db_manager: DatabaseManager, parent=None, product_data=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.product_data = product_data
        self.setWindowTitle("Add Gas Product" if not product_data else "Edit Gas Product")
        self.setFixedSize(500, 450)
        self.init_ui()
        
        if product_data:
            self.load_product_data()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Form layout
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        # Gas Type
        self.gas_type_combo = QComboBox()
        self.gas_type_combo.addItems([
            "Oxygen", "Nitrogen", "Organ Gas", "LPG"
        ])
        self.gas_type_combo.currentTextChanged.connect(self.on_gas_type_changed)
        form_layout.addRow("Gas Type *:", self.gas_type_combo)
        
        # Sub Type (for Oxygen and LPG)
        self.sub_type_combo = QComboBox()
        self.update_sub_types()
        form_layout.addRow("Sub Type:", self.sub_type_combo)
        
        # Capacity
        self.capacity_combo = QComboBox()
        self.update_capacities()
        form_layout.addRow("Capacity *:", self.capacity_combo)
        
        # Unit Price
        self.unit_price_spinbox = QDoubleSpinBox()
        self.unit_price_spinbox.setRange(0, 100000)
        self.unit_price_spinbox.setDecimals(2)
        self.unit_price_spinbox.setPrefix("Rs. ")
        self.unit_price_spinbox.setSingleStep(100)
        form_layout.addRow("Unit Price *:", self.unit_price_spinbox)
        
        # Description
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Enter product description (optional)")
        self.description_input.setMaximumHeight(80)
        form_layout.addRow("Description:", self.description_input)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def on_gas_type_changed(self, gas_type):
        """Update sub-types and capacities based on gas type"""
        self.update_sub_types()
        self.update_capacities()
    
    def update_sub_types(self):
        """Update sub-type options based on gas type"""
        gas_type = self.gas_type_combo.currentText()
        self.sub_type_combo.clear()
        
        if gas_type == "Oxygen":
            self.sub_type_combo.addItems(["Type A", "Type B", "Type C"])
            self.sub_type_combo.setEnabled(True)
        elif gas_type == "LPG":
            self.sub_type_combo.addItems(["Type 1", "Type 2", "Type 3"])
            self.sub_type_combo.setEnabled(True)
        else:
            self.sub_type_combo.addItem("")
            self.sub_type_combo.setEnabled(False)
    
    def update_capacities(self):
        """Update capacity options based on gas type"""
        gas_type = self.gas_type_combo.currentText()
        self.capacity_combo.clear()
        
        if gas_type in ["Oxygen", "Nitrogen", "Organ Gas"]:
            capacities = ["1.4", "3.11", "6.23", "6.79", "8.4", "9.9"]
        elif gas_type == "LPG":
            capacities = ["12kg", "45kg"]
        else:
            capacities = []
        
        self.capacity_combo.addItems(capacities)
    
    def load_product_data(self):
        """Load existing product data for editing"""
        self.gas_type_combo.setCurrentText(self.product_data['gas_type'])
        self.sub_type_combo.setCurrentText(self.product_data['sub_type'] or "")
        self.capacity_combo.setCurrentText(self.product_data['capacity'])
        self.unit_price_spinbox.setValue(float(self.product_data['unit_price']))
        self.description_input.setPlainText(self.product_data['description'] or '')
    
    def get_product_data(self):
        """Get product data from form"""
        return {
            'gas_type': self.gas_type_combo.currentText(),
            'sub_type': self.sub_type_combo.currentText() if self.sub_type_combo.currentText() else None,
            'capacity': self.capacity_combo.currentText(),
            'unit_price': self.unit_price_spinbox.value(),
            'description': self.description_input.toPlainText().strip()
        }
    
    def validate(self):
        """Validate form data"""
        gas_type = self.gas_type_combo.currentText()
        capacity = self.capacity_combo.currentText()
        unit_price = self.unit_price_spinbox.value()
        
        if not gas_type:
            QMessageBox.warning(self, "Validation Error", "Gas type is required.")
            return False
        
        if not capacity:
            QMessageBox.warning(self, "Validation Error", "Capacity is required.")
            return False
        
        if unit_price <= 0:
            QMessageBox.warning(self, "Validation Error", "Unit price must be greater than 0.")
            return False
        
        return True
    
    def accept(self):
        if self.validate():
            super().accept()

class GasProductsWidget(QWidget):
    def __init__(self, db_manager: DatabaseManager, current_user: dict):
        super().__init__()
        self.db_manager = db_manager
        self.current_user = current_user
        self.init_ui()
        self.load_products()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title_label = QLabel("Gas Products Configuration")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title_label)
        
        # Search and controls
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(10)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by gas type, capacity, or description...")
        self.search_input.textChanged.connect(self.filter_products)
        controls_layout.addWidget(self.search_input)
        
        self.add_product_btn = QPushButton("Add New Product")
        self.add_product_btn.clicked.connect(self.add_product)
        controls_layout.addWidget(self.add_product_btn)
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.load_products)
        controls_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(controls_layout)
        
        # Products table
        self.products_table = QTableWidget()
        self.products_table.setColumnCount(7)
        self.products_table.setHorizontalHeaderLabels([
            "ID", "Gas Type", "Sub Type", "Capacity", "Unit Price", "Description", "Actions"
        ])
        
        # Configure table
        self.products_table.setAlternatingRowColors(True)
        self.products_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.products_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.products_table.horizontalHeader().setStretchLastSection(True)
        self.products_table.setColumnWidth(0, 50)   # ID
        self.products_table.setColumnWidth(1, 120)  # Gas Type
        self.products_table.setColumnWidth(2, 100)  # Sub Type
        self.products_table.setColumnWidth(3, 100)  # Capacity
        self.products_table.setColumnWidth(4, 100)  # Unit Price
        self.products_table.setColumnWidth(5, 200)  # Description
        self.products_table.setColumnWidth(6, 150)  # Actions
        
        layout.addWidget(self.products_table)
        
        # Set role-based permissions
        self.set_role_permissions()
    
    def set_role_permissions(self):
        """Set permissions based on user role"""
        role = self.current_user['role']
        
        if role == 'Driver':
            self.add_product_btn.setEnabled(False)
    
    def load_products(self):
        """Load all gas products from database"""
        try:
            products = self.db_manager.get_gas_products()
            self.populate_table(products)
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load products: {str(e)}")
    
    def populate_table(self, products):
        """Populate table with product data"""
        self.products_table.setRowCount(len(products))
        
        for row, product in enumerate(products):
            # ID
            self.products_table.setItem(row, 0, QTableWidgetItem(str(product['id'])))
            
            # Gas Type
            self.products_table.setItem(row, 1, QTableWidgetItem(product['gas_type']))
            
            # Sub Type
            self.products_table.setItem(row, 2, QTableWidgetItem(product['sub_type'] or ''))
            
            # Capacity
            self.products_table.setItem(row, 3, QTableWidgetItem(product['capacity']))
            
            # Unit Price
            price_item = QTableWidgetItem(f"Rs. {product['unit_price']:,.2f}")
            price_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.products_table.setItem(row, 4, price_item)
            
            # Description
            self.products_table.setItem(row, 5, QTableWidgetItem(product['description'] or ''))
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setSpacing(5)
            actions_layout.setContentsMargins(5, 5, 5, 5)
            
            edit_btn = QPushButton("Edit")
            edit_btn.clicked.connect(lambda checked, p=product: self.edit_product(p))
            actions_layout.addWidget(edit_btn)
            
            if self.current_user['role'] == 'Admin':
                delete_btn = QPushButton("Delete")
                delete_btn.clicked.connect(lambda checked, p=product: self.delete_product(p))
                delete_btn.setStyleSheet("background-color: #e74c3c;")
                actions_layout.addWidget(delete_btn)
            
            self.products_table.setCellWidget(row, 6, actions_widget)
    
    def filter_products(self):
        """Filter products based on search input"""
        # This is a simple implementation - you might want to enhance it
        search_text = self.search_input.text().strip().lower()
        
        try:
            products = self.db_manager.get_gas_products()
            
            if search_text:
                filtered_products = []
                for product in products:
                    if (search_text in product['gas_type'].lower() or
                        search_text in product['capacity'].lower() or
                        (product['description'] and search_text in product['description'].lower()) or
                        (product['sub_type'] and search_text in product['sub_type'].lower())):
                        filtered_products.append(product)
                products = filtered_products
            
            self.populate_table(products)
            
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to filter products: {str(e)}")
    
    def add_product(self):
        """Add new gas product"""
        dialog = AddGasProductDialog(self.db_manager, self)
        if dialog.exec() == QDialog.Accepted:
            try:
                product_data = dialog.get_product_data()
                product_id = self.db_manager.add_gas_product(
                    product_data['gas_type'],
                    product_data['sub_type'],
                    product_data['capacity'],
                    product_data['unit_price'],
                    product_data['description']
                )
                
                self.db_manager.log_activity(
                    "ADD_GAS_PRODUCT",
                    f"Added new gas product: {product_data['gas_type']} - {product_data['capacity']}",
                    self.current_user['id']
                )
                
                QMessageBox.information(self, "Success", "Gas product added successfully!")
                self.load_products()
                
            except Exception as e:
                QMessageBox.critical(self, "Database Error", f"Failed to add product: {str(e)}")
    
    def edit_product(self, product):
        """Edit existing gas product"""
        dialog = AddGasProductDialog(self.db_manager, self, product)
        if dialog.exec() == QDialog.Accepted:
            try:
                product_data = dialog.get_product_data()
                
                # For now, we'll delete and re-add since we don't have an update method
                # In a real application, you'd want to add an update method to DatabaseManager
                query = '''
                    UPDATE gas_products 
                    SET gas_type = ?, sub_type = ?, capacity = ?, unit_price = ?, description = ?
                    WHERE id = ?
                '''
                self.db_manager.execute_update(query, (
                    product_data['gas_type'],
                    product_data['sub_type'],
                    product_data['capacity'],
                    product_data['unit_price'],
                    product_data['description'],
                    product['id']
                ))
                
                self.db_manager.log_activity(
                    "EDIT_GAS_PRODUCT",
                    f"Updated gas product: {product_data['gas_type']} - {product_data['capacity']}",
                    self.current_user['id']
                )
                
                QMessageBox.information(self, "Success", "Gas product updated successfully!")
                self.load_products()
                
            except Exception as e:
                QMessageBox.critical(self, "Database Error", f"Failed to update product: {str(e)}")
    
    def delete_product(self, product):
        """Delete gas product (Admin only)"""
        if self.current_user['role'] != 'Admin':
            QMessageBox.warning(self, "Permission Denied", "Only administrators can delete products.")
            return
        
        reply = QMessageBox.question(
            self,
            "Delete Product",
            f"Are you sure you want to delete product '{product['gas_type']} - {product['capacity']}'?\n\n"
            "This action cannot be undone and will affect sales transactions.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Check if product has any sales
                query = 'SELECT COUNT(*) as count FROM sales WHERE gas_product_id = ?'
                result = self.db_manager.execute_query(query, (product['id'],))
                sales_count = result[0]['count'] if result else 0
                
                if sales_count > 0:
                    QMessageBox.warning(
                        self,
                        "Cannot Delete",
                        f"Cannot delete product '{product['gas_type']} - {product['capacity']}' "
                        f"because it has {sales_count} sales transactions."
                    )
                    return
                
                # Delete product
                query = 'DELETE FROM gas_products WHERE id = ?'
                self.db_manager.execute_update(query, (product['id'],))
                
                self.db_manager.log_activity(
                    "DELETE_GAS_PRODUCT",
                    f"Deleted gas product: {product['gas_type']} - {product['capacity']}",
                    self.current_user['id']
                )
                
                QMessageBox.information(self, "Success", "Gas product deleted successfully!")
                self.load_products()
                
            except Exception as e:
                QMessageBox.critical(self, "Database Error", f"Failed to delete product: {str(e)}")