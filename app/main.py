from fastapi import FastAPI
from app.models.response import SummaryResponse
from app.utils.helpers import chunk_transcript
from app.services.gemini_service import combine_summaries
import json
from fastapi.middleware.cors import CORSMiddleware
from app.models.request import SummaryRequest
from app.utils.helpers import extract_video_id

from app.services.transcript_service import (
    fetch_transcript,
    transcript_to_text
)
from app.services.gemini_service import summarize_transcript
from app.services.cache_service import initialize_database
from app.services.cache_service import (
    save_summary,
    get_summary
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

initialize_database()


@app.post("/summary",response_model=SummaryResponse)
async def summary(request: SummaryRequest):

    video_id = extract_video_id(request.url)
     # Step 1: Check cache
    cached_summary = get_summary(video_id)

    if cached_summary:
        print("Returning summary from cache")
        return cached_summary
    
    print("Generating the summary...")

    # Step 2: Fetch transcript
    transcript = fetch_transcript(video_id)

    # Step 3: Split transcript into chunks
    chunks=chunk_transcript(transcript)

    # Step 4: Summarize each chunk
    summaries=[]

    # FastAPI automatically converts the Pydantic model to JSON
    for chunk in chunks:
        summary = summarize_transcript(chunk)
        summaries.append(summary)

    # Step 5: Combine summaries
    final_summary = combine_summaries(summaries)

    # Step 6: Save in cache
    save_summary(video_id, final_summary.model_dump())

    return final_summary
  