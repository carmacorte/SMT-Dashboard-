"""
export/smtinel_exporter.py
Export engine for SMTinel Dashboard integration.
Generates structured JSON packages and optional Supabase sync.
"""

import json
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
from pathlib import Path

from config.settings import settings
from config.logging_config import get_logger
from schemas.event_schema import (
    CorrelatedIncident, SentinelAlert, IncidentTimeline, ExportPackage
)


logger = get_logger("export")


class SMTinelExporter:
    """
    Exports manufacturing intelligence to SMTinel Dashboard.

    Output formats:
    - JSON file export (local-first)
    - Supabase sync (optional cloud)
    - Webhook push (for real-time integration)
    """

    def __init__(self, export_dir: str = None):
        self.export_dir = Path(export_dir or settings.EXPORT_DIR)
        self.export_dir.mkdir(parents=True, exist_ok=True)
        self._stats = {
            "exports_generated": 0,
            "incidents_exported": 0,
            "alerts_exported": 0,
        }
        logger.info(f"SMTinelExporter initialized: {self.export_dir}")

    def create_package(
        self,
        incidents: List[CorrelatedIncident],
        timelines: List[IncidentTimeline],
        alerts: List[SentinelAlert],
        time_range_start: Optional[datetime] = None,
        time_range_end: Optional[datetime] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> ExportPackage:
        """Create a complete export package."""
        return ExportPackage(
            package_id=f"PKG-{uuid.uuid4().hex[:12].upper()}",
            generated_at=datetime.now(timezone.utc),
            incidents=incidents,
            timelines=timelines,
            alerts=alerts,
            event_count=sum(len(inc.event_ids) for inc in incidents),
            incident_count=len(incidents),
            alert_count=len(alerts),
            time_range_start=time_range_start,
            time_range_end=time_range_end,
            filters=filters or {}
        )

    def export_json(
        self,
        package: ExportPackage,
        filename: Optional[str] = None
    ) -> Path:
        """
        Export package as JSON file.

        Returns:
            Path to exported file
        """
        if filename is None:
            timestamp = package.generated_at.strftime("%Y%m%d_%H%M%S")
            filename = f"traceops_export_{timestamp}_{package.package_id}.json"

        filepath = self.export_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(package.dict(), f, indent=2, default=str, ensure_ascii=False)

        self._stats["exports_generated"] += 1
        self._stats["incidents_exported"] += package.incident_count
        self._stats["alerts_exported"] += package.alert_count

        logger.info(
            f"Exported package to {filepath}",
            extra={
                "package_id": package.package_id,
                "filepath": str(filepath),
                "incidents": package.incident_count,
                "alerts": package.alert_count,
            }
        )

        return filepath

    def export_incident_summary(
        self,
        incidents: List[CorrelatedIncident],
        filename: Optional[str] = None
    ) -> Path:
        """
        Export condensed incident summary for dashboard display.

        Returns:
            Path to exported file
        """
        if filename is None:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            filename = f"incident_summary_{timestamp}.json"

        filepath = self.export_dir / filename

        summary = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_incidents": len(incidents),
            "by_severity": {},
            "by_station": {},
            "by_defect": {},
            "by_line": {},
            "by_status": {},
            "recurring_count": 0,
            "incidents": []
        }

        for inc in incidents:
            # Count by severity
            sev = inc.max_severity.value
            summary["by_severity"][sev] = summary["by_severity"].get(sev, 0) + 1

            # Count by station
            if inc.primary_station:
                st = inc.primary_station.value
                summary["by_station"][st] = summary["by_station"].get(st, 0) + 1

            # Count by defect
            if inc.primary_defect:
                d = inc.primary_defect.value
                summary["by_defect"][d] = summary["by_defect"].get(d, 0) + 1

            # Count by line
            if inc.primary_line:
                summary["by_line"][inc.primary_line] = summary["by_line"].get(inc.primary_line, 0) + 1

            # Count by status
            summary["by_status"][inc.status] = summary["by_status"].get(inc.status, 0) + 1

            # Recurring
            if inc.is_recurring:
                summary["recurring_count"] += 1

            # Add condensed incident
            summary["incidents"].append({
                "id": inc.incident_id,
                "severity": inc.max_severity.value,
                "station": inc.primary_station.value if inc.primary_station else None,
                "component": inc.primary_component,
                "defect": inc.primary_defect.value if inc.primary_defect else None,
                "line": inc.primary_line,
                "model": inc.primary_model,
                "status": inc.status,
                "events": inc.event_count,
                "duration_min": inc.duration_minutes,
                "recurring": inc.is_recurring,
                "created_at": inc.created_at.isoformat() if inc.created_at else None,
            })

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, default=str, ensure_ascii=False)

        logger.info(f"Exported incident summary to {filepath}")
        return filepath

    def export_alert_feed(
        self,
        alerts: List[SentinelAlert],
        filename: Optional[str] = None
    ) -> Path:
        """
        Export alert feed for real-time dashboard display.

        Returns:
            Path to exported file
        """
        if filename is None:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            filename = f"alert_feed_{timestamp}.json"

        filepath = self.export_dir / filename

        feed = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_alerts": len(alerts),
            "alerts": []
        }

        for alert in alerts:
            feed["alerts"].append({
                "id": alert.alert_id,
                "incident_id": alert.incident_id,
                "severity": alert.severity.value,
                "type": alert.alert_type,
                "title": alert.title,
                "description": alert.description,
                "recommendation": alert.recommendation,
                "station": alert.affected_station.value if alert.affected_station else None,
                "line": alert.affected_line,
                "component": alert.affected_component,
                "model": alert.affected_model,
                "escalation_score": alert.escalation_score,
                "recurrence_score": alert.recurrence_score,
                "operational_impact": alert.operational_impact,
                "generated_at": alert.generated_at.isoformat() if alert.generated_at else None,
                "target_groups": alert.target_groups,
            })

        # Sort by severity and time
        feed["alerts"].sort(
            key=lambda x: (
                {"critical": 4, "high": 3, "medium": 2, "low": 1}.get(x["severity"], 0),
                x["generated_at"] or ""
            ),
            reverse=True
        )

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(feed, f, indent=2, default=str, ensure_ascii=False)

        logger.info(f"Exported alert feed to {filepath}")
        return filepath

    def get_stats(self) -> Dict[str, Any]:
        """Return export statistics."""
        return dict(self._stats)


