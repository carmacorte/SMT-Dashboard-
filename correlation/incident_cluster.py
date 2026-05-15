"""
correlation/incident_cluster.py
Correlation Engine for manufacturing event clustering.
Groups related events into incidents based on temporal and spatial proximity.
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Set, Tuple
from collections import defaultdict

from config.settings import settings
from config.logging_config import get_correlation_logger
from schemas.event_schema import (
    ParsedManufacturingEvent, CorrelatedIncident,
    StationType, DefectType, SeverityLevel
)


logger = get_correlation_logger()


class IncidentClusterer:
    """
    Groups manufacturing events into correlated incidents.

    Clustering dimensions:
    - Time: events within CORRELATION_WINDOW_MINUTES
    - Station: same or related stations
    - Component: same component reference
    - Line: same production line
    - Model: same product model

    Detects recurring failures by pattern matching.
    """

    def __init__(
        self,
        window_minutes: int = None,
        min_events: int = None
    ):
        self.window_minutes = window_minutes or settings.CORRELATION_WINDOW_MINUTES
        self.min_events = min_events or settings.CORRELATION_MIN_EVENTS

        # Active incidents (open, being built)
        self._active_incidents: Dict[str, CorrelatedIncident] = {}

        # Stats
        self._stats = {
            "total_clustered": 0,
            "total_incidents": 0,
            "merged_events": 0,
            "rejected_events": 0,
        }

        logger.info(
            "IncidentClusterer initialized",
            extra={
                "window_minutes": self.window_minutes,
                "min_events": self.min_events,
            }
        )

    def _generate_incident_id(self) -> str:
        """Generate unique incident ID."""
        return f"INC-{uuid.uuid4().hex[:12].upper()}"

    def _events_match(
        self,
        event: ParsedManufacturingEvent,
        incident: CorrelatedIncident
    ) -> bool:
        """
        Check if an event matches an existing incident.

        Matching rules (OR logic with weights):
        - Same component: strong match
        - Same line: strong match
        - Same station: medium match
        - Same model: medium match
        - Same defect: medium match
        - Time within window: required
        """
        # Time check - must be within window
        if incident.last_event_time:
            time_diff = abs((event.timestamp - incident.last_event_time).total_seconds() / 60)
            if time_diff > self.window_minutes:
                return False

        # If no prior events, can't match
        if not incident.event_ids:
            return False

        match_score = 0

        # Component match (strong)
        if event.component and incident.primary_component:
            if event.component == incident.primary_component:
                match_score += 3

        # Line match (strong)
        if event.line and incident.primary_line:
            if event.line == incident.primary_line:
                match_score += 3

        # Station match (medium)
        if event.station and incident.primary_station:
            if event.station == incident.primary_station:
                match_score += 2
            # Related stations (SPI→AOI→REFLOW chain)
            elif self._are_stations_related(event.station, incident.primary_station):
                match_score += 1

        # Model match (medium)
        if event.model and incident.primary_model:
            if event.model == incident.primary_model:
                match_score += 2

        # Defect match (medium)
        if event.defect and incident.primary_defect:
            if event.defect == incident.primary_defect:
                match_score += 2

        # Need at least 2 points to match
        return match_score >= 2

    def _are_stations_related(self, s1: StationType, s2: StationType) -> bool:
        """Check if two stations are in the same process chain."""
        # SMT process flow: SPI → PICK&PLACE → AOI → REFLOW → AOI → ICT → FCT
        process_chain = [
            [StationType.SPI, StationType.AOI, StationType.REFLOW],
            [StationType.AOI, StationType.XRAY, StationType.FIVE_DX],
            [StationType.ICT, StationType.FCT],
            [StationType.PTH, StationType.PRESSFIT],
        ]
        for chain in process_chain:
            if s1 in chain and s2 in chain:
                return True
        return False

    def _update_incident(
        self,
        incident: CorrelatedIncident,
        event: ParsedManufacturingEvent
    ):
        """Add event to existing incident and update metadata."""
        incident.event_ids.append(event.event_id)
        incident.event_count = len(incident.event_ids)

        # Update time window
        if incident.first_event_time is None or event.timestamp < incident.first_event_time:
            incident.first_event_time = event.timestamp
        if incident.last_event_time is None or event.timestamp > incident.last_event_time:
            incident.last_event_time = event.timestamp

        # Recalculate duration
        if incident.first_event_time and incident.last_event_time:
            incident.duration_minutes = (
                incident.last_event_time - incident.first_event_time
            ).total_seconds() / 60

        # Update affected lists
        if event.line and event.line not in incident.affected_lines:
            incident.affected_lines.append(event.line)
        if event.component and event.component not in incident.affected_components:
            incident.affected_components.append(event.component)

        # Update severity based on event tags
        if "line_down" in event.tags:
            incident.max_severity = SeverityLevel.CRITICAL
        elif event.confidence_score > 0.8 and incident.max_severity.value < SeverityLevel.HIGH.value:
            incident.max_severity = SeverityLevel.HIGH

        # Update primary fields if more specific
        if event.component and not incident.primary_component:
            incident.primary_component = event.component
        if event.station and not incident.primary_station:
            incident.primary_station = event.station
        if event.line and not incident.primary_line:
            incident.primary_line = event.line
        if event.model and not incident.primary_model:
            incident.primary_model = event.model
        if event.defect and not incident.primary_defect:
            incident.primary_defect = event.defect

        logger.debug(
            f"Updated incident {incident.incident_id} with event {event.event_id}",
            extra={
                "incident_id": incident.incident_id,
                "event_id": event.event_id,
                "event_count": incident.event_count,
            }
        )

    def _create_incident(self, event: ParsedManufacturingEvent) -> CorrelatedIncident:
        """Create new incident from single event."""
        incident = CorrelatedIncident(
            incident_id=self._generate_incident_id(),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            primary_station=event.station,
            primary_component=event.component,
            primary_line=event.line,
            primary_model=event.model,
            primary_defect=event.defect,
            event_ids=[event.event_id],
            event_count=1,
            first_event_time=event.timestamp,
            last_event_time=event.timestamp,
            duration_minutes=0.0,
            max_severity=SeverityLevel.LOW,
            affected_lines=[event.line] if event.line else [],
            affected_components=[event.component] if event.component else [],
        )

        # Set initial severity based on event
        if "line_down" in event.tags:
            incident.max_severity = SeverityLevel.CRITICAL
        elif event.confidence_score > 0.8:
            incident.max_severity = SeverityLevel.HIGH
        elif event.confidence_score > 0.5:
            incident.max_severity = SeverityLevel.MEDIUM

        logger.info(
            f"Created incident {incident.incident_id} from event {event.event_id}",
            extra={
                "incident_id": incident.incident_id,
                "event_id": event.event_id,
                "station": event.station.value if event.station else None,
                "component": event.component,
            }
        )

        return incident

    def process_events(
        self,
        events: List[ParsedManufacturingEvent]
    ) -> Tuple[List[CorrelatedIncident], List[ParsedManufacturingEvent]]:
        """
        Process events and cluster into incidents.

        Returns:
            Tuple of (new_or_updated_incidents, unclustered_events)
        """
        new_incidents: List[CorrelatedIncident] = []
        unclustered: List[ParsedManufacturingEvent] = []

        for event in events:
            self._stats["total_clustered"] += 1

            # Try to match with existing active incidents
            matched = False
            for incident in list(self._active_incidents.values()):
                if self._events_match(event, incident):
                    self._update_incident(incident, event)
                    matched = True
                    self._stats["merged_events"] += 1
                    break

            if not matched:
                # Create new incident
                incident = self._create_incident(event)
                self._active_incidents[incident.incident_id] = incident
                new_incidents.append(incident)
                self._stats["total_incidents"] += 1

        # Filter incidents that meet minimum event threshold
        # Note: We keep single-event incidents as "emerging" - they may grow
        # Only finalize incidents with min_events or more
        finalized = [
            inc for inc in new_incidents
            if inc.event_count >= self.min_events
        ]

        # Single-event incidents stay in active pool
        for inc in new_incidents:
            if inc.event_count < self.min_events:
                # Keep in active for potential future merging
                pass

        # Clean up old active incidents (older than 2x window)
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=self.window_minutes * 2)
        expired = [
            k for k, v in self._active_incidents.items()
            if v.last_event_time and v.last_event_time < cutoff
        ]
        for k in expired:
            del self._active_incidents[k]

        logger.info(
            f"Processed {len(events)} events: "
            f"{len(finalized)} finalized incidents, "
            f"{len(self._active_incidents)} active, "
            f"{len(unclustered)} unclustered"
        )

        return finalized, unclustered

    def get_active_incidents(self) -> List[CorrelatedIncident]:
        """Get all currently active (open) incidents."""
        return list(self._active_incidents.values())

    def get_incident(self, incident_id: str) -> Optional[CorrelatedIncident]:
        """Get specific incident by ID."""
        return self._active_incidents.get(incident_id)

    def close_incident(self, incident_id: str) -> bool:
        """Mark incident as closed."""
        if incident_id in self._active_incidents:
            incident = self._active_incidents[incident_id]
            incident.status = "closed"
            logger.info(f"Closed incident {incident_id}")
            return True
        return False

    def get_stats(self) -> Dict[str, any]:
        """Return clustering statistics."""
        return {
            **self._stats,
            "active_incidents": len(self._active_incidents),
        }
