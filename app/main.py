# main.py — The FastAPI application (entry point)
#
# WHAT IS FASTAPI?
# FastAPI is a Python web framework. It lets you define URLs ("endpoints")
# that other programs (or curl, or a browser) can call.
# It automatically validates incoming data using Pydantic (from models.py).
# It also auto-generates interactive API docs at http://localhost:8000/docs
#
# HOW THIS WORKS (with memory):
#   1. User sends POST /route with {"prompt": "Hello"}
#   2. mempalace searches for relevant past interactions
#   3. Context is injected into the prompt (if found)
#   4. Classifier labels difficulty: simple / medium / complex
#   5. Router sends enriched prompt to the right model
#   6. Response is stored in mempalace + logged to PostgreSQL
#   7. Response returned to user

import time
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager

from app.models import RouterRequest, RouterResponse
from app.classifier import classify_prompt
from app.router import route
from app.database import init_db, log_request, get_logs
from app.cost import get_dashboard
from app.memory import build_enriched_prompt, store_interaction


# ── Startup / Shutdown ────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Runs once when the server starts, and once when it stops."""
    print("[startup] Initializing database...")
    init_db()
    print("[startup] Smart Router is ready!")
    yield
    print("[shutdown] Goodbye!")


# ── Create the FastAPI app ────────────────────────────────────────────────────

app = FastAPI(
    title="Smart Model Router",
    description="Routes prompts to the cheapest AI model that can handle them. Has memory.",
    version="2.0.0",
    lifespan=lifespan,
)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.post("/route", response_model=RouterResponse)
def route_prompt(request: RouterRequest):
    """
    Main endpoint — classify, inject memory context, route to right model.

    Send: {"prompt": "Your question here"}
    """
    start_time = time.time()

    try:
        # Step 1: Classify difficulty using the original prompt
        difficulty = classify_prompt(request.prompt)
        print(f"[route] Difficulty: {difficulty} | Prompt: {request.prompt[:60]}...")

        # Step 2: Fetch relevant past context from mempalace and inject it
        # The enriched prompt = past context + current question
        enriched_prompt, had_context = build_enriched_prompt(request.prompt)

        # Step 3: Route the enriched prompt to the right model
        response_text, model_used, cost = route(enriched_prompt, difficulty)

        elapsed_ms = int((time.time() - start_time) * 1000)

        # Step 4: Store this interaction in mempalace for future context
        store_interaction(
            prompt=request.prompt,      # store original (not enriched) for cleanliness
            response=response_text,
            difficulty=difficulty,
            model_used=model_used,
        )

        # Step 5: Log to PostgreSQL
        log_request(
            prompt=request.prompt,
            difficulty=difficulty,
            model_used=model_used,
            response=response_text,
            cost=cost,
            response_time_ms=elapsed_ms,
        )

        print(f"[route] Done in {elapsed_ms}ms | {model_used} | context={'yes' if had_context else 'no'} | cost=${cost}")

        return RouterResponse(
            response=response_text,
            model_used=model_used,
            difficulty=difficulty,
            cost=cost,
            response_time_ms=elapsed_ms,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/dashboard")
def dashboard():
    """Cost savings: actual spend vs. what GPT-4o-for-everything would cost."""
    return get_dashboard()


@app.get("/logs")
def logs(limit: int = 20, offset: int = 0):
    """Recent request history. Use ?limit=10&offset=20 to paginate."""
    return get_logs(limit=limit, offset=offset)


@app.get("/memory/search")
def memory_search(q: str, n: int = 5):
    """
    Search past interactions in mempalace.
    Example: GET /memory/search?q=python+async
    """
    from app.memory import fetch_context
    from mempalace.searcher import search_memories
    from app.memory import PALACE_PATH, WING
    results = search_memories(query=q, palace_path=PALACE_PATH, wing=WING, n_results=n)
    return results


@app.get("/health")
def health():
    """Quick check to confirm the server is running."""
    return {"status": "ok", "message": "Smart Router is running", "version": "2.0.0"}
