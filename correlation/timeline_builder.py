"""
correlation/timeline_builder.py
Timeline reconstruction for manufacturing incidents.
Builds chronological event sequences from clustered incidents.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from config.logging_config import get_correlation_logger
from schemas.event_schema import (
    ParsedManufacturingEvent, TimelineEvent, IncidentTimeline,
    StationType, DefectType
)


logger = get_correlation_logger()


class TimelineBuilder:
    """
    Reconstructs incident timelines from chronological event sequences.

    Example timeline:
    07:12 PE notified
    07:18 AOI fail
    07:25 Yield impacted
    07:41 Xray confirmation
    08:03 Rework completed
    """

    def __init__(self):
        self._stats = {
            "timelines_built": 0,
            "events_timelined": 0,
        }
        logger.info("TimelineBuilder initialized")

    def _classify_event_type(
        self,
        event: ParsedManufacturingEvent,
        position: int,
        total: int
    ) -> str:
        """
        Classify event role in timeline based on content and position.
        """
        content_lower = event.raw_message.lower()

        # First event in sequence
        if position == 0:
            if "notif" in content_lower or "alert" in content_lower or "report" in content_lower:
                return "notification"
            return "detection"

        # Last event
        if position == total - 1:
            if any(w in content_lower for w in ["rework", "repair", "fixed", "corrected"]):
                return "resolution"
            if any(w in content_lower for w in ["hold", "stop", "quarantine"]):
                return "hold"
            if any(w in content_lower for w in ["release", "approve", "clear"]):
                return "release"

        # Middle events - classify by content
        if any(w in content_lower for w in ["confirm", "verify", "check", "xray", "validate"]):
            return "confirmation"

        if any(w in content_lower for w in ["yield", "impact", "affect", "drop", "fall"]):
            return "impact"

        if any(w in content_lower for w in ["escal", "supervisor", "manager", "lead"]):
            return "escalation"

        if any(w in content_lower for w in ["action", "do", "take", "implement"]):
            return "action"

        if any(w in content_lower for w in ["rework", "repair", "fix"]):
            return "rework"

        # Default based on station
        if event.station:
            station_order = {
                StationType.SPI: "detection",
                StationType.AOI: "detection",
                StationType.XRAY: "confirmation",
                StationType.FIVE_DX: "confirmation",
                StationType.ICT: "confirmation",
                StationType.FCT: "confirmation",
                StationType.REFLOW: "impact",
            }
            return station_order.get(event.station, "detection")

        return "detection"

    def build_timeline(
        self,
        incident_id: str,
        events: List[ParsedManufacturingEvent]
    ) -> IncidentTimeline:
        """
        Build timeline from ordered events.

        Args:
            incident_id: Parent incident ID
            events: Chronologically ordered events

        Returns:
            IncidentTimeline with classified events
        """
        # Sort by timestamp
        sorted_events = sorted(events, key=lambda e: e.timestamp)

        timeline_events: List[TimelineEvent] = []

        for i, event in enumerate(sorted_events):
            event_type = self._classify_event_type(event, i, len(sorted_events))

            # Build description
            desc_parts = []
            if event.station:
                desc_parts.append(event.station.value)
            if event.defect:
                desc_parts.append(event.defect.value)
            if event.component:
                desc_parts.append(f"on {event.component}")

            description = " ".join(desc_parts) if desc_parts else event.raw_message[:100]

            timeline_event = TimelineEvent(
                timestamp=event.timestamp,
                event_type=event_type,
                description=description,
                actor=event.sender,
                station=event.station,
                component=event.component,
                line=event.line,
                source_event_id=event.event_id,
                source_message_id=event.source_message_id,
            )
            timeline_events.append(timeline_event)

        # Calculate time metrics
        time_to_detect = None
        time_to_respond = None
        time_to_resolve = None

        if len(timeline_events) >= 2:
            first = timeline_events[0].timestamp
            last = timeline_events[-1].timestamp

            # Time to detect: from first detection to first confirmation
            detections = [e for e in timeline_events if e.event_type == "detection"]
            confirmations = [e for e in timeline_events if e.event_type == "confirmation"]

            if detections and confirmations:
                time_to_detect = (confirmations[0].timestamp - detections[0].timestamp).total_seconds() / 60

            # Time to respond: from detection to first action
            actions = [e for e in timeline_events if e.event_type in ("action", "escalation")]
            if detections and actions:
                time_to_respond = (actions[0].timestamp - detections[0].timestamp).total_seconds() / 60

            # Time to resolve: from detection to resolution
            resolutions = [e for e in timeline_events if e.event_type == "resolution"]
            if detections and resolutions:
                time_to_resolve = (resolutions[0].timestamp - detections[0].timestamp).total_seconds() / 60

        timeline = IncidentTimeline(
            incident_id=incident_id,
            timeline_id=f"TL-{uuid.uuid4().hex[:12].upper()}",
            events=timeline_events,
            time_to_detect_minutes=time_to_detect,
            time_to_respond_minutes=time_to_respond,
            time_to_resolve_minutes=time_to_resolve,
        )

        self._stats["timelines_built"] += 1
        self._stats["events_timelined"] += len(timeline_events)

        logger.info(
            f"Built timeline {timeline.timeline_id} for incident {incident_id}: "
            f"{len(timeline_events)} events, "
            f"TTD={time_to_detect:.1f}m" if time_to_detect else "N/A",
            extra={
                "timeline_id": timeline.timeline_id,
                "incident_id": incident_id,
                "event_count": len(timeline_events),
            }
        )

        return timeline

    def get_stats(self) -> Dict[str, Any]:
        """Return timeline statistics."""
        return dict(self._stats)
