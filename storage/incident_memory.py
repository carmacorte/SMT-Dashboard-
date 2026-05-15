"""
storage/incident_memory.py
Historical incident storage with recurrence detection.
SQLite-based persistence for incident history and pattern matching.
"""

import sqlite3
import json
import hashlib
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path

from config.settings import settings
from config.logging_config import get_logger
from schemas.event_schema import CorrelatedIncident, ParsedManufacturingEvent


logger = get_logger("incidents")


class IncidentMemory:
    """
    Persistent storage for incident history and recurrence detection.

    Features:
    - Store complete incident records
    - Detect recurring patterns by component/station/line/model
    - Generate "similar past incidents" references
    - Fast lookup by various dimensions
    """

    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.DB_PATH
        self._init_db()

    def _init_db(self):
        """Initialize SQLite schema for incident memory."""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS incidents (
                    incident_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    status TEXT DEFAULT 'open',
                    primary_station TEXT,
                    primary_component TEXT,
                    primary_line TEXT,
                    primary_model TEXT,
                    primary_defect TEXT,
                    max_severity TEXT,
                    event_count INTEGER DEFAULT 0,
                    first_event_time TEXT,
                    last_event_time TEXT,
                    duration_minutes REAL,
                    is_recurring INTEGER DEFAULT 0,
                    recurrence_count INTEGER DEFAULT 0,
                    similar_incident_ids TEXT,  -- JSON array
                    affected_lines TEXT,        -- JSON array
                    affected_components TEXT,   -- JSON array
                    full_data TEXT NOT NULL     -- JSON serialized CorrelatedIncident
                );

                CREATE TABLE IF NOT EXISTS incident_patterns (
                    pattern_hash TEXT PRIMARY KEY,
                    incident_id TEXT NOT NULL,
                    component TEXT,
                    station TEXT,
                    line TEXT,
                    model TEXT,
                    defect TEXT,
                    first_seen TEXT NOT NULL,
                    last_seen TEXT NOT NULL,
                    occurrence_count INTEGER DEFAULT 1,
                    FOREIGN KEY (incident_id) REFERENCES incidents(incident_id)
                );

                CREATE INDEX IF NOT EXISTS idx_incidents_component 
                    ON incidents(primary_component);
                CREATE INDEX IF NOT EXISTS idx_incidents_station 
                    ON incidents(primary_station);
                CREATE INDEX IF NOT EXISTS idx_incidents_line 
                    ON incidents(primary_line);
                CREATE INDEX IF NOT EXISTS idx_incidents_model 
                    ON incidents(primary_model);
                CREATE INDEX IF NOT EXISTS idx_incidents_status 
                    ON incidents(status);
                CREATE INDEX IF NOT EXISTS idx_incidents_time 
                    ON incidents(created_at);
                CREATE INDEX IF NOT EXISTS idx_patterns_hash 
                    ON incident_patterns(pattern_hash);
                CREATE INDEX IF NOT EXISTS idx_patterns_component 
                    ON incident_patterns(component);
            """)
            conn.commit()
        logger.info("Incident memory database initialized")

    def _generate_pattern_hash(
        self,
        component: Optional[str],
        station: Optional[str],
        line: Optional[str],
        model: Optional[str],
        defect: Optional[str]
    ) -> str:
        """Generate hash for pattern matching."""
        key = f"{component or ''}|{station or ''}|{line or ''}|{model or ''}|{defect or ''}"
        return hashlib.sha256(key.encode()).hexdigest()[:16]

    def store_incident(self, incident: CorrelatedIncident) -> None:
        """Store or update an incident record."""
        now = datetime.now(timezone.utc).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            # Store main incident record
            conn.execute("""
                INSERT OR REPLACE INTO incidents (
                    incident_id, created_at, updated_at, status,
                    primary_station, primary_component, primary_line,
                    primary_model, primary_defect, max_severity,
                    event_count, first_event_time, last_event_time,
                    duration_minutes, is_recurring, recurrence_count,
                    similar_incident_ids, affected_lines, affected_components,
                    full_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                incident.incident_id,
                incident.created_at.isoformat(),
                now,
                incident.status,
                incident.primary_station.value if incident.primary_station else None,
                incident.primary_component,
                incident.primary_line,
                incident.primary_model,
                incident.primary_defect.value if incident.primary_defect else None,
                incident.max_severity.value,
                incident.event_count,
                incident.first_event_time.isoformat() if incident.first_event_time else None,
                incident.last_event_time.isoformat() if incident.last_event_time else None,
                incident.duration_minutes,
                1 if incident.is_recurring else 0,
                incident.recurrence_count,
                json.dumps(incident.similar_incident_ids),
                json.dumps(incident.affected_lines),
                json.dumps(incident.affected_components),
                incident.json()
            ))

            # Store/update pattern
            pattern_hash = self._generate_pattern_hash(
                incident.primary_component,
                incident.primary_station.value if incident.primary_station else None,
                incident.primary_line,
                incident.primary_model,
                incident.primary_defect.value if incident.primary_defect else None
            )

            # Check if pattern exists
            cursor = conn.execute(
                "SELECT occurrence_count, incident_id FROM incident_patterns WHERE pattern_hash = ?",
                (pattern_hash,)
            )
            row = cursor.fetchone()

            if row:
                # Update existing pattern
                conn.execute("""
                    UPDATE incident_patterns 
                    SET last_seen = ?, occurrence_count = occurrence_count + 1,
                        incident_id = ?
                    WHERE pattern_hash = ?
                """, (now, incident.incident_id, pattern_hash))
            else:
                # Insert new pattern
                conn.execute("""
                    INSERT INTO incident_patterns (
                        pattern_hash, incident_id, component, station, line, model, defect,
                        first_seen, last_seen, occurrence_count
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    pattern_hash,
                    incident.incident_id,
                    incident.primary_component,
                    incident.primary_station.value if incident.primary_station else None,
                    incident.primary_line,
                    incident.primary_model,
                    incident.primary_defect.value if incident.primary_defect else None,
                    now, now, 1
                ))

            conn.commit()

        logger.info(
            f"Incident stored: {incident.incident_id}",
            extra={
                "incident_id": incident.incident_id,
                "component": incident.primary_component,
                "station": incident.primary_station.value if incident.primary_station else None,
                "recurring": incident.is_recurring,
            }
        )

    def find_similar_incidents(
        self,
        component: Optional[str] = None,
        station: Optional[str] = None,
        line: Optional[str] = None,
        model: Optional[str] = None,
        defect: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find historically similar incidents.
        Returns list of similar incidents with similarity scores.
        """
        conditions = []
        params = []

        if component:
            conditions.append("primary_component = ?")
            params.append(component)
        if station:
            conditions.append("primary_station = ?")
            params.append(station)
        if line:
            conditions.append("primary_line = ?")
            params.append(line)
        if model:
            conditions.append("primary_model = ?")
            params.append(model)
        if defect:
            conditions.append("primary_defect = ?")
            params.append(defect)

        if not conditions:
            return []

        query = f"""
            SELECT incident_id, created_at, max_severity, status, event_count,
                   primary_component, primary_station, primary_line, primary_model,
                   duration_minutes, is_recurring, recurrence_count
            FROM incidents
            WHERE {" AND ".join(conditions)}
            AND status != 'closed'
            ORDER BY created_at DESC
            LIMIT ?
        """
        params.append(limit)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

        results = []
        for row in rows:
            results.append({
                "incident_id": row["incident_id"],
                "created_at": row["created_at"],
                "severity": row["max_severity"],
                "status": row["status"],
                "event_count": row["event_count"],
                "component": row["primary_component"],
                "station": row["primary_station"],
                "line": row["primary_line"],
                "model": row["primary_model"],
                "duration_minutes": row["duration_minutes"],
                "is_recurring": bool(row["is_recurring"]),
                "recurrence_count": row["recurrence_count"],
            })

        return results

    def get_incident(self, incident_id: str) -> Optional[CorrelatedIncident]:
        """Retrieve full incident by ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT full_data FROM incidents WHERE incident_id = ?",
                (incident_id,)
            )
            row = cursor.fetchone()
            if row:
                return CorrelatedIncident.parse_raw(row[0])
        return None

    def get_open_incidents(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get paginated list of open incidents."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT incident_id, created_at, updated_at, status,
                       primary_station, primary_component, primary_line,
                       primary_model, max_severity, event_count,
                       duration_minutes, is_recurring
                FROM incidents
                WHERE status = 'open'
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))
            rows = cursor.fetchall()

        return [dict(row) for row in rows]

    def update_incident_status(
        self,
        incident_id: str,
        status: str
    ) -> bool:
        """Update incident status."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "UPDATE incidents SET status = ?, updated_at = ? WHERE incident_id = ?",
                (status, datetime.now(timezone.utc).isoformat(), incident_id)
            )
            conn.commit()
            return cursor.rowcount > 0

    def get_recurrence_stats(
        self,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get recurrence statistics for reporting."""
        cutoff = (datetime.now(timezone.utc) - __import__('datetime').timedelta(days=days)).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Total incidents in period
            cursor = conn.execute(
                "SELECT COUNT(*) FROM incidents WHERE created_at > ?",
                (cutoff,)
            )
            total = cursor.fetchone()[0]

            # Recurring incidents
            cursor = conn.execute(
                "SELECT COUNT(*) FROM incidents WHERE created_at > ? AND is_recurring = 1",
                (cutoff,)
            )
            recurring = cursor.fetchone()[0]

            # Top recurring patterns
            cursor = conn.execute("""
                SELECT component, station, line, model, defect,
                       COUNT(*) as count, MAX(occurrence_count) as max_occurrences
                FROM incident_patterns
                WHERE last_seen > ?
                GROUP BY component, station, line, model, defect
                HAVING count > 1
                ORDER BY count DESC
                LIMIT 10
            """, (cutoff,))
            top_patterns = [dict(row) for row in cursor.fetchall()]

        return {
            "period_days": days,
            "total_incidents": total,
            "recurring_incidents": recurring,
            "recurrence_rate": recurring / total if total > 0 else 0.0,
            "top_patterns": top_patterns,
        }
