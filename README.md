# 🧭 Job Search AI Agent

An **Agentic RAG** project that combines:

- **LLM** — Claude (Anthropic API) for reasoning, tool selection, and generation
- **Vector Embeddings** — `sentence-transformers` (`all-MiniLM-L6-v2`) turns job
  postings and queries into dense vectors
- **RAG (Retrieval-Augmented Generation)** — job postings are retrieved from a
  vector database and given to the LLM as grounded context (no hallucinated jobs)
- **Agentic behavior** — the LLM doesn't just answer once; it decides *which
  tools to call* (search jobs, fetch job details) and *reasons over multiple
  steps* before replying — e.g. searching, then evaluating match quality,
  then drafting a cover letter, all in one user turn

## How it's "agentic" and not just RAG

A plain RAG chatbot does: **retrieve → stuff into prompt → generate answer**, once.

This agent instead runs a **loop**: it sends the conversation + a list of tools
to Claude, and Claude decides whether to call a tool (e.g. `search_jobs`),
inspect the result, then possibly call another tool (`get_job_details`), and
only produces a final answer once it has enough information. The UI shows
this tool trace so you can see the agent's reasoning steps — useful for a
viva/demo.

## Architecture

```
User (Streamlit chat) 
      │
      ▼
agent.py  ── system prompt + tool schemas + conversation ──▶  Claude API
      │                                                            │
      │◀── Claude decides to call a tool (e.g. search_jobs) ───────┘
      ▼
tools.py ── calls vector_store.py ──▶ ChromaDB (job embeddings)
      │
      ▼
tool result sent back to Claude ──▶ Claude reasons + replies
      │
      ▼
Final answer shown in Streamlit
```

## Project structure

```
job-search-ai-agent/
├── app.py                 # Streamlit UI (entry point)
├── ingest.py               # One-off script to build the vector index
├── requirements.txt
├── .env.example             # Copy to .env and add your API key
├── data/
│   └── jobs.json           # Sample job postings dataset (15 jobs)
├── chroma_db/               # ChromaDB persistent storage (auto-created)
└── src/
    ├── config.py            # Paths, model names, constants
    ├── embeddings.py         # Vector embedding logic (sentence-transformers)
    ├── vector_store.py       # ChromaDB wrapper (build index + search)
    ├── resume_parser.py      # Extracts text from uploaded PDF/TXT resumes
    ├── tools.py              # Tool schemas + implementations for the agent
    ├── llm_client.py         # Anthropic API client wrapper
    └── agent.py              # The agentic tool-calling loop
```

## Setup

### 1. Create a virtual environment and install dependencies

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Add your API key

```bash
cp .env.example .env
```

Edit `.env` and paste your Anthropic API key (get one at
https://console.anthropic.com/). You need a small amount of API credit —
this project makes a handful of small requests per chat turn.

### 3. Build the vector index (optional — the app also does this automatically on first run)

```bash
python ingest.py
```

You should see:
```
Building vector index from data/jobs.json ...
Done. Indexed 15 job postings into ChromaDB.
```

### 4. Run the app

```bash
streamlit run app.py
```

Open the URL Streamlit prints (usually `http://localhost:8501`).

## How to use it

1. **(Optional) Upload your resume** in the sidebar (PDF or TXT) and click
   "Load resume into agent."
2. **Chat with the agent**, e.g.:
   - *"Find jobs matching my resume"*
   - *"Show me remote Python jobs for someone with 1 year of experience"*
   - *"Why is job_005 a good match for me?"*
   - *"What skills am I missing for job_011?"*
   - *"Draft a cover letter for job_002"*
3. Expand **"🔧 Agent reasoning trace"** under any response to see exactly
   which tools the agent called and what it retrieved — great for explaining
   the agentic/RAG flow in a project demo or viva.

## Extending this project (good next steps for a stronger submission)

- **Live job data**: swap `data/jobs.json` for a real API (Adzuna, RemoteOK,
  Jooble) — only `vector_store.build_from_json` and the ingest script need
  to change.
- **More tools**: add `score_resume_match(job_id)` that returns a numeric
  score + reasoning, or `compare_jobs(job_id_1, job_id_2)`.
- **Memory**: persist `agent_history` to disk per user so conversations
  survive restarts.
- **Better resume parsing**: extract structured fields (skills list, years
  of experience) instead of raw text, and use that for a hybrid
  keyword + vector search.
- **Different embedding/LLM providers**: swap `sentence-transformers` for
  OpenAI/Cohere embeddings, or the Anthropic client for OpenAI's — the
  interfaces in `embeddings.py` / `llm_client.py` are intentionally isolated
  so this is a small change.

## Notes on cost & models

- Embeddings run **locally and free** (no API calls, no API key needed for
  that part) via `sentence-transformers`.
- Only the LLM reasoning/tool-calling steps use the Anthropic API, and each
  chat turn typically makes 1-3 small API calls.
