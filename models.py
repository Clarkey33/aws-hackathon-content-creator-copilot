from pydantic import BaseModel, Field,conint
from typing import Literal, List,Annotated


class InputQuery(BaseModel):
    query: str
    search_depth: Literal["basic", "advanced"] = "advanced"
    topic: Literal["news","general","finance"] = "general"
    include_answer: Literal["true","basic","advanced"] = "advanced"
    max_results: Annotated[int, Field(default=3, ge=1, le=5)]
    #chunks_per_source: Annotated[int, Field(default=3, ge=1, le=3)]

class ResearchToolArgs(BaseModel):
    queries: List[InputQuery] = Field(..., description="A list of 2-3 focused search query objects based on the user's topic.")

class ResearchResult(BaseModel):
    #query: str = Field(..., description="The original query that was searched.")
    #raw_content: str = Field(..., description="The combined raw content extracted from relevant URLs for this query.")
    s3_uri: str = Field(..., description="The combined raw content extracted from relevant URLs saved to s3 bucket.")
    research_summary: str = Field(..., description= "A summary response to the search query")