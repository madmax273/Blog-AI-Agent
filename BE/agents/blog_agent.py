import os
import sys
from pathlib import Path
#TODO: Remove this when running as a module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Set environment variables BEFORE any LangGraph imports to suppress warnings
from fastapi.openapi.models import OAuthFlowClientCredentials
from langchain_core.prompts import PromptTemplate
from langgraph.graph import StateGraph, END,START
from typing import Dict, Any
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI

from langgraph.types import Send
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_tavily import TavilySearch
from typing import List


from langgraph.types import interrupt,Command
from typing_extensions import   TypedDict
from langgraph.checkpoint.memory import InMemorySaver
from Model.agent_models import BlogAgentState,Plan,RouterOutput,EvidencePack,EvidenceItem,Task
from utils.agent_prompts import PLANNING_PROMPT,GENERATOR_PROMPT,ROUTER_PROMPT,RESEARCH_PROMPT
from dotenv import load_dotenv
from datetime import datetime, date, timedelta

import asyncio

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

def _iso_to_date(date_str: str) -> date:
    """Convert ISO date string to date object, return None if invalid."""
    if not date_str:
        return None
    try:
        return date.fromisoformat(date_str.split("T")[0])
    except (ValueError, AttributeError):
        return None

def check_approval(state: BlogAgentState)->str:
    """
    Check if the plan is approved or not
    """
    if state["approval"] == "approved":
        return "generate"
    else:
        return "planner"

def _tavily_search(query: str, max_results: int = 3) -> List[dict]:
    """
    Uses TavilySearch if installed and TAVILY_API_KEY is set.
    Returns list of dict with common fields. Note: published date is often missing.
    """
    tool = TavilySearch(max_results=max_results)
    results = tool.invoke({"query": query})

    normalized: List[dict] = []
    # New TavilySearch returns a dict with 'results' key
    if isinstance(results, dict) and 'results' in results:
        results_list = results['results']
    else:
        results_list = results if isinstance(results, list) else []
    
    for r in results_list or []:
        normalized.append(
            {
                "title": r.get("title") or "",
                "url": r.get("url") or "",
                "snippet": r.get("content") or r.get("snippet") or "",
                "published_at": r.get("published_date") or r.get("published_at") or "",
                "source": r.get("source") or "",
            }
        )
    print("\n========Tavily searched====\n")    
    return normalized   

def route_next(state: BlogAgentState) -> str:
    return "research" if state["needs_research"]=="true" else "planner"      


