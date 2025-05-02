from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                           QLineEdit, QPushButton, QLabel, QFrame,
                           QGridLayout, QHBoxLayout)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap, QFont
from chat_window import ChatWindow
import os
import getpass

class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Wells Fargo Operator Portal")
        self.setFixedSize(500, 600)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ffffff;
            }
            QLabel#titleLabel {
                color: #D71E28;
                font-size: 24px;
                font-weight: bold;
                font-family: 'Arial';
            }
            QLabel#subtitleLabel {
                color: #666666;
                font-size: 14px;
                font-family: 'Arial';
            }
            QLineEdit {
                padding: 12px;
                border: 1px solid #cccccc;
                border-radius: 4px;
                font-size: 16px;  /* Increased font size */
                font-family: 'Arial';
                background: white;
                margin: 8px 0px;
                min-height: 25px;  /* Base height */
                padding-top: 8px;  /* Additional padding */
                padding-bottom: 8px;
            }
            QLineEdit:focus {
                border: 2px solid #D71E28;
                outline: none;
            }
            QPushButton#loginButton {
                padding: 12px;
                background-color: #D71E28;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 16px;
                font-weight: bold;
                font-family: 'Arial';
                min-height: 45px;
            }
            QPushButton#loginButton:hover {
                background-color: #b01821;
            }
            QPushButton#loginButton:pressed {
                background-color: #8f141c;
            }
            QFrame#loginFrame {
                background-color: white;
                border: 1px solid #e5e5e5;
                border-radius: 8px;
                padding: 30px;
            }
            QPushButton#closeButton {
                background-color: transparent;
                color: #666666;
                border: none;
                font-size: 20px;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton#closeButton:hover {
                background-color: #f5f5f5;
                color: #D71E28;
            }
            QPushButton#closeButton:pressed {
                background-color: #e5e5e5;
            }
            QWidget#titleBar {
                background-color: transparent;
            }
        """)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(40, 20, 40, 40)
        
        # Add title bar with close button
        title_bar = QWidget()
        title_bar.setObjectName("titleBar")
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(0, 0, 0, 10)
        
        title_bar_layout.addStretch()
        
        close_button = QPushButton("×")
        close_button.setObjectName("closeButton")
        close_button.setFixedSize(30, 30)
        close_button.clicked.connect(self.close)
        title_bar_layout.addWidget(close_button)
        
        main_layout.addWidget(title_bar)
        
        # Create login frame
        login_frame = QFrame()
        login_frame.setObjectName("loginFrame")
        login_frame.setFrameStyle(QFrame.StyledPanel)
        frame_layout = QVBoxLayout(login_frame)
        frame_layout.setSpacing(20)
        
        # Add Wells Fargo logo
        logo_label = QLabel()
        logo_label.setFixedSize(200, 100)  # Adjusted size for Wells Fargo logo
        current_dir = os.path.dirname(os.path.abspath(__file__))
        image_path = os.path.join(current_dir, 'image.png')
        pixmap = QPixmap(image_path)
        scaled_pixmap = pixmap.scaled(200, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        logo_label.setPixmap(scaled_pixmap)
        logo_label.setStyleSheet("background: transparent;")
        logo_label.setAlignment(Qt.AlignCenter)
        
        # Title and subtitle
        title_label = QLabel("Operator Portal")
        title_label.setObjectName("titleLabel")
        title_label.setAlignment(Qt.AlignCenter)
        
        subtitle_label = QLabel("Please sign in with your credentials")
        subtitle_label.setObjectName("subtitleLabel")
        subtitle_label.setAlignment(Qt.AlignCenter)
        
        # Username input
        self.username = QLineEdit()
        self.username.setPlaceholderText("Username")
        self.username.setMinimumHeight(50)  # Increased from 45 to 50
        self.username.setStyleSheet("QLineEdit { padding-left: 15px; }")  # Add left padding for text
        # Set default username as current Windows user
        current_user = getpass.getuser()
        self.username.setText(current_user)
        
        # Password input
        self.password = QLineEdit()
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setMinimumHeight(50)  # Increased from 45 to 50
        self.password.setStyleSheet("QLineEdit { padding-left: 15px; }")  # Add left padding for text
        
        # Login button
        login_btn = QPushButton("Sign In")
        login_btn.setObjectName("loginButton")
        login_btn.setCursor(Qt.PointingHandCursor)  # Add hand cursor on hover
        
        # Add widgets to frame layout
        frame_layout.addWidget(logo_label, 0, Qt.AlignCenter)
        frame_layout.addSpacing(30)  # Increased from 10 to 30
        frame_layout.addWidget(title_label, 0, Qt.AlignCenter)
        frame_layout.addWidget(subtitle_label, 0, Qt.AlignCenter)
        frame_layout.addSpacing(20)
        frame_layout.addWidget(self.username)
        frame_layout.addWidget(self.password)
        frame_layout.addSpacing(10)
        frame_layout.addWidget(login_btn)
        
        # Add frame to main layout with spacing
        main_layout.addStretch(1)
        main_layout.addWidget(login_frame)
        main_layout.addStretch(1)
        
        # Connect login button
        login_btn.clicked.connect(self.login)
        
        # Set window flags for modern look
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        
        # Add ability to drag window
        self.oldPos = None
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        if self.oldPos is not None:
            delta = event.globalPos() - self.oldPos
            self.move(self.pos() + delta)
            self.oldPos = event.globalPos()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.oldPos = None
            
    def login(self):
        if self.username.text() and self.password.text():
            self.chat_window = ChatWindow()
            self.chat_window.show()
            self.close()
