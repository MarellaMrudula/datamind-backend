"""
Mimi AI Chatbot — FastAPI Backend
====================================
Run:  uvicorn main:app --reload
Docs: http://localhost:8000/docs
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import anthropic
import pandas as pd
import pymupdf
import requests
from bs4 import BeautifulSoup
import io
import json

# ─────────────────────────────────────────────
# 1. App setup
# ─────────────────────────────────────────────
app = FastAPI(title="Mimi AI Chatbot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = anthropic.Anthropic()
conversation_history = []
user_resumes = {}

# ─────────────────────────────────────────────
# 2. Data models
# ─────────────────────────────────────────────
class ChatMessage(BaseModel):
    message: str
    voice_mode: bool = False
    session_id: str = "default"

class SQLQuery(BaseModel):
    question: str
    table_summary: str

class JobURL(BaseModel):
    url: str
    session_id: str = "default"

class JobText(BaseModel):
    text: str
    session_id: str = "default"

class CoverLetterRequest(BaseModel):
    job_title: str
    company: str
    summary: str
    session_id: str = "default"

# ─────────────────────────────────────────────
# 3. Health check
# ─────────────────────────────────────────────
@app.get("/")
def home():
    return {"status": "Mimi API is running"}

# ─────────────────────────────────────────────
# 4. Resume upload
# ─────────────────────────────────────────────
@app.post("/upload-resume")
async def upload_resume(
    file: UploadFile = File(...),
    session_id: str = "default"
):
    contents = await file.read()
    resume_text = ""

    if file.filename.endswith(".pdf"):
        pdf = pymupdf.open(stream=contents, filetype="pdf")
        for page in pdf:
            resume_text += page.get_text()
        pdf.close()
    elif file.filename.endswith(".txt"):
        resume_text = contents.decode("utf-8", errors="ignore")
    else:
        raise HTTPException(status_code=400, detail="Only PDF or TXT resumes supported")

    if not resume_text.strip():
        raise HTTPException(status_code=400, detail="Could not extract text from resume.")

    user_resumes[session_id] = resume_text.strip()

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        messages=[{
            "role": "user",
            "content": (
                f"Extract key info from this resume in plain text. "
                f"No markdown. List: name, email, phone, top 5 skills, "
                f"most recent job title and company.\n\n{resume_text[:3000]}"
            )
        }]
    )

    return {
        "success": True,
        "filename": file.filename,
        "characters_extracted": len(resume_text),
        "summary": response.content[0].text.strip(),
        "session_id": session_id,
        "message": "Resume uploaded! I can now calculate your job match score."
    }


@app.get("/resume-status")
def resume_status(session_id: str = "default"):
    has_resume = session_id in user_resumes
    return {
        "has_resume": has_resume,
        "message": "Resume ready!" if has_resume else "No resume uploaded yet."
    }


@app.delete("/resume")
def delete_resume(session_id: str = "default"):
    if session_id in user_resumes:
        del user_resumes[session_id]
    return {"message": "Resume cleared."}


# ─────────────────────────────────────────────
# 5. Chat
# ─────────────────────────────────────────────
@app.post("/chat")
def chat(body: ChatMessage):
    conversation_history.append({
        "role": "user",
        "content": body.message
    })

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=(
            "You are Mimi, a helpful AI assistant built by Mrudula. "
            "You help users with data analysis, job applications, SQL queries, "
            "file summarization, and general questions. "
            "Always refer to yourself as Mimi. "
            "IMPORTANT: Never use markdown formatting. "
            "No hashtags, asterisks, bold, bullet symbols, ### or **. "
            "Write in plain clean text only. "
            "Use numbered lists like 1. 2. 3. and simple line breaks. "
            "Be concise and practical."
        ),
        messages=conversation_history
    )

    reply = response.content[0].text
    conversation_history.append({
        "role": "assistant",
        "content": reply
    })

    return {"reply": reply, "history_length": len(conversation_history)}


# ─────────────────────────────────────────────
# 6. CSV upload
# ─────────────────────────────────────────────
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files supported")

    contents = await file.read()
    df = pd.read_csv(io.StringIO(contents.decode("utf-8")))

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

    conversation_history.append({"role": "user", "content": f"[System: {data_context}]"})
    conversation_history.append({
        "role": "assistant",
        "content": (
            f"I can see the uploaded file '{file.filename}'. "
            f"It has {len(df)} rows and {len(df.columns)} columns: "
            f"{', '.join(df.columns)}. Ask me anything about this data!"
        )
    })

    return {
        "filename": file.filename,
        "rows": len(df),
        "columns": list(df.columns),
        "dtypes": df.dtypes.astype(str).to_dict(),
        "preview": df.head(3).to_dict(orient="records"),
        "stats": df.describe().round(2).to_dict()
    }


# ─────────────────────────────────────────────
# 7. Text summarization
# ─────────────────────────────────────────────
@app.post("/summarize")
async def summarize_file(file: UploadFile = File(...)):
    contents = await file.read()
    text = contents.decode("utf-8", errors="ignore")

    if len(text) > 8000:
        text = text[:8000] + "\n\n[Document truncated]"

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        messages=[{
            "role": "user",
            "content": f"Summarize this in plain text no markdown:\n\n{text}"
        }]
    )

    return {
        "filename": file.filename,
        "summary": response.content[0].text,
        "original_length": len(contents)
    }


# ─────────────────────────────────────────────
# 8. SQL converter
# ─────────────────────────────────────────────
@app.post("/sql")
def natural_language_to_sql(body: SQLQuery):
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        messages=[{
            "role": "user",
            "content": (
                f"Convert this to SQL:\nQuestion: {body.question}\n"
                f"Data: {body.table_summary}\n"
                f"Return ONLY the SQL query, no explanation."
            )
        }]
    )

    sql = response.content[0].text.strip()
    sql = sql.replace("```sql", "").replace("```", "").strip()
    return {"sql": sql, "question": body.question}


# ─────────────────────────────────────────────
# 9. Job scraper (simple — no browser needed)
# ─────────────────────────────────────────────
def scrape_with_requests(url: str) -> str:
    """Simple HTTP scraper — works on most job sites except LinkedIn"""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)
    # Clean up excessive whitespace
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    return "\n".join(lines)[:6000]


def analyze_job_with_claude(job_text: str, session_id: str) -> dict:
    """Use Claude to extract job details and calculate match score"""
    has_resume = session_id in user_resumes
    resume_section = ""

    if has_resume:
        resume_text = user_resumes[session_id][:3000]
        resume_section = f"\n\nUSER RESUME:\n{resume_text}"

    if has_resume:
        prompt = f"""