class BlogAgent:
    
    def __init__(self, api_key: str, llm: ChatGroq, checkpointer: InMemorySaver):
        self.graph = None
        self.api_key = api_key
        self.compiled_graph = None
        self.llm = llm
        self.checkpointer = checkpointer
    
    async def initialize_graph(self):
        if self.compiled_graph is None:
            self.compiled_graph = await self._build_graph()
        return self.compiled_graph

    async def router_node(self, state: BlogAgentState) -> dict:
        topic = state["prompt"]
        decider = self.llm.with_structured_output(RouterOutput)
        decision = await decider.ainvoke(
            [
                SystemMessage(content=ROUTER_PROMPT),
                HumanMessage(content=f"Topic: {topic}\nAs-of date: {state['as_of']}"),
            ]
        )

        # Set default recency window based on mode
        if decision.mode == "open_book":
            recency_days = 7
        elif decision.mode == "hybrid":
            recency_days = 45
        else:
            recency_days = 3650

        print(f"Decision: {decision}")
        print(f"Recency days: {recency_days}")
        print(f"State: {state}")


        return {
            "needs_research": str(decision.needs_research).lower() == "true",
            "mode": decision.mode,
            "queries": decision.queries,
            "recency_days": recency_days,
            "topic": topic
        }
 
    async def research_node(self, state: BlogAgentState) -> dict:
        queries = (state.get("queries", []) or [])[:10]
        max_results = 1

        raw_results: List[dict] = []
        for q in queries:
            raw_results.extend(_tavily_search(q, max_results=max_results))
        print("\n===Results from tavily===\n",raw_results)
        if not raw_results:
            return {"evidence": []}

        extractor = self.llm.with_structured_output(EvidencePack)
        pack = await extractor.ainvoke(
            [
                SystemMessage(content=RESEARCH_PROMPT),
                HumanMessage(
                    content=(
                        f"As-of date: {state['as_of']}\n"
                        f"Recency days: {state['recency_days']}\n\n"
                        f"Raw results:\n{raw_results}"
                    )
                ),
            ]
        )

        print("\n===Evidence pack===\n",pack)

        # Deduplicate by URL
        dedup = {}
        for e in pack.items:
            if e.url:
                dedup[e.url] = e
        evidence = list(dedup.values())

        # HARD RECENCY FILTER for open_book weekly roundup:
        # keep only items with a parseable ISO date and within the window.
        mode = state.get("mode", "closed_book")
        if mode == "open_book":
            as_of = date.fromisoformat(state["as_of"])
            cutoff = as_of - timedelta(days=int(state["recency_days"]))
            fresh: List[EvidenceItem] = []
            for e in evidence:
                d = _iso_to_date(e.published_at)
                if d and d >= cutoff:
                    fresh.append(e)

            evidence = fresh
        print("\n===Filtered evidence===\n",evidence)
        print("finished research node moving to planner node")
        return {"evidence": evidence}

    async def planner_node(self, state: BlogAgentState):
        print("\n=== PLANNER NODE STARTING ===")
        print(f"State keys: {state.keys()}")
        
        planner = self.llm.with_structured_output(Plan)
        evidence = state.get("evidence", [])
        mode = state.get("mode", "closed_book")
        
        print(f"Evidence count: {len(evidence)}")
        print(f"Mode: {mode}")

        # Force blog_kind for open_book
        forced_kind = "news_roundup" if mode == "open_book" else None

        try:
            plan = await planner.ainvoke(
                [
                    SystemMessage(content=PLANNING_PROMPT),
                    HumanMessage(
                        content=(
                            f"Topic: {state['topic']}\n"
                            f"Mode: {mode}\n"
                            f"Evidence (ONLY use for fresh claims; may be empty):\n"
                            f"{[e.model_dump() for e in evidence][:16]}\n\n"
                        )
                    ),
                ]
            )
            print(f"\n=== PLAN GENERATED ===")
            print(f"Title: {plan.blog_title}")
            print(f"Tasks: {len(plan.tasks)}")
        except Exception as e:
            print(f"\n=== PLANNER ERROR ===")
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            raise

        # Ensure open_book forces the kind even if model forgets
        if forced_kind:
            plan.blog_kind = "news_roundup"

        # Convert Plan to dict for serialization
        print("=== PLANNER NODE COMPLETE ===\n")
        return {"plan": plan.model_dump()}

    async def hitl_node(self,state: BlogAgentState):
        plan_data = state["plan"]
        plan = Plan(**plan_data) if isinstance(plan_data, dict) else plan_data
        plan_generated=plan
        
        message_for_hitl=interrupt(f"Plan generated: {plan_generated}\nDo you like the plan? (yes/no): or you have some feedback? ")
        
        print("Plan generated:", plan_generated)
        
        print("Message for hitl:", message_for_hitl)
        if message_for_hitl["approval"] != "approved":
            return {"approval": "rejected"}
        
        return {"approval": "approved"}    
    
    async def fanout(self,state: BlogAgentState):
        plan_data = state["plan"]
        plan = Plan(**plan_data) if isinstance(plan_data, dict) else plan_data
        evidence = state.get("evidence", [])
        return [
            Send(
                "worker",
                {"task": task, "topic": state["topic"], "plan": plan, "mode":state.get("mode", "closed_book"),"evidence":evidence},
            )
            for task in plan.tasks
        ]

    async def worker(self,payload: dict) -> dict:

        task_data = payload["task"]
        task = Task(**task_data) if isinstance(task_data, dict) else task_data
        
        plan_data = payload["plan"]
        plan = Plan(**plan_data) if isinstance(plan_data, dict) else plan_data
        
        evidence_data = payload.get("evidence", [])
        evidence = [EvidenceItem(**e) if isinstance(e, dict) else e for e in evidence_data]
        topic = payload["topic"]
        mode = payload.get("mode", "closed_book")

        bullets_text = "\n- " + "\n- ".join(task.bullets)

        evidence_text = ""
        if evidence:
            evidence_text = "\n".join(
                f"- {e.title} | {e.url} | {e.published_at or 'date:unknown'}".strip()
                for e in evidence[:20]
            )

        response = await self.llm.ainvoke(
            [
                SystemMessage(content=GENERATOR_PROMPT),
                HumanMessage(
                    content=(
                        f"Blog title: {plan.blog_title}\n"
                        f"Audience: {plan.audience}\n"
                        f"Tone: {plan.tone}\n"
                        f"Blog kind: {plan.blog_kind}\n"
                        f"Constraints: {plan.constraints}\n"
                        f"Topic: {topic}\n"
                        f"Mode: {mode}\n\n"
                        f"Section title: {task.title}\n"
                        f"Goal: {task.goal}\n"
                        f"Target words: {task.target_words}\n"
                        f"Tags: {task.tags}\n"
                        f"requires_research: {task.requires_research}\n"
                        f"requires_citations: {task.requires_citations}\n"
                        f"requires_code: {task.requires_code}\n"
                        f"Bullets:{bullets_text}\n\n"
                        f"Evidence (ONLY use these URLs when citing):\n{evidence_text}\n"
                    )
                ),
            ]
        )
        section_md = response.content.strip()

        return {"sections": [(task.id, section_md)]}
      
    async def reducer(self, state: BlogAgentState) -> dict:
        plan_data = state["plan"]
        plan = Plan(**plan_data) if isinstance(plan_data, dict) else plan_data
        
        title = plan.blog_title
        
        # Sort sections by task ID and extract the markdown content
        sorted_sections = sorted(state["sections"], key=lambda x: x[0])
        body = "\n\n".join(section_md for _, section_md in sorted_sections).strip()
        
        final_md = f"# {title}\n\n{body}\n"

        # Save to file
        filename = "".join(c if c.isalnum() or c in (" ", "_", "-") else "" for c in title)
        filename = filename.strip().lower().replace(" ", "_") + ".md"
        Path(filename).write_text(final_md, encoding="utf-8")

        return {"markdown_content": final_md}
       


    async def _build_graph(self):
        graph = StateGraph(BlogAgentState)
        graph.add_node("router", self.router_node)
        graph.add_node("research", self.research_node)
        graph.add_node("planner", self.planner_node)
        graph.add_node("hitl", self.hitl_node)
        graph.add_node("worker", self.worker)
        graph.add_node("reducer", self.reducer)
        
        graph.add_edge(START, "router")
        graph.add_conditional_edges("router",route_next)
        graph.add_edge("research", "planner")
        graph.add_edge("planner", "hitl")
        graph.add_conditional_edges("hitl",check_approval)
        graph.add_conditional_edges("hitl", self.fanout, ["worker"])
        graph.add_edge("worker", "reducer")
        graph.add_edge("reducer", END)
        checkpoint = InMemorySaver()
        compiled_graph= graph.compile(checkpointer=checkpoint)
        return compiled_graph
    



