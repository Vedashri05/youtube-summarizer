from typing import Optional

from pydantic import BaseModel

from app.models.response import SummaryResponse


class VideoJobCreated(BaseModel):
    job_id: int
    video_id: str
    status: str


class VideoStatusResponse(BaseModel):
    job_id: int
    video_id: str
    url: str
    mode: str
    # pending | transcribing | indexing | chunking | summarizing
    # | complete | failed
    status: str
    error: Optional[str] = None
    summary: Optional[SummaryResponse] = None
    created_at: str
    updated_at: str


class VideoListItem(BaseModel):
    job_id: int
    video_id: str
    url: str
    mode: str
    status: str
    created_at: str
    # None while still processing - the title only exists once the
    # summary has actually been generated, since it comes from Gemini's
    # output, not something the user types in.
    title: Optional[str] = None