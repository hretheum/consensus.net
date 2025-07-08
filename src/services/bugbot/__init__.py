"""
BugBot - Automatyczny system monitorowania i zarządzania błędami
"""

from .bugbot import BugBot
from .monitor import ErrorMonitor
from .analyzer import ErrorAnalyzer
from .notifier import NotificationManager

__all__ = ['BugBot', 'ErrorMonitor', 'ErrorAnalyzer', 'NotificationManager']