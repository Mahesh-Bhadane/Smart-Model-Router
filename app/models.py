# models.py — Data shapes for our API requests and responses
#
# WHAT IS PYDANTIC?
# Pydantic validates data automatically. If a user sends {"prompt": 123}
# (a number instead of text), Pydantic will reject it with a clear error
# before it even reaches our code. Think of it as a bouncer for your API.

from pydantic import BaseModel


class RouterRequest(BaseModel):
    """What the user sends TO our API."""
    prompt: str                    # The user's question or instruction


class RouterResponse(BaseModel):
    """What our API sends BACK to the user."""
    response: str                  # The AI model's answer
    model_used: str                # Which model answered (e.g. "phi3:mini")
    difficulty: str                # How we classified the prompt: simple/medium/complex
    cost: float                    # Cost in USD (0.0 for local Ollama models)
    response_time_ms: int          # How long it took in milliseconds


class LogEntry(BaseModel):
    """One row from the database — used in the /logs endpoint."""
    id: int
    prompt: str
    difficulty: str
    model_used: str
    cost: float
    response_time_ms: int
    created_at: str