async def main():
    
    # Set environment variable to handle msgpack serialization
    
    # Load environment variables from .env file
    load_dotenv()
    
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    # Use gemma-7b-it model (free, available on Groq)
    llm = ChatGroq(api_key=GROQ_API_KEY, model="meta-llama/llama-4-scout-17b-16e-instruct")
    # llm = ChatGoogleGenerativeAI(api_key=GEMINI_API_KEY, model="gemini-2.0-flash")
    checkpointer = InMemorySaver()

    
    
    # Create agent instance
    today = datetime.now().strftime("%Y-%m-%d")
    agent = BlogAgent(GROQ_API_KEY, llm=llm, checkpointer=checkpointer)
    config = {"configurable": {"thread_id": "2"}}
    compiled_graph = await agent.initialize_graph()
    # Run the agent asynchronously
    result = await compiled_graph.ainvoke({
        "prompt": "create a blog on python library numpy only make 1 querry",
        "tone": "informative",
        "recency_days": 7,
        "as_of": today
    }, config=config)

    # Handle interrupts in a loop until workflow completes
    while True:
        state = agent.compiled_graph.get_state(config)
            
        if not state.next:
            break  # Workflow completed
            
        user_input = input("approver: ")
        user_suggestions = input("Enter your suggestions: ")
        user_input = user_input.strip()
        user_suggestions = user_suggestions.strip()
        user_feedback_dict = {
            "approval": "approved" if user_input.lower() in ["yes", "approved"] else "rejected",
            "suggestions": user_suggestions
        }
        
        result = await agent.compiled_graph.ainvoke(
            Command(resume=user_feedback_dict),
                config=config
            )
        
        # print("Generated Blog Plan:")
        # print(result.get("plan", "No plan generated"))
        print("\nGenerated Content:")
        print(result.get("content", "No content generated"))
        print("\nSections:")
        print(len(result.get("sections", [])))
        print()
    
        
        
        
if __name__ == "__main__":    
    # Run the async main function
    try:
        asyncio.run(main())
    except Exception as e:
        import traceback
        traceback.print_exc()