from google import genai
from app.config import settings
from app.models.response import SummaryResponse
from fastapi import HTTPException
from google.genai.errors import ServerError, ClientError

client = genai.Client(
    api_key=settings.GEMINI_API_KEY
)

PROMPT = """
    You are an expert YouTube video summarizer.

    Analyze the transcript and produce a concise, structured summary.

    Instructions:

    1. Read the transcript carefully.

    2. Write an overall summary in 5-7 sentences that captures the main idea of the video.

    3. Extract ONLY the 5-7 MOST IMPORTANT educational key points.

    - Each key point should represent a major concept or learning.
    - Merge similar ideas into a single point.
    - Ignore minor details and repetitive explanations.
    - Ignore greetings, introductions, sponsor messages, social media promotions, outros, farewells, and requests to like/share/subscribe.
    - Do NOT create a key point for every timestamp.
    - Choose only the concepts that are essential for someone who wants to understand the video without watching it.

    4. Include one timestamp for each key point.
    - Use the timestamp where that concept is first introduced.

    5. List only the major topics covered (4-8 topics).

    6. Return valid JSON only.

    Rules:

    - Do NOT invent information.
    - Do NOT add markdown.
    - Do NOT explain your reasoning.
    - Keep summaries concise.
"""

def summarize_transcript(transcript: str):
    try:
        # return output in python object
        response = client.models.generate_content(
            model=settings.MODEL,
            contents=f"{PROMPT}\n\nTranscript:\n{transcript}",
            config={
                "response_mime_type":"application/json",
                "response_schema":SummaryResponse
            }
        )
    
    except ServerError:
        raise HTTPException(
            status_code=503,
            detail="Gemini service is temporarily unavailable. Please try again later."
        )

    except ClientError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    
    # Parse Response
    summary = SummaryResponse.model_validate_json(response.text)

    return summary


def combine_summaries(summaries):

    combined = "\n\n".join(
        str(summary)
        for summary in summaries
    )

    prompt = f"""
        Below are summaries of different chunks of the same YouTube video.

        Merge them into one summary.

        Return JSON.

        {combined}
    """

    response = client.models.generate_content(
        model=settings.MODEL,
        contents=prompt,
        config={
            "response_mime_type":"application/json",
            "response_schema":SummaryResponse
        }
    )

    return SummaryResponse.model_validate_json(response.text)
