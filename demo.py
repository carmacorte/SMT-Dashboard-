"""
demo.py
Demonstration script for TraceOps Live.
Simulates WhatsApp messages and runs the complete pipeline.
"""

import asyncio
from datetime import datetime, timezone, timedelta
from pathlib import Path

from config.settings import settings
from config.logging_config import setup_logging
from schemas.event_schema import RawWhatsAppMessage
from parser.manufacturing_parser import ManufacturingParser
from correlation.incident_cluster import IncidentClusterer
from correlation.timeline_builder import TimelineBuilder
from sentinel.severity_engine import SeverityEngine
from storage.incident_memory import IncidentMemory
from export.smtinel_exporter import SMTinelExporter


# Demo messages simulating real production line WhatsApp traffic
DEMO_MESSAGES = [
    # Scenario 1: AOI defect detection
    "07:12 Line 2 AOI: bridge detected on U519, 1st shift",
    "07:18 Confirmed, U519 bridge on line 2. Yield dropped to 72%",
    "07:25 Line 2 stopped for rework. All boards on hold.",
    "07:41 Xray confirmation: U519 solder bridge confirmed",
    "08:03 Rework completed on line 2. U519 fixed.",
    "08:15 Line 2 released. Yield back to 98%.",

    # Scenario 2: SPI paste issue
    "09:30 SPI on line 1: insufficient paste on R123",
    "09:35 R123 open circuit detected at ICT",
    "09:42 Stencil cleaned. Paste volume restored.",

    # Scenario 3: Recurring tombstone
    "10:00 Line 3 AOI: tombstone on C47 again",
    "10:05 Same C47 tombstone, 3rd time this week",
    "10:15 ECO deviation logged for C47 placement",

    # Scenario 4: Non-manufacturing (should be filtered)
    "10:30 Hey, anyone want coffee?",
    "10:31 Meeting at 11 in conference room B",

    # Scenario 5: Multi-station impact
    "11:00 Line 1 AOI: misalignment on J5 connector",
    "11:05 ICT fail on J5, same board",
    "11:12 FCT also failing on J5 line 1",
    "11:20 All stations on line 1 stopped for J5 issue",

    # Scenario 6: Media evidence
    "12:00 AOI image attached, polarity wrong on D23",
    "12:05 Confirmed D23 reversed. See attached image.",

    # Scenario 7: Model-specific issue
    "13:00 Model XYZ-9000: void detected on Q3 at XRAY",
    "13:10 Same Q3 void on next board, model XYZ-9000",
    "13:15 Reflow profile adjusted for XYZ-9000",
]


def create_demo_messages() -> list[RawWhatsAppMessage]:
    """Create demo RawWhatsAppMessage objects."""
    base_time = datetime.now(timezone.utc).replace(hour=7, minute=0, second=0, microsecond=0)
    messages = []

    for i, content in enumerate(DEMO_MESSAGES):
        # Parse time from content if present
        msg_time = base_time + timedelta(minutes=i * 5)

        msg = RawWhatsAppMessage(
            id=f"demo-msg-{i:03d}",
            timestamp=msg_time,
            sender="operator@line2" if "line 2" in content.lower() else "operator@line1",
            chat_jid="production-group@whatsapp",
            chat_name="Production Alerts",
            content=content,
            is_from_me=False,
            media_type="image/jpeg" if "image" in content.lower() else None
        )
        messages.append(msg)

    return messages


async def run_demo():
    """Run complete pipeline demonstration."""
    print("=" * 70)
    print("TRACEOPS LIVE - DEMONSTRATION")
    print("=" * 70)

    # Setup
    setup_logging()

    # Initialize modules
    parser = ManufacturingParser()
    clusterer = IncidentClusterer()
    timeline_builder = TimelineBuilder()
    incident_memory = IncidentMemory()
    severity_engine = SeverityEngine(incident_memory)
    exporter = SMTinelExporter()

    # Create demo messages
    print("\n[1] CREATING DEMO MESSAGES")
    print("-" * 70)
    messages = create_demo_messages()
    print(f"Created {len(messages)} simulated WhatsApp messages")

    # Show sample messages
    for msg in messages[:5]:
        print(f"  [{msg.timestamp.strftime('%H:%M')}] {msg.content[:60]}...")

    # Step 2: PARSE
    print("\n[2] PARSING MESSAGES → MANUFACTURING EVENTS")
    print("-" * 70)
    events = parser.parse_batch(messages)
    print(f"Parsed {len(events)} manufacturing events from {len(messages)} messages")
    print(f"Success rate: {parser.get_stats()['success_rate']:.1%}")

    # Show parsed events
    for event in events[:8]:
        print(f"  → [{event.confidence_score:.2f}] {event.station.value if event.station else 'N/A'} | "
              f"{event.component or 'N/A'} | {event.defect.value if event.defect else 'N/A'} | "
              f"Line {event.line or 'N/A'} | {event.tags}")

    # Step 3: CORRELATE
    print("\n[3] CORRELATING EVENTS → INCIDENTS")
    print("-" * 70)
    incidents, _ = clusterer.process_events(events)
    print(f"Clustered into {len(incidents)} incidents")

    for inc in incidents:
        print(f"  → {inc.incident_id}: {inc.event_count} events, "
              f"severity={inc.max_severity.value}, "
              f"station={inc.primary_station.value if inc.primary_station else 'N/A'}, "
              f"component={inc.primary_component or 'N/A'}")

    # Step 4: TIMELINE
    print("\n[4] BUILDING TIMELINES")
    print("-" * 70)
    timelines = []
    for inc in incidents:
        inc_events = [e for e in events if e.event_id in inc.event_ids]
        if inc_events:
            timeline = timeline_builder.build_timeline(inc.incident_id, inc_events)
            timelines.append(timeline)
            print(f"  → {timeline.timeline_id}: {len(timeline.events)} events, "
                  f"TTD={timeline.time_to_detect_minutes:.1f}m" if timeline.time_to_detect_minutes else "N/A")

    # Step 5: SCORE
    print("\n[5] SEVERITY SCORING → ALERTS")
    print("-" * 70)
    alerts = severity_engine.process_incidents(incidents)
    print(f"Generated {len(alerts)} alerts")

    for alert in alerts:
        print(f"  → [{alert.severity.value.upper()}] {alert.title}")
        print(f"      Escalation: {alert.escalation_score:.1f} | "
              f"Recurrence: {alert.recurrence_score:.1f} | "
              f"Impact: {alert.operational_impact:.1f}")
        if alert.recommendation:
            print(f"      💡 {alert.recommendation}")

    # Step 6: EXPORT
    print("\n[6] EXPORTING TO SMTINEL FORMAT")
    print("-" * 70)
    package = exporter.create_package(incidents, timelines, alerts)
    filepath = exporter.export_json(package, filename="demo_export.json")
    print(f"Exported to: {filepath}")

    # Also export summaries
    summary_path = exporter.export_incident_summary(incidents, filename="demo_summary.json")
    alert_path = exporter.export_alert_feed(alerts, filename="demo_alerts.json")
    print(f"Summary: {summary_path}")
    print(f"Alerts:  {alert_path}")

    # Final stats
    print("\n" + "=" * 70)
    print("DEMO COMPLETE")
    print("=" * 70)
    print(f"Messages processed: {len(messages)}")
    print(f"Events extracted:   {len(events)}")
    print(f"Incidents created:  {len(incidents)}")
    print(f"Timelines built:    {len(timelines)}")
    print(f"Alerts generated:   {len(alerts)}")
    print(f"Export files:       3")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_demo())
