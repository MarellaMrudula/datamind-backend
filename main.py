"""
Mimi Chatbot — FastAPI Backend
====================================
Run:  uvicorn main:app --reload
Docs: http://localhost:8000/docs
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import anthropic
import pandas as pd
import io
import json
from typing import Optional

# ─────────────────────────────────────────────
# 1. Create the app
# ─────────────────────────────────────────────
app = FastAPI(title="Mimi Chatbot API")

# Allow your React frontend (running on port 3000) to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
# 2. Connect to Claude (Anthropic API)
# ─────────────────────────────────────────────
client = anthropic.Anthropic()  # Reads ANTHROPIC_API_KEY from environment

# In-memory store for conversation history
conversation_history = []


# ─────────────────────────────────────────────
# 3. Data models (what the frontend sends us)
# ─────────────────────────────────────────────
class ChatMessage(BaseModel):
    message: str
    voice_mode: bool = False


class SQLQuery(BaseModel):
    question: str
    table_summary: str


# ─────────────────────────────────────────────
# 4. Routes
# ─────────────────────────────────────────────

@app.get("/")
def home():
    """Health check"""
    return {"status": "Mimi API is running"}


@app.post("/chat")
def chat(body: ChatMessage):
    """
    Main chat endpoint.
    Receives a message, sends it to Claude with full history,
    returns Claude's reply.
    """
    conversation_history.append({
        "role": "user",
        "content": body.message
    })

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=(
            "You are Mimi, a helpful AI data assistant. "
            "You help users analyze data, write SQL queries, summarize files, "
            "and answer questions about their datasets. "
            "Always refer to yourself as Mimi, never DataMind."
            "Be concise and practical."
        ),
        messages=conversation_history
    )

    reply = response.content[0].text

    conversation_history.append({
        "role": "assistant",
        "content": reply
    })

    return {
        "reply": reply,
        "history_length": len(conversation_history)
    }


@app.post("/chat/stream")
def chat_stream(body: ChatMessage):
    """
    Streaming chat — sends reply word by word.
    Creates the typing effect like ChatGPT.
    """
    conversation_history.append({
        "role": "user",
        "content": body.message
    })

    def generate():
        full_reply = ""
        with client.messages.stream(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system="You are Mimi, a helpful AI data assistant.",
            messages=conversation_history
        ) as stream:
            for text in stream.text_stream:
                full_reply += text
                yield f"data: {json.dumps({'chunk': text})}\n\n"

        conversation_history.append({
            "role": "assistant",
            "content": full_reply
        })
        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    CSV upload endpoint.
    Reads the CSV with Pandas and returns a summary.
    Also tells Claude about the data for future questions.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    contents = await file.read()
    df = pd.read_csv(io.StringIO(contents.decode("utf-8")))

    summary = {
        "filename": file.filename,
        "rows": len(df),
        "columns": list(df.columns),
        "dtypes": df.dtypes.astype(str).to_dict(),
        "preview": df.head(3).to_dict(orient="records"),
        "stats": df.describe().round(2).to_dict()
    }

    max_rows = 100
    data_to_send = df.head(max_rows).to_dict(orient='records')

    data_context = (
        f"The user uploaded '{file.filename}' with {len(df)} rows "
        f"and {len(df.columns)} columns: {list(df.columns)}.\n"
        f"Data types: {df.dtypes.astype(str).to_dict()}\n"
        f"Full data ({min(len(df), max_rows)} of {len(df)} rows):\n"
        f"{data_to_send}\n"
        f"Statistics:\n{df.describe().round(2).to_dict()}"
    )
    conversation_history.append({
        "role": "user",
        "content": f"[System: {data_context}]"
    })
    conversation_history.append({
        "role": "assistant",
        "content": (
            f" Mimi can see the uploaded file '{file.filename}'. "
            f"It has {len(df)} rows and {len(df.columns)} columns: "
            f"{', '.join(df.columns)}. Ask me anything about it!"
        )
    })

    return summary


@app.post("/summarize")
async def summarize_file(file: UploadFile = File(...)):
    """
    Text file summarization.
    Upload any .txt file, get a plain-English summary back.
    """
    contents = await file.read()
    text = contents.decode("utf-8", errors="ignore")

    if len(text) > 8000:
        text = text[:8000] + "\n\n[Document truncated for length]"

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        messages=[{
            "role": "user",
            "content": f"Please summarize this document clearly and concisely:\n\n{text}"
        }]
    )

    return {
        "filename": file.filename,
        "summary": response.content[0].text,
        "original_length": len(contents)
    }


@app.post("/sql")
def natural_language_to_sql(body: SQLQuery):
    """
    Convert plain English to SQL.
    """
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        messages=[{
            "role": "user",
            "content": (
                f"Convert this question to a SQL query:\n"
                f"Question: {body.question}\n\n"
                f"Available data: {body.table_summary}\n\n"
                f"Return ONLY the SQL query. No explanation, no markdown."
            )
        }]
    )

    sql = response.content[0].text.strip()
    sql = sql.replace("```sql", "").replace("```", "").strip()

    return {
        "sql": sql,
        "question": body.question
    }


@app.delete("/chat/history")
def clear_history():
    """Clear all conversation history"""
    conversation_history.clear()
    return {"message": "Conversation history cleared"}


@app.get("/chat/history")
def get_history():
    """See the full conversation history"""
    return {
        "history": conversation_history,
        "total_messages": len(conversation_history)
    }