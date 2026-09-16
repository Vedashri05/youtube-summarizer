from pydantic import BaseModel, Field
from typing import Literal

# The four "products" one transcript can become. Kept as a Literal (not a
# free string) so FastAPI/Pydantic rejects an invalid mode at the request
# boundary instead of it silently falling through to the default prompt.
SummaryMode = Literal["beginner", "technical", "quick_revision", "interview_prep"]


class SummaryRequest(BaseModel):
    url: str

    # Defaults to "technical" so any old frontend code (or a manual request
    # with no mode field) keeps behaving exactly like it did before this
    # feature existed.
    mode: SummaryMode = "technical"


class ChatMessage(BaseModel):
    """One turn of the conversation, sent back by the frontend."""
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    # We send the video_id (not the URL) because by this point the video is
    # already processed and indexed under that id.
    video_id: str
    question: str

    # The backend stays stateless: the client owns the conversation and
    # replays it. Trimmed to the recent turns to keep the payload small.
    history: list[ChatMessage] = Field(default_factory=list)


class SearchRequest(BaseModel):
    video_id: str
    query: str