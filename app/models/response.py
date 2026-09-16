from pydantic import BaseModel, Field


class KeyPoint(BaseModel):
    timestamp: str
    point: str


class SummaryContent(BaseModel):
    """
    Exactly the shape we ask Gemini to produce.

    Kept separate from SummaryResponse so that fields we add for the API
    (like video_id) never leak into the model's response schema - otherwise
    the model would try to invent a value for them.

    likely_interview_questions only gets populated in "interview_prep" mode
    (see gemini_service.py) - it stays an empty list for every other mode.
    It lives on the shared schema rather than a mode-specific one so a single
    response_schema config still works for every mode; the frontend simply
    doesn't render the section when the list is empty.
    """
    title: str
    overall_summary: str
    key_points: list[KeyPoint]
    topics_covered: list[str]
    likely_interview_questions: list[str] = Field(default_factory=list)


class SummaryResponse(SummaryContent):
    # Returned so the frontend knows which video to chat about.
    # Optional because older cached rows were saved without it.
    video_id: str | None = None

    # Echoed back so the frontend can highlight which mode is active,
    # even when the summary came from cache rather than a fresh generation.
    mode: str | None = None


class Source(BaseModel):
    """A citation pointing back into the video."""
    timestamp: str          # e.g. "38:42 - 41:15"
    start_seconds: float    # used to build the ?t=2322 deep link
    snippet: str            # the transcript text the answer came from


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]


class SearchResult(BaseModel):
    """One matching transcript moment for a semantic search query."""
    timestamp: str          # e.g. "38:42 - 41:15"
    start_seconds: float    # used to build the ?t=2322 deep link
    snippet: str            # the transcript text at that moment
    score: float            # cosine similarity, 0-1, higher = closer match


class SearchResponse(BaseModel):
    results: list[SearchResult]