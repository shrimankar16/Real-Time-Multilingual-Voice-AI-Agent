# Setup Guide

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Redis (optional, via Docker)
- Groq API key (get free at https://console.groq.com)

### 1. Environment Configuration

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your GROQ_API_KEY
# Get your free API key from: https://console.groq.com
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the backend server
uvicorn app.main:app --reload --port 8000
```

The backend will:
- Start on http://localhost:8000
- Automatically create and seed the SQLite database
- Create 3 sample doctors with 7 days of appointment slots

### 3. Frontend Setup

```bash
cd frontend/nextjs-ui

# Install dependencies (if not already done)
npm install

# Run the development server
npm run dev
```

The frontend will start on http://localhost:3000

### 4. Optional: Redis & Celery

For session persistence and background campaigns:

```bash
# Start Redis using Docker
docker run -d -p 6379:6379 redis:alpine

# In a new terminal, start Celery worker
cd backend
celery -A celery_worker worker --loglevel=info
```

## Docker Setup (Alternative)

Run everything with Docker Compose:

```bash
# Make sure .env file has your GROQ_API_KEY
docker-compose up --build
```

This will start:
- Backend on http://localhost:8000
- Frontend on http://localhost:3000
- Redis on localhost:6379
- Celery worker for background tasks

## Verification

1. Backend health check: http://localhost:8000/api/health
2. API docs: http://localhost:8000/docs
3. Frontend: http://localhost:3000

## Troubleshooting

### Backend Issues

**Import errors:**
```bash
# Make sure you're in the backend directory and venv is activated
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

**Database errors:**
```bash
# Delete and recreate the database
rm backend/clinic.db
# Restart the backend - it will auto-seed
```

**Whisper model download:**
The first run will download the Whisper model (~150MB for 'base'). This is normal and only happens once.

### Frontend Issues

**Module not found:**
```bash
cd frontend/nextjs-ui
rm -rf node_modules package-lock.json
npm install
```

**Port already in use:**
```bash
# Use a different port
npm run dev -- -p 3001
```

### Redis Connection Issues

If Redis is not available, the system will automatically fall back to in-memory session storage. This is fine for development but sessions won't persist across server restarts.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/converse` | Voice conversation (audio in/out) |
| POST | `/api/converse/text` | Text conversation |
| GET | `/api/doctors` | List all doctors |
| GET | `/api/slots/{doctor_id}` | Available slots |
| GET | `/api/appointments` | All appointments |
| POST | `/api/campaigns/trigger` | Trigger campaign |
| GET | `/api/health` | Health check |

## Testing the Voice Agent

1. Open http://localhost:3000
2. Click the microphone button
3. Say: "I want to book an appointment with Dr. Sharma"
4. The agent will guide you through the booking process

You can also test in Hindi or Tamil - the system will auto-detect the language!

## Next Steps

- Add your actual Groq API key to `.env`
- Customize doctors and slots in `backend/app/database.py`
- Modify the UI in `frontend/nextjs-ui/src/app/page.tsx`
- Add more tools in `backend/tools/appointment_tools.py`
