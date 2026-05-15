"""
parser/manufacturing_parser.py
Manufacturing NLP Parser for WhatsApp messages.
Extracts structured SMT data from unstructured text using regex patterns.
No cloud AI - all local processing.
"""

import re
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Tuple, Set
from dataclasses import dataclass

from config.logging_config import get_parser_logger
from schemas.event_schema import (
    RawWhatsAppMessage, ParsedManufacturingEvent,
    StationType, DefectType, ComponentPrefix
)


logger = get_parser_logger()


# ============================================================
# REGEX PATTERNS - Industrial-grade pattern matching
# ============================================================

# Component patterns: U519, R123, C47, J5, L2, Q3, etc.
COMPONENT_PATTERN = re.compile(
    r'\b([URCJLQDFYTP]{1,2})(\d{1,4}[A-Z]?)\b',
    re.IGNORECASE
)

# Station keywords with context
STATION_PATTERNS: Dict[StationType, List[str]] = {
    StationType.SPI: [
        r'\bSPI\b', r'\bsolder paste inspection\b', r'\bpaste print\b',
        r'\bstencil\b', r'\bprint quality\b'
    ],
    StationType.AOI: [
        r'\bAOI\b', r'\boptical inspection\b', r'\bvisual inspection\b',
        r'\binspection\b.*\bfail', r'\bdefect detected\b'
    ],
    StationType.ICT: [
        r'\bICT\b', r'\bin.circuit test\b', r'\btest fixture\b',
        r'\belectrical test\b', r'\bcircuit test\b'
    ],
    StationType.FCT: [
        r'\bFCT\b', r'\bfunctional test\b', r'\bfunction test\b',
        r'\bpower up\b', r'\bfunctional failure\b'
    ],
    StationType.FIVE_DX: [
        r'\b5DX\b', r'\b5-DX\b', r'\bfive dx\b'
    ],
    StationType.XRAY: [
        r'\bX[\s\-]?RAY\b', r'\bxray\b', r'\bx-ray\b',
        r'\bradiographic\b', r'\bBGA inspection\b'
    ],
    StationType.REFLOW: [
        r'\bREFLOW\b', r'\breflow oven\b', r'\boven\b.*\bprofile\b',
        r'\bthermal profile\b', r'\b soldering\b.*\boven\b'
    ],
    StationType.PTH: [
        r'\bPTH\b', r'\bthrough hole\b', r'\bwave solder\b',
        r'\bdip soldering\b'
    ],
    StationType.PRESSFIT: [
        r'\bPRESS\s*FIT\b', r'\bpress-fit\b', r'\bpressfit\b',
        r'\bcompliant pin\b'
    ],
    StationType.ASSEMBLY: [
        r'\bASSEMBLY\b', r'\bassembly line\b', r'\bpick and place\b',
        r'\bmounter\b', r'\bplacement\b'
    ],
}

# Defect patterns
DEFECT_PATTERNS: Dict[DefectType, List[str]] = {
    DefectType.BRIDGE: [
        r'\bbridge\w*\b', r'\bbridging\b', r'\bsolder bridge\b',
        r'\bshort\b.*\bsolder\b'
    ],
    DefectType.SHORT: [
        r'\bshort\w*\b', r'\bshort circuit\b'
    ],
    DefectType.OPEN: [
        r'\bopen\b', r'\bopen circuit\b', r'\bno solder\b',
        r'\bunsoldered\b', r'\bdry joint\b'
    ],
    DefectType.MISSING: [
        r'\bmissing\b', r'\bomitted\b', r'\bnot placed\b',
        r'\bno component\b', r'\babsent\b'
    ],
    DefectType.TOMBSTONE: [
        r'\btombston\w*\b', r'\bmanhattan\b', r'\bstanding up\b',
        r'\bvertical\b.*\bcomponent\b'
    ],
    DefectType.POLARITY: [
        r'\bpolar\w*\b', r'\breversed\b', r'\bwrong orientation\b',
        r'\bbackward\b', r'\b180\b.*\bdegrees\b'
    ],
    DefectType.MISALIGNMENT: [
        r'\bmisalign\w*\b', r'\bshifted\b', r'\boffset\b',
        r'\bskew\w*\b', r'\boff center\b', r'\bplacement error\b'
    ],
    DefectType.VOID: [
        r'\bvoid\w*\b', r'\bporosity\b', r'\bair pocket\b',
        r'\bgas pocket\b'
    ],
    DefectType.SOLDER_SPLASH: [
        r'\bsolder splash\b', r'\bsplash\b', r'\bsolder ball\b',
        r'\bsolder sphere\b'
    ],
    DefectType.LIFTED_LEAD: [
        r'\blifted\b.*\blead\b', r'\blead\b.*\blift\w*\b',
        r'\bheel crack\b', r'\bfractured lead\b'
    ],
    DefectType.COPLANARITY: [
        r'\bcoplanar\w*\b', r'\bstandoff\b', r'\bheight variation\b',
        r'\blead\b.*\bheight\b'
    ],
}

