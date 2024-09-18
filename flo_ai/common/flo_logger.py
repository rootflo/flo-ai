import os
import logging
from logging.handlers import RotatingFileHandler
from typing import Dict, Optional

class FloLoggerUtil(logging.Logger):
    def __init__(self, name: str, level: str = "INFO", use_file: bool = False, file_path: str = None, max_bytes: int = 1048576):
        super().__init__(name, level)
        self.setLevel(level)

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.addHandler(console_handler)

        if use_file:
            file_handler = RotatingFileHandler(file_path or f"{name}.log", maxBytes=max_bytes)
            file_handler.setFormatter(formatter)
            self.addHandler(file_handler)

class FloLogger:
    _loggers = {}

    @classmethod
    def get_logger(cls, name: str, level: str = None, use_file: bool = False, file_path: str = None, max_bytes: int = 1048576) -> FloLoggerUtil:
        if name not in cls._loggers:
            level = level or os.environ.get(f"FLO_LOG_LEVEL_{name.upper()}", "INFO")
            cls._loggers[name] = FloLoggerUtil(name, level, use_file, file_path, max_bytes)
        return cls._loggers[name]

    @classmethod
    def set_log_level(cls, name: str, level: str):
        if name in cls._loggers:
            cls._loggers[name].setLevel(level)

def get_logger(name: str, level: str = None, use_file: bool = False, file_path: str = None, max_bytes: int = 1048576) -> FloLoggerUtil:
    return FloLogger.get_logger(name, level, use_file, file_path, max_bytes)

common_logger = get_logger("COMMON")
builder_logger = get_logger("BUILDER")
session_logger = get_logger("SESSION")

def set_global_log_level(level: str):
    for name in ["COMMON", "BUILDER", "SESSION"]:
        FloLogger.set_log_level(name, level)