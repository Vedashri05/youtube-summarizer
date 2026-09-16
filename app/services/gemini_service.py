from app.models.request import SummaryMode
from app.models.response import SummaryContent
from app.services.llm_client import generate

# ---------------------------------------------------------------------------
# Base instructions shared by every mode: what fields to fill, what to
# ignore (intros, sponsor reads, outros), and the timestamp rule. This is
# the part that stays constant regardless of audience.
# ---------------------------------------------------------------------------
BASE_PROMPT = """
    You are an expert YouTube video summarizer.

    Analyze the transcript and produce a concise, structured summary.

    Base rules (apply to every summary regardless of style):

    - Ignore greetings, introductions, sponsor messages, social media
      promotions, outros, farewells, and requests to like/share/subscribe.
    - Do NOT invent information that is not in the transcript.
    - Include one timestamp per key point - use the timestamp where that
      concept is FIRST introduced.
    - Do NOT create a key point for every timestamp; merge similar ideas.
    - List only the major topics covered (4-8 topics).
    - Do NOT add markdown.
    - Do NOT explain your reasoning. Return valid JSON only.
"""

# ---------------------------------------------------------------------------
# Per-mode style instructions.
#
# This is the actual feature: four different audiences reading the SAME
# transcript need different things kept, different vocabulary, and in
# interview_prep's case, an entirely different field populated. Everything
# else in the pipeline (chunking, map-reduce, caching) stays untouched -
# only this dict changes what gets asked for.
# ---------------------------------------------------------------------------
MODE_INSTRUCTIONS: dict[SummaryMode, str] = {

    "beginner": """
    Audience: someone learning this subject for the first time.

    - Explain the overall_summary in simple, plain language - avoid jargon;
      when a technical term is unavoidable, briefly explain it in the same
      sentence.
    - Each key point should include a small, concrete, everyday example or
      analogy, not just the abstract definition.
    - Write 5-7 key points. Prefer clarity over completeness.
    - Leave likely_interview_questions as an empty list.
    """,

    "technical": """
    Audience: someone who already knows the field and wants precision.

    - Preserve technical terminology exactly as used in the video (do not
      simplify or rename it).
    - Where the video gives implementation details, formulas, algorithm
      steps, or complexity/parameter notes, keep them in the key points
      instead of summarizing them away.
    - Write 5-7 key points, favoring density over accessibility.
    - Leave likely_interview_questions as an empty list.
    """,

    "quick_revision": """
    Audience: someone who has already watched the video and wants a fast
    recap before an exam or interview, not an explanation.

    - overall_summary: 2-3 sentences maximum.
    - Write ONLY the 3-5 single most important points - cut anything that
      is not essential to remember.
    - Each key point should be ONE short sentence or phrase, not a paragraph.
    - Leave likely_interview_questions as an empty list.
    """,

    "interview_prep": """
    Audience: someone preparing to be asked about this material in a
    technical interview.

    - Key points should foreground definitions, formulas, and concepts
      that are commonly asked about in interviews, not just "what the
      video covers".
    - Populate likely_interview_questions with 4-6 realistic interview
      questions that this video's content would prepare someone to answer.
      Base them ONLY on concepts actually present in the transcript.
    - For each question, the answer should be something a viewer of this
      video could confidently give - do not ask about anything not covered.
    """,
}


def _build_prompt(mode: SummaryMode) -> str:
    return f"{BASE_PROMPT}\n\nStyle for this summary:\n{MODE_INSTRUCTIONS[mode]}"


def summarize_transcript(transcript: str, mode: SummaryMode = "technical") -> SummaryContent:

    prompt = _build_prompt(mode)

    response = generate(
        contents=f"{prompt}\n\nTranscript:\n{transcript}",
        config={
            "response_mime_type": "application/json",
            "response_schema": SummaryContent,
        },
    )

    return SummaryContent.model_validate_json(response.text)


def combine_summaries(summaries, mode: SummaryMode = "technical") -> SummaryContent:

    # A single chunk needs no reduce step - saves an API call on short videos.
    if len(summaries) == 1:
        return summaries[0]

    combined = "\n\n".join(
        summary.model_dump_json()
        for summary in summaries
    )

    style = MODE_INSTRUCTIONS[mode]

    prompt = f"""
        Below are "{mode}"-style summaries of different chunks of the same
        YouTube video, in chronological order.

        Merge them into ONE summary of the whole video, keeping the same
        style as the chunks below:
        {style}

        Keep the original timestamps attached to their key points.
        Remove duplicate points.
        {"Merge and deduplicate likely_interview_questions across chunks - do not just concatenate them." if mode == "interview_prep" else ""}

        Return JSON.

        {combined}
    """

    response = generate(
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": SummaryContent,
        },
    )

    return SummaryContent.model_validate_json(response.text)