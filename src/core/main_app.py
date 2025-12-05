#!/usr/bin/env python3
"""
Rajput Gas Control System - Main Application Class
Core application logic and initialization
"""

import sys
import os
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox
from PySide6.QtCore import Qt, QTimer
from src.database_module import DatabaseManager
from src.components.auth import LoginDialog
from src.ui.main_window import MainWindow
from src.components.backup import BackupManager

class RajputGasManagement(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        self.setApplicationName("Rajput Gas Control System")
        self.setApplicationVersion("1.0")
        self.setOrganizationName("Rajput Gas Ltd.")
        
        # Initialize database
        self.db = DatabaseManager()
        
        # Initialize backup manager
        self.backup_manager = BackupManager(self.db)
        
        # Setup automatic daily backup
        self.setup_automatic_backup()
        
        # Show login dialog
        self.show_login()
    
    def show_login(self):
        login_dialog = LoginDialog(self.db)
        if login_dialog.exec() == LoginDialog.Accepted:
            self.current_user = login_dialog.get_user()
            self.show_main_window()
        else:
            sys.exit()
    
    def show_main_window(self):
        self.main_window = MainWindow(self.db, self.current_user)
        self.main_window.show()
        
        # Log successful login
        self.db.log_activity("LOGIN", f"User {self.current_user['username']} logged in")
    
    def setup_automatic_backup(self):
        """Setup automatic daily backup (runs once per day)"""
        self.backup_timer = QTimer()
        self.backup_timer.timeout.connect(self.check_backup_time)
        self.backup_timer.start(60000)  # Check every minute
        # Initial check
        self.check_backup_time()
    
    def check_backup_time(self):
        """Check if daily backup should run; runs if last backup is older than today"""
        try:
            if self.backup_manager.should_backup():
                backup_path = self.backup_manager.create_backup()
                if backup_path:
                    print(f"Automatic backup created: {backup_path}")
                # Optional cleanup of backups older than 30 days
                try:
                    self.backup_manager.cleanup_old_backups(days_to_keep=30)
                except Exception:
                    pass
        except Exception as e:
            print(f"Automatic backup check failed: {str(e)}")

def main():
    """Main entry point"""
    app = RajputGasManagement(sys.argv)
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
