"""Simple logging utility."""
import logging
import sys
from datetime import datetime
from pathlib import Path


class Logger:
    """Simple application logger."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance
    
    def _init(self):
        self.logs = []
        self.listeners = []
    
    def add_listener(self, callback):
        """Add a callback that receives new log messages."""
        self.listeners.append(callback)
    
    def remove_listener(self, callback):
        """Remove a log listener."""
        if callback in self.listeners:
            self.listeners.remove(callback)
    
    def _notify(self, msg):
        for cb in self.listeners:
            try:
                cb(msg)
            except Exception:
                pass
    
    def log(self, level, msg):
        """Log a message."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        full = f"[{timestamp}] {level}: {msg}"
        self.logs.append(full)
        self._notify(full)
        print(full, file=sys.stderr)
    
    def info(self, msg):
        self.log("INFO", msg)
    
    def warning(self, msg):
        self.log("WARN", msg)
    
    def error(self, msg):
        self.log("ERROR", msg)
    
    def debug(self, msg):
        self.log("DEBUG", msg)
    
    def get_logs(self):
        return self.logs[:]


logger = Logger()
