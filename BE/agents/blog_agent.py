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
from typing_extensions import TypedDict
from langgraph.checkpoint.base import BaseCheckpointSaver
from Model.agent_models import BlogAgentState,Plan,RouterOutput,EvidencePack,EvidenceItem,Task
from utils.agent_prompts import PLANNING_PROMPT,GENERATOR_PROMPT,ROUTER_PROMPT,RESEARCH_PROMPT
from dotenv import load_dotenv
from datetime import datetime, date, timedelta
from agents.sub_graph import create_reducer_subgraph
from config.logging import get_logger
import asyncio

logger=get_logger()

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
    try:
        tool = TavilySearch(max_results=max_results)
        results = tool.invoke({"query": query})
    except Exception as e:
        logger.error(f"Tavily search failed: {str(e)}")
        return []
    
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
    logger.info(f"Tavily searched results no of items searched: {len(normalized)}")    
    return normalized   

def route_next(state: BlogAgentState) -> str:
    logger.info(f"Routing to research or planner based on needs_research: {state['needs_research']}")
    return "research" if state["needs_research"] is True else "planner"      


class BlogAgent:
    
    def __init__(self, api_key: str, llm: ChatGroq, checkpointer: BaseCheckpointSaver):
        self.graph = None
        self.api_key = api_key
        self.compiled_graph = None
        self.llm = llm
        self.checkpointer = checkpointer
    
    async def initialize_graph(self):
        try:
            logger.info("Initializing graph")
            if self.compiled_graph is None:
                self.compiled_graph = await self._build_graph()
            return self.compiled_graph
        except Exception as e:
            logger.log_error_with_context(e, "Error initializing graph")
            raise

    async def router_node(self, state: BlogAgentState) -> dict:
        try:
            logger.info("Router node started")
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

            logger.info(f"Router decision: {decision}, Recency days: {recency_days}")

            return {
                "needs_research": str(decision.needs_research).lower() == "true",
                "mode": decision.mode,
                "queries": decision.queries,
                "recency_days": recency_days,
                "topic": topic,
                "error": None
            }
        except Exception as e:
            logger.log_error_with_context(e, "Error in router_node")
            # Return safe defaults on error
            return {
                "needs_research": False,
                "mode": "closed_book",
                "queries": [],
                "recency_days": 3650,
                "topic": state.get("prompt", ""),
                "error": str(e)
            }
 
    async def research_node(self, state: BlogAgentState) -> dict:
        try:
            logger.info("Research node started")
            queries = (state.get("queries", []) or [])[:10]
            max_results = 2

            raw_results: List[dict] = []
            for q in queries:
                try:
                    raw_results.extend(_tavily_search(q, max_results=max_results))
                except Exception as e:
                    logger.warning(f"Error searching for query '{q}': {str(e)}")
                    continue

            logger.info(f"Tavily search results count: {len(raw_results)}")

            if not raw_results:
                logger.warning("No search results found, returning empty evidence")
                return {"evidence": [], "error": None}

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

            logger.info(f"Evidence pack extracted with {len(pack.items)} items")

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
                try:
                    as_of = date.fromisoformat(state["as_of"])
                    cutoff = as_of - timedelta(days=int(state["recency_days"]))
                    fresh: List[EvidenceItem] = []
                    for e in evidence:
                        d = _iso_to_date(e.published_at)
                        if d and d >= cutoff:
                            fresh.append(e)

                    evidence = fresh
                except Exception as e:
                    logger.warning(f"Error in recency filtering: {str(e)}")

            logger.info(f"Filtered evidence count: {len(evidence)}")
            return {"evidence": evidence, "error": None}
        except Exception as e:
            logger.log_error_with_context(e, "Error in research_node")
            return {"evidence": [], "error": str(e)}

    async def planner_node(self, state: BlogAgentState):
        try:
            logger.info("Planner node started")
            planner = self.llm.with_structured_output(Plan)
            evidence = state.get("evidence", [])
            mode = state.get("mode", "closed_book")

            logger.info(f"Evidence count: {len(evidence)}, Mode: {mode}")

            # Force blog_kind for open_book
            forced_kind = "news_roundup" if mode == "open_book" else None

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

            logger.info(f"Plan generated: Title={plan.blog_title}, Tasks={len(plan.tasks)}")
            for i, task in enumerate(plan.tasks):
                logger.info(f"  Task {i+1}: {task.title} (target_words={task.target_words})")

            # Ensure open_book forces the kind even if model forgets
            if forced_kind:
                plan.blog_kind = "news_roundup"

            # Convert Plan to dict for serialization
            logger.info(f"Planning node done moving to HITL")
            return {"plan": plan.model_dump(), "error": None}
        except Exception as e:
            logger.log_error_with_context(e, "Error in planner_node")
            # Return a minimal fallback plan on error
            fallback_plan = Plan(
                blog_title=state.get("topic", "Untitled Blog"),
                audience="general",
                tone="informative",
                tasks=[
                    Task(
                        id=1,
                        title="Introduction",
                        goal="Introduce the topic",
                        bullets=["Overview", "Background", "Context"],
                        target_words=200
                    )
                ]
            )
            return {"plan": fallback_plan.model_dump(), "error": str(e)}

    async def hitl_node(self,state: BlogAgentState):
        logger.info("HITL node started")
        plan_data = state["plan"]
        plan = Plan(**plan_data) if isinstance(plan_data, dict) else plan_data
        plan_generated=plan

        message_for_hitl=interrupt(f"Plan generated: {plan_generated}\nDo you like the plan? (yes/no): or you have some feedback? ")

        logger.info(f"Plan generated: {plan_generated}")
        logger.info(f"User feedback: {message_for_hitl}")

        if message_for_hitl["approval"] != "approved":
            return {"approval": "rejected"}

        return {"approval": "approved"}    
    
    async def fanout(self,state: BlogAgentState):
        try:
            logger.info("Fanout node started")
            plan_data = state["plan"]
            plan = Plan(**plan_data) if isinstance(plan_data, dict) else plan_data
            evidence = state.get("evidence", [])
            logger.info(f"Fanout: Creating {len(plan.tasks)} worker tasks")
            return [
                Send(
                    "worker",
                    {"task": task, "topic": state["topic"], "plan": plan, "mode":state.get("mode", "closed_book"),"evidence":evidence},
                )
                for task in plan.tasks
            ]
        except Exception as e:
            logger.log_error_with_context(e, "Error in fanout")
            # Return empty list on error to prevent workflow break
            return []

    async def worker(self,payload: dict) -> dict:
        try:
            logger.info(f"Worker node started for task")
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
            logger.info(f"Worker completed section {task.id}")

            return {"sections": [(task.id, section_md)]}
        except Exception as e:
            logger.log_error_with_context(e, "Error in worker node for task")
            # Return error section on failure
            error_section = f"## {task.title}\n\n**Error generating section**: {str(e)}"
            return {"sections": [(task.id, error_section)]}
      
    async def reducer(self, state: BlogAgentState) -> dict:
        try:
            logger.info("Reducer node started")
            plan_data = state["plan"]
            plan = Plan(**plan_data) if isinstance(plan_data, dict) else plan_data

            title = plan.blog_title

            # Sort sections by task ID and extract the markdown content
            sorted_sections = sorted(state["sections"], key=lambda x: x[0])
            body = "\n\n".join(section_md for _, section_md in sorted_sections).strip()

            final_md = f"# {title}\n\n{body}\n"
            logger.info(f"Reducer merged {len(sorted_sections)} sections")

            # Convert markdown to HTML
            import markdown2
            final_html = markdown2.markdown(
                final_md,
                extras=[
                    "fenced-code-blocks",
                    "tables",
                    "header-ids",
                    "strike",
                    "target-blank-links",
                    "nofollow",
                    "toc",
                    "smarty-pants"
                ]
            )
            logger.info("Converted markdown to HTML in reducer")
            logger.debug(f"HTML preview: {final_html[:500]}...")

            return {"markdown_content": final_md, "html_content": final_html, "error": None}
        except Exception as e:
            logger.log_error_with_context(e, "Error in reducer")
            # Return fallback markdown on error
            fallback_md = f"# Error\n\nAn error occurred while generating the blog: {str(e)}"
            import markdown2
            fallback_html = markdown2.markdown(fallback_md, extras=["fenced-code-blocks", "tables", "header-ids"])
            return {"markdown_content": fallback_md, "html_content": fallback_html, "error": str(e)}
       


    async def _build_graph(self):
        try:
            logger.info("Building graph")
            graph = StateGraph(BlogAgentState)
            graph.add_node("router", self.router_node)
            graph.add_node("research", self.research_node)
            graph.add_node("planner", self.planner_node)
            graph.add_node("hitl", self.hitl_node)
            graph.add_node("worker", self.worker)

            # Create and add the reducer subgraph
            try:
                reducer_subgraph = create_reducer_subgraph(self.llm)
                graph.add_node("reducer", reducer_subgraph)
                logger.info("Reducer subgraph added successfully")
            except Exception as e:
                logger.log_error_with_context(e, "Error creating reducer subgraph")
                # Fallback to simple reducer if subgraph fails
                graph.add_node("reducer", self.reducer)
                logger.warning("Using fallback reducer instead of subgraph")

            graph.add_edge(START, "router")
            graph.add_conditional_edges("router",route_next)
            graph.add_edge("research", "planner")
            graph.add_edge("planner", "hitl")
            graph.add_conditional_edges("hitl",check_approval)
            graph.add_conditional_edges("hitl", self.fanout, ["worker"])
            graph.add_edge("worker", "reducer")
            graph.add_edge("reducer", END)

            compiled_graph= graph.compile(checkpointer=self.checkpointer)
            logger.info("Graph built successfully")
            return compiled_graph
        except Exception as e:
            logger.log_error_with_context(e, "Error building graph")
            raise
    