# Line patterns
LINE_PATTERN = re.compile(
    r'(?:line|línea|lnea)\s*[:#]?\s*(\d{1,2}[A-Z]?)',
    re.IGNORECASE
)

# Model/SKU patterns (alphanumeric product codes)
MODEL_PATTERN = re.compile(
    r'\b(?:model|modelo|sku|pn|part\s*number|product)[:#]?\s*([A-Z0-9\-]{4,20})\b',
    re.IGNORECASE
)

# Serial number patterns
SERIAL_PATTERN = re.compile(
    r'\b(?:serial|s/n|sn)[:#]?\s*([A-Z0-9\-]{6,20})\b',
    re.IGNORECASE
)

# Shift patterns
SHIFT_PATTERN = re.compile(
    r'\b(\d)(?:st|nd|rd|th)?\s*(?:shift|turno)\b|\b(?:first|second|third|1st|2nd|3rd)\s*shift\b',
    re.IGNORECASE
)

# Yield/quality indicators
YIELD_PATTERN = re.compile(
    r'\b(?:yield|rendimiento)\b[^0-9]{0,20}(\d{1,3}(?:\.\d{1,2})?)\s*%?',
    re.IGNORECASE
)

# Line down / stop indicators
LINE_DOWN_PATTERNS = [
    re.compile(r'\bline\s+down\b', re.IGNORECASE),
    re.compile(r'\bstop\w*\b.*\bline\b', re.IGNORECASE),
    re.compile(r'\bline\b.*\bstop\w*\b', re.IGNORECASE),
    re.compile(r'\bdown\b.*\bproduction\b', re.IGNORECASE),
    re.compile(r'\bproduction\s+halt\w*\b', re.IGNORECASE),
]

# ECO / Deviation / Hold patterns
ECO_PATTERNS = [
    re.compile(r'\bECO\b', re.IGNORECASE),
    re.compile(r'\bdeviation\b', re.IGNORECASE),
    re.compile(r'\bhold\b', re.IGNORECASE),
    re.compile(r'\bstop\s+ship\b', re.IGNORECASE),
    re.compile(r'\bquarantine\b', re.IGNORECASE),
]


@dataclass
class ParseResult:
    """Internal parse result before conversion to schema."""
    station: Optional[StationType] = None
    component: Optional[str] = None
    component_prefix: Optional[ComponentPrefix] = None
    defect: Optional[DefectType] = None
    line: Optional[str] = None
    model: Optional[str] = None
    serial: Optional[str] = None
    shift: Optional[str] = None
    yield_value: Optional[float] = None
    is_line_down: bool = False
    is_eco_deviation: bool = False
    has_media: bool = False
    confidence: float = 0.0
    matched_patterns: List[str] = None

    def __post_init__(self):
        if self.matched_patterns is None:
            self.matched_patterns = []


