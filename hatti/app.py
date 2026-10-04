"""Stateless Python server. Family voices never leave the browser."""
from datetime import date
import hmac
import time
from collections import deque
from pathlib import Path
from typing import Literal
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from .content import LESSON_BY_ID, WORD_BY_ID, bootstrap
from .engine import due_review, grade, lesson_payload, quiz_payload, schedule_review, retrieve
from .guide import guidance
from .rag import RagService, StoryRequest, THEMES
from .observability import metrics, EVAL

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

def create_app(settings=None, transport=None):
    application = FastAPI(title="Hatti Quest", description="Family-supported Badaga learning", docs_url="/api/docs")
    rag = RagService(settings, transport)
    application.state.rag = rag
    budget = deque()
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

    @application.get("/demo", response_class=HTMLResponse)
    async def demo_slides(request: Request):
        return templates.TemplateResponse(request=request, name="demo.html", context={})

    @application.get("/health")
    async def health():
        return {"status": "ok", "version": "2.0.0"}

    def allow_ops(request):
        token = rag.settings.ops_token
        supplied = request.headers.get("authorization", "").removeprefix("Bearer ")
        if token:
            permitted = hmac.compare_digest(token.encode(), supplied.encode())
        else:
            permitted = bool(request.client and request.client.host in ("127.0.0.1", "::1", "testclient"))
        if not permitted:
            raise HTTPException(403, "Operations data requires local access or an operations token")

    @application.get("/lab", response_class=HTMLResponse)
    async def lab(request: Request):
        return templates.TemplateResponse(request=request, name="lab.html", context={})

    @application.get("/metrics")
    async def prometheus_metrics():
        import json
        report = ROOT / "evals" / "reports" / "latest.json"
        if report.exists():
            data = json.loads(report.read_text())
            for system in ("bm25", "hybrid"):
                for metric, value in data["metrics"][system].items():
                    EVAL.labels(metric, system).set(value)
            for metric in ("story_grounding", "guard_pass_rate", "live_generation_rate"):
                EVAL.labels(metric, "story-pipeline").set(data["metrics"][metric])
        return Response(content=metrics(), media_type="text/plain; version=0.0.4")

    @application.get("/api/ai/options")
    async def ai_options():
        return {"live_enabled": rag.settings.generation_ready, "themes": THEMES}

    @application.post("/api/ai/story")
    async def ai_story(body: StoryRequest):
        now = time.monotonic()
        while budget and budget[0] < now - 60:
            budget.popleft()
        # Process-wide spend protection without collecting child IP addresses.
        if len(budget) >= rag.settings.rate_per_minute:
            raise HTTPException(429, "Story studio is taking a small pause. Try again in a minute.")
        budget.append(now)
        try:
            return await rag.story(body)
        except ValueError:
            raise HTTPException(422, "Choose documented words from the selected topic") from None

    @application.get("/api/ai/status")
    async def ai_status(request: Request):
        allow_ops(request)
        return rag.status()

    @application.get("/api/ai/evals")
    async def ai_evals(request: Request):
        allow_ops(request)
        import json
        report = ROOT / "evals" / "reports" / "latest.json"
        return json.loads(report.read_text()) if report.exists() else {"status": "not-run", "cases": []}

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
