from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    NoTranscriptFound,
    TranscriptsDisabled,
)
from fastapi import HTTPException

yt_api=YouTubeTranscriptApi()

def fetch_transcript(video_id: str):

    try:
        transcript = yt_api.fetch(video_id)

        return transcript

    except NoTranscriptFound:

        raise HTTPException(
            status_code=404,
            detail="Transcript not found."
        )

    except TranscriptsDisabled:

        raise HTTPException(
            status_code=403,
            detail="Transcripts are disabled for this video."
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
    
def format_timestamp(seconds: float) -> str:

    total_seconds = int(seconds)

    minutes = total_seconds // 60

    seconds = total_seconds % 60

    return f"{minutes:02}:{seconds:02}"


def transcript_to_text(transcript):

    lines = []
    for item in transcript:

        timestamp = format_timestamp(item.start)
        text = item.text
        lines.append(f"[{timestamp}] {text}")

    return "\n".join(lines)