from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QFrame, QMessageBox)
from PySide6.QtCore import Qt
from src.database_module import DatabaseManager

class LoginDialog(QDialog):
    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.current_user = None
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Rajput Gas Management System - Login")
        self.setFixedSize(420, 500)
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)

        self.setStyleSheet("""
            QDialog {
                background-color: #eef3fb;
            }

            QFrame#loginCard {
                background-color: white;
                border: 1px solid #d7e1ef;
                border-radius: 14px;
            }
            QLabel#titleLabel {
                color: #1e3a8a;
                font-size: 24px;
                font-weight: 700;
            }
            QLabel#subtitleLabel {
                color: #64748b;
                font-size: 13px;
            }
            QLabel#inputLabel {
                color: #334155;
                font-size: 13px;
                font-weight: 600;
            }
            QLineEdit {
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                padding: 8px 10px;
                font-size: 14px;
                color: #0f172a;
                min-height: 32px;
            }
            QLineEdit:focus {
                border-color: #2563eb;
                background-color: white;
            }
            QPushButton#loginButton {
                background-color: #2563eb;
                color: white;
                border: 1px solid #1d4ed8;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
                font-weight: 600;
                min-height: 32px;
            }
            QPushButton#loginButton:hover { background-color: #1d4ed8; }
            QPushButton#cancelButton {
                background-color: #ffffff;
                color: #475569;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
                font-weight: 600;
                min-height: 32px;
            }
            QPushButton#cancelButton:hover { background-color: #f8fafc; }
            QPushButton#togglePassword {
                background-color: transparent;
                border: none;
                color: #64748b;
                font-size: 14px;
                min-width: 28px;
            }
            QPushButton#togglePassword:hover { color: #2563eb; }
            QLabel#helperText {
                color: #64748b;
                font-size: 12px;
            }
            QLabel#logoLabel {
                color: #2563eb;
                font-size: 34px;
                font-weight: 700;
            }
            QLabel#linkLabel {
                color: #2563eb;
                font-size: 12px;
                text-decoration: underline;
            }
            QLabel#linkLabel:hover {
                color: white;
                background-color: #2563eb;
            }
        """)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(18, 18, 18, 18)

        login_card = QFrame()
        login_card.setObjectName("loginCard")

        card_layout = QVBoxLayout()
        card_layout.setSpacing(8)
        card_layout.setContentsMargins(24, 24, 24, 24)

        logo_container = QFrame()
        logo_container.setFixedSize(64, 64)
        logo_container.setStyleSheet("background-color: #eff6ff; border-radius: 32px; border: 1px solid #dbeafe;")
        logo_layout = QVBoxLayout(logo_container)
        logo_layout.setContentsMargins(0, 0, 0, 0)

        logo_label = QLabel("🛢️")
        logo_label.setObjectName("logoLabel")
        logo_label.setAlignment(Qt.AlignCenter)
        logo_layout.addWidget(logo_label)

        card_layout.addWidget(logo_container, alignment=Qt.AlignCenter)

        title_label = QLabel("Welcome Back")
        title_label.setObjectName("titleLabel")
        title_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(title_label)

        subtitle_label = QLabel("Sign in to your account to continue")
        subtitle_label.setObjectName("subtitleLabel")
        subtitle_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(subtitle_label)

        card_layout.addSpacing(8)

        username_label = QLabel("Username")
        username_label.setObjectName("inputLabel")
        card_layout.addWidget(username_label)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username")
        self.username_input.setClearButtonEnabled(True)
        card_layout.addWidget(self.username_input)

        password_label = QLabel("Password")
        password_label.setObjectName("inputLabel")
        card_layout.addWidget(password_label)

        password_container = QHBoxLayout()
        password_container.setSpacing(4)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setClearButtonEnabled(True)
        password_container.addWidget(self.password_input)

        self.toggle_password_btn = QPushButton("👁")
        self.toggle_password_btn.setObjectName("togglePassword")
        self.toggle_password_btn.setFixedSize(28, 28)
        self.toggle_password_btn.clicked.connect(self.toggle_password_visibility)
        password_container.addWidget(self.toggle_password_btn)

        card_layout.addLayout(password_container)

        forgot_password_label = QLabel("Forgot password?")
        forgot_password_label.setObjectName("linkLabel")
        forgot_password_label.setAlignment(Qt.AlignRight)
        forgot_password_label.setCursor(Qt.PointingHandCursor)
        card_layout.addWidget(forgot_password_label)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        button_layout.setContentsMargins(0, 12, 0, 0)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setObjectName("cancelButton")
        self.cancel_button.clicked.connect(self.reject)

        self.login_button = QPushButton("Sign In")
        self.login_button.setObjectName("loginButton")
        self.login_button.clicked.connect(self.login)
        self.login_button.setDefault(True)

        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.login_button)

        card_layout.addLayout(button_layout)

        hint_label = QLabel("Default credentials: admin / admin123")
        hint_label.setObjectName("helperText")
        hint_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(hint_label)

        login_card.setLayout(card_layout)
        main_layout.addWidget(login_card)

        self.setLayout(main_layout)

        self.username_input.returnPressed.connect(self.login)
        self.password_input.returnPressed.connect(self.login)

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
                border: 1px solid #ef4444;
                border-radius: 8px;
                padding: 8px 10px;
                min-height: 32px;
            """)
            self.username_input.setFocus()
            return
        
        if not password:
            self.password_input.setStyleSheet("""
                background-color: #fff5f5;
                border: 1px solid #ef4444;
                border-radius: 8px;
                padding: 8px 10px;
                min-height: 32px;
            """)
            self.password_input.setFocus()
            return
        
        # Reset styles
        self.username_input.setStyleSheet("""
            background-color: #ffffff;
            border: 1px solid #cbd5e1;
            border-radius: 8px;
            padding: 8px 10px;
            min-height: 32px;
        """)
        self.password_input.setStyleSheet("""
            background-color: #ffffff;
            border: 1px solid #cbd5e1;
            border-radius: 8px;
            padding: 8px 10px;
            min-height: 32px;
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
