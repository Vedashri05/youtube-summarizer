from pydantic import BaseModel

class KeyPoint(BaseModel):
    timestamp: str
    point: str


class SummaryResponse(BaseModel):
    title: str
    overall_summary: str
    key_points: list[KeyPoint]
    topics_covered: list[str]