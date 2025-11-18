"""
Logging configuration module for Planted application.

Provides structured logging with:
- Environment-based log levels (DEBUG for development, INFO for production)
- Multiple log files (application, errors, access logs)
- File rotation (10MB max size, 5 backup files)
- Request ID tracking for distributed tracing
- Proper formatting with timestamps, module names, and log levels
"""

import logging
import logging.handlers
import os
import sys
import uuid
from pathlib import Path
from typing import Optional
from contextvars import ContextVar

# Context variable for request ID tracking
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)


class RequestIdFilter(logging.Filter):
    """
    Logging filter that adds request ID to log records for distributed tracing.

    Uses context variables to track request IDs across async operations.
    """

    def filter(self, record):
        """Add request_id to the log record."""
        record.request_id = request_id_var.get() or 'N/A'
        return True


class ColoredFormatter(logging.Formatter):
    """
    Colored console formatter for better readability in development.

    Uses ANSI color codes to highlight different log levels.
    """

    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'

    def format(self, record):
        """Format log record with colors for console output."""
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname_colored = f"{log_color}{record.levelname}{self.RESET}"

        # Format the message using the parent class
        formatted = super().format(record)
        return formatted


def setup_logging(
    app_name: str = 'planted',
    log_dir: Optional[str] = None,
    log_level: Optional[str] = None,
    enable_console: bool = True,
    enable_file: bool = True
) -> logging.Logger:
    """
    Set up comprehensive logging for the application.

    Args:
        app_name: Name of the application (used for logger name)
        log_dir: Directory to store log files (defaults to 'logs' in project root)
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
                  If None, uses DEBUG for development, INFO for production
        enable_console: Whether to enable console logging
        enable_file: Whether to enable file logging

    Returns:
        logging.Logger: Configured root logger

    Example:
        >>> logger = setup_logging('planted')
        >>> logger.info('Application started')
    """
    # Determine log level from environment or parameter
    if log_level is None:
        env = os.environ.get('FLASK_ENV', 'production').lower()
        log_level = 'DEBUG' if env == 'development' else 'INFO'

    log_level_value = getattr(logging, log_level.upper(), logging.INFO)

    # Set up log directory
    if log_dir is None:
        # Default to 'logs' directory in project root
        project_root = Path(__file__).parent.parent.parent
        log_dir = project_root / 'logs'
    else:
        log_dir = Path(log_dir)

    # Create log directory if it doesn't exist
    log_dir.mkdir(exist_ok=True)

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level_value)

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Define log formats
    detailed_format = (
        '%(asctime)s - %(name)s - %(levelname)s - '
        '[%(filename)s:%(lineno)d] - [RequestID: %(request_id)s] - '
        '%(message)s'
    )

    simple_format = '%(asctime)s - %(levelname)s - %(message)s'

    console_format = (
        '%(asctime)s - %(name)s - %(levelname_colored)s - '
        '[%(filename)s:%(lineno)d] - %(message)s'
    )

    # Date format
    date_format = '%Y-%m-%d %H:%M:%S'

    # Console Handler (with colors for better development experience)
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level_value)

        console_formatter = ColoredFormatter(
            console_format,
            datefmt=date_format
        )
        console_handler.setFormatter(console_formatter)
        console_handler.addFilter(RequestIdFilter())
        root_logger.addHandler(console_handler)

    if enable_file:
        # Application Log Handler (all logs)
        app_log_file = log_dir / f'{app_name}.log'
        app_handler = logging.handlers.RotatingFileHandler(
            app_log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        app_handler.setLevel(log_level_value)
        app_formatter = logging.Formatter(detailed_format, datefmt=date_format)
        app_handler.setFormatter(app_formatter)
        app_handler.addFilter(RequestIdFilter())
        root_logger.addHandler(app_handler)

        # Error Log Handler (ERROR and CRITICAL only)
        error_log_file = log_dir / f'{app_name}_error.log'
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_formatter = logging.Formatter(detailed_format, datefmt=date_format)
        error_handler.setFormatter(error_formatter)
        error_handler.addFilter(RequestIdFilter())
        root_logger.addHandler(error_handler)

        # Access Log Handler (INFO level, for HTTP requests)
        access_log_file = log_dir / f'{app_name}_access.log'
        access_handler = logging.handlers.RotatingFileHandler(
            access_log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        access_handler.setLevel(logging.INFO)
        access_formatter = logging.Formatter(simple_format, datefmt=date_format)
        access_handler.setFormatter(access_formatter)
        # Access log doesn't need request ID filter (will be in message)
        root_logger.addHandler(access_handler)

    # Log the logging setup
    logger = logging.getLogger(__name__)
    logger.info('Logging system initialized')
    logger.info('Log level: %s', log_level)
    logger.info('Log directory: %s', log_dir)
    logger.debug('Debug logging is enabled')

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.

    Args:
        name: Name of the module (typically __name__)

    Returns:
        logging.Logger: Logger instance for the module

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info('Module loaded')
    """
    return logging.getLogger(name)


def set_request_id(request_id: Optional[str] = None) -> str:
    """
    Set the request ID for the current context.

    Args:
        request_id: Request ID to set. If None, generates a new UUID.

    Returns:
        str: The request ID that was set

    Example:
        >>> request_id = set_request_id()
        >>> logger.info('Processing request')  # Will include request_id
    """
    if request_id is None:
        request_id = str(uuid.uuid4())
    request_id_var.set(request_id)
    return request_id


def get_request_id() -> Optional[str]:
    """
    Get the current request ID from context.

    Returns:
        Optional[str]: Current request ID or None if not set
    """
    return request_id_var.get()


def clear_request_id():
    """
    Clear the request ID from current context.

    Useful for cleaning up after request processing.
    """
    request_id_var.set(None)


def log_function_call(func):
    """
    Decorator to log function calls with arguments and return values.

    Useful for debugging and tracing execution flow.

    Args:
        func: Function to decorate

    Returns:
        Wrapped function with logging

    Example:
        >>> @log_function_call
        >>> def my_function(x, y):
        >>>     return x + y
    """
    import functools

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        logger.debug('Calling %s with args=%s, kwargs=%s', func.__name__, args, kwargs)
        try:
            result = func(*args, **kwargs)
            logger.debug('%s returned %s', func.__name__, result)
            return result
        except Exception as e:
            logger.error('%s raised %s: %s', func.__name__, type(e).__name__, e, exc_info=True)
            raise

    return wrapper


# Production log aggregation instructions
PRODUCTION_LOGGING_GUIDE = """
Production Logging Integration Guide
=====================================

This application uses Python's logging module with structured logging and request ID tracking.
Logs are written to files with automatic rotation (10MB max, 5 backups).

Log Files:
----------
- planted.log: All application logs (DEBUG/INFO level in dev, INFO+ in prod)
- planted_error.log: Only ERROR and CRITICAL logs
- planted_access.log: HTTP access logs

Integration with Cloud Services:
--------------------------------

1. AWS CloudWatch:
   - Install: pip install watchtower
   - Configure CloudWatch handler in logging_config.py
   - Set environment variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION

   Example:
   import watchtower
   cloudwatch_handler = watchtower.CloudWatchLogHandler(
       log_group='planted',
       stream_name='application'
   )
   logger.addHandler(cloudwatch_handler)

2. Datadog:
   - Install: pip install datadog
   - Configure Datadog handler in logging_config.py
   - Set environment variable: DD_API_KEY

   Example:
   from datadog import initialize, statsd
   initialize(api_key='your_api_key', app_key='your_app_key')

3. Splunk:
   - Install: pip install splunk-handler
   - Configure Splunk HEC handler in logging_config.py
   - Set environment variables: SPLUNK_HOST, SPLUNK_TOKEN

   Example:
   from splunk_handler import SplunkHandler
   splunk = SplunkHandler(
       host='splunk.example.com',
       token='your_token',
       index='planted'
   )
   logger.addHandler(splunk)

4. ELK Stack (Elasticsearch, Logstash, Kibana):
   - Install: pip install python-logstash
   - Configure Logstash handler in logging_config.py

   Example:
   import logstash
   elk_handler = logstash.TCPLogstashHandler(
       'logstash.example.com', 5959, version=1
   )
   logger.addHandler(elk_handler)

5. Sentry (Error Tracking):
   - Install: pip install sentry-sdk
   - Initialize Sentry in app.py

   Example:
   import sentry_sdk
   sentry_sdk.init(
       dsn="your_sentry_dsn",
       traces_sample_rate=1.0
   )

Environment Variables:
---------------------
- FLASK_ENV: 'development' or 'production' (affects log level)
- LOG_LEVEL: Override log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- LOG_DIR: Override log directory path

Request ID Tracking:
-------------------
All logs include a request ID for distributed tracing.
Request IDs are automatically generated for each HTTP request.
Use get_request_id() to retrieve the current request ID.

Best Practices:
--------------
1. Use appropriate log levels:
   - DEBUG: Detailed information for diagnosing problems
   - INFO: General information about application flow
   - WARNING: Something unexpected but not an error
   - ERROR: Error that caused operation to fail
   - CRITICAL: Serious error that may cause application to crash

2. Include context in log messages:
   - Good: logger.info('User %s logged in from %s', user_id, ip_address)
   - Bad: logger.info('Login successful')

3. Use structured logging:
   - Include request IDs in all logs
   - Use extra parameters for additional context
   - Example: logger.info('Payment processed', extra={'amount': 100, 'currency': 'USD'})

4. Avoid logging sensitive information:
   - Never log passwords, API keys, or tokens
   - Mask sensitive data (e.g., credit card numbers, SSNs)

5. Monitor log file sizes:
   - Configure appropriate rotation settings
   - Set up alerts for disk space usage
   - Archive old logs periodically
"""
