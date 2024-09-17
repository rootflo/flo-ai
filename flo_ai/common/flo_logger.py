import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional


class FloLogger:
    _instances = {}

    def __new__(cls, name: str, level: str = "INFO", use_file: bool = True, file_path: str = "flo.log", max_bytes: int = 1048576):
        """
        Custom new method to check for existing instance.
        """
        if name not in cls._instances:
            instance = super().__new__(cls)  
            cls._instances[name] = instance
        return cls._instances[name]

    def __init__(self, name: str, level: str = "INFO", use_file: bool = True, file_path: str = "flo.log", max_bytes: int = 1048576):

        self.logger = logging.getLogger(name)
        if not self.logger.handlers:
            self.set_level(level)
            self._setup_handler(use_file, file_path, max_bytes)

    def _setup_handler(self, use_file: bool, file_path: str, max_bytes: int):
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

        if use_file:
            log_file_path = os.path.join(os.path.dirname(__file__), file_path)
            file_handler = RotatingFileHandler(
                log_file_path, 
                maxBytes=max_bytes, 
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def set_level(self, level):
        if isinstance(level, str):
            level = getattr(logging, level.upper(), logging.INFO)
        self.logger.setLevel(level)

    def debug(self, message: str):
        self.logger.debug(message)

    def info(self, message: str):
        self.logger.info(message)

    def warning(self, message: str):
        self.logger.warning(message)

    def error(self, message: str):
        self.logger.error(message)

    def critical(self, message: str):
        self.logger.critical(message)


def get_logger(name: str, level: Optional[str] = 'INFO', use_file: bool = True, file_path: str = "flo.log") -> FloLogger:
    """
    Creates a FloLogger instance with optional file logging and caching.

    Args:
        name: The name of the logger.
        level: The logging level (default: INFO).
        use_file: Whether to log to a file (default: False).
        file_path: The path to the log file (default: "flo.log").
        max_bytes: The maximum size of the log file before it gets rotated (default: 1MB).

    Returns:
        A FloLogger instance.
    """
     
    logger = FloLogger(name, level, use_file, file_path)
    return logger