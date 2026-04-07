# memory.py — Context memory using mempalace
#
# WHAT IS HAPPENING HERE?
# Every time a prompt is routed, we:
#   1. BEFORE routing: search mempalace for relevant past interactions
#   2. Inject that context into the prompt so the model has history
#   3. AFTER routing: store the new interaction for future use
#
# WHY DOES THIS HELP?
# Without memory, every prompt is stateless — the model knows nothing
# about previous conversations. With memory, if you asked about Python
# last week, the router can reference that context today.
#
# PALACE STRUCTURE:
#   Wing: "smart-router"            ← our project name
#     Room: "conversations"         ← stores Q&A pairs
#     Room: "technical"             ← stores technical details detected

import chromadb
from pathlib import Path
from mempalace.searcher import search_memories

# Where the memory database lives on disk
PALACE_PATH = str(Path.home() / ".mempalace" / "smart-router-palace")
WING = "smart-router"
COLLECTION = "mempalace_drawers"

# Only inject context if the similarity score is high enough
# 0.0 = no match, 1.0 = perfect match — 0.4 is a reasonable threshold
MIN_SIMILARITY = 0.18


def _get_collection():
    """Get (or create) the ChromaDB collection for our palace."""
    client = chromadb.PersistentClient(path=PALACE_PATH)
    # get_or_create so first run doesn't crash
    return client.get_or_create_collection(
        name=COLLECTION,
        metadata={"hnsw:space": "cosine"},   # cosine = better for text similarity
    )


def fetch_context(prompt: str, n_results: int = 3) -> str:
    """
    Search mempalace for past interactions relevant to this prompt.

    Returns a formatted context string to inject into the prompt,
    or an empty string if nothing relevant is found.
    """
    try:
        results = search_memories(
            query=prompt,
            palace_path=PALACE_PATH,
            wing=WING,
            n_results=n_results,
        )

        if "error" in results or not results.get("results"):
            return ""   # No palace yet or no results — that's fine

        # Filter by similarity threshold — only use good matches
        relevant = [
            r for r in results["results"]
            if r["similarity"] >= MIN_SIMILARITY
        ]

        if not relevant:
            return ""

        # Format the context block to inject before the user's prompt
        lines = ["[Relevant context from past interactions:]"]
        for r in relevant:
            lines.append(f"- {r['text']}")

        return "\n".join(lines)

    except Exception as e:
        # Memory failures should never block the main response
        print(f"[memory] fetch_context error: {e}")
        return ""


def store_interaction(prompt: str, response: str, difficulty: str, model_used: str):
    """
    Save a prompt+response pair to mempalace for future context retrieval.
    """
    try:
        col = _get_collection()

        # Store as: "Q: ... A: ..." so searches can match on either part
        document = f"Q: {prompt}\nA: {response}"

        # Use a unique ID based on content hash
        doc_id = str(abs(hash(document)))

        col.upsert(
            ids=[doc_id],
            documents=[document],
            metadatas=[{
                "wing": WING,
                "room": "conversations",
                "difficulty": difficulty,
                "model_used": model_used,
                "source_file": "smart-router-api",
            }]
        )
    except Exception as e:
        print(f"[memory] store_interaction error: {e}")


def build_enriched_prompt(original_prompt: str) -> tuple[str, bool]:
    """
    Fetch relevant past context and prepend it to the prompt.

    Returns:
        (enriched_prompt, was_context_injected)
    """
    context = fetch_context(original_prompt)

    if context:
        enriched = f"{context}\n\n[Current question:]\n{original_prompt}"
        print(f"[memory] Injected context ({len(context)} chars) into prompt")
        return enriched, True

    return original_prompt, False
