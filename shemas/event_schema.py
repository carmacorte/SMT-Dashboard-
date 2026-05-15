"""
schemas/event_schema.py
Normalized event schema for TraceOps Live Manufacturing Intelligence.
All data flows through these Pydantic models for type safety and validation.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, validator
from enum import Enum


class SeverityLevel(str, Enum):
    """Incident severity classification for SMT manufacturing."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class StationType(str, Enum):
    """SMT manufacturing stations."""
    SPI = "SPI"
    AOI = "AOI"
    ICT = "ICT"
    FCT = "FCT"
    FIVE_DX = "5DX"
    XRAY = "X-RAY"
    REFLOW = "REFLOW"
    PTH = "PTH"
    PRESSFIT = "PRESSFIT"
    ASSEMBLY = "ASSEMBLY"


class DefectType(str, Enum):
    """Common SMT defect classifications."""
    BRIDGE = "bridge"
    SHORT = "short"
    OPEN = "open"
    MISSING = "missing"
    TOMBSTONE = "tombstone"
    POLARITY = "polarity"
    MISALIGNMENT = "misalignment"
    VOID = "void"
    SOLDER_SPLASH = "solder_splash"
    LIFTED_LEAD = "lifted_lead"
    COPLANARITY = "coplanarity"


class ComponentPrefix(str, Enum):
    """Standard SMT component prefixes."""
    U = "U"   # ICs, processors
    R = "R"   # Resistors
    C = "C"   # Capacitors
    J = "J"   # Connectors
    L = "L"   # Inductors
    Q = "Q"   # Transistors
    D = "D"   # Diodes
    Y = "Y"   # Crystals/oscillators
    F = "F"   # Fuses
    TP = "TP" # Test points


