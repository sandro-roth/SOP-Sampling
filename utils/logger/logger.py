import logging
import os
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler

class _ServiceFilter(logging.Filter):
    def __init__(self, service: str):
        super().__init__()
        self.service = service

    def filter(self, record: logging.LogRecord) -> bool:
        record.service = self.service
        return True