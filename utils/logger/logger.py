import logging
import os
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler

class _ServiceFilter(logging.Filter):
    """
    A custom logging filter that injects a 'service' attribute into log records.

    This allows log messages to include the service name (e.g. "flask-ui" or "backend"),
    making it easier to identify the source of log entries when multiple services
    write to the same log file.
    """
    def __init__(self, service: str):
        super().__init__()
        self.service = service

    def filter(self, record: logging.LogRecord) -> bool:
        record.service = self.service
        return True