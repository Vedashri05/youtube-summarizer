"""
Embedding service.

This is the piece that turns text into vectors so that we can compare
meaning instead of comparing keywords.

Two different task types are used on purpose:

    RETRIEVAL_DOCUMENT -> for the transcript chunks we store
    RETRIEVAL_QUERY    -> for the user's question at query time

Gemini's embedding model is trained asymmetrically: a question and the
passage that answers it do not look alike as plain text ("Why do we scale
features?" vs "...so the cost surface becomes more circular..."), so the
model is told which side of the pair it is embedding. Using the same task
type for both measurably hurts recall.
"""

import time

import numpy as np
from fastapi import HTTPException
from google import genai
from google.genai import types
from google.genai.errors import ClientError, ServerError

from app.config import settings

client = genai.Client(api_key=settings.GEMINI_API_KEY)

# 768 dims is plenty for a single video and keeps the SQLite rows small.
EMBEDDING_DIM = 768

# The API rejects very large batches, so we send the chunks in slices.
BATCH_SIZE = 50

# 429 = RESOURCE_EXHAUSTED. The free tier allows a limited number of
# embedding calls per minute; a long video (many batches) or repeated
# testing can hit that ceiling. We retry instead of failing the request.
MAX_RETRIES = 3


def _retry_delay_seconds(error: ClientError, attempt: int) -> float:
    """
    Gemini's 429 response includes the exact wait time it wants
    (RetryInfo.retryDelay, e.g. "29s"). Use that when present instead of
    guessing - it is far more accurate than a fixed backoff.
    """

    try:
        for detail in error.details.get("error", {}).get("details", []):
            if detail.get("@type", "").endswith("RetryInfo"):
                return float(detail["retryDelay"].rstrip("s")) + 1

    except (AttributeError, KeyError, ValueError):
        pass

    # No RetryInfo in the response - fall back to exponential backoff.
    return 2 ** attempt


def _embed(texts: list[str], task_type: str) -> np.ndarray:
    """
    Call the Gemini embedding API and return a (n, EMBEDDING_DIM) float32 array.
    """

    vectors: list[list[float]] = []

    for i in range(0, len(texts), BATCH_SIZE):

        batch = texts[i:i + BATCH_SIZE]

        for attempt in range(MAX_RETRIES + 1):

            try:
                response = client.models.embed_content(
                    model=settings.EMBEDDING_MODEL,
                    contents=batch,
                    config=types.EmbedContentConfig(
                        task_type=task_type,
                        output_dimensionality=EMBEDDING_DIM,
                    ),
                )

                vectors.extend(
                    embedding.values
                    for embedding in response.embeddings
                )

                break  # this batch succeeded, move to the next one

            except ServerError:
                raise HTTPException(
                    status_code=503,
                    detail="Embedding service is temporarily unavailable. Please try again later."
                )

            except ClientError as e:

                is_rate_limited = getattr(e, "code", None) == 429

                if is_rate_limited and attempt < MAX_RETRIES:
                    time.sleep(_retry_delay_seconds(e, attempt))
                    continue

                if is_rate_limited:
                    raise HTTPException(
                        status_code=429,
                        detail=(
                            "The embedding quota for this API key is exhausted "
                            "for now. Wait a minute and try again, or check "
                            "your plan at https://ai.google.dev/gemini-api/docs/rate-limits."
                        ),
                    )

                raise HTTPException(status_code=400, detail=str(e))

    return np.array(vectors, dtype=np.float32)


def embed_documents(texts: list[str]) -> np.ndarray:
    """Embed transcript chunks (the things we store and search over)."""
    return _embed(texts, task_type="RETRIEVAL_DOCUMENT")


def embed_query(text: str) -> np.ndarray:
    """Embed a single user question. Returns a 1-D array."""
    return _embed([text], task_type="RETRIEVAL_QUERY")[0]


# ---------------------------------------------------------------------------
# Similarity search
#
# There is no vector database here, and that is a deliberate choice, not a
# shortcut. We only ever search inside ONE video at a time, which is a few
# hundred vectors. A brute-force cosine similarity over a 300 x 768 numpy
# matrix takes well under a millisecond - far less than the network round
# trip to a hosted vector DB would cost. FAISS / Chroma / Pinecone start to
# pay off at 100k+ vectors, i.e. if you later search across all videos.
# ---------------------------------------------------------------------------
def cosine_top_k(
    query_vector: np.ndarray,
    matrix: np.ndarray,
    k: int = 5,
) -> list[tuple[int, float]]:
    """
    Return the indices and scores of the k rows most similar to query_vector.

    Cosine similarity = dot(a, b) / (|a| * |b|)
    It measures the ANGLE between two vectors, ignoring their length, which
    is what we want: a long chunk and a short question can still be "about"
    exactly the same thing.
    """

    if matrix.size == 0:
        return []

    # Normalise everything to unit length, then cosine is just a dot product.
    matrix_norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    matrix_norms[matrix_norms == 0] = 1e-10

    query_norm = np.linalg.norm(query_vector) or 1e-10

    scores = (matrix / matrix_norms) @ (query_vector / query_norm)

    k = min(k, len(scores))

    # argpartition finds the top-k without fully sorting the array,
    # then we sort just those k.
    top_indices = np.argpartition(-scores, k - 1)[:k]
    top_indices = top_indices[np.argsort(-scores[top_indices])]

    return [(int(i), float(scores[i])) for i in top_indices]