Analyze this job posting and the user resume.
Return ONLY a valid JSON object with no extra text or markdown.

JOB POSTING:
{job_text}
{resume_section}

Return exactly this JSON:
{{
  "job_title": "job title",
  "company": "company name",
  "location": "location or Remote",
  "job_type": "full-time or part-time or contract or internship",
  "summary": "2 sentence plain text summary of the role",
  "required_skills": ["skill1", "skill2", "skill3", "skill4", "skill5"],
  "responsibilities": ["task1", "task2", "task3", "task4"],
  "match_score": 75,
  "matched_skills": ["skill1", "skill2", "skill3"],
  "missing_skills": ["skill4", "skill5"],
  "match_summary": "2 sentence plain text explanation of the match score",
  "recommendation": "Strong Match",
  "has_resume": true,
  "form_fields": {{
    "name": "extracted from resume",
    "email": "extracted from resume",
    "phone": "extracted from resume",
    "location": "extracted from resume"
  }}
}}
For recommendation use exactly: Strong Match, Good Match, Partial Match, or Weak Match
"""
    else:
        prompt = f"""
Analyze this job posting.
Return ONLY a valid JSON object with no extra text or markdown.

JOB POSTING:
{job_text}

Return exactly this JSON:
{{
  "job_title": "job title",
  "company": "company name",
  "location": "location or Remote",
  "job_type": "full-time or part-time or contract or internship",
  "summary": "2 sentence plain text summary of the role",
  "required_skills": ["skill1", "skill2", "skill3", "skill4", "skill5"],
  "responsibilities": ["task1", "task2", "task3", "task4"],
  "match_score": null,
  "matched_skills": [],
  "missing_skills": [],
  "match_summary": "Upload your resume to see your personal match score for this job.",
  "recommendation": "Upload Resume for Match Score",
  "has_resume": false,
  "form_fields": {{
    "name": "",
    "email": "",
    "phone": "",
    "location": ""
  }}
}}
"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.content[0].text.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(raw)


@app.post("/scrape-job")
async def scrape_job(body: JobURL):
    """
    Scrape a job posting URL using simple HTTP request.
    Works on: Indeed, Glassdoor, Greenhouse, Lever, Workday, company sites.
    For LinkedIn: ask user to paste job description text instead.
    """
    try:
        # Check if LinkedIn URL
        if "linkedin.com" in body.url:
            return {
                "success": False,
                "linkedin": True,
                "message": (
                    "LinkedIn blocks automated scraping. "
                    "Please copy and paste the job description text "
                    "into the chat and I will analyze it for you!"
                )
            }

        job_text = scrape_with_requests(body.url)

        if len(job_text) < 100:
            raise HTTPException(
                status_code=400,
                detail="Could not extract enough content from this URL. Try pasting the job description text instead."
            )

        job_data = analyze_job_with_claude(job_text, body.session_id)

        return {"success": True, "url": body.url, "data": job_data}

    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Failed to parse job data. Try pasting the job description text instead.")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Could not access this URL: {str(e)}. Try pasting the job description text.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze job: {str(e)}")


@app.post("/analyze-job-text")
async def analyze_job_text(body: JobText):
    """
    Analyze job description pasted as text.
    Works for LinkedIn and any site that blocks scraping.
    """
    try:
        if len(body.text) < 50:
            raise HTTPException(status_code=400, detail="Please paste more job description text.")

        job_data = analyze_job_with_claude(body.text, body.session_id)
        return {"success": True, "data": job_data}

    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Failed to parse job data. Please try again.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze: {str(e)}")


# ─────────────────────────────────────────────
# 10. Cover letter
# ─────────────────────────────────────────────
@app.post("/cover-letter")
def generate_cover_letter(body: CoverLetterRequest):
    resume_section = ""
    if body.session_id in user_resumes:
        resume_section = f"\n\nUser Resume:\n{user_resumes[body.session_id][:2000]}"

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=800,
        messages=[{
            "role": "user",
            "content": (
                f"Write a professional cover letter in plain text. "
                f"No markdown. 3 paragraphs maximum.\n\n"
                f"Job Title: {body.job_title}\n"
                f"Company: {body.company}\n"
                f"Job Summary: {body.summary}"
                f"{resume_section}"
            )
        }]
    )

    return {"cover_letter": response.content[0].text.strip()}


# ─────────────────────────────────────────────
# 11. Chat history
# ─────────────────────────────────────────────
@app.delete("/chat/history")
def clear_history():
    conversation_history.clear()
    return {"message": "Conversation history cleared"}

@app.get("/chat/history")
def get_history():
    return {
        "history": conversation_history,
        "total_messages": len(conversation_history)
    }