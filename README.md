# ⚡ Mimi — AI Data Assistant Chatbot

> **Built by Mrudula Marella** | Full-Stack AI Application | FastAPI + React + Claude AI

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Click%20Here-blue)](https://datamind-frontend-henna.vercel.app)
[![Backend API](https://img.shields.io/badge/Backend%20API-Render-green)](https://datamind-backend-u9nm.onrender.com/docs)
[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://python.org)
[![React](https://img.shields.io/badge/React-TypeScript-blue)](https://reactjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green)](https://fastapi.tiangolo.com)

---

## 🌐 Live Demo

🔗 **Try it now:** [https://datamind-frontend-henna.vercel.app](https://datamind-frontend-henna.vercel.app)

> ⚠️ Backend runs on Render free tier — first message may take 30-60 seconds to wake up.

---

## 📌 What is Mimi?

**Mimi** is a full-stack AI-powered data assistant chatbot that allows users to:

- 💬 Chat with an AI about data, SQL, analytics, and more
- 🎤 Speak questions using voice input
- 🔊 Hear replies in a female voice (Microsoft Heera)
- 📎 Upload CSV files and ask questions about the data
- 📄 Upload text files and get instant summaries
- 📝 Summarize any AI reply with one click
- 🗄️ Convert plain English questions into SQL queries

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                   USER BROWSER                       │
│  ┌──────────────────────────────────────────────┐   │
│  │         React + TypeScript Frontend           │   │
│  │  • Chat UI with message bubbles               │   │
│  │  • Voice Input (Web Speech API)               │   │
│  │  • Voice Output (Speech Synthesis API)        │   │
│  │  • File Upload (CSV / TXT)                    │   │
│  │  • Charts (Recharts)                          │   │
│  └──────────────┬───────────────────────────────┘   │
└─────────────────┼───────────────────────────────────┘
                  │ HTTP Requests (Axios)
                  ▼
┌─────────────────────────────────────────────────────┐
│              FastAPI Backend (Python)                │
│  ┌──────────────────────────────────────────────┐   │
│  │  Endpoints:                                   │   │
│  │  POST /chat         → Send message to AI      │   │
│  │  POST /chat/stream  → Streaming response       │   │
│  │  POST /upload       → Process CSV file         │   │
│  │  POST /summarize    → Summarize text file      │   │
│  │  POST /sql          → Natural language to SQL  │   │
│  │  GET  /chat/history → Get conversation         │   │
│  │  DELETE /chat/history → Clear conversation     │   │
│  └──────────────┬───────────────────────────────┘   │
└─────────────────┼───────────────────────────────────┘
                  │ API Calls
        ┌─────────┴──────────┐
        ▼                    ▼
┌──────────────┐    ┌───────────────┐
│  Claude AI   │    │    Pandas     │
│  (Anthropic) │    │  Data Engine  │
└──────────────┘    └───────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React, TypeScript, Axios, Recharts |
| Backend | Python, FastAPI, Uvicorn |
| AI Brain | Claude API (Anthropic) |
| Data Processing | Pandas, NumPy |
| Voice Input | Web Speech API (browser built-in) |
| Voice Output | Speech Synthesis API + Microsoft Heera |
| Cloud | AWS EC2/RDS, Microsoft Azure (AZ-204) |
| Hosting (Backend) | Render |
| Hosting (Frontend) | Vercel |
| Version Control | Git, GitHub |

---

## ✨ Features

### 💬 AI Chat
- Powered by Claude AI (claude-sonnet-4-6)
- Remembers full conversation history
- Responds to data, SQL, analytics, and general questions

### 🎤 Voice Input
- Click the microphone button and speak
- Converts voice to text automatically using Web Speech API
- Works in Google Chrome

### 🔊 Voice Output (Female Voice)
- Toggle voice ON/OFF with the speaker button
- Uses Microsoft Heera (Indian English female voice)
- Also available per-message via 🔊 Listen button

### 📎 File Upload
- Upload CSV files → get row count, columns, statistics
- Upload TXT files → get instant AI summary
- Ask follow-up questions about uploaded data

### 📝 Summarize
- Every AI reply has a 📝 Summarize button
- Click to get a 2-3 sentence summary of any response

### 🗄️ Natural Language to SQL
- Ask a question in plain English
- Get back a ready-to-run SQL query

---

## 📁 Project Structure

```
mimi/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── requirements.txt     # Python dependencies
│   └── venv/               # Virtual environment
│
└── frontend/
    └── datamind-ui/
        ├── src/
        │   ├── App.tsx      # Main React component
        │   └── index.tsx    # Entry point
        ├── public/
        ├── package.json
        └── tsconfig.json
```

---

## 🚀 Local Setup

### Prerequisites
- Python 3.12+
- Node.js 20+
- Anthropic API key (get from console.anthropic.com)

### Backend Setup

```bash
# 1. Navigate to backend
cd backend

# 2. Create virtual environment
python -m venv venv

# 3. Activate (Windows)
venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Set API key (Windows PowerShell)
$env:ANTHROPIC_API_KEY="your-key-here"

# 6. Run server
uvicorn main:app --reload
```

Backend runs at: `http://localhost:8000`
API docs at: `http://localhost:8000/docs`

### Frontend Setup

```bash
# 1. Navigate to frontend
cd frontend/datamind-ui

# 2. Install dependencies
npm install

# 3. Start React app
npm start
```

Frontend runs at: `http://localhost:3000`

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| POST | `/chat` | Send message, get AI reply |
| POST | `/chat/stream` | Streaming chat response |
| POST | `/upload` | Upload and analyze CSV |
| POST | `/summarize` | Summarize text file |
| POST | `/sql` | Natural language to SQL |
| GET | `/chat/history` | Get conversation history |
| DELETE | `/chat/history` | Clear conversation |

---

## 🌍 Deployment

| Service | Platform | URL |
|---------|----------|-----|
| Frontend | Vercel | https://datamind-frontend-henna.vercel.app |
| Backend | Render | https://datamind-backend-u9nm.onrender.com |

---

## 👩‍💻 About the Developer

**Mrudula Marella**
- 📍 Chicago, IL, USA
- 🎓 MS Computer Science, University of Illinois Springfield (GPA: 4.0)
- 💼 Data Analyst | AI/ML Engineer | Full-Stack Developer
- 🔗 [LinkedIn](https://www.linkedin.com/in/marella-mrudula)
- 🐱 [GitHub](https://github.com/MarellaMrudula)
- 📧 marellamrudula1@gmail.com

---

## 📄 License

MIT License — feel free to use, modify, and distribute.

---

*Built with ❤️ by Mrudula Marella using FastAPI, React, and Claude AI*