class RawWhatsAppMessage(BaseModel):
    """
    Raw message from WhatsApp MCP bridge.
    Represents a single message as stored in the SQLite database.
    """
    id: str = Field(..., description="Unique message ID from WhatsApp")
    timestamp: datetime = Field(..., description="Message timestamp (ISO-8601)")
    sender: str = Field(..., description="Sender JID or phone number")
    sender_name: Optional[str] = Field(None, description="Resolved contact name")
    chat_jid: str = Field(..., description="Chat/group JID")
    chat_name: Optional[str] = Field(None, description="Chat/group display name")
    content: str = Field(..., description="Message text content")
    is_from_me: bool = Field(default=False, description="Message sent by self")
    media_type: Optional[str] = Field(None, description="Type of attached media")
    media_path: Optional[str] = Field(None, description="Local path to downloaded media")
    reply_to_id: Optional[str] = Field(None, description="ID of message being replied to")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class ParsedManufacturingEvent(BaseModel):
    """
    Manufacturing event extracted from a WhatsApp message.
    Contains structured data after NLP parsing.
    """
    # Identity
    event_id: str = Field(..., description="Unique event UUID")
    source_message_id: str = Field(..., description="Reference to raw message")

    # Temporal
    timestamp: datetime = Field(..., description="Event timestamp")

    # Source
    sender: str = Field(..., description="Event originator")
    group: str = Field(..., description="Source WhatsApp group")

    # Content
    raw_message: str = Field(..., description="Original message text")

    # Extracted entities
    station: Optional[StationType] = Field(None, description="Manufacturing station")
    component: Optional[str] = Field(None, description="Component reference (e.g., U519)")
    component_prefix: Optional[ComponentPrefix] = Field(None, description="Component category")
    defect: Optional[DefectType] = Field(None, description="Detected defect type")
    line: Optional[str] = Field(None, description="Production line identifier")
    model: Optional[str] = Field(None, description="Product model/SKU")
    serial: Optional[str] = Field(None, description="Serial number")

    # Context
    shift: Optional[str] = Field(None, description="Work shift (1st, 2nd, 3rd)")
    operator: Optional[str] = Field(None, description="Operator name/ID")

    # Confidence
    confidence_score: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Parser confidence (0.0-1.0)"
    )

    # Flags
    has_media: bool = Field(default=False, description="Message contains media")
    media_count: int = Field(default=0, ge=0, description="Number of media attachments")

    # Tags for quick filtering
    tags: List[str] = Field(default_factory=list, description="Auto-generated tags")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class CorrelatedIncident(BaseModel):
    """
    Group of related manufacturing events forming an operational incident.
    Events are clustered by time, station, component, line, and model.
    """
    incident_id: str = Field(..., description="Unique incident UUID")

    # Clustering metadata
    created_at: datetime = Field(..., description="Incident creation time")
    updated_at: datetime = Field(..., description="Last event addition time")

    # Clustering keys
    primary_station: Optional[StationType] = Field(None, description="Dominant station")
    primary_component: Optional[str] = Field(None, description="Dominant component")
    primary_line: Optional[str] = Field(None, description="Dominant line")
    primary_model: Optional[str] = Field(None, description="Dominant model")
    primary_defect: Optional[DefectType] = Field(None, description="Dominant defect")

    # Event collection
    event_ids: List[str] = Field(default_factory=list, description="Contained event IDs")
    event_count: int = Field(default=0, ge=0, description="Number of events")

    # Time window
    first_event_time: Optional[datetime] = Field(None, description="First event timestamp")
    last_event_time: Optional[datetime] = Field(None, description="Last event timestamp")
    duration_minutes: Optional[float] = Field(None, description="Incident duration")

    # Severity
    max_severity: SeverityLevel = Field(default=SeverityLevel.LOW)
    severity_history: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Severity changes over time"
    )

    # Recurrence tracking
    is_recurring: bool = Field(default=False, description="Previously seen pattern")
    similar_incident_ids: List[str] = Field(default_factory=list)
    recurrence_count: int = Field(default=0, ge=0)

    # Status
    status: Literal["open", "contained", "resolved", "closed"] = Field(default="open")

    # Impact
    affected_lines: List[str] = Field(default_factory=list)
    affected_components: List[str] = Field(default_factory=list)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class SentinelAlert(BaseModel):
    """
    Generated alert after severity scoring and operational impact analysis.
    Ready for injection into SMTinel Dashboard.
    """
    alert_id: str = Field(..., description="Unique alert UUID")
    incident_id: str = Field(..., description="Source incident reference")

    # Timing
    generated_at: datetime = Field(..., description="Alert generation time")

    # Severity
    severity: SeverityLevel = Field(...)
    escalation_score: float = Field(
        default=0.0, ge=0.0, le=100.0,
        description="Escalation urgency (0-100)"
    )
    recurrence_score: float = Field(
        default=0.0, ge=0.0, le=100.0,
        description="Recurrence risk (0-100)"
    )
    operational_impact: float = Field(
        default=0.0, ge=0.0, le=100.0,
        description="Operational impact score (0-100)"
    )

    # Classification
    alert_type: Literal[
        "line_down", "yield_drop", "defect_spike", 
        "recurring_failure", "eco_deviation", "media_evidence",
        "station_alarm", "shift_handoff"
    ] = Field(..., description="Alert category")

    # Content
    title: str = Field(..., description="Alert headline")
    description: str = Field(..., description="Detailed description")
    recommendation: Optional[str] = Field(None, description="Suggested action")

    # Context
    affected_station: Optional[StationType] = Field(None)
    affected_line: Optional[str] = Field(None)
    affected_component: Optional[str] = Field(None)
    affected_model: Optional[str] = Field(None)

    # Evidence
    evidence_events: List[str] = Field(default_factory=list, description="Supporting event IDs")
    has_media_evidence: bool = Field(default=False)
    media_paths: List[str] = Field(default_factory=list)

    # Routing
    target_groups: List[str] = Field(default_factory=list, description="Alert target groups")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class TimelineEvent(BaseModel):
    """
    Single entry in an incident timeline.
    Used for chronological reconstruction of events.
    """
    timestamp: datetime = Field(...)
    event_type: Literal[
        "notification", "detection", "confirmation", 
        "impact", "escalation", "action", "resolution",
        "rework", "hold", "release"
    ] = Field(...)
    description: str = Field(...)
    actor: Optional[str] = Field(None, description="Person/system responsible")
    station: Optional[StationType] = Field(None)
    component: Optional[str] = Field(None)
    line: Optional[str] = Field(None)

    # Links
    source_event_id: Optional[str] = Field(None)
    source_message_id: Optional[str] = Field(None)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class IncidentTimeline(BaseModel):
    """
    Complete timeline for an incident.
    """
    incident_id: str = Field(...)
    timeline_id: str = Field(...)
    events: List[TimelineEvent] = Field(default_factory=list)

    # Derived metrics
    time_to_detect_minutes: Optional[float] = Field(None)
    time_to_respond_minutes: Optional[float] = Field(None)
    time_to_resolve_minutes: Optional[float] = Field(None)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class ExportPackage(BaseModel):
    """
    Complete export package for SMTinel integration.
    """
    package_id: str = Field(...)
    generated_at: datetime = Field(...)

    incidents: List[CorrelatedIncident] = Field(default_factory=list)
    timelines: List[IncidentTimeline] = Field(default_factory=list)
    alerts: List[SentinelAlert] = Field(default_factory=list)

    # Metadata
    event_count: int = Field(default=0)
    incident_count: int = Field(default=0)
    alert_count: int = Field(default=0)

    # Filters applied
    time_range_start: Optional[datetime] = Field(None)
    time_range_end: Optional[datetime] = Field(None)
    filters: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