class ManufacturingParser:
    """
    Local NLP parser for manufacturing messages.
    Extracts SMT-specific entities using regex patterns and scoring.
    """

    def __init__(self):
        self._stats = {
            "total_parsed": 0,
            "successful_parses": 0,
            "failed_parses": 0,
            "by_station": {},
            "by_defect": {},
        }
        logger.info("ManufacturingParser initialized")

    def _extract_components(self, text: str) -> List[Tuple[str, str]]:
        """Extract component references from text."""
        matches = []
        for match in COMPONENT_PATTERN.finditer(text):
            prefix = match.group(1).upper()
            number = match.group(2).upper()
            full_ref = f"{prefix}{number}"
            matches.append((full_ref, prefix))
        return matches

    def _extract_station(self, text: str) -> Optional[Tuple[StationType, str]]:
        """Extract station type from text."""
        text_lower = text.lower()
        best_station = None
        best_pattern = None
        best_score = 0

        for station, patterns in STATION_PATTERNS.items():
            for pattern_str in patterns:
                if re.search(pattern_str, text, re.IGNORECASE):
                    # Score based on specificity (longer pattern = more specific)
                    score = len(pattern_str)
                    if score > best_score:
                        best_score = score
                        best_station = station
                        best_pattern = pattern_str

        if best_station:
            return best_station, best_pattern
        return None

    def _extract_defect(self, text: str) -> Optional[Tuple[DefectType, str]]:
        """Extract defect type from text."""
        best_defect = None
        best_pattern = None
        best_score = 0

        for defect, patterns in DEFECT_PATTERNS.items():
            for pattern_str in patterns:
                if re.search(pattern_str, text, re.IGNORECASE):
                    score = len(pattern_str)
                    if score > best_score:
                        best_score = score
                        best_defect = defect
                        best_pattern = pattern_str

        if best_defect:
            return best_defect, best_pattern
        return None

    def _extract_line(self, text: str) -> Optional[str]:
        """Extract line identifier."""
        match = LINE_PATTERN.search(text)
        if match:
            return match.group(1).upper()
        return None

    def _extract_model(self, text: str) -> Optional[str]:
        """Extract model/SKU."""
        match = MODEL_PATTERN.search(text)
        if match:
            return match.group(1).upper()
        return None

    def _extract_serial(self, text: str) -> Optional[str]:
        """Extract serial number."""
        match = SERIAL_PATTERN.search(text)
        if match:
            return match.group(1).upper()
        return None

    def _extract_shift(self, text: str) -> Optional[str]:
        """Extract shift information."""
        match = SHIFT_PATTERN.search(text)
        if match:
            shift_num = match.group(1)
            if shift_num:
                return f"{shift_num}st"
            # Handle text-based shifts
            text_lower = text.lower()
            if "first" in text_lower or "1st" in text_lower:
                return "1st"
            elif "second" in text_lower or "2nd" in text_lower:
                return "2nd"
            elif "third" in text_lower or "3rd" in text_lower:
                return "3rd"
        return None

    def _extract_yield(self, text: str) -> Optional[float]:
        """Extract yield percentage."""
        match = YIELD_PATTERN.search(text)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
        return None

    def _check_line_down(self, text: str) -> bool:
        """Check if message indicates line down."""
        for pattern in LINE_DOWN_PATTERNS:
            if pattern.search(text):
                return True
        return False

    def _check_eco_deviation(self, text: str) -> bool:
        """Check if message indicates ECO/deviation/hold."""
        for pattern in ECO_PATTERNS:
            if pattern.search(text):
                return True
        return False

    def _calculate_confidence(self, result: ParseResult) -> float:
        """
        Calculate confidence score based on extracted entities.
        
        Scoring rules:
        - Component found: +0.30
        - Station found: +0.25
        - Defect found: +0.25
        - Line found: +0.10
        - Model found: +0.05
        - Yield reported: +0.20 (manufacturing context)
        - Low yield (< 90%): +0.05 additional
        - Line down flag: +0.05 (context boost)
        - ECO flag: +0.05 (context boost)
        - Multiple components: +0.05 bonus
        """
        score = 0.0
        
        if result.component:
            score += 0.30
        if result.station:
            score += 0.25
        if result.defect:
            score += 0.25
        if result.line:
            score += 0.10
        if result.model:
            score += 0.05
        if result.yield_value is not None:
            score += 0.20
            if result.yield_value < 90.0:
                score += 0.05
        if result.is_line_down:
            score += 0.05
        if result.is_eco_deviation:
            score += 0.05
        
        return min(score, 1.0)
    def parse(self, message: RawWhatsAppMessage) -> Optional[ParsedManufacturingEvent]:
        """
        Parse a WhatsApp message into a structured manufacturing event.

        Args:
            message: RawWhatsAppMessage from the ingestor

        Returns:
            ParsedManufacturingEvent or None if no manufacturing content detected
        """
        self._stats["total_parsed"] += 1

        text = message.content or ""
        if not text.strip():
            return None

        result = ParseResult()

        # Extract entities
        components = self._extract_components(text)
        if components:
            # Use first component as primary
            result.component = components[0][0]
            prefix = components[0][1]
            try:
                result.component_prefix = ComponentPrefix(prefix)
            except ValueError:
                pass
            if len(components) > 1:
                result.matched_patterns.append(f"multiple_components:{len(components)}")

        station_result = self._extract_station(text)
        if station_result:
            result.station = station_result[0]
            result.matched_patterns.append(f"station:{station_result[1]}")

        defect_result = self._extract_defect(text)
        if defect_result:
            result.defect = defect_result[0]
            result.matched_patterns.append(f"defect:{defect_result[1]}")

        result.line = self._extract_line(text)
        result.model = self._extract_model(text)
        result.serial = self._extract_serial(text)
        result.shift = self._extract_shift(text)
        result.yield_value = self._extract_yield(text)
        result.is_line_down = self._check_line_down(text)
        result.is_eco_deviation = self._check_eco_deviation(text)
        result.has_media = message.media_type is not None

        # Calculate confidence
        result.confidence = self._calculate_confidence(result)

        # Skip if confidence too low (not manufacturing related)
        if result.confidence < 0.15:
            self._stats["failed_parses"] += 1
            return None

        self._stats["successful_parses"] += 1

        # Update stats
        if result.station:
            self._stats["by_station"][result.station.value] =                 self._stats["by_station"].get(result.station.value, 0) + 1
        if result.defect:
            self._stats["by_defect"][result.defect.value] =                 self._stats["by_defect"].get(result.defect.value, 0) + 1

        # Generate tags
        tags = []
        if result.is_line_down:
            tags.append("line_down")
        if result.is_eco_deviation:
            tags.append("eco_deviation")
        if result.yield_value is not None and result.yield_value < 90:
            tags.append("low_yield")
        if result.has_media:
            tags.append("media_attached")
        if result.confidence > 0.8:
            tags.append("high_confidence")

        # Build event
        event = ParsedManufacturingEvent(
            event_id=str(uuid.uuid4()),
            source_message_id=message.id,
            timestamp=message.timestamp,
            sender=message.sender_name or message.sender,
            group=message.chat_name or message.chat_jid,
            raw_message=text,
            station=result.station,
            component=result.component,
            component_prefix=result.component_prefix,
            defect=result.defect,
            line=result.line,
            model=result.model,
            serial=result.serial,
            shift=result.shift,
            confidence_score=result.confidence,
            has_media=result.has_media,
            media_count=1 if result.has_media else 0,
            tags=tags
        )

        logger.info(
            f"Parsed event: {event.event_id} "
            f"[station={event.station.value if event.station else None}, "
            f"component={event.component}, "
            f"defect={event.defect.value if event.defect else None}, "
            f"confidence={event.confidence_score:.2f}]",
            extra={
                "event_id": event.event_id,
                "station": event.station.value if event.station else None,
                "component": event.component,
                "defect": event.defect.value if event.defect else None,
                "confidence": event.confidence_score,
            }
        )

        return event

    def parse_batch(self, messages: List[RawWhatsAppMessage]) -> List[ParsedManufacturingEvent]:
        """Parse multiple messages in batch."""
        events = []
        for msg in messages:
            event = self.parse(msg)
            if event:
                events.append(event)

        logger.info(f"Batch parse: {len(events)}/{len(messages)} messages converted to events")
        return events

    def get_stats(self) -> Dict[str, any]:
        """Return parser statistics."""
        return {
            **self._stats,
            "success_rate": (
                self._stats["successful_parses"] / self._stats["total_parsed"]
                if self._stats["total_parsed"] > 0 else 0.0
            ),
        }

    def reset_stats(self):
        """Reset parser statistics."""
        self._stats = {
            "total_parsed": 0,
            "successful_parses": 0,
            "failed_parses": 0,
            "by_station": {},
            "by_defect": {},
        }


# Singleton instance
parser = ManufacturingParser()
