"""
pipeline_orchestrator.py
Central pipeline controller for TraceOps Live.
Coordinates all modules: ingest → parse → correlate → score → export.
"""

import asyncio
import signal
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from pathlib import Path

from config.settings import settings
from config.logging_config import setup_logging, get_logger
from schemas.event_schema import (
    RawWhatsAppMessage, ParsedManufacturingEvent,
    CorrelatedIncident, SentinelAlert, IncidentTimeline
)
from storage.sqlite_ingestor import SQLiteIngestor
from storage.incident_memory import IncidentMemory
from parser.manufacturing_parser import ManufacturingParser
from correlation.incident_cluster import IncidentClusterer
from correlation.timeline_builder import TimelineBuilder
from sentinel.severity_engine import SeverityEngine
from export.smtinel_exporter import SMTinelExporter, SupabaseSync


logger = get_logger("pipeline")


class TraceOpsPipeline:
    """
    Central orchestrator for the complete TraceOps Live pipeline.

    Pipeline flow:
    1. INGEST: Poll WhatsApp SQLite DB → RawWhatsAppMessage[]
    2. PARSE: NLP extraction → ParsedManufacturingEvent[]
    3. CORRELATE: Event clustering → CorrelatedIncident[]
    4. TIMELINE: Chronological reconstruction → IncidentTimeline[]
    5. SCORE: Severity & impact calculation → SentinelAlert[]
    6. EXPORT: JSON generation + optional Supabase sync

    All steps are local, no cloud AI required.
    """

    def __init__(self):
        # Initialize all modules
        self.ingestor = SQLiteIngestor(on_new_messages=self._on_new_messages)
        self.incident_memory = IncidentMemory()
        self.parser = ManufacturingParser()
        self.clusterer = IncidentClusterer()
        self.timeline_builder = TimelineBuilder()
        self.severity_engine = SeverityEngine(self.incident_memory)
        self.exporter = SMTinelExporter()
        self.supabase = SupabaseSync()

        # State tracking
        self._running = False
        self._shutdown_event = asyncio.Event()

        # Metrics
        self._metrics = {
            "messages_ingested": 0,
            "events_parsed": 0,
            "incidents_clustered": 0,
            "timelines_built": 0,
            "alerts_generated": 0,
            "exports_created": 0,
            "pipeline_start_time": None,
        }

        # Active collections
        self._active_incidents: Dict[str, CorrelatedIncident] = {}
        self._active_alerts: Dict[str, SentinelAlert] = {}
        self._active_timelines: Dict[str, IncidentTimeline] = {}

        logger.info("TraceOpsPipeline initialized")

    def _on_new_messages(self, messages: List[RawWhatsAppMessage]):
        """Callback triggered by ingestor when new messages arrive."""
        logger.info(f"Pipeline received {len(messages)} new messages")
        self._metrics["messages_ingested"] += len(messages)

        # Step 2: PARSE
        events = self._parse(messages)
        if not events:
            return

        # Step 3: CORRELATE
        incidents = self._correlate(events)

        # Step 4: TIMELINE
        timelines = self._build_timelines(incidents, events)

        # Step 5: SCORE
        alerts = self._score(incidents)

        # Step 6: EXPORT
        self._export(incidents, timelines, alerts)

    def _parse(self, messages: List[RawWhatsAppMessage]) -> List[ParsedManufacturingEvent]:
        """Step 2: Parse messages into manufacturing events."""
        events = self.parser.parse_batch(messages)
        self._metrics["events_parsed"] += len(events)

        logger.info(
            f"PARSE: {len(events)}/{len(messages)} messages → events",
            extra={"events": len(events), "messages": len(messages)}
        )
        return events

    def _correlate(
        self,
        events: List[ParsedManufacturingEvent]
    ) -> List[CorrelatedIncident]:
        """Step 3: Cluster events into incidents."""
        incidents, _ = self.clusterer.process_events(events)

        for inc in incidents:
            self._active_incidents[inc.incident_id] = inc
            self.incident_memory.store_incident(inc)

        self._metrics["incidents_clustered"] += len(incidents)

        logger.info(
            f"CORRELATE: {len(events)} events → {len(incidents)} incidents",
            extra={"incidents": len(incidents), "events": len(events)}
        )
        return incidents

    def _build_timelines(
        self,
        incidents: List[CorrelatedIncident],
        all_events: List[ParsedManufacturingEvent]
    ) -> List[IncidentTimeline]:
        """Step 4: Build timelines for incidents."""
        timelines = []

        for inc in incidents:
            inc_events = [e for e in all_events if e.event_id in inc.event_ids]
            if inc_events:
                timeline = self.timeline_builder.build_timeline(inc.incident_id, inc_events)
                self._active_timelines[timeline.timeline_id] = timeline
                timelines.append(timeline)

        self._metrics["timelines_built"] += len(timelines)

        logger.info(
            f"TIMELINE: Built {len(timelines)} timelines",
            extra={"timelines": len(timelines)}
        )
        return timelines

    def _score(self, incidents: List[CorrelatedIncident]) -> List[SentinelAlert]:
        """Step 5: Score incidents and generate alerts."""
        alerts = self.severity_engine.process_incidents(incidents)

        for alert in alerts:
            self._active_alerts[alert.alert_id] = alert

        self._metrics["alerts_generated"] += len(alerts)

        logger.info(
            f"SCORE: {len(incidents)} incidents → {len(alerts)} alerts",
            extra={"alerts": len(alerts), "incidents": len(incidents)}
        )
        return alerts

    def _export(
        self,
        incidents: List[CorrelatedIncident],
        timelines: List[IncidentTimeline],
        alerts: List[SentinelAlert]
    ):
        """Step 6: Export data to files and optional cloud."""
        if incidents:
            package = self.exporter.create_package(incidents, timelines, alerts)
            filepath = self.exporter.export_json(package)
            self._metrics["exports_created"] += 1

            # Also export summaries
            self.exporter.export_incident_summary(list(self._active_incidents.values()))
            self.exporter.export_alert_feed(list(self._active_alerts.values()))

            logger.info(f"EXPORT: Package exported to {filepath}")

        # Optional Supabase sync
        if self.supabase.enabled:
            asyncio.create_task(self.supabase.sync_incidents(incidents))
            asyncio.create_task(self.supabase.sync_alerts(alerts))

    async def start(self):
        """Start the complete pipeline."""
        self._running = True
        self._metrics["pipeline_start_time"] = datetime.now(timezone.utc).isoformat()

        logger.info("=" * 60)
        logger.info("TRACEOPS LIVE PIPELINE STARTING")
        logger.info("=" * 60)
        logger.info(f"WhatsApp DB: {settings.WHATSAPP_DB_PATH}")
        logger.info(f"Poll interval: {settings.POLLING_INTERVAL}s")
        logger.info(f"Correlation window: {settings.CORRELATION_WINDOW_MINUTES}min")
        logger.info(f"Auto-alerts: {settings.ENABLE_AUTO_ALERTS}")
        logger.info(f"Supabase sync: {settings.ENABLE_SUPABASE_SYNC}")
        logger.info("=" * 60)

        # Setup signal handlers
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, self._signal_handler)

        # Start ingestor
        self.ingestor.start()

        # Run until shutdown
        try:
            await self._shutdown_event.wait()
        except asyncio.CancelledError:
            pass

        await self.stop()

    def _signal_handler(self):
        """Handle shutdown signals."""
        logger.info("Shutdown signal received")
        self._shutdown_event.set()

    async def stop(self):
        """Graceful shutdown."""
        self._running = False

        logger.info("=" * 60)
        logger.info("TRACEOPS LIVE PIPELINE SHUTTING DOWN")
        logger.info("=" * 60)

        # Stop ingestor
        self.ingestor.stop()

        # Final export
        if self._active_incidents:
            logger.info("Performing final export...")
            package = self.exporter.create_package(
                incidents=list(self._active_incidents.values()),
                timelines=list(self._active_timelines.values()),
                alerts=list(self._active_alerts.values())
            )
            self.exporter.export_json(package, filename="traceops_final_export.json")

        # Print final metrics
        logger.info("=" * 60)
        logger.info("FINAL METRICS")
        logger.info("=" * 60)
        for key, value in self._metrics.items():
            logger.info(f"  {key}: {value}")
        logger.info("=" * 60)
        logger.info("TraceOps Live stopped")

    def get_metrics(self) -> Dict[str, Any]:
        """Get current pipeline metrics."""
        return {
            **self._metrics,
            "active_incidents": len(self._active_incidents),
            "active_alerts": len(self._active_alerts),
            "active_timelines": len(self._active_timelines),
            "is_running": self._running,
        }

    def get_active_incidents(self) -> List[CorrelatedIncident]:
        """Get currently active incidents."""
        return sorted(
            self._active_incidents.values(),
            key=lambda x: x.created_at or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True
        )

    def get_active_alerts(self) -> List[SentinelAlert]:
        """Get currently active alerts."""
        return sorted(
            self._active_alerts.values(),
            key=lambda x: (
                {"critical": 4, "high": 3, "medium": 2, "low": 1}.get(x.severity.value, 0),
                x.generated_at or datetime.min.replace(tzinfo=timezone.utc)
            ),
            reverse=True
        )


# CLI entry point
def main():
    """CLI entry point for running the pipeline."""
    import argparse

    parser = argparse.ArgumentParser(description="TraceOps Live - Manufacturing Intelligence")
    parser.add_argument("--config", help="Path to config file")
    parser.add_argument("--poll-interval", type=float, help="Polling interval in seconds")
    parser.add_argument("--no-auto-alerts", action="store_true", help="Disable auto-alerts")
    parser.add_argument("--supabase", action="store_true", help="Enable Supabase sync")

    args = parser.parse_args()

    # Setup logging
    setup_logging()

    # Create and run pipeline
    pipeline = TraceOpsPipeline()

    try:
        asyncio.run(pipeline.start())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")


if __name__ == "__main__":
    main()
