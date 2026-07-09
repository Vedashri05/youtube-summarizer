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

    Your task is to analyze the transcript and produce a concise structured summary.

    Instructions:

    1. Read the transcript carefully.

    2. Write an overall summary.

    3. Extract ONLY the educational concepts.

        Ignore:

        - greetings
        - introductions
        - sponsor messages
        - social media promotions
        - outros
        - farewells
        - requests to like/share/subscribe

        Return only concepts that help someone learn the topic.

    4. Preserve timestamps whenever possible.

    5. List the main topics discussed.

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
