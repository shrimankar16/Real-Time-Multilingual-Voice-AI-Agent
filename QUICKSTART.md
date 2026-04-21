# 🚀 Quick Start Guide

Get your Voice AI Agent running in 3 simple steps!

## Step 1: Get Your API Key (2 minutes)

1. Go to https://console.groq.com
2. Sign up for a free account
3. Create an API key
4. Copy the key (starts with `gsk_...`)

## Step 2: Configure (1 minute)

1. Open the `.env` file in this directory
2. Replace `your_groq_api_key_here` with your actual API key:
   ```
   GROQ_API_KEY=gsk_your_actual_key_here
   ```
3. Save the file

## Step 3: Run (1 command)

Double-click `start-all.bat` or run in terminal:
```bash
start-all.bat
```

This will:
- ✅ Create Python virtual environment (first time only)
- ✅ Install all dependencies (first time only)
- ✅ Start the backend server on http://localhost:8000
- ✅ Start the frontend on http://localhost:3000
- ✅ Seed the database with sample doctors and slots

## You're Done! 🎉

Open your browser to http://localhost:3000 and start talking to your AI agent!

---

## Troubleshooting

### "Python not found"
Install Python 3.11+ from https://www.python.org/downloads/

### "Node not found"
Install Node.js 18+ from https://nodejs.org/

### Check your setup
Run `check-setup.bat` to verify everything is installed correctly.

### Still having issues?
See the detailed [SETUP.md](SETUP.md) guide.

---

## What Can You Do?

Try saying:
- "I want to book an appointment with Dr. Sharma"
- "Show me available slots for tomorrow"
- "Cancel my appointment"
- "मुझे डॉक्टर से मिलना है" (Hindi)
- "எனக்கு டாக்டர் அப்பாயின்ட்மென்ட் வேண்டும்" (Tamil)

The agent supports **English, Hindi, and Tamil** with automatic language detection!

---

## Project Structure

```
voice-ai-agent/
├── backend/              # FastAPI + Python
│   ├── app/             # Main application
│   ├── agents/          # LangChain agent
│   ├── tools/           # Appointment tools
│   └── pipeline/        # STT/TTS/Language
├── frontend/nextjs-ui/  # Next.js UI
│   └── src/app/         # React components
├── .env                 # Your configuration
├── start-all.bat        # Start everything
└── check-setup.bat      # Verify setup
```

---

## Next Steps

1. **Customize Doctors**: Edit `backend/app/database.py`
2. **Modify UI**: Edit `frontend/nextjs-ui/src/app/page.tsx`
3. **Add Tools**: Create new tools in `backend/tools/`
4. **Deploy**: Use Docker Compose for production

See [README.md](README.md) for full documentation.
