import sqlite3
import shutil
import os
from datetime import datetime, date, timedelta
from typing import Optional

class BackupManager:
    def __init__(self, db_manager, backup_dir: str = "backups"):
        self.db_manager = db_manager
        self.backup_dir = backup_dir
        self.ensure_backup_directory()
    
    def ensure_backup_directory(self):
        """Create backup directory if it doesn't exist"""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
    
    def should_backup(self) -> bool:
        """Check if daily backup is needed.

        SQLite's CURRENT_TIMESTAMP is UTC. If we compare that raw timestamp to the
        local date in Python right after midnight, we can mistakenly think we
        haven't backed up "today" yet and run multiple backups.

        To avoid UTC vs local mismatches, compare dates inside SQLite using
        the 'localtime' modifier.
        """
        query = """
            SELECT
                MAX(DATE(created_at, 'localtime')) AS last_backup_day,
                DATE('now', 'localtime') AS today_day
            FROM backup_logs
        """
        result = self.db_manager.execute_query(query)
        if not result:
            return True

        last_backup_day = result[0].get("last_backup_day")
        today_day = result[0].get("today_day")

        if not last_backup_day or not today_day:
            return True

        # YYYY-MM-DD strings compare correctly lexicographically.
        return last_backup_day < today_day
    
    def create_backup(self) -> str:
        """Create database backup"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"rajput_gas_backup_{timestamp}.db"
        backup_path = os.path.join(self.backup_dir, backup_filename)
        
        # Copy database file
        shutil.copy2(self.db_manager.db_path, backup_path)
        
        # Log backup
        backup_size = os.path.getsize(backup_path)
        query = 'INSERT INTO backup_logs (backup_path, backup_size) VALUES (?, ?)'
        self.db_manager.execute_update(query, (backup_path, backup_size))
        
        return backup_path
    
    def restore_backup(self, backup_path: str) -> bool:
        """Restore database from backup"""
        try:
            # Create current backup before restore
            current_backup = self.create_backup()
            
            # Restore from selected backup
            shutil.copy2(backup_path, self.db_manager.db_path)
            
            # Log restore activity
            self.db_manager.log_activity("RESTORE", f"Database restored from {backup_path}")
            
            return True
        except Exception as e:
            # Restore from current backup if restore fails
            if os.path.exists(current_backup):
                shutil.copy2(current_backup, self.db_manager.db_path)
            return False
    
    def get_backup_history(self, days: int = 30) -> list:
        """Get backup history for specified number of days"""
        cutoff_day = (date.today() - timedelta(days=days)).isoformat()
        query = '''
            SELECT * FROM backup_logs 
            WHERE DATE(created_at, 'localtime') >= ?
            ORDER BY created_at DESC
        '''
        return self.db_manager.execute_query(query, (cutoff_day,))
    
    def cleanup_old_backups(self, days_to_keep: int = 30):
        """Remove backups older than specified days"""
        cutoff_day = (date.today() - timedelta(days=days_to_keep)).isoformat()
        query = '''
            SELECT backup_path FROM backup_logs 
            WHERE DATE(created_at, 'localtime') < ?
        '''
        old_backups = self.db_manager.execute_query(query, (cutoff_day,))
        
        for backup in old_backups:
            backup_path = backup['backup_path']
            if os.path.exists(backup_path):
                try:
                    os.remove(backup_path)
                    # Remove from logs
                    query = 'DELETE FROM backup_logs WHERE backup_path = ?'
                    self.db_manager.execute_update(query, (backup_path,))
                except Exception as e:
                    print(f"Failed to delete old backup {backup_path}: {e}")
