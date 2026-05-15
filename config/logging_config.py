"""
config/logging_config.py
Structured logging configuration for TraceOps Live.
Rotating logs with separate files per subsystem.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from datetime import datetime
import json

from config.settings import LOGS_DIR


class JSONFormatter(logging.Formatter):
    """JSON structured log formatter for machine parsing."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra fields if present
        if hasattr(record, "event_id"):
            log_obj["event_id"] = record.event_id
        if hasattr(record, "incident_id"):
            log_obj["incident_id"] = record.incident_id
        if hasattr(record, "component"):
            log_obj["component"] = record.component
        if hasattr(record, "station"):
            log_obj["station"] = record.station
        if hasattr(record, "line"):
            log_obj["line"] = record.line
        if hasattr(record, "severity"):
            log_obj["severity"] = record.severity
        if hasattr(record, "duration_ms"):
            log_obj["duration_ms"] = record.duration_ms

        # Add exception info
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_obj, ensure_ascii=False)


def setup_logging(
    level: int = logging.INFO,
    use_json: bool = False,
    console: bool = True
) -> logging.Logger:
    """
    Configure logging with rotating file handlers per subsystem.

    Args:
        level: Minimum log level
        use_json: Use JSON formatter instead of plain text
        console: Also output to console

    Returns:
        Root logger instance
    """

    # Ensure logs directory exists
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    # Root logger
    root_logger = logging.getLogger("traceops")
    root_logger.setLevel(level)
    root_logger.handlers = []  # Clear existing

    # Formatter
    if use_json:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # File handlers with rotation
    log_configs = [
        ("traceops", "traceops.log", level),           # Main application
        ("traceops.ingest", "ingest.log", level),      # Ingestion pipeline
        ("traceops.parser", "parser.log", level),      # NLP parser
        ("traceops.correlation", "correlation.log", level),  # Incident clustering
        ("traceops.sentinel", "sentinel.log", level),  # Severity scoring
        ("traceops.api", "api.log", level),            # FastAPI requests
        ("traceops.export", "export.log", level),      # SMTinel export
        ("traceops.incidents", "incidents.log", level), # Incident memory
    ]

    for logger_name, filename, log_level in log_configs:
        logger = logging.getLogger(logger_name)
        logger.setLevel(log_level)

        # Rotating file handler: 10MB per file, keep 5 backups
        file_handler = logging.handlers.RotatingFileHandler(
            filename=LOGS_DIR / filename,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8"
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Incident log - special structured format for audit trail
    incident_handler = logging.handlers.RotatingFileHandler(
        filename=LOGS_DIR / "incident_audit.log",
        maxBytes=50 * 1024 * 1024,  # 50MB
        backupCount=10,
        encoding="utf-8"
    )
    incident_handler.setLevel(logging.INFO)
    incident_formatter = JSONFormatter() if use_json else logging.Formatter(
        fmt="%(asctime)s | INCIDENT | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    incident_handler.setFormatter(incident_formatter)
    logging.getLogger("traceops.incidents").addHandler(incident_handler)

    return root_logger


# Convenience loggers
def get_logger(name: str) -> logging.Logger:
    """Get a namespaced logger."""
    return logging.getLogger(f"traceops.{name}")


def get_ingest_logger() -> logging.Logger:
    return logging.getLogger("traceops.ingest")


def get_parser_logger() -> logging.Logger:
    return logging.getLogger("traceops.parser")


def get_correlation_logger() -> logging.Logger:
    return logging.getLogger("traceops.correlation")


def get_sentinel_logger() -> logging.Logger:
    return logging.getLogger("traceops.sentinel")


def get_api_logger() -> logging.Logger:
    return logging.getLogger("traceops.api")
