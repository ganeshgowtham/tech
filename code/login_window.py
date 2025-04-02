from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                           QLineEdit, QPushButton, QLabel)
from PyQt5.QtCore import Qt
from chat_window import ChatWindow

class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bank Operator Login")
        self.setFixedSize(400, 300)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        layout.addStretch()
        
        self.username = QLineEdit()
        self.username.setPlaceholderText("Username")
        self.username.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #ccc;
                border-radius: 5px;
                font-size: 14px;
            }
        """)
        
        self.password = QLineEdit()
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setStyleSheet(self.username.styleSheet())
        
        login_btn = QPushButton("Login 🔐")
        login_btn.setStyleSheet("""
            QPushButton {
                padding: 10px;
                background-color: #2ecc71;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        
        layout.addWidget(QLabel("Bank Operator Login 🏦"))
        layout.addWidget(self.username)
        layout.addWidget(self.password)
        layout.addWidget(login_btn)
        layout.addStretch()
        
        login_btn.clicked.connect(self.login)
        
    def login(self):
        # Add actual authentication logic here
        if self.username.text() and self.password.text():
            self.chat_window = ChatWindow()
            self.chat_window.show()
            self.close()
