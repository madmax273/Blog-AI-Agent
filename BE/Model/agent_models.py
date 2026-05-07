from pydantic import BaseModel, Field
from typing import TypedDict, List, Literal, Annotated, Optional
import operator


class Task(BaseModel):
    id: int
    title: str

    goal: str = Field(
        ...,
        description="One sentence describing what the reader should be able to do/understand after this section.",
    )
    bullets: List[str] = Field(
        ...,
        min_length=3,
        max_length=5,
        description="3–5 concrete, non-overlapping subpoints to cover in this section.",
    )
    target_words: int = Field(
        ...,
        description="Target word count for this section (120–450).",
    )
    target_words: int = Field(..., description="Target word count for this section (120–550).")

    tags: List[str] = Field(default_factory=list)
    requires_research: bool = False
    requires_citations: bool = False
    requires_code: bool = False

class Plan(BaseModel):
    blog_title: str
    audience: str = Field(..., description="Who this blog is for.")
    tone: str = Field(..., description="Writing tone (e.g., practical, crisp).")
    tasks: List[Task]
    # NEW: tells workers what genre this is (prevents drift)
    blog_kind: Literal["explainer", "tutorial", "news_roundup", "comparison", "system_design"] = "explainer"
    constraints: List[str] = Field(default_factory=list)  

class RouterOutput(BaseModel):
    needs_research: bool = Field(..., description="Must be a boolean: True or False (not a string)")
    mode: Literal["closed_book", "hybrid", "open_book"] = Field(..., description="One of: closed_book, hybrid, open_book")
    queries: List[str] = Field(default_factory=list, description="List of search queries if needs_research is true")

class EvidenceItem(BaseModel):
    title: str
    url: str
    published_at: Optional[str] = None  # prefer ISO "YYYY-MM-DD"
    snippet: Optional[str] = None
    source: Optional[str] = None

class EvidencePack(BaseModel):
    items: List[EvidenceItem]

class ImageSpec(BaseModel):
    placeholder: str = Field(..., description="e.g. [[IMAGE_1]]")
    filename: str = Field(..., description="Save under images/, e.g. qkv_flow.png")
    alt: str
    caption: str
    prompt: str = Field(..., description="Prompt to send to the image model.")
    size: Literal["1024x1024", "1024x1536", "1536x1024"] = "1024x1024"
    quality: Literal["low", "medium", "high"] = "medium"


class GlobalImagePlan(BaseModel):
    md_with_placeholders: str
    images: List[ImageSpec] = Field(default_factory=list)

class BlogAgentState(TypedDict):
    prompt: str
    
    approval: str
    tone: str
    content: str
    topic: str
    as_of: str   # ISO date, e.g. "2026-01-29"
    
    #fanout
    sections: Annotated[List[tuple[int, str]], operator.add]  # (task_id, section_md)


    #plan
    plan: Plan

    #research    
    evidence: List[EvidenceItem]
    

    #router
    recency_days: int    # 7 for weekly news, 30 for hybrid, etc.
    mode:Literal["closed_book","open_book","hybrid"]
    queries: List[str]
    needs_research: bool 

    #reducer
    merged_md: str
    md_with_placeholders: str
    image_specs: List[dict]
    markdown_content: str