# Supabase sync (optional)
class SupabaseSync:
    """
    Optional Supabase synchronization for cloud persistence.
    Only active if ENABLE_SUPABASE_SYNC is True.
    """

    def __init__(self):
        self.enabled = settings.ENABLE_SUPABASE_SYNC
        self.url = settings.SUPABASE_URL
        self.key = settings.SUPABASE_KEY
        self._client = None

        if self.enabled:
            try:
                from supabase import create_client
                self._client = create_client(self.url, self.key)
                logger.info("Supabase client initialized")
            except ImportError:
                logger.warning("supabase package not installed, sync disabled")
                self.enabled = False
            except Exception as e:
                logger.error(f"Supabase init failed: {e}")
                self.enabled = False

    async def sync_incidents(self, incidents: List[CorrelatedIncident]) -> bool:
        """Sync incidents to Supabase."""
        if not self.enabled or not self._client:
            return False

        try:
            data = [inc.dict() for inc in incidents]
            response = self._client.table("incidents").upsert(data).execute()
            logger.info(f"Synced {len(incidents)} incidents to Supabase")
            return True
        except Exception as e:
            logger.error(f"Supabase sync failed: {e}")
            return False

    async def sync_alerts(self, alerts: List[SentinelAlert]) -> bool:
        """Sync alerts to Supabase."""
        if not self.enabled or not self._client:
            return False

        try:
            data = [alert.dict() for alert in alerts]
            response = self._client.table("alerts").upsert(data).execute()
            logger.info(f"Synced {len(alerts)} alerts to Supabase")
            return True
        except Exception as e:
            logger.error(f"Supabase sync failed: {e}")
            return False
