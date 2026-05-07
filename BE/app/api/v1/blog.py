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
from langgraph.checkpoint.memory import InMemorySaver
from config.settings import settings

router = APIRouter()

# Global agent instance (for demo purposes, InMemorySaver will lose data on restart)
# In production, use SqliteSaver or PostgresSaver
agent_instance = None

def get_agent():
    global agent_instance
    if agent_instance is None:
        load_dotenv()
        GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
        # Initialize LLM and Checkpointer
        # llm = ChatGroq(api_key=GROQ_API_KEY, model="meta-llama/llama-4-scout-17b-16e-instruct")
        llm = ChatGroq(api_key=GROQ_API_KEY, model="llama-3.3-70b-versatile")
        checkpointer = InMemorySaver()
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
    except Exception as e:
        print(f"Error in background execution: {e}")

@router.post("/generate")
async def generate_blog(req: GenerateRequest, background_tasks: BackgroundTasks):
    agent = get_agent()
    thread_id = str(uuid.uuid4())
    
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
async def get_status(thread_id: str):
    agent = get_agent()
    graph = await agent.initialize_graph()
    config = {"configurable": {"thread_id": thread_id}}
    
    try:
        state_snapshot = graph.get_state(config)
    except Exception as e:
        return {"status": "error", "message": str(e)}

    if not state_snapshot:
        return {"status": "not_found"}

    is_interrupted = bool(state_snapshot.next)
    values = state_snapshot.values
    
    if is_interrupted:
        return {
            "status": "awaiting_approval",
            "plan": values.get("plan"),
            "topic": values.get("topic")
        }
    
    if not is_interrupted and "markdown_content" in values:
        return {
            "status": "completed",
            "markdown_content": values.get("markdown_content"),
            "plan": values.get("plan")
        }
        
    return {
        "status": "processing",
        "current_state": values.get("topic", "initializing")
    }

@router.post("/resume/{thread_id}")
async def resume_blog(thread_id: str, req: ResumeRequest, background_tasks: BackgroundTasks):
    agent = get_agent()
    config = {"configurable": {"thread_id": thread_id}}
    
    user_feedback_dict = {
        "approval": req.approval,
        "suggestions": req.suggestions
    }
    
    async def resume_agent_background():
        graph = await agent.initialize_graph()
        try:
            await graph.ainvoke(Command(resume=user_feedback_dict), config=config)
        except Exception as e:
            print(f"Error in background resume: {e}")
            
    background_tasks.add_task(resume_agent_background)
    
    return {"status": "resumed"}
