import re
from app.services.transcript_service import format_timestamp
from fastapi import HTTPException

# Regular expression to match common YouTube URL formats
YOUTUBE_REGEX = (
    r"(?:https?:\/\/)?"
    r"(?:www\.)?"
    r"(?:youtube\.com\/(?:watch\?v=|embed\/|shorts\/)|youtu\.be\/)"
    r"([A-Za-z0-9_-]{11})"
)

def extract_video_id(url: str) -> str:
    """
    Extract the YouTube video ID from different URL formats.

    Parameters:
        url (str): YouTube URL

    Returns:
        str: Video ID

    Raises:
        HTTPException: If the URL is invalid.
    """

    match = re.search(YOUTUBE_REGEX, url)

    if not match:
        raise HTTPException(
            status_code=400,
            detail="Invalid YouTube URL."
        )

    return match.group(1)


# Creating chunks function
def chunk_transcript(transcript, chunk_size=500):
    """
    Parameters:
        transcript (list): Transcript returned by youtube-transcript-api
        chunk_size (int): Number of transcript entries per chunk

    Returns:
        list[str]
    """

    chunks = []
    current_chunk = []

    for item in transcript:

        timestamp = format_timestamp(item.start)
        line = f"[{timestamp}] {item.text}"

        current_chunk.append(line)

        if len(current_chunk) >= chunk_size:

            chunks.append("\n".join(current_chunk))

            current_chunk = []

    if current_chunk:
        chunks.append("\n".join(current_chunk))

    return chunks