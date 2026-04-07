# router.py — Routes each prompt to the right AI model
#
# ROUTING TIERS:
#   simple  → Groq: llama-3.1-8b-instant  (free, very fast)
#   medium  → Groq: llama-3.3-70b-versatile (free, very capable)
#   complex → OpenAI: gpt-4o               (paid, most powerful)
#
# WHY GROQ?
# Groq is a cloud API that runs open-source Llama models for free
# (with rate limits). It's faster than local Ollama AND free —
# perfect for the simple/medium tiers.
#
# COST ESTIMATES (GPT-4o pricing):
#   Input:  $2.50 per 1M tokens
#   Output: $10.00 per 1M tokens
#   Typical request ≈ $0.003

from openai import OpenAI
from app.config import settings

# OpenAI client — for complex tasks (GPT-4o)
openai_client = OpenAI(api_key=settings.openai_api_key)

# Groq client — OpenAI-compatible API, just different base_url and key
# This means we can use the same OpenAI Python library for both!
groq_client = OpenAI(
    api_key=settings.groq_api_key,
    base_url="https://api.groq.com/openai/v1",
)


def _call_groq(model: str, prompt: str) -> tuple[str, float]:
    """
    Call a Groq-hosted model (Llama 3 variants).
    Groq is free with rate limits — cost is $0.00 for our purposes.
    """
    result = groq_client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    response_text = result.choices[0].message.content
    return response_text, 0.0   # Free tier


def _call_openai(prompt: str) -> tuple[str, float]:
    """
    Call GPT-4o via OpenAI. Used only for complex prompts.
    Returns (response_text, cost_in_usd).
    """
    result = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
    )
    response_text = result.choices[0].message.content

    # Calculate actual cost from token usage
    input_tokens  = result.usage.prompt_tokens
    output_tokens = result.usage.completion_tokens
    cost = (input_tokens / 1_000_000 * 2.50) + (output_tokens / 1_000_000 * 10.00)

    return response_text, round(cost, 6)


def route(prompt: str, difficulty: str) -> tuple[str, str, float]:
    """
    Route the prompt to the correct model based on difficulty.

    Returns:
        (response_text, model_name, cost_in_usd)
    """
    if difficulty == "simple":
        # Fast small Llama 3 — free via Groq
        response, cost = _call_groq("llama-3.1-8b-instant", prompt)
        return response, "llama-3.1-8b-instant", cost

    elif difficulty == "medium":
        # Larger Llama 3 70B — still free via Groq!
        response, cost = _call_groq("llama-3.3-70b-versatile", prompt)
        return response, "llama-3.3-70b-versatile", cost

    else:
        # GPT-4o for the hardest tasks only
        response, cost = _call_openai(prompt)
        return response, "gpt-4o", cost
