"""
config/settings.py
Centralized configuration for TraceOps Live.
All environment-specific variables loaded here.
"""

import os
from pathlib import Path
from typing import Optional


# Base paths
BASE_DIR = Path(__file__).parent.parent
LOGS_DIR = BASE_DIR / "logs"
DATA_DIR = BASE_DIR / "data"

# Ensure directories exist
LOGS_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)


class Settings:
    """
    Application settings with sensible defaults for local-first operation.
    Override via environment variables for production deployment.
    """

    # --- Database ---
    DB_PATH: str = os.getenv(
        "TRACEOPS_DB_PATH", 
        str(DATA_DIR / "traceops_live.db")
    )

    # WhatsApp bridge database (read-only reference)
    WHATSAPP_DB_PATH: str = os.getenv(
        "WHATSAPP_DB_PATH",
        str(Path("../whatsapp-bridge/store/messages.db").resolve())
    )

    # --- API ---
    API_HOST: str = os.getenv("TRACEOPS_API_HOST", "127.0.0.1")
    API_PORT: int = int(os.getenv("TRACEOPS_API_PORT", "8081"))
    API_WORKERS: int = int(os.getenv("TRACEOPS_API_WORKERS", "1"))

    # --- Polling ---
    POLLING_INTERVAL: float = float(os.getenv("TRACEOPS_POLL_INTERVAL", "5.0"))
    """Seconds between WhatsApp DB polling cycles."""

    POLLING_BACKOFF_MAX: float = float(os.getenv("TRACEOPS_BACKOFF_MAX", "60.0"))
    """Max backoff seconds when errors occur."""

    # --- Processing ---
    BATCH_SIZE: int = int(os.getenv("TRACEOPS_BATCH_SIZE", "50"))
    """Messages processed per polling cycle."""

    MAX_MESSAGE_AGE_HOURS: int = int(os.getenv("TRACEOPS_MAX_AGE", "72"))
    """Ignore messages older than this many hours."""

    # --- Correlation ---
    CORRELATION_WINDOW_MINUTES: int = int(os.getenv("TRACEOPS_CORR_WINDOW", "30"))
    """Time window for event clustering."""

    CORRELATION_MIN_EVENTS: int = int(os.getenv("TRACEOPS_CORR_MIN", "2"))
    """Minimum events to form an incident."""

    # --- Sentinel ---
    AUTO_ALERT_THRESHOLD: str = os.getenv("TRACEOPS_ALERT_THRESHOLD", "high")
    """Minimum severity to auto-generate alerts."""

    # --- Features ---
    ENABLE_SUPABASE_SYNC: bool = os.getenv("TRACEOPS_SUPABASE", "false").lower() == "true"
    ENABLE_MEDIA_PROCESSING: bool = os.getenv("TRACEOPS_MEDIA", "true").lower() == "true"
    ENABLE_AUTO_ALERTS: bool = os.getenv("TRACEOPS_AUTO_ALERTS", "false").lower() == "true"

    # --- Supabase (optional) ---
    SUPABASE_URL: Optional[str] = os.getenv("TRACEOPS_SUPABASE_URL")
    SUPABASE_KEY: Optional[str] = os.getenv("TRACEOPS_SUPABASE_KEY")

    # --- Media ---
    MEDIA_DIR: str = os.getenv("TRACEOPS_MEDIA_DIR", str(DATA_DIR / "media"))

    # --- Export ---
    EXPORT_DIR: str = os.getenv("TRACEOPS_EXPORT_DIR", str(DATA_DIR / "exports"))

    @classmethod
    def validate(cls) -> list[str]:
        """Validate configuration and return list of issues."""
        issues = []

        # Check WhatsApp DB exists
        if not Path(cls.WHATSAPP_DB_PATH).exists():
            issues.append(f"WhatsApp DB not found: {cls.WHATSAPP_DB_PATH}")

        # Check media directory
        Path(cls.MEDIA_DIR).mkdir(parents=True, exist_ok=True)
        Path(cls.EXPORT_DIR).mkdir(parents=True, exist_ok=True)

        return issues

    @classmethod
    def to_dict(cls) -> dict:
        """Export settings as dictionary (for logging/debugging)."""
        return {
            k: v for k, v in cls.__dict__.items() 
            if not k.startswith("_") and not callable(v)
        }


# Singleton instance
settings = Settings()
