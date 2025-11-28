from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                               QTableWidgetItem, QPushButton, QLineEdit, QLabel, 
                               QMessageBox, QDialog, QFormLayout, QDialogButtonBox,
                               QDoubleSpinBox, QDateEdit, QComboBox, QHeaderView, QGroupBox)
from PySide6.QtCore import Qt, QDate
from src.database_module import DatabaseManager
from datetime import datetime

class AddEmployeeDialog(QDialog):
    def __init__(self, db_manager: DatabaseManager, parent=None, employee_data=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.employee_data = employee_data
        self.setWindowTitle("Add Employee" if not employee_data else "Edit Employee")
        self.setFixedSize(500, 450)
        self.init_ui()
        
        if employee_data:
            self.load_employee_data()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Form layout
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter employee name")
        form_layout.addRow("Name *:", self.name_input)
        
        self.role_combo = QComboBox()
        self.role_combo.addItems([
            "Manager", "Accountant", "Gate Operator", "Driver", "Technician", "Helper", "Security"
        ])
        form_layout.addRow("Role *:", self.role_combo)
        
        self.salary_spinbox = QDoubleSpinBox()
        self.salary_spinbox.setRange(0, 1000000)
        self.salary_spinbox.setDecimals(2)
        self.salary_spinbox.setPrefix("Rs. ")
        self.salary_spinbox.setSingleStep(1000)
        form_layout.addRow("Salary *:", self.salary_spinbox)
        
        self.contact_input = QLineEdit()
        self.contact_input.setPlaceholderText("Enter phone number")
        form_layout.addRow("Contact:", self.contact_input)
        
        self.joining_date_edit = QDateEdit()
        self.joining_date_edit.setDate(QDate.currentDate())
        self.joining_date_edit.setCalendarPopup(True)
        form_layout.addRow("Joining Date *:", self.joining_date_edit)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def load_employee_data(self):
        """Load existing employee data for editing"""
        self.name_input.setText(self.employee_data['name'])
        self.role_combo.setCurrentText(self.employee_data['role'])
        self.salary_spinbox.setValue(float(self.employee_data['salary']))
        self.contact_input.setText(self.employee_data['contact'] or '')
        
        # Parse joining date
        joining_date = QDate.fromString(self.employee_data['joining_date'], "yyyy-MM-dd")
        if joining_date.isValid():
            self.joining_date_edit.setDate(joining_date)
    
    def get_employee_data(self):
        """Get employee data from form"""
        return {
            'name': self.name_input.text().strip(),
            'role': self.role_combo.currentText(),
            'salary': self.salary_spinbox.value(),
            'contact': self.contact_input.text().strip(),
            'joining_date': self.joining_date_edit.date().toString("yyyy-MM-dd")
        }
    
    def validate(self):
        """Validate form data"""
        name = self.name_input.text().strip()
        role = self.role_combo.currentText()
        salary = self.salary_spinbox.value()
        
        if not name:
            QMessageBox.warning(self, "Validation Error", "Employee name is required.")
            return False
        
        if not role:
            QMessageBox.warning(self, "Validation Error", "Employee role is required.")
            return False
        
        if salary <= 0:
            QMessageBox.warning(self, "Validation Error", "Salary must be greater than 0.")
            return False
        
        return True
    
    def accept(self):
        if self.validate():
            super().accept()

class EmployeesWidget(QWidget):
    def __init__(self, db_manager: DatabaseManager, current_user: dict):
        super().__init__()
        self.db_manager = db_manager
        self.current_user = current_user
        self.init_ui()
        self.load_employees()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title_label = QLabel("Employee Management")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title_label)
        
        # Search and controls
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(10)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by name, role, or contact...")
        self.search_input.textChanged.connect(self.filter_employees)
        controls_layout.addWidget(self.search_input)
        
        self.role_filter_combo = QComboBox()
        self.role_filter_combo.addItem("All Roles")
        self.role_filter_combo.addItems([
            "Manager", "Accountant", "Gate Operator", "Driver", "Technician", "Helper", "Security"
        ])
        self.role_filter_combo.currentTextChanged.connect(self.filter_employees)
        controls_layout.addWidget(self.role_filter_combo)
        
        self.add_employee_btn = QPushButton("Add New Employee")
        self.add_employee_btn.clicked.connect(self.add_employee)
        controls_layout.addWidget(self.add_employee_btn)
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.load_employees)
        controls_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(controls_layout)
        
        # Employees table
        self.employees_table = QTableWidget()
        self.employees_table.setColumnCount(7)
        self.employees_table.setHorizontalHeaderLabels([
            "ID", "Name", "Role", "Salary", "Contact", "Joining Date", "Actions"
        ])
        
        # Configure table
        self.employees_table.setAlternatingRowColors(True)
        self.employees_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.employees_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.employees_table.horizontalHeader().setStretchLastSection(True)
        self.employees_table.setColumnWidth(0, 50)   # ID
        self.employees_table.setColumnWidth(1, 200)  # Name
        self.employees_table.setColumnWidth(2, 120)  # Role
        self.employees_table.setColumnWidth(3, 120)  # Salary
        self.employees_table.setColumnWidth(4, 120)  # Contact
        self.employees_table.setColumnWidth(5, 120)  # Joining Date
        self.employees_table.setColumnWidth(6, 150)  # Actions
        
        layout.addWidget(self.employees_table)
        
        # Salary report section
        salary_group = QGroupBox("Salary Summary")
        salary_layout = QHBoxLayout()
        salary_layout.setSpacing(20)
        
        self.total_salary_label = QLabel("Total Monthly Salary: Rs. 0.00")
        self.total_salary_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        salary_layout.addWidget(self.total_salary_label)
        
        self.employee_count_label = QLabel("Total Employees: 0")
        self.employee_count_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        salary_layout.addWidget(self.employee_count_label)
        
        self.generate_report_btn = QPushButton("Generate Salary Report")
        self.generate_report_btn.clicked.connect(self.generate_salary_report)
        salary_layout.addWidget(self.generate_report_btn)
        
        salary_layout.addStretch()
        salary_group.setLayout(salary_layout)
        layout.addWidget(salary_group)
        
        # Set role-based permissions
        self.set_role_permissions()
    
    def set_role_permissions(self):
        """Set permissions based on user role"""
        role = self.current_user['role']
        
        if role == 'Driver':
            self.add_employee_btn.setEnabled(False)
            self.generate_report_btn.setEnabled(False)
    
    def load_employees(self):
        """Load all employees from database"""
        try:
            employees = self.db_manager.get_employees()
            self.populate_table(employees)
            self.update_salary_summary(employees)
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load employees: {str(e)}")
    
    def populate_table(self, employees):
        """Populate table with employee data"""
        self.employees_table.setRowCount(len(employees))
        
        for row, employee in enumerate(employees):
            # ID
            self.employees_table.setItem(row, 0, QTableWidgetItem(str(employee['id'])))
            
            # Name
            self.employees_table.setItem(row, 1, QTableWidgetItem(employee['name']))
            
            # Role
            self.employees_table.setItem(row, 2, QTableWidgetItem(employee['role']))
            
            # Salary
            salary_item = QTableWidgetItem(f"Rs. {employee['salary']:,.2f}")
            salary_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.employees_table.setItem(row, 3, salary_item)
            
            # Contact
            self.employees_table.setItem(row, 4, QTableWidgetItem(employee['contact'] or ''))
            
            # Joining Date
            self.employees_table.setItem(row, 5, QTableWidgetItem(employee['joining_date']))
            
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
                    border-radius: 6px;
                    padding: 6px 12px;
                    font-size: 13px;
                    font-weight: 600;
                }
                QPushButton:hover { background-color: #138496; }
                QPushButton:pressed { background-color: #117a8b; }
            """)
            view_btn.setMinimumWidth(96)
            view_btn.setFixedHeight(32)
            view_btn.clicked.connect(lambda checked, e=employee: self.view_employee(e))
            actions_layout.addWidget(view_btn)
            
            if self.current_user['role'] in ['Admin', 'Manager']:
                edit_btn = QPushButton("Edit")
                edit_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #28a745;
                        color: white;
                        border: 1px solid #1e7e34;
                        border-radius: 6px;
                        padding: 6px 12px;
                        font-size: 13px;
                        font-weight: 600;
                    }
                    QPushButton:hover { background-color: #218838; }
                    QPushButton:pressed { background-color: #1e7e34; }
                """)
                edit_btn.setMinimumWidth(96)
                edit_btn.setFixedHeight(32)
                edit_btn.clicked.connect(lambda checked, e=employee: self.edit_employee(e))
                actions_layout.addWidget(edit_btn)
                
                delete_btn = QPushButton("Delete")
                delete_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #dc3545;
                        color: white;
                        border: 1px solid #bd2130;
                        border-radius: 6px;
                        padding: 6px 12px;
                        font-size: 13px;
                        font-weight: 600;
                    }
                    QPushButton:hover { background-color: #c82333; }
                    QPushButton:pressed { background-color: #bd2130; }
                """)
                delete_btn.setMinimumWidth(96)
                delete_btn.setFixedHeight(32)
                delete_btn.clicked.connect(lambda checked, e=employee: self.delete_employee(e))
                actions_layout.addWidget(delete_btn)
            
            self.employees_table.setCellWidget(row, 6, actions_widget)
    
    def update_salary_summary(self, employees):
        """Update salary summary"""
        total_salary = sum(employee['salary'] for employee in employees)
        employee_count = len(employees)
        
        self.total_salary_label.setText(f"Total Monthly Salary: Rs. {total_salary:,.2f}")
        self.employee_count_label.setText(f"Total Employees: {employee_count}")
    
    def filter_employees(self):
        """Filter employees based on search and role filter"""
        search_text = self.search_input.text().strip().lower()
        selected_role = self.role_filter_combo.currentText()
        
        try:
            employees = self.db_manager.get_employees()
            
            # Apply filters
            filtered_employees = []
            for employee in employees:
                # Role filter
                if selected_role != "All Roles" and employee['role'] != selected_role:
                    continue
                
                # Search filter
                if search_text:
                    if (search_text in employee['name'].lower() or
                        search_text in employee['role'].lower() or
                        (employee['contact'] and search_text in employee['contact'].lower())):
                        filtered_employees.append(employee)
                else:
                    filtered_employees.append(employee)
            
            self.populate_table(filtered_employees)
            self.update_salary_summary(filtered_employees)
            
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to filter employees: {str(e)}")
    
    def add_employee(self):
        """Add new employee"""
        dialog = AddEmployeeDialog(self.db_manager, self)
        if dialog.exec() == QDialog.Accepted:
            try:
                employee_data = dialog.get_employee_data()
                employee_id = self.db_manager.add_employee(
                    employee_data['name'],
                    employee_data['role'],
                    employee_data['salary'],
                    employee_data['contact'],
                    datetime.strptime(employee_data['joining_date'], "%Y-%m-%d").date()
                )
                
                self.db_manager.log_activity(
                    "ADD_EMPLOYEE",
                    f"Added new employee: {employee_data['name']}",
                    self.current_user['id']
                )
                
                QMessageBox.information(self, "Success", "Employee added successfully!")
                self.load_employees()
                
            except Exception as e:
                QMessageBox.critical(self, "Database Error", f"Failed to add employee: {str(e)}")
    
    def edit_employee(self, employee):
        """Edit existing employee"""
        dialog = AddEmployeeDialog(self.db_manager, self, employee)
        if dialog.exec() == QDialog.Accepted:
            try:
                employee_data = dialog.get_employee_data()
                
                query = '''
                    UPDATE employees 
                    SET name = ?, role = ?, salary = ?, contact = ?, joining_date = ?
                    WHERE id = ?
                '''
                self.db_manager.execute_update(query, (
                    employee_data['name'],
                    employee_data['role'],
                    employee_data['salary'],
                    employee_data['contact'],
                    employee_data['joining_date'],
                    employee['id']
                ))
                
                self.db_manager.log_activity(
                    "EDIT_EMPLOYEE",
                    f"Updated employee: {employee_data['name']}",
                    self.current_user['id']
                )
                
                QMessageBox.information(self, "Success", "Employee updated successfully!")
                self.load_employees()
                
            except Exception as e:
                QMessageBox.critical(self, "Database Error", f"Failed to update employee: {str(e)}")
    
    def view_employee(self, employee):
        """View employee details"""
        from PySide6.QtWidgets import QTextEdit
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Employee Details - {employee['name']}")
        dialog.setFixedSize(500, 400)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Employee details
        details_text = f"""
<b>Employee Information:</b><br>
Name: {employee['name']}<br>
Role: {employee['role']}<br>
Salary: Rs. {employee['salary']:,.2f}<br>
Contact: {employee['contact'] or 'N/A'}<br>
Joining Date: {employee['joining_date']}<br>
Status: {'Active' if employee['is_active'] else 'Inactive'}
        """
        
        details_edit = QTextEdit()
        details_edit.setHtml(details_text)
        details_edit.setReadOnly(True)
        details_edit.setMaximumHeight(150)
        layout.addWidget(details_edit)
        
        # Calculate tenure
        joining_date = datetime.strptime(employee['joining_date'], "%Y-%m-%d")
        tenure = datetime.now() - joining_date
        years = tenure.days // 365
        months = (tenure.days % 365) // 30
        
        tenure_text = f"<b>Tenure:</b> {years} years, {months} months"
        tenure_label = QLabel(tenure_text)
        layout.addWidget(tenure_label)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec()
    
    def delete_employee(self, employee):
        """Delete employee (Admin only)"""
        if self.current_user['role'] != 'Admin':
            QMessageBox.warning(self, "Permission Denied", "Only administrators can delete employees.")
            return
        
        reply = QMessageBox.question(
            self,
            "Delete Employee",
            f"Are you sure you want to delete employee '{employee['name']}'?\n\n"
            "This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Soft delete by setting is_active to 0
                query = 'UPDATE employees SET is_active = 0 WHERE id = ?'
                self.db_manager.execute_update(query, (employee['id'],))
                
                self.db_manager.log_activity(
                    "DELETE_EMPLOYEE",
                    f"Deleted employee: {employee['name']}",
                    self.current_user['id']
                )
                
                QMessageBox.information(self, "Success", "Employee deleted successfully!")
                self.load_employees()
                
            except Exception as e:
                QMessageBox.critical(self, "Database Error", f"Failed to delete employee: {str(e)}")
    
    def generate_salary_report(self):
        """Generate salary report"""
        try:
            employees = self.db_manager.get_employees()
            
            # Create report content
            report_content = "EMPLOYEE SALARY REPORT\n"
            report_content += "=" * 60 + "\n\n"
            report_content += f"Generated on: {QDate.currentDate().toString('yyyy-MM-dd')}\n"
            report_content += f"Total Employees: {len(employees)}\n"
            report_content += f"Total Monthly Salary: Rs. {sum(e['salary'] for e in employees):,.2f}\n\n"
            
            report_content += f"{'Name':<25} {'Role':<15} {'Salary':>15}\n"
            report_content += "-" * 60 + "\n"
            
            for employee in employees:
                report_content += f"{employee['name']:<25} {employee['role']:<15} Rs. {employee['salary']:>12,.2f}\n"
            
            # Show report in dialog
            from PySide6.QtWidgets import QTextEdit
            
            dialog = QDialog(self)
            dialog.setWindowTitle("Salary Report")
            dialog.setFixedSize(600, 500)
            
            layout = QVBoxLayout(dialog)
            layout.setSpacing(10)
            layout.setContentsMargins(10, 10, 10, 10)
            
            text_edit = QTextEdit()
            text_edit.setPlainText(report_content)
            text_edit.setReadOnly(True)
            text_edit.setFontFamily("Courier New")
            layout.addWidget(text_edit)
            
            button_layout = QHBoxLayout()
            
            export_btn = QPushButton("Export to File")
            export_btn.clicked.connect(lambda: self.export_salary_report(report_content))
            button_layout.addWidget(export_btn)
            
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(dialog.accept)
            button_layout.addWidget(close_btn)
            
            layout.addLayout(button_layout)
            dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate salary report: {str(e)}")
    
    def export_salary_report(self, report_content: str):
        """Export salary report to file"""
        from PySide6.QtWidgets import QFileDialog
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Salary Report",
            f"Salary_Report_{QDate.currentDate().toString('yyyy-MM-dd')}.txt",
            "Text Files (*.txt)"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as file:
                    file.write(report_content)
                
                QMessageBox.information(self, "Success", f"Salary report exported to {filename}")
                
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export report: {str(e)}")
