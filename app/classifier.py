# classifier.py — Uses Phi-3 Mini to classify prompt difficulty
#
# WHAT IS A CLASSIFIER?
# A classifier reads an input and puts it into a category.
# Here, Phi-3 reads the user's prompt and answers with one word:
# "simple", "medium", or "complex".
#
# WHY USE A SMALL MODEL FOR THIS?
# Phi-3 Mini is tiny and fast (~2.3GB). Sending a 5-word prompt to GPT-4o
# just to classify it would waste money. Let the small free model do this job.

from openai import OpenAI
from app.config import settings

# Groq client — same library as OpenAI, just different URL and key
groq_client = OpenAI(
    api_key=settings.groq_api_key,
    base_url="https://api.groq.com/openai/v1",
)

# The instruction we give the classifier model.
# This is called a "system prompt" — it sets the AI's behaviour.
CLASSIFIER_SYSTEM_PROMPT = """You are a prompt difficulty classifier.

Classify the user's message into exactly one of these categories:
- simple: greetings, basic facts, single-step questions, short translations
- medium: explanations, comparisons, summaries, writing tasks
- complex: code generation, architecture design, multi-step reasoning, mathematics

Rules:
- Reply with ONLY the category name (simple, medium, or complex)
- No punctuation, no explanation, just the single word
"""


def classify_prompt(prompt: str) -> str:
    """
    Send the prompt to Llama 3.1 8B (via Groq) and get back a difficulty label.

    Returns:
        "simple", "medium", or "complex"
        Falls back to "medium" if the model returns something unexpected.
    """
    try:
        result = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",   # Fast, cheap, good enough for classification
            messages=[
                {"role": "system", "content": CLASSIFIER_SYSTEM_PROMPT},
                {"role": "user",   "content": prompt},
            ],
            max_tokens=10,    # We only need one word — no need for a long response
            temperature=0,    # Temperature 0 = deterministic, no creativity needed here
        )

        label = result.choices[0].message.content.strip().lower()

        if label in ("simple", "medium", "complex"):
            return label

        print(f"[classifier] Unexpected label '{label}', defaulting to 'medium'")
        return "medium"

    except Exception as e:
        print(f"[classifier] Error: {e}. Defaulting to 'medium'")
        return "medium"
