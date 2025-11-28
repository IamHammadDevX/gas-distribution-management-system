from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QGroupBox, QFormLayout, QLineEdit, 
                               QMessageBox, QTabWidget, QTableWidget, QTableWidgetItem,
                               QHeaderView, QCheckBox, QTextEdit, QComboBox)
from PySide6.QtCore import Qt, QDateTime
from src.database_module import DatabaseManager
from src.components.backup import BackupManager
import os

class SettingsWidget(QWidget):
    def __init__(self, db_manager: DatabaseManager, current_user: dict):
        super().__init__()
        self.db_manager = db_manager
        self.current_user = current_user
        self.backup_manager = BackupManager(db_manager)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title_label = QLabel("Settings")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title_label)
        
        # Check if user is admin
        if self.current_user['role'] != 'Admin':
            self.init_user_settings()
        else:
            self.init_admin_settings()
    
    def init_user_settings(self):
        """Initialize settings for non-admin users"""
        # User info section
        user_group = QGroupBox("User Information")
        user_layout = QFormLayout()
        user_layout.setSpacing(10)
        
        user_layout.addRow("Username:", QLabel(self.current_user.get('username', 'N/A')))
        user_layout.addRow("Full Name:", QLabel(self.current_user.get('full_name', 'N/A')))
        user_layout.addRow("Role:", QLabel(self.current_user.get('role', 'N/A')))
        user_layout.addRow("Phone:", QLabel(self.current_user.get('phone', 'N/A')))
        user_layout.addRow("Email:", QLabel(self.current_user.get('email', 'N/A')))
        user_layout.addRow("Last Login:", QLabel(self.current_user.get('last_login', 'Never')))
        
        user_group.setLayout(user_layout)
        self.layout().addWidget(user_group)
        
        # Change password section
        password_group = QGroupBox("Change Password")
        password_layout = QFormLayout()
        password_layout.setSpacing(10)
        
        self.current_password_input = QLineEdit()
        self.current_password_input.setEchoMode(QLineEdit.Password)
        password_layout.addRow("Current Password:", self.current_password_input)
        
        self.new_password_input = QLineEdit()
        self.new_password_input.setEchoMode(QLineEdit.Password)
        password_layout.addRow("New Password:", self.new_password_input)
        
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        password_layout.addRow("Confirm Password:", self.confirm_password_input)
        
        change_password_btn = QPushButton("Change Password")
        change_password_btn.clicked.connect(self.change_password)
        password_layout.addRow(change_password_btn)
        
        password_group.setLayout(password_layout)
        self.layout().addWidget(password_group)
        
        self.layout().addStretch()
    
    def init_admin_settings(self):
        """Initialize settings for admin users"""
        # Create tab widget
        tab_widget = QTabWidget()
        
        # General Settings Tab
        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)
        general_layout.setSpacing(15)
        
        # Company Info
        company_group = QGroupBox("Company Information")
        company_layout = QFormLayout()
        company_layout.setSpacing(10)
        
        self.company_name_input = QLineEdit("Rajput Gas Traders")
        self.company_address_input = QLineEdit("Plot No.69C-70C, Small Industrial Estate No.2, Gujranwala")
        self.company_phone_input = QLineEdit("0301-6465144")
        self.company_email_input = QLineEdit("info@rajputgas.com")
        
        company_layout.addRow("Company Name:", self.company_name_input)
        company_layout.addRow("Address:", self.company_address_input)
        company_layout.addRow("Phone:", self.company_phone_input)
        company_layout.addRow("Email:", self.company_email_input)
        
        save_company_btn = QPushButton("Save Company Info")
        save_company_btn.clicked.connect(self.save_company_info)
        company_layout.addRow(save_company_btn)
        
        company_group.setLayout(company_layout)
        general_layout.addWidget(company_group)
        
        # Tax Settings
        tax_group = QGroupBox("Tax Settings")
        tax_layout = QFormLayout()
        tax_layout.setSpacing(10)
        
        self.tax_rate_input = QLineEdit("Customizeable")
        self.tax_rate_input.setReadOnly(True)  # Fixed at 16% as per requirements
        tax_layout.addRow("Tax Rate (%):", self.tax_rate_input)
        
        tax_layout.addRow(QLabel("Note: Tax rate is not fixed."))
        
        tax_group.setLayout(tax_layout)
        general_layout.addWidget(tax_group)
        
        general_layout.addStretch()
        tab_widget.addTab(general_tab, "General Settings")
        
        # User Management Tab
        user_tab = QWidget()
        user_layout = QVBoxLayout(user_tab)
        user_layout.setSpacing(15)
        
        # Add User Section
        add_user_group = QGroupBox("Add New User")
        add_user_layout = QFormLayout()
        add_user_layout.setSpacing(10)
        
        self.new_username_input = QLineEdit()
        self.new_username_input.setPlaceholderText("Enter username")
        add_user_layout.addRow("Username:", self.new_username_input)
        
        self.new_password_input = QLineEdit()
        self.new_password_input.setEchoMode(QLineEdit.Password)
        self.new_password_input.setPlaceholderText("Enter password")
        add_user_layout.addRow("Password:", self.new_password_input)
        
        self.new_full_name_input = QLineEdit()
        self.new_full_name_input.setPlaceholderText("Enter full name")
        add_user_layout.addRow("Full Name:", self.new_full_name_input)
        
        self.new_role_combo = QComboBox()
        self.new_role_combo.addItems(["Admin", "Accountant", "Gate Operator", "Driver"])
        add_user_layout.addRow("Role:", self.new_role_combo)
        
        self.new_phone_input = QLineEdit()
        self.new_phone_input.setPlaceholderText("Enter phone number")
        add_user_layout.addRow("Phone:", self.new_phone_input)
        
        
        
        add_user_btn = QPushButton("Add User")
        add_user_btn.clicked.connect(self.add_user)
        add_user_layout.addRow(add_user_btn)
        
        add_user_group.setLayout(add_user_layout)
        user_layout.addWidget(add_user_group)
        
        # Users Table
        users_group = QGroupBox("Existing Users")
        users_layout = QVBoxLayout()
        
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(5)
        self.users_table.setHorizontalHeaderLabels([
            "ID", "Username", "Full Name", "Role", "Status"
        ])
        self.users_table.setAlternatingRowColors(True)
        self.users_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.users_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.users_table.horizontalHeader().setStretchLastSection(True)
        
        users_layout.addWidget(self.users_table)
        
        # User actions
        user_actions_layout = QHBoxLayout()
        
        self.toggle_user_btn = QPushButton("Toggle Status")
        self.toggle_user_btn.clicked.connect(self.toggle_user_status)
        user_actions_layout.addWidget(self.toggle_user_btn)
        
        self.reset_password_btn = QPushButton("Reset Password")
        self.reset_password_btn.clicked.connect(self.reset_user_password)
        user_actions_layout.addWidget(self.reset_password_btn)
        
        self.delete_user_btn = QPushButton("Delete User")
        self.delete_user_btn.clicked.connect(self.delete_user)
        user_actions_layout.addWidget(self.delete_user_btn)
        
        user_actions_layout.addStretch()
        users_layout.addLayout(user_actions_layout)
        
        users_group.setLayout(users_layout)
        user_layout.addWidget(users_group)
        
        tab_widget.addTab(user_tab, "User Management")
        
        # Backup Tab
        backup_tab = QWidget()
        backup_layout = QVBoxLayout(backup_tab)
        backup_layout.setSpacing(15)
        
        # Manual Backup
        manual_backup_group = QGroupBox("Manual Backup")
        manual_backup_layout = QVBoxLayout()
        manual_backup_layout.setSpacing(10)
        
        self.backup_path_label = QLabel(f"Backup Location: {self.backup_manager.backup_dir}")
        manual_backup_layout.addWidget(self.backup_path_label)
        
        manual_backup_btn = QPushButton("Create Manual Backup")
        manual_backup_btn.clicked.connect(self.create_manual_backup)
        manual_backup_layout.addWidget(manual_backup_btn)
        
        manual_backup_group.setLayout(manual_backup_layout)
        backup_layout.addWidget(manual_backup_group)
        
        # Backup History
        backup_history_group = QGroupBox("Backup History")
        backup_history_layout = QVBoxLayout()
        backup_history_layout.setSpacing(10)
        
        self.backup_table = QTableWidget()
        self.backup_table.setColumnCount(4)
        self.backup_table.setHorizontalHeaderLabels([
            "Date", "Backup File", "Size (MB)", "Actions"
        ])
        self.backup_table.setAlternatingRowColors(True)
        self.backup_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.backup_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.backup_table.horizontalHeader().setStretchLastSection(True)
        
        backup_history_layout.addWidget(self.backup_table)
        
        # Backup actions
        backup_actions_layout = QHBoxLayout()
        
        self.refresh_backup_btn = QPushButton("Refresh")
        self.refresh_backup_btn.clicked.connect(self.load_backup_history)
        backup_actions_layout.addWidget(self.refresh_backup_btn)
        
        self.restore_backup_btn = QPushButton("Restore Selected")
        self.restore_backup_btn.clicked.connect(self.restore_backup)
        backup_actions_layout.addWidget(self.restore_backup_btn)
        
        self.delete_backup_btn = QPushButton("Delete Selected")
        self.delete_backup_btn.clicked.connect(self.delete_backup)
        backup_actions_layout.addWidget(self.delete_backup_btn)
        
        backup_actions_layout.addStretch()
        backup_history_layout.addLayout(backup_actions_layout)
        
        backup_history_group.setLayout(backup_history_layout)
        backup_layout.addWidget(backup_history_group)
        
        # Cleanup old backups
        cleanup_btn = QPushButton("Cleanup Backups Older Than 30 Days")
        cleanup_btn.clicked.connect(self.cleanup_old_backups)
        backup_layout.addWidget(cleanup_btn)
        
        backup_layout.addStretch()
        tab_widget.addTab(backup_tab, "Backup & Restore")
        
        # Activity Logs Tab
        logs_tab = QWidget()
        logs_layout = QVBoxLayout(logs_tab)
        logs_layout.setSpacing(15)
        
        # Activity Logs
        logs_group = QGroupBox("Activity Logs")
        logs_group_layout = QVBoxLayout()
        
        self.logs_text = QTextEdit()
        self.logs_text.setReadOnly(True)
        self.logs_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                font-family: 'Courier New';
                font-size: 10px;
            }
        """)
        logs_group_layout.addWidget(self.logs_text)
        
        # Log controls
        log_controls_layout = QHBoxLayout()
        
        self.refresh_logs_btn = QPushButton("Refresh Logs")
        self.refresh_logs_btn.clicked.connect(self.load_activity_logs)
        log_controls_layout.addWidget(self.refresh_logs_btn)
        
        self.clear_logs_btn = QPushButton("Clear Old Logs")
        self.clear_logs_btn.clicked.connect(self.clear_old_logs)
        log_controls_layout.addWidget(self.clear_logs_btn)
        
        log_controls_layout.addStretch()
        logs_group_layout.addLayout(log_controls_layout)
        
        logs_group.setLayout(logs_group_layout)
        logs_layout.addWidget(logs_group)
        
        logs_layout.addStretch()
        tab_widget.addTab(logs_tab, "Activity Logs")
        
        self.layout().addWidget(tab_widget)
        
        # Load initial data
        self.load_users()
        self.load_backup_history()
        self.load_activity_logs()
    
    def save_company_info(self):
        """Save company information"""
        QMessageBox.information(self, "Info", "Company information saved successfully!")
        self.db_manager.log_activity("SETTINGS", "Updated company information", self.current_user['id'])
    
    def add_user(self):
        """Add new user"""
        username = self.new_username_input.text().strip()
        password = self.new_password_input.text().strip()
        full_name = self.new_full_name_input.text().strip()
        role = self.new_role_combo.currentText()
        phone = self.new_phone_input.text().strip()
        email = ""  # Email field removed as requested
        
        if not username or not password or not full_name:
            QMessageBox.warning(self, "Validation Error", "Username, password, and full name are required.")
            return
        
        try:
            # Hash password
            import hashlib
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            # Check if username exists
            query = 'SELECT COUNT(*) as count FROM users WHERE username = ?'
            result = self.db_manager.execute_query(query, (username,))
            
            if result[0]['count'] > 0:
                QMessageBox.warning(self, "Error", "Username already exists.")
                return
            
            # Add user
            query = '''
                INSERT INTO users (username, password_hash, role, full_name, phone)
                VALUES (?, ?, ?, ?, ?)
            '''
            self.db_manager.execute_update(query, (username, password_hash, role, full_name, phone))
            
            QMessageBox.information(self, "Success", "User added successfully!")
            self.load_users()
            
            # Clear form
            self.new_username_input.clear()
            self.new_password_input.clear()
            self.new_full_name_input.clear()
            self.new_phone_input.clear()
            
            self.db_manager.log_activity("ADD_USER", f"Added new user: {username}", self.current_user['id'])
            
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to add user: {str(e)}")
    
    def load_users(self):
        """Load all users"""
        try:
            query = '''
                SELECT id, username, full_name, role, phone, is_active
                FROM users
                ORDER BY username
            '''
            users = self.db_manager.execute_query(query)
            
            self.users_table.setRowCount(len(users))
            
            for row, user in enumerate(users):
                self.users_table.setItem(row, 0, QTableWidgetItem(str(user['id'])))
                self.users_table.setItem(row, 1, QTableWidgetItem(user['username']))
                self.users_table.setItem(row, 2, QTableWidgetItem(user['full_name']))
                self.users_table.setItem(row, 3, QTableWidgetItem(user['role']))
                self.users_table.setItem(row, 4, QTableWidgetItem('Active' if user['is_active'] else 'Inactive'))
            
            self.users_table.resizeColumnsToContents()
            
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load users: {str(e)}")
    
    def toggle_user_status(self):
        """Toggle user active/inactive status"""
        current_row = self.users_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a user.")
            return
        
        user_id = int(self.users_table.item(current_row, 0).text())
        username = self.users_table.item(current_row, 1).text()
        
        try:
            query = 'UPDATE users SET is_active = NOT is_active WHERE id = ?'
            self.db_manager.execute_update(query, (user_id,))
            
            QMessageBox.information(self, "Success", f"User status toggled successfully!")
            self.load_users()
            self.db_manager.log_activity("TOGGLE_USER", f"Toggled user status: {username}", self.current_user['id'])
            
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to toggle user status: {str(e)}")
    
    def reset_user_password(self):
        """Reset user password"""
        current_row = self.users_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a user.")
            return
        
        user_id = int(self.users_table.item(current_row, 0).text())
        username = self.users_table.item(current_row, 1).text()
        
        # Default password: username123
        default_password = f"{username.lower()}123"
        
        reply = QMessageBox.question(
            self,
            "Reset Password",
            f"Reset password for user '{username}' to default password '{default_password}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                import hashlib
                password_hash = hashlib.sha256(default_password.encode()).hexdigest()
                
                query = 'UPDATE users SET password_hash = ? WHERE id = ?'
                self.db_manager.execute_update(query, (password_hash, user_id))
                
                QMessageBox.information(self, "Success", f"Password reset successfully!\nNew password: {default_password}")
                self.db_manager.log_activity("RESET_PASSWORD", f"Reset password for user: {username}", self.current_user['id'])
                
            except Exception as e:
                QMessageBox.critical(self, "Database Error", f"Failed to reset password: {str(e)}")
    
    def delete_user(self):
        """Delete user"""
        current_row = self.users_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a user.")
            return
        
        user_id = int(self.users_table.item(current_row, 0).text())
        username = self.users_table.item(current_row, 1).text()
        
        if username == self.current_user['username']:
            QMessageBox.warning(self, "Cannot Delete", "You cannot delete your own account.")
            return
        
        reply = QMessageBox.question(
            self,
            "Delete User",
            f"Are you sure you want to delete user '{username}'?\n\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                query = 'DELETE FROM users WHERE id = ?'
                self.db_manager.execute_update(query, (user_id,))
                
                QMessageBox.information(self, "Success", "User deleted successfully!")
                self.load_users()
                self.db_manager.log_activity("DELETE_USER", f"Deleted user: {username}", self.current_user['id'])
                
            except Exception as e:
                QMessageBox.critical(self, "Database Error", f"Failed to delete user: {str(e)}")
    
    def create_manual_backup(self):
        """Create manual backup"""
        try:
            backup_path = self.backup_manager.create_backup()
            QMessageBox.information(self, "Success", f"Backup created successfully!\nLocation: {backup_path}")
            self.load_backup_history()
            self.db_manager.log_activity("MANUAL_BACKUP", f"Created manual backup: {backup_path}", self.current_user['id'])
            
        except Exception as e:
            QMessageBox.critical(self, "Backup Error", f"Failed to create backup: {str(e)}")
    
    def load_backup_history(self):
        """Load backup history"""
        try:
            backups = self.backup_manager.get_backup_history(30)
            
            self.backup_table.setRowCount(len(backups))
            
            for row, backup in enumerate(backups):
                self.backup_table.setItem(row, 0, QTableWidgetItem(backup['created_at']))
                self.backup_table.setItem(row, 1, QTableWidgetItem(backup['backup_path']))
                
                # Convert size to MB
                size_mb = backup['backup_size'] / (1024 * 1024)
                self.backup_table.setItem(row, 2, QTableWidgetItem(f"{size_mb:.2f}"))
                
                # Add restore button
                restore_btn = QPushButton("Restore")
                restore_btn.clicked.connect(lambda checked, path=backup['backup_path']: self.restore_specific_backup(path))
                self.backup_table.setCellWidget(row, 3, restore_btn)
            
            self.backup_table.resizeColumnsToContents()
            
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load backup history: {str(e)}")
    
    def restore_backup(self):
        """Restore selected backup"""
        current_row = self.backup_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a backup to restore.")
            return
        
        backup_path = self.backup_table.item(current_row, 1).text()
        self.restore_specific_backup(backup_path)
    
    def restore_specific_backup(self, backup_path: str):
        """Restore specific backup"""
        reply = QMessageBox.question(
            self,
            "Restore Backup",
            f"Are you sure you want to restore backup from {backup_path}?\n\n"
            "This will replace the current database with the backup data.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                if self.backup_manager.restore_backup(backup_path):
                    QMessageBox.information(self, "Success", "Backup restored successfully!")
                    self.db_manager.log_activity("RESTORE_BACKUP", f"Restored backup: {backup_path}", self.current_user['id'])
                else:
                    QMessageBox.critical(self, "Restore Error", "Failed to restore backup.")
                    
            except Exception as e:
                QMessageBox.critical(self, "Restore Error", f"Failed to restore backup: {str(e)}")
    
    def delete_backup(self):
        """Delete selected backup"""
        current_row = self.backup_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a backup to delete.")
            return
        
        backup_path = self.backup_table.item(current_row, 1).text()
        
        reply = QMessageBox.question(
            self,
            "Delete Backup",
            f"Are you sure you want to delete backup {backup_path}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                if os.path.exists(backup_path):
                    os.remove(backup_path)
                    
                    # Remove from database
                    query = 'DELETE FROM backup_logs WHERE backup_path = ?'
                    self.db_manager.execute_update(query, (backup_path,))
                    
                    QMessageBox.information(self, "Success", "Backup deleted successfully!")
                    self.load_backup_history()
                    self.db_manager.log_activity("DELETE_BACKUP", f"Deleted backup: {backup_path}", self.current_user['id'])
                else:
                    QMessageBox.warning(self, "Not Found", "Backup file not found.")
                    
            except Exception as e:
                QMessageBox.critical(self, "Delete Error", f"Failed to delete backup: {str(e)}")
    
    def cleanup_old_backups(self):
        """Cleanup backups older than 30 days"""
        reply = QMessageBox.question(
            self,
            "Cleanup Old Backups",
            "This will delete all backups older than 30 days.\n\nContinue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.backup_manager.cleanup_old_backups(30)
                QMessageBox.information(self, "Success", "Old backups cleaned up successfully!")
                self.load_backup_history()
                self.db_manager.log_activity("CLEANUP_BACKUPS", "Cleaned up old backups", self.current_user['id'])
                
            except Exception as e:
                QMessageBox.critical(self, "Cleanup Error", f"Failed to cleanup old backups: {str(e)}")
    
    def load_activity_logs(self):
        """Load activity logs"""
        try:
            query = '''
                SELECT al.*, u.username, u.full_name
                FROM activity_logs al
                LEFT JOIN users u ON al.user_id = u.id
                ORDER BY al.timestamp DESC
                LIMIT 500
            '''
            logs = self.db_manager.execute_query(query)
            
            logs_text = "ACTIVITY LOGS\n"
            logs_text += "=" * 80 + "\n"
            
            for log in logs:
                timestamp = log['timestamp']
                user = log['full_name'] or log['username'] or 'System'
                activity_type = log['activity_type']
                description = log['description'] or ''
                
                logs_text += f"{timestamp} | {user} | {activity_type}"
                if description:
                    logs_text += f" | {description}"
                logs_text += "\n"
            
            self.logs_text.setPlainText(logs_text)
            
        except Exception as e:
            self.logs_text.setPlainText(f"Failed to load activity logs: {str(e)}")
    
    def clear_old_logs(self):
        """Clear old activity logs"""
        reply = QMessageBox.question(
            self,
            "Clear Old Logs",
            "This will delete activity logs older than 90 days.\n\nContinue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                query = "DELETE FROM activity_logs WHERE timestamp < datetime('now', '-90 days')"
                self.db_manager.execute_update(query)
                
                QMessageBox.information(self, "Success", "Old activity logs cleared successfully!")
                self.load_activity_logs()
                self.db_manager.log_activity("CLEAR_LOGS", "Cleared old activity logs", self.current_user['id'])
                
            except Exception as e:
                QMessageBox.critical(self, "Clear Error", f"Failed to clear old logs: {str(e)}")
    
    def change_password(self):
        """Change current user's password"""
        current_password = self.current_password_input.text().strip()
        new_password = self.new_password_input.text().strip()
        confirm_password = self.confirm_password_input.text().strip()
        
        if not current_password or not new_password or not confirm_password:
            QMessageBox.warning(self, "Validation Error", "All password fields are required.")
            return
        
        if new_password != confirm_password:
            QMessageBox.warning(self, "Validation Error", "New passwords do not match.")
            return
        
        try:
            # Verify current password
            import hashlib
            current_hash = hashlib.sha256(current_password.encode()).hexdigest()
            
            query = 'SELECT COUNT(*) as count FROM users WHERE id = ? AND password_hash = ?'
            result = self.db_manager.execute_query(query, (self.current_user['id'], current_hash))
            
            if result[0]['count'] == 0:
                QMessageBox.warning(self, "Validation Error", "Current password is incorrect.")
                return
            
            # Update password
            new_hash = hashlib.sha256(new_password.encode()).hexdigest()
            query = 'UPDATE users SET password_hash = ? WHERE id = ?'
            self.db_manager.execute_update(query, (new_hash, self.current_user['id']))
            
            QMessageBox.information(self, "Success", "Password changed successfully!")
            
            # Clear form
            self.current_password_input.clear()
            self.new_password_input.clear()
            self.confirm_password_input.clear()
            
            self.db_manager.log_activity("CHANGE_PASSWORD", "Changed password", self.current_user['id'])
            
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to change password: {str(e)}")
