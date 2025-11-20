import sqlite3
import os
from datetime import datetime, date
from typing import Dict, List, Optional, Any
import shutil
import json

class DatabaseManager:
    def __init__(self, db_path: str = "rajput_gas.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('Admin', 'Accountant', 'Gate Operator', 'Driver')),
                    full_name TEXT NOT NULL,
                    phone TEXT,
                    email TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS clients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    address TEXT,
                    company TEXT,
                    total_purchases DECIMAL(10,2) DEFAULT 0,
                    total_paid DECIMAL(10,2) DEFAULT 0,
                    balance DECIMAL(10,2) DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS gas_products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    gas_type TEXT NOT NULL,
                    sub_type TEXT,
                    capacity TEXT NOT NULL,
                    unit_price DECIMAL(10,2) DEFAULT 0,
                    description TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sales (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id INTEGER NOT NULL,
                    gas_product_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    unit_price DECIMAL(10,2) NOT NULL,
                    subtotal DECIMAL(10,2) NOT NULL,
                    tax_amount DECIMAL(10,2) NOT NULL,
                    total_amount DECIMAL(10,2) NOT NULL,
                    amount_paid DECIMAL(10,2) DEFAULT 0,
                    balance DECIMAL(10,2) DEFAULT 0,
                    created_by INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (client_id) REFERENCES clients (id),
                    FOREIGN KEY (gas_product_id) REFERENCES gas_products (id),
                    FOREIGN KEY (created_by) REFERENCES users (id)
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS receipts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    receipt_number TEXT UNIQUE NOT NULL,
                    sale_id INTEGER NOT NULL,
                    client_id INTEGER NOT NULL,
                    total_amount DECIMAL(10,2) NOT NULL,
                    amount_paid DECIMAL(10,2) DEFAULT 0,
                    balance DECIMAL(10,2) DEFAULT 0,
                    created_by INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (sale_id) REFERENCES sales (id),
                    FOREIGN KEY (client_id) REFERENCES clients (id),
                    FOREIGN KEY (created_by) REFERENCES users (id)
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS gate_passes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    gate_pass_number TEXT UNIQUE NOT NULL,
                    receipt_id INTEGER NOT NULL,
                    client_id INTEGER NOT NULL,
                    driver_name TEXT NOT NULL,
                    vehicle_number TEXT NOT NULL,
                    gas_type TEXT NOT NULL,
                    capacity TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    time_out TIMESTAMP,
                    time_in TIMESTAMP,
                    gate_operator_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (receipt_id) REFERENCES receipts (id),
                    FOREIGN KEY (client_id) REFERENCES clients (id),
                    FOREIGN KEY (gate_operator_id) REFERENCES users (id)
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS employees (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    role TEXT NOT NULL,
                    salary DECIMAL(10,2) NOT NULL,
                    contact TEXT,
                    joining_date DATE NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS activity_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    activity_type TEXT NOT NULL,
                    description TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS backup_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    backup_path TEXT NOT NULL,
                    backup_size INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_clients_phone ON clients (phone)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sales_client_id ON sales (client_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sales_created_at ON sales (created_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_receipts_receipt_number ON receipts (receipt_number)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_gate_passes_receipt_id ON gate_passes (receipt_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_activity_logs_timestamp ON activity_logs (timestamp)')
            cursor.execute('SELECT COUNT(*) FROM users WHERE role = "Admin"')
            if cursor.fetchone()[0] == 0:
                import hashlib
                password_hash = hashlib.sha256("admin123".encode()).hexdigest()
                cursor.execute('''
                    INSERT INTO users (username, password_hash, role, full_name, phone, email)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', ("admin", password_hash, "Admin", "System Administrator", "", ""))
            conn.commit()
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.lastrowid if cursor.lastrowid else cursor.rowcount
    
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
                WHERE name LIKE ? OR phone LIKE ? OR company LIKE ?
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
    
    def add_client(self, name: str, phone: str, address: str = "", company: str = "") -> int:
        query = '''
            INSERT INTO clients (name, phone, address, company)
            VALUES (?, ?, ?, ?)
        '''
        return self.execute_update(query, (name, phone, address, company))
    
    def update_client(self, client_id: int, name: str, phone: str, address: str = "", company: str = "") -> bool:
        query = '''
            UPDATE clients 
            SET name = ?, phone = ?, address = ?, company = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        '''
        return self.execute_update(query, (name, phone, address, company, client_id)) > 0
    
    def update_client_balance(self, client_id: int):
        query = '''
            UPDATE clients 
            SET total_purchases = COALESCE((SELECT SUM(total_amount) FROM sales WHERE client_id = ?), 0),
                total_paid = COALESCE((SELECT SUM(amount_paid) FROM sales WHERE client_id = ?), 0),
                balance = COALESCE((SELECT SUM(balance) FROM sales WHERE client_id = ?), 0),
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
        return self.execute_update(query, (gas_type, sub_type, capacity, unit_price, description))
    
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
        query = 'SELECT COUNT(*) + 1 FROM receipts'
        result = self.execute_query(query)
        count = result[0]['COUNT(*) + 1'] if result else 1
        return f"RCP-{datetime.now().year}-{str(count).zfill(6)}"
    
    def get_next_gate_pass_number(self) -> str:
        query = 'SELECT COUNT(*) + 1 FROM gate_passes'
        result = self.execute_query(query)
        count = result[0]['COUNT(*) + 1'] if result else 1
        return f"GP-{datetime.now().year}-{str(count).zfill(6)}"
    
    def create_gate_pass(self, gate_pass_number: str, receipt_id: int, client_id: int, driver_name: str,
                        vehicle_number: str, gas_type: str, capacity: str, quantity: int, gate_operator_id: int) -> int:
        query = '''
            INSERT INTO gate_passes (gate_pass_number, receipt_id, client_id, driver_name, 
                                   vehicle_number, gas_type, capacity, quantity, gate_operator_id, time_out)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        '''
        return self.execute_update(query, (gate_pass_number, receipt_id, client_id, driver_name,
                                          vehicle_number, gas_type, capacity, quantity, gate_operator_id))
    
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
                   gp.gas_type, gp.sub_type, gp.capacity
            FROM sales s
            JOIN clients c ON s.client_id = c.id
            JOIN gas_products gp ON s.gas_product_id = gp.id
            WHERE DATE(s.created_at) BETWEEN ? AND ?
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
        query = '''
            SELECT gp.*, c.name as client_name, u.full_name as operator_name
            FROM gate_passes gp
            JOIN clients c ON gp.client_id = c.id
            JOIN users u ON gp.gate_operator_id = u.id
            WHERE DATE(gp.created_at) BETWEEN ? AND ?
            ORDER BY gp.created_at DESC
        '''
        return self.execute_query(query, (start_date, end_date))