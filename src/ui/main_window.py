from PySide6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, 
                               QPushButton, QLabel, QStackedWidget, QMessageBox, QStatusBar, QFrame, QSizePolicy, QScrollArea)
from PySide6.QtCore import Qt, QTimer, QDateTime, QTime
from PySide6.QtGui import QFont, QGuiApplication
from database_module import DatabaseManager
from datetime import datetime
from components.clients import ClientsWidget
from components.gas_products import GasProductsWidget
from components.sales import SalesWidget
from components.receipts import ReceiptsWidget
from components.gate_passes import GatePassesWidget
from components.employees import EmployeesWidget
from components.reports import ReportsWidget
from components.settings import SettingsWidget

class MainWindow(QMainWindow):
    def __init__(self, db_manager: DatabaseManager, current_user: dict):
        super().__init__()
        self.db_manager = db_manager
        self.current_user = current_user
        self.init_ui()
        self.setup_navigation()
    
    def init_ui(self):
        self.setWindowTitle("Rajput Gas Management System")
        screen = self.screen() or QGuiApplication.primaryScreen()
        available = screen.availableGeometry()
        target_w = min(1200, available.width())
        target_h = min(800, available.height())
        self.resize(target_w, target_h)
        fg = self.frameGeometry()
        fg.moveCenter(available.center())
        self.move(fg.topLeft())

        safe_min_w = min(800, available.width())
        safe_min_h = min(600, available.height())
        self.setMinimumSize(safe_min_w, safe_min_h)
        
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
        
        central_widget = QWidget()
        central_widget.setMinimumSize(0, 0)
        central_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
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
        
        self.nav_buttons = {}
        nav_items = [
            ("Dashboard", "dashboard"),
            ("Clients", "clients"),
            ("Gas Products", "gas_products"),
            ("Sales", "sales"),
            ("Receipts", "receipts"),
            ("Daily Transactions", "daily_transactions"),
            ("Cylinder Track", "cylinder_track"),
            ("Weekly Payments", "weekly_payments"),
            ("Vehicle Expenses", "vehicle_expenses"),
            ("Gate Passes", "gate_passes"),
            ("Employees", "employees"),
            ("Reports", "reports"),
            ("Settings", "settings")
        ]

        buttons_container = QWidget()
        buttons_layout = QVBoxLayout(buttons_container)
        buttons_layout.setSpacing(0)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        for text, name in nav_items:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, n=name: self.switch_page(n))
            buttons_layout.addWidget(btn)
            self.nav_buttons[name] = btn
        buttons_layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidget(buttons_container)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.NoFrame)
        nav_layout.addWidget(scroll)
        
        # User info section
        user_widget = QWidget()
        user_widget.setStyleSheet("background-color: #34495e;")
        user_layout = QVBoxLayout(user_widget)
        user_layout.setSpacing(5)
        user_layout.setContentsMargins(15, 15, 15, 15)
        
        user_label = QLabel(f"Welcome,\n{self.current_user['full_name']}")
        user_label.setStyleSheet("font-size: 14px; font-weight: bold; padding: 0;")
        user_layout.addWidget(user_label)
        self.user_label = user_label
        
        role_label = QLabel(f"Role: {self.current_user['role']}")
        role_label.setStyleSheet("font-size: 12px; color: #bdc3c7; padding: 0;")
        user_layout.addWidget(role_label)
        self.role_label = role_label
        
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
        nav_layout.setStretch(0, 0)
        nav_layout.setStretch(1, 1)
        nav_layout.setStretch(2, 0)
    
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
        """Update date/time in status bar and dashboard greeting"""
        current_datetime = QDateTime.currentDateTime()
        self.datetime_label.setText(current_datetime.toString("dd-MM-yyyy hh:mm:ss"))
        
        # Update dashboard greeting if it exists
        if hasattr(self, 'greeting_label') and hasattr(self, 'date_time_label'):
            # Update greeting
            greeting = self.get_time_based_greeting()
            role_display = "Admin" if self.current_user['role'] == 'Admin' else self.current_user['role']
            self.greeting_label.setText(f"Hello, {greeting} {role_display}!")
            
            # Update date/time in dashboard
            self.date_time_label.setText(current_datetime.toString("dddd, dd MMM yyyy, hh:mm AP"))
    
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

        # Daily Transactions widget
        from components.daily_transactions import DailyTransactionsWidget
        daily_widget = DailyTransactionsWidget(self.db_manager, self.current_user)
        self.widgets["daily_transactions"] = daily_widget
        self.content_area.addWidget(daily_widget)

        # Cylinder Track widget
        from components.cylinder_track import CylinderTrackWidget
        cyl_widget = CylinderTrackWidget(self.db_manager, self.current_user)
        self.widgets["cylinder_track"] = cyl_widget
        self.content_area.addWidget(cyl_widget)

        # Vehicle Expenses widget
        from components.vehicle_expenses import VehicleExpensesWidget
        vexp_widget = VehicleExpensesWidget(self.db_manager, self.current_user)
        self.widgets["vehicle_expenses"] = vexp_widget
        self.content_area.addWidget(vexp_widget)
        
        # Gate passes widget
        gate_passes_widget = GatePassesWidget(self.db_manager, self.current_user)
        self.widgets["gate_passes"] = gate_passes_widget
        self.content_area.addWidget(gate_passes_widget)

        from components.weekly_payments import WeeklyPaymentsWidget
        weekly_widget = WeeklyPaymentsWidget(self.db_manager, self.current_user)
        self.widgets["weekly_payments"] = weekly_widget
        self.content_area.addWidget(weekly_widget)
        
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
    
    def get_time_based_greeting(self):
        hour = QTime.currentTime().hour()
        if 5 <= hour < 12:
            return "Good morning"
        elif 12 <= hour < 17:
            return "Good afternoon"
        elif 17 <= hour < 21:
            return "Good evening"
        else:
            return "Good night"
    
    def create_dashboard_widget(self):
        """Create dashboard widget"""
        from PySide6.QtWidgets import QGridLayout
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        top_bar = self.create_dashboard_top_bar()
        layout.addWidget(top_bar)

        stats_layout = QGridLayout()
        stats_layout.setSpacing(20)

        stats = self.get_dashboard_stats()
        stat_cards = [
            ("Total Cylinders", str(stats['total_cylinders']), "#34495e"),
            ("Empty Cylinders Returned", str(stats['total_cylinders_in']), "#16a085"),
            ("Not Returned Cylinders", str(stats['pending_cylinders']), "#e74c3c"),
            ("Clients Count", str(stats['total_clients']), "#3498db"),
            ("Employees Count", str(stats['employees']), "#9b59b6")
        ]

        for i, (title, value, color) in enumerate(stat_cards):
            card = self.create_stat_card(title, value, color)
            stats_layout.addWidget(card, i // 3, i % 3)

        self.update_dashboard_stats(widget, stats)
        layout.addLayout(stats_layout)
        layout.addStretch()
        return widget
    
    def create_dashboard_top_bar(self):
        """Create dashboard top bar with greeting and current date/time"""
        from PySide6.QtWidgets import QHBoxLayout
        
        top_bar = QWidget()
        top_bar.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-radius: 25px;
                padding: 15px 25px;
                margin: 0;
            }
        """)
        
        layout = QHBoxLayout(top_bar)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(20)
        
        # Left side - Greeting
        greeting = self.get_time_based_greeting()
        role_display = "Admin" if self.current_user['role'] == 'Admin' else self.current_user['role']
        greeting_label = QLabel(f"{greeting}, {role_display}!")
        greeting_label.setStyleSheet("""
            QLabel {
                color: #007bff;
                font-size: 18px;
                font-weight: bold;
                padding: 0;
                margin: 0;
            }
        """)
        layout.addWidget(greeting_label)
        
        layout.addStretch()
        
        # Right side - Date and Time
        current_datetime = QDateTime.currentDateTime()
        date_time_label = QLabel(current_datetime.toString("dddd, dd MMM yyyy, hh:mm AP"))
        date_time_label.setStyleSheet("""
            QLabel {
                color: #6c757d;
                font-size: 14px;
                font-weight: normal;
                padding: 0;
                margin: 0;
            }
        """)
        layout.addWidget(date_time_label)
        
        # Store references for updating
        self.greeting_label = greeting_label
        self.date_time_label = date_time_label
        
        return top_bar
    
    def create_stat_card(self, title: str, value: str, color: str):
        """Create a statistics card"""
        card = QFrame()
        card.setFrameStyle(QFrame.Box)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 2px solid {color};
                border-radius: 12px;
                padding: 16px;
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(6)
        
        caption = QLabel(title)
        caption.setStyleSheet(f"color: {color}; font-size: 13px; font-weight: 600;")
        caption.setAlignment(Qt.AlignLeft)
        layout.addWidget(caption)
        
        value_label = QLabel(value if value is not None else "0")
        value_label.setObjectName(f"stat_value_{title}")
        value_label.setStyleSheet(f"color: {color}; font-size: 26px; font-weight: 800;")
        value_label.setAlignment(Qt.AlignLeft)
        layout.addWidget(value_label)
        
        return card
    
    def get_dashboard_stats(self) -> dict:
        """Get dashboard statistics"""
        from datetime import date
        
        # Total clients
        query = 'SELECT COUNT(*) as count FROM clients'
        result = self.db_manager.execute_query(query)
        total_clients = result[0]['count'] if result else 0
        
        # Employees
        query = 'SELECT COUNT(*) as count FROM employees WHERE is_active = 1'
        result = self.db_manager.execute_query(query)
        employees = result[0]['count'] if result else 0

        # Today's sales
        today = date.today()
        today_str = today.strftime('%Y-%m-%d')
        query = '''
            SELECT COALESCE(SUM(total_amount), 0) as total 
            FROM sales 
            WHERE DATE(created_at) = ?
        '''
        result = self.db_manager.execute_query(query, (today_str,))
        today_sales = result[0]['total'] if result else 0

        # Today's outstanding
        query = '''
            SELECT COALESCE(SUM(balance), 0) as total 
            FROM sales 
            WHERE DATE(created_at) = ?
        '''
        result = self.db_manager.execute_query(query, (today_str,))
        today_outstanding = result[0]['total'] if result else 0

        # Cylinder stats
        query = 'SELECT COALESCE(SUM(quantity), 0) as total FROM gate_passes WHERE DATE(time_out) = ?'
        result = self.db_manager.execute_query(query, (today_str,))
        cylinders_out_today = result[0]['total'] if result else 0

        query = 'SELECT COALESCE(SUM(quantity), 0) as total FROM gate_passes WHERE DATE(time_in) = ?'
        result = self.db_manager.execute_query(query, (today_str,))
        cylinders_in_today = result[0]['total'] if result else 0

        # Pending = total delivered - total returned
        query = 'SELECT COALESCE(SUM(quantity), 0) as total FROM gate_passes'
        result = self.db_manager.execute_query(query)
        total_delivered = int(result[0]['total']) if result else 0
        query = 'SELECT COALESCE(SUM(quantity), 0) as total FROM cylinder_returns'
        result = self.db_manager.execute_query(query)
        total_returned = result[0]['total'] if result else 0
        pending_cylinders = int(total_delivered) - int(total_returned)

        # Total cylinders in (returned)
        total_cylinders_in = int(total_returned)
        
        return {
            'total_clients': total_clients,
            'employees': employees,
            'today_sales': today_sales,
            'today_outstanding': today_outstanding,
            'cylinders_out_today': cylinders_out_today,
            'cylinders_in_today': cylinders_in_today,
            'pending_cylinders': pending_cylinders,
            'total_cylinders_in': total_cylinders_in,
            'total_cylinders': total_delivered
        }
    
    def refresh_dashboard(self):
        """Refresh dashboard statistics"""
        try:
            stats = self.get_dashboard_stats()
            
            # Update the dashboard widget if it exists
            if 'dashboard' in self.widgets:
                dashboard_widget = self.widgets['dashboard']
                self.update_dashboard_stats(dashboard_widget, stats)
                
        except Exception as e:
            print(f"Error refreshing dashboard: {str(e)}")
    
    def update_dashboard_stats(self, dashboard_widget, stats):
        """Update dashboard statistics display"""
        try:
            # Find all stat cards in the dashboard widget
            stat_cards = dashboard_widget.findChildren(QFrame)
            
            # Update the stat card values
            for card in stat_cards:
                # Find the labels within each card
                labels = card.findChildren(QLabel)
                if len(labels) >= 2:
                    title_label = labels[0]
                    value_label = labels[1]
                    
                    # Update based on title
                    title = title_label.text()
                    if title == "Total Clients":
                        value_label.setText(str(stats['total_clients']))
                    elif title == "Employees":
                        value_label.setText(str(stats['employees']))
                    elif title == "Today's Sales":
                        value_label.setText(f"Rs. {stats['today_sales']:,.2f}")
                    elif title == "Today's Outstanding":
                        value_label.setText(f"Rs. {stats['today_outstanding']:,.2f}")
                    elif title == "Cylinders Out Today":
                        value_label.setText(str(stats['cylinders_out_today']))
                    elif title == "Returned Today":
                        value_label.setText(str(stats['cylinders_in_today']))
                    elif title == "Pending Empty Cylinders":
                        value_label.setText(str(stats['pending_cylinders']))
                    elif title == "Total Cylinders In":
                        value_label.setText(str(stats['total_cylinders_in']))
                    elif title == "Total Cylinders":
                        value_label.setText(str(stats['total_cylinders']))
                    elif title == "Empty Cylinders Returned":
                        value_label.setText(str(stats['total_cylinders_in']))
                    elif title == "Not Returned Cylinders":
                        value_label.setText(str(stats['pending_cylinders']))
                    elif title == "Clients Count":
                        value_label.setText(str(stats['total_clients']))
                    elif title == "Employees Count":
                        value_label.setText(str(stats['employees']))
                        
        except Exception as e:
            print(f"Error updating dashboard stats: {str(e)}")
    
    def set_role_permissions(self):
        """Set permissions based on user role"""
        role = self.current_user['role']
        
        # Base permissions for all roles
        enabled_modules = ['dashboard']
        
        if role == 'Admin':
            enabled_modules = ['dashboard', 'clients', 'gas_products', 'sales', 'receipts', 'daily_transactions', 'cylinder_track', 'vehicle_expenses', 'gate_passes', 'employees', 'reports', 'settings']
        elif role == 'Accountant':
            enabled_modules = ['dashboard', 'clients', 'gas_products', 'sales', 'receipts', 'daily_transactions', 'cylinder_track', 'vehicle_expenses', 'reports']
        elif role == 'Gate Operator':
            enabled_modules = ['dashboard', 'daily_transactions', 'cylinder_track', 'gate_passes']
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
            
            # Refresh the current page data
            self.refresh_current_page(page_name)
            
            # Update status bar
            page_titles = {
                "dashboard": "Dashboard",
                "clients": "Client Management",
                "gas_products": "Gas Products",
                "sales": "Sales & Billing",
                "receipts": "Receipts",
                "daily_transactions": "Daily Transactions",
                "cylinder_track": "Cylinder Track",
                "vehicle_expenses": "Vehicle Expenses",
                "gate_passes": "Gate Passes",
                "employees": "Employee Management",
                "reports": "Reports",
                "settings": "Settings"
            }
            self.status_bar.showMessage(f"{page_titles.get(page_name, page_name)} - {self.current_user['full_name']}")
    
    def refresh_current_page(self, page_name: str):
        """Refresh the current page data"""
        try:
            if page_name == "dashboard":
                self.refresh_dashboard()
            elif page_name == "clients":
                if hasattr(self.widgets['clients'], 'load_clients'):
                    self.widgets['clients'].load_clients()
            elif page_name == "gas_products":
                if hasattr(self.widgets['gas_products'], 'load_products'):
                    self.widgets['gas_products'].load_products()
            elif page_name == "sales":
                if hasattr(self.widgets['sales'], 'load_gas_products'):
                    self.widgets['sales'].load_gas_products()
                if hasattr(self.widgets['sales'], 'load_recent_sales'):
                    self.widgets['sales'].load_recent_sales()
            elif page_name == "receipts":
                if hasattr(self.widgets['receipts'], 'load_receipts'):
                    self.widgets['receipts'].load_receipts()
            elif page_name == "gate_passes":
                if hasattr(self.widgets['gate_passes'], 'load_gate_passes'):
                    self.widgets['gate_passes'].load_gate_passes()
            elif page_name == "daily_transactions":
                if hasattr(self.widgets['daily_transactions'], 'load_transactions'):
                    self.widgets['daily_transactions'].load_transactions()
            # Weekly Billing removed
            elif page_name == "employees":
                if hasattr(self.widgets['employees'], 'load_employees'):
                    self.widgets['employees'].load_employees()
            elif page_name == "reports":
                if hasattr(self.widgets['reports'], 'refresh_data'):
                    self.widgets['reports'].refresh_data()
            elif page_name == "settings":
                if hasattr(self.widgets['settings'], 'load_settings'):
                    self.widgets['settings'].load_settings()
        except Exception as e:
            print(f"Error refreshing {page_name}: {str(e)}")
    
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
            # Show login dialog again instead of restarting
            from components.auth import LoginDialog
            login_dialog = LoginDialog(self.db_manager)
            if login_dialog.exec() == LoginDialog.Accepted:
                self.current_user = login_dialog.get_user()
                self.update_user_info()
                self.show()  # Show main window again
            else:
                # If user cancels login, exit application
                import sys
                sys.exit()

    def update_user_info(self):
        """Update UI to reflect current_user after re-login"""
        if hasattr(self, "user_label"):
            self.user_label.setText(f"Welcome,\n{self.current_user['full_name']}")
        if hasattr(self, "role_label"):
            self.role_label.setText(f"Role: {self.current_user['role']}")
        if hasattr(self, "status_bar"):
            self.status_bar.showMessage(f"Welcome, {self.current_user['full_name']}!")
        if hasattr(self, "greeting_label"):
            greeting = self.get_time_based_greeting()
            role_display = "Admin" if self.current_user['role'] == 'Admin' else self.current_user['role']
            self.greeting_label.setText(f"{greeting}, {role_display}!")
        self.set_role_permissions()
        for name, widget in getattr(self, "widgets", {}).items():
            if hasattr(widget, "current_user"):
                widget.current_user = self.current_user
                if hasattr(widget, "set_role_permissions"):
                    widget.set_role_permissions()
        current_widget = self.content_area.currentWidget() if hasattr(self, "content_area") else None
        if current_widget:
            for name, widget in self.widgets.items():
                if widget is current_widget:
                    self.refresh_current_page(name)
                    break