async def main():
    
    # Set environment variable to handle msgpack serialization
    
    # Load environment variables from .env file
    load_dotenv()
    
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    # Use gemma-7b-it model (free, available on Groq)
    llm = ChatGroq(api_key=GROQ_API_KEY, model="meta-llama/llama-4-scout-17b-16e-instruct")
    # llm = ChatGoogleGenerativeAI(api_key=GEMINI_API_KEY, model="gemini-2.0-flash")
    
    import aiosqlite
    from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
    conn = aiosqlite.connect("blog_agent_checkpoints.db")
    checkpointer = AsyncSqliteSaver(conn)

    
    
    # Create agent instance
    today = datetime.now().strftime("%Y-%m-%d")
    # Use unique thread_id for each run to prevent state accumulation
    import uuid
    thread_id = str(uuid.uuid4())
    agent = BlogAgent(GROQ_API_KEY, llm=llm, checkpointer=checkpointer)
    config = {"configurable": {"thread_id": thread_id}}
    compiled_graph = await agent.initialize_graph()
    # Run the agent asynchronously
    result = await compiled_graph.ainvoke({
        "prompt": "create a blog on IPL 2026.",
        "tone": "informative",
        "recency_days": 7,
        "as_of": today
    }, config=config)

    # Handle interrupts in a loop until workflow completes
    while True:
        state = await agent.compiled_graph.aget_state(config)

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