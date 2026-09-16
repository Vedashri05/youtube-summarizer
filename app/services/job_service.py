from app.services.cache_service import (
    get_summary,
    save_summary,
    save_video_result,
    update_video_status,
)
from app.services.gemini_service import combine_summaries, summarize_transcript
from app.services.rag_service import ensure_video_indexed
from app.services.transcript_service import fetch_transcript
from app.utils.helpers import chunk_transcript


def run_video_pipeline(job_id: int, video_id: str, mode: str):
    """
    The actual summarization pipeline, run as a background task after
    POST /videos has already returned the job_id to the client.

    Every stage updates videos.status, so GET /videos/{job_id} reflects
    live progress instead of the client just staring at a blank spinner:

        pending -> transcribing -> indexing -> chunking -> summarizing
                -> complete (or failed, with `error` set)
    """

    try:
        # Same cache-check the old synchronous /summary endpoint did - if
        # this (video, mode) pair was already summarized by anyone, skip
        # straight to done instead of re-doing the work.
        cached = get_summary(video_id, mode)

        if cached:
            ensure_video_indexed(video_id)
            save_video_result(job_id, cached)
            return

        update_video_status(job_id, "transcribing")
        transcript = fetch_transcript(video_id)

        update_video_status(job_id, "indexing")
        ensure_video_indexed(video_id, transcript=transcript)

        update_video_status(job_id, "chunking")
        chunks = chunk_transcript(transcript)

        update_video_status(job_id, "summarizing")
        summaries = [summarize_transcript(chunk, mode=mode) for chunk in chunks]
        final_summary = combine_summaries(summaries, mode=mode)

        save_summary(video_id, mode, final_summary.model_dump())
        save_video_result(job_id, final_summary.model_dump())

    except Exception as exc:
        update_video_status(job_id, "failed", error=str(exc))