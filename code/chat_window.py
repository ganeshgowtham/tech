from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                           QLineEdit, QPushButton, QComboBox, QCompleter,
                           QListWidget, QLabel, QMenu, QAction, QProgressBar, 
                           QTextEdit, QSystemTrayIcon, QListWidgetItem, QStyle)
from PyQt5.QtCore import Qt, QStringListModel, QTimer
from PyQt5.QtGui import QIcon
import json
from datetime import datetime
import logging
from service import ChatService  # Add this import
from service import ChatServiceError, CommandError, EmailError, LogError, LoginError

# Setup logging configuration
logging.basicConfig(
    filename='operator.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class LoadingOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        layout = QVBoxLayout()
        self.loading_label = QLabel("⌛")
        self.loading_label.setProperty('class', 'loading-label')
        self.loading_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.loading_label)
        layout.setAlignment(Qt.AlignCenter)
        self.setLayout(layout)
        self.hide()

    def showEvent(self, event):
        self.setGeometry(self.parent().rect())

class ChatWindow(QMainWindow):
    APP_VERSION = "1.0.0"
    
    # Add theme color constants
    DARK_THEME = {
        'bg': '#111315',
        'sidebar': '#1D2023',
        'content': '#1A1C1E',
        'input': '#2D3135',
        'border': '#404346',
        'text': '#E4E7EB',
        'highlight': '#2662D9',
        'hover': '#363A3D'
    }
    
    LIGHT_THEME = {
        'bg': '#FFFFFF',
        'sidebar': '#F5F5F5',
        'content': '#FAFAFA',
        'input': '#EEEEEE',
        'border': '#E0E0E0',
        'text': '#2C3E50',
        'highlight': '#3498DB',
        'hover': '#E8E8E8'
    }
    
    # Add persona icons
    USER_ICON = "👨‍💼"  # Bank operator icon
    ASSISTANT_ICON = "🤖"  # AI assistant icon

    # Add persona list
    PERSONAS = [
        {"name": "General Assistant", "icon": "🤖", "description": "General purpose AI assistant"},
        {"name": "Technical Support", "icon": "👨‍💻", "description": "Technical help and troubleshooting"},
        {"name": "Banking Expert", "icon": "💰", "description": "Banking and financial assistance"},
        {"name": "Customer Service", "icon": "👩‍💼", "description": "Customer support and inquiries"}
    ]
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bank Operator Assistant")
        self.resize(1000, 800)
        self.command_list = ["/fix", "/help", "/search", "/text", "/image", "/video"]
        
        # Setup command completer
        self.command_completer = QCompleter(self.command_list)
        self.command_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.command_completer.setFilterMode(Qt.MatchStartsWith)
        
        self.history = []
        self.history_widget = None
        self.contact_widget = None
        self.log_widget = None
        self.right_panel = None
        self.username = None  # Add username attribute
        self.loading_overlay = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.handle_response)
        self.current_message = None
        self.is_dark_mode = True
        self.notification_count = 0
        self.current_theme = self.DARK_THEME
        self.current_persona = self.PERSONAS[0]  # Default persona
        self.chat_service = ChatService()
        self.setup_tray()
        self.setup_ui()

    def setup_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        # Get system default app icon
        app_icon = self.style().standardIcon(QStyle.SP_ComputerIcon)
        self.tray_icon.setIcon(app_icon)
        
        # Create tray menu
        tray_menu = QMenu()
        show_action = QAction("Show", self)
        quit_action = QAction("Exit", self)
        show_action.triggered.connect(self.show)
        quit_action.triggered.connect(self.close)
        
        tray_menu.addAction(show_action)
        tray_menu.addSeparator()
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)
        self.tray_icon.show()

    def tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show()
            self.activateWindow()

    def closeEvent(self, event):
        try:
            self.chat_service.logout_user()
            logging.info("Application closing, user logged out")
        except LoginError as e:
            logging.error(f"Error during logout: {str(e)}")
        except Exception as e:
            logging.error(f"Unexpected error during logout: {str(e)}")
        finally:
            self.tray_icon.hide()
            event.accept()

    def set_user_logged_in(self, username):
        try:
            username = self.chat_service.login_user(username)
            self.username = username
            self.setWindowTitle(f"Bank Operator Assistant - {username} 👤")
            self.show_notification("Login Successful", f"Welcome, {username}!")
            logging.info(f"User interface updated for logged in user: {username}")
        except LoginError as e:
            self.show_error("Login Error", e)
            self.username = None
            logging.error(f"Login failed in UI: {str(e)}")
        except Exception as e:
            self.show_error("Unexpected Error", f"Login failed: {str(e)}")
            self.username = None
            logging.error(f"Unexpected error during login in UI: {str(e)}")

    def show_notification(self, title, message, duration=3000):
        self.tray_icon.showMessage(
            title,
            message,
            QSystemTrayIcon.Information,
            duration
        )
        self.update_notification_badge()

    def show_error(self, title, error):
        """Show error notification with appropriate icon and longer duration"""
        self.tray_icon.showMessage(
            f"Error: {title}",
            str(error),
            QSystemTrayIcon.Critical,
            5000
        )
        logging.error(f"{title}: {str(error)}")

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Left vertical sidebar
        sidebar = QWidget()
        sidebar.setFixedWidth(70)  # Increased from 50
        sidebar.setProperty("sidebar", True)
        
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setAlignment(Qt.AlignTop)
        sidebar_layout.setSpacing(20)  # Add spacing between buttons
        sidebar_layout.setContentsMargins(10, 20, 10, 10)  # Add margins around buttons
        
        # Theme toggle button
        theme_btn = QPushButton("🌙" if self.is_dark_mode else "☀️")
        theme_btn.setToolTip("Toggle Theme")
        theme_btn.clicked.connect(self.toggle_theme)
        
        # History button
        history_btn = QPushButton("📝")
        history_btn.setToolTip("Chat History")
        history_btn.clicked.connect(self.toggle_history)
        
        # Notifications button with badge
        notif_container = QWidget()
        notif_layout = QHBoxLayout(notif_container)
        notif_layout.setContentsMargins(0, 0, 0, 0)
        
        notif_btn = QPushButton("🔔")
        notif_btn.setToolTip("Notifications")
        
        self.notif_badge = QLabel("0")
        self.notif_badge.setProperty('class', 'notification-badge')
        self.notif_badge.hide()
        
        notif_layout.addWidget(notif_btn)
        notif_layout.addWidget(self.notif_badge, 0, Qt.AlignTop | Qt.AlignRight)
        
        # Log viewer button
        log_btn = QPushButton("📋")
        log_btn.setToolTip("View Logs")
        log_btn.clicked.connect(self.toggle_logs)
        
        # Info button
        info_btn = QPushButton("ℹ️")
        info_btn.setToolTip("Information")
        info_btn.clicked.connect(self.show_contact_info)
        
        # Add buttons to sidebar
        sidebar_layout.addWidget(theme_btn)
        sidebar_layout.addWidget(history_btn)
        sidebar_layout.addWidget(notif_container)
        sidebar_layout.addWidget(log_btn)
        sidebar_layout.addWidget(info_btn)
        sidebar_layout.addStretch()
        
        # Main content container
        content_container = QWidget()
        content_layout = QHBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        # Left panel for chat
        chat_panel = QWidget()
        chat_layout = QVBoxLayout(chat_panel)
        
        # Add persona selector
        persona_container = QWidget()
        persona_container.setProperty('class', 'persona-container')
        persona_layout = QHBoxLayout(persona_container)
        
        self.persona_combo = QComboBox()
        self.persona_combo.setProperty('class', 'persona-selector')
        for persona in self.PERSONAS:
            self.persona_combo.addItem(f"{persona['icon']} {persona['name']}")
        self.persona_combo.currentIndexChanged.connect(self.change_persona)
        
        persona_layout.addWidget(QLabel("Current Persona:"))
        persona_layout.addWidget(self.persona_combo)
        persona_layout.addStretch()
        
        chat_layout.addWidget(persona_container)
        
        # Chat display
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.clear()  # Clear any initial empty space
        self.chat_display.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.chat_display.setPlaceholderText("Start chatting...")  # Add placeholder text
        
        # Progress bar
        self.progress = QProgressBar()
        self.progress.hide()
        
        # Input area
        input_container = QWidget()
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(0)
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type your message here...")
        self.input_field.setMinimumHeight(45)
        self.input_field.textChanged.connect(self.on_input_changed)
        self.input_field.setCompleter(self.command_completer)  # Add completer to input field
        
        # Clear button
        self.clear_btn = QPushButton("✕")
        self.clear_btn.setProperty('class', 'clear-btn')
        self.clear_btn.setFixedSize(45, 45)
        self.clear_btn.setCursor(Qt.PointingHandCursor)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #808080;
                font-size: 14px;
                margin-right: 5px;
            }
            QPushButton:hover {
                color: #e74c3c;
            }
        """)
        self.clear_btn.clicked.connect(self.clear_input)
        self.clear_btn.hide()  # Initially hidden
        
        send_btn = QPushButton("Send")
        send_btn.setProperty('class', 'send-btn')
        send_btn.setFixedSize(70, 45)  # Make wider to fit text
        send_btn.setStyleSheet("""
            QPushButton {
                background-color: #2662D9;
                border-radius: 22px;
                font-size: 14px;
                font-weight: bold;
                color: white;
            }
            QPushButton:hover {
                background-color: #1D4BA3;
            }
        """)
        send_btn.clicked.connect(self.send_message)
        
        self.input_field.returnPressed.connect(self.send_message)
        
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.clear_btn)
        input_layout.addWidget(send_btn)
        
        chat_layout.addWidget(self.chat_display)
        chat_layout.addWidget(self.progress)
        chat_layout.addWidget(input_container)
        
        # Right panel for settings only
        right_panel = QWidget()
        right_panel.setFixedWidth(40)  # Reduce width
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 5, 5, 0)  # Adjust margins
        
        # Settings menu - updated style and layout
        settings_btn = QPushButton("⚙️")
        settings_btn.setFixedSize(25, 25)  # Make button smaller
        settings_btn.clicked.connect(self.show_settings)
        
        right_layout.addWidget(settings_btn, 0, Qt.AlignRight | Qt.AlignTop)
        
        # Add panels to content layout
        content_layout.addWidget(chat_panel, stretch=9)
        content_layout.addWidget(right_panel)
        
        # Add sidebar and content to main layout
        layout.addWidget(sidebar)
        layout.addWidget(content_container, stretch=1)
        
        # Initialize panels
        self.setup_history_panel()
        self.setup_contact_panel()
        self.setup_log_panel()
        self.loading_overlay = LoadingOverlay(self.chat_display)
        
        self.apply_theme()

    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        self.current_theme = self.DARK_THEME if self.is_dark_mode else self.LIGHT_THEME
        sender = self.sender()
        sender.setText("🌙" if self.is_dark_mode else "☀️")
        self.apply_theme()
        
    def apply_theme(self):
        theme = self.current_theme
        # Load CSS file
        with open('styles.css', 'r') as f:
            css = f.read()
        
        # Replace CSS variables with theme colors
        css = css.replace('var(--bg)', theme['bg'])
        css = css.replace('var(--sidebar)', theme['sidebar'])
        css = css.replace('var(--content)', theme['content'])
        css = css.replace('var(--input)', theme['input'])
        css = css.replace('var(--border)', theme['border'])
        css = css.replace('var(--text)', theme['text'])
        css = css.replace('var(--highlight)', theme['highlight'])
        css = css.replace('var(--hover)', theme['hover'])
        
        self.setStyleSheet(css)
        
        # Update sidebar style
        for widget in self.findChildren(QWidget):
            if widget.property("sidebar"):
                widget.setStyleSheet(f"""
                    background-color: {theme['sidebar']};
                    border-right: 1px solid {theme['border']};
                """)

    def setup_history_panel(self):
        self.history_widget = QWidget()
        history_layout = QVBoxLayout(self.history_widget)
        
        # Create header with title and buttons
        header_layout = QHBoxLayout()
        history_label = QLabel("Chat History 📝")
        
        # Add email button
        email_btn = QPushButton("📧")
        email_btn.setFixedSize(20, 20)
        email_btn.setToolTip("Share history via email")
        email_btn.setProperty('class', 'email-btn')
        email_btn.clicked.connect(self.send_history_email)
        
        close_btn = QPushButton("×")
        close_btn.setFixedSize(20, 20)
        close_btn.setProperty('class', 'close-btn')
        close_btn.clicked.connect(self.toggle_history)
        
        header_layout.addWidget(history_label)
        header_layout.addStretch()
        header_layout.addWidget(email_btn)
        header_layout.addWidget(close_btn)
        
        self.history_list = QListWidget()
        
        history_layout.addLayout(header_layout)
        history_layout.addWidget(self.history_list)
        
        self.history_widget.hide()

    def send_history_email(self):
        try:
            self.chat_service.send_history_email(self.history)
            self.show_notification(
                "Email Client",
                "Opening email client with chat history...",
                3000
            )
        except EmailError as e:
            self.show_error("Email Error", e)
        except Exception as e:
            self.show_error("Unexpected Error", f"Failed to send history: {str(e)}")

    def toggle_history(self):
        if self.history_widget.isHidden():
            self.history_widget.show()
            self.layout().addWidget(self.history_widget)
        else:
            self.layout().removeWidget(self.history_widget)
            self.history_widget.hide()

    def setup_contact_panel(self):
        self.contact_widget = QWidget()
        contact_layout = QVBoxLayout(self.contact_widget)
        
        # Create header with title and close button
        header_layout = QHBoxLayout()
        contact_label = QLabel("Contact & About ℹ️")
        
        close_btn = QPushButton("×")
        close_btn.setFixedSize(20, 20)
        close_btn.setProperty('class', 'close-btn')
        
        header_layout.addWidget(contact_label)
        header_layout.addStretch()
        header_layout.addWidget(close_btn)
        
        # Contact info content
        content = QLabel(f"""
            <div style='text-align: center; padding: 20px;'>
                <h2 style='color: #90CAF9;'>Bank Operator Assistant</h2>
                <p>Version {self.APP_VERSION}</p>
                <p style='margin-top: 20px;'>
                    Having issues? Contact the GenAI team:
                    <br>genai-support@company.com
                </p>
                <p style='margin-top: 20px; color: #90CAF9;'>
                    © 2024 GenAI Team
                </p>
            </div>
        """)
        content.setAlignment(Qt.AlignTop)
        content.setProperty('class', 'contact-info')
        
        contact_layout.addLayout(header_layout)
        contact_layout.addWidget(content)
        
        self.contact_widget.hide()

    def toggle_contact(self):
        if self.contact_widget.isHidden():
            self.contact_widget.show()
            self.layout().addWidget(self.contact_widget)
        else:
            self.layout().removeWidget(self.contact_widget)
            self.contact_widget.hide()

    def setup_log_panel(self):
        self.log_widget = QWidget()
        self.log_widget.setMinimumSize(600, 500)
        self.log_widget.setProperty('class', 'log-widget')
        
        log_layout = QVBoxLayout(self.log_widget)
        
        # Create header with title and buttons
        header_layout = QHBoxLayout()
        log_label = QLabel("Operation Logs 📋")
        
        # Add email button
        email_btn = QPushButton("📧")
        email_btn.setFixedSize(20, 20)
        email_btn.setToolTip("Send logs via email")
        email_btn.setProperty('class', 'email-btn')
        
        close_btn = QPushButton("×")
        close_btn.setFixedSize(20, 20)
        close_btn.setProperty('class', 'close-btn')
        close_btn.clicked.connect(self.toggle_logs)  # Add this line to connect close button
        
        header_layout.addWidget(log_label)
        header_layout.addStretch()
        header_layout.addWidget(email_btn)
        header_layout.addWidget(close_btn)
        
        # Log content
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setMinimumSize(580, 400)  # Set text area size
        
        log_layout.addLayout(header_layout)
        log_layout.addWidget(self.log_display)
        
        self.log_widget.hide()

    def send_logs_email(self):
        try:
            log_content = self.log_display.toPlainText()
            self.chat_service.send_logs_email(log_content)
            self.show_notification(
                "Email Client",
                "Opening email client with logs...",
                3000
            )
        except Exception as e:
            self.show_error("Unexpected Error", f"Failed to send logs: {str(e)}")

    def toggle_logs(self):
        if self.log_widget.isHidden():
            self.load_logs()
            self.log_widget.show()
            self.layout().addWidget(self.log_widget)
        else:
            self.layout().removeWidget(self.log_widget)
            self.log_widget.hide()

    def load_logs(self):
        try:
            logs = self.chat_service.load_logs()
            self.log_display.setText(logs)
            self.log_display.verticalScrollBar().setValue(
                self.log_display.verticalScrollBar().maximum()
            )
        except LogError as e:
            self.show_error("Log Error", e)
            self.log_display.setText(f"Error loading logs: {str(e)}")
        except Exception as e:
            self.show_error("Unexpected Error", f"Failed to load logs: {str(e)}")
            self.log_display.setText(f"Unexpected error: {str(e)}")

    def send_message(self):
        message = self.input_field.text()
        if message.strip():
            timestamp = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
            logging.info(f"User Message: {message}")
            self.history.append({"message": message, "timestamp": timestamp})
            
            history_item = QListWidgetItem()
            history_item.setText(f"[{timestamp}] {message}")
            history_item.setToolTip(f"Sent at {timestamp}")
            self.history_list.addItem(history_item)
            
            self.chat_display.append(f"""
                <div style='background-color: #2D3135; padding: 10px; border-radius: 8px; margin: 5px 0;
                     border-left: 4px solid #2ecc71;'>
                    <table width="100%">
                        <tr>
                            <td width="40" valign="top"><span title="Logged in as: {self.username or 'Anonymous'}">{self.USER_ICON}</span></td>
                            <td><b style='color: #2ecc71;'>You ({timestamp}):</b><br>{message}</td>
                        </tr>
                    </table>
                </div>
            """)
            
            # After appending message, scroll to bottom
            self.chat_display.verticalScrollBar().setValue(
                self.chat_display.verticalScrollBar().maximum()
            )
            
            print('--> ', message)
            if message.startswith("/"):
                print('--> hm')
                self.handle_command(message)
                
            else:
                print('--> pm')
                self.process_message(message)
                
            self.input_field.clear()
        
    def handle_command(self, command):
        self.progress.show()
        self.show_loading()
        self.current_message = command
        self.show_notification("Processing Command", f"Executing command: {command}")
        
        # Simulate 2-second delay for commands
        self.timer.timeout.connect(self.handle_command_response)
        self.timer.start(2000)

    def handle_command_response(self):
        try:
            self.timer.stop()
            self.timer.timeout.disconnect(self.handle_command_response)
            self.timer.timeout.connect(self.handle_response)
            
            command = self.current_message
            timestamp = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
            
            response = self.chat_service.process_command(command)
            
            logging.info(f"Command Response: {response}")
            self.chat_display.append(f"""
                <div style='background-color: #1D4BA3; padding: 10px; border-radius: 8px; margin: 5px 0;
                     border-left: 4px solid #e74c3c;'>
                    <table width="100%">
                        <tr>
                            <td width="40" valign="top">{self.ASSISTANT_ICON}</td>
                            <td><b style='color: #e74c3c;'>System ({timestamp}):</b><br>{response}</td>
                        </tr>
                    </table>
                </div>
            """)
        except CommandError as e:
            self.show_error("Command Error", e)
        except Exception as e:
            self.show_error("Unexpected Error", f"An unexpected error occurred: {str(e)}")
        finally:
            self.hide_loading()
            self.progress.hide()

    def process_message(self, message):
        self.progress.show()
        self.show_loading()
        self.current_message = message
        self.show_notification("Processing Request", "Assistant is thinking... 🤔")
        
        # Simulate 2-second delay
        self.timer.start(2000)

    def handle_response(self):
        try:
            self.timer.stop()
            timestamp = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
            response = self.chat_service.process_message(self.current_message)
            
            logging.info(f"Assistant Response: {response}")
            self.chat_display.append(f"""
                <div style='background-color: #1D4BA3; padding: 10px; border-radius: 8px; margin: 5px 0;
                     border-left: 4px solid #3498db;'>
                    <table width="100%">
                        <tr>
                            <td width="40" valign="top">{self.ASSISTANT_ICON}</td>
                            <td><b style='color: #3498db;'>Assistant ({timestamp}):</b><br>{response}</td>
                        </tr>
                    </table>
                </div>
            """)
            
            preview = response[:50] + "..." if len(response) > 50 else response
            self.show_notification(
                "Assistant Response",
                f"💬 {preview}",
                5000
            )
        except ChatServiceError as e:
            self.show_error("Processing Error", e)
        except Exception as e:
            self.show_error("Unexpected Error", f"An unexpected error occurred: {str(e)}")
        finally:
            self.hide_loading()

    def show_loading(self):
        self.loading_overlay.show()
        self.input_field.setEnabled(False)

    def hide_loading(self):
        self.loading_overlay.hide()
        self.input_field.setEnabled(True)
        
    def show_contact_info(self):
        self.toggle_contact()
        self.show_notification("Contact Info", "Contact information panel opened")
        
    def show_settings(self):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2D3135;
                color: #E4E7EB;
                border: 1px solid #404346;
                border-radius: 6px;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #1D4BA3;
            }
        """)
        
        history_action = QAction("History 📝", self)
        history_action.triggered.connect(self.toggle_history)
        menu.addAction(history_action)
        
        menu.addSeparator()
        menu.addAction(QAction("Theme Settings 🎨", self))
        menu.addAction(QAction("Notification Settings 🔔", self))
        menu.addAction(QAction("Language Settings 🌐", self))
        menu.addAction(QAction("Security Settings 🔒", self))
        menu.addAction(QAction("API Configuration ⚙️", self))
        
        menu.addSeparator()
        contact_action = QAction("Contact & About ℹ️", self)
        contact_action.triggered.connect(self.show_contact_info)
        menu.addAction(contact_action)
        
        menu.exec_(self.sender().mapToGlobal(self.sender().rect().bottomRight()))

    def update_notification_badge(self, count=None):
        if count is not None:
            self.notification_count = count
        else:
            self.notification_count += 1
        
        self.notif_badge.setText(str(self.notification_count))
        self.notif_badge.setVisible(self.notification_count > 0)

    def on_input_changed(self, text):
        self.clear_btn.setVisible(bool(text))
        # Show completer only when typing commands
        if text.startswith('/'):
            self.command_completer.setCompletionPrefix(text)
            if self.command_completer.completionCount() > 0:
                self.command_completer.complete()

    def clear_input(self):
        self.input_field.clear()

    def change_persona(self, index):
        self.current_persona = self.PERSONAS[index]
        self.show_notification(
            "Persona Changed",
            f"Switched to {self.current_persona['name']} {self.current_persona['icon']}"
        )
