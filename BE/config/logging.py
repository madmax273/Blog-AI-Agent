import logging
import os
from datetime import datetime, timedelta
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path


class Logger:
    def __init__(self, name: str = "app", log_level: str = "INFO", log_dir: str = "logs", backup_count: int = 10):
        """
        Initialize logger with daily rotation and backup
        
        Args:
            name: Logger name
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_dir: Directory to store log files
            backup_count: Number of backup files to keep (default: 10 days)
        """
        self.name = name
        self.log_dir = Path(log_dir)
        self.backup_count = backup_count
        
        # Create logs directory if it doesn't exist
        self.log_dir.mkdir(exist_ok=True)
        
        # Setup logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # Avoid duplicate handlers
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup console and file handlers"""
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        
        # File handler with daily rotation at midnight
        log_file = self.log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.log"
        file_handler = TimedRotatingFileHandler(
            filename=log_file,
            when='midnight',
            interval=1,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        
        # Add handlers to logger
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
    
    def info(self, message: str):
        """Log info message"""
        self.logger.info(message)
    
    def error(self, message: str):
        """Log error message"""
        self.logger.error(message)
    
    def warning(self, message: str):
        """Log warning message"""
        self.logger.warning(message)
    
    def debug(self, message: str):
        """Log debug message"""
        self.logger.debug(message)
    
    def critical(self, message: str):
        """Log critical message"""
        self.logger.critical(message)
    
    def log_error_with_context(self, error: Exception, context: str = ""):
        """Log error with context and exception details"""
        if context:
            self.error(f"{context}: {str(error)}")
        else:
            self.error(str(error))
        self.debug(f"Exception details: {type(error).__name__}: {error}")


def configure_app_logging(log_level: str = "INFO", log_dir: str = "logs"):
    """
    Configure application-wide logging settings
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory to store log files
    """
    # Set root logging level
    logging.getLogger().setLevel(getattr(logging, log_level.upper()))
    
    # Create logs directory if it doesn't exist
    Path(log_dir).mkdir(exist_ok=True)


# Example usage and singleton instance
def get_logger(name: str = "app", log_level: str = "INFO", log_dir: str = "logs") -> Logger:
    """Get logger instance"""
    return Logger(name, log_level, log_dir)


# Default logger instance
logger = get_logger()