"""
Configuration module for Planted application.

Contains logging configuration and other application settings.
"""

from .logging_config import setup_logging, get_logger

__all__ = ['setup_logging', 'get_logger']
