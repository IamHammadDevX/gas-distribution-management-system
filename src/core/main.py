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
        if login_dialog.exec():
            self.current_user = login_dialog.get_user()
            self.main_window = MainWindow(self.db, self.current_user)
            self.main_window.show()
            self.log_activity("LOGIN", f"User {self.current_user['username']} logged in")
        else:
            sys.exit()
    
    def setup_automatic_backup(self):
        # Setup daily backup timer
        backup_timer = QTimer()
        backup_timer.timeout.connect(self.perform_daily_backup)
        # Check every hour if backup is needed
        backup_timer.start(3600000)  # 1 hour in milliseconds
        
        # Perform backup check on startup
        self.perform_daily_backup()
    
    def perform_daily_backup(self):
        if self.backup_manager.should_backup():
            try:
                backup_path = self.backup_manager.create_backup()
                self.log_activity("BACKUP", f"Automatic backup created: {backup_path}")
            except Exception as e:
                self.log_activity("BACKUP_ERROR", f"Automatic backup failed: {str(e)}")
    
    def log_activity(self, activity_type, description):
        try:
            self.db.log_activity(activity_type, description)
        except Exception as e:
            print(f"Failed to log activity: {e}")

def main():
    app = RajputGasManagement(sys.argv)
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
