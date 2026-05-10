from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uuid
from datetime import datetime
import asyncio
from langgraph.types import Command
import os
from dotenv import load_dotenv

# Import from agents
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from agents.blog_agent import BlogAgent
from langchain_groq import ChatGroq
import aiosqlite
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from config.settings import settings
from config.logging import get_logger
from sqlalchemy.orm import Session
from database.connection import get_db, SessionLocal
from database.models import BlogThread, User
from app.api.v1.auth import get_current_user, check_blog_quota, increment_blog_count, get_user_quota_status

logger = get_logger("blog_api")

router = APIRouter()

# Global agent instance (for demo purposes, InMemorySaver will lose data on restart)
# In production, use SqliteSaver or PostgresSaver
agent_instance = None

async def get_agent():
    global agent_instance
    if agent_instance is None:
        load_dotenv()
        GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
        # Initialize LLM and Checkpointer
        # llm = ChatGroq(api_key=GROQ_API_KEY, model="meta-llama/llama-4-scout-17b-16e-instruct")
        llm = ChatGroq(api_key=GROQ_API_KEY, model="llama-3.3-70b-versatile")
        
        conn = await aiosqlite.connect("blog_agent_checkpoints.db")
        checkpointer = AsyncSqliteSaver(conn)
        
        agent_instance = BlogAgent(api_key=GROQ_API_KEY, llm=llm, checkpointer=checkpointer)
    return agent_instance

class GenerateRequest(BaseModel):
    prompt: str
    tone: str
    recency_days: Optional[int] = 7

class ResumeRequest(BaseModel):
    approval: str  # "approved" or "rejected"
    suggestions: Optional[str] = ""

async def run_agent_background(agent: BlogAgent, thread_id: str, inputs: dict):
    config = {"configurable": {"thread_id": thread_id}}
    graph = await agent.initialize_graph()
    try:
        await graph.ainvoke(inputs, config=config)

        # Check if completed without interruption
        state_snapshot = await graph.aget_state(config)
        if state_snapshot and not getattr(state_snapshot, "next", []):
            if "html_content" in state_snapshot.values:
                # Save to DB
                db = SessionLocal()
                try:
                    db_thread = db.query(BlogThread).filter(BlogThread.thread_id == thread_id).first()
                    if db_thread:
                        db_thread.content = state_snapshot.values["html_content"]
                        db_thread.markdown_content = state_snapshot.values.get("markdown_content")
                        db_thread.status = "completed"

                        # Increment blog count for user
                        user = db.query(User).filter(User.id == int(db_thread.user_id)).first()
                        if user:
                            word_count = len(state_snapshot.values.get("markdown_content", "").split())
                            logger.info(f"Incrementing blog count for user {user.id}, word_count: {word_count}")
                            increment_blog_count(user, word_count=word_count, db=db)
                            logger.info(f"Blog count incremented successfully")
                        else:
                            logger.warning(f"User not found for thread {thread_id}")

                        db.commit()
                finally:
                    db.close()
    except Exception as e:
        logger.log_error_with_context(e, "Error in background execution")

