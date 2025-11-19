from PySide6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, 
                               QPushButton, QLabel, QStackedWidget, QMessageBox, QStatusBar)
from PySide6.QtCore import Qt, QTimer, QDateTime
from PySide6.QtGui import QFont
from database import DatabaseManager
from clients import ClientsWidget
from gas_products import GasProductsWidget
from sales import SalesWidget
from receipts import ReceiptsWidget
from gate_passes import GatePassesWidget
from employees import EmployeesWidget
from reports import ReportsWidget
from settings import SettingsWidget

class MainWindow(QMainWindow):
    def __init__(self, db_manager: DatabaseManager, current_user: dict):
        super().__init__()
        self.db_manager = db_manager
        self.current_user = current_user
        self.init_ui()
        self.setup_navigation()
    
    def init_ui(self):
        self.setWindowTitle("Rajput Gas Management System")
        self.setGeometry(100, 100, 1200, 800)
        
        # Set application style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            QLabel {
                color: #333;
                font-size: 14px;
            }
            QLineEdit {
                padding: 6px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #4CAF50;
            }
            QComboBox {
                padding: 6px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
            }
            QTableWidget {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                gridline-color: #e0e0e0;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #e8f5e8;
                color: #333;
            }
            QHeaderView::section {
                background-color: #4CAF50;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create navigation sidebar
        self.create_navigation_sidebar()
        main_layout.addWidget(self.nav_widget)
        
        # Create content area
        self.content_area = QStackedWidget()
        main_layout.addWidget(self.content_area)
        
        # Create status bar
        self.create_status_bar()
        
        # Set sidebar width ratio
        main_layout.setStretch(0, 1)  # Navigation sidebar
        main_layout.setStretch(1, 4)  # Content area
    
    def create_navigation_sidebar(self):
        """Create the navigation sidebar"""
        self.nav_widget = QWidget()
        self.nav_widget.setFixedWidth(250)
        self.nav_widget.setStyleSheet("""
            QWidget {
                background-color: #2c3e50;
            }
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
                padding: 12px 20px;
                text-align: left;
                font-size: 14px;
                font-weight: bold;
                border-radius: 0;
            }
            QPushButton:hover {
                background-color: #34495e;
            }
            QPushButton:checked {
                background-color: #4CAF50;
            }
            QLabel {
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 20px;
            }
        """)
        
        nav_layout = QVBoxLayout(self.nav_widget)
        nav_layout.setSpacing(0)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        
        # Company name
        company_label = QLabel("Rajput Gas Ltd.")
        company_label.setAlignment(Qt.AlignCenter)
        nav_layout.addWidget(company_label)
        
        # Add separator
        separator = QLabel()
        separator.setFixedHeight(2)
        separator.setStyleSheet("background-color: #34495e;")
        nav_layout.addWidget(separator)
        
        # Create navigation buttons
        self.nav_buttons = {}
        nav_items = [
            ("Dashboard", "dashboard"),
            ("Clients", "clients"),
            ("Gas Products", "gas_products"),
            ("Sales", "sales"),
            ("Receipts", "receipts"),
            ("Gate Passes", "gate_passes"),
            ("Employees", "employees"),
            ("Reports", "reports"),
            ("Settings", "settings")
        ]
        
        for text, name in nav_items:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, n=name: self.switch_page(n))
            nav_layout.addWidget(btn)
            self.nav_buttons[name] = btn
        
        nav_layout.addStretch()
        
        # User info section
        user_widget = QWidget()
        user_widget.setStyleSheet("background-color: #34495e;")
        user_layout = QVBoxLayout(user_widget)
        user_layout.setSpacing(5)
        user_layout.setContentsMargins(15, 15, 15, 15)
        
        user_label = QLabel(f"Welcome,\n{self.current_user['full_name']}")
        user_label.setStyleSheet("font-size: 14px; font-weight: bold; padding: 0;")
        user_layout.addWidget(user_label)
        
        role_label = QLabel(f"Role: {self.current_user['role']}")
        role_label.setStyleSheet("font-size: 12px; color: #bdc3c7; padding: 0;")
        user_layout.addWidget(role_label)
        
        logout_btn = QPushButton("Logout")
        logout_btn.clicked.connect(self.logout)
        logout_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                padding: 8px;
                border-radius: 4px;
                text-align: center;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        user_layout.addWidget(logout_btn)
        
        nav_layout.addWidget(user_widget)
    
    def create_status_bar(self):
        """Create status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Add current date/time
        self.datetime_label = QLabel()
        self.status_bar.addPermanentWidget(self.datetime_label)
        
        # Update datetime every second
        self.datetime_timer = QTimer()
        self.datetime_timer.timeout.connect(self.update_datetime)
        self.datetime_timer.start(1000)
        self.update_datetime()
        
        # Add welcome message
        self.status_bar.showMessage(f"Welcome, {self.current_user['full_name']}!")
    
    def update_datetime(self):
        """Update date/time in status bar"""
        current_datetime = QDateTime.currentDateTime()
        self.datetime_label.setText(current_datetime.toString("dd-MM-yyyy hh:mm:ss"))
    
    def setup_navigation(self):
        """Setup navigation and create widgets based on user role"""
        # Create widgets for content area
        self.widgets = {}
        
        # Dashboard widget
        dashboard_widget = self.create_dashboard_widget()
        self.widgets["dashboard"] = dashboard_widget
        self.content_area.addWidget(dashboard_widget)
        
        # Clients widget
        clients_widget = ClientsWidget(self.db_manager, self.current_user)
        self.widgets["clients"] = clients_widget
        self.content_area.addWidget(clients_widget)
        
        # Gas Products widget
        gas_products_widget = GasProductsWidget(self.db_manager, self.current_user)
        self.widgets["gas_products"] = gas_products_widget
        self.content_area.addWidget(gas_products_widget)
        
        # Sales widget
        sales_widget = SalesWidget(self.db_manager, self.current_user)
        self.widgets["sales"] = sales_widget
        self.content_area.addWidget(sales_widget)
        
        # Receipts widget
        receipts_widget = ReceiptsWidget(self.db_manager, self.current_user)
        self.widgets["receipts"] = receipts_widget
        self.content_area.addWidget(receipts_widget)
        
        # Gate passes widget
        gate_passes_widget = GatePassesWidget(self.db_manager, self.current_user)
        self.widgets["gate_passes"] = gate_passes_widget
        self.content_area.addWidget(gate_passes_widget)
        
        # Employees widget
        employees_widget = EmployeesWidget(self.db_manager, self.current_user)
        self.widgets["employees"] = employees_widget
        self.content_area.addWidget(employees_widget)
        
        # Reports widget
        reports_widget = ReportsWidget(self.db_manager, self.current_user)
        self.widgets["reports"] = reports_widget
        self.content_area.addWidget(reports_widget)
        
        # Settings widget
        settings_widget = SettingsWidget(self.db_manager, self.current_user)
        self.widgets["settings"] = settings_widget
        self.content_area.addWidget(settings_widget)
        
        # Set role-based permissions
        self.set_role_permissions()
        
        # Show dashboard by default
        self.switch_page("dashboard")
    
    def create_dashboard_widget(self):
        """Create dashboard widget"""
        from PySide6.QtWidgets import QGridLayout, QFrame
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title_label = QLabel("Dashboard")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title_label)
        
        # Statistics cards
        stats_layout = QGridLayout()
        stats_layout.setSpacing(20)
        
        # Get dashboard statistics
        stats = self.get_dashboard_stats()
        
        # Create stat cards
        stat_cards = [
            ("Total Clients", str(stats['total_clients']), "#3498db"),
            ("Total Sales", f"Rs. {stats['total_sales']:,.2f}", "#2ecc71"),
            ("Outstanding Balance", f"Rs. {stats['outstanding_balance']:,.2f}", "#e74c3c"),
            ("Today's Sales", f"Rs. {stats['today_sales']:,.2f}", "#f39c12")
        ]
        
        for i, (title, value, color) in enumerate(stat_cards):
            card = self.create_stat_card(title, value, color)
            stats_layout.addWidget(card, i // 2, i % 2)
        
        layout.addLayout(stats_layout)
        layout.addStretch()
        
        return widget
    
    def create_stat_card(self, title: str, value: str, color: str):
        """Create a statistics card"""
        from PySide6.QtWidgets import QFrame
        
        card = QFrame()
        card.setFrameStyle(QFrame.Box)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 2px solid {color};
                border-radius: 8px;
                padding: 20px;
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(10)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {color}; font-size: 14px; font-weight: bold;")
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setStyleSheet(f"color: {color}; font-size: 20px; font-weight: bold;")
        layout.addWidget(value_label)
        
        return card
    
    def get_dashboard_stats(self) -> dict:
        """Get dashboard statistics"""
        from datetime import date
        
        # Total clients
        query = 'SELECT COUNT(*) as count FROM clients'
        result = self.db_manager.execute_query(query)
        total_clients = result[0]['count'] if result else 0
        
        # Total sales
        query = 'SELECT COALESCE(SUM(total_amount), 0) as total FROM sales'
        result = self.db_manager.execute_query(query)
        total_sales = result[0]['total'] if result else 0
        
        # Outstanding balance
        query = 'SELECT COALESCE(SUM(balance), 0) as total FROM clients'
        result = self.db_manager.execute_query(query)
        outstanding_balance = result[0]['total'] if result else 0
        
        # Today's sales
        today = date.today()
        query = '''
            SELECT COALESCE(SUM(total_amount), 0) as total 
            FROM sales 
            WHERE DATE(created_at) = ?
        '''
        result = self.db_manager.execute_query(query, (today,))
        today_sales = result[0]['total'] if result else 0
        
        return {
            'total_clients': total_clients,
            'total_sales': total_sales,
            'outstanding_balance': outstanding_balance,
            'today_sales': today_sales
        }
    
    def set_role_permissions(self):
        """Set permissions based on user role"""
        role = self.current_user['role']
        
        # Base permissions for all roles
        enabled_modules = ['dashboard']
        
        if role == 'Admin':
            enabled_modules = ['dashboard', 'clients', 'gas_products', 'sales', 'receipts', 'gate_passes', 'employees', 'reports', 'settings']
        elif role == 'Accountant':
            enabled_modules = ['dashboard', 'clients', 'gas_products', 'sales', 'receipts', 'reports']
        elif role == 'Gate Operator':
            enabled_modules = ['dashboard', 'gate_passes']
        elif role == 'Driver':
            enabled_modules = ['dashboard']
        
        # Enable/disable navigation buttons based on role
        for module_name, button in self.nav_buttons.items():
            button.setEnabled(module_name in enabled_modules)
    
    def switch_page(self, page_name: str):
        """Switch to different page"""
        if page_name in self.widgets:
            # Update button states
            for name, button in self.nav_buttons.items():
                button.setChecked(name == page_name)
            
            # Switch content
            self.content_area.setCurrentWidget(self.widgets[page_name])
            
            # Update status bar
            page_titles = {
                "dashboard": "Dashboard",
                "clients": "Client Management",
                "gas_products": "Gas Products",
                "sales": "Sales & Billing",
                "receipts": "Receipts",
                "gate_passes": "Gate Passes",
                "employees": "Employee Management",
                "reports": "Reports",
                "settings": "Settings"
            }
            self.status_bar.showMessage(f"{page_titles.get(page_name, page_name)} - {self.current_user['full_name']}")
    
    def logout(self):
        """Handle logout"""
        reply = QMessageBox.question(
            self, 
            "Logout", 
            "Are you sure you want to logout?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.db_manager.log_activity("LOGOUT", f"User {self.current_user['username']} logged out")
            self.close()
            # Restart application
            import subprocess
            import sys
            subprocess.Popen([sys.executable, __file__.replace('main_window.py', 'main.py')])