# TraceOps Live 🏭

## Manufacturing Intelligence Layer for SMT Production

TraceOps Live is a local-first, privacy-preserving manufacturing intelligence system that transforms unstructured WhatsApp messages from production lines into structured, actionable operational data for the SMTinel Dashboard.

### Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  WhatsApp MCP   │────▶│  TraceOps Live   │────▶│ SMTinel Dash    │
│  Bridge (SQLite)│     │  Intelligence    │     │  (JSON Feed)    │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
   ┌─────────┐          ┌──────────┐          ┌──────────┐
   │ INGEST  │          │  PARSE   │          │ CORRELATE│
   │ SQLite  │          │  NLP     │          │ Cluster  │
   │ Reader  │          │  Regex   │          │ Engine   │
   └─────────┘          └──────────┘          └──────────┘
        │                     │                     │
        ▼                     ▼                     ▼
   ┌─────────┐          ┌──────────┐          ┌──────────┐
   │ TIMELINE│          │ SENTINEL │          │  EXPORT  │
   │ Builder │          │ Severity │          │  JSON    │
   │         │          │ Engine   │          │  + Sync  │
   └─────────┘          └──────────┘          └──────────┘
```

### Pipeline Flow

1. **INGEST** → Poll WhatsApp `messages.db` every 5s, detect new messages
2. **PARSE** → Extract components (U519), stations (AOI), defects (bridge), lines, models
3. **CORRELATE** → Cluster related events into incidents (time + station + component proximity)
4. **TIMELINE** → Reconstruct chronological sequence: detection → confirmation → impact → resolution
5. **SENTINEL** → Score severity, escalation urgency, recurrence risk, operational impact
6. **EXPORT** → Generate JSON feeds for SMTinel Dashboard + optional Supabase sync

### Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your paths

# 3. Run the pipeline
python pipeline_orchestrator.py

# 4. Or run the API server
uvicorn api.main:app --host 127.0.0.1 --port 8081
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/status` | GET | System status & metrics |
| `/incidents` | GET | List incidents (with filters) |
| `/incidents/{id}` | GET | Get incident details |
| `/incidents/{id}/status` | POST | Update incident status |
| `/alerts` | GET | List alerts (severity sorted) |
| `/alerts/{id}` | GET | Get alert details |
| `/timelines/{id}` | GET | Get incident timeline |
| `/export` | POST | Export package to JSON |
| `/export/summary` | GET | Export incident summary |
| `/export/alerts` | GET | Export alert feed |
| `/stats` | GET | Pipeline statistics |
| `/stats/recurrence` | GET | Recurrence analytics |
| `/ingest/poll` | POST | Manual poll trigger |

### Configuration

All settings via environment variables:

```env
# Database
TRACEOPS_DB_PATH=./data/traceops_live.db
WHATSAPP_DB_PATH=../whatsapp-bridge/store/messages.db

# API
TRACEOPS_API_HOST=127.0.0.1
TRACEOPS_API_PORT=8081

# Polling
TRACEOPS_POLL_INTERVAL=5.0
TRACEOPS_BATCH_SIZE=50

# Correlation
TRACEOPS_CORR_WINDOW=30
TRACEOPS_CORR_MIN=2

# Features
TRACEOPS_AUTO_ALERTS=false
TRACEOPS_SUPABASE=false
```

### Detection Capabilities

**Stations:** SPI, AOI, ICT, FCT, 5DX, X-RAY, REFLOW, PTH, PRESSFIT, ASSEMBLY

**Defects:** bridge, short, open, missing, tombstone, polarity, misalignment, void, solder_splash, lifted_lead, coplanarity

**Components:** U (IC), R (resistor), C (capacitor), J (connector), L (inductor), Q (transistor), D (diode), Y (crystal), F (fuse), TP (test point)

### License

MIT
