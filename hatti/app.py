"""Stateless Python server. Family voices never leave the browser."""
from datetime import date
from pathlib import Path
from typing import Literal
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from .content import LESSON_BY_ID, WORD_BY_ID, bootstrap
from .engine import due_review, grade, lesson_payload, quiz_payload, schedule_review, retrieve
from .guide import guidance

ROOT = Path(__file__).resolve().parent.parent

class Recall(BaseModel):
    wins: int = Field(default=0, ge=0, le=50)
    misses: int = Field(default=0, ge=0, le=1000)
    due: date
    last: date

class Answer(BaseModel):
    word_id: str = Field(max_length=60)
    choice_id: str = Field(max_length=60)
    today: date
    prior: Recall | None = None

class ReviewRequest(BaseModel):
    today: date
    progress: dict[str, Recall] = Field(default_factory=dict, max_length=100)

class GuideRequest(BaseModel):
    topic: Literal["start", "family", "variants", "numbers", "listening"]

def create_app():
    application = FastAPI(title="Hatti Quest", description="Family-supported Badaga learning", docs_url="/api/docs")
    application.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
    templates = Jinja2Templates(directory=ROOT / "templates")

    @application.middleware("http")
    async def browser_boundaries(request, call_next):
        if request.method == "POST":
            origin = request.headers.get("origin")
            if origin and origin != str(request.base_url).rstrip("/"):
                return HTMLResponse("Origin not allowed", status_code=403)
            try:
                too_large = int(request.headers.get("content-length", "0")) > 32_768
            except ValueError:
                too_large = True
            if too_large:
                return HTMLResponse("Request is too large", status_code=413)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data: blob:; media-src 'self' blob:; connect-src 'self'; font-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
        response.headers["Permissions-Policy"] = "camera=(), geolocation=(), microphone=(self)"
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @application.get("/", response_class=HTMLResponse)
    async def home(request: Request):
        return templates.TemplateResponse(request=request, name="index.html", context={})

    @application.get("/health")
    async def health():
        return {"status": "ok", "version": "1.0.0"}

    @application.get("/api/content")
    async def content():
        return bootstrap()

    @application.get("/api/lessons/{lesson_id}")
    async def lesson(lesson_id: str):
        if lesson_id not in LESSON_BY_ID:
            raise HTTPException(404, "Unknown adventure")
        return lesson_payload(lesson_id)

    @application.post("/api/answer")
    async def answer(body: Answer):
        if body.word_id not in WORD_BY_ID or body.choice_id not in WORD_BY_ID:
            raise HTTPException(422, "Unknown word")
        result = grade(body.word_id, body.choice_id)
        prior = body.prior.model_dump(mode="json") if body.prior else None
        result["review"] = schedule_review(prior, result["correct"], body.today)
        return result

    @application.get("/api/words/{word_id}/challenge")
    async def word_challenge(word_id: str):
        if word_id not in WORD_BY_ID:
            raise HTTPException(404, "Unknown word")
        return quiz_payload(word_id)

    @application.post("/api/review")
    async def review(body: ReviewRequest):
        if any(id not in WORD_BY_ID for id in body.progress):
            raise HTTPException(422, "Unknown review word")
        progress = {id: recall.model_dump(mode="json") for id, recall in body.progress.items()}
        return {"words": due_review(progress, body.today)}

    @application.get("/api/search")
    async def search(q: str = "", category: str = ""):
        if len(q) > 120:
            raise HTTPException(422, "Search is too long")
        words = retrieve(q, limit=52) if q.strip() else bootstrap()["words"]
        return {"words": [w for w in words if not category or w["category"] == category]}

    @application.post("/api/guide")
    async def guide(body: GuideRequest):
        return await guidance(body.topic)

    return application

app = create_app()
