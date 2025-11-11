import logging
import os
from pathlib import Path
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

def setup_logging(app_name: str = 'app', log_dir: str | None = None, retention: int = 30, level: int = logging.INFO,
        to_stdout: bool = True) -> logging.Logger:
    """
    Configure and initialize the application-wide logging system.

    This function sets up a rotating file logger and, optionally, console output.
    Log files are stored in a directory structure organized by service name, and
    old logs are automatically rotated daily and deleted after the retention period.

    Steps performed:
        1. Creates a log directory for the given app (default: ./logs/<app_name>).
        2. Configures the root logger with the specified log level.
        3. Adds a timed rotating file handler that rolls over at midnight.
        4. Optionally adds a StreamHandler to print logs to stdout.
        5. Applies the custom _ServiceFilter to include the service name in each log record.

    Args:
        app_name (str): Name of the application or service (used in log directory and record filter).
        log_dir (str | None): Base directory for log files. Defaults to current working directory/logs.
        retention (int): Number of daily log files to retain before old ones are deleted.
        level (int): Logging level (e.g. logging.INFO, logging.DEBUG).
        to_stdout (bool): If True, logs are also printed to the console.

    Returns:
        logging.Logger: The configured root logger instance.
    """
    base_log_dir = Path(log_dir or os.getenv('LOG_DIR', Path(__file__).resolve().parents[3] / 'logs'))
    service_log_dir = base_log_dir / app_name
    service_log_dir.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(level)

    # Make sure Handlers are not duplicated
    for h in list(root.handlers):
        root.removeHandler(h)

    log_path = service_log_dir / 'service.log'
    file_handler = TimedRotatingFileHandler(
        filename=str(log_path),
        when='midnight',
        interval=1,
        backupCount=retention,
        encoding='utf-8',
        utc=False,
        delay=True
    )
    file_handler.suffix = '%Y-%m-%d'

    # Formatter with service and name
    file_fmt = logging.Formatter('%(asctime)s [%(levelname)s] [%(service)s] %(name)s: %(message)s')
    file_handler.setFormatter(file_fmt)
    file_handler.addFilter(_ServiceFilter(app_name))
    root.addHandler(file_handler)

    if to_stdout:
        console = logging.StreamHandler()
        console.setFormatter(file_fmt)
        console.addFilter(_ServiceFilter(app_name))
        root.addHandler(console)

    root.info(f'[{app_name}] Logging initialized at {service_log_dir}')
    return root

def get_logger(app_name: str | None = None) -> logging.Logger:
    """
    Retrieve a logger by name, inheriting the configuration from the root logger.

    This is a convenience function to obtain a logger instance anywhere in the code
    after `setup_logging()` has initialized the logging system.

    Args:
        app_name (str | None): Optional name for the logger. If None, returns the root logger.

    Returns:
        logging.Logger: The requested logger instance.
    """
    return logging.getLogger(app_name)