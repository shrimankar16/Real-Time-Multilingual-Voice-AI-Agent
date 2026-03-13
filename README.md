# Real-Time Multilingual Voice AI Agent
### Clinical Appointment Booking System

A real-time voice AI agent that helps patients book, reschedule, and cancel doctor appointments through natural speech in **English**, **Hindi**, and **Tamil**.

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│                  Next.js UI                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
│  │ Voice    │ │ Transcript│ │ Dashboard        │ │
│  │ Panel    │ │ Log      │ │ (Doctors/Slots)  │ │
│  └────┬─────┘ └──────────┘ └──────────────────┘ │
└───────┼─────────────────────────────────────────┘
        │ Audio / Text (HTTP)
        ▼
┌─────────────────────────────────────────────────┐
│              FastAPI Backend                      │
│                                                   │
│  ┌─────────┐   ┌──────────┐   ┌──────────────┐  │
│  │  STT    │──▶│  Agent   │──▶│    TTS       │  │
│  │(Whisper)│   │(LangChain│   │ (edge-tts)   │  │
│  └─────────┘   │ + Tools) │   └──────────────┘  │
│                └────┬─────┘                      │
│                     │ Tool Calls                  │
│          ┌──────────┼──────────┐                 │
│          ▼          ▼          ▼                  │
│    ┌──────────┐ ┌───────┐ ┌────────┐            │
│    │  SQLite  │ │ Redis │ │ Celery │            │
│    │(persist) │ │(session│ │(campaigns)          │
│    └──────────┘ └───────┘ └────────┘            │
└─────────────────────────────────────────────────┘
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js (TypeScript) |
| Backend | Python + FastAPI |
| Agent | LangChain with OpenAI function-calling |
| STT | faster-whisper (local) |
| TTS | edge-tts (free Microsoft API) |
| Database | SQLite + SQLAlchemy |
| Session Memory | Redis (optional, falls back to in-memory) |
| Background Jobs | Celery + Redis (optional) |
| Language Detection | langdetect + deep-translator |

---

## Setup Instructions

### Prerequisites
- Python 3.11+
- Node.js 18+
- Groq API key (free)
- Redis (optional — system works without it)

### 1. Clone & Configure

```bash
cd voice-ai-agent
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

### 2. Backend Setup

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Start Backend

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

The database will be automatically seeded with 3 doctors and 7 days of slots on first run.

### 4. Frontend Setup

```bash
cd frontend/nextjs-ui
npm install
npm run dev
```

Open **http://localhost:3000** in your browser.

### 5. (Optional) Redis & Celery

```bash
# Start Redis
docker run -d -p 6379:6379 redis:alpine

# Start Celery worker (from backend/)
celery -A celery_worker worker --loglevel=info
```

---

## Features

### 1. Voice Conversation Agent
- Real-time speech-to-text using faster-whisper
- LangChain tool-calling agent with 5 scheduling tools
- Text-to-speech response via edge-tts
- **Barge-in support**: interrupting the agent stops playback

### 2. Multilingual Support
- Automatic language detection (English, Hindi, Tamil)
- Whisper detects spoken language; agent responds in same language
- Language preference persisted for returning patients

### 3. Agent Tools
| Tool | Description |
|------|------------|
| `get_available_slots` | Query doctor availability |
| `book_appointment` | Book with conflict detection |
| `cancel_appointment` | Cancel and free the slot |
| `reschedule_appointment` | Move to a new slot |
| `get_patient_history` | Retrieve past appointments |

### 4. Conflict Management
- Prevents double-booking and past-date booking
- Suggests alternative slots when conflicts occur
- Example: *"Dr. Sharma is booked at 5 PM. Next available: 5:30 PM."*

### 5. Contextual Memory

| Layer | Store | Purpose |
|-------|-------|---------|
| Session | Redis (TTL 30 min) | Conversation state, pending booking |
| Persistent | SQLite | Patient preferences, appointment history, language |

Falls back to in-memory dict if Redis is unavailable.

### 6. Outbound Campaigns
- **Reminder campaign**: Sends reminders for appointments in next 24h
- **Follow-up campaign**: Contacts patients from past 7 days
- Triggered via API or Celery background tasks

---

## Latency Measurement

Every request logs pipeline latencies:

```
┌────────────────────────┬─────────────┐
│ Stage                  │ Target      │
├────────────────────────┼─────────────┤
│ Speech-to-Text (STT)   │ ~100-200ms  │
│ Language Detection      │ ~5-10ms     │
│ Agent Reasoning (LLM)  │ ~150-300ms  │
│ Text-to-Speech (TTS)   │ ~50-100ms   │
│ TOTAL                  │ <450ms      │
└────────────────────────┴─────────────┘
```

Latency is measured using `perf_counter` and returned in every API response. The frontend displays color-coded bars and a target indicator.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/converse` | Audio in → audio + text out |
| POST | `/api/converse/text` | Text in → text + audio out |
| GET | `/api/doctors` | List all doctors |
| GET | `/api/slots/{id}` | Available slots for doctor |
| GET | `/api/appointments` | All appointments |
| POST | `/api/campaigns/trigger` | Trigger campaign |
| GET | `/api/health` | Health check |

---

## Horizontal Scalability Design

```
                    ┌──────────────┐
                    │ Load Balancer│
                    └──────┬───────┘
            ┌──────────────┼──────────────┐
            ▼              ▼              ▼
     ┌────────────┐ ┌────────────┐ ┌────────────┐
     │ FastAPI    │ │ FastAPI    │ │ FastAPI    │
     │ Worker 1   │ │ Worker 2   │ │ Worker 3   │
     └─────┬──────┘ └─────┬──────┘ └─────┬──────┘
           └───────────────┼───────────────┘
                    ┌──────┴───────┐
                    │ Redis Cluster│ (shared session memory)
                    └──────┬───────┘
                    ┌──────┴───────┐
                    │  PostgreSQL  │ (replace SQLite)
                    └──────────────┘
```

**Scaling strategy:**
- Replace SQLite → PostgreSQL for concurrent writes
- Redis Cluster for shared session memory
- Multiple uvicorn workers behind nginx/Traefik
- Celery workers scale independently for campaigns
- Whisper model can be offloaded to GPU workers

---

## Trade-offs & Decisions

| Decision | Rationale |
|----------|-----------|
| HTTP instead of WebSocket | Simpler, more reliable for turn-based conversation |
| edge-tts over Coqui | Zero setup, multilingual, very fast |
| SQLite over PostgreSQL | Simple local setup; designed for easy swap |
| Redis optional | System works without Redis via in-memory fallback |
| gpt-4o-mini default | Cost-effective with good tool-calling ability |

## Known Limitations
- STT latency depends on Whisper model size (base ~150ms, large ~600ms)
- LLM latency depends on OpenAI API response time
- SQLite doesn't support concurrent writes well (swap to PostgreSQL for production)
- edge-tts requires internet connection
- WebM audio format from browser may need conversion for some Whisper builds

---

## Project Structure

```
voice-ai-agent/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI routes + voice pipeline
│   │   ├── config.py        # Environment configuration
│   │   ├── database.py      # SQLAlchemy + seeding
│   │   └── models.py        # Database models
│   ├── agents/
│   │   └── voice_agent.py   # LangChain tool-calling agent
│   ├── tools/
│   │   └── appointment_tools.py  # 5 scheduling tools
│   ├── pipeline/
│   │   ├── stt.py           # Speech-to-Text
│   │   ├── tts.py           # Text-to-Speech
│   │   └── language.py      # Detection & translation
│   ├── memory/
│   │   └── memory_manager.py # Redis + SQLite memory
│   ├── scheduling/
│   │   └── campaigns.py     # Outbound campaigns
│   ├── latency/
│   │   └── tracker.py       # Pipeline timing
│   ├── celery_worker.py     # Background jobs
│   └── requirements.txt
├── frontend/nextjs-ui/
│   └── src/
│       ├── app/
│       │   ├── page.tsx      # Main page
│       │   ├── layout.tsx    # Root layout
│       │   └── globals.css   # Design system
│       ├── components/
│       │   ├── VoicePanel.tsx
│       │   ├── TranscriptLog.tsx
│       │   ├── ReasoningLog.tsx
│       │   ├── LatencyPanel.tsx
│       │   └── Dashboard.tsx
│       └── lib/
│           └── api.ts        # API client
├── README.md
├── .env.example
└── docker-compose.yml
```

---

