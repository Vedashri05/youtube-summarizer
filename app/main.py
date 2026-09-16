from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm

from app.models.auth import TokenResponse, UserCreate
from app.models.request import ChatRequest, SearchRequest, SummaryRequest
from app.models.response import ChatResponse, SearchResponse
from app.models.video import VideoJobCreated, VideoListItem, VideoStatusResponse
from app.services.auth_service import (
    create_access_token,
    get_current_user_id,
    hash_password,
    verify_password,
)
from app.services.cache_service import (
    create_user,
    create_video_job,
    get_user_by_email,
    get_video_job,
    get_video_job_by_video_id,
    initialize_database,
    list_user_videos,
)
from app.services.job_service import run_video_pipeline
from app.services.rag_service import answer_question, semantic_search
from app.utils.helpers import extract_video_id

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

initialize_database()


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
@app.post("/auth/register", response_model=TokenResponse)
async def register(request: UserCreate):

    if get_user_by_email(request.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    user_id = create_user(request.email, hash_password(request.password))

    return TokenResponse(access_token=create_access_token(user_id, request.email))


@app.post("/auth/login", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # OAuth2PasswordRequestForm's field is called `username` by spec - the
    # frontend sends the user's email into that field.

    user = get_user_by_email(form_data.username)

    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    return TokenResponse(access_token=create_access_token(user["id"], user["email"]))


# ---------------------------------------------------------------------------
# Videos - async processing pipeline + per-user history
# ---------------------------------------------------------------------------
@app.post("/videos", response_model=VideoJobCreated)
async def create_video(
    request: SummaryRequest,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(get_current_user_id),
):
    """
    Kicks off summarization as a background task and returns immediately
    with a job_id. The client polls GET /videos/{job_id} for progress.
    """

    video_id = extract_video_id(request.url)

    job_id = create_video_job(user_id, request.url, video_id, request.mode)

    background_tasks.add_task(run_video_pipeline, job_id, video_id, request.mode)

    return VideoJobCreated(job_id=job_id, video_id=video_id, status="pending")


@app.get("/videos/{job_id}", response_model=VideoStatusResponse)
async def get_video_status(job_id: int, user_id: int = Depends(get_current_user_id)):

    job = get_video_job(job_id, user_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return VideoStatusResponse(
        job_id=job["id"],
        video_id=job["video_id"],
        url=job["url"],
        mode=job["mode"],
        status=job["status"],
        error=job["error"],
        summary=job["summary"],
        created_at=job["created_at"],
        updated_at=job["updated_at"],
    )


@app.get("/videos", response_model=list[VideoListItem])
async def list_videos(user_id: int = Depends(get_current_user_id)):
    """
    The "My Videos" sidebar - every job this user has ever kicked off,
    newest first, regardless of status.
    """

    jobs = list_user_videos(user_id)

    return [
        VideoListItem(
            job_id=job["id"],
            video_id=job["video_id"],
            url=job["url"],
            mode=job["mode"],
            status=job["status"],
            created_at=job["created_at"],
            title=job["title"],
        )
        for job in jobs
    ]


# ---------------------------------------------------------------------------
# Chat / search - auth-gated, and scoped to videos this user owns
# ---------------------------------------------------------------------------
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, user_id: int = Depends(get_current_user_id)):
    """
    Ask a question about an already-processed video.

    Returns a grounded answer plus the timestamp ranges it came from.
    """

    if not get_video_job_by_video_id(request.video_id, user_id):
        raise HTTPException(status_code=404, detail="Video not found")

    return answer_question(
        video_id=request.video_id,
        question=request.question,
        history=request.history,
    )


@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest, user_id: int = Depends(get_current_user_id)):
    """
    Semantic search over an already-processed video's transcript.

    Unlike /chat, this does not call the LLM at all - it returns the raw
    ranked matches from the embedding index, so the user can see exactly
    which moments the video covers a concept in, even if their query's
    wording never appears verbatim in the transcript.
    """

    if not get_video_job_by_video_id(request.video_id, user_id):
        raise HTTPException(status_code=404, detail="Video not found")

    return semantic_search(
        video_id=request.video_id,
        query=request.query,
    )