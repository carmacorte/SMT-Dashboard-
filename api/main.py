"""
api/main.py
FastAPI application for TraceOps Live REST API.
Provides endpoints for incident monitoring, alerts, and exports.
"""

import asyncio
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config.settings import settings
from config.logging_config import setup_logging, get_api_logger
from schemas.event_schema import (
    CorrelatedIncident, SentinelAlert, IncidentTimeline, ExportPackage
)
from storage.sqlite_ingestor import SQLiteIngestor
from storage.incident_memory import IncidentMemory
from parser.manufacturing_parser import ManufacturingParser
from correlation.incident_cluster import IncidentClusterer
from correlation.timeline_builder import TimelineBuilder
from sentinel.severity_engine import SeverityEngine
from export.smtinel_exporter import SMTinelExporter, SupabaseSync


logger = get_api_logger()

# Global service instances
_ingestor: Optional[SQLiteIngestor] = None
_incident_memory: Optional[IncidentMemory] = None
_parser: Optional[ManufacturingParser] = None
_clusterer: Optional[IncidentClusterer] = None
_timeline_builder: Optional[TimelineBuilder] = None
_severity_engine: Optional[SeverityEngine] = None
_exporter: Optional[SMTinelExporter] = None
_supabase: Optional[SupabaseSync] = None

# In-memory storage for active pipeline
_active_incidents: Dict[str, CorrelatedIncident] = {}
_active_alerts: Dict[str, SentinelAlert] = {}
_active_timelines: Dict[str, IncidentTimeline] = {}


class PipelineMessage(BaseModel):
    """Message from pipeline processing."""
    message: str
    timestamp: datetime


class StatusResponse(BaseModel):
    """System status response."""
    status: str
    version: str = "1.0.0"
    uptime_seconds: float
    components: Dict[str, Any]


class IncidentListResponse(BaseModel):
    """Paginated incident list."""
    total: int
    incidents: List[Dict[str, Any]]
    page: int
    page_size: int


class AlertListResponse(BaseModel):
    """Alert feed response."""
    total: int
    alerts: List[Dict[str, Any]]
    generated_at: str


class StatsResponse(BaseModel):
    """Pipeline statistics."""
    ingestor: Dict[str, Any]
    parser: Dict[str, Any]
    clusterer: Dict[str, Any]
    sentinel: Dict[str, Any]
    exporter: Dict[str, Any]


def _process_messages(messages: List[Any]):
    """Process messages through the full pipeline."""
    global _active_incidents, _active_alerts, _active_timelines

    if not _parser:
        return

    # Parse messages
    events = _parser.parse_batch(messages)
    if not events:
        return

    # Cluster events
    if _clusterer:
        incidents, _ = _clusterer.process_events(events)

        # Store incidents
        for inc in incidents:
            _active_incidents[inc.incident_id] = inc
            if _incident_memory:
                _incident_memory.store_incident(inc)

        # Build timelines
        if _timeline_builder:
            # Group events by incident
            for inc in incidents:
                inc_events = [e for e in events if e.event_id in inc.event_ids]
                if inc_events:
                    timeline = _timeline_builder.build_timeline(inc.incident_id, inc_events)
                    _active_timelines[timeline.timeline_id] = timeline

        # Generate alerts
        if _severity_engine:
            alerts = _severity_engine.process_incidents(incidents)
            for alert in alerts:
                _active_alerts[alert.alert_id] = alert

            # Sync to Supabase if enabled
            if _supabase and _supabase.enabled:
                asyncio.create_task(_supabase.sync_alerts(alerts))
                asyncio.create_task(_supabase.sync_incidents(incidents))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global _ingestor, _incident_memory, _parser, _clusterer
    global _timeline_builder, _severity_engine, _exporter, _supabase

    # Startup
    logger.info("TraceOps Live starting up...")

    # Setup logging
    setup_logging()

    # Validate settings
    issues = settings.validate()
    if issues:
        for issue in issues:
            logger.warning(f"Config issue: {issue}")

    # Initialize services
    _incident_memory = IncidentMemory()
    _parser = ManufacturingParser()
    _clusterer = IncidentClusterer()
    _timeline_builder = TimelineBuilder()
    _severity_engine = SeverityEngine(_incident_memory)
    _exporter = SMTinelExporter()
    _supabase = SupabaseSync()

    # Start ingestor
    _ingestor = SQLiteIngestor(on_new_messages=_process_messages)
    _ingestor.start()

    logger.info("TraceOps Live startup complete")

    yield

    # Shutdown
    logger.info("TraceOps Live shutting down...")
    if _ingestor:
        _ingestor.stop()
    logger.info("TraceOps Live shutdown complete")


