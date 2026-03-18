import os
import shutil
import subprocess
from pathlib import Path
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

    def _resolve_pg_tool(self, tool_name: str) -> Optional[str]:
        """Resolve PostgreSQL client tool path (pg_dump/pg_restore)."""
        found = shutil.which(tool_name)
        if found:
            return found

        pg_bin = os.environ.get("PGBIN")
        if pg_bin:
            candidate = Path(pg_bin) / (f"{tool_name}.exe" if os.name == "nt" else tool_name)
            if candidate.exists():
                return str(candidate)

        if os.name == "nt":
            base = Path("C:/Program Files/PostgreSQL")
            if base.exists():
                versions = sorted((p for p in base.iterdir() if p.is_dir()), reverse=True)
                for ver in versions:
                    candidate = ver / "bin" / f"{tool_name}.exe"
                    if candidate.exists():
                        return str(candidate)

        return None
    
    def should_backup(self) -> bool:
        """Check if a backup already exists for the current local day.

        For PostgreSQL we store `created_at` as TIMESTAMPTZ and pin the session
        timezone in the DB connection, so `created_at::date` and `CURRENT_DATE`
        both use that local timezone.
        """
        query = """
            SELECT
                MAX(created_at::date) AS last_backup_day,
                CURRENT_DATE AS today_day
            FROM backup_logs
        """
        result = self.db_manager.execute_query(query)
        if not result or not result[0].get("today_day"):
            return True

        last_backup_day = result[0].get("last_backup_day")
        today_day = result[0].get("today_day")
        if not last_backup_day:
            return True

        return last_backup_day < today_day
    
    def create_backup(self) -> str:
        """Create a logical PostgreSQL backup using pg_dump."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"rajput_gas_backup_{timestamp}.dump"
        backup_path = os.path.join(self.backup_dir, backup_filename)
        temp_backup_path = f"{backup_path}.tmp"
        
        pg_dump = self._resolve_pg_tool("pg_dump")
        if not pg_dump:
            raise RuntimeError(
                "pg_dump not found on PATH. Install PostgreSQL client tools to enable backups."
            )

        # Prefer environment-based connection (PGHOST/PGDATABASE/PGUSER/PGPASSWORD) to avoid
        # putting credentials on the command line. Fall back to DATABASE_URL/DSN if needed.
        dbname_arg = os.environ.get("PGDATABASE") or os.environ.get("DATABASE_URL") or self.db_manager.dsn

        # Custom format is compact and supports pg_restore.
        args = [
            pg_dump,
            "--format=custom",
            "--no-owner",
            "--no-privileges",
            "--file",
            temp_backup_path,
            "--dbname",
            dbname_arg,
        ]
        try:
            subprocess.run(args, check=True)
            # Atomic finalize to avoid exposing partial/corrupt dump files after interruption.
            os.replace(temp_backup_path, backup_path)
        finally:
            if os.path.exists(temp_backup_path):
                try:
                    os.remove(temp_backup_path)
                except Exception:
                    pass
        
        # Log backup
        backup_size = os.path.getsize(backup_path)
        query = 'INSERT INTO backup_logs (backup_path, backup_size) VALUES (?, ?)'
        self.db_manager.execute_update(query, (backup_path, backup_size))
        
        return backup_path
    
    def restore_backup(self, backup_path: str) -> bool:
        """Restore database from a pg_dump custom-format backup using pg_restore."""
        try:
            if not os.path.exists(backup_path):
                raise FileNotFoundError(f"Backup file not found: {backup_path}")

            pg_restore = self._resolve_pg_tool("pg_restore")
            if not pg_restore:
                raise RuntimeError(
                    "pg_restore not found on PATH. Install PostgreSQL client tools to enable restore."
                )

            # Create current backup before restore (safety net)
            current_backup = self.create_backup()
            
            dbname_arg = os.environ.get("PGDATABASE") or os.environ.get("DATABASE_URL") or self.db_manager.dsn
            args = [
                pg_restore,
                "--clean",
                "--if-exists",
                "--single-transaction",
                "--exit-on-error",
                "--no-owner",
                "--no-privileges",
                "--dbname",
                dbname_arg,
                backup_path,
            ]
            subprocess.run(args, check=True)
            
            # Log restore activity
            self.db_manager.log_activity("RESTORE", f"Database restored from {backup_path}")
            
            return True
        except Exception as e:
            # If restore fails, the pre-restore backup remains available for manual recovery.
            return False
    
    def get_backup_history(self, days: int = 30) -> list:
        """Get backup history for specified number of days"""
        cutoff_day = (date.today() - timedelta(days=days)).isoformat()
        query = '''
            SELECT * FROM backup_logs 
            WHERE created_at::date >= ?
            ORDER BY created_at DESC
        '''
        return self.db_manager.execute_query(query, (cutoff_day,))
    
    def cleanup_old_backups(self, days_to_keep: int = 30):
        """Remove backups older than specified days"""
        cutoff_day = (date.today() - timedelta(days=days_to_keep)).isoformat()
        query = '''
            SELECT backup_path FROM backup_logs 
            WHERE created_at::date < ?
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
