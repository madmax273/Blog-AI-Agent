from fastapi.openapi.models import OAuthFlowClientCredentials
from langchain_core.prompts import PromptTemplate
from langgraph.graph import StateGraph, END,START
from typing import Dict, Any
from langchain_groq import ChatGroq
import os
import sys
from pathlib import Path
from langgraph.types import Send
from langchain_core.messages import SystemMessage, HumanMessage

# Add parent directory to Python path for direct execution
#TODO: Remove this when running as a module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langgraph.types import interrupt,Command
from typing_extensions import   TypedDict
from langgraph.checkpoint.memory import InMemorySaver
from Models.agent_models import BlogAgentState,Plan
from utils.agent_prompts import PLANNING_PROMPT,GENERATOR_PROMPT


def check_approval(state: BlogAgentState)->str:
    """
    Check if the plan is approved or not
    """
    if state["approval"] == "approved":
        return "generate"
    else:
        return "planner"




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

    async def planner_node(self, state: BlogAgentState):
            # 1. Bind the structured output to the LLM
            structured_llm = self.llm.with_structured_output(Plan)
            
            # 2. Define the template
            prompt_template = PromptTemplate.from_template(PLANNING_PROMPT)
            
            # 3. Create the chain (Template -> LLM)
            # The prompt_template will format the input, then pass it to the LLM
            chain = prompt_template | structured_llm
            
            # 4. Invoke the chain
            response = await chain.ainvoke({
                "user_prompt": state["prompt"],
                "tone": state["tone"]
            })
            
            return {
                "plan": response, 
                "topic": state["prompt"]
            }  

    async def hitl_node(self,state: BlogAgentState):
        plan_generated=state["plan"]
        
        message_for_hitl=interrupt(f"Plan generated: {plan_generated}\nDo you like the plan? (yes/no): or you have some feedback? ")
        
        print("Plan generated:", plan_generated)
        
        print("Message for hitl:", message_for_hitl)
        if message_for_hitl["approval"] != "approved":
            return {"approval": "rejected"}
        
        return {"approval": "approved"}    
    
    # async def generate_node(self, state: BlogAgentState):


    #     prompt = """
    #     you are a content generator agent, you need to generate the blog content based on the plan given by the planner agent
        
    #     {plan}
    #     """
    #     prompt_template=PromptTemplate(template=prompt, input_variables=["plan"])
        
    #     llm = ChatGroq(api_key=self.api_key, model="llama-3.1-8b-instant")
    #     chain = prompt_template | llm
        
    #     response = await chain.ainvoke({"plan": state["plan"]})
    #     return {"content": response.content}

    async def fanout(aelf,state: BlogAgentState):
        return [
            Send(
                "worker",
                {"task": task, "topic": state["topic"], "plan": state["plan"]},
            )
            for task in state["plan"].tasks
        ]

    async def worker(self,payload: dict) -> dict:

        task = payload["task"]
        topic = payload["topic"]
        plan = payload["plan"]

        bullets_text = "\n- " + "\n- ".join(task.bullets)
        response = await self.llm.ainvoke(
            [
                SystemMessage(
        content=(
        GENERATOR_PROMPT
        )
    )
    ,
                HumanMessage(
                    content=(
                        f"Blog: {plan.blog_title}\n"
                        f"Audience: {plan.audience}\n"
                        f"Tone: {plan.tone}\n"
                        f"Topic: {topic}\n\n"
                        f"Section: {task.title}\n"
                        f"Section type: {task.section_type}\n"
                        f"Goal: {task.goal}\n"
                        f"Target words: {task.target_words}\n"
                        f"Bullets:{bullets_text}\n"
                    )
                ),
            ]
        )
        section_md = response.content.strip()

        return {"sections": [section_md]}
    

    # async def converter_node(self, state: BlogAgentState):
    #     content=state["content"]
        
    #     prompt = """convert the following content to markdown format
        
    #     {content}
    #     """
    #     prompt_template=PromptTemplate(template=prompt, input_variables=["content"])
        
    #     llm = ChatGroq(api_key=self.api_key, model="llama-3.1-8b-instant")
    #     chain = prompt_template | llm
        
    #     response = await chain.ainvoke({"content": content})
    #     return {"markdown_content": response.content}
       
    async def reducer(self, state: BlogAgentState) -> dict:

        title = state["plan"].blog_title
        body = "\n\n".join(state["sections"]).strip()
        
        final_md = f"# {title}\n\n{body}\n"

        # Save to file
        filename = "".join(c if c.isalnum() or c in (" ", "_", "-") else "" for c in title)
        filename = filename.strip().lower().replace(" ", "_") + ".md"
        Path(filename).write_text(final_md, encoding="utf-8")

        return {"markdown_content": final_md}
       


    async def _build_graph(self):
        graph = StateGraph(BlogAgentState)
        graph.add_node("planner", self.planner_node)
        graph.add_node("hitl", self.hitl_node)
        graph.add_node("worker", self.worker)
        graph.add_node("reducer", self.reducer)
        
        graph.add_edge(START, "planner")
        graph.add_edge("planner", "hitl")
        graph.add_conditional_edges("hitl",check_approval)
        graph.add_conditional_edges("hitl", self.fanout, ["worker"])
        graph.add_edge("worker", "reducer")
        graph.add_edge("reducer", END)
        checkpoint = InMemorySaver()
        compiled_graph= graph.compile(checkpointer=checkpoint)
        return compiled_graph
    



if __name__ == "__main__":
    import os
    import asyncio
    from dotenv import load_dotenv
    
    # Load environment variables from .env file
    load_dotenv()
    
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
    llm = ChatGroq(api_key=GROQ_API_KEY, model="llama-3.1-8b-instant")
    checkpointer = InMemorySaver()
    
    async def main():
        # Create agent instance
        agent = BlogAgent(GROQ_API_KEY, llm=llm, checkpointer=checkpointer)
        config = {"configurable": {"thread_id": "1"}}
        compiled_graph = await agent.initialize_graph()
        # Run the agent asynchronously
        result = await compiled_graph.ainvoke({
            "prompt": "Write a blog about AI in just 500 words",
            "tone": "informative"
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
        print(result.get("sections", "No sections generated"))
    
        
        
        
    
    # Run the async main function
    asyncio.run(main())
