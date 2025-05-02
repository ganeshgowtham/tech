import sys
import os
import getpass
from PyQt5.QtWidgets import QApplication
from login_window import LoginWindow
from service import ChatService
import logging

def get_windows_username():
    """Get current Windows username"""
    try:
        return getpass.getuser()
    except:
        return os.environ.get('USERNAME', 'Unknown User')

def display_health_check():
    """Display system health check messages"""
    chat_service = ChatService()
    health_result = chat_service.get_system_health()
    windows_user = get_windows_username()
    
    print("\nSystem Health Check:")
    print("===================")
    print(f"Hi {windows_user}, I am checking health check of various systems...")
    print("===================")
    for check in health_result["checks"]:
        status_icon = "✅" if check["status"] else "❌"
        print(f"{status_icon} {check['message']}")
    print(f"\nStatus: {health_result['message']}")
    print("===================\n")

def main():
    app = QApplication(sys.argv)
    
    # Configure logging
    logging.basicConfig(
        filename='operator.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Display health check messages
    display_health_check()
    
    # Initialize and show login window
    login = LoginWindow()
    login.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
