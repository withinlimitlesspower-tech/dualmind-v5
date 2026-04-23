from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from database import SessionLocal, engine, Base, get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import models
from handlers.chat import deepseek_chat, detect_intent, generate_code
from handlers.github import push_to_github
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

class ChatRequest(BaseModel):
    session_id: int
    message: str

class CreateSessionRequest(BaseModel):
    name: str

class PushRequest(BaseModel):
    session_id: int
    repo_name: str

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/chat")
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    # Get session
    result = await db.execute(select(models.Session).where(models.Session.id == request.session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Detect intent
    intent = detect_intent(request.message)
    
    if intent == "CODE_GENERATE":
        # Generate code
        ai_response = await deepseek_chat(request.message, session_id=request.session_id)
        code = generate_code(ai_response)
        # Save user message
        user_msg = models.Message(session_id=request.session_id, role="user", content=request.message, code=None)
        db.add(user_msg)
        # Save assistant message
        assistant_msg = models.Message(session_id=request.session_id, role="assistant", content=ai_response, code=code)
        db.add(assistant_msg)
        await db.commit()
        return {"response": ai_response, "code": code}
    elif intent == "GITHUB_PUSH":
        # Expect message to contain repo name or something? We'll handle via separate endpoint.
        return {"response": "Please use the Push to GitHub button to specify repository name.", "code": None}
    else:
        # General chat
        ai_response = await deepseek_chat(request.message, session_id=request.session_id)
        user_msg = models.Message(session_id=request.session_id, role="user", content=request.message, code=None)
        db.add(user_msg)
        assistant_msg = models.Message(session_id=request.session_id, role="assistant", content=ai_response, code=None)
        db.add(assistant_msg)
        await db.commit()
        return {"response": ai_response, "code": None}

@app.get("/api/sessions")
async def get_sessions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Session).order_by(models.Session.created_at.desc()))
    sessions = result.scalars().all()
    return [{"id": s.id, "name": s.name, "created_at": s.created_at.isoformat()} for s in sessions]

@app.post("/api/sessions")
async def create_session(req: CreateSessionRequest, db: AsyncSession = Depends(get_db)):
    session = models.Session(name=req.name)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return {"id": session.id, "name": session.name, "created_at": session.created_at.isoformat()}

@app.post("/api/push-to-github")
async def push_to_github_endpoint(req: PushRequest, db: AsyncSession = Depends(get_db)):
    # Get all messages in session with code
    result = await db.execute(
        select(models.Message).where(
            models.Message.session_id == req.session_id,
            models.Message.code.isnot(None)
        )
    )
    messages = result.scalars().all()
    if not messages:
        raise HTTPException(status_code=400, detail="No code to push")
    
    # Build files dict: filename from first line or generic
    files = {}
    for idx, msg in enumerate(messages):
        filename = f"generated_{idx}.py"
        files[filename] = msg.code
    
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise HTTPException(status_code=500, detail="GitHub token not configured")
    
    repo_url = push_to_github(files, req.repo_name, token)
    
    # Create project record
    project = models.Project(session_id=req.session_id, name=req.repo_name, repo_url=repo_url)
    db.add(project)
    await db.commit()
    
    return {"repo_url": repo_url}
