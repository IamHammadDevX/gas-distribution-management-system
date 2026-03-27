import os
import re
import time as pytime
import random
from contextlib import contextmanager
from datetime import datetime, date, time, timedelta
from typing import Dict, List, Optional, Any
import json

try:
    import psycopg
    from psycopg.rows import dict_row
except Exception:  # pragma: no cover
    psycopg = None
    dict_row = None

try:
    from psycopg_pool import ConnectionPool
except Exception:  # pragma: no cover
    ConnectionPool = None

class DatabaseManager:
    def __init__(self, dsn: str | None = None):
        if psycopg is None:
            raise RuntimeError(
                "PostgreSQL support requires psycopg. Install dependencies from requirements.txt."
            )

        self.dsn = dsn or self._default_dsn()
        self.app_timezone = os.environ.get("APP_TIMEZONE", "Asia/Karachi")
        self.statement_timeout_ms = int(os.environ.get("PG_STATEMENT_TIMEOUT_MS", "30000"))
        self.lock_timeout_ms = int(os.environ.get("PG_LOCK_TIMEOUT_MS", "10000"))
        self.query_retries = max(0, int(os.environ.get("PG_QUERY_RETRIES", "2")))
        self.retry_backoff_ms = max(10, int(os.environ.get("PG_RETRY_BACKOFF_MS", "120")))

        self.pool = None
        if ConnectionPool is not None:
            self.pool = ConnectionPool(
                conninfo=self.dsn,
                min_size=1,
                max_size=int(os.environ.get("PG_POOL_MAX", "10")),
                timeout=float(os.environ.get("PG_POOL_TIMEOUT", "10")),
                configure=self._configure_connection,
            )

        self.init_database()

    @staticmethod
    def _default_dsn() -> str:
        # Preferred: standard DATABASE_URL, e.g. postgresql://user:pass@host:5432/dbname
        url = os.environ.get("DATABASE_URL")
        if url:
            return url

        host = os.environ.get("PGHOST", "127.0.0.1")
        port = os.environ.get("PGPORT", "5432")
        dbname = os.environ.get("PGDATABASE", "rajput_gas")
        user = os.environ.get("PGUSER", "rajput_gas_app")
        password = os.environ.get("PGPASSWORD", "")
        sslmode = os.environ.get("PGSSLMODE", "prefer")

        # psycopg "conninfo" format
        parts = [
            f"host={host}",
            f"port={port}",
            f"dbname={dbname}",
            f"user={user}",
            f"sslmode={sslmode}",
            "connect_timeout=10",
            "target_session_attrs=read-write",
            "application_name=rajput_gas_management",
        ]
        if password:
            parts.append(f"password={password}")
        return " ".join(parts)

    def _configure_connection(self, conn):
        # Keep date handling consistent across the app by pinning a session timezone.
        # This influences DATE(timestamp) and other time operations.
        with conn.cursor() as cur:
            cur.execute("SELECT set_config('TimeZone', %s, false)", (self.app_timezone,))
            # Make committed transactions durable on server crash (WAL).
            cur.execute("SET synchronous_commit TO on")
            cur.execute("SELECT set_config('statement_timeout', %s, false)", (f"{self.statement_timeout_ms}ms",))
            cur.execute("SELECT set_config('lock_timeout', %s, false)", (f"{self.lock_timeout_ms}ms",))
            cur.execute("SET idle_in_transaction_session_timeout TO '60000ms'")
        conn.commit()

    def _is_retryable_query_error(self, exc: Exception) -> bool:
        sqlstate = getattr(exc, "sqlstate", None)
        if sqlstate:
            if sqlstate.startswith("08"):
                return True
            if sqlstate in {"40001", "40P01", "53300", "57P01"}:
                return True
        if psycopg is not None:
            return isinstance(exc, (psycopg.OperationalError, psycopg.InterfaceError))
        return False

    @staticmethod
    def _is_retryable_write_error(exc: Exception) -> bool:
        sqlstate = getattr(exc, "sqlstate", None)
        return sqlstate in {"40001", "40P01"}

    @contextmanager
    def _connection(self):
        if self.pool is not None:
            with self.pool.connection() as conn:
                yield conn
            return

        with psycopg.connect(self.dsn, row_factory=dict_row) as conn:
            self._configure_connection(conn)
            yield conn

    @staticmethod
    def _translate_sql(query: str) -> str:
        # Param placeholders: sqlite3 uses '?', psycopg uses '%s'
        query = query.replace("?", "%s")

        # SQLite allows double-quotes for strings in some modes; PostgreSQL treats them as identifiers.
        query = query.replace('"PAID"', "'PAID'").replace('"UNPAID"', "'UNPAID'").replace('"Admin"', "'Admin'")

        # SQLite date modifier 'localtime' has no direct Postgres equivalent; we use session TZ instead.
        query = re.sub(r"DATE\(\s*([^,\)]+?)\s*,\s*'localtime'\s*\)", r"DATE(\1)", query, flags=re.IGNORECASE)

        # SQLite often uses 1/0 for booleans; normalize known app predicates for PostgreSQL.
        query = re.sub(r"\bis_active\s*=\s*1\b", "is_active = TRUE", query, flags=re.IGNORECASE)
        query = re.sub(r"\bis_active\s*=\s*0\b", "is_active = FALSE", query, flags=re.IGNORECASE)

        return query

    def close(self):
        if self.pool is not None:
            try:
                self.pool.close()
            except Exception:
                pass
    
    def init_database(self):
        ddl_statements = [
            """
            CREATE TABLE IF NOT EXISTS users (
                id BIGSERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('Admin', 'Accountant', 'Gate Operator', 'Driver')),
                full_name TEXT NOT NULL,
                phone TEXT,
                email TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMPTZ
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS clients (
                id BIGSERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                address TEXT,
                company TEXT,
                total_purchases DECIMAL(10,2) DEFAULT 0,
                total_paid DECIMAL(10,2) DEFAULT 0,
                balance DECIMAL(10,2) DEFAULT 0,
                initial_previous_balance DECIMAL(10,2) DEFAULT 0,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS gas_products (
                id BIGSERIAL PRIMARY KEY,
                gas_type TEXT NOT NULL,
                sub_type TEXT,
                capacity TEXT NOT NULL,
                unit_price DECIMAL(10,2) DEFAULT 0,
                description TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS sales (
                id BIGSERIAL PRIMARY KEY,
                client_id BIGINT NOT NULL REFERENCES clients(id),
                gas_product_id BIGINT NOT NULL REFERENCES gas_products(id),
                quantity INTEGER NOT NULL,
                unit_price DECIMAL(10,2) NOT NULL,
                subtotal DECIMAL(10,2) NOT NULL,
                tax_amount DECIMAL(10,2) NOT NULL,
                total_amount DECIMAL(10,2) NOT NULL,
                amount_paid DECIMAL(10,2) DEFAULT 0,
                balance DECIMAL(10,2) DEFAULT 0,
                created_by BIGINT NOT NULL REFERENCES users(id),
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS sale_items (
                id BIGSERIAL PRIMARY KEY,
                sale_id BIGINT NOT NULL REFERENCES sales(id),
                gas_product_id BIGINT NOT NULL REFERENCES gas_products(id),
                quantity INTEGER NOT NULL,
                unit_price DECIMAL(10,2) NOT NULL,
                subtotal DECIMAL(10,2) NOT NULL,
                tax_amount DECIMAL(10,2) NOT NULL,
                total_amount DECIMAL(10,2) NOT NULL,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS receipts (
                id BIGSERIAL PRIMARY KEY,
                receipt_number TEXT UNIQUE NOT NULL,
                sale_id BIGINT NOT NULL REFERENCES sales(id),
                client_id BIGINT NOT NULL REFERENCES clients(id),
                total_amount DECIMAL(10,2) NOT NULL,
                amount_paid DECIMAL(10,2) DEFAULT 0,
                balance DECIMAL(10,2) DEFAULT 0,
                created_by BIGINT NOT NULL REFERENCES users(id),
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS client_initial_outstanding (
                id BIGSERIAL PRIMARY KEY,
                client_id BIGINT NOT NULL REFERENCES clients(id),
                gas_type TEXT NOT NULL,
                sub_type TEXT,
                capacity TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS weekly_invoices (
                id BIGSERIAL PRIMARY KEY,
                invoice_number TEXT UNIQUE NOT NULL,
                client_id BIGINT NOT NULL REFERENCES clients(id),
                week_start DATE NOT NULL,
                week_end DATE NOT NULL,
                total_cylinders INTEGER DEFAULT 0,
                subtotal DECIMAL(10,2) DEFAULT 0,
                discount DECIMAL(10,2) DEFAULT 0,
                tax_amount DECIMAL(10,2) DEFAULT 0,
                total_payable DECIMAL(10,2) DEFAULT 0,
                previous_balance DECIMAL(10,2) DEFAULT 0,
                final_payable DECIMAL(10,2) DEFAULT 0,
                amount_paid DECIMAL(10,2) DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'UNPAID' CHECK(status IN ('PAID','UNPAID')),
                receipt_number TEXT,
                created_by BIGINT REFERENCES users(id),
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                paid_at TIMESTAMPTZ
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS weekly_payments (
                id BIGSERIAL PRIMARY KEY,
                weekly_invoice_id BIGINT NOT NULL REFERENCES weekly_invoices(id),
                client_id BIGINT NOT NULL REFERENCES clients(id),
                amount DECIMAL(10,2) NOT NULL,
                payment_date DATE NOT NULL,
                payment_method TEXT,
                created_by BIGINT REFERENCES users(id),
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS employees (
                id BIGSERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                salary DECIMAL(10,2) NOT NULL,
                contact TEXT,
                joining_date DATE NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS activity_logs (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES users(id),
                activity_type TEXT NOT NULL,
                description TEXT,
                timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS backup_logs (
                id BIGSERIAL PRIMARY KEY,
                backup_path TEXT NOT NULL,
                backup_size BIGINT,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS cylinder_returns (
                id BIGSERIAL PRIMARY KEY,
                client_id BIGINT NOT NULL REFERENCES clients(id),
                gas_type TEXT NOT NULL,
                sub_type TEXT,
                capacity TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS cylinder_inventory (
                id BIGSERIAL PRIMARY KEY,
                gas_product_id BIGINT NOT NULL UNIQUE REFERENCES gas_products(id) ON DELETE CASCADE,
                opening_count INTEGER NOT NULL DEFAULT 0,
                sold_count INTEGER NOT NULL DEFAULT 0,
                returned_count INTEGER NOT NULL DEFAULT 0,
                available_count INTEGER NOT NULL DEFAULT 0,
                updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS cylinder_stock_movements (
                id BIGSERIAL PRIMARY KEY,
                gas_product_id BIGINT NOT NULL REFERENCES gas_products(id) ON DELETE CASCADE,
                movement_type TEXT NOT NULL CHECK(movement_type IN ('OPENING', 'SALE_OUT', 'RETURN_IN')),
                quantity INTEGER NOT NULL,
                reference_type TEXT,
                reference_id BIGINT,
                client_id BIGINT REFERENCES clients(id),
                created_by BIGINT REFERENCES users(id),
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_clients_phone ON clients (phone)",
            "CREATE INDEX IF NOT EXISTS idx_sales_client_id ON sales (client_id)",
            "CREATE INDEX IF NOT EXISTS idx_sales_created_at ON sales (created_at)",
            "CREATE INDEX IF NOT EXISTS idx_receipts_receipt_number ON receipts (receipt_number)",
            "CREATE INDEX IF NOT EXISTS idx_receipts_created_at ON receipts (created_at)",
            "CREATE INDEX IF NOT EXISTS idx_weekly_invoices_client_week ON weekly_invoices (client_id, week_start, week_end)",
            "CREATE INDEX IF NOT EXISTS idx_weekly_invoices_status ON weekly_invoices (status)",
            "CREATE INDEX IF NOT EXISTS idx_weekly_payments_invoice ON weekly_payments (weekly_invoice_id)",
            "CREATE INDEX IF NOT EXISTS idx_weekly_payments_payment_date ON weekly_payments (payment_date)",
            "CREATE INDEX IF NOT EXISTS idx_activity_logs_timestamp ON activity_logs (timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_clients_name ON clients (name)",
            "CREATE INDEX IF NOT EXISTS idx_clients_company ON clients (company)",
            "CREATE INDEX IF NOT EXISTS idx_client_initial_outstanding_client ON client_initial_outstanding (client_id)",
            "CREATE INDEX IF NOT EXISTS idx_sales_client_created_at ON sales (client_id, created_at)",
            "CREATE INDEX IF NOT EXISTS idx_sales_gas_product_id ON sales (gas_product_id)",
            "CREATE INDEX IF NOT EXISTS idx_sales_created_by ON sales (created_by)",
            "CREATE INDEX IF NOT EXISTS idx_sale_items_sale_id ON sale_items (sale_id)",
            "CREATE INDEX IF NOT EXISTS idx_sale_items_gas_product_id ON sale_items (gas_product_id)",
            "CREATE INDEX IF NOT EXISTS idx_receipts_sale_id ON receipts (sale_id)",
            "CREATE INDEX IF NOT EXISTS idx_receipts_client_id ON receipts (client_id)",
            "CREATE INDEX IF NOT EXISTS idx_cylinder_returns_client_created ON cylinder_returns (client_id, created_at)",
            "CREATE INDEX IF NOT EXISTS idx_cylinder_returns_client_product ON cylinder_returns (client_id, gas_type, sub_type, capacity)",
            "CREATE INDEX IF NOT EXISTS idx_cylinder_inventory_product ON cylinder_inventory (gas_product_id)",
            "CREATE INDEX IF NOT EXISTS idx_stock_movements_product_type_time ON cylinder_stock_movements (gas_product_id, movement_type, created_at)",
            "CREATE INDEX IF NOT EXISTS idx_stock_movements_client_time ON cylinder_stock_movements (client_id, created_at)",
            "CREATE INDEX IF NOT EXISTS idx_weekly_invoices_created_at ON weekly_invoices (created_at)",
            "CREATE INDEX IF NOT EXISTS idx_weekly_invoices_receipt_number ON weekly_invoices (receipt_number)",
            "CREATE SEQUENCE IF NOT EXISTS receipt_number_seq START WITH 1 INCREMENT BY 1",
            "CREATE SEQUENCE IF NOT EXISTS weekly_invoice_number_seq START WITH 1 INCREMENT BY 1",
            "CREATE SEQUENCE IF NOT EXISTS weekly_receipt_number_seq START WITH 1 INCREMENT BY 1",
        ]

        with self._connection() as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    for ddl in ddl_statements:
                        cur.execute(ddl)
                    cur.execute("ALTER TABLE client_initial_outstanding ADD COLUMN IF NOT EXISTS sub_type TEXT")
                    cur.execute("DROP TABLE IF EXISTS gate_passes")
                    cur.execute("DROP TABLE IF EXISTS vehicle_expenses")
                    cur.execute('''
                        INSERT INTO cylinder_inventory (gas_product_id)
                        SELECT id FROM gas_products
                        ON CONFLICT (gas_product_id) DO NOTHING
                    ''')
                    cur.execute('''
                        SELECT COALESCE(MAX((regexp_match(receipt_number, '^(?:RCP)-\\d{4}-(\\d+)$'))[1]::BIGINT), 0) AS max_n
                        FROM receipts
                    ''')
                    max_receipt = int((cur.fetchone() or [0])[0] or 0)
                    cur.execute("SELECT setval('receipt_number_seq', %s, true)", (max_receipt if max_receipt > 0 else 1,))

                    cur.execute('''
                        SELECT COALESCE(MAX((regexp_match(invoice_number, '^(?:WEEK)-\\d{4}-(\\d+)$'))[1]::BIGINT), 0) AS max_n
                        FROM weekly_invoices
                    ''')
                    max_week_invoice = int((cur.fetchone() or [0])[0] or 0)
                    cur.execute("SELECT setval('weekly_invoice_number_seq', %s, true)", (max_week_invoice if max_week_invoice > 0 else 1,))

                    cur.execute('''
                        SELECT COALESCE(MAX((regexp_match(receipt_number, '^(?:WRCP)-\\d{4}-(\\d+)$'))[1]::BIGINT), 0) AS max_n
                        FROM weekly_invoices
                        WHERE receipt_number IS NOT NULL
                    ''')
                    max_week_receipt = int((cur.fetchone() or [0])[0] or 0)
                    cur.execute("SELECT setval('weekly_receipt_number_seq', %s, true)", (max_week_receipt if max_week_receipt > 0 else 1,))

        rows = self.execute_query("SELECT COUNT(*) AS n FROM users WHERE role = 'Admin'")
        if not rows or int(rows[0]["n"]) == 0:
            import hashlib

            password_hash = hashlib.sha256("admin123".encode()).hexdigest()
            self.execute_update(
                """
                INSERT INTO users (username, password_hash, role, full_name, phone, email)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                ("admin", password_hash, "Admin", "System Administrator", "", ""),
            )
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict]:
        sql = self._translate_sql(query)
        retries = self.query_retries
        for attempt in range(retries + 1):
            try:
                with self._connection() as conn:
                    with conn.cursor(row_factory=dict_row) as cur:
                        cur.execute(sql, params)
                        rows = list(cur.fetchall())
                        normalized: List[Dict] = []
                        for row in rows:
                            item = dict(row)
                            for key, value in list(item.items()):
                                if isinstance(value, datetime):
                                    item[key] = value.strftime("%Y-%m-%d %H:%M:%S")
                                elif isinstance(value, date):
                                    item[key] = value.isoformat()
                                elif isinstance(value, time):
                                    item[key] = value.strftime("%H:%M:%S")
                            normalized.append(item)
                        return normalized
            except Exception as exc:
                if attempt >= retries or not self._is_retryable_query_error(exc):
                    raise
                sleep_ms = self.retry_backoff_ms * (2 ** attempt) + random.randint(0, 50)
                pytime.sleep(sleep_ms / 1000.0)
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        sql = self._translate_sql(query).strip()
        is_insert = sql[:6].upper() == "INSERT" and "RETURNING" not in sql.upper()
        if is_insert:
            sql = f"{sql} RETURNING id"

        retries = self.query_retries
        for attempt in range(retries + 1):
            try:
                with self._connection() as conn:
                    with conn.transaction():
                        with conn.cursor(row_factory=dict_row) as cur:
                            cur.execute(sql, params)
                            if is_insert:
                                row = cur.fetchone()
                                return int(row["id"]) if row and "id" in row else 0
                            return int(cur.rowcount or 0)
            except Exception as exc:
                if attempt >= retries or not self._is_retryable_write_error(exc):
                    raise
                sleep_ms = self.retry_backoff_ms * (2 ** attempt) + random.randint(0, 50)
                pytime.sleep(sleep_ms / 1000.0)

    @contextmanager
    def transaction(self):
        with self._connection() as conn:
            with conn.transaction():
                yield conn
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        import hashlib
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        query = '''
            SELECT id, username, role, full_name, phone, email, is_active
            FROM users 
            WHERE username = ? AND password_hash = ? AND is_active = 1
        '''
        users = self.execute_query(query, (username, password_hash))
        return users[0] if users else None
    
    def update_last_login(self, user_id: int):
        query = 'UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?'
        self.execute_update(query, (user_id,))
    
    def log_activity(self, activity_type: str, description: str, user_id: Optional[int] = None):
        query = 'INSERT INTO activity_logs (user_id, activity_type, description) VALUES (?, ?, ?)'
        self.execute_update(query, (user_id, activity_type, description))
    
    def get_clients(self, search_term: str = "") -> List[Dict]:
        if search_term:
            query = '''
                SELECT * FROM clients 
                WHERE LOWER(COALESCE(name, '')) LIKE LOWER(?)
                   OR LOWER(COALESCE(phone, '')) LIKE LOWER(?)
                   OR LOWER(COALESCE(company, '')) LIKE LOWER(?)
                ORDER BY name
            '''
            search_pattern = f"%{search_term}%"
            return self.execute_query(query, (search_pattern, search_pattern, search_pattern))
        else:
            query = 'SELECT * FROM clients ORDER BY name'
            return self.execute_query(query)
    
    def get_client_by_id(self, client_id: int) -> Optional[Dict]:
        query = 'SELECT * FROM clients WHERE id = ?'
        clients = self.execute_query(query, (client_id,))
        return clients[0] if clients else None
    
    def add_client(self, name: str, phone: str, address: str = "", company: str = "", initial_previous_balance: float = 0.0) -> int:
        query = '''
            INSERT INTO clients (name, phone, address, company, initial_previous_balance, total_purchases, total_paid, balance)
            VALUES (?, ?, ?, ?, COALESCE(?,0), 0, 0, COALESCE(?,0))
        '''
        val = float(initial_previous_balance or 0.0)
        return self.execute_update(query, (name, phone, address, company, val, val))
    
    def update_client(self, client_id: int, name: str, phone: str, address: str = "", company: str = "", initial_previous_balance: Optional[float] = None) -> bool:
        rows = self.execute_query('SELECT id FROM clients WHERE id = ?', (client_id,))
        if not rows:
            return False
        query = '''
            UPDATE clients 
            SET name = ?, phone = ?, address = ?, company = ?, 
                initial_previous_balance = COALESCE(?, initial_previous_balance),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        '''
        self.execute_update(query, (name, phone, address, company, initial_previous_balance, client_id))
        self.update_client_balance(client_id)
        return True
    
    def update_client_balance(self, client_id: int):
        query = '''
            UPDATE clients 
            SET total_purchases = COALESCE((SELECT SUM(total_amount) FROM sales WHERE client_id = ?), 0),
                total_paid = COALESCE((SELECT SUM(amount_paid) FROM sales WHERE client_id = ?), 0),
                balance = COALESCE((SELECT SUM(balance) FROM sales WHERE client_id = ?), 0) + COALESCE(initial_previous_balance, 0),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        '''
        self.execute_update(query, (client_id, client_id, client_id, client_id))
    
    def get_gas_products(self) -> List[Dict]:
        query = 'SELECT * FROM gas_products WHERE is_active = 1 ORDER BY gas_type, sub_type, capacity'
        return self.execute_query(query)
    
    def get_gas_product_by_id(self, product_id: int) -> Optional[Dict]:
        query = 'SELECT * FROM gas_products WHERE id = ? AND is_active = 1'
        products = self.execute_query(query, (product_id,))
        return products[0] if products else None
    
    def add_gas_product(self, gas_type: str, sub_type: str, capacity: str, unit_price: float, description: str = "") -> int:
        query = '''
            INSERT INTO gas_products (gas_type, sub_type, capacity, unit_price, description)
            VALUES (?, ?, ?, ?, ?)
        '''
        product_id = self.execute_update(query, (gas_type, sub_type, capacity, unit_price, description))
        try:
            self.execute_update('''
                INSERT INTO cylinder_inventory (gas_product_id, opening_count, sold_count, returned_count, available_count)
                VALUES (?, 0, 0, 0, 0)
            ''', (product_id,))
        except Exception:
            pass
        return product_id
    
    def create_sale(self, client_id: int, gas_product_id: int, quantity: int, unit_price: float,
                   subtotal: float, tax_amount: float, total_amount: float, amount_paid: float,
                   balance: float, created_by: int) -> int:
        query = '''
            INSERT INTO sales (client_id, gas_product_id, quantity, unit_price, subtotal, 
                             tax_amount, total_amount, amount_paid, balance, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        sale_id = self.execute_update(query, (client_id, gas_product_id, quantity, unit_price,
                                            subtotal, tax_amount, total_amount, amount_paid, balance, created_by))
        self.update_client_balance(client_id)
        return sale_id

    def get_product_available_count(self, gas_product_id: int) -> int:
        rows = self.execute_query('''
            SELECT COALESCE(available_count, 0) AS available
            FROM cylinder_inventory
            WHERE gas_product_id = ?
            LIMIT 1
        ''', (gas_product_id,))
        if rows:
            return int(rows[0].get('available') or 0)
        self.execute_update('''
            INSERT INTO cylinder_inventory (gas_product_id, opening_count, sold_count, returned_count, available_count)
            VALUES (?, 0, 0, 0, 0)
        ''', (gas_product_id,))
        return 0

    def _decrease_inventory_for_sale(self, gas_product_id: int, quantity: int, sale_id: Optional[int] = None,
                                     client_id: Optional[int] = None, created_by: Optional[int] = None):
        qty = int(quantity or 0)
        if qty <= 0:
            return
        self.execute_update('''
            INSERT INTO cylinder_inventory (gas_product_id, opening_count, sold_count, returned_count, available_count)
            VALUES (?, 0, 0, 0, 0)
            ON CONFLICT (gas_product_id) DO NOTHING
        ''', (gas_product_id,))
        self.execute_update('''
            UPDATE cylinder_inventory
            SET sold_count = sold_count + ?,
                available_count = available_count - ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE gas_product_id = ?
        ''', (qty, qty, gas_product_id))
        self.execute_update('''
            INSERT INTO cylinder_stock_movements
                (gas_product_id, movement_type, quantity, reference_type, reference_id, client_id, created_by)
            VALUES (?, 'SALE_OUT', ?, 'SALE', ?, ?, ?)
        ''', (gas_product_id, qty, sale_id, client_id, created_by))

    def _increase_inventory_for_return(self, gas_product_id: int, quantity: int, return_id: Optional[int] = None,
                                       client_id: Optional[int] = None, created_by: Optional[int] = None):
        qty = int(quantity or 0)
        if qty <= 0:
            return
        self.execute_update('''
            INSERT INTO cylinder_inventory (gas_product_id, opening_count, sold_count, returned_count, available_count)
            VALUES (?, 0, 0, 0, 0)
            ON CONFLICT (gas_product_id) DO NOTHING
        ''', (gas_product_id,))
        self.execute_update('''
            UPDATE cylinder_inventory
            SET returned_count = returned_count + ?,
                available_count = available_count + ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE gas_product_id = ?
        ''', (qty, qty, gas_product_id))
        self.execute_update('''
            INSERT INTO cylinder_stock_movements
                (gas_product_id, movement_type, quantity, reference_type, reference_id, client_id, created_by)
            VALUES (?, 'RETURN_IN', ?, 'CYLINDER_RETURN', ?, ?, ?)
        ''', (gas_product_id, qty, return_id, client_id, created_by))

    def set_cylinder_opening_count(self, gas_product_id: int, opening_count: int, created_by: Optional[int] = None) -> bool:
        opening = max(0, int(opening_count or 0))
        self.execute_update('''
            INSERT INTO cylinder_inventory (gas_product_id, opening_count, sold_count, returned_count, available_count)
            VALUES (?, ?, 0, 0, ?)
            ON CONFLICT (gas_product_id) DO UPDATE
            SET opening_count = EXCLUDED.opening_count,
                sold_count = 0,
                returned_count = 0,
                available_count = EXCLUDED.available_count,
                updated_at = CURRENT_TIMESTAMP
        ''', (gas_product_id, opening, opening))
        self.execute_update('''
            INSERT INTO cylinder_stock_movements
                (gas_product_id, movement_type, quantity, reference_type, reference_id, client_id, created_by)
            VALUES (?, 'OPENING', ?, 'OPENING_SET', NULL, NULL, ?)
        ''', (gas_product_id, opening, created_by))
        return True

    def get_cylinder_availability_rows(self, search_term: str = "") -> List[Dict]:
        params: tuple = ()
        where = ""
        if search_term:
            like = f"%{search_term.strip().lower()}%"
            where = '''
                WHERE LOWER(COALESCE(gp.gas_type, '')) LIKE ?
                   OR LOWER(COALESCE(gp.sub_type, '')) LIKE ?
                   OR LOWER(COALESCE(gp.capacity, '')) LIKE ?
            '''
            params = (like, like, like)
        return self.execute_query(f'''
            SELECT gp.id AS gas_product_id,
                   gp.gas_type,
                   gp.sub_type,
                   gp.capacity,
                   gp.is_active,
                   COALESCE(ci.opening_count, 0) AS opening_count,
                   COALESCE(ci.returned_count, 0) AS returned_count,
                   COALESCE(ci.sold_count, 0) AS sold_count,
                   COALESCE(ci.available_count, 0) AS available_count,
                   COALESCE(ci.updated_at, gp.created_at) AS updated_at
            FROM gas_products gp
            LEFT JOIN cylinder_inventory ci ON ci.gas_product_id = gp.id
            {where}
            ORDER BY gp.gas_type, gp.sub_type, gp.capacity
        ''', params)

    def get_cylinder_availability_totals(self) -> Dict[str, int]:
        rows = self.execute_query('''
            SELECT COALESCE(SUM(opening_count),0) AS opening_total,
                   COALESCE(SUM(returned_count),0) AS returned_total,
                   COALESCE(SUM(sold_count),0) AS sold_total,
                   COALESCE(SUM(available_count),0) AS available_total
            FROM cylinder_inventory
        ''')
        data = rows[0] if rows else {}
        return {
            'opening_total': int(data.get('opening_total') or 0),
            'returned_total': int(data.get('returned_total') or 0),
            'sold_total': int(data.get('sold_total') or 0),
            'available_total': int(data.get('available_total') or 0),
        }

    def add_sale_item(self, sale_id: int, gas_product_id: int, quantity: int, unit_price: float,
                      subtotal: float, tax_amount: float, total_amount: float) -> int:
        query = '''
            INSERT INTO sale_items (sale_id, gas_product_id, quantity, unit_price, subtotal, tax_amount, total_amount)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        '''
        item_id = self.execute_update(query, (sale_id, gas_product_id, quantity, unit_price, subtotal, tax_amount, total_amount))
        sale_rows = self.execute_query('SELECT client_id, created_by FROM sales WHERE id = ?', (sale_id,))
        client_id = sale_rows[0]['client_id'] if sale_rows else None
        created_by = sale_rows[0].get('created_by') if sale_rows else None
        self._decrease_inventory_for_sale(gas_product_id, int(quantity), sale_id=sale_id, client_id=client_id, created_by=created_by)
        return item_id

    def update_sale_payment(self, sale_id: int, amount_paid: float) -> bool:
        query = 'UPDATE sales SET amount_paid = ?, balance = total_amount - ? WHERE id = ?'
        updated = self.execute_update(query, (amount_paid, amount_paid, sale_id))
        client_rows = self.execute_query('SELECT client_id FROM sales WHERE id = ?', (sale_id,))
        if client_rows:
            self.update_client_balance(client_rows[0]['client_id'])
        return updated > 0
    
    def create_receipt(self, receipt_number: str, sale_id: int, client_id: int, total_amount: float,
                      amount_paid: float, balance: float, created_by: int) -> int:
        query = '''
            INSERT INTO receipts (receipt_number, sale_id, client_id, total_amount, amount_paid, balance, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        '''
        return self.execute_update(query, (receipt_number, sale_id, client_id, total_amount, amount_paid, balance, created_by))
    
    def get_next_receipt_number(self) -> str:
        year = datetime.now().year
        for _ in range(50):
            result = self.execute_query("SELECT nextval('receipt_number_seq') AS n")
            count = int(result[0]['n']) if result else 1
            candidate = f"RCP-{year}-{str(count).zfill(6)}"
            exists = self.execute_query("SELECT 1 AS x FROM receipts WHERE receipt_number = ? LIMIT 1", (candidate,))
            if not exists:
                return candidate
        fallback = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"RCP-{year}-{fallback[-6:]}"

    def get_next_weekly_invoice_number(self) -> str:
        year = datetime.now().year
        for _ in range(50):
            rows = self.execute_query("SELECT nextval('weekly_invoice_number_seq') AS n")
            n = int(rows[0]['n']) if rows else 1
            candidate = f"WEEK-{year}-{str(n).zfill(6)}"
            exists = self.execute_query("SELECT 1 AS x FROM weekly_invoices WHERE invoice_number = ? LIMIT 1", (candidate,))
            if not exists:
                return candidate
        fallback = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"WEEK-{year}-{fallback[-6:]}"

    def get_next_weekly_receipt_number(self) -> str:
        year = datetime.now().year
        for _ in range(50):
            rows = self.execute_query("SELECT nextval('weekly_receipt_number_seq') AS n")
            n = int(rows[0]['n']) if rows else 1
            candidate = f"WRCP-{year}-{str(n).zfill(6)}"
            exists = self.execute_query("SELECT 1 AS x FROM weekly_invoices WHERE receipt_number = ? LIMIT 1", (candidate,))
            if not exists:
                return candidate
        fallback = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"WRCP-{year}-{fallback[-6:]}"

    def get_sale_items(self, sale_id: int) -> List[Dict]:
        items = self.execute_query('''
            SELECT si.created_at, si.quantity, si.unit_price, si.total_amount, si.subtotal, si.tax_amount,
                   gp.gas_type, gp.sub_type, gp.capacity
            FROM sale_items si
            JOIN gas_products gp ON si.gas_product_id = gp.id
            WHERE si.sale_id = ?
            ORDER BY si.id
        ''', (sale_id,))
        if items:
            return items
        # Fallback to single-line sale if no sale_items exist
        return self.execute_query('''
            SELECT s.created_at, s.quantity, s.unit_price, s.total_amount, s.subtotal, s.tax_amount,
                   gp.gas_type, gp.sub_type, gp.capacity
            FROM sales s
            JOIN gas_products gp ON s.gas_product_id = gp.id
            WHERE s.id = ?
        ''', (sale_id,))

    def get_sale_item_summaries(self, sale_id: int) -> Dict:
        row = self.execute_query('''
            SELECT 
                (
                    SELECT string_agg(
                        COALESCE(gp.gas_type,'') ||
                        CASE WHEN gp.sub_type IS NOT NULL AND gp.sub_type != '' THEN ' ' || gp.sub_type ELSE '' END ||
                        ' ' || COALESCE(gp.capacity,'')
                        , ', ' ORDER BY si2.id
                    )
                    FROM sale_items si2
                    JOIN gas_products gp ON si2.gas_product_id = gp.id
                    WHERE si2.sale_id = s.id
                ) AS product_summary,
                (
                    SELECT string_agg(si2.quantity::text, ', ' ORDER BY si2.id)
                    FROM sale_items si2
                    WHERE si2.sale_id = s.id
                ) AS quantities_summary
            FROM sales s
            WHERE s.id = ?
        ''', (sale_id,))
        return row[0] if row else {'product_summary': '', 'quantities_summary': ''}

    def get_receipts_with_summaries(self, limit: int = 100, search: Optional[str] = None) -> List[Dict]:
        params: tuple = ()
        where = ''
        if search:
            where = 'WHERE LOWER(r.receipt_number) LIKE ? OR LOWER(c.name) LIKE ?'
            like = f"%{search.lower()}%"
            params = (like, like)
        query = f'''
            SELECT r.*, c.name as client_name, c.phone as client_phone, c.company as client_company,
                   s.quantity, s.unit_price, s.subtotal, s.tax_amount, s.total_amount,
                   (
                       SELECT string_agg(
                           COALESCE(gp.gas_type,'') ||
                           CASE WHEN gp.sub_type IS NOT NULL AND gp.sub_type != '' THEN ' ' || gp.sub_type ELSE '' END ||
                           ' ' || COALESCE(gp.capacity,'')
                           , ', ' ORDER BY si2.id
                       )
                       FROM sale_items si2
                       JOIN gas_products gp ON si2.gas_product_id = gp.id
                       WHERE si2.sale_id = r.sale_id
                   ) AS product_summary,
                   (
                       SELECT string_agg(si2.quantity::text, ', ' ORDER BY si2.id)
                       FROM sale_items si2
                       WHERE si2.sale_id = r.sale_id
                   ) AS quantities_summary
            FROM receipts r
            JOIN clients c ON r.client_id = c.id
            JOIN sales s ON r.sale_id = s.id
            {where}
            ORDER BY r.created_at DESC
            LIMIT {int(limit)}
        '''
        return self.execute_query(query, params)

    def get_receipt_with_summaries_by_number(self, receipt_number: str) -> Optional[Dict]:
        query = '''
            SELECT r.*, c.name as client_name, c.phone as client_phone, c.company as client_company,
                   s.quantity, s.unit_price, s.subtotal, s.tax_amount, s.total_amount,
                   (
                       SELECT string_agg(
                           COALESCE(gp.gas_type,'') ||
                           CASE WHEN gp.sub_type IS NOT NULL AND gp.sub_type != '' THEN ' ' || gp.sub_type ELSE '' END ||
                           ' ' || COALESCE(gp.capacity,'')
                           , ', ' ORDER BY si2.id
                       )
                       FROM sale_items si2
                       JOIN gas_products gp ON si2.gas_product_id = gp.id
                       WHERE si2.sale_id = r.sale_id
                   ) AS product_summary,
                   (
                       SELECT string_agg(si2.quantity::text, ', ' ORDER BY si2.id)
                       FROM sale_items si2
                       WHERE si2.sale_id = r.sale_id
                   ) AS quantities_summary
            FROM receipts r
            JOIN clients c ON r.client_id = c.id
            JOIN sales s ON r.sale_id = s.id
            WHERE r.receipt_number = ?
            LIMIT 1
        '''
        rows = self.execute_query(query, (receipt_number,))
        return rows[0] if rows else None

    def compute_weekly_summary_for_client(self, client_id: int, week_start: str, week_end: str) -> Dict[str, Any]:
        params = (client_id, week_start, week_end)
        items_rows = self.execute_query('''
            SELECT 
                COALESCE(SUM(si.quantity),0) AS total_cylinders,
                COALESCE(SUM(si.quantity * si.unit_price),0) AS gross_total,
                COALESCE(SUM(si.subtotal),0) AS subtotal,
                COALESCE(SUM(si.tax_amount),0) AS tax_amount,
                COALESCE(SUM(si.total_amount),0) AS items_total
            FROM sale_items si
            JOIN sales s ON si.sale_id = s.id
            WHERE s.client_id = ?
              AND s.created_at >= (?::date)
              AND s.created_at < (?::date + INTERVAL '1 day')
        ''', params)
        sales_rows = self.execute_query('''
            SELECT 
                COALESCE(SUM(s.quantity),0) AS total_cylinders,
                COALESCE(SUM(s.quantity * s.unit_price),0) AS gross_total,
                COALESCE(SUM(s.subtotal),0) AS subtotal,
                COALESCE(SUM(s.tax_amount),0) AS tax_amount,
                COALESCE(SUM(s.total_amount),0) AS total_payable
            FROM sales s
            WHERE s.client_id = ?
              AND s.created_at >= (?::date)
              AND s.created_at < (?::date + INTERVAL '1 day')
        ''', params)
        items_has_data = bool(items_rows and (items_rows[0]['total_cylinders'] or items_rows[0]['subtotal'] or items_rows[0]['items_total']))
        total_cylinders = int(items_rows[0]['total_cylinders']) if items_has_data else (int(sales_rows[0]['total_cylinders']) if sales_rows else 0)
        gross_total = float(items_rows[0]['gross_total']) if items_has_data else (float(sales_rows[0]['gross_total']) if sales_rows else 0.0)
        subtotal = float(items_rows[0]['subtotal']) if items_has_data else (float(sales_rows[0]['subtotal']) if sales_rows else 0.0)
        tax_amount = float(items_rows[0]['tax_amount']) if items_has_data else (float(sales_rows[0]['tax_amount']) if sales_rows else 0.0)
        total_payable = float(sales_rows[0]['total_payable']) if sales_rows else (float(items_rows[0]['items_total']) if items_has_data else 0.0)
        discount = max(0.0, gross_total + tax_amount - total_payable)
        prev_rows = self.execute_query('''
            SELECT COALESCE(SUM(balance),0) AS prev_balance
            FROM sales
            WHERE client_id = ? AND created_at < (?::date)
        ''', (client_id, week_start))
        init_rows = self.execute_query('SELECT COALESCE(initial_previous_balance,0) AS init_prev FROM clients WHERE id = ?', (client_id,))
        init_prev = float(init_rows[0]['init_prev']) if init_rows else 0.0
        previous_balance = init_prev + (float(prev_rows[0]['prev_balance']) if prev_rows else 0.0)
        final_payable = previous_balance + total_payable
        pay_rows = self.execute_query('''
            SELECT COALESCE(SUM(amount),0) AS paid
            FROM weekly_payments
            WHERE client_id = ? AND weekly_invoice_id IN (
                SELECT id FROM weekly_invoices WHERE client_id = ? AND week_start = ? AND week_end = ?
            )
        ''', (client_id, client_id, week_start, week_end))
        amount_paid = float(pay_rows[0]['paid']) if pay_rows else 0.0
        eps = 0.01
        status = 'PAID' if (final_payable <= eps) or (amount_paid + eps >= final_payable) else 'UNPAID'
        return {
            'total_cylinders': total_cylinders,
            'subtotal': round(subtotal, 2),
            'discount': round(discount, 2),
            'tax_amount': round(tax_amount, 2),
            'total_payable': round(total_payable, 2),
            'previous_balance': round(previous_balance, 2),
            'final_payable': round(final_payable, 2),
            'amount_paid': round(amount_paid, 2),
            'status': status
        }

    def upsert_weekly_invoice(self, client_id: int, week_start: str, week_end: str, created_by: Optional[int] = None) -> int:
        summary = self.compute_weekly_summary_for_client(client_id, week_start, week_end)
        rows = self.execute_query('''
            SELECT id, previous_balance, amount_paid FROM weekly_invoices WHERE client_id = ? AND week_start = ? AND week_end = ?
        ''', (client_id, week_start, week_end))
        receipt_number = None
        if summary['final_payable'] > 0:
            existing = self.execute_query('''
                SELECT receipt_number FROM weekly_invoices WHERE client_id = ? AND week_start = ? AND week_end = ? AND receipt_number IS NOT NULL
            ''', (client_id, week_start, week_end))
            receipt_number = existing[0]['receipt_number'] if existing else self.get_next_weekly_receipt_number()
        if rows:
            prev_snapshot = float(rows[0]['previous_balance'])
            weekly_total = float(summary['total_payable'])
            final_payable_calc = round(prev_snapshot + weekly_total, 2)
            amount_paid_calc = float(summary['amount_paid'])
            eps = 0.01
            status_calc = 'PAID' if (final_payable_calc <= eps) or (amount_paid_calc + eps >= final_payable_calc) else 'UNPAID'
            self.execute_update('''
                UPDATE weekly_invoices
                SET total_cylinders = ?, subtotal = ?, discount = ?, tax_amount = ?, total_payable = ?, final_payable = ?, updated_at = CURRENT_TIMESTAMP, amount_paid = ?, status = ?, receipt_number = COALESCE(receipt_number, ?)
                WHERE id = ?
            ''', (
                summary['total_cylinders'], summary['subtotal'], summary['discount'], summary['tax_amount'], summary['total_payable'], final_payable_calc, amount_paid_calc, status_calc, receipt_number, rows[0]['id']
            ))
            return rows[0]['id']
        invoice_number = self.get_next_weekly_invoice_number()
        nid = self.execute_update('''
            INSERT INTO weekly_invoices (invoice_number, client_id, week_start, week_end, total_cylinders, subtotal, discount, tax_amount, total_payable, previous_balance, final_payable, amount_paid, status, receipt_number, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            invoice_number, client_id, week_start, week_end, summary['total_cylinders'], summary['subtotal'], summary['discount'], summary['tax_amount'], summary['total_payable'], summary['previous_balance'], summary['final_payable'], summary['amount_paid'], summary['status'], receipt_number, created_by
        ))
        try:
            self.log_activity('WeeklyInvoiceGenerated', f"Weekly invoice {invoice_number} for client {client_id} {week_start} to {week_end}", created_by)
        except Exception:
            pass
        return nid

    def get_weekly_invoices(self, week_start: str, week_end: str) -> List[Dict]:
        return self.execute_query('''
            SELECT wi.*, c.name AS client_name, c.phone AS client_phone, c.company AS client_company
            FROM weekly_invoices wi
            JOIN clients c ON wi.client_id = c.id
            WHERE wi.week_start = ? AND wi.week_end = ?
            ORDER BY c.name
        ''', (week_start, week_end))

    def record_weekly_payment(self, weekly_invoice_id: int, amount: float, payment_date: str, created_by: Optional[int] = None, payment_method: Optional[str] = None) -> int:
        inv_rows = self.execute_query('SELECT id, client_id, final_payable, amount_paid, status, week_start, week_end FROM weekly_invoices WHERE id = ?', (weekly_invoice_id,))
        if not inv_rows:
            raise ValueError('Weekly invoice not found')
        inv = inv_rows[0]
        if amount is None or float(amount) < 0:
            raise ValueError('Payment amount cannot be negative')
        remaining = float(inv['final_payable']) - float(inv['amount_paid'])
        if float(amount) > max(0.0, remaining):
            raise ValueError('Payment exceeds remaining balance')
        pid = self.execute_update('''
            INSERT INTO weekly_payments (weekly_invoice_id, client_id, amount, payment_date, payment_method, created_by)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (weekly_invoice_id, inv['client_id'], float(amount), payment_date, payment_method, created_by))
        new_paid = float(inv['amount_paid']) + float(amount)
        eps = 0.01
        remaining = max(0.0, float(inv['final_payable']) - new_paid)
        new_status = 'PAID' if remaining <= eps else 'UNPAID'
        self.execute_update('UPDATE weekly_invoices SET amount_paid = ?, status = ?, updated_at = CURRENT_TIMESTAMP, paid_at = CASE WHEN ? = "PAID" THEN CURRENT_TIMESTAMP ELSE paid_at END WHERE id = ?', (new_paid, new_status, new_status, weekly_invoice_id))
        self.apply_weekly_payment_to_sales(weekly_invoice_id, float(amount), created_by)
        try:
            self.log_activity('WeeklyPaymentRecorded', f"Weekly payment Rs.{float(amount):.2f} for invoice {weekly_invoice_id}", created_by)
        except Exception:
            pass
        return pid

    def apply_weekly_payment_to_sales(self, weekly_invoice_id: int, amount: float, created_by: Optional[int]):
        inv_rows = self.execute_query('SELECT client_id, week_start, week_end FROM weekly_invoices WHERE id = ?', (weekly_invoice_id,))
        if not inv_rows:
            return
        client_id = inv_rows[0]['client_id']
        ws = inv_rows[0]['week_start']
        we = inv_rows[0]['week_end']
        prev_rows = self.execute_query('SELECT COALESCE(initial_previous_balance,0) AS init_prev FROM clients WHERE id = ?', (client_id,))
        remaining_amount = float(amount)
        if prev_rows:
            init_prev = float(prev_rows[0]['init_prev'])
            if init_prev > 0 and remaining_amount > 0:
                apply_prev = min(remaining_amount, init_prev)
                new_prev = max(0.0, init_prev - apply_prev)
                self.execute_update('UPDATE clients SET initial_previous_balance = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', (new_prev, client_id))
                self.update_client_balance(client_id)
                remaining_amount -= apply_prev
        rows = self.execute_query('''
            SELECT id, total_amount, amount_paid
            FROM sales
            WHERE client_id = ? AND (total_amount - amount_paid) > 0
            ORDER BY created_at ASC
        ''', (client_id,))
        for s in rows:
            if remaining_amount <= 0:
                break
            sale_remaining = float(s['total_amount']) - float(s['amount_paid'])
            if sale_remaining <= 0:
                continue
            pay_now = min(remaining_amount, sale_remaining)
            new_paid = float(s['amount_paid']) + pay_now
            self.update_sale_payment(s['id'], new_paid)
            balance = float(s['total_amount']) - new_paid
            receipt_number = self.get_next_receipt_number()
            if created_by is None:
                created_by_val = 1
            else:
                created_by_val = created_by
            self.create_receipt(receipt_number, s['id'], client_id, float(s['total_amount']), new_paid, balance, created_by_val)
            remaining_amount -= pay_now
        self.update_client_balance(client_id)
        rows_bal = self.execute_query('SELECT COALESCE(balance,0) AS bal, COALESCE(initial_previous_balance,0) AS ipb FROM clients WHERE id = ?', (client_id,))
        if rows_bal:
            eps = 0.01
            bal = float(rows_bal[0]['bal'])
            ipb = float(rows_bal[0]['ipb'])
            if abs(bal) <= eps and ipb > 0:
                self.execute_update('UPDATE clients SET initial_previous_balance = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?', (client_id,))
                self.update_client_balance(client_id)

    def mark_weekly_invoice_paid(self, weekly_invoice_id: int) -> bool:
        inv_rows = self.execute_query('SELECT id, client_id, final_payable, amount_paid, status FROM weekly_invoices WHERE id = ?', (weekly_invoice_id,))
        if not inv_rows:
            return False
        inv = inv_rows[0]
        eps = 0.01
        remaining = float(inv['final_payable']) - float(inv['amount_paid'])
        if abs(remaining) > eps:
            raise ValueError('Remaining balance is not zero')
        updated = self.execute_update('UPDATE weekly_invoices SET status = "PAID", paid_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE id = ?', (weekly_invoice_id,))
        client_id = inv['client_id']
        self.execute_update('UPDATE clients SET initial_previous_balance = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?', (client_id,))
        self.execute_update('UPDATE sales SET amount_paid = total_amount, balance = 0 WHERE client_id = ? AND balance != 0', (client_id,))
        self.update_client_balance(client_id)
        try:
            self.log_activity('WeeklyInvoiceMarkedPaid', f"Weekly invoice {weekly_invoice_id} marked PAID", None)
        except Exception:
            pass
        return updated > 0

    def get_client_weekly_items(self, client_id: int, week_start: str, week_end: str) -> List[Dict]:
        return self.execute_query('''
            SELECT * FROM (
                SELECT DATE(s.created_at) AS date, 
                       COALESCE(gp.gas_type,'') AS gas_type,
                       COALESCE(gp.sub_type,'') AS sub_type,
                       COALESCE(gp.capacity,'') AS capacity,
                       si.quantity AS quantity,
                       si.unit_price AS unit_price,
                       si.subtotal AS subtotal,
                       si.tax_amount AS tax_amount,
                       si.total_amount AS total_amount
                FROM sale_items si
                JOIN sales s ON si.sale_id = s.id
                JOIN gas_products gp ON si.gas_product_id = gp.id
                                WHERE s.client_id = ?
                                    AND s.created_at >= (?::date)
                                    AND s.created_at < (?::date + INTERVAL '1 day')
                UNION ALL
                                SELECT DATE(s.created_at) AS date,
                       COALESCE(gp.gas_type,'') AS gas_type,
                       COALESCE(gp.sub_type,'') AS sub_type,
                       COALESCE(gp.capacity,'') AS capacity,
                       s.quantity AS quantity,
                       s.unit_price AS unit_price,
                       s.subtotal AS subtotal,
                       s.tax_amount AS tax_amount,
                       s.total_amount AS total_amount
                FROM sales s
                LEFT JOIN sale_items si_chk ON si_chk.sale_id = s.id
                JOIN gas_products gp ON s.gas_product_id = gp.id
                                WHERE si_chk.id IS NULL
                                    AND s.client_id = ?
                                    AND s.created_at >= (?::date)
                                    AND s.created_at < (?::date + INTERVAL '1 day')
            )
            ORDER BY date ASC
        ''', (client_id, week_start, week_end, client_id, week_start, week_end))

    def get_weekly_payment_history(self, weekly_invoice_id: int) -> List[Dict]:
        return self.execute_query('''
            SELECT payment_date, amount, COALESCE(payment_method,'') AS payment_method, created_at
            FROM weekly_payments
            WHERE weekly_invoice_id = ?
            ORDER BY payment_date ASC, id ASC
        ''', (weekly_invoice_id,))

    def get_recent_sales_with_summaries(self, limit: int = 20) -> List[Dict]:
        query = f'''
            SELECT s.*, c.name as client_name, c.phone as client_phone,
                   (
                       SELECT string_agg(
                           COALESCE(gp.gas_type,'') ||
                           CASE WHEN gp.sub_type IS NOT NULL AND gp.sub_type != '' THEN ' ' || gp.sub_type ELSE '' END ||
                           ' ' || COALESCE(gp.capacity,'')
                           , ', ' ORDER BY si2.id
                       )
                       FROM sale_items si2
                       JOIN gas_products gp ON si2.gas_product_id = gp.id
                       WHERE si2.sale_id = s.id
                   ) AS product_summary,
                   (
                       SELECT string_agg(si2.quantity::text, ', ' ORDER BY si2.id)
                       FROM sale_items si2
                       WHERE si2.sale_id = s.id
                   ) AS quantities_summary
            FROM sales s
            JOIN clients c ON s.client_id = c.id
            ORDER BY s.created_at DESC
            LIMIT {int(limit)}
        '''
        return self.execute_query(query)

    # Weekly billing removed

    # Weekly billing removed

    # Weekly billing removed

    # Weekly billing removed

    # Weekly billing removed

    # Weekly billing removed

    def get_client_purchases_with_summaries(self, client_id: int, limit: int = 10) -> List[Dict]:
        query = f'''
            SELECT s.*, 
                   (
                       SELECT string_agg(
                           COALESCE(gp.gas_type,'') ||
                           CASE WHEN gp.sub_type IS NOT NULL AND gp.sub_type != '' THEN ' ' || gp.sub_type ELSE '' END ||
                           ' ' || COALESCE(gp.capacity,'')
                           , ', ' ORDER BY si2.id
                       )
                       FROM sale_items si2
                       JOIN gas_products gp ON si2.gas_product_id = gp.id
                       WHERE si2.sale_id = s.id
                   ) AS product_summary,
                   (
                       SELECT string_agg(si2.quantity::text, ', ' ORDER BY si2.id)
                       FROM sale_items si2
                       WHERE si2.sale_id = s.id
                   ) AS quantities_summary
            FROM sales s
            WHERE s.client_id = ?
            ORDER BY s.created_at DESC
            LIMIT {int(limit)}
        '''
        return self.execute_query(query, (client_id,))

    def get_sales_for_date_with_summaries(self, day: str) -> List[Dict]:
        query = '''
            SELECT s.*, c.name as client_name, u.full_name as cashier_name,
                   (
                       SELECT string_agg(
                           COALESCE(gp.gas_type,'') ||
                           CASE WHEN gp.sub_type IS NOT NULL AND gp.sub_type != '' THEN ' ' || gp.sub_type ELSE '' END ||
                           ' ' || COALESCE(gp.capacity,'')
                           , ', ' ORDER BY si2.id
                       )
                       FROM sale_items si2
                       JOIN gas_products gp ON si2.gas_product_id = gp.id
                       WHERE si2.sale_id = s.id
                   ) AS product_summary,
                   (
                       SELECT string_agg(si2.quantity::text, ', ' ORDER BY si2.id)
                       FROM sale_items si2
                       WHERE si2.sale_id = s.id
                   ) AS quantities_summary
            FROM sales s
            JOIN clients c ON s.client_id = c.id
            JOIN users u ON s.created_by = u.id
            WHERE s.created_at >= (?::date)
              AND s.created_at < (?::date + INTERVAL '1 day')
            ORDER BY s.created_at DESC
        '''
        return self.execute_query(query, (day, day))

    def get_return_rows_for_client_product(self, client_id: int, gas_type: str, capacity: str) -> List[Dict]:
        return self.execute_query(
            'SELECT * FROM cylinder_returns WHERE client_id = ? AND gas_type = ? AND capacity = ? ORDER BY created_at DESC',
            (client_id, gas_type, capacity)
        )

    def update_total_return_for_client_product(self, client_id: int, gas_type: str, capacity: str, new_total: int) -> bool:
        # Kept for backward compatibility; we maintain per-entry rows so no aggregate row to update.
        # This method performs no-op and returns True if parameters are valid.
        return True

    def get_cylinder_summary_for_client(self, client_id: int):
        return self.get_client_cylinder_status(client_id)

    def get_client_deliveries_with_returns(self, client_id: int) -> List[Dict]:
        rows = self.get_client_cylinder_status(client_id)
        for r in rows:
            r['status'] = 'Done' if int(r['pending']) <= 0 else 'Pending'
        return rows

    def auto_mark_due_returns(self) -> int:
        raise NotImplementedError("Cylinder returns feature removed")

    def find_latest_gate_pass_for_product(self, client_id: int, gas_type: str, capacity: str) -> Optional[int]:
        raise NotImplementedError("Cylinder returns feature removed")
    
    def get_type_summary_for_client(self, client_id: int) -> List[Dict]:
        raise NotImplementedError("Cylinder returns feature removed")

    def get_pending_capacity_map_for_client(self, client_id: int) -> Dict[str, List[str]]:
        raise NotImplementedError("Cylinder returns feature removed")

    def get_empty_stock_by_category(self, day: Optional[str] = None) -> List[Dict]:
        raise NotImplementedError("Cylinder returns feature removed")
    
    def add_client_initial_outstanding(self, client_id: int, gas_type: str, capacity: str, quantity: int, sub_type: Optional[str] = None) -> int:
        query = '''
            INSERT INTO client_initial_outstanding (client_id, gas_type, sub_type, capacity, quantity)
            VALUES (?, ?, ?, ?, ?)
        '''
        return self.execute_update(query, (client_id, gas_type, sub_type if sub_type else None, capacity, int(quantity)))

    def replace_client_initial_outstanding(self, client_id: int, entries: List[Dict[str, Any]]) -> None:
        with self.transaction() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute("DELETE FROM client_initial_outstanding WHERE client_id = %s", (client_id,))
                for entry in entries:
                    qty = int(entry.get('quantity') or 0)
                    if qty <= 0:
                        continue
                    cur.execute(
                        """
                        INSERT INTO client_initial_outstanding (client_id, gas_type, sub_type, capacity, quantity)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (
                            client_id,
                            entry.get('gas_type'),
                            entry.get('sub_type') or None,
                            entry.get('capacity'),
                            qty,
                        ),
                    )

    def get_employees(self) -> List[Dict]:
        query = 'SELECT * FROM employees WHERE is_active = 1 ORDER BY name'
        return self.execute_query(query)
    
    def add_employee(self, name: str, role: str, salary: float, contact: str, joining_date: date) -> int:
        query = '''
            INSERT INTO employees (name, role, salary, contact, joining_date)
            VALUES (?, ?, ?, ?, ?)
        '''
        return self.execute_update(query, (name, role, salary, contact, joining_date))
    
    def get_sales_report(self, start_date: date, end_date: date) -> List[Dict]:
        query = '''
            SELECT s.*, c.name as client_name, c.phone as client_phone,
                   (
                       SELECT string_agg(
                           COALESCE(gp.gas_type,'') ||
                           CASE WHEN gp.sub_type IS NOT NULL AND gp.sub_type != '' THEN ' ' || gp.sub_type ELSE '' END ||
                           ' ' || COALESCE(gp.capacity,'')
                           , ', ' ORDER BY si2.id
                       )
                       FROM sale_items si2
                       JOIN gas_products gp ON si2.gas_product_id = gp.id
                       WHERE si2.sale_id = s.id
                   ) AS product_summary,
                   (
                       SELECT string_agg(si2.quantity::text, ', ' ORDER BY si2.id)
                       FROM sale_items si2
                       WHERE si2.sale_id = s.id
                   ) AS quantities_summary
            FROM sales s
            JOIN clients c ON s.client_id = c.id
                        WHERE s.created_at >= (?::date)
                            AND s.created_at < (?::date + INTERVAL '1 day')
            ORDER BY s.created_at DESC
        '''
        return self.execute_query(query, (start_date, end_date))
    
    def get_outstanding_balances(self) -> List[Dict]:
        query = '''
            SELECT id, name, phone, company, balance, total_purchases, total_paid
            FROM clients 
            WHERE balance > 0
            ORDER BY balance DESC
        '''
        return self.execute_query(query)
    
    def get_gate_activity_report(self, start_date: date, end_date: date) -> List[Dict]:
        return []
    # Add to class DatabaseManager:

    def get_all_company_products(self):
        """Return all gas products with type, sub_type, capacity."""
        return self.execute_query(
            '''
            SELECT gas_type, sub_type, capacity
            FROM gas_products
            WHERE is_active = 1
            ORDER BY gas_type, sub_type, capacity
            '''
        )

    def get_client_cylinder_status(self, client_id: int):
        """
        List all company products with delivered, returned, and pending counts for this client.
        Delivered = initial outstanding + sum of sales quantities for the product
        Returned = sum of cylinder_returns quantities
        Pending = Delivered - Returned
        Returns: list of dict with gas_type, sub_type, capacity, delivered, returned, pending.
        """
        def group_cap(gas_type: str, capacity: str) -> str:
            if gas_type == 'LPG' and capacity in ('12kg', '15kg'):
                return '12/15kg'
            return capacity

        product_rows = self.get_all_company_products()
        keys = {(p['gas_type'], group_cap(p['gas_type'], p['capacity'])) for p in product_rows}

        init_rows = self.execute_query(
            '''
            SELECT gas_type,
                   CASE WHEN gas_type = 'LPG' AND capacity IN ('12kg','15kg') THEN '12/15kg' ELSE capacity END AS cap_group,
                   COALESCE(SUM(quantity), 0) AS qty
            FROM client_initial_outstanding
            WHERE client_id = ?
            GROUP BY gas_type, cap_group
            ''',
            (client_id,)
        )
        init_map = {(r['gas_type'], r['cap_group']): int(r['qty']) for r in init_rows}

        delivered_items = self.execute_query(
            '''
            SELECT gp.gas_type,
                   CASE WHEN gp.gas_type = 'LPG' AND gp.capacity IN ('12kg','15kg') THEN '12/15kg' ELSE gp.capacity END AS cap_group,
                   COALESCE(SUM(si.quantity), 0) AS qty
            FROM sale_items si
            JOIN sales s ON si.sale_id = s.id
            JOIN gas_products gp ON si.gas_product_id = gp.id
            WHERE s.client_id = ?
            GROUP BY gp.gas_type, cap_group
            ''',
            (client_id,)
        )
        delivered_map = {(r['gas_type'], r['cap_group']): int(r['qty']) for r in delivered_items}

        delivered_single = self.execute_query(
            '''
            SELECT gp.gas_type,
                   CASE WHEN gp.gas_type = 'LPG' AND gp.capacity IN ('12kg','15kg') THEN '12/15kg' ELSE gp.capacity END AS cap_group,
                   COALESCE(SUM(s.quantity), 0) AS qty
            FROM sales s
            LEFT JOIN sale_items si ON si.sale_id = s.id
            JOIN gas_products gp ON s.gas_product_id = gp.id
            WHERE s.client_id = ? AND si.id IS NULL
            GROUP BY gp.gas_type, cap_group
            ''',
            (client_id,)
        )
        for r in delivered_single:
            k = (r['gas_type'], r['cap_group'])
            delivered_map[k] = delivered_map.get(k, 0) + int(r['qty'])

        return_rows = self.execute_query(
            '''
            SELECT gas_type,
                   CASE WHEN gas_type = 'LPG' AND capacity IN ('12kg','15kg') THEN '12/15kg' ELSE capacity END AS cap_group,
                   COALESCE(SUM(quantity), 0) AS qty
            FROM cylinder_returns
            WHERE client_id = ?
            GROUP BY gas_type, cap_group
            ''',
            (client_id,)
        )
        returned_map = {(r['gas_type'], r['cap_group']): int(r['qty']) for r in return_rows}

        keys.update(init_map.keys())
        keys.update(delivered_map.keys())
        keys.update(returned_map.keys())

        rows: List[Dict[str, Any]] = []
        for gas_type, cap_group in sorted(keys, key=lambda x: (x[0], x[1])):
            delivered = int(delivered_map.get((gas_type, cap_group), 0)) + int(init_map.get((gas_type, cap_group), 0))
            returned = int(returned_map.get((gas_type, cap_group), 0))
            pending = max(0, delivered - returned)
            rows.append({
                'gas_type': gas_type,
                'sub_type': '',
                'capacity': cap_group,
                'delivered': delivered,
                'returned': returned,
                'pending': pending,
            })
        return rows

    def add_cylinder_return(self, client_id: int, gas_type: str, sub_type: str, capacity: str, quantity: int):
        query = '''
            INSERT INTO cylinder_returns (client_id, gas_type, sub_type, capacity, quantity)
            VALUES (?, ?, ?, ?, ?)
        '''
        return_id = self.execute_update(query, (client_id, gas_type, sub_type, capacity, int(quantity)))
        try:
            product_rows = self.execute_query('''
                SELECT id
                FROM gas_products
                WHERE gas_type = ?
                  AND COALESCE(sub_type, '') = COALESCE(?, '')
                  AND capacity = ?
                LIMIT 1
            ''', (gas_type, sub_type, capacity))
            if not product_rows and sub_type:
                product_rows = self.execute_query('''
                    SELECT id
                    FROM gas_products
                    WHERE gas_type = ? AND capacity = ?
                    ORDER BY id
                    LIMIT 1
                ''', (gas_type, capacity))
            if product_rows:
                self._increase_inventory_for_return(int(product_rows[0]['id']), int(quantity), return_id=return_id, client_id=client_id)
        except Exception:
            pass
        return return_id

    def get_total_cylinder_stats(self) -> Dict[str, int]:
        init_total_rows = self.execute_query('SELECT COALESCE(SUM(quantity),0) AS total FROM client_initial_outstanding')
        init_total = int(init_total_rows[0]['total']) if init_total_rows else 0
        delivered_items_rows = self.execute_query('SELECT COALESCE(SUM(quantity),0) AS total FROM sale_items')
        delivered_items_total = int(delivered_items_rows[0]['total']) if delivered_items_rows else 0
        delivered_sales_rows = self.execute_query('''
            SELECT COALESCE(SUM(s.quantity),0) AS total
            FROM sales s
            WHERE NOT EXISTS (
                SELECT 1 FROM sale_items si WHERE si.sale_id = s.id
            )
        ''')
        delivered_sales_total = int(delivered_sales_rows[0]['total']) if delivered_sales_rows else 0
        returned_rows = self.execute_query('SELECT COALESCE(SUM(quantity),0) AS total FROM cylinder_returns')
        returned_total_basic = int(returned_rows[0]['total']) if returned_rows else 0
        delivered_total_basic = init_total + delivered_items_total + delivered_sales_total
        pending_total_basic = max(0, delivered_total_basic - returned_total_basic)
        if pending_total_basic > 0:
            return {
                'total_delivered': delivered_total_basic,
                'total_returned': returned_total_basic,
                'total_pending': pending_total_basic
            }
        acc_delivered = 0
        acc_returned = 0
        for c in self.get_clients():
            rows = self.get_client_cylinder_status(c['id'])
            acc_delivered += sum(int(r.get('delivered') or 0) for r in rows)
            acc_returned += sum(int(r.get('returned') or 0) for r in rows)
        pending_total = max(0, acc_delivered - acc_returned)
        return {
            'total_delivered': acc_delivered,
            'total_returned': acc_returned,
            'total_pending': pending_total
        }

    def get_pending_cylinder_summary_by_client(self) -> List[Dict]:
        clients = self.get_clients()
        result: List[Dict] = []
        for c in clients:
            rows = self.get_client_cylinder_status(c['id'])
            pending_sum = sum(int(r['pending']) for r in rows)
            result.append({
                'client_id': c['id'],
                'name': c['name'],
                'phone': c['phone'],
                'company': c.get('company'),
                'pending_cylinders': pending_sum
            })
        result.sort(key=lambda x: x['pending_cylinders'], reverse=True)
        return result

    def get_weekly_returns_breakdown(self, client_id: int, week_start: str, week_end: str) -> str:
        query = '''
            SELECT string_agg(summary, ', ') as result FROM (
                SELECT 
                    CASE 
                        WHEN gas_type = 'LPG' THEN 'L'
                        WHEN gas_type = 'Oxygen' THEN 'O2'
                        WHEN gas_type = 'Nitrogen' THEN 'N2'
                        WHEN gas_type = 'Argon' THEN 'Ar'
                        WHEN gas_type = 'Acetylene' THEN 'C2H2'
                        WHEN gas_type = 'Helium' THEN 'He'
                        WHEN gas_type = 'CO2' THEN 'CO2'
                        ELSE SUBSTR(gas_type, 1, 3)
                    END || 
                    CASE 
                        WHEN sub_type IS NOT NULL AND sub_type != '' THEN ' ' || SUBSTR(sub_type, 1, 3) 
                        ELSE '' 
                    END || 
                    CASE 
                        WHEN gas_type = 'LPG' AND cap_group = '12kg' THEN ' 12'
                        WHEN gas_type = 'LPG' AND cap_group = '15kg' THEN ' 15'
                        WHEN gas_type = 'LPG' AND cap_group = '12/15kg' THEN ' 12/15'
                        ELSE ' ' || REPLACE(COALESCE(cap_group,''), 'm3', '')
                    END || ' ' || SUM(qty)::text as summary
                FROM (
                    SELECT 
                        gas_type,
                        sub_type,
                        CASE WHEN gas_type='LPG' AND capacity IN ('12kg','15kg') THEN '12/15kg' ELSE capacity END AS cap_group,
                        quantity as qty
                    FROM cylinder_returns
                                        WHERE client_id = ?
                                            AND created_at >= (?::date)
                                            AND created_at < (?::date + INTERVAL '1 day')
                ) t
                GROUP BY gas_type, sub_type, cap_group
            )
        '''
        rows = self.execute_query(query, (client_id, week_start, week_end))
        return rows[0]['result'] if rows and rows[0]['result'] else "0"

    def get_weekly_sales_breakdown(self, client_id: int, week_start: str, week_end: str) -> str:
        query = '''
            SELECT string_agg(summary, ', ') as result FROM (
                SELECT 
                    CASE 
                        WHEN gp.gas_type = 'LPG' THEN 'L'
                        WHEN gp.gas_type = 'Oxygen' THEN 'O2'
                        WHEN gp.gas_type = 'Nitrogen' THEN 'N2'
                        WHEN gp.gas_type = 'Argon' THEN 'Ar'
                        WHEN gp.gas_type = 'Acetylene' THEN 'C2H2'
                        WHEN gp.gas_type = 'Helium' THEN 'He'
                        WHEN gp.gas_type = 'CO2' THEN 'CO2'
                        ELSE SUBSTR(gp.gas_type, 1, 3)
                    END || 
                    CASE 
                        WHEN gp.sub_type IS NOT NULL AND gp.sub_type != '' THEN ' ' || SUBSTR(gp.sub_type, 1, 3) 
                        ELSE '' 
                    END || 
                    CASE 
                        WHEN gp.gas_type = 'LPG' AND cap_group = '12kg' THEN ' 12'
                        WHEN gp.gas_type = 'LPG' AND cap_group = '15kg' THEN ' 15'
                        WHEN gp.gas_type = 'LPG' AND cap_group = '12/15kg' THEN ' 12/15'
                        ELSE ' ' || REPLACE(COALESCE(cap_group,''), 'm3', '')
                    END || ' ' || SUM(qty)::text as summary
                FROM (
                    SELECT 
                        si.gas_product_id,
                        si.quantity as qty,
                        CASE WHEN gp.gas_type='LPG' AND gp.capacity IN ('12kg','15kg') THEN '12/15kg' ELSE gp.capacity END AS cap_group
                    FROM sale_items si
                    JOIN sales s ON si.sale_id = s.id
                    JOIN gas_products gp ON si.gas_product_id = gp.id
                                        WHERE s.client_id = ?
                                            AND s.created_at >= (?::date)
                                            AND s.created_at < (?::date + INTERVAL '1 day')
                    UNION ALL
                    SELECT 
                        s.gas_product_id,
                        s.quantity as qty,
                        CASE WHEN gp.gas_type='LPG' AND gp.capacity IN ('12kg','15kg') THEN '12/15kg' ELSE gp.capacity END AS cap_group
                    FROM sales s
                    LEFT JOIN sale_items si ON si.sale_id = s.id
                    JOIN gas_products gp ON s.gas_product_id = gp.id
                                        WHERE s.client_id = ?
                                            AND si.id IS NULL
                                            AND s.created_at >= (?::date)
                                            AND s.created_at < (?::date + INTERVAL '1 day')
                ) t
                JOIN gas_products gp ON t.gas_product_id = gp.id
                GROUP BY gp.gas_type, gp.sub_type, cap_group
            )
        '''
        rows = self.execute_query(query, (client_id, week_start, week_end, client_id, week_start, week_end))
        return rows[0]['result'] if rows and rows[0]['result'] else "0"
