"""
Middleware de Logger para Artificiall Ops Manager.

Implementa logging estruturado em JSON para rastreabilidade de operações.
"""

import logging
import json
import os
from datetime import datetime
from typing import Any, Dict, Optional
import uuid

logger = logging.getLogger(__name__)


class OperationLogger:
    """
    Structured operation logger for audit trail.
    
    Logs all operations in JSON format for easy parsing and analysis.
    """

    def __init__(
        self,
        log_dir: str = "logs",
        log_level: str = "INFO",
    ):
        """
        Initialize Operation Logger.

        Args:
            log_dir: Directory to store log files
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.log_dir = log_dir
        self.log_level = getattr(logging, log_level.upper(), logging.INFO)

        # Ensure log directory exists
        os.makedirs(log_dir, exist_ok=True)

        # Setup operations log
        self._setup_logger(
            name="operations",
            filename=os.path.join(log_dir, "operations.log"),
        )

        # Setup errors log
        self._setup_logger(
            name="errors",
            filename=os.path.join(log_dir, "errors.log"),
            level=logging.ERROR,
        )

        logger.info(f"Operation logger initialized (level={log_level})")

    def _setup_logger(
        self,
        name: str,
        filename: str,
        level: Optional[int] = None,
    ) -> logging.Logger:
        """
        Setup file logger with JSON formatting.

        Args:
            name: Logger name
            filename: Log file path
            level: Logging level (optional, defaults to self.log_level)
        """
        log_logger = logging.getLogger(name)
        log_logger.setLevel(level or self.log_level)

        # Remove existing handlers to avoid duplicates
        log_logger.handlers = []

        # Create file handler
        file_handler = logging.FileHandler(filename, encoding="utf-8")
        file_handler.setLevel(level or self.log_level)

        # Create JSON formatter
        formatter = logging.Formatter("%(message)s")
        file_handler.setFormatter(formatter)

        log_logger.addHandler(file_handler)
        return log_logger

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO 8601 format with timezone."""
        from datetime import timezone, timedelta

        # Fixed offset for America/Sao_Paulo (BRT = UTC-3)
        # Using timedelta instead of strptime for better Windows compatibility
        # Note: Does not handle DST, but acceptable for logging purposes
        tz = timezone(timedelta(hours=-3))
        return datetime.now(tz).isoformat()

    def _create_log_entry(
        self,
        level: str,
        command: str,
        telegram_id: str,
        user_name: str,
        action: str,
        details: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create structured log entry.

        Args:
            level: Log level (INFO, WARNING, ERROR, CRITICAL)
            command: Command name
            telegram_id: Telegram user ID
            user_name: User name
            action: Action performed
            details: Additional details dictionary
            trace_id: Unique trace identifier

        Returns:
            Dictionary with log entry data
        """
        safe_telegram_id = telegram_id
        if level == "ERROR" and telegram_id:
            safe_telegram_id = f"***{telegram_id[-4:]}" if len(telegram_id) > 4 else "***"

        return {
            "timestamp": self._get_timestamp(),
            "level": level,
            "command": command,
            "telegram_id": safe_telegram_id,
            "user_name": user_name,
            "action": action,
            "details": details or {},
            "trace_id": trace_id or str(uuid.uuid4()),
        }

    def log_operation(
        self,
        command: str,
        telegram_id: str,
        user_name: str,
        action: str,
        details: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
    ) -> None:
        """
        Log successful operation.

        Args:
            command: Command name
            telegram_id: Telegram user ID
            user_name: User name
            action: Action performed
            details: Additional details
            trace_id: Trace identifier
        """
        entry = self._create_log_entry(
            level="INFO",
            command=command,
            telegram_id=telegram_id,
            user_name=user_name,
            action=action,
            details=details,
            trace_id=trace_id,
        )
        logging.getLogger("operations").info(json.dumps(entry, ensure_ascii=False))

    def log_error(
        self,
        command: str,
        telegram_id: str,
        user_name: str,
        error: str,
        details: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
    ) -> None:
        """
        Log error operation.

        Args:
            command: Command name
            telegram_id: Telegram user ID
            user_name: User name
            error: Error message
            details: Additional details
            trace_id: Trace identifier
        """
        entry = self._create_log_entry(
            level="ERROR",
            command=command,
            telegram_id=telegram_id,
            user_name=user_name,
            action="error",
            details={**(details or {}), "error": error},
            trace_id=trace_id,
        )
        logging.getLogger("errors").error(json.dumps(entry, ensure_ascii=False))
        logging.getLogger("operations").warning(json.dumps(entry, ensure_ascii=False))

    def log_warning(
        self,
        command: str,
        telegram_id: str,
        user_name: str,
        warning: str,
        details: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
    ) -> None:
        """
        Log warning operation.

        Args:
            command: Command name
            telegram_id: Telegram user ID
            user_name: User name
            warning: Warning message
            details: Additional details
            trace_id: Trace identifier
        """
        entry = self._create_log_entry(
            level="WARNING",
            command=command,
            telegram_id=telegram_id,
            user_name=user_name,
            action="warning",
            details={**(details or {}), "warning": warning},
            trace_id=trace_id,
        )
        logging.getLogger("operations").warning(json.dumps(entry, ensure_ascii=False))

    def log_critical(
        self,
        command: str,
        telegram_id: str,
        user_name: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
    ) -> None:
        """
        Log critical operation (e.g., executive decisions).

        Args:
            command: Command name
            telegram_id: Telegram user ID
            user_name: User name
            message: Critical message
            details: Additional details
            trace_id: Trace identifier
        """
        entry = self._create_log_entry(
            level="CRITICAL",
            command=command,
            telegram_id=telegram_id,
            user_name=user_name,
            action="critical",
            details={**(details or {}), "message": message},
            trace_id=trace_id,
        )
        logging.getLogger("operations").critical(json.dumps(entry, ensure_ascii=False))

    @classmethod
    def from_env(cls) -> "OperationLogger":
        """
        Create OperationLogger instance from environment variables.

        Expects:
            - AIOX_LOG_LEVEL: Logging level (default: INFO)

        Returns:
            OperationLogger instance
        """
        log_level = os.getenv("AIOX_LOG_LEVEL", "INFO")
        return cls(log_level=log_level)
