from pydantic import BaseModel, Field
from typing import Literal


class InputQuery(BaseModel):
    query: str
    search_depth: Literal["basic", "advanced"] = "advanced"
    topic: Literal["news","general","finance"] = "general"


class ResearchResult(BaseModel):
    query: str = Field(..., description="The original query that was searched.")
    raw_content: str = Field(..., description="The combined raw content extracted from relevant URLs for this query.")