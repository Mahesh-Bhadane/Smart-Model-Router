# Smart Model Router

A FastAPI gateway that automatically routes prompts to the cheapest AI model based on complexity — saving money by only using expensive models when needed.

## How It Works

Every prompt goes through 3 steps:

```
Your Prompt
    │
    ▼
1. Classifier (Llama 3 8B) → labels it: simple / medium / complex
    │
    ▼
2. Router → picks the right model
    ├── simple  → Groq: llama-3.1-8b-instant    (free)
    ├── medium  → Groq: llama-3.3-70b-versatile  (free)
    └── complex → OpenAI: GPT-4o                 (paid)
    │
    ▼
3. Memory (mempalace) → injects past context, stores new interaction
```

---

## Prerequisites

- Python 3.10+
- PostgreSQL running locally
- A [Groq API key](https://console.groq.com) (free)
- An [OpenAI API key](https://platform.openai.com/api-keys) (paid, for complex prompts only)

---

## Setup

### 1. Clone the repo

```bash
git clone git@github.com:Mahesh-Bhadane/Smart-Model-Router.git
cd Smart-Model-Router
```

### 2. Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create the database

```bash
psql -U postgres -c "CREATE DATABASE smart_router_db;"
```

### 5. Set up environment variables

```bash
cp .env.template .env
```

Open `.env` and fill in your keys:

```env
OPENAI_API_KEY=sk-...
GROQ_API_KEY=gsk_...

DB_HOST=localhost
DB_PORT=5432
DB_NAME=smart_router_db
DB_USER=postgres
DB_PASSWORD=your_postgres_password
```

### 6. Start the server

```bash
uvicorn app.main:app --reload
```

Server runs at `http://localhost:8000`

---

## Usage

### Route a prompt

```bash
curl -X POST http://localhost:8000/route \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello, how are you?"}'
```

**Response:**
```json
{
  "response": "I'm doing well! How can I help you?",
  "model_used": "llama-3.1-8b-instant",
  "difficulty": "simple",
  "cost": 0.0,
  "response_time_ms": 540
}
```

### Test all 3 tiers

**Simple** — routes to Llama 3.1 8B (free):
```bash
curl -X POST http://localhost:8000/route \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is the capital of France?"}'
```

**Medium** — routes to Llama 3.3 70B (free):
```bash
curl -X POST http://localhost:8000/route \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Explain how DNS resolution works"}'
```

**Complex** — routes to GPT-4o (paid):
```bash
curl -X POST http://localhost:8000/route \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Write a binary search tree in Python with balancing"}'
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/route` | Route a prompt to the right model |
| `GET` | `/dashboard` | Cost savings summary |
| `GET` | `/logs` | Recent request history |
| `GET` | `/memory/search?q=...` | Search past interactions |
| `GET` | `/health` | Server status |
| `GET` | `/docs` | Interactive API docs (auto-generated) |

### Cost Dashboard

```bash
curl http://localhost:8000/dashboard
```

```json
{
  "total_requests": 42,
  "by_tier": { "simple": 20, "medium": 15, "complex": 7 },
  "actual_cost_usd": 0.021,
  "cost_if_all_gpt4o": 0.126,
  "money_saved_usd": 0.105,
  "savings_percent": 83.3
}
```

### Search Memory

```bash
curl "http://localhost:8000/memory/search?q=python+async"
```

---

## Project Structure

```
smart-router/
├── .env.template         # Copy to .env and fill in your keys
├── requirements.txt      # Python dependencies
├── REQUIREMENTS.md       # Full project plan and architecture
└── app/
    ├── main.py           # FastAPI app + all endpoints
    ├── config.py         # Load settings from .env
    ├── models.py         # Request/response schemas
    ├── classifier.py     # Classifies prompt difficulty
    ├── router.py         # Routes to correct model
    ├── memory.py         # mempalace context injection
    ├── database.py       # PostgreSQL logging
    └── cost.py           # Cost calculations
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Web Framework | FastAPI |
| Simple/Medium AI | Groq (Llama 3 — free) |
| Complex AI | OpenAI GPT-4o |
| Memory | mempalace + ChromaDB |
| Database | PostgreSQL |
| Config | pydantic-settings |
