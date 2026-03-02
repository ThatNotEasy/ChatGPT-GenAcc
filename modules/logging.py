"""
Logging module for ChatGPT Account Creator
"""
from datetime import datetime


class Logger:
    """Handles logging with timestamps and labels"""

    def __init__(self):
        self.current_progress = None

    def set_progress(self, progress):
        """Set the current progress label for logging"""
        self.current_progress = progress

    def clear_progress(self):
        """Clear the progress label"""
        self.current_progress = None

    def log(self, message, level=None):
        """Log a message with timestamp and label"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        label = self.current_progress if self.current_progress else (level if level else "INFO")
        log_message = f"[{timestamp}] [{label}] {message}"
        print(log_message)
        return log_message

    def info(self, message):
        """Log an info message"""
        return self.log(message, "INFO")

    def warning(self, message):
        """Log a warning message"""
        return self.log(message, "WARNING")

    def error(self, message):
        """Log an error message"""
        return self.log(message, "ERROR")
