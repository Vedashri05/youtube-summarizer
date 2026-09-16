"""
Retrieval-Augmented Generation over a single video's transcript.

The pipeline, end to end:

    INDEX (once per video)
        transcript -> overlapping timestamped chunks -> embeddings -> SQLite

    QUERY (every question)
        question (+ chat history) -> standalone question
                                  -> query embedding
                                  -> cosine top-k chunks
                                  -> prompt with numbered context
                                  -> model returns {answer, used_chunk_ids}
                                  -> we map ids back to real timestamps

    SEARCH (semantic search, no LLM call)
        query -> query embedding -> cosine top-k chunks -> return them
        directly, ranked by score. This is the same index and the same
        embed_query()/cosine_top_k() as chat - it just skips the generation
        step and hands the raw matches back.
"""

from fastapi import HTTPException
from google import genai
from google.genai.errors import ClientError, ServerError
from pydantic import BaseModel

from app.config import settings
from app.models.response import ChatResponse, SearchResponse, SearchResult, Source
from app.services.cache_service import (
    get_chunks,
    is_video_indexed,
    save_chunks,
)
from app.services.embedding_service import (
    cosine_top_k,
    embed_documents,
    embed_query,
)
from app.services.transcript_service import fetch_transcript, format_timestamp
from app.utils.helpers import build_retrieval_chunks

client = genai.Client(api_key=settings.GEMINI_API_KEY)

TOP_K = 5

# Below this cosine score a chunk is almost certainly unrelated to the
# question. Filtering here is what lets the app say "the video does not
# cover that" instead of confidently answering from noise.
MIN_SCORE = 0.45


def _snippet(text: str, max_chars: int = 280) -> str:
    """
    Truncate at the last whole word instead of a raw character cut.

    text[:280] can land mid-word ("...and you"), which looks broken in the
    UI. Cutting back to the last space and adding an ellipsis reads as an
    intentional excerpt instead of a bug.
    """

    if len(text) <= max_chars:
        return text

    truncated = text[:max_chars].rsplit(" ", 1)[0]

    return truncated + "..."


# ---------------------------------------------------------------------------
# Internal schema: what we force the model to return.
#
# Note that the model is NOT asked for timestamps. It only reports WHICH
# numbered context blocks it used. We look the timestamps up ourselves from
# the database. A model asked to echo a timestamp will eventually invent one;
# a model asked to return "[3]" either returns a valid id or it does not.
# ---------------------------------------------------------------------------
class _GroundedAnswer(BaseModel):
    answer: str
    used_chunk_ids: list[int]


ANSWER_PROMPT = """
You are answering questions about a YouTube video, using ONLY the transcript
excerpts provided below.

Rules:

1. Answer ONLY from the excerpts. Never use outside knowledge, even if you
   are confident it is correct.
2. If the excerpts do not contain the answer, say clearly that the video does
   not cover it, and return an empty used_chunk_ids list.
3. In used_chunk_ids, list the numbers of the excerpts you actually relied on.
   Do not list an excerpt you did not use.
4. Write 2-5 sentences in plain language. Explain the idea, do not just quote.
5. Do not mention "excerpts", "transcript" or "context" in your answer. Write
   as if you are explaining what the video says.
6. Do not use markdown.
"""

CONDENSE_PROMPT = """
Rewrite the follow-up question as a standalone question that makes sense on
its own, resolving pronouns like "it", "that" or "this" using the chat
history. Return ONLY the rewritten question, nothing else. If the question is
already standalone, return it unchanged.
"""


# ---------------------------------------------------------------------------
# Indexing
# ---------------------------------------------------------------------------
def ensure_video_indexed(video_id: str, transcript=None):
    """
    Chunk + embed a video if it has not been indexed yet.

    Safe to call on every request: if the index already exists this is a
    single cheap SQLite lookup and nothing else happens.
    """

    if is_video_indexed(video_id):
        return

    if transcript is None:
        transcript = fetch_transcript(video_id)

    chunks = build_retrieval_chunks(transcript)

    if not chunks:
        raise HTTPException(
            status_code=404,
            detail="Transcript is empty, nothing to index."
        )

    embeddings = embed_documents([chunk["text"] for chunk in chunks])

    save_chunks(video_id, chunks, embeddings)


