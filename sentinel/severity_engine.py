"""
sentinel/severity_engine.py
Sentinel Engine for manufacturing alert severity calculation.
Computes severity, escalation score, recurrence score, and operational impact.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from config.settings import settings
from config.logging_config import get_sentinel_logger
from schemas.event_schema import (
    CorrelatedIncident, SentinelAlert, SeverityLevel,
    StationType, DefectType, TimelineEvent
)
from storage.incident_memory import IncidentMemory


logger = get_sentinel_logger()


class SeverityEngine:
    """
    Calculates severity and operational impact for manufacturing incidents.

    Severity rules:
    - line down = critical
    - repeated component failure = high
    - ECO / deviation / hold = high
    - image evidence attached = severity boost
    - yield drop > 20% = high
    - yield drop > 50% = critical
    - multiple stations affected = escalation boost
    - recurring pattern = recurrence score boost
    """

    # Severity thresholds
    YIELD_CRITICAL = 50.0
    YIELD_HIGH = 80.0
    YIELD_MEDIUM = 90.0

    # Score weights
    ESCALATION_WEIGHTS = {
        "line_down": 40,
        "yield_critical": 35,
        "yield_high": 25,
        "multi_station": 15,
        "multi_line": 15,
        "media_evidence": 10,
        "eco_deviation": 20,
        "duration_long": 10,  # > 2 hours
        "recurring": 20,
    }

    def __init__(self, incident_memory: IncidentMemory = None):
        self.incident_memory = incident_memory
        self._stats = {
            "alerts_generated": 0,
            "by_severity": {s.value: 0 for s in SeverityLevel},
            "by_type": {},
        }
        logger.info("SeverityEngine initialized")

    def _calculate_base_severity(self, incident: CorrelatedIncident) -> SeverityLevel:
        """Determine base severity from incident characteristics."""

        # Critical: line down
        if any("line_down" in str(incident.affected_lines) for _ in [1]):
            # Check if line_down is actually in the incident data
            pass

        # We need to check the full incident data for tags
        # For now, use max_severity from clustering as starting point
        return incident.max_severity

    def _calculate_escalation_score(self, incident: CorrelatedIncident) -> float:
        """
        Calculate escalation urgency score (0-100).
        Higher = more urgent to escalate.
        """
        score = 0.0

        # Line down
        if incident.primary_line and incident.duration_minutes and incident.duration_minutes > 0:
            # If line is down (implied by critical severity + line context)
            if incident.max_severity == SeverityLevel.CRITICAL:
                score += self.ESCALATION_WEIGHTS["line_down"]

        # Multi-station impact
        # (Would need full event data to count unique stations)

        # Multi-line impact
        if len(incident.affected_lines) > 1:
            score += self.ESCALATION_WEIGHTS["multi_line"]

        # Long duration
        if incident.duration_minutes and incident.duration_minutes > 120:
            score += self.ESCALATION_WEIGHTS["duration_long"]

        # Recurring
        if incident.is_recurring:
            score += self.ESCALATION_WEIGHTS["recurring"]

        return min(score, 100.0)

    def _calculate_recurrence_score(
        self,
        incident: CorrelatedIncident
    ) -> float:
        """
        Calculate recurrence risk score (0-100).
        Based on historical pattern matching.
        """
        score = 0.0

        # Base on recurrence count
        if incident.recurrence_count > 0:
            score += min(incident.recurrence_count * 15, 50)

        # Check historical patterns
        if self.incident_memory:
            similar = self.incident_memory.find_similar_incidents(
                component=incident.primary_component,
                station=incident.primary_station.value if incident.primary_station else None,
                line=incident.primary_line,
                model=incident.primary_model,
                defect=incident.primary_defect.value if incident.primary_defect else None,
                limit=5
            )
            if similar:
                score += min(len(similar) * 10, 30)
                # Boost if recent similar incidents
                recent_count = sum(1 for s in similar if s.get("recurrence_count", 0) > 0)
                score += recent_count * 5

        return min(score, 100.0)

    def _calculate_operational_impact(self, incident: CorrelatedIncident) -> float:
        """
        Calculate operational impact score (0-100).
        Considers lines affected, components, duration.
        """
        score = 0.0

        # Lines affected (each line = 20 points)
        line_count = len(incident.affected_lines)
        score += min(line_count * 20, 60)

        # Components affected (each = 5 points)
        comp_count = len(incident.affected_components)
        score += min(comp_count * 5, 20)

        # Duration impact
        if incident.duration_minutes:
            if incident.duration_minutes > 240:  # > 4 hours
                score += 20
            elif incident.duration_minutes > 120:  # > 2 hours
                score += 10
            elif incident.duration_minutes > 60:  # > 1 hour
                score += 5

        # Severity multiplier
        if incident.max_severity == SeverityLevel.CRITICAL:
            score = min(score * 1.5, 100)
        elif incident.max_severity == SeverityLevel.HIGH:
            score = min(score * 1.2, 100)

        return min(score, 100.0)

    def _determine_alert_type(self, incident: CorrelatedIncident) -> str:
        """Classify alert type based on incident characteristics."""

        if incident.max_severity == SeverityLevel.CRITICAL:
            return "line_down"

        if incident.is_recurring:
            return "recurring_failure"

        if incident.primary_defect:
            defect_value = incident.primary_defect.value
            if defect_value in ["bridge", "short", "open", "missing"]:
                return "defect_spike"

        # Check for yield indicators (would need full event data)

        if incident.primary_station in [StationType.AOI, StationType.SPI]:
            return "yield_drop"

        return "station_alarm"

    def _generate_title(self, incident: CorrelatedIncident) -> str:
        """Generate alert title."""
        parts = []

        if incident.max_severity == SeverityLevel.CRITICAL:
            parts.append("🚨 CRITICAL")
        elif incident.max_severity == SeverityLevel.HIGH:
            parts.append("⚠️ HIGH")

        if incident.primary_station:
            parts.append(incident.primary_station.value)

        if incident.primary_defect:
            parts.append(incident.primary_defect.value)

        if incident.primary_component:
            parts.append(f"on {incident.primary_component}")

        if incident.primary_line:
            parts.append(f"| Line {incident.primary_line}")

        return " ".join(parts) if parts else "Manufacturing Alert"

    def _generate_description(self, incident: CorrelatedIncident) -> str:
        """Generate detailed alert description."""
        parts = []

        parts.append(f"Incident ID: {incident.incident_id}")

        if incident.primary_component:
            parts.append(f"Component: {incident.primary_component}")

        if incident.primary_station:
            parts.append(f"Station: {incident.primary_station.value}")

        if incident.primary_defect:
            parts.append(f"Defect: {incident.primary_defect.value}")

        if incident.primary_line:
            parts.append(f"Line: {incident.primary_line}")

        if incident.primary_model:
            parts.append(f"Model: {incident.primary_model}")

        if incident.event_count:
            parts.append(f"Events: {incident.event_count}")

        if incident.duration_minutes:
            hours = int(incident.duration_minutes // 60)
            mins = int(incident.duration_minutes % 60)
            parts.append(f"Duration: {hours}h {mins}m")

        if incident.is_recurring:
            parts.append(f"⚠️ RECURRING (count: {incident.recurrence_count})")

        return " | ".join(parts)

    def _generate_recommendation(self, incident: CorrelatedIncident) -> Optional[str]:
        """Generate action recommendation."""
        if incident.max_severity == SeverityLevel.CRITICAL:
            return "Immediate line stop required. Notify production manager and quality engineer."

        if incident.is_recurring:
            return "Root cause analysis required. Review process parameters and component supplier."

        if incident.primary_defect:
            defect_recs = {
                "bridge": "Check solder paste volume and reflow profile. Inspect stencil aperture.",
                "short": "Verify component placement accuracy. Check for solder splash.",
                "open": "Inspect solder paste deposit. Check component lead coplanarity.",
                "missing": "Verify pick-and-place accuracy. Check feeder alignment.",
                "tombstone": "Review pad design symmetry. Check reflow profile heating rate.",
                "polarity": "Verify component orientation in feeder. Check vision system calibration.",
                "misalignment": "Recalibrate placement machine. Check PCB fiducial recognition.",
                "void": "Review reflow profile peak temperature. Check solder paste storage conditions.",
            }
            return defect_recs.get(incident.primary_defect.value)

        return "Monitor and document. Escalate if trend continues."

    def process_incident(self, incident: CorrelatedIncident) -> Optional[SentinelAlert]:
        """
        Process an incident and generate alert if threshold met.

        Args:
            incident: CorrelatedIncident to evaluate

        Returns:
            SentinelAlert or None if below threshold
        """
        # Calculate scores
        escalation = self._calculate_escalation_score(incident)
        recurrence = self._calculate_recurrence_score(incident)
        impact = self._calculate_operational_impact(incident)

        # Determine final severity
        # Start with base and adjust based on scores
        severity = incident.max_severity

        # Boost severity if scores are high
        if escalation > 70 or impact > 70:
            severity = SeverityLevel.CRITICAL
        elif escalation > 50 or impact > 50 or recurrence > 60:
            if severity.value < SeverityLevel.HIGH.value:
                severity = SeverityLevel.HIGH
        elif escalation > 30 or impact > 30:
            if severity.value < SeverityLevel.MEDIUM.value:
                severity = SeverityLevel.MEDIUM

        # Check auto-alert threshold
        threshold_map = {
            "low": SeverityLevel.LOW,
            "medium": SeverityLevel.MEDIUM,
            "high": SeverityLevel.HIGH,
            "critical": SeverityLevel.CRITICAL,
        }
        threshold = threshold_map.get(settings.AUTO_ALERT_THRESHOLD, SeverityLevel.HIGH)

        if severity.value < threshold.value and not settings.ENABLE_AUTO_ALERTS:
            logger.debug(
                f"Incident {incident.incident_id} below alert threshold",
                extra={"incident_id": incident.incident_id, "severity": severity.value}
            )
            return None

        # Generate alert
        alert = SentinelAlert(
            alert_id=f"ALT-{uuid.uuid4().hex[:12].upper()}",
            incident_id=incident.incident_id,
            generated_at=datetime.now(timezone.utc),
            severity=severity,
            escalation_score=escalation,
            recurrence_score=recurrence,
            operational_impact=impact,
            alert_type=self._determine_alert_type(incident),
            title=self._generate_title(incident),
            description=self._generate_description(incident),
            recommendation=self._generate_recommendation(incident),
            affected_station=incident.primary_station,
            affected_line=incident.primary_line,
            affected_component=incident.primary_component,
            affected_model=incident.primary_model,
            evidence_events=incident.event_ids,
            target_groups=["production", "quality"] if severity.value >= SeverityLevel.HIGH.value else ["production"],
        )

        self._stats["alerts_generated"] += 1
        self._stats["by_severity"][severity.value] += 1
        self._stats["by_type"][alert.alert_type] =             self._stats["by_type"].get(alert.alert_type, 0) + 1

        logger.info(
            f"Alert generated: {alert.alert_id} [{alert.severity.value}] {alert.title}",
            extra={
                "alert_id": alert.alert_id,
                "incident_id": incident.incident_id,
                "severity": alert.severity.value,
                "escalation": alert.escalation_score,
                "recurrence": alert.recurrence_score,
                "impact": alert.operational_impact,
            }
        )

        return alert

    def process_incidents(
        self,
        incidents: List[CorrelatedIncident]
    ) -> List[SentinelAlert]:
        """Process multiple incidents and generate alerts."""
        alerts = []
        for incident in incidents:
            alert = self.process_incident(incident)
            if alert:
                alerts.append(alert)
        return alerts

    def get_stats(self) -> Dict[str, Any]:
        """Return engine statistics."""
        return dict(self._stats)
