from PySide6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, 
                               QPushButton, QLabel, QStackedWidget, QMessageBox, QStatusBar, QFrame, QSizePolicy)
from PySide6.QtCore import Qt, QTimer, QDateTime, QTime
from PySide6.QtGui import QFont, QGuiApplication
from database_module import DatabaseManager
from datetime import datetime
from components.clients import ClientsWidget
from components.gas_products import GasProductsWidget
from components.sales import SalesWidget
from components.receipts import ReceiptsWidget
from components.gate_passes import GatePassesWidget, CylinderReturnsWidget
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
        
        # Create navigation buttons
        self.nav_buttons = {}
        nav_items = [
            ("Dashboard", "dashboard"),
            ("Clients", "clients"),
            ("Gas Products", "gas_products"),
            ("Sales", "sales"),
            ("Receipts", "receipts"),
            ("Gate Passes", "gate_passes"),
            ("Cylinder Returns", "cylinder_returns"),
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
            self.greeting_label.setText(f"{greeting}, {role_display}!")
            
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
        
        # Gate passes widget
        gate_passes_widget = GatePassesWidget(self.db_manager, self.current_user)
        self.widgets["gate_passes"] = gate_passes_widget
        self.content_area.addWidget(gate_passes_widget)
        cylinder_returns_widget = CylinderReturnsWidget(self.db_manager, self.current_user)
        self.widgets["cylinder_returns"] = cylinder_returns_widget
        self.content_area.addWidget(cylinder_returns_widget)
        
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
        """Get time-based greeting"""
        current_time = QTime.currentTime()
        hour = current_time.hour()
        
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
        from PySide6.QtWidgets import QGridLayout, QStackedWidget
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        top_bar = self.create_dashboard_top_bar()
        layout.addWidget(top_bar)
        
        self.dashboard_widget = widget
        
        self.dashboard_stack = QStackedWidget()
        
        full_page = QWidget()
        full_layout = QVBoxLayout(full_page)
        full_layout.setSpacing(20)
        
        title_label = QLabel("Dashboard")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50;")
        full_layout.addWidget(title_label)
        
        stats_layout = QGridLayout()
        stats_layout.setSpacing(20)
        
        stats = self.get_dashboard_stats()
        stat_cards = [
            ("Total Clients", str(stats['total_clients']), "#3498db"),
            ("Total Sales", f"Rs. {stats['total_sales']:,.2f}", "#2ecc71"),
            ("Outstanding Balance", f"Rs. {stats['outstanding_balance']:,.2f}", "#e74c3c"),
            ("Today's Sales", f"Rs. {stats['today_sales']:,.2f}", "#f39c12")
        ]
        for i, (title, value, color) in enumerate(stat_cards):
            card = self.create_stat_card(title, value, color)
            stats_layout.addWidget(card, i // 2, i % 2)
        full_layout.addLayout(stats_layout)
        full_layout.addStretch()
        
        company_page = QWidget()
        company_layout = QVBoxLayout(company_page)
        company_layout.setSpacing(20)
        
        company_title = QLabel("Company Information")
        company_title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50;")
        company_layout.addWidget(company_title)
        
        from PySide6.QtWidgets import QGridLayout
        info_card = QFrame()
        info_card.setStyleSheet("QFrame { background-color: white; border: 2px solid #3498db; border-radius: 8px; padding: 20px; }")
        info_layout = QGridLayout(info_card)
        info_layout.setHorizontalSpacing(20)
        info_layout.setVerticalSpacing(10)
        
        label_style = "color: #7f8c8d; font-size: 13px;"
        value_style = "color: #2c3e50; font-size: 16px; font-weight: bold;"
        
        name_label = QLabel("Company Name:")
        name_label.setStyleSheet(label_style)
        self.company_name_value = QLabel("")
        self.company_name_value.setStyleSheet(value_style)
        info_layout.addWidget(name_label, 0, 0)
        info_layout.addWidget(self.company_name_value, 0, 1)
        
        proprietor_label = QLabel("Proprietor:")
        proprietor_label.setStyleSheet(label_style)
        self.company_proprietor_value = QLabel("")
        self.company_proprietor_value.setStyleSheet(value_style)
        info_layout.addWidget(proprietor_label, 1, 0)
        info_layout.addWidget(self.company_proprietor_value, 1, 1)
        
        company_layout.addWidget(info_card)
        
        description_card = QFrame()
        description_card.setStyleSheet("QFrame { background-color: white; border: 2px solid #2ecc71; border-radius: 8px; padding: 20px; }")
        description_layout = QVBoxLayout(description_card)
        description_title = QLabel("Description")
        description_title.setStyleSheet("color: #2ecc71; font-size: 14px; font-weight: bold;")
        self.company_description_value = QLabel("")
        self.company_description_value.setStyleSheet("color: #2c3e50; font-size: 14px;")
        self.company_description_value.setWordWrap(True)
        description_layout.addWidget(description_title)
        description_layout.addWidget(self.company_description_value)
        company_layout.addWidget(description_card)
        
        self.dashboard_stack.addWidget(full_page)
        self.dashboard_stack.addWidget(company_page)
        layout.addWidget(self.dashboard_stack)
        
        self.refresh_company_page()
        
        return widget
    
    def create_dashboard_top_bar(self):
        """Create dashboard top bar with greeting and current date/time"""
        from PySide6.QtWidgets import QHBoxLayout, QPushButton
        
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
        
        if self.current_user['role'] == 'Admin':
            toggle_btn = QPushButton("Toggle View")
            toggle_btn.setStyleSheet("""
                QPushButton {
                    background-color: #6c757d;
                    color: white;
                    padding: 8px 16px;
                    border-radius: 18px;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #5a6268; }
                QPushButton:pressed { background-color: #545b62; }
            """)
            toggle_btn.clicked.connect(self.toggle_dashboard_view)
            layout.addWidget(toggle_btn)
            self.dashboard_toggle_btn = toggle_btn
        
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
    
    def refresh_dashboard(self):
        """Refresh dashboard statistics"""
        try:
            if hasattr(self, 'dashboard_stack') and self.dashboard_stack.currentIndex() == 0:
                stats = self.get_dashboard_stats()
                if 'dashboard' in self.widgets:
                    dashboard_widget = self.widgets['dashboard']
                    self.update_dashboard_stats(dashboard_widget, stats)
            else:
                self.refresh_company_page()
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
                    elif title == "Total Sales":
                        value_label.setText(f"Rs. {stats['total_sales']:,.2f}")
                    elif title == "Outstanding Balance":
                        value_label.setText(f"Rs. {stats['outstanding_balance']:,.2f}")
                    elif title == "Today's Sales":
                        value_label.setText(f"Rs. {stats['today_sales']:,.2f}")
                        
        except Exception as e:
            print(f"Error updating dashboard stats: {str(e)}")

    def get_company_info(self) -> dict:
        return {
            'company_name': 'Rajput Gas Ltd.',
            'proprietor': 'Saleem Ahmad',
            'description': 'Rajput Gas Ltd. supplies industrial and medical gases with a focus on safety, reliability, and timely delivery. We manage cylinder logistics, gate pass operations, and customer billing with robust controls.'
        }

    def refresh_company_page(self):
        try:
            info = self.get_company_info()
            self.company_name_value.setText(info['company_name'])
            self.company_proprietor_value.setText(info['proprietor'])
            self.company_description_value.setText(info['description'])
        except Exception as e:
            print(f"Error refreshing company page: {str(e)}")

    def toggle_dashboard_view(self):
        try:
            if hasattr(self, 'dashboard_stack'):
                idx = self.dashboard_stack.currentIndex()
                self.dashboard_stack.setCurrentIndex(1 if idx == 0 else 0)
                if hasattr(self, 'dashboard_toggle_btn'):
                    self.dashboard_toggle_btn.setText("Show Dashboard" if idx == 0 else "Toggle View")
                self.refresh_dashboard()
        except Exception as e:
            print(f"Error toggling dashboard: {str(e)}")
    
    def set_role_permissions(self):
        """Set permissions based on user role"""
        role = self.current_user['role']
        
        # Base permissions for all roles
        enabled_modules = ['dashboard']
        
        if role == 'Admin':
            enabled_modules = ['dashboard', 'clients', 'gas_products', 'sales', 'receipts', 'gate_passes', 'cylinder_returns', 'employees', 'reports', 'settings']
        elif role == 'Accountant':
            enabled_modules = ['dashboard', 'clients', 'gas_products', 'sales', 'receipts', 'reports']
        elif role == 'Gate Operator':
            enabled_modules = ['dashboard', 'gate_passes', 'cylinder_returns']
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
                "gate_passes": "Gate Passes",
                "cylinder_returns": "Cylinder Returns",
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
            elif page_name == "cylinder_returns":
                if hasattr(self.widgets['cylinder_returns'], 'load_summary'):
                    self.widgets['cylinder_returns'].load_summary()
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