# ---------------------------------------------------------------------------
# Query rewriting (handles follow-up questions)
# ---------------------------------------------------------------------------
def condense_question(question: str, history: list) -> str:
    """
    "Why is that a problem?" is useless as a search query on its own - the
    embedding of it is meaningless. We rewrite it against the chat history
    into something like "Why are unscaled features a problem for gradient
    descent?", which retrieves properly.

    Only runs when there is history, so the first question costs nothing.
    """

    if not history:
        return question

    recent = history[-4:]

    conversation = "\n".join(
        f"{message.role}: {message.content}"
        for message in recent
    )

    try:
        response = client.models.generate_content(
            model=settings.MODEL,
            contents=(
                f"{CONDENSE_PROMPT}\n\n"
                f"Chat history:\n{conversation}\n\n"
                f"Follow-up question: {question}"
            ),
        )

    except (ServerError, ClientError):
        # Rewriting is a nice-to-have. If it fails, search the raw question.
        return question

    rewritten = (response.text or "").strip()

    return rewritten or question


# ---------------------------------------------------------------------------
# Answering
# ---------------------------------------------------------------------------
def answer_question(video_id: str, question: str, history: list) -> ChatResponse:

    chunks, matrix = get_chunks(video_id)

    if not chunks:
        raise HTTPException(
            status_code=404,
            detail="This video has not been processed yet. Summarize it first."
        )

    # 1. Make the question searchable on its own
    search_query = condense_question(question, history)

    # 2. Embed it and find the closest chunks
    query_vector = embed_query(search_query)

    hits = cosine_top_k(query_vector, matrix, k=TOP_K)

    hits = [(index, score) for index, score in hits if score >= MIN_SCORE]

    if not hits:
        return ChatResponse(
            answer="I could not find anything in this video that answers that question.",
            sources=[],
        )

    # 3. Build a numbered context block.
    #    The numbers are what the model cites, and what we map back.
    retrieved = [chunks[index] for index, _ in hits]

    context = "\n\n".join(
        f"[{position + 1}] {chunk['text']}"
        for position, chunk in enumerate(retrieved)
    )

    try:
        response = client.models.generate_content(
            model=settings.MODEL,
            contents=(
                f"{ANSWER_PROMPT}\n\n"
                f"Transcript excerpts:\n{context}\n\n"
                f"Question: {question}"
            ),
            config={
                "response_mime_type": "application/json",
                "response_schema": _GroundedAnswer,
            },
        )

    except ServerError:
        raise HTTPException(
            status_code=503,
            detail="Gemini service is temporarily unavailable. Please try again later."
        )

    except ClientError as e:
        raise HTTPException(status_code=400, detail=str(e))

    grounded = _GroundedAnswer.model_validate_json(response.text)

    # 4. Turn the cited ids back into real, verified timestamps.
    sources = []

    for cited_id in grounded.used_chunk_ids:

        position = cited_id - 1

        # Silently drop anything out of range instead of trusting it
        if position < 0 or position >= len(retrieved):
            continue

        chunk = retrieved[position]

        sources.append(
            Source(
                timestamp=(
                    f"{format_timestamp(chunk['start'])}"
                    f" - {format_timestamp(chunk['end'])}"
                ),
                start_seconds=chunk["start"],
                snippet=_snippet(chunk["text"], max_chars=200),
            )
        )

    return ChatResponse(answer=grounded.answer, sources=sources)


# ---------------------------------------------------------------------------
# Semantic search
#
# Deliberately the simplest function in this file: no LLM call, no query
# rewriting (a search box query is usually already self-contained, unlike a
# conversational follow-up), no strict MIN_SCORE cutoff. We just embed the
# query and hand back the closest chunks so the user can judge relevance
# themselves from the snippet - that IS the feature.
# ---------------------------------------------------------------------------
SEARCH_TOP_K = 8

# A much looser floor than chat's MIN_SCORE (0.45). Chat needs to be
# confident before it commits to an answer; a search box can show "this is
# the closest thing we found" without that same bar, and let the score
# (surfaced in the UI) tell the user how strong the match really is.
SEARCH_MIN_SCORE = 0.2


def semantic_search(video_id: str, query: str) -> SearchResponse:

    chunks, matrix = get_chunks(video_id)

    if not chunks:
        raise HTTPException(
            status_code=404,
            detail="This video has not been processed yet. Summarize it first."
        )

    query_vector = embed_query(query)

    hits = cosine_top_k(query_vector, matrix, k=SEARCH_TOP_K)

    results = [
        SearchResult(
            timestamp=(
                f"{format_timestamp(chunks[index]['start'])}"
                f" - {format_timestamp(chunks[index]['end'])}"
            ),
            start_seconds=chunks[index]["start"],
            snippet=_snippet(chunks[index]["text"], max_chars=280),
            score=round(score, 3),
        )
        for index, score in hits
        if score >= SEARCH_MIN_SCORE
    ]

    return SearchResponse(results=results)