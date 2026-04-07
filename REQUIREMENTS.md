# Smart Model Router — Project Requirements & Plan

## What We're Building

A **FastAPI gateway** that automatically routes user prompts to different AI models based on complexity.

> **The Core Idea:** Why pay $0.03 per query for GPT-4o when "Hello!" can be answered for free by a local model? This router classifies every prompt and sends it to the cheapest model that can handle it.

---

## The Problem

| Situation | Cost |
|-----------|------|
| Using GPT-4o for everything (simple + complex) | 💸 Expensive |
| Using a cheap model for everything | 🤦 Poor quality on hard tasks |
| **Smart routing (what we're building)** | ✅ Best of both worlds |

---

## Routing Tiers

| Tier | Model | Runs Where | Cost | Example Prompts |
|------|-------|-----------|------|-----------------|
| **Simple** | Phi-3 Mini | Your Mac (Ollama) | Free | "Hello", "What's 2+2?", "Translate 'cat' to French" |
| **Medium** | Llama 3 8B | Your Mac (Ollama) | Free | "Explain DNS", "Summarize this article", "Compare Python vs JS" |
| **Complex** | GPT-4o | OpenAI Cloud | ~$0.01–0.03/query | "Write a binary search tree", "Design a microservices architecture" |

**The Classifier** (Phi-3 Mini) reads every incoming prompt first and labels it simple / medium / complex — then the router sends it to the right model.

---

## Architecture

```
User
  │
  ▼
POST /route   ←── Single FastAPI endpoint
  │
  ├─ 1. Classifier (Phi-3) → labels prompt: simple / medium / complex
  │
  ├─ 2. Router → picks the right model
  │         ├── simple  → Phi-3 Mini  (Ollama, free)
  │         ├── medium  → Llama 3 8B  (Ollama, free)
  │         └── complex → GPT-4o      (OpenAI, paid)
  │
  ├─ 3. Model generates response
  │
  ├─ 4. Logger → saves to PostgreSQL (prompt, model, cost, time)
  │
  └─ 5. Returns response to user
```

---

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| **Web Framework** | FastAPI (Python) | Fast, modern, auto-generates API docs |
| **Local AI Models** | Ollama | Run Phi-3 + Llama 3 locally for free |
| **Cloud AI** | OpenAI API | GPT-4o for complex tasks |
| **Database** | PostgreSQL | Log every request and track cost savings |
| **Config** | pydantic-settings | Safely load API keys from .env file |

---

## Project File Structure

```
smart-router/
├── REQUIREMENTS.md       ← This file
├── README.md             ← Setup instructions
├── .env                  ← Your API keys (never commit this!)
├── .env.template         ← Template showing what keys are needed
├── .gitignore            ← Files git should ignore
├── requirements.txt      ← Python packages to install
│
└── app/
    ├── __init__.py       ← Makes 'app' a Python package
    ├── main.py           ← FastAPI app + all endpoints
    ├── config.py         ← Load settings from .env
    ├── models.py         ← Request/Response data shapes (Pydantic)
    ├── classifier.py     ← Phi-3 classifies prompt difficulty
    ├── router.py         ← Routes to correct model
    ├── database.py       ← PostgreSQL connection + logging
    └── cost.py           ← Cost calculations + dashboard
```

---

## API Endpoints

### `POST /route`
The main endpoint. Send a prompt, get back a response routed to the right model.

**Request:**
```json
{
  "prompt": "Explain how a binary search tree works"
}
```

**Response:**
```json
{
  "response": "A binary search tree is...",
  "model_used": "llama3:8b",
  "difficulty": "medium",
  "cost": 0.0
}
```

---

### `GET /dashboard`
Shows cost savings summary.

**Response:**
```json
{
  "total_requests": 42,
  "by_tier": {
    "simple": 20,
    "medium": 15,
    "complex": 7
  },
  "actual_cost": 0.21,
  "cost_if_all_gpt4o": 1.26,
  "money_saved": 1.05,
  "savings_percent": 83.3
}
```

---

### `GET /logs`
View all past requests (paginated).

---

## Database Schema

```sql
CREATE TABLE request_logs (
    id               SERIAL PRIMARY KEY,
    prompt           TEXT          NOT NULL,
    difficulty       VARCHAR(20)   NOT NULL,   -- 'simple', 'medium', 'complex'
    model_used       VARCHAR(50)   NOT NULL,   -- 'phi3:mini', 'llama3:8b', 'gpt-4o'
    response         TEXT,
    cost             DECIMAL(10,6) DEFAULT 0,  -- in USD
    response_time_ms INTEGER,                  -- how long it took
    created_at       TIMESTAMP     DEFAULT NOW()
);
```

---

## Build Phases

| Phase | What We Build | Learning |
|-------|--------------|----------|
| 1 | Project setup, venv, dependencies | Virtual environments, pip |
| 2 | Install Ollama, pull AI models | How local AI models work |
| 3 | Basic FastAPI server + `/route` stub | FastAPI, HTTP, Pydantic |
| 4 | Classifier (Phi-3 labels prompts) | Prompt engineering, LLM calls |
| 5 | Router (sends to right model) | Strategy pattern, OpenAI API |
| 6 | PostgreSQL logging | SQL, database connections |
| 7 | Cost dashboard | SQL aggregations, ROI tracking |

---

## Environment Variables Needed

```env
# OpenAI API Key (get from platform.openai.com)
OPENAI_API_KEY=sk-...

# PostgreSQL connection
DB_HOST=localhost
DB_PORT=5432
DB_NAME=smart_router_db
DB_USER=postgres
DB_PASSWORD=your_password

# Ollama (default, no changes needed)
OLLAMA_HOST=http://localhost:11434
```

---

## Prerequisites

- **Python 3.10+** — check with `python3 --version`
- **PostgreSQL** — already installed locally
- **Homebrew** — to install Ollama (`brew install ollama`)
- **OpenAI API Key** — from [platform.openai.com](https://platform.openai.com) (add $5 credit)


-----------------------------


Smart Model Router — Implementation Plan                                                                                                                                             

 Context

 Build a FastAPI gateway that classifies prompt complexity and routes to the right AI model — saving money by only using expensive models when needed. The user is a beginner and wants
  step-by-step learning. Fully new project, no dependencies on existing repos.

 Routing tiers:

 ┌─────────────────────┬────────────┬────────────────┬───────────────────┐
 │        Tier         │   Model    │    Provider    │       Cost        │
 ├─────────────────────┼────────────┼────────────────┼───────────────────┤
 │ Classifier + Simple │ Phi-3      │ Ollama (local) │ Free              │
 ├─────────────────────┼────────────┼────────────────┼───────────────────┤
 │ Medium              │ Llama 3 8B │ Ollama (local) │ Free              │
 ├─────────────────────┼────────────┼────────────────┼───────────────────┤
 │ Hard                │ GPT-4o     │ OpenAI API     │ ~$0.01-0.03/query │
 └─────────────────────┴────────────┴────────────────┴───────────────────┘

 Project Structure

 smart-router/                  # New standalone git repo
 ├── README.md
 ├── .env                       # API keys (gitignored)
 ├── .env.template              # Template for others
 ├── .gitignore
 ├── requirements.txt
 ├── app/
 │   ├── __init__.py
 │   ├── main.py               # FastAPI app + endpoints
 │   ├── config.py             # Load env vars with pydantic-settings
 │   ├── classifier.py         # Phi-3 prompt classifier
 │   ├── router.py             # Routes to correct model
 │   ├── models.py             # Pydantic request/response schemas
 │   ├── database.py           # PostgreSQL connection + logging
 │   └── cost.py               # Cost tracking + dashboard

 Implementation Phases

 Phase 1: Project Setup

 Goal: Create repo, virtual environment, install dependencies

 1. Create /Users/amberuser/Projects/smart-router/
 2. git init
 3. Create Python virtual environment (python3 -m venv venv)
 4. Create requirements.txt:
   - fastapi — web framework
   - uvicorn — server to run FastAPI
   - openai — OpenAI API client
   - ollama — Python client for Ollama
   - psycopg2-binary — PostgreSQL driver
   - pydantic-settings — config from env vars
   - python-dotenv — load .env files
 5. pip install -r requirements.txt
 6. Create .gitignore (venv, .env, pycache)
 7. Create .env.template and .env (user provides their OpenAI key)

 Learning: What a virtual environment is, why we isolate dependencies

 Phase 2: Install Ollama + Pull Models

 Goal: Get local AI models running on your Mac

 1. Install Ollama: brew install ollama
 2. Start Ollama: ollama serve
 3. Pull models:
   - ollama pull phi3:mini (~2.3GB) — classifier + simple tasks
   - ollama pull llama3:8b (~4.7GB) — medium tasks
 4. Test: ollama run phi3:mini "Hello world"

 Learning: What Ollama is (like Docker but for AI models), how local models work

 Phase 3: Basic FastAPI Server

 Goal: A working API you can hit with curl

 Files: app/main.py, app/config.py, app/models.py

 1. app/config.py — load OPENAI_API_KEY and DB settings from .env
 2. app/models.py — Pydantic schemas:
   - RouterRequest: prompt: str
   - RouterResponse: response: str, model_used: str, difficulty: str, cost: float
 3. app/main.py — FastAPI app with POST /route (echoes prompt for now)
 4. Run: uvicorn app.main:app --reload
 5. Test: curl -X POST http://localhost:8000/route -d '{"prompt": "Hello"}'

 Learning: What FastAPI is, how HTTP POST works, what Pydantic does

 Phase 4: Build the Classifier

 Goal: Phi-3 classifies each prompt as simple/medium/complex

 File: app/classifier.py

 1. classify_prompt(prompt: str) -> str function
 2. Sends prompt to Phi-3 via Ollama with a system prompt asking it to classify as "simple", "medium", or "complex"
 3. Parses response, defaults to "medium" if parsing fails

 Learning: What a classifier is, prompt engineering basics

 Phase 5: Build the Router

 Goal: Route to the right model based on classification

 File: app/router.py

 1. route_to_model(prompt: str, difficulty: str) -> tuple[str, float]
 2. Routing: simple → Phi-3, medium → Llama 3 8B, complex → GPT-4o
 3. Wire into /route endpoint: classify → route → return response

 Learning: Strategy pattern, token-based pricing

 Phase 6: PostgreSQL Logging

 Goal: Log every request with classification, model, and cost

 File: app/database.py

 1. Create new database: smart_router_db
 2. Create request_logs table (id, prompt, difficulty, model_used, response, cost, response_time_ms, created_at)
 3. log_request() and get_logs() functions
 4. Wire into /route — log after every response

 Learning: What SQL is, why we log, connection basics

 Phase 7: Cost Dashboard

 Goal: See how much money the router saves

 File: app/cost.py

 1. GET /dashboard — total requests by tier, actual cost vs. all-GPT-4o cost, savings %
 2. GET /logs — paginated request history

 Learning: SQL aggregation, measuring ROI

 Verification

 1. ollama serve
 2. uvicorn app.main:app --reload
 3. Test simple: curl -X POST localhost:8000/route -d '{"prompt":"Hello!"}' → Phi-3
 4. Test medium: curl -X POST localhost:8000/route -d '{"prompt":"Explain how DNS works"}' → Llama 3 8B
 5. Test complex: curl -X POST localhost:8000/route -d '{"prompt":"Write a binary search tree in Python with balancing"}' → GPT-4o
 6. curl localhost:8000/dashboard → cost savings
 7. curl localhost:8000/logs → all requests