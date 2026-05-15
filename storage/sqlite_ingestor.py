"""
storage/sqlite_ingestor.py
WhatsApp SQLite database reader with incremental polling.
Detects new messages, avoids duplicates, exports normalized objects.
"""

import sqlite3
import asyncio
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any, Callable
from pathlib import Path
import logging

from config.settings import settings
from config.logging_config import get_ingest_logger
from schemas.event_schema import RawWhatsAppMessage


logger = get_ingest_logger()


class SQLiteIngestor:
    """
    Incremental SQLite reader for WhatsApp messages.db.

    Features:
    - Polling-based incremental detection
    - Duplicate prevention via message ID tracking
    - Reconnection handling with exponential backoff
    - Structured logging of all operations
    - Batch processing for efficiency
    """

    def __init__(
        self,
        db_path: str = None,
        poll_interval: float = None,
        batch_size: int = None,
        max_age_hours: int = None,
        on_new_messages: Optional[Callable[[List[RawWhatsAppMessage]], None]] = None
    ):
        self.db_path = db_path or settings.WHATSAPP_DB_PATH
        self.poll_interval = poll_interval or settings.POLLING_INTERVAL
        self.batch_size = batch_size or settings.BATCH_SIZE
        self.max_age_hours = max_age_hours or settings.MAX_MESSAGE_AGE_HOURS
        self.on_new_messages = on_new_messages

        # State tracking
        self._last_processed_id: Optional[str] = None
        self._last_processed_time: Optional[datetime] = None
        self._seen_ids: set = set()
        self._running = False
        self._poll_task: Optional[asyncio.Task] = None

        # Connection management
        self._connection: Optional[sqlite3.Connection] = None
        self._connection_retries = 0
        self._max_retries = 5

        # Statistics
        self._stats = {
            "total_processed": 0,
            "total_batches": 0,
            "errors": 0,
            "last_poll_time": None,
            "last_poll_count": 0,
        }

        logger.info(
            "SQLiteIngestor initialized",
            extra={
                "db_path": self.db_path,
                "poll_interval": self.poll_interval,
                "batch_size": self.batch_size,
            }
        )

    def _connect(self) -> sqlite3.Connection:
        """Establish database connection with timeout and row factory."""
        try:
            conn = sqlite3.connect(
                self.db_path,
                timeout=10.0,
                check_same_thread=False  # For async compatibility
            )
            conn.row_factory = sqlite3.Row
            self._connection_retries = 0
            return conn
        except sqlite3.Error as e:
            self._connection_retries += 1
            logger.error(
                f"DB connection failed (attempt {self._connection_retries}/{self._max_retries}): {e}",
                exc_info=True
            )
            raise

    def _ensure_connection(self) -> sqlite3.Connection:
        """Ensure active connection, reconnect if needed."""
        if self._connection is None:
            self._connection = self._connect()
        try:
            # Test connection with simple query
            self._connection.execute("SELECT 1")
        except sqlite3.Error:
            logger.warning("Connection lost, reconnecting...")
            self._connection = self._connect()
        return self._connection

    def _build_query(self) -> tuple[str, tuple]:
        """Build parameterized query for new messages."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=self.max_age_hours)
        cutoff_iso = cutoff_time.isoformat()

        base_query = """
            SELECT 
                m.id,
                m.timestamp,
                m.sender,
                c.name as chat_name,
                m.content,
                m.is_from_me,
                m.chat_jid,
                m.media_type,
                m.reply_to
            FROM messages m
            JOIN chats c ON m.chat_jid = c.jid
            WHERE m.timestamp > ?
            AND m.content IS NOT NULL
            AND LENGTH(TRIM(m.content)) > 0
        """

        params = [cutoff_iso]

        # If we have a last processed time, use it for incremental loading
        if self._last_processed_time:
            # Replace the time condition
            base_query = base_query.replace("m.timestamp > ?", "m.timestamp > ?")
            params = [self._last_processed_time.isoformat()]

        # Exclude already seen IDs if we have them
        if self._seen_ids:
            placeholders = ",".join("?" * len(self._seen_ids))
            base_query += f" AND m.id NOT IN ({placeholders})"
            params.extend(self._seen_ids)

        # Order by timestamp ascending for chronological processing
        base_query += " ORDER BY m.timestamp ASC LIMIT ?"
        params.append(self.batch_size)

        return base_query, tuple(params)

    def _row_to_message(self, row: sqlite3.Row) -> RawWhatsAppMessage:
        """Convert database row to RawWhatsAppMessage."""
        # Parse timestamp
        ts_str = row["timestamp"]
        try:
            timestamp = datetime.fromisoformat(ts_str)
        except (ValueError, TypeError):
            timestamp = datetime.now(timezone.utc)

        return RawWhatsAppMessage(
            id=row["id"],
            timestamp=timestamp,
            sender=row["sender"] or "unknown",
            sender_name=None,  # Will be resolved later if needed
            chat_jid=row["chat_jid"] or "unknown",
            chat_name=row["chat_name"],
            content=row["content"] or "",
            is_from_me=bool(row["is_from_me"]),
            media_type=row["media_type"],
            reply_to_id=row["reply_to"]
        )

    def poll_once(self) -> List[RawWhatsAppMessage]:
        """
        Single polling cycle. Returns list of new messages.

        Returns:
            List of RawWhatsAppMessage objects
        """
        messages: List[RawWhatsAppMessage] = []

        try:
            conn = self._ensure_connection()
            query, params = self._build_query()

            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

            for row in rows:
                msg = self._row_to_message(row)

                # Skip if already seen (double-check)
                if msg.id in self._seen_ids:
                    continue

                self._seen_ids.add(msg.id)
                messages.append(msg)

                # Update tracking
                self._last_processed_id = msg.id
                if self._last_processed_time is None or msg.timestamp > self._last_processed_time:
                    self._last_processed_time = msg.timestamp

            self._stats["total_processed"] += len(messages)
            self._stats["total_batches"] += 1
            self._stats["last_poll_time"] = datetime.now(timezone.utc).isoformat()
            self._stats["last_poll_count"] = len(messages)

            if messages:
                logger.info(
                    f"Poll cycle: {len(messages)} new messages",
                    extra={
                        "poll_count": len(messages),
                        "last_id": self._last_processed_id,
                    }
                )

            return messages

        except sqlite3.Error as e:
            self._stats["errors"] += 1
            logger.error(f"Database error during poll: {e}", exc_info=True)
            # Reset connection to force reconnect
            self._connection = None
            return []
        except Exception as e:
            self._stats["errors"] += 1
            logger.error(f"Unexpected error during poll: {e}", exc_info=True)
            return []

    async def poll_loop(self):
        """
        Main polling loop. Runs until stopped.
        Implements exponential backoff on errors.
        """
        self._running = True
        backoff = 1.0

        logger.info("Starting polling loop")

        while self._running:
            try:
                messages = await asyncio.get_event_loop().run_in_executor(
                    None, self.poll_once
                )

                if messages and self.on_new_messages:
                    try:
                        self.on_new_messages(messages)
                    except Exception as e:
                        logger.error(f"Message handler error: {e}", exc_info=True)

                # Reset backoff on success
                if messages:
                    backoff = 1.0

                # Wait before next poll
                await asyncio.sleep(self.poll_interval * backoff)

            except asyncio.CancelledError:
                logger.info("Polling loop cancelled")
                break
            except Exception as e:
                self._stats["errors"] += 1
                logger.error(f"Polling loop error: {e}", exc_info=True)

                # Exponential backoff
                backoff = min(backoff * 2, settings.POLLING_BACKOFF_MAX / self.poll_interval)
                logger.warning(f"Backing off: next poll in {self.poll_interval * backoff:.1f}s")
                await asyncio.sleep(self.poll_interval * backoff)

        logger.info("Polling loop stopped")

    def start(self):
        """Start polling in background."""
        if self._poll_task is None or self._poll_task.done():
            self._poll_task = asyncio.create_task(self.poll_loop())
            logger.info("Polling task started")

    def stop(self):
        """Stop polling loop."""
        self._running = False
        if self._poll_task and not self._poll_task.done():
            self._poll_task.cancel()
        logger.info("Polling stop requested")

    def get_stats(self) -> Dict[str, Any]:
        """Return current ingestion statistics."""
        return {
            **self._stats,
            "seen_ids_count": len(self._seen_ids),
            "last_processed_id": self._last_processed_id,
            "last_processed_time": self._last_processed_time.isoformat() if self._last_processed_time else None,
            "is_running": self._running,
        }

    def reset_cursor(self):
        """Reset polling cursor (useful for reprocessing)."""
        self._last_processed_id = None
        self._last_processed_time = None
        self._seen_ids.clear()
        logger.info("Polling cursor reset")
