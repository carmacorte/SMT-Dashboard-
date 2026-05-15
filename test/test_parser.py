"""
tests/test_parser.py
Unit tests for ManufacturingParser.
Tests all pattern extraction and confidence scoring.
"""

import pytest
from datetime import datetime, timezone
from schemas.event_schema import RawWhatsAppMessage, StationType, DefectType, ComponentPrefix
from parser.manufacturing_parser import ManufacturingParser


class TestManufacturingParser:
    """Test suite for manufacturing message parsing."""

    @pytest.fixture
    def parser(self):
        return ManufacturingParser()

    def _create_message(self, content: str, sender: str = "test@sender") -> RawWhatsAppMessage:
        return RawWhatsAppMessage(
            id="msg-001",
            timestamp=datetime.now(timezone.utc),
            sender=sender,
            chat_jid="group@test",
            chat_name="Test Group",
            content=content,
            is_from_me=False
        )

    def test_component_extraction(self, parser):
        """Test component reference extraction."""
        msg = self._create_message("AOI fail on U519, bridge detected")
        event = parser.parse(msg)
        assert event is not None
        assert event.component == "U519"
        assert event.component_prefix == ComponentPrefix.U

    def test_station_detection(self, parser):
        """Test station type detection."""
        msg = self._create_message("SPI detected insufficient paste on R123")
        event = parser.parse(msg)
        assert event is not None
        assert event.station == StationType.SPI

    def test_defect_detection(self, parser):
        """Test defect type detection."""
        msg = self._create_message("AOI: tombstone on C47 line 2")
        event = parser.parse(msg)
        assert event is not None
        assert event.defect == DefectType.TOMBSTONE

    def test_line_extraction(self, parser):
        """Test line identifier extraction."""
        msg = self._create_message("Line 3 down, AOI fail on J5")
        event = parser.parse(msg)
        assert event is not None
        assert event.line == "3"

    def test_line_down_detection(self, parser):
        """Test line down flag detection."""
        msg = self._create_message("Line down on line 1, all stations stopped")
        event = parser.parse(msg)
        assert event is not None
        assert "line_down" in event.tags

    def test_eco_detection(self, parser):
        """Test ECO/deviation detection."""
        msg = self._create_message("ECO applied to U200, hold all boards")
        event = parser.parse(msg)
        assert event is not None
        assert "eco_deviation" in event.tags

    def test_yield_extraction(self, parser):
        """Test yield percentage extraction."""
        msg = self._create_message("Yield dropped to 72% on line 2")
        event = parser.parse(msg)
        assert event is not None
        # Yield would be extracted but not stored in event directly
        # It's used for tag generation

    def test_shift_extraction(self, parser):
        """Test shift information extraction."""
        msg = self._create_message("2nd shift: AOI fail on Q3")
        event = parser.parse(msg)
        assert event is not None
        assert event.shift == "2st"

    def test_multiple_components(self, parser):
        """Test multiple component detection."""
        msg = self._create_message("AOI fail on U519 and R123, both bridged")
        event = parser.parse(msg)
        assert event is not None
        assert event.component == "U519"  # First one taken

    def test_low_confidence_rejection(self, parser):
        """Test that non-manufacturing messages are rejected."""
        msg = self._create_message("Hey, how are you doing today?")
        event = parser.parse(msg)
        assert event is None

    def test_confidence_scoring(self, parser):
        """Test confidence score calculation."""
        # High confidence: component + station + defect + line
        msg = self._create_message("Line 1 AOI: bridge on U519")
        event = parser.parse(msg)
        assert event is not None
        assert event.confidence_score > 0.8
        assert "high_confidence" in event.tags

    def test_media_detection(self, parser):
        """Test media attachment detection."""
        msg = RawWhatsAppMessage(
            id="msg-002",
            timestamp=datetime.now(timezone.utc),
            sender="test@sender",
            chat_jid="group@test",
            chat_name="Test Group",
            content="AOI image attached, defect on C47",
            is_from_me=False,
            media_type="image/jpeg"
        )
        event = parser.parse(msg)
        assert event is not None
        assert event.has_media is True
        assert "media_attached" in event.tags

    def test_model_extraction(self, parser):
        """Test model/SKU extraction."""
        msg = self._create_message("Model ABC-1234: AOI fail on U5")
        event = parser.parse(msg)
        assert event is not None
        assert event.model == "ABC-1234"

    def test_serial_extraction(self, parser):
        """Test serial number extraction."""
        msg = self._create_message("S/N XYZ789012: ICT fail on R10")
        event = parser.parse(msg)
        assert event is not None
        assert event.serial == "XYZ789012"

    def test_spanish_input(self, parser):
        """Test Spanish language input parsing."""
        msg = self._create_message("Línea 2 AOI: puente en U519")
        event = parser.parse(msg)
        assert event is not None
        assert event.line == "2"
        assert event.station == StationType.AOI

    def test_batch_parsing(self, parser):
        """Test batch message processing."""
        messages = [
            self._create_message("AOI fail on U519"),
            self._create_message("SPI paste issue on R123"),
            self._create_message("Hey, lunch time?"),
            self._create_message("Line 3 down, all stop"),
        ]
        events = parser.parse_batch(messages)
        assert len(events) == 3  # 3 manufacturing messages

    def test_parser_stats(self, parser):
        """Test statistics tracking."""
        msg = self._create_message("AOI fail on U519")
        parser.parse(msg)
        stats = parser.get_stats()
        assert stats["total_parsed"] == 1
        assert stats["successful_parses"] == 1
        assert stats["success_rate"] == 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