@router.post("/generate")
async def generate_blog(req: GenerateRequest, background_tasks: BackgroundTasks, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Check if user has exceeded their quota
    if not check_blog_quota(current_user, db):
        quota_status = get_user_quota_status(current_user, db)
        raise HTTPException(
            status_code=429,
            detail={
                "message": "Blog generation limit exceeded",
                "quota": quota_status
            }
        )

    agent = await get_agent()
    thread_id = str(uuid.uuid4())

    # Save thread to DB
    db_thread = BlogThread(
        thread_id=thread_id,
        user_id=str(current_user.id),
        topic=req.prompt,
        status="processing"
    )
    db.add(db_thread)
    db.commit()

    today = datetime.now().strftime("%Y-%m-%d")
    inputs = {
        "prompt": req.prompt,
        "tone": req.tone,
        "recency_days": req.recency_days,
        "as_of": today
    }

    background_tasks.add_task(run_agent_background, agent, thread_id, inputs)

    return {"thread_id": thread_id, "status": "started"}

@router.get("/status/{thread_id}")
async def get_status(thread_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Check if thread belongs to current user
    db_thread = db.query(BlogThread).filter(BlogThread.thread_id == thread_id).first()
    if not db_thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    if db_thread.user_id != str(current_user.id):
        raise HTTPException(status_code=403, detail="Access denied")

    agent = await get_agent()
    graph = await agent.initialize_graph()
    config = {"configurable": {"thread_id": thread_id}}

    try:
        state_snapshot = await graph.aget_state(config)
    except Exception as e:
        logger.log_error_with_context(e, "Error getting status")
        return {"status": "error", "message": str(e)}

    if not state_snapshot:
        return {"status": "not_found"}

    if hasattr(state_snapshot, "tasks") and state_snapshot.tasks:
        is_interrupted = any(bool(task.interrupts) for task in state_snapshot.tasks)
    else:
        is_interrupted = bool(state_snapshot.next and state_snapshot.next[0] == "hitl")

    values = state_snapshot.values

    if is_interrupted:
        return {
            "status": "awaiting_approval",
            "plan": values.get("plan"),
            "topic": values.get("topic")
        }

    if not is_interrupted and "html_content" in values:
        logger.info(f"Returning html_content, length: {len(values.get('html_content', ''))}")
        logger.info(f"html_content preview: {values.get('html_content', '')[:200]}")
        return {
            "status": "completed",
            "html_content": values.get("html_content"),
            "markdown_content": values.get("markdown_content"),
            "plan": values.get("plan"),
            "evidence": values.get("evidence"),
            "needs_research": values.get("needs_research"),
            "mode": values.get("mode"),
            "queries": values.get("queries"),
            "recency_days": values.get("recency_days"),
            "topic": values.get("topic"),
            "sections": values.get("sections"),
            "error": values.get("error")
        }

    return {
        "status": "processing",
        "current_state": values.get("topic", "initializing")
    }

@router.post("/resume/{thread_id}")
async def resume_blog(thread_id: str, req: ResumeRequest, background_tasks: BackgroundTasks, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Check if thread belongs to current user
    db_thread = db.query(BlogThread).filter(BlogThread.thread_id == thread_id).first()
    if not db_thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    if db_thread.user_id != str(current_user.id):
        raise HTTPException(status_code=403, detail="Access denied")

    agent = await get_agent()
    config = {"configurable": {"thread_id": thread_id}}

    user_feedback_dict = {
        "approval": req.approval,
        "suggestions": req.suggestions
    }

    async def resume_agent_background():
        graph = await agent.initialize_graph()
        try:
            await graph.ainvoke(Command(resume=user_feedback_dict), config=config)

            # Check if completed
            state_snapshot = await graph.aget_state(config)
            if state_snapshot and not getattr(state_snapshot, "next", []):
                if "html_content" in state_snapshot.values:
                    db = SessionLocal()
                    try:
                        db_thread = db.query(BlogThread).filter(BlogThread.thread_id == thread_id).first()
                        if db_thread:
                            db_thread.content = state_snapshot.values["html_content"]
                            db_thread.markdown_content = state_snapshot.values.get("markdown_content")
                            db_thread.status = "completed"

                            # Increment blog count for user
                            user = db.query(User).filter(User.id == int(db_thread.user_id)).first()
                            if user:
                                # Estimate word count from markdown content
                                word_count = len(state_snapshot.values.get("markdown_content", "").split())
                                logger.info(f"Incrementing blog count for user {user.id}, word_count: {word_count}")
                                increment_blog_count(user, word_count=word_count, db=db)
                                logger.info(f"Blog count incremented successfully")
                            else:
                                logger.warning(f"User not found for thread {thread_id}")

                            db.commit()
                    finally:
                        db.close()
        except Exception as e:
            logger.log_error_with_context(e, "Error in background resume")

    background_tasks.add_task(resume_agent_background)

    return {"status": "resumed"}

@router.get("/threads")
async def get_user_threads(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    threads = db.query(BlogThread).filter(BlogThread.user_id == str(current_user.id)).order_by(BlogThread.created_at.desc()).all()
    return {
        "threads": [
            {
                "thread_id": t.thread_id,
                "topic": t.topic,
                "status": t.status,
                "created_at": t.created_at
            } for t in threads
        ]
    }
