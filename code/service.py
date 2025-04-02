import logging
from datetime import datetime
import webbrowser
from urllib.parse import quote

class ChatServiceError(Exception):
    """Base exception for chat service errors"""
    def __init__(self, message):
        super().__init__(message)
        logging.error(f"ChatServiceError: {message}")

class CommandError(ChatServiceError):
    """Raised when command processing fails"""
    def __init__(self, message):
        super().__init__(f"Command Error: {message}")
        logging.error(f"CommandError: {message}")

class EmailError(ChatServiceError):
    """Raised when email operations fail"""
    def __init__(self, message):
        super().__init__(f"Email Error: {message}")
        logging.error(f"EmailError: {message}")

class LogError(ChatServiceError):
    """Raised when log operations fail"""
    def __init__(self, message):
        super().__init__(f"Log Error: {message}")
        logging.error(f"LogError: {message}")

class LoginError(ChatServiceError):
    """Raised when login operations fail"""
    def __init__(self, message):
        super().__init__(f"Login Error: {message}")
        logging.error(f"LoginError: {message}")

class ChatService:
    def __init__(self):
        self.command_list = ["/fix", "/help", "/search", "/text", "/image", "/video"]
        self.support_email = "ganesh.gowtham@gmail.com"
        self.logged_in_user = None

    def login_user(self, username):
        """Validate and log in a user"""
        try:
            if not username or len(username.strip()) == 0:
                raise LoginError("Username cannot be empty")
            if len(username) < 3:
                raise LoginError("Username must be at least 3 characters")
                
            self.logged_in_user = username
            logging.info(f"User logged in successfully: {username}")
            return username
            
        except LoginError as e:
            logging.error(f"Login failed for user {username}: {str(e)}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error during login: {str(e)}")
            raise LoginError(f"Login failed: {str(e)}")

    def logout_user(self):
        """Log out current user"""
        try:
            if self.logged_in_user:
                logging.info(f"User logged out: {self.logged_in_user}")
            self.logged_in_user = None
        except Exception as e:
            logging.error(f"Error during logout: {str(e)}")
            raise LoginError(f"Logout failed: {str(e)}")

    def process_command(self, command):
        try:
            if command.startswith("/fix"):
                return "🔧 Fix process completed successfully!"
            elif command.startswith("/help"):
                return "ℹ️ Available commands:\n" + "\n".join(self.command_list)
            elif command.startswith("/search"):
                return "🔍 Search results found!"
            elif command.startswith("/text"):
                return "📝 Text processing complete!"
            elif command.startswith("/image"):
                return "🖼️ Image processing finished!"
            elif command.startswith("/video"):
                
                return "🎥 Video processing done!"
            return "Unknown command"
        except Exception as e:
            logging.error(f"Command processing error: {str(e)}")
            raise CommandError(f"Failed to process command: {str(e)}")

    def process_message(self, message):
        try:
            # Here you can add more complex message processing logic
            return "This is a sample response from the assistant."
        except Exception as e:
            logging.error(f"Message processing error: {str(e)}")
            raise ChatServiceError(f"Failed to process message: {str(e)}")

    def log_message(self, message, message_type="User"):
        timestamp = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
        logging.info(f"{message_type} Message: {message}")
        return timestamp

    def send_history_email(self, history):
        try:
            if not history:
                raise ValueError("No history to send")
            history_text = "\n".join([f"{item['timestamp']}: {item['message']}" for item in history])
            subject = "Chat History"
            body = f"Chat History Export\n\nDate: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n{history_text}"
            
            return self._send_email(subject, body)
        except Exception as e:
            logging.error(f"Email error: {str(e)}")
            raise EmailError(f"Failed to send history email: {str(e)}")

    def send_logs_email(self, log_content):
        try:
            if not log_content:
                raise ValueError("No log content to send")
            subject = "Issue"
            return self._send_email(subject, log_content)
        except Exception as e:
            logging.error(f"Email error: {str(e)}")
            raise EmailError(f"Failed to send logs email: {str(e)}")

    def _send_email(self, subject, body):
        mailto_url = f"mailto:{self.support_email}?subject={quote(subject)}&body={quote(body)}"
        webbrowser.open(mailto_url)
        return True

    def load_logs(self, filename='operator.log'):
        try:
            if not filename:
                raise ValueError("No log file specified")
            with open(filename, 'r') as f:
                return f.read()
        except FileNotFoundError:
            raise LogError("Log file not found")
        except PermissionError:
            raise LogError("Permission denied accessing log file")
        except Exception as e:
            logging.error(f"Log error: {str(e)}")
            raise LogError(f"Failed to load logs: {str(e)}")
