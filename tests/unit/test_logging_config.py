"""
Unit tests for logging configuration.

Tests the logging setup, request ID tracking, and log file creation.
"""

import os
import tempfile
import logging
import shutil
from pathlib import Path
import pytest

from garden_manager.config.logging_config import (
    setup_logging,
    get_logger,
    set_request_id,
    get_request_id,
    clear_request_id,
    RequestIdFilter
)


class TestLoggingSetup:
    """Tests for logging system initialization."""

    def test_setup_logging_creates_log_directory(self):
        """Test that setup_logging creates the log directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / 'logs'
            setup_logging(
                app_name='test_app',
                log_dir=str(log_dir),
                enable_console=False,
                enable_file=True
            )

            assert log_dir.exists()
            assert log_dir.is_dir()

    def test_setup_logging_creates_log_files(self):
        """Test that setup_logging creates the expected log files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / 'logs'
            setup_logging(
                app_name='test_app',
                log_dir=str(log_dir),
                enable_console=False,
                enable_file=True
            )

            # Log files should be created after first log message
            logger = get_logger(__name__)
            logger.info('Test message')
            logger.error('Test error')

            assert (log_dir / 'test_app.log').exists()
            assert (log_dir / 'test_app_error.log').exists()
            assert (log_dir / 'test_app_access.log').exists()

    def test_setup_logging_development_mode(self):
        """Test that development mode sets DEBUG level."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ['FLASK_ENV'] = 'development'
            try:
                setup_logging(
                    app_name='test_app',
                    log_dir=tmpdir,
                    enable_console=False,
                    enable_file=True
                )

                root_logger = logging.getLogger()
                assert root_logger.level == logging.DEBUG
            finally:
                os.environ.pop('FLASK_ENV', None)

    def test_setup_logging_production_mode(self):
        """Test that production mode sets INFO level."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ['FLASK_ENV'] = 'production'
            try:
                setup_logging(
                    app_name='test_app',
                    log_dir=tmpdir,
                    enable_console=False,
                    enable_file=True
                )

                root_logger = logging.getLogger()
                assert root_logger.level == logging.INFO
            finally:
                os.environ.pop('FLASK_ENV', None)

    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a logger instance."""
        logger = get_logger('test_module')
        assert isinstance(logger, logging.Logger)
        assert logger.name == 'test_module'


class TestRequestIdTracking:
    """Tests for request ID tracking functionality."""

    def test_set_request_id_generates_id(self):
        """Test that set_request_id generates a request ID."""
        request_id = set_request_id()
        assert request_id is not None
        assert len(request_id) > 0

    def test_set_request_id_with_custom_id(self):
        """Test that set_request_id accepts custom ID."""
        custom_id = 'custom-request-id-123'
        request_id = set_request_id(custom_id)
        assert request_id == custom_id

    def test_get_request_id_returns_set_id(self):
        """Test that get_request_id returns the set request ID."""
        custom_id = 'test-request-id'
        set_request_id(custom_id)
        assert get_request_id() == custom_id

    def test_clear_request_id_removes_id(self):
        """Test that clear_request_id removes the request ID."""
        set_request_id('test-id')
        clear_request_id()
        assert get_request_id() is None

    def test_request_id_filter_adds_id_to_record(self):
        """Test that RequestIdFilter adds request_id to log records."""
        set_request_id('test-request-123')

        # Create a log record
        logger = logging.getLogger('test')
        record = logger.makeRecord(
            'test', logging.INFO, '', 1, 'Test message',
            None, None
        )

        # Apply filter
        filter_instance = RequestIdFilter()
        filter_instance.filter(record)

        assert hasattr(record, 'request_id')
        assert record.request_id == 'test-request-123'

        clear_request_id()

    def test_request_id_filter_handles_no_id(self):
        """Test that RequestIdFilter handles missing request ID."""
        clear_request_id()

        # Create a log record
        logger = logging.getLogger('test')
        record = logger.makeRecord(
            'test', logging.INFO, '', 1, 'Test message',
            None, None
        )

        # Apply filter
        filter_instance = RequestIdFilter()
        filter_instance.filter(record)

        assert hasattr(record, 'request_id')
        assert record.request_id == 'N/A'


class TestLogLevels:
    """Tests for different log levels."""

    def test_error_logs_written_to_error_file(self):
        """Test that ERROR logs are written to error log file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / 'logs'
            setup_logging(
                app_name='test_app',
                log_dir=str(log_dir),
                enable_console=False,
                enable_file=True
            )

            logger = get_logger('test_error')
            logger.error('This is an error message')

            error_log = log_dir / 'test_app_error.log'
            assert error_log.exists()

            content = error_log.read_text()
            assert 'This is an error message' in content
            assert 'ERROR' in content

    def test_info_logs_not_in_error_file(self):
        """Test that INFO logs are not written to error log file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / 'logs'
            setup_logging(
                app_name='test_app',
                log_dir=str(log_dir),
                enable_console=False,
                enable_file=True
            )

            logger = get_logger('test_info')
            logger.info('This is an info message')

            error_log = log_dir / 'test_app_error.log'
            # Error log should be empty or not contain the info message
            if error_log.exists():
                content = error_log.read_text()
                assert 'This is an info message' not in content


class TestLogRotation:
    """Tests for log file rotation."""

    def test_log_rotation_configuration(self):
        """Test that log rotation is configured correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / 'logs'
            setup_logging(
                app_name='test_app',
                log_dir=str(log_dir),
                enable_console=False,
                enable_file=True
            )

            # Check that handlers are RotatingFileHandler
            root_logger = logging.getLogger()
            rotating_handlers = [
                h for h in root_logger.handlers
                if isinstance(h, logging.handlers.RotatingFileHandler)
            ]

            # Should have 3 rotating file handlers (app, error, access)
            assert len(rotating_handlers) == 3

            # Check max bytes and backup count
            for handler in rotating_handlers:
                assert handler.maxBytes == 10 * 1024 * 1024  # 10MB
                assert handler.backupCount == 5


class TestLogFormatting:
    """Tests for log message formatting."""

    def test_log_format_includes_timestamp(self):
        """Test that log messages include timestamp."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / 'logs'
            setup_logging(
                app_name='test_app',
                log_dir=str(log_dir),
                enable_console=False,
                enable_file=True
            )

            logger = get_logger('test_format')
            logger.info('Test message with timestamp')

            log_file = log_dir / 'test_app.log'
            content = log_file.read_text()

            # Check for timestamp format YYYY-MM-DD HH:MM:SS
            import re
            timestamp_pattern = r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}'
            assert re.search(timestamp_pattern, content)

    def test_log_format_includes_module_name(self):
        """Test that log messages include module name."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / 'logs'
            setup_logging(
                app_name='test_app',
                log_dir=str(log_dir),
                enable_console=False,
                enable_file=True
            )

            logger = get_logger('test_module')
            logger.info('Test message with module')

            log_file = log_dir / 'test_app.log'
            content = log_file.read_text()

            assert 'test_module' in content

    def test_log_format_includes_log_level(self):
        """Test that log messages include log level."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / 'logs'
            setup_logging(
                app_name='test_app',
                log_dir=str(log_dir),
                enable_console=False,
                enable_file=True
            )

            logger = get_logger('test_level')
            logger.info('Info message')
            logger.warning('Warning message')
            logger.error('Error message')

            log_file = log_dir / 'test_app.log'
            content = log_file.read_text()

            assert 'INFO' in content
            assert 'WARNING' in content
            assert 'ERROR' in content


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
