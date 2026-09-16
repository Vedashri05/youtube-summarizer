"""
Shared wrapper around Gemini's generate_content call.

Every part of the app that asks Gemini to write something (summarising a
transcript chunk, merging summaries, condensing a follow-up question,
answering a chat question) was duplicating the same try/except around
client.models.generate_content. That duplication is exactly why the last
429 you saw came through as a raw Python error dict instead of a clean
message - only ONE of the four call sites had ever been given a friendly
error, the same way ONE call site (embeddings) already had retry logic.

This module is the single place that talks to the generation model, so a
fix here (retry, error message, model choice) applies everywhere at once.
"""

import time

from fastapi import HTTPException
from google import genai
from google.genai.errors import ClientError, ServerError

from app.config import settings

client = genai.Client(api_key=settings.GEMINI_API_KEY)

# Generation calls are more expensive and slower than embedding calls, and -
# importantly - the free tier's limit on gemini-2.5-flash is PER DAY, not
# per minute (your error showed "limit: 20 ... PerDayPerProjectPerModel").
# Retrying rapidly cannot fix a daily cap, so we only retry a couple of
# times for the rare case where the delay really is short (a burst
# per-minute limit sharing the same error shape), then fail clearly.
MAX_RETRIES = 2


def _retry_delay_seconds(error: ClientError, attempt: int) -> float:
    """Read Gemini's own suggested wait time out of the 429 response."""

    try:
        for detail in error.details.get("error", {}).get("details", []):
            if detail.get("@type", "").endswith("RetryInfo"):
                return float(detail["retryDelay"].rstrip("s")) + 1

    except (AttributeError, KeyError, ValueError):
        pass

    return 2 ** attempt


def _is_daily_quota(error: ClientError) -> bool:
    """
    Distinguish "you'll be fine in a few seconds" from "you are done for
    today" so the error message we show is actually true, instead of
    telling someone to retry a limit that will not lift until tomorrow.
    """

    try:
        for violation in (
            error.details.get("error", {})
            .get("details", [{}])[1]
            .get("violations", [])
        ):
            if "PerDay" in violation.get("quotaId", ""):
                return True

    except (AttributeError, IndexError, KeyError):
        pass

    return False


def generate(contents, config=None, model=None):
    """
    Call Gemini's text/JSON generation endpoint.

    Drop-in replacement for client.models.generate_content(...) that adds
    429 retry (using Gemini's own suggested delay) and turns any remaining
    error into an HTTPException with a message a user can actually act on.
    """

    for attempt in range(MAX_RETRIES + 1):

        try:
            return client.models.generate_content(
                model=model or settings.MODEL,
                contents=contents,
                config=config,
            )

        except ServerError:
            raise HTTPException(
                status_code=503,
                detail="Gemini service is temporarily unavailable. Please try again later."
            )

        except ClientError as e:

            is_rate_limited = getattr(e, "code", None) == 429

            if is_rate_limited and not _is_daily_quota(e) and attempt < MAX_RETRIES:
                time.sleep(_retry_delay_seconds(e, attempt))
                continue

            if is_rate_limited and _is_daily_quota(e):
                raise HTTPException(
                    status_code=429,
                    detail=(
                        "You've used up today's free quota for Gemini's "
                        f"{model or settings.MODEL} model. This limit resets "
                        "daily and does not lift by retrying - either wait "
                        "for the reset or switch to a billed API key before "
                        "your next test/demo."
                    ),
                )

            if is_rate_limited:
                raise HTTPException(
                    status_code=429,
                    detail="Rate limited by Gemini. Please wait a moment and try again."
                )

            raise HTTPException(status_code=400, detail=str(e))