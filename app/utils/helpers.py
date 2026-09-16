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
    """

    match = re.search(YOUTUBE_REGEX, url)

    if not match:
        raise HTTPException(
            status_code=400,
            detail="Invalid YouTube URL."
        )

    return match.group(1)


# ---------------------------------------------------------------------------
# Chunking for SUMMARISATION (map-reduce)
# Big chunks are fine here: we want each chunk to cover a large slice of the
# video so the model can write a meaningful partial summary.
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Chunking for RETRIEVAL (RAG)
# Completely different goal from the chunking above.
#
# For retrieval we want chunks that are:
#   - SMALL   -> one chunk = roughly one idea, so the embedding is focused
#   - OVERLAPPING -> so an explanation that straddles a boundary is not cut
#                    in half and lost
#   - TIME-AWARE   -> every chunk remembers its start/end second, which is
#                     what lets us cite "38:42 - 41:15" later
# ---------------------------------------------------------------------------
def build_retrieval_chunks(
    transcript,
    max_chars: int = 900,
    overlap_chars: int = 200,
):
    """
    Turn raw transcript entries into overlapping, timestamped chunks.

    Parameters:
        transcript (list): Transcript returned by youtube-transcript-api.
                           Each item has .text, .start, .duration
        max_chars (int): Target size of one chunk in characters
                         (~900 chars is roughly 40-60 seconds of speech)
        overlap_chars (int): How much text to repeat from the previous chunk

    Returns:
        list[dict]: [{"start": float, "end": float, "text": str}, ...]
    """

    # Normalise the transcript items into plain dicts first.
    # (youtube-transcript-api returns objects; dicts are easier to slice.)
    entries = []

    for item in transcript:
        text = getattr(item, "text", None)
        start = getattr(item, "start", None)
        duration = getattr(item, "duration", 0.0)

        # Fallback in case a dict-style transcript is passed in
        if text is None and isinstance(item, dict):
            text = item.get("text", "")
            start = item.get("start", 0.0)
            duration = item.get("duration", 0.0)

        text = (text or "").strip()

        if not text:
            continue

        entries.append({
            "text": text,
            "start": float(start or 0.0),
            "end": float(start or 0.0) + float(duration or 0.0),
        })

    chunks = []
    current = []          # list of entries in the chunk being built
    current_len = 0

    for entry in entries:

        current.append(entry)
        current_len += len(entry["text"]) + 1

        if current_len >= max_chars:

            chunks.append({
                "start": current[0]["start"],
                "end": current[-1]["end"],
                "text": " ".join(e["text"] for e in current),
            })

            # Build the overlap: walk backwards from the end of this chunk
            # and keep entries until we have ~overlap_chars of text.
            tail = []
            tail_len = 0

            for entry_back in reversed(current):

                if tail_len >= overlap_chars:
                    break

                tail.insert(0, entry_back)
                tail_len += len(entry_back["text"]) + 1

            current = tail
            current_len = tail_len

    # Flush whatever is left, as long as it is not just leftover overlap
    if current and len(" ".join(e["text"] for e in current)) > overlap_chars // 2:

        chunks.append({
            "start": current[0]["start"],
            "end": current[-1]["end"],
            "text": " ".join(e["text"] for e in current),
        })

    return chunks