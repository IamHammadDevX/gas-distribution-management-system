from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QFrame, QMessageBox)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QFont, QPixmap
from src.database_module import DatabaseManager
import hashlib

class LoginDialog(QDialog):
    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.current_user = None
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Rajput Gas Management System - Login")
        self.setFixedSize(450, 550)
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        
        # Modern gradient background
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #667eea, stop: 1 #764ba2);
            }
            
            /* Card container */
            .login-card {
                background-color: white;
                border-radius: 15px;
                padding: 40px;
                margin: 20px;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
            }
            
            /* Title styling */
            .title-label {
                color: #2d3748;
                font-size: 28px;
                font-weight: 700;
                margin-bottom: 10px;
            }
            
            .subtitle-label {
                color: #718096;
                font-size: 14px;
                margin-bottom: 30px;
            }
            
            /* Input field styling */
            .input-field {
                background-color: #f7fafc;
                border: 2px solid #e2e8f0;
                border-radius: 10px;
                padding: 15px 20px;
                font-size: 16px;
                color: #2d3748;
                min-height: 50px;
            }
            
            .input-field:focus {
                border-color: #4299e1;
                background-color: white;
                outline: none;
            }
            
            .input-field::placeholder {
                color: #a0aec0;
                font-size: 15px;
            }
            
            /* Label styling */
            .input-label {
                color: #4a5568;
                font-size: 14px;
                font-weight: 600;
                margin-bottom: 8px;
            }
            
            /* Button styling */
            .login-btn {
                background: linear-gradient(to right, #4299e1, #667eea);
                color: white;
                border: none;
                border-radius: 10px;
                padding: 15px;
                font-size: 16px;
                font-weight: 600;
                min-height: 50px;
                margin-top: 10px;
            }
            
            .login-btn:hover {
                background: linear-gradient(to right, #3182ce, #5a67d8);
            }
            
            .login-btn:pressed {
                background: linear-gradient(to right, #2c5282, #4c51bf);
            }
            
            .cancel-btn {
                background-color: transparent;
                color: #718096;
                border: 2px solid #e2e8f0;
                border-radius: 10px;
                padding: 15px;
                font-size: 16px;
                font-weight: 600;
                min-height: 50px;
            }
            
            .cancel-btn:hover {
                background-color: #f7fafc;
                border-color: #cbd5e0;
            }
            
            /* Password toggle button */
            .toggle-password {
                background-color: transparent;
                border: none;
                color: #a0aec0;
                font-size: 14px;
                padding: 5px;
            }
            
            .toggle-password:hover {
                color: #4299e1;
            }
            
            /* Helper text */
            .helper-text {
                color: #a0aec0;
                font-size: 13px;
                margin-top: 20px;
            }
            
            /* Logo placeholder */
            .logo-container {
                background-color: #f7fafc;
                border-radius: 50%;
                width: 80px;
                height: 80px;
                margin-bottom: 20px;
            }
        """)
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Login card container
        login_card = QFrame()
        login_card.setObjectName("login-card")
        
        card_layout = QVBoxLayout()
        card_layout.setSpacing(0)
        card_layout.setContentsMargins(40, 40, 40, 40)
        
        # Logo placeholder
        logo_container = QFrame()
        logo_container.setObjectName("logo-container")
        logo_layout = QVBoxLayout(logo_container)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        
        logo_label = QLabel("🛢️")
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setStyleSheet("""
            font-size: 40px;
            color: #4299e1;
        """)
        logo_layout.addWidget(logo_label)
        
        card_layout.addWidget(logo_container, alignment=Qt.AlignCenter)
        
        # Title section
        title_label = QLabel("Welcome Back")
        title_label.setObjectName("title-label")
        title_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(title_label)
        
        subtitle_label = QLabel("Sign in to your account to continue")
        subtitle_label.setObjectName("subtitle-label")
        subtitle_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(subtitle_label)
        
        # Spacer
        card_layout.addSpacing(20)
        
        # Username field
        username_label = QLabel("Username")
        username_label.setObjectName("input-label")
        card_layout.addWidget(username_label)
        
        self.username_input = QLineEdit()
        self.username_input.setObjectName("input-field")
        self.username_input.setPlaceholderText("Enter your username")
        self.username_input.setClearButtonEnabled(True)
        card_layout.addWidget(self.username_input)
        
        # Password field
        password_label = QLabel("Password")
        password_label.setObjectName("input-label")
        card_layout.addWidget(password_label)
        
        # Password input with toggle
        password_container = QHBoxLayout()
        password_container.setSpacing(0)
        
        self.password_input = QLineEdit()
        self.password_input.setObjectName("input-field")
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setClearButtonEnabled(True)
        password_container.addWidget(self.password_input)
        
        self.toggle_password_btn = QPushButton("👁")
        self.toggle_password_btn.setObjectName("toggle-password")
        self.toggle_password_btn.setFixedSize(30, 30)
        self.toggle_password_btn.clicked.connect(self.toggle_password_visibility)
        password_container.addWidget(self.toggle_password_btn)
        
        card_layout.addLayout(password_container)
        
        # Forgot password link
        forgot_password_label = QLabel("Forgot password?")
        forgot_password_label.setStyleSheet("""
            color: #4299e1;
            font-size: 13px;
            text-decoration: underline;
            margin-top: 5px;
        """)
        forgot_password_label.setAlignment(Qt.AlignRight)
        forgot_password_label.setCursor(Qt.PointingHandCursor)
        # forgot_password_label.mousePressEvent = self.forgot_password_clicked
        card_layout.addWidget(forgot_password_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        button_layout.setContentsMargins(0, 20, 0, 0)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setObjectName("cancel-btn")
        self.cancel_button.clicked.connect(self.reject)
        
        self.login_button = QPushButton("Sign In")
        self.login_button.setObjectName("login-btn")
        self.login_button.clicked.connect(self.login)
        self.login_button.setDefault(True)
        
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.login_button)
        
        card_layout.addLayout(button_layout)
        
        # Default credentials hint
        hint_label = QLabel("Default credentials: admin / admin123")
        hint_label.setObjectName("helper-text")
        hint_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(hint_label)
        
        login_card.setLayout(card_layout)
        main_layout.addWidget(login_card)
        
        self.setLayout(main_layout)
        
        # Connect enter key to login
        self.username_input.returnPressed.connect(self.login)
        self.password_input.returnPressed.connect(self.login)
        
        # Set focus to username
        self.username_input.setFocus()
    
    def toggle_password_visibility(self):
        """Toggle password visibility"""
        if self.password_input.echoMode() == QLineEdit.Password:
            self.password_input.setEchoMode(QLineEdit.Normal)
            self.toggle_password_btn.setText("🙈")
        else:
            self.password_input.setEchoMode(QLineEdit.Password)
            self.toggle_password_btn.setText("👁")
    
    def login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        
        if not username:
            self.username_input.setStyleSheet("""
                background-color: #fff5f5;
                border: 2px solid #fc8181;
                border-radius: 10px;
                padding: 15px 20px;
                font-size: 16px;
                color: #2d3748;
                min-height: 50px;
            """)
            self.username_input.setFocus()
            return
        
        if not password:
            self.password_input.setStyleSheet("""
                background-color: #fff5f5;
                border: 2px solid #fc8181;
                border-radius: 10px;
                padding: 15px 20px;
                font-size: 16px;
                color: #2d3748;
                min-height: 50px;
            """)
            self.password_input.setFocus()
            return
        
        # Reset styles
        self.username_input.setStyleSheet("""
            background-color: #f7fafc;
            border: 2px solid #e2e8f0;
            border-radius: 10px;
            padding: 15px 20px;
            font-size: 16px;
            color: #2d3748;
            min-height: 50px;
        """)
        self.password_input.setStyleSheet("""
            background-color: #f7fafc;
            border: 2px solid #e2e8f0;
            border-radius: 10px;
            padding: 15px 20px;
            font-size: 16px;
            color: #2d3748;
            min-height: 50px;
        """)
        
        try:
            user = self.db_manager.authenticate_user(username, password)
            if user:
                self.current_user = user
                self.db_manager.update_last_login(user['id'])
                self.accept()
            else:
                # Show error with shake animation
                self.shake_dialog()
                self.password_input.clear()
                self.password_input.setFocus()
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Login failed: {str(e)}")
    
    def shake_dialog(self):
        """Shake animation for invalid login"""
        import time
        original_pos = self.pos()
        for i in range(5):
            self.move(original_pos.x() + 5, original_pos.y())
            time.sleep(0.02)
            self.move(original_pos.x() - 5, original_pos.y())
            time.sleep(0.02)
        self.move(original_pos)
    
    def get_user(self) -> dict:
        return self.current_user
