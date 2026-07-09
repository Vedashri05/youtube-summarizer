from fastapi import FastAPI
from app.models.response import SummaryResponse
from app.utils.helpers import chunk_transcript
from app.services.gemini_service import combine_summaries
import json

from app.services.transcript_service import (
    fetch_transcript,
    transcript_to_text
)
from app.services.gemini_service import summarize_transcript
from app.services.cache_service import initialize_database

app = FastAPI()

initialize_database()


@app.get("/transcript/{video_id}")
async def transcript(video_id: str):

    transcript = fetch_transcript(video_id)

    chunks = chunk_transcript(transcript)

    print(len(chunks))


@app.get("/summary/{video_id}",response_model=SummaryResponse)
async def summary(video_id: str):

    transcript = fetch_transcript(video_id)

    summaries=[]
    chunks=chunk_transcript(transcript)

    # FastAPI automatically converts the Pydantic model to JSON
    for chunk in chunks:
        summary = summarize_transcript(chunk)
        summaries.append(summary)

    final_summary = combine_summaries(summaries)

    return final_summary
  