app = FastAPI(
    title="TraceOps Live API",
    description="Manufacturing Intelligence Layer for SMT Production",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# HEALTH & STATUS
# ============================================================

@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/status", response_model=StatusResponse, tags=["System"])
async def system_status():
    """Get complete system status."""
    components = {
        "ingestor": _ingestor.get_stats() if _ingestor else {},
        "parser": _parser.get_stats() if _parser else {},
        "clusterer": _clusterer.get_stats() if _clusterer else {},
        "sentinel": _severity_engine.get_stats() if _severity_engine else {},
        "exporter": _exporter.get_stats() if _exporter else {},
        "supabase": {"enabled": _supabase.enabled if _supabase else False},
        "active_incidents": len(_active_incidents),
        "active_alerts": len(_active_alerts),
        "active_timelines": len(_active_timelines),
    }

    return StatusResponse(
        status="running",
        uptime_seconds=0,  # Would track actual uptime
        components=components
    )


# ============================================================
# INCIDENTS
# ============================================================

@app.get("/incidents", response_model=IncidentListResponse, tags=["Incidents"])
async def list_incidents(
    status: Optional[str] = Query(None, description="Filter by status: open, contained, resolved, closed"),
    severity: Optional[str] = Query(None, description="Filter by severity: low, medium, high, critical"),
    station: Optional[str] = Query(None, description="Filter by station"),
    line: Optional[str] = Query(None, description="Filter by line"),
    component: Optional[str] = Query(None, description="Filter by component"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    """List incidents with optional filters."""
    incidents = list(_active_incidents.values())

    # Apply filters
    if status:
        incidents = [i for i in incidents if i.status == status]
    if severity:
        incidents = [i for i in incidents if i.max_severity.value == severity]
    if station:
        incidents = [i for i in incidents if i.primary_station and i.primary_station.value == station]
    if line:
        incidents = [i for i in incidents if i.primary_line == line]
    if component:
        incidents = [i for i in incidents if i.primary_component == component]

    # Sort by created_at desc
    incidents.sort(key=lambda x: x.created_at or datetime.min.replace(tzinfo=timezone.utc), reverse=True)

    total = len(incidents)
    paginated = incidents[offset:offset + limit]

    return IncidentListResponse(
        total=total,
        incidents=[inc.dict() for inc in paginated],
        page=offset // limit + 1,
        page_size=limit
    )


@app.get("/incidents/{incident_id}", tags=["Incidents"])
async def get_incident(incident_id: str):
    """Get specific incident by ID."""
    if incident_id in _active_incidents:
        return _active_incidents[incident_id].dict()

    # Try from persistent storage
    if _incident_memory:
        incident = _incident_memory.get_incident(incident_id)
        if incident:
            return incident.dict()

    raise HTTPException(status_code=404, detail="Incident not found")


@app.post("/incidents/{incident_id}/status", tags=["Incidents"])
async def update_incident_status(incident_id: str, status: str):
    """Update incident status."""
    if incident_id in _active_incidents:
        _active_incidents[incident_id].status = status
        if _incident_memory:
            _incident_memory.update_incident_status(incident_id, status)
        return {"incident_id": incident_id, "status": status}

    raise HTTPException(status_code=404, detail="Incident not found")


# ============================================================
# ALERTS
# ============================================================

@app.get("/alerts", response_model=AlertListResponse, tags=["Alerts"])
async def list_alerts(
    severity: Optional[str] = Query(None, description="Filter by severity"),
    alert_type: Optional[str] = Query(None, description="Filter by alert type"),
    limit: int = Query(50, ge=1, le=200)
):
    """List alerts with optional filters."""
    alerts = list(_active_alerts.values())

    if severity:
        alerts = [a for a in alerts if a.severity.value == severity]
    if alert_type:
        alerts = [a for a in alerts if a.alert_type == alert_type]

    # Sort by severity desc, then time desc
    alerts.sort(
        key=lambda x: (
            {"critical": 4, "high": 3, "medium": 2, "low": 1}.get(x.severity.value, 0),
            x.generated_at or datetime.min.replace(tzinfo=timezone.utc)
        ),
        reverse=True
    )

    return AlertListResponse(
        total=len(alerts),
        alerts=[a.dict() for a in alerts[:limit]],
        generated_at=datetime.now(timezone.utc).isoformat()
    )


@app.get("/alerts/{alert_id}", tags=["Alerts"])
async def get_alert(alert_id: str):
    """Get specific alert by ID."""
    if alert_id in _active_alerts:
        return _active_alerts[alert_id].dict()
    raise HTTPException(status_code=404, detail="Alert not found")


# ============================================================
# TIMELINES
# ============================================================

@app.get("/timelines/{incident_id}", tags=["Timelines"])
async def get_timeline(incident_id: str):
    """Get timeline for an incident."""
    for timeline in _active_timelines.values():
        if timeline.incident_id == incident_id:
            return timeline.dict()
    raise HTTPException(status_code=404, detail="Timeline not found")


# ============================================================
# EXPORT
# ============================================================

@app.post("/export", tags=["Export"])
async def export_data(
    background_tasks: BackgroundTasks,
    incident_ids: Optional[List[str]] = None,
    time_range_start: Optional[datetime] = None,
    time_range_end: Optional[datetime] = None
):
    """Export incidents and alerts to JSON."""
    if not _exporter:
        raise HTTPException(status_code=503, detail="Exporter not initialized")

    # Filter incidents
    incidents = list(_active_incidents.values())
    if incident_ids:
        incidents = [i for i in incidents if i.incident_id in incident_ids]

    # Get related timelines
    timelines = [
        t for t in _active_timelines.values()
        if t.incident_id in [i.incident_id for i in incidents]
    ]

    # Get related alerts
    alerts = [
        a for a in _active_alerts.values()
        if a.incident_id in [i.incident_id for i in incidents]
    ]

    package = _exporter.create_package(
        incidents=incidents,
        timelines=timelines,
        alerts=alerts,
        time_range_start=time_range_start,
        time_range_end=time_range_end
    )

    filepath = _exporter.export_json(package)

    return {
        "package_id": package.package_id,
        "filepath": str(filepath),
        "incidents": len(incidents),
        "alerts": len(alerts),
        "timelines": len(timelines)
    }


@app.get("/export/summary", tags=["Export"])
async def export_summary():
    """Export incident summary for dashboard."""
    if not _exporter:
        raise HTTPException(status_code=503, detail="Exporter not initialized")

    filepath = _exporter.export_incident_summary(list(_active_incidents.values()))
    return {"filepath": str(filepath), "incidents": len(_active_incidents)}


@app.get("/export/alerts", tags=["Export"])
async def export_alert_feed():
    """Export alert feed for dashboard."""
    if not _exporter:
        raise HTTPException(status_code=503, detail="Exporter not initialized")

    filepath = _exporter.export_alert_feed(list(_active_alerts.values()))
    return {"filepath": str(filepath), "alerts": len(_active_alerts)}


# ============================================================
# STATISTICS
# ============================================================

@app.get("/stats", response_model=StatsResponse, tags=["Statistics"])
async def get_stats():
    """Get pipeline statistics."""
    return StatsResponse(
        ingestor=_ingestor.get_stats() if _ingestor else {},
        parser=_parser.get_stats() if _parser else {},
        clusterer=_clusterer.get_stats() if _clusterer else {},
        sentinel=_severity_engine.get_stats() if _severity_engine else {},
        exporter=_exporter.get_stats() if _exporter else {}
    )


@app.get("/stats/recurrence", tags=["Statistics"])
async def get_recurrence_stats(days: int = Query(30, ge=1, le=365)):
    """Get recurrence statistics."""
    if _incident_memory:
        return _incident_memory.get_recurrence_stats(days)
    return {"error": "Incident memory not available"}


# ============================================================
# MANUAL TRIGGER
# ============================================================

@app.post("/ingest/poll", tags=["Ingestion"])
async def manual_poll():
    """Manually trigger a poll cycle."""
    if not _ingestor:
        raise HTTPException(status_code=503, detail="Ingestor not initialized")

    messages = await asyncio.get_event_loop().run_in_executor(None, _ingestor.poll_once)

    if messages:
        _process_messages(messages)

    return {
        "messages_polled": len(messages),
        "new_events": len([e for e in _active_incidents.values()]),
        "new_alerts": len([a for a in _active_alerts.values()])
    }
