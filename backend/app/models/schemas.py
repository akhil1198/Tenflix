from pydantic import BaseModel
from typing import List


class QueryRequest(BaseModel):
    query: str


class RecommendationRequest(BaseModel):
    preferences: str


class ComparisonRequest(BaseModel):
    titles: List[str]
